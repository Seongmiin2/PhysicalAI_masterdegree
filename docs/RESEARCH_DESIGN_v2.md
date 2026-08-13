# Research Design v2 — implementation reference

The full source document is `MS_Thesis_Industrial_CPS_Research_Design_v2.md`
(supplied outside this repository on 2026-08-13). This repository implements its
TEP-first bounded milestone.

Core research question: learn the expected response of an industrial CPS from
state, action, and operating context, then model how residual relations evolve
toward a fault. The implementation adds recovery decision episodes:

```text
Current State + Fault + Candidate Recovery Action
    -> Success / Failure / Unsafe
```

Research constraints retained from v2:

- split by run/episode before windowing;
- fit scalers on training data only;
- never use future actions as model inputs;
- keep raw telemetry out of the RDBMS;
- store telemetry in Parquet/NumPy and reproducibility metadata in a relational DB;
- do not make novelty, SOTA, or real-system effectiveness claims from pilot data;
- begin with minimal GRU/TCN baselines before adding complex models.

See `IMPLEMENTATION_PLAN.md` for the executable milestone and storage contract.
