from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time
import uuid

from providers.base import GenerationRequest
from .store import Store

ROOT = Path(__file__).resolve().parents[1]


def refresh_work_state(root: Path = ROOT):
    path = root / "state/CHUM_WORK_STATE.json"
    if not path.exists():
        return
    state = json.loads(path.read_text(encoding="utf-8"))
    live = {}
    for name, directory in (("pilot", "chum_window_pilot_20261001"),
                            ("main", "chum_window_extension_20261001")):
        source = root / "outputs" / directory / "LIVE_STATUS.json"
        if source.exists():
            row = json.loads(source.read_text(encoding="utf-8"))
            live[name] = {k: row[k] for k in ("status", "stage", "completed_tasks", "task", "epoch", "updated_at") if k in row}
            live[name]["source"] = str(source.relative_to(root))
    state["live_experiments"] = live
    active = live.get("main", live.get("pilot"))
    if active:
        state["next_authorized_work"]["status"] = ("MAIN_" if "main" in live else "PILOT_") + active["status"]
        if active["status"] in {"RUNNING", "PARTIAL", "COMPLETE"}:
            state["next_authorized_work"]["blocker"] = None
    text = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    if text != path.read_text(encoding="utf-8"):
        tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)


def index_evidence(store: Store, root: Path = ROOT) -> dict:
    refresh_work_state(root)
    count = changed = 0
    for folder in ("state", "docs", "deliverables", "outputs"):
        for path in sorted((root / folder).rglob("*")):
            if not path.is_file() or path.suffix.lower() not in {".md", ".json", ".csv"}:
                continue
            if any(part.startswith("chum_ops_training_") for part in path.parts) or path.name == "LOCAL_MODEL_EVALUATION.json":
                store.remove_document(path)
                continue
            if any(p in {"harness", "reviews", "professor_research"} for p in path.parts):
                continue
            if path.stat().st_size > 250_000 or "PUBLISH" in path.name:
                continue
            changed += bool(store.index_document(path))
            count += 1
    result = {"documents": count, "changed": changed}
    store.append_event("evidence_indexed", result)
    return result


def deliberate(store: Store, provider, question: str) -> dict:
    """Evidence agent -> planner -> critic. Suggestions never dispatch commands."""
    started = time.perf_counter()
    state_path = ROOT / "state/CHUM_WORK_STATE.json"
    if state_path.exists() and store.document_chunks(state_path, limit=1):
        refresh_work_state(ROOT)
        store.index_document(state_path)
    current = store.document_chunks(state_path, limit=3)
    known = {e["chunk_id"] for e in current}
    evidence = current + [e for e in store.search(question, limit=4) if e["chunk_id"] not in known]
    request_id = uuid.uuid4().hex
    store.append_event("retrieval", {"request_id": request_id, "question": question,
                       "sources": [{k: row[k] for k in ("path", "chunk_id", "content_hash")} for row in evidence]})
    if not evidence:
        result = {"request_id": request_id, "status": "NEEDS_EVIDENCE", "question": question,
                  "needs_human_review": True, "agents": [], "evidence": []}
        store.append_event("deliberation_completed", result)
        return result
    feedback = [e["payload"] for e in store.events() if e["kind"] == "human_decision"][-5:]
    results = []
    for role in ("planner", "reviewer"):
        context = {"evidence": evidence, "current_state": current, "human_feedback": feedback}
        if role == "reviewer":
            context["proposal_to_critique"] = results[0]
        before = time.perf_counter()
        try:
            response = provider.generate(GenerationRequest(role, {"question": question}, context))
        except Exception as exc:
            store.append_event("agent_failed", {"request_id": request_id, "agent": role,
                               "error": str(exc), "latency_seconds": time.perf_counter() - before})
            raise
        response = dict(response, agent=role, latency_seconds=time.perf_counter() - before)
        results.append(response)
        store.append_event("agent_completed", {"request_id": request_id, **response})
    result = {"request_id": request_id, "status": "ADVISORY_ONLY", "question": question,
              "provenance": "LOCAL_MODEL_SUGGESTION", "agents": results,
              "evidence": evidence, "latency_seconds": time.perf_counter() - started,
              "needs_human_review": any(r.get("needs_human_review", True) for r in results)}
    store.append_event("deliberation_completed", result)
    return result


def record_human_decision(store: Store, request_id: str, decision: str, reason: str) -> dict:
    if decision not in {"accept", "reject", "revise"} or not reason.strip():
        raise ValueError("Decision must be accept/reject/revise with a nonempty reason")
    if not any(e["kind"] == "deliberation_completed" and e["payload"].get("request_id") == request_id
               for e in store.events()):
        raise ValueError("Unknown deliberation request")
    record = {"request_id": request_id, "decision": decision, "reason": reason,
              "actor": "human", "authorizes_execution": False}
    store.append_event("human_decision", record)
    return record


