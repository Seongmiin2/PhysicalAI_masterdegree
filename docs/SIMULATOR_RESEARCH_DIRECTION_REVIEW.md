# Simulator and Research-Direction Review

## Decision summary

- Mechanism verdict: `MIXED_MECHANISM`
- Simulator verdict: `SIMULATOR_READY_WITH_MINOR_WORK`
- Primary path: **Path 1 — Reinartz mechanism-first control-response analysis**
- Fallback path: **Path 3 — paired simulator-supervised decomposition pilot**
- Candidate B remains `PROMISING_MODEL_CANDIDATE / NOT YET AUTHORIZED`.
- Candidate C becomes technically feasible, but no simulator dataset or model is authorized by this review.

## Simulator audit

### `jkitchin/tennessee-eastman-profbraatz`

| Item | Finding |
|---|---|
| License | BSD-3-Clause |
| Windows dependency | Python 3.8+ and NumPy; the pure-Python backend needs no compiler. Optional Fortran acceleration needs gfortran, which is not currently found on this PC. |
| Controller exposure | Closed-loop decentralized PI implementation, 20 setpoints, controller state, and controller plugin interface are accessible in Python. |
| Signals | 41 XMEAS, 12 XMV, and 50 internal process states are returned separately. XMV is the applied manipulated-variable/valve-position history; controller calculations and setpoints are inspectable in code. |
| Faults/modes | 20 original disturbances and open-loop, closed-loop, and manual control. This is not the same 28-fault/multimode universe as Reinartz. |
| Reproducibility | Explicit random seed; same-seed normal/fault paired runs are possible. |
| Reinartz compatibility | Core 41 XMEAS and XMV1–11 align conceptually; the simulator additionally exposes XMV12. Exact distributions, controllers, preprocessing, fault IDs above 20, and provenance do not match automatically. |

A bounded Windows smoke test used the Python backend only: one 0.1-hour normal run and one fault-1 run with seed 12345. Both completed without shutdown and returned `(37,41)` XMEAS, `(37,12)` XMV, and `(37,50)` states. The paired trajectories were exactly equal before the scheduled onset and diverged afterward. This establishes execution feasibility, not scientific validity or Reinartz equivalence.

### `ElsevierSoftwareX/SOFTX-D-24-00664` (COSTEP)

| Item | Finding |
|---|---|
| License | MIT |
| Windows dependency | MATLAB and Simulink are required by the `.m`/`.slx` workflow; MATLAB is not currently found on this PC. No purchase or heavy installation was attempted. |
| Controller exposure | Open-loop, Braatz, Ricker, and custom controller modes are described; seed and disturbance blocks are configurable. |
| Signals | Documentation and automation script export measured variables, manipulated variables/actuator settings (`XMV0`), and other simulation outputs. Internal Simulink blocks offer richer intervention access, but exact logging separation requires MATLAB-side inspection. |
| Paired runs | Noise seed is configurable, so paired normal/fault design appears possible; it was not executed because the required runtime is absent. |
| Reinartz compatibility | Potentially map-able at XMEAS/XMV level, but controller configuration, sampling, fault definitions, and preprocessing require an explicit adapter and equivalence audit. |

COSTEP is therefore not the immediate implementation choice on this machine. Its richer Simulink model remains a later cross-check if a licensed runtime becomes available.

## Route comparison

Scores are 1 (poor) to 5 (strong). For risk, 5 means low risk.

| Criterion | Path 1: Reinartz analysis | Path 2: nested correction | Path 3: simulator-supervised |
|---|---:|---:|---:|
| Research-question clarity | 4 | 3 | 5 |
| Potential mathematical distinction | 3 | 3 | 5 |
| Link to Phase 1 evidence | 5 | 4 | 4 |
| Current implementation feasibility | 5 | 4 | 3 |
| Master's timeline fit | 5 | 4 | 3 |
| Reproducibility | 5 | 4 | 4 |
| Low scientific/engineering risk | 4 | 3 | 3 |
| Reinartz compatibility | 5 | 5 | 3 |
| Industrial applicability | 4 | 4 | 5 |
| **Total / 45** | **40** | **34** | **35** |

## Recommendation

**Primary — Path 1.** First turn the mechanism audit into a falsifiable question on existing data: does the onset-aligned, fault-specific XMV response add early information beyond lagged XMEAS without claiming causal decomposition? This path is closest to verified Phase 1 evidence, lowest risk, and does not depend on an unproven loss.

**Fallback — Path 3.** If the thesis requires a true control/fault decomposition, use the Python simulator for a small paired-identical-seed feasibility study. The simulator can expose state, measurement, setpoint, and applied XMV histories and can create normal/fault pairs. The resulting labels would be simulator-defined supervision, not ground truth for Reinartz or a real plant; transfer and circularity must be tested explicitly.

Path 2 is deferred. A nested architecture solves predictor comparability better than independent F0/F1, but the present audit finds no identified target for its correction branch. Implementing it now would convert an interpretation problem into an architectural assumption.

## Single next research task

Write a preregistered, no-training diagnostic protocol for Path 1: define onset-relative XMV lead features, an XMEAS-only comparator, run-level evaluation, and falsification criteria on the fixed Reinartz split. Do not design a new loss until that protocol decides whether the extra signal is merely fault-label leakage through controller response or a generalizable early-warning relation.
