import importlib.util
import json
import os
from pathlib import Path

import pytest

from harness.store import Store

SPEC = importlib.util.spec_from_file_location(
    "workspace_finalizer", Path(__file__).resolve().parents[1] / "experiments/finalize_workspace_consolidation.py"
)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


@pytest.fixture
def workspace(tmp_path):
    root = tmp_path / "master_degree/Thesis-Orchestrator"
    (root / "physical_ai").mkdir(parents=True)
    (tmp_path / "master_degree_archive_20261001").mkdir()
    legacy = root.parent / "PhysicalAI_mini"
    legacy.mkdir()
    for name in ("data", "checkpoints"):
        (legacy / name).mkdir()
        (legacy / name / "preserve.txt").write_text(name, encoding="utf-8")
    (legacy / "history.txt").write_text("preserve legacy", encoding="utf-8")
    return root, Store(tmp_path / "store.sqlite3")


def link_workspace(root):
    if os.name != "nt":
        pytest.skip("Tests verify real Windows directory junctions")
    for name in ("data", "checkpoints"):
        module.create_junction(root / "physical_ai" / name, root.parent / "PhysicalAI_mini" / name)


def test_live_process_prevents_all_moves(workspace):
    root, store = workspace
    state = module.finalize(root, store, alive=lambda pid: True)
    assert state["status"] == "PENDING"
    assert (root.parent / "PhysicalAI_mini/data/preserve.txt").is_file()
    assert store.acquire_resource("compute:gpu0", "test")
    store.release_resource("compute:gpu0", "test")


def test_other_gpu_owner_is_preserved(workspace):
    root, store = workspace
    assert store.acquire_resource("compute:gpu0", "experiment")
    assert module.finalize(root, store, alive=lambda pid: False)["status"] == "PENDING"
    store.release_resource("compute:gpu0", "experiment")


def test_registered_live_pid_is_checked(workspace):
    root, store = workspace
    live = root / "outputs/chum_window_extension_20261001/LIVE_STATUS.json"
    live.parent.mkdir(parents=True)
    live.write_text(json.dumps({"pid": 1234}), encoding="utf-8")
    assert module.finalize(root, store, alive=lambda pid: pid == 1234)["status"] == "PENDING"


def test_process_inspection_error_fails_closed(workspace):
    root, store = workspace
    def unavailable(pid):
        raise PermissionError("Cannot inspect")
    assert module.finalize(root, store, alive=unavailable)["status"] == "FAILED"
    assert (root.parent / "PhysicalAI_mini/data").is_dir()


def test_existing_destination_is_not_overwritten(workspace):
    root, store = workspace
    destination = root / "physical_ai/data"
    destination.mkdir()
    marker = destination / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    assert module.finalize(root, store, alive=lambda pid: False)["status"] == "FAILED"
    assert marker.read_text(encoding="utf-8") == "keep"
    assert (root.parent / "PhysicalAI_mini/data/preserve.txt").is_file()


def test_verified_junctions_move_and_resume_idempotently(workspace):
    root, store = workspace
    link_workspace(root)
    assert module.finalize(root, store, alive=lambda pid: False)["status"] == "COMPLETE"
    for name in ("data", "checkpoints"):
        destination = root / "physical_ai" / name
        assert not module.is_junction(destination)
        assert (destination / "preserve.txt").read_text(encoding="utf-8") == name
    retired = root.parent.parent / "master_degree_archive_20261001/PhysicalAI_mini_retired"
    assert (retired / "history.txt").is_file()
    assert not (root.parent / "PhysicalAI_mini").exists()
    assert module.finalize(root, store, alive=lambda pid: False)["status"] == "COMPLETE"
    assert store.acquire_resource("compute:gpu0", "test")
    store.release_resource("compute:gpu0", "test")


def test_wrong_junction_target_leaves_both_links_untouched(workspace):
    root, store = workspace
    link_workspace(root)
    bad = root / "physical_ai/checkpoints"
    os.rmdir(bad)
    module.create_junction(bad, root.parent / "PhysicalAI_mini/data")
    assert module.finalize(root, store, alive=lambda pid: False)["status"] == "FAILED"
    assert module.is_junction(root / "physical_ai/data")
    assert module.is_junction(bad)


def test_failed_move_restores_junction_then_retry_completes(workspace, monkeypatch):
    root, store = workspace
    link_workspace(root)
    rename = module.os.rename
    def fail_data(source, destination):
        if Path(source).name == "data":
            raise PermissionError("Simulated move failure")
        return rename(source, destination)
    monkeypatch.setattr(module.os, "rename", fail_data)
    assert module.finalize(root, store, alive=lambda pid: False)["status"] == "FAILED"
    assert module.is_junction(root / "physical_ai/data")
    assert (root.parent / "PhysicalAI_mini/data/preserve.txt").is_file()
    monkeypatch.setattr(module.os, "rename", rename)
    assert module.finalize(root, store, alive=lambda pid: False)["status"] == "COMPLETE"


def test_archive_failure_keeps_migrated_data_and_allows_retry(workspace, monkeypatch):
    root, store = workspace
    link_workspace(root)
    rename = module.os.rename
    def fail_archive(source, destination):
        if Path(source).name == "PhysicalAI_mini":
            raise PermissionError("Simulated archive failure")
        return rename(source, destination)
    monkeypatch.setattr(module.os, "rename", fail_archive)
    assert module.finalize(root, store, alive=lambda pid: False)["status"] == "FAILED"
    assert (root / "physical_ai/data/preserve.txt").is_file()
    assert (root.parent / "PhysicalAI_mini/history.txt").is_file()
    monkeypatch.setattr(module.os, "rename", rename)
    assert module.finalize(root, store, alive=lambda pid: False)["status"] == "COMPLETE"


def test_archive_collision_is_rejected_before_unlinking(workspace):
    root, store = workspace
    link_workspace(root)
    retired = root.parent.parent / "master_degree_archive_20261001/PhysicalAI_mini_retired"
    retired.mkdir()
    (retired / "keep.txt").write_text("keep", encoding="utf-8")
    assert module.finalize(root, store, alive=lambda pid: False)["status"] == "FAILED"
    assert module.is_junction(root / "physical_ai/data")
    assert (retired / "keep.txt").is_file()


def test_retry_after_crash_between_unlink_and_move(workspace):
    root, store = workspace
    link_workspace(root)
    destination = root / "physical_ai/data"
    os.rmdir(destination)
    status = root / "outputs/harness/WORKSPACE_CONSOLIDATION_STATUS.json"
    module.write_status(status, {
        "status": "MOVING", "moving": "data", "moved": [],
        "paths": {
            "legacy": str(root.parent / "PhysicalAI_mini"),
            "physical": str(root / "physical_ai"),
            "retired": str(root.parent.parent / "master_degree_archive_20261001/PhysicalAI_mini_retired"),
        },
    })
    assert module.finalize(root, store, alive=lambda pid: False)["status"] == "COMPLETE"
    assert (destination / "preserve.txt").read_text(encoding="utf-8") == "data"
