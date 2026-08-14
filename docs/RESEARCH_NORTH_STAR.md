# Research North Star

## Authoritative current status — 2026-08-14

- Phase 0: complete.
- Phase 1: complete.
- Phase 2: mathematical distinction gate remains `INCONCLUSIVE`; mechanism audit is complete.
- Phase 3: not started.

Phase 1 established limited, fault-specific evidence that manipulated-variable history merits follow-up. It did not prove a forecasting method or causal control effect. F1's fault-detection improvement repeated across model seeds 42–44 and was not reproduced by the one F0-C capacity control, while normal future-prediction improvement was inconsistent.

## Research problem

> Can control-history-associated state variation and unexplained deviation be defined as identifiable components, rather than merely as differences between predictors, and can the unexplained component support earlier fault detection at a controlled false-alarm rate?

## Current candidate — not a proposed method

```text
xhat_0 = f_x(X_t)
xhat_1 = f_xu(X_t, U_t)
c_t    = xhat_1 - xhat_0
e_t    = x_(t+1) - xhat_1
```

- `c_t` is a control-history-associated prediction difference, not an identified or causal control effect.
- `e_t` is currently an ordinary input-conditioned prediction residual.
- A temporal model, GRU, nonlinear network, CUSUM or sliding window is not novelty by itself.

## Current evidence

- Chen 2016 full text is now verified. Static Eq. (1)/(9) defines `r(k)=L^Ty(k)-M^Tu(k)`. Dynamic Eq. (24) defines a residual between transformed future outputs and a term conditioned on past input/output plus future inputs.
- Chen therefore strongly overlaps with `e_t` as an input-conditioned prediction residual, but does not contain a sensor-only/input-conditioned two-predictor difference `c_t` or a separately learned residual-evolution model.
- Patel 2018 also confirms action-conditioned future prediction and prediction-error monitoring.
- Mercer 2002 and Ji 2024 remain `ABSTRACT_ONLY` after renewed lawful-full-text search.
- No concrete constraint currently makes `c_t/e_t` an identifiable decomposition.

## Gate decision

The mathematical gate remains `INCONCLUSIVE`. Chen reduces uncertainty but does not justify `DISTINCTION_SURVIVES`: `e_t` has clear prior-art overlap and `c_t` is not yet mathematically identified. Missing Mercer/Ji full texts prevent a complete four-paper exclusion test.

Phase 3 must not begin under this status.

## Data and experiment principles

```text
Raw -> run split -> train-normal selection -> train-only scaler
    -> run-safe windows -> model -> prediction/residual -> evaluation
```

Never fit on test data, tune thresholds on test faults, cross run boundaries, use future XMV, feed labels to a model, or train a normal model on post-onset samples. XMV is `MANIPULATED_VARIABLE_HISTORY`, not an independent causal intervention. Reinartz TEP is public industrial-process simulation data, not real plant measurements.

## Scope controls

- F0/F1 experiments are closed; no more seeds, thresholds, windows or backbones.
- No new model or loss while Phase 2 is inconclusive.
- RAG, retrieval, recovery-action ranking and new datasets remain outside this gate.

## Single next action

Obtain lawful full texts for Mercer 2002 and Ji 2024, then complete their equation-level comparison. Only a later `DISTINCTION_SURVIVES` decision may authorize exact loss-function design.

## Mechanism and direction audit (2026-08-14)

- Candidate A: `INCONCLUSIVE / NOT ADOPTED`.
- Candidate B: `PROMISING_MODEL_CANDIDATE / NOT YET AUTHORIZED`.
- Candidate C: technically feasible via the Python simulator, but scientific feasibility remains untested.
- F1 mechanism: `MIXED_MECHANISM`, dominated by fault-specific XMV patterns and early-warning behavior in faults 19, 24, 25, and 26. Normal-context improvement was not supported.
- Primary route: mechanism-first Reinartz analysis. Fallback: a small paired, same-seed Python-simulator study.

The next single action is a preregistered, no-training Path-1 diagnostic protocol with run-level falsification criteria. No Candidate B/C model or loss is authorized. Mercer/Ji verification remains required before any mathematical novelty claim.