def task_spec(root: Path, python: Path, mode: str, max_tasks: int, profile: str = "main") -> dict:
    if mode not in {"dry-run", "smoke", "pilot"} or not 1 <= max_tasks <= 18:
        raise ValueError("Unknown mode or max_tasks outside 1..18")
    profiles = {"main": "chum_window_extension.yaml", "pilot": "chum_window_pilot.yaml"}
    if profile not in profiles:
        raise ValueError("Unknown experiment profile")
    config = root / "configs" / profiles[profile]
    script = root / "experiments/run_chum_window_extension.py"
    argv = [str(python.resolve()), "-u", str(script), "--config", str(config)]
    argv += ["--max-tasks", str(max_tasks)] if mode == "pilot" else ["--" + mode]
    identity = {"argv": argv, "config_sha256": hashlib.sha256(config.read_bytes()).hexdigest(),
                "script_sha256": hashlib.sha256(script.read_bytes()).hexdigest(), "mode": mode,
                "config_path": str(config), "profile": profile}
    identity["fingerprint"] = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    return identity


def snapshot_outputs(store: Store, output: Path, seen: dict, task_id: str):
    if not output.exists():
        return
    for path in output.rglob("*"):
        if not path.is_file() or path.name not in {
            "LIVE_STATUS.json", "TRAINING_HISTORY.csv", "RESULT.json", "METRICS.csv",
            "RUN_MANIFEST.json", "SMOKE_RESULT.json", "DRY_RUN.json"
        }:
            continue
        try:
            data = path.read_bytes()
            digest = hashlib.sha256(data).hexdigest()
            if seen.get(str(path)) == digest:
                continue
            content = data.decode("utf-8-sig")
            if path.suffix == ".json":
                json.loads(content)
            store.append_event("artifact_updated", {"path": str(path), "sha256": digest,
                               "content": content}, task_id=task_id)
            store.index_document(path, text=content)
            seen[str(path)] = digest
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue


def execute(store: Store, python: Path, mode: str, max_tasks: int = 1,
            root: Path = ROOT, timeout_seconds: float = 14400, profile: str = "main") -> dict:
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive and finite")
    spec = task_spec(root, python, mode, max_tasks, profile)
    import yaml
    cfg = yaml.safe_load(Path(spec["config_path"]).read_text(encoding="utf-8"))
    output = (root / cfg["paths"]["output"]).resolve()
    task_id = "window-" + mode + "-" + uuid.uuid4().hex[:12]
    worker = f"pid-{os.getpid()}-{task_id}"
    resource = "experiment-output:" + str(output)
    if not store.acquire_resource(resource, worker):
        raise RuntimeError("Another worker holds this experiment output; inspect its process before retrying")
    started, seen, process, claimed = time.monotonic(), {}, None, False
    lock_path, lock_owned = output / ".harness-execution.lock", False
    gpu_owned = False
    try:
        output.mkdir(parents=True, exist_ok=True)
        with lock_path.open("x", encoding="utf-8") as lock:
            lock_owned = True
            json.dump({"worker": worker, "pid": os.getpid(), "task_id": task_id}, lock)
        if mode == "pilot":
            gpu_owned = store.acquire_resource("compute:gpu0", worker)
            if not gpu_owned:
                raise RuntimeError("Another harness job owns the GPU; retry after it finishes")
        store.create_task(task_id, spec)
        claimed = store.claim_task(task_id, worker)
        if not claimed:
            raise RuntimeError("Task already claimed")
        log_dir = root / "outputs/harness/runs" / task_id
        log_dir.mkdir(parents=True, exist_ok=True)
        store.append_event("execution_started", spec, task_id=task_id)
        with (log_dir / "stdout.log").open("wb") as out, (log_dir / "stderr.log").open("wb") as err:
            process = subprocess.Popen(spec["argv"], cwd=root, stdout=out, stderr=err,
                                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            while process.poll() is None:
                snapshot_outputs(store, output, seen, task_id)
                if time.monotonic() - started > timeout_seconds:
                    raise TimeoutError("Experiment exceeded configured execution deadline")
                time.sleep(2)
            snapshot_outputs(store, output, seen, task_id)
        result = {"returncode": process.returncode, "log_dir": str(log_dir),
                  "elapsed_seconds": time.monotonic() - started,
                  "stdout_tail": (log_dir / "stdout.log").read_text(encoding="utf-8", errors="replace")[-4096:],
                  "stderr_tail": (log_dir / "stderr.log").read_text(encoding="utf-8", errors="replace")[-4096:],
                  "note": "Task completion does not imply full experiment grid completion."}
        status = "completed" if process.returncode == 0 else "failed"
        store.finish_task(task_id, worker, status=status, result=result)
        claimed = False
        store.append_event("execution_finished", result, task_id=task_id)
        return {"task_id": task_id, "status": status, **result}
    except BaseException as exc:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)
        if claimed:
            store.finish_task(task_id, worker, status="failed", result={"error": str(exc)})
        store.append_event("execution_failed", {"error": str(exc)}, task_id=task_id)
        raise
    finally:
        # Keep a persistent lock if the child could not be stopped.
        if process is None or process.poll() is not None:
            if gpu_owned:
                store.release_resource("compute:gpu0", worker)
            if lock_owned:
                lock_path.unlink(missing_ok=True)
            store.release_resource(resource, worker)
