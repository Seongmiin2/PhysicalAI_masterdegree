# Reinartz TEP F0/F1 Seed-42 Information Value Gate

## 1. What was implemented

A minimal, CPU-safe F0/F1 forecasting experiment was implemented without adding a
proposed model.

- one-time float32 NumPy memmap cache for 5.6M rows;
- fault-stratified run-level train/validation/test split;
- train-normal-only standardization;
- run-safe dynamic windows without materializing duplicated window arrays;
- identical one-layer GRU forecasting baselines;
- validation-normal 99th-percentile threshold;
- three-consecutive-exceedance persistence alarm;
- pooled and fault-level metrics, checkpoints, logs, and reproducibility artifacts.

This is a baseline/Hypothesis Gate, not a thesis contribution.

## 2. Research hypothesis tested

H1: past manipulated-variable history contains useful information for modeling
normal future state and detecting faults.

```text
F0: Past 20 × 41 XMEAS -> GRU -> next 41 XMEAS
F1: Past 20 × (41 XMEAS + 11 XMV) -> same GRU -> next 41 XMEAS
```

## 3. Data used

- AIRI FDDBenchmark processed `reinartz_tep`;
- 2,800 runs, 28 faults, 2,000 samples/run;
- onset at sample 600;
- train 1,792 / validation 448 / test 560 runs;
- training targets use only samples up to 599;
- available XMV is 11/12; XMV12 and operating mode are absent.

## 4. Leakage checks

- Existing 80/20 mask is run-level; overlap is zero.
- Validation is selected by run from original training runs (16/fault).
- Scaler is fit on training runs, samples 1–599 only.
- Windows never cross run boundaries.
- F1 input ends immediately before its XMEAS target; future XMV is not used.
- Labels, fault IDs, and masks are never model features.
- Threshold uses validation pre-fault scores only; test faults do not tune it.
- Seed 42 and deterministic PyTorch algorithms are used.

## 5. Common configuration

```yaml
window: 20
horizon: 1
hidden_dim: 64
layers: 1
epochs: 30
batch_size: 128
learning_rate: 0.001
optimizer: Adam
loss: MSE
threshold: validation pre-fault 99th percentile
alarm: 3 consecutive exceedances
```

Input dimension is the only intentional architecture difference. Because GRU input
weights depend on input dimension, F1 has 25,321 parameters versus F0's 23,209
(+2,112, about +9.1%). This is a known confound for follow-up analysis.

## 6. Overall results

| Metric | F0 XMEAS | F1 XMEAS+XMV | F1 − F0 | Direction |
|---|---:|---:|---:|---|
| MAE_z | 0.497480 | 0.496841 | -0.000640 | marginally better |
| RMSE_z | 0.736070 | 0.733787 | -0.002284 | marginally better |
| AUROC | 0.750770 | 0.819648 | +0.068878 | better |
| AUPRC | 0.899502 | 0.931234 | +0.031732 | better |
| Detected run ratio | 0.648214 | 0.680357 | +0.032143 | better |
| Detection delay (samples) | 51.865 | 24.583 | -27.282 | earlier |
| Pre-fault sample FPR | 0.010125 | 0.010051 | -0.000074 | essentially equal |
| Pre-fault run alarm rate | 0.000000 | 0.000000 | 0 | equal |

At a 3-minute sampling interval, the mean delay difference is about 81.8 minutes,
but this pooled mean includes only detected runs and is strongly influenced by a
few faults. It must not be interpreted as universal early detection improvement.

## 7. Fault-level results

F1 improved fault-level AUROC for 22/28 faults and AUPRC for 21/28, but many gains
were numerically tiny. Material improvements were concentrated in:

| Fault | AUROC F0→F1 | AUPRC F0→F1 | Detection ratio F0→F1 | Delay F0→F1 |
|---:|---:|---:|---:|---:|
| 4 | 0.5014→0.9639 | 0.7123→0.9834 | 1.00→1.00 | 4.0→4.0 |
| 7 | 0.5118→0.9993 | 0.7255→0.9998 | 1.00→1.00 | 4.0→4.0 |
| 19 | 0.7624→0.9772 | 0.8955→0.9915 | 1.00→1.00 | 119.3→32.3 |
| 24 | 0.9047→0.9844 | 0.9631→0.9944 | 1.00→1.00 | 26.5→17.0 |
| 25 | 0.6848→0.8892 | 0.8456→0.9543 | 0.95→1.00 | 247.1→37.5 |
| 26 | 0.5411→0.9522 | 0.7408→0.9823 | 0.20→1.00 | 1052.3→30.9 |

Small degradations appeared for faults 6, 10, 12, 17, 18, and 28. Faults 3, 9,
15, 16, 21–23, and 28 remained undetected by the persistence threshold in both
models; fault 5 moved from 0% to 5% detected.

The complete table is `artifacts/tables/reinartz_fault_results.csv`.

## 8. Statistical and qualitative observations

1. Normal prediction improvement is very small: H1 is not strongly supported by
   aggregate MAE/RMSE alone.
2. Detection ranking improves substantially overall, suggesting XMV history changes
   residual separability more than average normal prediction accuracy.
3. Benefits are heterogeneous and concentrated in several fault types, consistent
   with different controller responses or XMV relevance by fault.
4. Overall delay improvement is dominated by faults 19, 25, and 26.
5. F1's extra input weights (+9.1% parameters) are a confound; the current run does
   not prove that information rather than capacity caused every gain.
6. This is a single seed. No variance, paired significance test, or alternate split
   has yet established robustness.

## 9. Dataset limitations

- third-party processed distribution with incomplete preprocessing provenance;
- XMV12 missing and two available XMV columns constant;
- operating mode absent;
- no independent all-normal runs;
- all faults aligned to onset sample 600;
- manipulated variables may reflect closed-loop controller reaction rather than
  independent causal action;
- fault identity and physical mechanism mapping were not used in training and are
  not reconstructed here.

## 10. H1 decision

### `PARTIALLY_SUPPORTED`

Past XMV history provides clear additional detection information in the pooled
seed-42 result and material improvements for a subset of faults. However, normal
forecast accuracy changes only marginally, several faults do not improve, gains are
heterogeneous, F1 has more parameters, and only one seed/split realization has been
tested. These results support continued investigation but do not justify claiming a
general control-information benefit or implementing CDREL yet.

## 11. What this means for the thesis

The closed-loop control direction remains viable: XMV history can materially alter
fault separability even when average normal forecasting accuracy barely changes.
The strongest research clue is fault-specific, not universal. The next work should
identify whether improvements correspond to meaningful controller-response/lag
mechanisms and survive capacity control and repeated seeds.

The result does **not** establish causal intervention, novelty, early-fault solution,
or the proposed control-disentangled method.

## 12. Recommended next Research Phase

Remain in **Phase 1B analysis**, not Phase 2 novelty review yet:

1. repeat F0/F1 over multiple seeds and report mean ± std;
2. control parameter count (matched-capacity F0 or input projection);
3. inspect faults 4, 7, 19, 24–26 versus non-improving faults;
4. analyze XMV/sensor lag, delta-XMV, and controller response;
5. test whether constant XMV removal changes results;
6. decide whether missing XMV12/operating mode requires official DTU Mode 1.

No probabilistic model, control disentanglement, residual evolution, Transformer,
GNN, RAG, open-set, or attribution should be implemented before that gate.
