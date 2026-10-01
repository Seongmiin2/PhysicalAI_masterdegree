from concurrent.futures import ThreadPoolExecutor
import hashlib
import sqlite3

import pytest

from harness.store import Store


def test_persistence_and_atomic_claim(tmp_path):
    path = tmp_path / "harness.sqlite3"
    store = Store(path)
    assert store.create_task("experiment", {"seed": 47})
    assert not store.create_task("experiment", {"seed": 47})
    with pytest.raises(ValueError):
        store.create_task("experiment", {"seed": 99})
    with ThreadPoolExecutor(max_workers=8) as pool:
        claims = list(pool.map(lambda i: store.claim_task("experiment", f"worker-{i}"), range(8)))
    assert sum(claims) == 1
    owner = f"worker-{claims.index(True)}"
    with pytest.raises(ValueError):
        store.finish_task("experiment", "intruder")
    store.finish_task("experiment", owner, result={"auroc": 0.81})
    reopened = Store(path)
    assert reopened.get_task("experiment")["result"] == {"auroc": 0.81}
    assert reopened.get_task("experiment")["payload"] == {"seed": 47}
    assert [e["kind"] for e in reopened.events("experiment")] == ["task_created", "task_claimed", "task_finished"]
    with sqlite3.connect(path) as db:
        assert db.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_index_replaces_stale_chunks_and_preserves_citations(tmp_path):
    store = Store(tmp_path / "harness.sqlite3")
    doc = tmp_path / "evidence.md"
    text = "TCN 제어이력을 검증했습니다. seed 47 완료."
    doc.write_text(text, encoding="utf-8")
    assert store.index_document(doc)
    assert not store.index_document(doc)
    hit = store.search("제어이력")[0]
    assert hit["path"] == str(doc.resolve())
    assert hit["content"] == text
    assert hit["content_hash"] == hashlib.sha256(text.encode()).hexdigest()
    assert hit["document_hash"] == hit["content_hash"]
    assert hit["chunk_id"]
    assert store.search('" OR TCN *')
    assert store.index_document(doc, "Transformer replacement")
    assert store.search("TCN") == []
    assert store.search("replacement")
    assert store.search("   ") == []


def test_chunking_and_literal_query(tmp_path):
    store = Store(tmp_path / "harness.sqlite3")
    store.index_document(tmp_path / "text.md", "abc_def XXXXX", chunk_size=7)
    assert store.search("abc_def")[0]["content"] == "abc_def"
    assert store.search("nomatch") == []
    assert store.search("abc", limit=0) == []
    with pytest.raises(ValueError):
        store.index_document(tmp_path / "text.md", "text", chunk_size=0)


def test_resource_lock_exclusion_and_ownership(tmp_path):
    store = Store(tmp_path / "locks.sqlite3")
    with ThreadPoolExecutor(max_workers=8) as pool:
        claims = list(pool.map(lambda i: store.acquire_resource("output", f"worker-{i}"), range(8)))
    assert sum(claims) == 1
    owner = f"worker-{claims.index(True)}"
    reopened = Store(store.db_path)
    assert not reopened.acquire_resource("output", "another")
    with pytest.raises(ValueError):
        reopened.release_resource("output", "intruder")
    reopened.release_resource("output", owner)
    assert reopened.acquire_resource("output", "another")


def test_pinned_document_chunks_preserve_source_order(tmp_path):
    store = Store(tmp_path / "pin.sqlite3")
    path = tmp_path / "state.json"
    store.index_document(path, "first-second-third", chunk_size=6)
    chunks = store.document_chunks(path)
    assert [chunk["content"] for chunk in chunks] == ["first-", "second"]
    assert all(chunk["path"] == str(path.resolve()) and chunk["content_hash"] for chunk in chunks)
    assert len(store.document_chunks(path, limit=10)) == 3
    assert store.document_chunks(tmp_path / "missing") == []
    store.index_document(path, "new state", chunk_size=6)
    assert [chunk["content"] for chunk in store.document_chunks(path)] == ["new st", "ate"]


def test_removed_sources_cannot_be_retrieved(tmp_path):
    from harness.store import Store
    store = Store(tmp_path / "remove.sqlite3")
    path = tmp_path / "model_suggestion.json"
    store.index_document(path, text="unsupported generated recommendation")
    assert store.search("recommendation")
    assert store.remove_document(path)
    assert not store.remove_document(path)
    assert not store.search("recommendation")
    assert store.events()[-1]["kind"] == "document_removed_from_retrieval"