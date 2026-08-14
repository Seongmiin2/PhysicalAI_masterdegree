# XMV Early-Warning Diagnostic Preregistration

## Registration status

- Registered: 2026-08-14, before running or inspecting the all-fault test diagnostic.
- Scope: no-training diagnostic on the frozen Reinartz split.
- This document fixes the analysis before any test result is generated. It may be corrected only for an implementation error that makes execution impossible; any correction requires a dated amendment and invalidates confirmatory status for the affected rule.
- Existing six-fault mechanism-audit results motivated this question but are not used to choose features, variables, weights, thresholds, shifts, or decision cutoffs below.

## 1. Validation question

Does past manipulated-variable history contain an onset-independent early-warning relation that repeats across many faults and held-out runs, beyond an XMEAS-only change score, or is the apparent gain concentrated in a small set of controller/fault signatures or likely fault-label leakage?

The protocol distinguishes exactly five outcomes: `GENERALIZABLE_EARLY_WARNING`, `FAULT_SPECIFIC_CONTROLLER_SIGNATURE`, `LIKELY_FAULT_LABEL_LEAKAGE`, `NO_RELIABLE_XMV_EARLY_SIGNAL`, and `INCONCLUSIVE`. It does not identify a causal control effect.

## 2. Data and frozen split

- Dataset: existing FDDBenchmark `reinartz_tep`, 41 XMEAS and 11 XMV, 2,000 ordered samples per run, 28 fault IDs.
- Time: one sample is 3 minutes. Every reported delay is in samples and minutes (`minutes = 3 × samples`).
- Split: use the exact existing Reinartz train/validation/test run manifests. Do not regenerate, rebalance, or stratify the split.
- Calibration population: existing train-normal samples for location/scale; existing validation-normal samples for score calibration and thresholds.
- Evaluation population: every run in the frozen test split and all 28 fault IDs. Fault onset and labels are read only after scores and alarms have been produced, solely to calculate metrics.
- Windows and deltas are computed within a run. No operation may cross a run boundary.

Before execution, the script must print and save hashes of the split manifest, configuration, and this preregistration. A mismatch is a stop condition.

## 3. Fixed feature and score definitions

All 41 XMEAS and all 11 XMV are used. There is no fault-specific feature selection, channel selection, or weighting.

For modality `M ∈ {XMEAS, XMV}`, estimate per-channel train-normal mean `μ_M`, standard deviation `σ_M`, delta mean `μ_ΔM`, and delta standard deviation `σ_ΔM`. Standard deviations below `1e-8` are replaced by `1.0` and reported. Define, using only current and past samples:

```text
z_M(t,i)  = (M(t,i) - μ_M(i)) / σ_M(i)
dz_M(t,i) = ((M(t,i) - M(t-1,i)) - μ_ΔM(i)) / σ_ΔM(i)
q_M(t)    = 0.5 * mean_i(z_M(t,i)^2) + 0.5 * mean_i(dz_M(t,i)^2)
s_M(t)    = mean(q_M(t-2), q_M(t-1), q_M(t))
```

The first two samples of every run have no score. The three-sample mean is the only persistence feature. Equal channel weights and the 0.5/0.5 level/delta weights are fixed.

Use validation-normal data to robustly calibrate each modality score:

```text
r_M(t) = (s_M(t) - median_val(s_M)) /
         max(1.4826 * MAD_val(s_M), 1e-8)
```

The three preregistered scores are:

1. **XMEAS-only:** `S_X(t) = r_XMEAS(t)`
2. **XMV-only:** `S_U(t) = r_XMV(t)`
3. **XMEAS+XMV:** `S_XU(t) = 0.5*r_XMEAS(t) + 0.5*r_XMV(t)`

No future XMV, learned parameter, classifier, fault label, onset, or fault-specific statistic enters these definitions.

## 4. Threshold and alarm policy

- For each of the three scores, set one global threshold to its pooled validation-normal 99th percentile.
- A run alarm is the first time the score is at or above its fixed threshold for three consecutive scored samples (9 minutes).
- Thresholds are not fault-specific, run-specific, or recomputed on test data.
- Report validation-normal sample false-alarm rate and run false-alarm rate before unlocking test labels. If the sample false-alarm rate exceeds 1.5% or the run false-alarm rate exceeds 10%, stop and report `INCONCLUSIVE`; do not adjust the threshold.
- AUROC/AUPRC use the continuous scores. Binary detection and delay use the fixed alarm rule.

