import hashlib
import json
import sys

import pytest

from harness import __main__ as cli
from harness.store import Store
from providers import finetuned


@pytest.fixture
def route_setup(tmp_path, monkeypatch):
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    source = tmp_path / "records.jsonl"
    row = {
        "label": "LABEL_SENTINEL", "split": "test", "provenance": {"private": "PROVENANCE_SENTINEL"},
        "messages": [{"role": "system", "content": "SYSTEM_SENTINEL"},
                     {"role": "user", "content": "Observed experiment PARTIAL"},
                     {"role": "assistant", "content": "TEACHER_SENTINEL"}],
    }
    source.write_text(json.dumps(row) + "\n", encoding="utf-8")
    database = tmp_path / "outputs/harness/research.sqlite3"
    calls = []
    class FakeProvider:
        def __init__(self):
            calls.append("constructed")
        def route(self, record):
            calls.append(record)
            return {"next_action": "RESUME_INCOMPLETE", "authorizes_execution": False}
    monkeypatch.setattr(finetuned, "FineTunedProvider", FakeProvider)
    monkeypatch.setattr(sys, "argv", ["harness", "route", str(source)])
    return source, database, calls


def test_route_excludes_teacher_and_records_success(route_setup, capsys):
    source, database, calls = route_setup
    cli.main()
    result = json.loads(capsys.readouterr().out)
    assert not result["authorizes_execution"]
    assert calls == ["constructed", {"text": "Observed experiment PARTIAL"}]
    events = Store(database).events()
    assert [event["kind"] for event in events] == ["finetuned_routing_started", "finetuned_routing_completed"]
    assert events[0]["payload"]["source"] == str(source.resolve())
    assert events[0]["payload"]["input_sha256"] == hashlib.sha256(calls[1]["text"].encode()).hexdigest()


@pytest.mark.parametrize("row", [-1, 1, 99])
def test_bad_row_never_constructs_model(route_setup, monkeypatch, row):
    source, database, calls = route_setup
    monkeypatch.setattr(sys, "argv", ["harness", "route", str(source), "--row", str(row)])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
    assert calls == []
    assert Store(database).events() == []


def test_route_failure_persisted(route_setup, monkeypatch):
    _, database, calls = route_setup
    class FailedProvider:
        def route(self, record):
            raise RuntimeError("adapter missing")
    monkeypatch.setattr(finetuned, "FineTunedProvider", FailedProvider)
    with pytest.raises(RuntimeError, match="adapter missing"):
        cli.main()
    events = Store(database).events()
    assert [event["kind"] for event in events] == ["finetuned_routing_started", "finetuned_routing_failed"]
    assert events[-1]["payload"]["error"] == "adapter missing"


def test_route_optional_retrieval_adds_cited_chunks(route_setup, monkeypatch, tmp_path, capsys):
    source, database, calls = route_setup
    store = Store(database)
    store.index_document(tmp_path / "evidence.md", "partial reference evidence")
    monkeypatch.setattr(sys, "argv", ["harness", "route", str(source), "--query", "partial"])
    cli.main()
    result = json.loads(capsys.readouterr().out)
    assert "partial reference evidence" in calls[1]["text"]
    assert "TEACHER_SENTINEL" not in calls[1]["text"]
    assert result["retrieved_chunk_ids"] == [store.search("partial")[0]["chunk_id"]]
