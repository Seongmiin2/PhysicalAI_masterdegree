"""Finish local workspace migration after the experiment releases the GPU.

Never kills processes or clears another owner's lock. Re-run after resolving a
FAILED status; the journal retains enough information to resume partial moves.
"""
from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from harness.store import Store


def process_alive(pid: int) -> bool:
    if pid <= 0:
        raise ValueError("Expected a positive process ID")
    if os.name != "nt":
        raise RuntimeError("Process inspection is implemented only for Windows")
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    kernel.GetExitCodeProcess.restype = wintypes.BOOL
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.CloseHandle.restype = wintypes.BOOL
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        error = ctypes.get_last_error()
        if error == 87:  # ERROR_INVALID_PARAMETER: no such PID
            return False
        raise OSError(error, "Cannot inspect process; refusing migration")
    try:
        code = wintypes.DWORD()
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return code.value == 259  # STILL_ACTIVE; PID reuse is conservatively busy
    finally:
        kernel.CloseHandle(handle)


def is_junction(path: Path) -> bool:
    try:
        return getattr(path.lstat(), "st_reparse_tag", None) == 0xA0000003
    except FileNotFoundError:
        return False


def create_junction(path: Path, target: Path) -> None:
    # Environment variables avoid interpolating paths into PowerShell source.
    env = dict(os.environ, CHUM_LINK_PATH=str(path), CHUM_LINK_TARGET=str(target))
    subprocess.run([
        "powershell", "-NoProfile", "-NonInteractive", "-Command",
        "New-Item -ItemType Junction -Path $env:CHUM_LINK_PATH -Target $env:CHUM_LINK_TARGET -ErrorAction Stop | Out-Null",
    ], env=env, check=True, capture_output=True, text=True)


def write_status(path: Path, state: dict) -> None:
    state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".{os.getpid()}.tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def plain_directory(path: Path) -> None:
    if not path.is_dir() or path.resolve() != path.absolute():
        raise ValueError(f"Expected an existing real directory: {path}")
    if getattr(path.lstat(), "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        raise ValueError(f"Refusing directory reparse point: {path}")


def finalize(root: Path, store, watched_pid: int = 19476, alive=process_alive) -> dict:
    root = root.absolute()
    legacy = root.parent / "PhysicalAI_mini"
    physical = root / "physical_ai"
    archive = root.parent.parent / "master_degree_archive_20261001"
    retired = archive / "PhysicalAI_mini_retired"
    status_path = root / "outputs/harness/WORKSPACE_CONSOLIDATION_STATUS.json"
    expected = {"legacy": str(legacy), "physical": str(physical), "retired": str(retired)}
    state = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {}
    if state.get("paths", expected) != expected:
        raise ValueError("Journal paths do not match this workspace")
    state.update(paths=expected)
    state.setdefault("moved", [])
    owner = f"workspace-consolidation-{os.getpid()}-{uuid.uuid4().hex}"

    def record(status, **extra):
        state.pop("reason", None)
        state.pop("error", None)
        state.update(status=status, **extra)
        write_status(status_path, state)
        return state

    def busy_pid():
        live = root / "outputs/chum_window_extension_20261001/LIVE_STATUS.json"
        pids = {watched_pid}
        if live.exists():
            payload = json.loads(live.read_text(encoding="utf-8"))
            if payload.get("pid") is not None:
                pids.add(int(payload["pid"]))
        return next((pid for pid in sorted(pids) if alive(pid)), None)

    try:
        pid = busy_pid()
        if pid:
            return record("PENDING", reason=f"Process {pid} is alive")
        if not store.acquire_resource("compute:gpu0", owner):
            return record("PENDING", reason="compute:gpu0 is locked")
    except Exception as error:
        return record("FAILED", error=f"{type(error).__name__}: {error}")
    try:
        # Recheck after acquiring the same lock used by the experiment launcher.
        pid = busy_pid()
        if pid:
            return record("PENDING", reason=f"Process {pid} is alive")
        for path in (root.parent.parent, root.parent, root, physical, archive):
            plain_directory(path)
        if not legacy.exists():
            plain_directory(retired)
            if not state.get("archive_started"):
                raise ValueError("Missing legacy directory without migration journal")
            for name in ("data", "checkpoints"):
                plain_directory(physical / name)
                if name not in state["moved"]:
                    raise ValueError("Incomplete journal for already retired workspace")
            return record("COMPLETE", reason="Legacy workspace already retired")
        plain_directory(legacy)
        if os.path.lexists(retired):
            raise FileExistsError(f"Refusing to overwrite archive destination: {retired}")
        # Validate BOTH trees before removing even one junction.
        for name in ("data", "checkpoints"):
            source, destination = legacy / name, physical / name
            if is_junction(destination):
                plain_directory(source)
                if destination.resolve() != source:
                    raise ValueError(f"Unexpected junction target: {destination}")
            elif destination.exists():
                plain_directory(destination)
                if source.exists() or (name not in state["moved"] and state.get("moving") != name):
                    raise ValueError(f"Unverified existing destination: {destination}")
            elif not (state.get("moving") == name and source.is_dir()):
                raise ValueError(f"Missing verified junction: {destination}")
            if source.exists():
                plain_directory(source)
        for name in ("data", "checkpoints"):
            source, destination = legacy / name, physical / name
            if source.exists():
                record("MOVING", moving=name)
                if is_junction(destination):
                    if destination.resolve() != source:
                        raise ValueError("Junction target changed during migration")
                    os.rmdir(destination)  # verified junction only; never recursive
                try:
                    os.rename(source, destination)  # same-volume move, no copying
                except Exception:
                    if source.exists() and not os.path.lexists(destination):
                        create_junction(destination, source)
                    raise
            if name not in state["moved"]:
                state["moved"].append(name)
            record("MOVING", moving=None)
        record("MOVING", archive_started=True)
        if os.path.lexists(retired):
            raise FileExistsError(f"Archive destination appeared during migration: {retired}")
        os.rename(legacy, retired)  # fail without overwriting or deleting anything
        return record("COMPLETE", reason="Data integrated and legacy workspace archived")
    except Exception as error:
        return record("FAILED", error=f"{type(error).__name__}: {error}")
    finally:
        store.release_resource("compute:gpu0", owner)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wait", action="store_true")
    args = parser.parse_args()
    store = Store(ROOT / "outputs/harness/research.sqlite3")
    while True:
        state = finalize(ROOT, store)
        print(json.dumps({k: state[k] for k in ("status", "reason", "error") if k in state}), flush=True)
        if state["status"] != "PENDING" or not args.wait:
            return 1 if state["status"] == "FAILED" else 0
        time.sleep(30)


if __name__ == "__main__":
    raise SystemExit(main())
