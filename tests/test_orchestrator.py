import hashlib
import json
import shutil
from pathlib import Path

import pytest
import yaml

from agents import ResearchOrchestrator
from providers.mock import MockProvider


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def project(tmp_path, monkeypatch):
    root = tmp_path / "project"
    for relative in (
        "missions/mission_001_topic_validation.yaml",
        "state/RESEARCH_STATE.json",
        "state/DECISION_LOG.md",
        "state/EVIDENCE_LEDGER.jsonl",
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    monkeypatch.chdir(root)
    return root


@pytest.fixture
def reference_projects(tmp_path):
    references = []
    for name in ("reference_a", "reference_b"):
        path = tmp_path / name
        path.mkdir()
        (path / "evidence.txt").write_text("Existing reference evidence\n", encoding="utf-8")
        references.append(path)
    return references


def _mission(root):
    return yaml.safe_load((root / "missions" / "mission_001_topic_validation.yaml").read_text(encoding="utf-8"))


def _manifest(path: Path) -> dict[str, str]:
    return {
        str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in path.rglob("*") if p.is_file() and ".git" not in p.parts
    }


def test_reference_projects_are_not_modified(project, reference_projects):
    before = [_manifest(path) for path in reference_projects]
    assert all(before), "Reference fixtures must contain files to test preservation"
    ResearchOrchestrator(project, MockProvider()).run(_mission(project))
    after = [_manifest(path) for path in reference_projects]
    assert before == after


def test_mock_mission_runs_to_report(project):
    output = ResearchOrchestrator(project, MockProvider()).run(_mission(project))
    assert output.is_relative_to(project)
    text = output.read_text(encoding="utf-8")
    assert "THESIS TOPIC VALIDATION REPORT" in text
    assert "Candidate A" in text and "Candidate B" in text
    assert "WAITING_FOR_USER_APPROVAL" in text


def test_agent_outputs_follow_schema(project):
    mission = _mission(project)
    provider = MockProvider()
    for candidate in mission["candidates"]:
        for agent in ("literature", "methodology", "reviewer"):
            from providers.base import GenerationRequest
            result = provider.generate(GenerationRequest(agent, mission, {"candidate": candidate}))
            assert result["agent"] == agent
            assert result["candidate_id"] == candidate["id"]
            assert result["provenance"] == "MOCK"


def test_topic_is_not_auto_locked(project):
    ResearchOrchestrator(project, MockProvider()).run(_mission(project))
    state = json.loads((project / "state" / "RESEARCH_STATE.json").read_text(encoding="utf-8"))
    assert state["locked_topic"] is None
    assert state["locked_research_question"] is None
    assert state["pending_human_approval"] is True
    assert state["status"] == "WAITING_FOR_USER_APPROVAL"


def test_major_decision_is_logged(project):
    before = (project / "state" / "DECISION_LOG.md").read_text(encoding="utf-8")
    ResearchOrchestrator(project, MockProvider()).run(_mission(project))
    after = (project / "state" / "DECISION_LOG.md").read_text(encoding="utf-8")
    assert len(after) > len(before)
    assert "mission_001_topic_validation" in after


def test_mock_is_not_written_to_evidence_ledger(project):
    ledger = project / "state" / "EVIDENCE_LEDGER.jsonl"
    before = ledger.read_bytes()
    ResearchOrchestrator(project, MockProvider()).run(_mission(project))
    assert ledger.read_bytes() == before
    for line in before.decode("utf-8").splitlines():
        assert json.loads(line)["mock"] is False

