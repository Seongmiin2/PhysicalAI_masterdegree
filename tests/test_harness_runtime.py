import hashlib
import json
from pathlib import Path
import sys

import pytest

from harness import runtime
from harness.store import Store


class RecordingProvider:
    def __init__(self):
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return {"command": "DO_NOT_EXECUTE_MODEL_CONTENT", "needs_human_review": True}


@pytest.fixture(autouse=True)
def isolate_runtime_root(tmp_path, monkeypatch):
    monkeypatch.setattr(runtime, "ROOT", tmp_path)


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "state.sqlite3")


def test_missing_evidence_never_calls_model(store):
    provider = RecordingProvider()
    result = runtime.deliberate(store, provider, "unknown")
    assert result["status"] == "NEEDS_EVIDENCE"
    assert provider.requests == []
    assert store.events()[-1]["kind"] == "deliberation_completed"


def test_planner_then_reviewer_advisory_only(store, tmp_path, monkeypatch):
    store.index_document(tmp_path / "source.md", "window evidence recorded")
    provider = RecordingProvider()
    def forbidden(*args, **kwargs):
        raise AssertionError("Model content must not execute")
    monkeypatch.setattr(runtime.subprocess, "Popen", forbidden)
    result = runtime.deliberate(store, provider, "window")
    assert [r.agent for r in provider.requests] == ["planner", "reviewer"]
    assert provider.requests[1].context["proposal_to_critique"]["agent"] == "planner"
    assert result["status"] == "ADVISORY_ONLY"
    assert result["evidence"][0]["content_hash"]
    decision = runtime.record_human_decision(store, result["request_id"], "accept", "reviewed")
    assert decision["authorizes_execution"] is False


@pytest.mark.parametrize("request_id,decision,reason", [
    ("unknown", "accept", "reviewed"),
    ("unknown", "launch", "reviewed"),
    ("unknown", "accept", "  "),
])
def test_invalid_human_decisions_are_not_recorded(store, request_id, decision, reason):
    with pytest.raises(ValueError):
        runtime.record_human_decision(store, request_id, decision, reason)
    assert store.events() == []


