# F1 Mechanism Audit

## Scope and status

This audit reuses the fixed Seed 42 split, scaler, thresholds, F0 checkpoint, and F1 checkpoint. It performs inference and descriptive analysis only; no model was trained and no threshold was changed.

- Candidate A (independent F0/F1 prediction difference): `INCONCLUSIVE / NOT ADOPTED`
- Candidate B (nested correction): `PROMISING_MODEL_CANDIDATE / NOT YET AUTHORIZED`
- Candidate C (simulator-supervised decomposition): `FEASIBILITY_NOT_TESTED`

The historical Candidate A gate documents remain authoritative records and were not edited by this audit.

## Method

The audit covers the 120 fixed test runs for faults 4, 7, 19, 24, 25, and 26 (20 runs each). For every run it compares samples 400–599 with the first 300 post-onset samples (onset 600). XMEAS and XMV use the existing train-only scaler. A variable-change alarm is the first three-sample persistence above the fault-specific pre-onset 99th percentile. Model alarms retain the existing validation-normal threshold and alarm policy.

The XMV-only diagnostic is deliberately lightweight: Euclidean XMV level deviation from each run's pre-onset median and first-difference magnitude. It is not a new fault classifier. Lag correlations are descriptive and cannot establish controller causality.

## Results

| Fault | XMV-only early AUROC | XMV change delay | XMEAS change delay | XMV leads XMEAS | F0 alarm delay | F1 alarm delay | F1 earlier |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 0.997 | 2.0 | 2.0 | 1/20 | 2.0 | 2.0 | 0/20 |
| 7 | 0.997 | 2.0 | 2.0 | 0/20 | 2.0 | 2.0 | 0/20 |
| 19 | 0.991 | 6.0 | 58.5 | 20/20 | 76.5 | 28.0 | 20/20 |
| 24 | 0.978 | 13.0 | 15.5 | 12/20 | 23.0 | 15.0 | 16/20 |
| 25 | 0.954 | 13.5 | 54.0 | 20/20 | 236.0 | 25.5 | 20/20 |
| 26 | 0.947 | 21.5 | 116.5 | 19/20 | 1070.5 | 29.0 | 20/20 |

The strongest early XMV shifts are fault-specific and concentrated: XMV10 for fault 4 (82.0% of aggregate absolute shift), XMV4 for fault 7 (93.6%), XMV8/XMV7 for fault 19 (54.3%/35.2%), XMV1 for fault 24 (44.5%), XMV2 for fault 25 (54.2%), and XMV4 for fault 26 (60.5%). The top three XMV variables explain 70.4–96.5% of the early shift for every audited fault.

Normalized pre-onset F0 and F1 scores are essentially equal (approximately 0.604–0.608 of their respective thresholds), so this audit does not support the claim that F1 mainly learns a better normal operating context. After onset, F1 scores separate much more strongly. Faults 19, 25, and 26 show the clearest sequence: an XMV change precedes the XMEAS change and F1 alarms substantially earlier than F0. Fault 24 is mixed; faults 4 and 7 change nearly simultaneously and improve ranking rather than alarm time.

Best aggregate XMV–XMEAS lag correlations occur mostly at lag 0 or -2 samples. These correlations are compatible with coupled closed-loop response but do not identify whether the disturbance, controller response, or process response is the cause.

## Verdict

**`MIXED_MECHANISM`**

The dominant supported components are `FAULT_SPECIFIC_XMV_PATTERN` and, for faults 19/24/25/26, `XMV_EARLY_WARNING_SIGNAL`. `XMV_NORMAL_CONTEXT` is not supported by the observed pre-onset scores. This means F1's gain is real as predictive information in these runs, but it must not be relabeled as an identified control effect.

## Artifacts and limitations

- `artifacts/tables/reinartz_f1_mechanism_summary.csv`
- `artifacts/tables/reinartz_f1_xmv_feature_ranking.csv`
- `artifacts/tables/reinartz_f1_mechanism_runs.csv`
- `artifacts/figures/reinartz_f1_mechanism_onset.png`
- Reproducible command: `python -m src.analysis.reinartz_f1_mechanism`

Reinartz lacks controller setpoints, controller errors, explicit controller outputs distinct from XMV, XMV12, operating mode, and paired counterfactual trajectories. Therefore this dataset cannot identify a physical decomposition of control-caused and fault-caused variation by itself.