The 99th percentile matches the established baseline policy; three-sample persistence limits isolated spikes without selecting a fault-dependent window.

## 5. Fixed negative controls

All controls reuse the original train-normal scaler and validation-normal thresholds. They do not refit or recalibrate anything. Control mappings are generated without reading test labels or onset.

### 5.1 XMV run-shuffle

Sort test run IDs and validation-normal donor run IDs lexicographically. Map test run `k` to donor `(k + 17) mod N`, rejecting identity and taking the next donor if necessary. Repeat the donor's complete normal XMV sequence cyclically to the required test-run length, then truncate. This joins a different normal run's XMV to the unchanged test XMEAS and removes fault-responsive XMV while preserving realistic normal within-run dynamics. The offset 17 is fixed independently of results.

### 5.2 XMV causal time shifts

Evaluate two delays only: 5 samples (15 minutes) and 20 samples (60 minutes). At time `t`, use XMV from `t-5` or `t-20`; fill the unavailable prefix with the first observed XMV vector of that same run. Do not wrap, interpolate, or use future XMV. Both delays must be reported separately; their median change is used in the Gate.

### 5.3 XMV variable permutation

Before applying the frozen channel-specific scaler, use the single global raw-channel rotation

```text
[XMV04, XMV05, XMV06, XMV07, XMV08, XMV09,
 XMV10, XMV11, XMV01, XMV02, XMV03]
```

in place of `[XMV01, ..., XMV11]` for every run and sample. No alternate permutation is tried. Because this intentionally mismatches channel identity and its frozen normal calibration, it is a sensitivity control, not a realistic deployment condition.

### 5.4 XMV-only diagnostic

Use `S_U` exactly as defined above. Report its pooled and fault-specific metrics. Do not select the best XMV, train a fault classifier, or infer fault identity from the score.

## 6. Evaluation metrics

Report for `S_X`, `S_U`, and `S_XU`, and for every control where applicable:

- pooled sample AUROC and AUPRC over all test faults;
- macro mean and median fault-level AUROC/AUPRC across all 28 faults;
- run detection rate;
- median and IQR detection delay among successfully detected runs, in samples and minutes;
- fraction of paired runs where the XMV-only alarm precedes the XMEAS-only alarm; a missing alarm is treated as `+∞`, while two missing alarms are excluded from the lead denominator and counted separately;
- all fault-level metrics and sample/run counts, including failures;
- validation-normal sample and run false-alarm rates;
- `ΔAUPRC_f = AUPRC_XU,f - AUPRC_X,f` for every fault;
- concentration: fraction of total positive `ΔAUPRC_f` attributable to the seven largest positive fault gains; if no gain is positive, concentration is zero;
- channel concentration as a descriptive result only: share of aggregate post-onset absolute standardized XMV deviation in the three largest channels, using the same three channels globally ranked on pooled test runs, never fault-specific;
- control degradation: original minus control AUROC, AUPRC, run detection rate, and XMV-lead fraction.

The primary effect measures are macro fault AUPRC gain of `S_XU` over `S_X`, the all-run XMV-lead fraction, the number of qualifying faults, and degradation under run-shuffle and the median of the two causal time shifts.

## 7. Numerical Gate fixed before results

Apply the outcomes in the following precedence order. A criterion must be fully met; values exactly on a boundary count as meeting it.

### `GENERALIZABLE_EARLY_WARNING`

All conditions must hold:

1. validation-normal sample false-alarm rate ≤1.5% and run false-alarm rate ≤10%;
2. `S_XU - S_X` macro fault AUPRC gain ≥0.03 and macro fault AUROC gain ≥0.02;
3. at least 14 of 28 faults have AUPRC gain ≥0.02;
4. XMV precedes XMEAS in ≥60% of eligible runs overall and in ≥14 faults whose within-fault lead fraction is ≥60%;
5. top-seven gain concentration <70%;
6. run-shuffle and the median causal time-shift each reduce macro AUPRC by ≥0.03 **and** XMV-lead fraction by ≥10 percentage points relative to original `S_XU`/alignment.

### `LIKELY_FAULT_LABEL_LEAKAGE`

Use this verdict if the generalizable Gate fails and all conditions hold:

1. XMV-only AUROC ≥0.95 for at least one fault;
2. median XMV-only fault AUROC <0.70;
3. either top-seven positive-gain concentration ≥70% or no more than 7 of 28 faults achieve XMV-only AUROC ≥0.80;
4. run-shuffle reduces the best affected fault's XMV-only AUPRC by ≥0.10.

