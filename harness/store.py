"""Durable local harness state and citation-bearing lexical retrieval.

Retrieved content is untrusted evidence, never executable instructions. Each
operation opens its own SQLite connection so workers may share a Store safely.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import sqlite3
from typing import Iterator


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class Store:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    kind TEXT NOT NULL, task_id TEXT, payload TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY, status TEXT NOT NULL,
                    worker_id TEXT, payload TEXT NOT NULL, result TEXT,
                    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                );
                CREATE TABLE IF NOT EXISTS resource_locks (
                    resource TEXT PRIMARY KEY, owner TEXT NOT NULL,
                    acquired_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
                );
                CREATE TABLE IF NOT EXISTS documents (
                    path TEXT PRIMARY KEY, content_hash TEXT NOT NULL,
                    chunk_size INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY, path TEXT NOT NULL,
                    content TEXT NOT NULL, content_hash TEXT NOT NULL,
                    document_hash TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS chunks_path ON chunks(path);
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                    chunk_id UNINDEXED, content, tokenize='unicode61'
                );
            """)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.db_path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _event(db, kind, payload, task_id=None):
        return db.execute(
            "INSERT INTO events(kind, task_id, payload) VALUES (?, ?, ?)",
            (kind, task_id, _json(payload)),
        ).lastrowid

    def append_event(self, kind: str, payload: object, task_id: str | None = None) -> int:
        with self._connection() as db:
            return self._event(db, kind, payload, task_id)

    def events(self, task_id: str | None = None) -> list[dict]:
        with self._connection() as db:
            rows = db.execute(
                "SELECT * FROM events WHERE (? IS NULL OR task_id=?) ORDER BY id",
                (task_id, task_id),
            ).fetchall()
        return [{**dict(row), "payload": json.loads(row["payload"])} for row in rows]

    def create_task(self, task_id: str, payload: object, status: str = "pending") -> bool:
        """Create once; reject duplicate IDs with conflicting payloads."""
        with self._connection() as db:
            inserted = db.execute(
                "INSERT OR IGNORE INTO tasks(task_id,status,payload) VALUES (?,?,?)",
                (task_id, status, _json(payload)),
            ).rowcount == 1
            if inserted:
                self._event(db, "task_created", {"status": status}, task_id)
            elif db.execute("SELECT payload FROM tasks WHERE task_id=?", (task_id,)).fetchone()[0] != _json(payload):
                raise ValueError(f"Task {task_id!r} already exists with a different payload")
            return inserted

    def close(self) -> None:
        """Compatibility hook; operations already close their connections."""

    @staticmethod
    def _task(row) -> dict | None:
        if row is None:
            return None
        return {**dict(row), "payload": json.loads(row["payload"]),
                "result": json.loads(row["result"]) if row["result"] is not None else None}

    def get_task(self, task_id: str) -> dict | None:
        with self._connection() as db:
            return self._task(db.execute("SELECT * FROM tasks WHERE task_id=?", (task_id,)).fetchone())

    def list_tasks(self, status: str | None = None) -> list[dict]:
        with self._connection() as db:
            return [self._task(row) for row in db.execute(
                "SELECT * FROM tasks WHERE (? IS NULL OR status=?) ORDER BY task_id", (status, status))]

    def claim_task(self, task_id: str, worker_id: str) -> bool:
        """Only one worker can atomically claim a pending task."""
        if not worker_id:
            raise ValueError("worker_id must be nonempty")
        with self._connection() as db:
            claimed = db.execute("""
                UPDATE tasks SET status='running', worker_id=?,
                    updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
                WHERE task_id=? AND status='pending'
            """, (worker_id, task_id)).rowcount == 1
            if claimed:
                self._event(db, "task_claimed", {"worker_id": worker_id}, task_id)
            return claimed

    def finish_task(self, task_id: str, worker_id: str, status: str = "completed", result=None) -> None:
        if status not in {"completed", "failed", "blocked"}:
            raise ValueError("finish status must be completed, failed, or blocked")
        with self._connection() as db:
            changed = db.execute("""
                UPDATE tasks SET status=?, result=?,
                    updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
                WHERE task_id=? AND status='running' AND worker_id=?
            """, (status, _json(result), task_id, worker_id)).rowcount
            if not changed:
                raise ValueError("Task is not running or belongs to another worker")
            self._event(db, "task_finished", {"worker_id": worker_id, "status": status, "result": result}, task_id)

    def acquire_resource(self, resource: str, owner: str) -> bool:
        """Exclusive persistent lock. Crash recovery requires manual inspection."""
        if not resource or not owner:
            raise ValueError("resource and owner must be nonempty")
        with self._connection() as db:
            acquired = db.execute(
                "INSERT OR IGNORE INTO resource_locks(resource,owner) VALUES (?,?)",
                (resource, owner),
            ).rowcount == 1
            if acquired:
                self._event(db, "resource_acquired", {"resource": resource, "owner": owner})
            return acquired

    def release_resource(self, resource: str, owner: str) -> None:
        with self._connection() as db:
            changed = db.execute(
                "DELETE FROM resource_locks WHERE resource=? AND owner=?", (resource, owner)
            ).rowcount
            if not changed:
                raise ValueError("Resource is not locked or belongs to another owner")
            self._event(db, "resource_released", {"resource": resource, "owner": owner})

    def remove_document(self, path: str | Path) -> bool:
        """Remove an ineligible source from retrieval, retaining the audit event."""
        key = str(Path(path).resolve())
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            if not db.execute("SELECT 1 FROM documents WHERE path=?", (key,)).fetchone():
                return False
            db.execute("DELETE FROM chunks_fts WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE path=?)", (key,))
            db.execute("DELETE FROM chunks WHERE path=?", (key,))
            db.execute("DELETE FROM documents WHERE path=?", (key,))
            self._event(db, "document_removed_from_retrieval", {"path": key})
            return True

    def index_document(self, path: str | Path, text: str | None = None, chunk_size: int = 1600) -> bool:
        """Replace a document's chunks atomically only when content or sizing changes."""
        if chunk_size < 1:
            raise ValueError("chunk_size must be positive")
        source = Path(path).resolve()
        if text is None:
            text = source.read_text(encoding="utf-8-sig")
        key, digest = str(source), _hash(text)
        with self._connection() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT * FROM documents WHERE path=?", (key,)).fetchone()
            if old and old["content_hash"] == digest and old["chunk_size"] == chunk_size:
                return False
            db.execute("DELETE FROM chunks_fts WHERE chunk_id IN (SELECT chunk_id FROM chunks WHERE path=?)", (key,))
            db.execute("DELETE FROM chunks WHERE path=?", (key,))
            db.execute("INSERT OR REPLACE INTO documents VALUES (?,?,?)", (key, digest, chunk_size))
            for offset in range(0, len(text), chunk_size):
                content = text[offset:offset + chunk_size]
                chunk_id = _hash(f"{key}\n{digest}\n{offset}\n{chunk_size}")
                db.execute("INSERT INTO chunks VALUES (?,?,?,?,?)", (chunk_id, key, content, _hash(content), digest))
                db.execute("INSERT INTO chunks_fts VALUES (?,?)", (chunk_id, content))
            self._event(db, "document_indexed", {"path": key, "content_hash": digest})
            return True

    def document_chunks(self, path: str | Path, limit: int = 2) -> list[dict]:
        """Read a pinned document's evidence chunks in source order.

        A zero score marks explicit retrieval rather than a ranked search hit.
        Indexing inserts chunks in source order inside a single transaction.
        """
        if limit <= 0:
            return []
        with self._connection() as db:
            return [dict(row) for row in db.execute(
                "SELECT *, 0.0 AS score FROM chunks WHERE path=? ORDER BY rowid LIMIT ?",
                (str(Path(path).resolve()), limit),
            )]

    def search(self, query: str, limit: int = 5) -> list[dict]:
        """FTS ranking plus substring fallback for Korean inflections.

        Scores rank results within this query only; they are not confidence.
        Queries are converted to literal tokens, never interpreted as FTS syntax.
        """
        tokens = list(dict.fromkeys(re.findall(r"\w+", query.lower(), flags=re.UNICODE)))
        if not tokens or limit <= 0:
            return []
        match = " OR ".join('"' + token.replace('"', '""') + '"' for token in tokens)
        with self._connection() as db:
            rows = db.execute("""
                SELECT c.*, -bm25(chunks_fts) AS score
                FROM chunks_fts JOIN chunks c ON c.chunk_id=chunks_fts.chunk_id
                WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts), c.chunk_id LIMIT ?
            """, (match, limit)).fetchall()
            found = {row["chunk_id"]: dict(row) for row in rows}
            # SQL LIKE provides partial Korean matches without dependencies or embeddings.
            predicates = " OR ".join("lower(content) LIKE ? ESCAPE '\\'" for _ in tokens)
            patterns = ["%" + token.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%" for token in tokens]
            for row in db.execute(f"SELECT * FROM chunks WHERE {predicates}", patterns):
                item = dict(row)
                coverage = sum(token in item["content"].lower() for token in tokens) / len(tokens)
                item["score"] = coverage + found.get(item["chunk_id"], {}).get("score", 0.0)
                found[item["chunk_id"]] = item
        return sorted(found.values(), key=lambda item: (-item["score"], item["chunk_id"]))[:limit]
