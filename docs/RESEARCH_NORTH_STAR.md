# Research North Star

## Authoritative current status — 2026-08-14

- Phase 0: complete.
- Phase 1: complete.
- Phase 2: mathematical distinction gate in progress. Current decision is `INCONCLUSIVE` because three of four required full texts were not obtained and the candidate residual is not yet mathematically distinguished.
- Phase 3: not started.

Phase 1 established limited, fault-specific evidence that manipulated-variable history merits follow-up. It did not prove a forecasting method or causal control effect. F1's fault-detection improvement repeated across model seeds 42–44 and was not reproduced by the one F0-C capacity control, while normal future-prediction improvement was inconsistent.

## Research problem

Closed-loop CPS observations mix process dynamics, controller response and fault effects. The long-term question is whether control-history-associated variation can be separated from unexplained deviation, and whether the latter's temporal evolution enables earlier detection.

> Can control-history-associated state variation and unexplained deviation be defined as identifiable components, rather than merely as differences between predictors, and can the unexplained component support earlier fault detection at a controlled false-alarm rate?

## Current candidate — not a proposed method

```text
xhat_0 = f_x(X_t)
xhat_1 = f_xu(X_t, U_t)
c_t    = xhat_1 - xhat_0
e_t    = x_(t+1) - xhat_1
```

- `c_t` is currently only a control-history-associated prediction-difference candidate. It is not a causal control effect.
- `e_t` is currently an ordinary conditional prediction residual.
- The algebraic identity does not establish an identifiable residual decomposition.
- Adding a temporal model, GRU, nonlinear network, CUSUM or sliding window is not novelty by itself.

## Gate decision

The preliminary label `VIABLE_GAP_CANDIDATE` is historical and preserved only in `RESEARCH_DECISION_LOG.md`. The current mathematical gate is `INCONCLUSIVE`:

1. Patel 2018 full text confirms strong overlap in action-conditioned future-observation prediction and prediction-error monitoring.
2. Chen 2016, Mercer 2002 and Ji 2024 full texts were not obtained, so absence of a two-predictor difference cannot be asserted.
3. No concrete learning constraint currently distinguishes `e_t` from existing prediction residuals or makes `c_t` identifiable.

Phase 3 must not begin under this status.

## Data and experiment principles

```text
Raw -> run split -> train-normal selection -> train-only scaler
    -> run-safe windows -> model -> prediction/residual -> evaluation
```

Never fit on test data, tune thresholds on test faults, cross run boundaries, include one run in multiple splits, use future XMV, feed labels/fault IDs to a model, or train a normal model on post-onset samples.

XMV is `MANIPULATED_VARIABLE_HISTORY`, not an independent causal intervention. The current Reinartz TEP data are publicly distributed industrial-process simulation data, not real plant measurements.

## Scope controls

- F0/F1 GRU experiments are closed; no more seeds, hidden dimensions, thresholds, windows or backbones.
- No new model or loss is implemented while Phase 2 is inconclusive.
- RAG, retrieval, recovery-action ranking and new datasets remain outside the current gate.
- SQLite stores reproducibility metadata; time-series telemetry stays in Parquet/NumPy.

## Single next action

Obtain lawful full texts for Chen 2016, Mercer 2002 and Ji 2024, then complete the equation-level comparison. Only a subsequent `DISTINCTION_SURVIVES` decision may authorize exact loss-function design.
