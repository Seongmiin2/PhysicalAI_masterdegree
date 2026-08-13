# TEP-first Recovery Episode Pipeline

## Today's bounded scope

- Main domain: Tennessee Eastman Process (TEP/COSTEP semantics)
- Remote datasets downloaded: none
- Default source: deterministic synthetic TEP-like recovery episodes
- Telemetry: Parquet and windowed NumPy (`.npz`)
- Relational metadata: SQLite (`db/experiment.db`)
- Baseline: GRU state encoder with recovery success prediction

The official Extended TEP collection is about 132.96 GB. The baseline therefore
creates only a source manifest. A later, explicit acquisition step must select a
small official subset instead of using “download all.”

## End-to-end flow

```text
baseline.yaml
  -> recovery episode simulator
  -> raw telemetry.parquet + episodes.jsonl
  -> episode-level split (no window leakage)
  -> train-only standard scaling
  -> windows.npz + processed telemetry.parquet
  -> GRU state encoder
  -> checkpoint + metrics + experiment status
```

## Recovery semantics

`RecoveryEpisode` contains operating mode, fault, current state, candidate action,
action sequence, success, recovery time, constraint violation, unsafe state, and
applicability. Child tables retain fault events, actions, and outcomes. Model runs
and metrics point back to an experiment.

This is a research scaffold. Synthetic success labels validate data and execution
contracts; they are not evidence of effectiveness on real TEP data.
