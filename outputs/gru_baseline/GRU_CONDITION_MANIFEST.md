# GRU condition manifest for CHUM

## 결론

4개 locked cell의 GRU perturbation은 `delta_auroc = original - perturbed`가
모든 seed에서 양수였다. 따라서 **원시 방향은 4/4 cell에서 CHUM locked
방향과 같다.** 그러나 GRU와 TCN·Transformer의 확정 조건이 다르므로 이
결과를 3-architecture consensus 판정에 포함하지 않는다. 이는 불일치가
아니라 **조건 상이로 인한 비교 제외**다.

## 출처와 범위

- PhysicalAI 대표 F0/F1/F0-C 결과: 이 저장소의
  `artifacts/tables/reinartz_f0_f1_seed_comparison.csv` 및
  `artifacts/tables/reinartz_capacity_control_comparison.csv`.
- 대표 seed-42 값: F0 AUROC 0.7508, AUPRC 0.8995, delay 51.9;
  F1 AUROC 0.8196, AUPRC 0.9312, delay 24.6; F0-C AUROC 0.7493,
  AUPRC 0.8989.
- PhysicalAI에 직접 보존된 F0/F1 반복은 model seed 42–44다.
- Cell-level GRU 값은 Thesis-Orchestrator의 삭제 전 evidence commit
  `bc6166f`에 있던 `outputs/architecture_chum_g3/G3_CELL_RESULTS.csv`와
  `G3_CELL_SUMMARY.csv`에서 복원했다. 해당 cell 실행은 seed 42–46이다.
  seed 42–44 checkpoint는 PhysicalAI, seed 45–46 checkpoint는
  Thesis-Orchestrator `outputs/final_gate_exp1/checkpoints`에서 공급되었다.

이 구분은 중요하다. 저장소 대표 실험의 “3 seeds”와 cell perturbation의
“5 seeds”를 같은 실행으로 쓰지 않는다.

## 조건 비교

| 항목 | PhysicalAI 대표 GRU | GRU cell conditional | GRU cell zero | CHUM locked consensus |
|---|---|---|---|---|
| 목적 | XMV 전체 추가(F0 대 F1) | 단일 XMV 조건부 대치 | 단일 XMV zero masking | 단일 XMV utility의 architecture 합의 |
| seed | 42–44 | 42–46 | 42–46 | 42–46 |
| 대치 | 없음 | normal-train ridge conditional mean (`legacy_mean`) | training-standardized zero | LOO residual sampling |
| threshold | seed/model별 validation-normal p99 | seed/condition별 validation-normal p99 재보정 | seed/condition별 validation-normal p99 재보정 | seed/condition별 validation-normal p99 재보정 |
| imputer gate | 해당 없음 | legacy gate: R2 >= 0.5, std ratio >= 0.75 | 해당 없음 | held-out distribution/lag gate |
| run-level hierarchical CI | 없음 | 없음 | 없음 | 2,000회 paired hierarchical bootstrap |
| consensus 사용 | 해당 없음 | 제외 | 제외 | TCN·Transformer만 사용 |

Conditional GRU에서 legacy imputer gate를 통과한 locked channel은 XMV2와
XMV7이며, XMV8과 XMV10은 탈락했다. CHUM의 LOO-residual gate는 이와 다른
기준이며 locked channel XMV2, XMV7, XMV8, XMV10을 모두 통과했다. 따라서
GRU의 raw sign을 모델 간 동일 조건의 합의 증거로 승격할 수 없다.

## 데이터 및 재현 조건

### 데이터

- AIRI fddbenchmark Reinartz TEP: 5,600,000 rows, 54 columns.
- 2,800 runs, 28 faults, fault당 100 runs, run당 2,000 samples.
- 41 XMEAS와 11 XMV; XMV12는 부재하고 XMV5·XMV9는 상수다.
- 모든 fault onset은 sample 600이다.

### 분할과 scaling

- Run-level split: 1,792 train / 448 validation / 560 test.
- StandardScaler는 train run의 정상 구간 sample 1–599에만 fit했다.
- F0/F1은 sensor scaler를 공유하고 XMV scaler도 train-normal에만 fit했다.

### 모델과 평가

- GRU hidden 64, 1 layer, 30 epochs, batch 128, Adam lr 0.001, MSE.
- F0 `[20, 41] -> 41`; F1 `[20, 52] -> 41`.
- F0-C는 sensors-only이고 F1보다 파라미터가 0.60% 많다.
- 평가 지표: MAE/RMSE, AUROC/AUPRC, normal FPR, detection delay,
  detected-run ratio.

## CHUM 후보 channel 분모 전달

- archive 제공 XMV: 11개.
- XMV12: 부재.
- 상수 XMV5·XMV9: 대치 가능한 informative 후보에서 제외.
- 비상수 후보: 9개(XMV1–4, XMV6–8, XMV10–11).
- CHUM의 primary LOO-residual imputer quality gate 통과: 8개
  (XMV1, XMV2, XMV3, XMV6, XMV7, XMV8, XMV10, XMV11).
- 비상수이지만 primary quality gate 탈락: XMV4 1개.
- 상수까지 포함한 11개 전체 중 primary gate 탈락: XMV4, XMV5, XMV9
  3개.

따라서 primary conditional-attribution의 channel 분모는 **8개**다. 실제
fault 분모와 결합한 전체 cell 분모는 CHUM의 G3 전수 결과 복원 단계에서
fault 필터를 확인한 뒤 확정해야 한다.

## 해석 경계

이 표는 특정 XMV history에 대한 예측 의존성과 추가 정보 utility를
기술한다. XMV, controller action 또는 fault 사이의 인과효과를 식별하지
않는다.
