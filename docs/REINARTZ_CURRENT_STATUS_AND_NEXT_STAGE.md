# Reinartz TEP Pilot — 현재 현황 및 다음 Stage

## 1. 연구 질문

> 실제 Tennessee Eastman Process 계열 데이터에서 과거 XMV를 함께 사용하는 것이
> XMEAS 기반 정상 미래 예측과 fault detection에 도움이 되는가?

비교 대상은 두 모델로 제한한다.

```text
F0: Past 41 XMEAS → Future 41 XMEAS
F1: Past 41 XMEAS + Past 11 XMV → Future 41 XMEAS
```

## 2. 지금까지 완료한 작업

### Synthetic pipeline

- Synthetic TEP-like episode 생성
- Parquet/NPZ 저장
- SQLite 실험 기록
- GRU 실행 구조, checkpoint, metric, background runner 검증
- `synthetic-pipeline-v0` Git tag 생성 및 GitHub push

Synthetic 결과는 코드 구조 검증용이며 논문 성능으로 사용하지 않는다.

### 공식 Extended TEP 조사

- DTU Figshare article `13385936` API catalog 생성
- 공식 README 다운로드 및 MD5 검증
- Mode별 HDF5가 각각 약 23–24GB임을 확인
- 공식 `TEP_Mode1.h5` 전체는 다운로드하지 않음
- 실제 HDF5용 canonical loader와 Data Quality 도구 준비

### FDDBenchmark `reinartz_tep` 조사

- Source repository: <https://github.com/AIRI-Institute/fddbenchmark>
- 조사 commit: `a536b027e69983d197469a642f57f120c3c6c6c3`
- 실제 archive URL을 loader 코드에서 확인
- `reinartz_tep.zip` 2,013,615,713 bytes 다운로드
- TLS 검증 유지, 재개 가능한 `.partial` 다운로드 사용
- Content-Length 및 ZIP 전체 CRC 검증 완료
- DTU 공식 데이터와 분리하여 저장

```text
data/external/fddbenchmark/reinartz_tep.zip
data/external/fddbenchmark/reinartz_tep/
```

## 3. 실제 데이터 구조

| File | Rows | Columns | Size (bytes) |
|---|---:|---:|---:|
| dataset.csv | 5,600,000 | 54 | 5,247,567,494 |
| labels.csv | 5,600,000 | 3 | 98,918,321 |
| train_mask.csv | 5,600,000 | 3 | 96,256,425 |
| test_mask.csv | 5,600,000 | 3 | 96,256,424 |
| labeled_train_mask.csv | 5,600,000 | 3 | 96,256,433 |

모든 파일은 `(run_id, sample)` key에 대해 5,600,000행이 정렬·정합된다.

## 4. Feature 구조

```text
run_id
sample
xmeas_1 ... xmeas_41
xmv_1 ... xmv_11
```

- Telemetry features: 52
- XMEAS: 41/41
- XMV: 11/12
- 누락: `XMV_12`
- Missing/NaN/Inf: 없음
- 상수 변수: `xmv_5 = 1.0`, `xmv_9 = 1.0`
- XMV12의 물리적 이름과 제거 이유: UNKNOWN

## 5. Run 및 Label 구조

- Runs: 2,800
- Fault classes: 28
- Runs per fault: 100
- Samples per run: 2,000
- 모든 run 길이 동일
- sample 1–599: label 0, pre-fault normal
- sample 600–2,000: fault ID 1–28
- fault onset: 모든 run에서 sample 600
- 독립 all-normal run: 없음
- operating mode: archive에 없음/UNKNOWN

## 6. 기존 Split

- Train: 2,240 runs, fault별 80
- Test: 560 runs, fault별 20
- 동일 run의 train/test 중복: 0
- run 내부 mask 변화: 0
- 기존 split은 row random split이 아니라 fault-stratified run-level 80/20 split

기존 test split은 유지할 수 있다. Validation은 training runs 안에서 run-level로 새로 만든다.

## 7. Leakage 평가

Telemetry feature에는 다음 정보가 포함되지 않는다.

- label
- fault ID
- train/test mask
- anomaly score

다음 guard는 실험에서 강제해야 한다.

```text
Input: XMEAS[t-window+1:t] (+ XMV[t-window+1:t])
Target: XMEAS[t+1]
```

금지:

- 미래 XMV 입력
- label/mask/fault ID 입력
- test fault로 threshold 조정
- 동일 run을 여러 split에 배정
- fault onset 이후 구간을 정상 학습에 사용

XMV는 독립 intervention이 아니라 closed-loop controller response일 수 있으므로, 결과는
“과거 manipulated-variable history의 추가 정보 가치”로만 해석한다.

## 8. Compatibility 최종 판정

```text
PARTIALLY_SUITABLE
```

제한된 F0/F1 pilot은 가능하다. 41 XMEAS, 11 XMV, 시간 순서, run boundary,
fault onset, normal/fault label, run-level split이 보존되어 있다.

