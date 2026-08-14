# Research North Star

## Authoritative current status — 2026-08-14

- Phase 0: complete.
- Phase 1: complete. It established limited evidence that manipulated-variable history merits follow-up study; it did not prove a forecasting method.
- Normal future-prediction improvement was not consistent across seeds.
- Fault-detection improvement repeated across model seeds 42–44 and was not reproduced by the one F0-C capacity control.
- Phase 2: active. Verified literature status is `VIABLE_GAP_CANDIDATE`, with substantial overlap in input-output residual monitoring, action-conditioned prediction, and temporal residual statistics.
- Phase 3 has not started. No proposed model should be implemented until a mathematical distinction from the highest-overlap methods is documented.
- The next question is: what objective distinguishes a learned control-unexplained residual and its evolution from existing CCA/CVA residuals, prediction-error monitors, and CUSUM/sliding-window statistics?

Any older “current phase” wording below is historical context and is superseded by this status block.

## Research problem

Closed-loop CPS state changes mix normal dynamics, controller-induced responses,
and fault-induced deviations. The long-term question is whether variations that are
explainable by control history can be separated from unexplained fault effects, and
whether the temporal evolution of the latter enables earlier detection.

> Can we separate control-explainable state variations from fault-induced
> unexplained deviations in a closed-loop CPS, and detect faults earlier by
> modeling the temporal evolution of the control-unexplained residual?

## Current hypothesis — Phase 1

H1: past manipulated-variable history contains useful information for modeling
normal future system response.

The Information Value Gate compares only:

```text
F0: Past XMEAS       -> same GRU -> Future XMEAS
F1: Past XMEAS + XMV -> same GRU -> Future XMEAS
```

This comparison is a baseline/hypothesis gate, not a thesis contribution.

## Provisional methodological direction

Working names: **Control-Disentangled Residual Evolution Learning (CDREL)** or
**Learning Control-Unexplained Residual Dynamics for Early Fault Detection**.

This is provisional until a literature novelty gate is passed. The repository must
not claim “novel,” “first,” or “state of the art.” Adding XMV, using a GRU,
forecasting residuals, infrastructure, RAG, or combining models is not novelty.

## Research phases

1. Phase 0 — Infrastructure: complete.
2. Phase 1 — Information Value Gate: current. Test H1 with F0/F1.
3. Phase 2 — Literature Novelty Gate: only if Phase 1 supports H1.
4. Phase 3 — Provisional method: only after Phase 2.
5. Later validation — ablation, alternate backbones, multiple datasets.

## Data and experiment principles

```text
Raw -> run split -> train-normal selection -> train-only scaler
    -> run-safe windows -> model -> prediction/residual -> evaluation
```

Never fit on test data, tune thresholds on test faults, cross run boundaries,
include one run in multiple splits, use future XMV, feed labels/fault IDs to a
model, or train a normal model on post-onset samples.

XMV is called `ACTION_CANDIDATE` or `MANIPULATED_VARIABLE_HISTORY`; it is not
assumed to be an independent causal intervention.

## RDBMS policy

SQLite stores reproducibility metadata, not telemetry. Legacy recovery tables stay,
while thesis-core records should represent Dataset, Variable, Run, SplitManifest,
PreprocessProfile, Experiment, ModelRun, Metric, and Artifact. PostgreSQL migration
is out of scope.

## Dataset policy

- Current Phase 1: Reinartz TEP processed distribution only.
- Later: TEP for closed-loop response, GE-UTK for explicit demand/response,
  N-CMAPSS for gradual degradation, HAI for external CPS validation.
- Do not add datasets during the current gate.

## Methodological roadmap (conditional)

Only after H1 support and novelty review:

1. action-conditioned probabilistic normal dynamics;
2. one literature-supported control-response representation;
3. residual decomposition into control-explainable and unexplained components;
4. uncertainty normalization;
5. temporal/inter-variable evolution of the unexplained residual.

## RAG policy

RAG is outside the thesis core. Reconsider only if retrieved process knowledge
directly changes a learning objective or representation and passes its own novelty
review. Document retrieval plus LLM explanation is not a methodological contribution.

## Current stop/pivot conditions

- Clear positive F1 effect: H1 supported; proceed to literature review, not a model.
- Prediction-only or fault-specific effect: H1 partially supported; analyze lag,
  useful XMV, affected sensors, delta-XMV, controller response, and parameter count.
- No effect/worse F1: H1 not supported; do not build CDREL. Revisit semantics, lag,
  missing XMV12, processed-data limitations, and official DTU Mode 1.

Current implementation stops after seed-42 F0/F1 smoke/full results, fault-level
results, leakage evidence, and an H1 decision.

## Phase status update — 2026-08-13

- Phase 1 Information Value Gate: **complete (`PASS`)**.
- F1 detection improvement repeated across model seeds 42, 43, and 44 using the fixed Seed 42 split.
- XMEAS-only F0-C matched F1 model capacity within 0.60% but remained near F0 detection performance.
- No further F0/F1 seeds, hidden dimensions, thresholds, windows, or backbones will be tested in this phase.
- Phase 2 Literature Novelty Gate: **current (`PARTIAL_OVERLAP` preliminary)**.
- The next research question is whether prior input-output residual monitoring and action-conditioned prediction already cover the proposed distinction between control-explainable response and temporally evolving unexplained residual.
- No proposed model is implemented until the highest-overlap papers are compared in detail.