def test_artifact_snapshot_indexes_only_complete_changes(store, tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    artifact = output / "RESULT.json"
    artifact.write_text('{"status":"first"}', encoding="utf-8")
    seen = {}
    runtime.snapshot_outputs(store, output, seen, "task")
    runtime.snapshot_outputs(store, output, seen, "task")
    assert len(store.events("task")) == 1
    assert store.search("first")
    artifact.write_text('{"status":', encoding="utf-8")
    runtime.snapshot_outputs(store, output, seen, "task")
    assert len(store.events("task")) == 1
    artifact.write_text('{"status":"second"}', encoding="utf-8")
    runtime.snapshot_outputs(store, output, seen, "task")
    assert len(store.events("task")) == 2
    assert not store.search("first")
    assert store.search("second")


def make_project(tmp_path, script):
    root = tmp_path / "project"
    (root / "configs").mkdir(parents=True)
    (root / "experiments").mkdir()
    (root / "configs/chum_window_extension.yaml").write_text(
        "paths:\n  output: outputs/window\n", encoding="utf-8")
    (root / "experiments/run_chum_window_extension.py").write_text(script, encoding="utf-8")
    return root


@pytest.mark.parametrize("exitcode,expected", [(0, "completed"), (7, "failed")])
def test_execute_real_stub_child_records_exit(store, tmp_path, exitcode, expected):
    root = make_project(tmp_path,
        "from pathlib import Path\n"
        "p=Path('outputs/window'); p.mkdir(parents=True,exist_ok=True)\n"
        "(p/'RESULT.json').write_text('{\"metric\":0.8}')\n"
        f"raise SystemExit({exitcode})\n")
    result = runtime.execute(store, Path(sys.executable), "pilot", root=root, timeout_seconds=10)
    assert result["status"] == expected
    assert result["returncode"] == exitcode
    assert store.get_task(result["task_id"])["status"] == expected
    assert store.search("metric")
    assert any(e["kind"] == "artifact_updated" for e in store.events(result["task_id"]))


def test_execute_timeout_stops_child_and_records_failure(store, tmp_path):
    root = make_project(tmp_path, "import time\ntime.sleep(60)\n")
    with pytest.raises(TimeoutError):
        runtime.execute(store, Path(sys.executable), "pilot", root=root, timeout_seconds=0.05)
    task = store.list_tasks()[0]
    assert task["status"] == "failed"
    assert "deadline" in task["result"]["error"]
    assert not (root / "outputs/window/.harness-execution.lock").exists()
    resource = "experiment-output:" + str((root / "outputs/window").resolve())
    assert store.acquire_resource(resource, "retry-after-timeout")
    assert store.events(task["task_id"])[-1]["kind"] == "execution_failed"


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_invalid_timeout_does_not_create_task(store, tmp_path, timeout):
    root = make_project(tmp_path, "pass")
    with pytest.raises(ValueError):
        runtime.execute(store, Path(sys.executable), "pilot", root=root, timeout_seconds=timeout)
    assert store.list_tasks() == []


def test_existing_output_lock_prevents_duplicate_process(store, tmp_path, monkeypatch):
    root = make_project(tmp_path, "pass")
    resource = "experiment-output:" + str((root / "outputs/window").resolve())
    assert store.acquire_resource(resource, "existing-worker")
    def forbidden(*args, **kwargs):
        raise AssertionError("Duplicate launch reached subprocess")
    monkeypatch.setattr(runtime.subprocess, "Popen", forbidden)
    with pytest.raises(RuntimeError, match="Another worker"):
        runtime.execute(store, Path(sys.executable), "pilot", root=root)
    assert store.list_tasks() == []
    assert not store.acquire_resource(resource, "intruder")
    store.release_resource(resource, "existing-worker")


def test_spawn_failure_marks_task_failed_and_releases_lock(store, tmp_path, monkeypatch):
    root = make_project(tmp_path, "pass")
    def fail_spawn(*args, **kwargs):
        raise OSError("spawn failure")
    monkeypatch.setattr(runtime.subprocess, "Popen", fail_spawn)
    with pytest.raises(OSError, match="spawn failure"):
        runtime.execute(store, Path(sys.executable), "pilot", root=root)
    assert store.list_tasks()[0]["status"] == "failed"
    resource = "experiment-output:" + str((root / "outputs/window").resolve())
    assert store.acquire_resource(resource, "retry-worker")


def test_output_file_lock_blocks_other_database(store, tmp_path, monkeypatch):
    root = make_project(tmp_path, "pass")
    output = root / "outputs/window"
    output.mkdir(parents=True)
    lock_path = output / ".harness-execution.lock"
    lock_path.write_text('{"worker":"other-database"}', encoding="utf-8")
    other_store = Store(tmp_path / "other.sqlite3")
    def forbidden(*args, **kwargs):
        raise AssertionError("Cross-database duplicate launch")
    monkeypatch.setattr(runtime.subprocess, "Popen", forbidden)
    with pytest.raises(FileExistsError):
        runtime.execute(other_store, Path(sys.executable), "pilot", root=root)
    assert other_store.list_tasks() == []
    assert json.loads(lock_path.read_text())["worker"] == "other-database"
    resource = "experiment-output:" + str(output.resolve())
    assert other_store.acquire_resource(resource, "retry")


def test_human_feedback_is_available_on_next_deliberation(store, tmp_path):
    store.index_document(tmp_path / "evidence.md", "window experiment")
    first = runtime.deliberate(store, RecordingProvider(), "window")
    for number in range(7):
        runtime.record_human_decision(store, first["request_id"], "revise", f"review-{number}")
    # Other event kinds must never appear as actual human feedback.
    store.append_event("model_suggested_feedback", {"reason": "not a human decision"})
    provider = RecordingProvider()
    runtime.deliberate(store, provider, "window")
    for request in provider.requests:
        feedback = request.context["human_feedback"]
        assert [row["reason"] for row in feedback] == [f"review-{number}" for number in range(2, 7)]
        assert all(row["actor"] == "human" and not row["authorizes_execution"] for row in feedback)


@pytest.mark.parametrize("profile,filename", [
    ("main", "chum_window_extension.yaml"), ("pilot", "chum_window_pilot.yaml"),
])
def test_task_profile_selects_allowlisted_config_and_hash(tmp_path, profile, filename):
    root = make_project(tmp_path, "pass")
    (root / "configs/chum_window_pilot.yaml").write_text("paths: {output: outputs/pilot}", encoding="utf-8")
    config = root / "configs" / filename
    spec = runtime.task_spec(root, Path(sys.executable), "pilot", 3, profile=profile)
    assert spec["argv"][-2:] == ["--max-tasks", "3"]
    assert spec["argv"][spec["argv"].index("--config") + 1] == str(config)
    assert spec["config_sha256"] == hashlib.sha256(config.read_bytes()).hexdigest()
    assert spec["profile"] == profile
    before = spec["fingerprint"]
    config.write_text(config.read_text() + "\n# changed", encoding="utf-8")
    assert runtime.task_spec(root, Path(sys.executable), "pilot", 3, profile)["fingerprint"] != before


def test_task_profile_rejects_arbitrary_paths(tmp_path):
    root = make_project(tmp_path, "pass")
    with pytest.raises(ValueError, match="profile"):
        runtime.task_spec(root, Path(sys.executable), "pilot", 1, "../../other.yaml")


def make_work_state(root):
    path = root / "state/CHUM_WORK_STATE.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"next_authorized_work": {"status": "PLANNED", "blocker": "waiting"}}), encoding="utf-8")
    return path


def write_live(root, profile, status):
    directory = "chum_window_pilot_20261001" if profile == "pilot" else "chum_window_extension_20261001"
    path = root / "outputs" / directory / "LIVE_STATUS.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"status": status, "stage": "task_budget_reached", "completed_tasks": 1}), encoding="utf-8")
    return path


def test_work_state_preserves_partial_pilot_and_source_provenance(tmp_path):
    path = make_work_state(tmp_path)
    source = write_live(tmp_path, "pilot", "PARTIAL")
    runtime.refresh_work_state(tmp_path)
    state = json.loads(path.read_text(encoding="utf-8"))
    assert state["next_authorized_work"]["status"] == "PILOT_PARTIAL"
    assert state["live_experiments"]["pilot"]["completed_tasks"] == 1
    assert state["live_experiments"]["pilot"]["source"] == str(source.relative_to(tmp_path))
    write_live(tmp_path, "main", "RUNNING")
    runtime.refresh_work_state(tmp_path)
    assert json.loads(path.read_text())["next_authorized_work"]["status"] == "MAIN_RUNNING"


def test_deliberate_refreshes_pinned_state_only_after_indexing(store, tmp_path):
    path = make_work_state(tmp_path)
    original = path.read_bytes()
    write_live(tmp_path, "pilot", "PARTIAL")
    provider = RecordingProvider()
    assert runtime.deliberate(store, provider, "unrelated")["status"] == "NEEDS_EVIDENCE"
    assert path.read_bytes() == original
    assert provider.requests == []
    store.index_document(path)
    result = runtime.deliberate(store, provider, "unrelated")
    current = provider.requests[0].context["current_state"]
    assert current and "PILOT_PARTIAL" in current[0]["content"]
    assert current[0]["path"] == str(path.resolve())
    assert current[0]["document_hash"] == hashlib.sha256(path.read_text(encoding="utf-8-sig").encode("utf-8")).hexdigest()
    assert result["evidence"][0]["chunk_id"] == current[0]["chunk_id"]
    assert len({row["chunk_id"] for row in result["evidence"]}) == len(result["evidence"])


def test_gpu_busy_prevents_child_and_releases_output_lock(store, tmp_path, monkeypatch):
    root = make_project(tmp_path, "pass")
    assert store.acquire_resource("compute:gpu0", "finetune-worker")
    def forbidden(*args, **kwargs):
        raise AssertionError("GPU busy must prevent subprocess launch")
    monkeypatch.setattr(runtime.subprocess, "Popen", forbidden)
    with pytest.raises(RuntimeError, match="owns the GPU"):
        runtime.execute(store, Path(sys.executable), "pilot", root=root)
    assert not (root / "outputs/window/.harness-execution.lock").exists()
    assert store.list_tasks() == []
    assert not store.acquire_resource("compute:gpu0", "other")
    assert store.acquire_resource("experiment-output:" + str((root / "outputs/window").resolve()), "retry")
    store.release_resource("compute:gpu0", "finetune-worker")


def test_gpu_lock_released_when_child_spawn_fails(store, tmp_path, monkeypatch):
    root = make_project(tmp_path, "pass")
    def fail_spawn(*args, **kwargs):
        raise OSError("failed before training")
    monkeypatch.setattr(runtime.subprocess, "Popen", fail_spawn)
    with pytest.raises(OSError):
        runtime.execute(store, Path(sys.executable), "pilot", root=root)
    assert store.acquire_resource("compute:gpu0", "finetune-next")
    assert store.list_tasks()[0]["status"] == "failed"