다만 다음 제한이 있다.

- XMV12 부재
- operating mode 부재
- 독립 normal run 부재
- preprocessing 생성 코드 및 원본 run provenance 부재

상세 근거는 `docs/FDDBENCHMARK_REINARTZ_COMPATIBILITY.md`를 참조한다.

# 다음 Stage — F0/F1 Forecasting Pilot

## 9. 목적과 범위

다음 질문만 검증한다.

> Available 11 XMV의 과거 history를 추가하면 XMEAS 미래 예측과 fault detection이
> 개선되는가?

다음 기능은 추가하지 않는다.

- Recovery/RAG
- Transformer/GNN
- Residual Evolution
- Open-set/Attribution
- Probabilistic Forecasting
- 공식 Mode 1 전체 다운로드

## 10. Split 계획

기존 test 20 runs/fault를 유지하고, 기존 train 80 runs/fault를 다시 나눈다.

```text
Train:      64 runs/fault = 1,792 runs
Validation: 16 runs/fault =   448 runs
Test:       20 runs/fault =   560 runs
```

- 고정 seed 사용
- 동일 run은 하나의 split에만 포함
- `artifacts/tables/reinartz_split_manifest.csv` 저장

## 11. 정상 학습 구간

학습에는 training run의 pre-fault 구간만 사용한다.

```text
sample 1–599
window = 20
horizon = 1
target sample ≤ 599
```

Fault onset 이후 데이터는 정상 모델 학습에 사용하지 않는다.

## 12. Scaling

- StandardScaler
- train runs의 sample 1–599로만 fit
- F0/F1은 동일 XMEAS scaler 사용
- F1 XMV scaler도 train normal에서만 fit
- 상수 XMV의 scale은 1로 처리
- `artifacts/tables/reinartz_scaler_parameters.csv` 저장

## 13. Window와 모델

```yaml
window: 20
horizon: 1
model: GRU
hidden_dim: 64
layers: 1
epochs: 30
batch_size: 128
learning_rate: 0.001
optimizer: Adam
loss: MSE
```

입력/출력 shape:

```text
F0 input: [20, 41]
F1 input: [20, 52]
Target:   [41]
```

입력 차원을 제외하고 architecture와 모든 training 설정을 동일하게 유지한다.

## 14. Anomaly score와 Threshold

주 anomaly score:

```text
41개 standardized XMEAS의 mean absolute prediction error
```

Threshold:

```text
validation normal anomaly score의 99th percentile
```

F0/F1에 동일한 threshold 결정 규칙을 적용한다.

## 15. 평가

Normal prediction:

- MAE
- RMSE

Fault detection:

- AUROC
- AUPRC
- Detection Delay
- Normal false-positive rate
- Detected run ratio
- fault별 결과

Detection delay:

```text
sample 600 이후 첫 threshold crossing - 600
```

## 16. 반복 실험

최종 비교는 최소 5 seeds를 권장한다.

```text
42, 43, 44, 45, 46
```

각 지표를 `mean ± std`로 보고한다.

## 17. 다음 Stage 산출물

```text
configs/reinartz_f0_f1.yaml
artifacts/tables/reinartz_split_manifest.csv
artifacts/tables/reinartz_scaler_parameters.csv
artifacts/tables/reinartz_f0_f1_results.csv
artifacts/tables/reinartz_fault_results.csv
checkpoints/reinartz_f0_seed_{seed}.pt
checkpoints/reinartz_f1_seed_{seed}.pt
logs/reinartz_f0_f1/
docs/REINARTZ_F0_F1_RESULTS.md
```

## 18. 최종 결과표

| Model | Input | MAE ↓ | RMSE ↓ | AUROC ↑ | AUPRC ↑ | Delay ↓ | Normal FPR ↓ |
|---|---|---:|---:|---:|---:|---:|---:|
| F0 | Past XMEAS | TBD | TBD | TBD | TBD | TBD | TBD |
| F1 | Past XMEAS + Past 11 XMV | TBD | TBD | TBD | TBD | TBD | TBD |

## 19. 연구 판단

### GO

F1이 여러 seed/fault에서 예측오차, AUROC/AUPRC, delay 또는 normal FPR을 일관되게 개선하면
다음 단계에서 probabilistic forecasting을 검토한다.

### PARTIAL

정상 예측만 개선하거나 특정 fault/delay에서만 개선하면 fault별 XMV 효과를 분석한다.

### STOP/PIVOT

F1 개선이 없거나 controller reaction만으로 설명되거나 XMV12 부재 때문에 해석이
불가능하면 공식 `TEP_Mode1.h5` 다운로드 여부를 결정한다.

## 20. 다음 Stage Stop Condition

지정된 설정, split, scaler, 전체/ fault별 결과표와 결과 문서가 생성되면 중단한다.
그 이후 모델이나 연구 기능은 자동으로 추가하지 않는다.