This operationally indicates an unusually readable but narrow controller/fault signature; it does not prove intentional label encoding.

### `FAULT_SPECIFIC_CONTROLLER_SIGNATURE`

Use this verdict if neither Gate above passes and all conditions hold:

1. at least one fault has `S_XU - S_X` AUPRC gain ≥0.05;
2. top-seven positive-gain concentration ≥70%;
3. fewer than 14 faults have AUPRC gain ≥0.02 or fewer than 14 faults have XMV lead fraction ≥60%;
4. at least one of run-shuffle or median time-shift reduces macro AUPRC by ≥0.01.

### `NO_RELIABLE_XMV_EARLY_SIGNAL`

Use this verdict if all conditions hold:

1. macro fault AUPRC gain of `S_XU` over `S_X` <0.01;
2. macro fault AUROC gain <0.01;
3. overall XMV-lead fraction ≤50%;
4. neither run-shuffle nor median time-shift reduces macro AUPRC by ≥0.01.

### `INCONCLUSIVE`

Use this verdict for every remaining pattern, any calibration/FAR failure, missing required artifact, or protocol-integrity failure.

The 14/28 requirement makes “generalizable” mean at least half of all faults, not recurrence in the six motivating faults. Gains of 0.02–0.03 are large enough to avoid treating rounding noise as support. The 70% top-quartile concentration boundary identifies effects dominated by seven faults while still permitting heterogeneous industrial responses. Shuffle drops must appear in both performance and temporal ordering to reduce one-metric overinterpretation.

## 8. Leakage prevention and execution lock

- Do not open existing six-fault mechanism tables while implementing or executing this protocol.
- The implementation receives unlabeled test telemetry and run boundaries first, writes immutable score/alarm files, and records their SHA-256 hashes. Only a separate evaluation command may then join labels/onsets.
- No test label or onset is available to scaler fitting, score construction, donor mapping, thresholding, persistence, shift selection, missing-value handling, or channel permutation.
- No fault-specific thresholds, weights, variable selection, donor selection, or post-hoc exclusions.
- No future XMV and no windows crossing run boundaries.
- Report all 28 faults, all test runs, missing alarms, NaN/Inf counts, constant channels, and every preregistered control.
- No alternative threshold, shift, persistence length, feature weight, score aggregation, or decision cutoff may be reported as confirmatory.

## 9. Planned interface and artifacts

An implementation may expose only this fixed interface; it is not created in this task:

```powershell
python -m src.analysis.run_xmv_early_warning_diagnostic `
  --config configs/xmv_early_warning_preregistered.yaml `
  --score-only

python -m src.analysis.evaluate_xmv_early_warning `
  --scores artifacts/xmv_early_warning/scores.parquet `
  --unlock-labels
```

The first command must not load labels. The second must reject scores whose hash/config/preregistration hash differs.

Planned outputs:

- `artifacts/xmv_early_warning/run_manifest_and_hashes.json`
- `artifacts/xmv_early_warning/normal_calibration.json`
- `artifacts/xmv_early_warning/scores.parquet`
- `artifacts/tables/xmv_early_warning_overall.csv`
- `artifacts/tables/xmv_early_warning_by_fault.csv`
- `artifacts/tables/xmv_early_warning_by_run.csv`
- `artifacts/tables/xmv_early_warning_controls.csv`
- `artifacts/figures/xmv_early_warning_fault_gains.png`
- `artifacts/figures/xmv_early_warning_delay_distribution.png`
- `artifacts/figures/xmv_early_warning_control_degradation.png`
- `docs/XMV_EARLY_WARNING_DIAGNOSTIC_RESULTS.md`

## 10. Success, failure, and stop conditions

- **Success:** all fixed signals and controls execute on every test run; calibration passes; all artifacts are complete; exactly one Gate verdict is assigned by the precedence rules.
- **Scientific failure:** `NO_RELIABLE_XMV_EARLY_SIGNAL` is a valid completed result and must not trigger parameter changes.
- **Ambiguous completion:** report `INCONCLUSIVE` without tuning when the evidence pattern is mixed.
- **Immediate stop:** split/hash mismatch, any test access before immutable score creation, calibration FAR above its bound, run-boundary crossing, future-XMV use, missing fault/run/control, non-finite score not covered by a preregistered rule, or pressure to alter a fixed rule after results are visible.
- After stopping, preserve logs and partial artifacts; do not repair and rerun as confirmatory. A new dated protocol would be exploratory.

No test diagnostic was executed or inspected while creating this registration.
