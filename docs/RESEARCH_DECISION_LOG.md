# Research Decision Log

| Date | Stage | Decision | Evidence | Reason | Next Action |
|---|---|---|---|---|---|
| 2026-08-13 | Phase 2 | Preliminary novelty gate is `PARTIAL_OVERLAP` | Input-output residual monitoring, action-conditioned prediction, and temporal residual statistics all have precedents | The complete industrial combination was not confirmed, but overlap risk is high | Compare the four highest-overlap papers before any proposed model |
| 2026-08-13 | Phase 1 | Capacity confound did not explain F1 result | XMEAS-only F0-C (25,473 params) remained near F0: AUROC 0.7493, AUPRC 0.8989, detection 0.6482; F1: 0.8196, 0.9312, 0.6804 | F0-C matched F1 capacity within 0.60% but not its detection performance | End F0/F1 experiments and enter Phase 2 literature gate |
| 2026-08-13 | Phase 1 | Close F0/F1 gate as `PASS` | F1 detection improvement repeated at model seeds 42, 43, 44 with Seed 42 split fixed | Directional improvement repeated; one capacity check was sufficient | Run F0-C once at Seed 42 |
| 2026-08-13 | Phase 0 | Store telemetry in Parquet/NumPy and experiment metadata in SQLite | Synthetic end-to-end pipeline completed | Avoid placing millions of time-series rows in an RDBMS | Preserve as infrastructure |
| 2026-08-13 | Phase 0 | Preserve synthetic pipeline as `synthetic-pipeline-v0` | Git tag at commit `62d3a1b` | Keep a recoverable baseline before real-data work | Move to real TEP inspection |
| 2026-08-13 | Phase 0 | Do not download all six official Extended TEP mode files | DTU catalog totals about 133 GB | Current research needs a bounded pilot | Inspect smaller preprocessed distribution |
| 2026-08-13 | Phase 0 | Assess AIRI FDDBenchmark `reinartz_tep` | 5.6M rows, 2,800 runs, 41 XMEAS, 11 XMV | Determine whether a small F0/F1 gate is possible | Compatibility audit |
| 2026-08-13 | Phase 0 | Classify `reinartz_tep` as `PARTIALLY_SUITABLE` | Run order/onset/split preserved; XMV12, mode and provenance missing | Limited F0/F1 is possible but claims must be constrained | Run Phase 1 gate |
| 2026-08-13 | Phase 1 | Treat XMV as manipulated-variable history, not causal action | TEP is closed-loop and XMV can be controller response | Prevent causal overclaiming | Test only incremental information value |
| 2026-08-13 | Phase 1 | Compare identical GRU F0/F1 at seed 42 | Master research directive | Isolate the information value of XMV | Smoke, then 30-epoch full pilot |
| 2026-08-13 | Phase 1 | Classify H1 as `PARTIALLY_SUPPORTED` | F1 improved pooled AUROC 0.7508→0.8196, AUPRC 0.8995→0.9312 and delay 51.9→24.6; prediction error changed marginally; effects concentrated in faults 4, 7, 19, 24–26; one seed and 9.1% more parameters | XMV history has useful information for some closed-loop fault responses, but generality and architecture-size independence are not established | Perform Phase-1B fault/XMV/lag and parameter-control analysis before novelty review |
