"""Run using python -m harness."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

from .runtime import ROOT, deliberate, execute, index_evidence, record_human_decision, refresh_work_state
from .store import Store


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=ROOT / "outputs/harness/research.sqlite3")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("index")
    sub.add_parser("status")
    search = sub.add_parser("search")
    search.add_argument("query")
    ask = sub.add_parser("ask")
    ask.add_argument("question")
    route = sub.add_parser("route", help="Opt-in fine-tuned router; never executes a suggestion")
    route.add_argument("records", type=Path, help="Project dataset JSONL file")
    route.add_argument("--row", type=int, default=0)
    route.add_argument("--query", help="Optionally append retrieved evidence; experimental input mode")
    decision = sub.add_parser("decision")
    decision.add_argument("request_id")
    decision.add_argument("decision", choices=["accept", "reject", "revise"])
    decision.add_argument("--reason", required=True)
    run = sub.add_parser("run")
    run.add_argument("mode", choices=["dry-run", "smoke", "pilot"])
    run.add_argument("--python", type=Path, default=Path(sys.executable))
    run.add_argument("--max-tasks", type=int, default=1)
    run.add_argument("--profile", choices=["main", "pilot"], default="main")
    run.add_argument("--timeout-seconds", type=float, default=14400)
    args = parser.parse_args()
    store = Store(args.db)
    if args.command == "index":
        result = index_evidence(store)
    elif args.command == "status":
        events = store.events()
        refresh_work_state(ROOT)
        tasks = [{"task_id": t["task_id"], "status": t["status"], "updated_at": t["updated_at"],
                  "profile": t["payload"].get("profile"), "mode": t["payload"].get("mode")} for t in store.list_tasks()]
        result = {"tasks": tasks, "event_count": len(events), "recent_events": [{k: e[k] for k in ("id", "created_at", "kind", "task_id")} for e in events[-10:]]}
    elif args.command == "search":
        result = store.search(args.query)
    elif args.command == "ask":
        from providers.local import LocalProvider
        result = deliberate(store, LocalProvider(), args.question)
    elif args.command == "route":
        from providers.finetuned import FineTunedProvider, record_text
        records = [json.loads(line) for line in args.records.read_text(encoding="utf-8").splitlines() if line.strip()]
        if not 0 <= args.row < len(records):
            parser.error("row must identify an existing JSONL record")
        record = {"text": record_text(records[args.row])}
        evidence = store.search(args.query, limit=3) if args.query else []
        if evidence:
            record["text"] += "\nRetrieved references:\n" + "\n".join(e["content"] for e in evidence)
        request_record = {"source": str(args.records.resolve()), "row": args.row,
                          "input_sha256": hashlib.sha256(record["text"].encode()).hexdigest(),
                          "retrieved_chunk_ids": [e["chunk_id"] for e in evidence]}
        store.append_event("finetuned_routing_started", request_record)
        try:
            result = FineTunedProvider().route(record)
        except Exception as exc:
            store.append_event("finetuned_routing_failed", {**request_record, "error": str(exc)})
            raise
        result["retrieved_chunk_ids"] = request_record["retrieved_chunk_ids"]
        store.append_event("finetuned_routing_completed", {**request_record, "result": result})
    elif args.command == "decision":
        result = record_human_decision(store, args.request_id, args.decision, args.reason)
    else:
        result = execute(store, args.python, args.mode, args.max_tasks, timeout_seconds=args.timeout_seconds, profile=args.profile)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if isinstance(result, dict) and result.get("status") == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
