# Reinartz TEP F0-C Capacity-Control Result

## 목적과 제한

F1이 F0보다 약 9.1% 큰 모델이라는 혼란요인을 한 번 점검했다. F0-C는 XMEAS 41개만 입력으로 사용하고 GRU hidden dimension을 68로 설정했다. 이 결과는 통계적 확정이나 인과관계의 근거가 아니다.

고정 조건은 Seed 42 split, model seed 42, 30 epochs, window 20, batch 128, Adam, learning rate 0.001, 기존 scaler, validation-normal 99th-percentile threshold 및 3-sample persistence alarm이다. 기존 F0/F1은 재학습하지 않았다.

## 모델 크기

코드로 계산한 F0-C 파라미터 수는 **25,473**이다. F1의 25,321보다 152개(0.60%) 많고, 기존 F0의 23,209보다 9.75% 많다.

| 모델 | 입력 | Hidden | Parameters |
|:---:|:---|---:|---:|
| F0 | 41 XMEAS | 64 | 23,209 |
| F0-C | 41 XMEAS | 68 | 25,473 |
| F1 | 41 XMEAS + 11 XMV | 64 | 25,321 |

## 전체 결과

| 모델 | MAE | RMSE | AUROC | AUPRC | 탐지 Run 비율 | 탐지 지연 | 정상 구간 오경보율 |
|:---:|---:|---:|---:|---:|---:|---:|---:|
| F0 | 0.497480 | 0.736070 | 0.750770 | 0.899502 | 0.648214 | 51.865 | 0.010125 |
| F0-C | 0.501825 | 0.737781 | 0.749277 | 0.898862 | 0.648214 | 49.444 | 0.010230 |
| F1 | 0.496841 | 0.733787 | 0.819648 | 0.931234 | 0.680357 | 24.583 | 0.010051 |

F0-C는 F1의 AUROC/AUPRC에 도달하지 못했다. F0-C의 탐지율은 F0와 같았고, 탐지 지연은 F0보다 2.42 samples 짧지만 F1보다 24.86 samples 길었다.

## 지정 Fault 결과

| Fault | 모델 | AUROC | 탐지율 | 탐지 지연 |
|---:|:---:|---:|---:|---:|
| 4 | F0 / F0-C / F1 | 0.5014 / 0.5015 / 0.9639 | 1.00 / 1.00 / 1.00 | 4.00 / 4.00 / 4.00 |
| 7 | F0 / F0-C / F1 | 0.5118 / 0.5125 / 0.9993 | 1.00 / 1.00 / 1.00 | 4.00 / 4.00 / 4.00 |
| 19 | F0 / F0-C / F1 | 0.7624 / 0.7556 / 0.9772 | 1.00 / 1.00 / 1.00 | 119.30 / 124.65 / 32.30 |
| 24 | F0 / F0-C / F1 | 0.9047 / 0.9030 / 0.9844 | 1.00 / 1.00 / 1.00 | 26.50 / 26.75 / 16.95 |
| 25 | F0 / F0-C / F1 | 0.6848 / 0.6790 / 0.8892 | 0.95 / 1.00 / 1.00 | 247.05 / 260.00 / 37.45 |
| 26 | F0 / F0-C / F1 | 0.5411 / 0.5387 / 0.9522 | 0.20 / 0.15 / 1.00 | 1052.25 / 891.33 / 30.90 |

- F0-C는 Fault 26의 100% 탐지율을 재현하지 못했다(15%).
- F0-C는 Fault 19와 25의 지연 감소를 재현하지 못했다.
- Fault 26 지연은 탐지된 소수 run에만 조건부로 계산되므로 낮은 탐지율과 함께 해석해야 하며, F1 수준에는 도달하지 못했다.

## Phase 1 최종 판정

**PASS — 후속 연구 가치 있음.** F0-C는 기존 F0와 비슷했고 F1은 탐지 지표에서 계속 우수했다. 따라서 이번 1회 점검에서는 단순 모델 크기만으로 F1 개선을 설명하기 어렵다. 다만 이것은 제어기록의 인과효과나 일반적 우월성을 확정하지 않는다.

> Reinartz TEP의 고정 split과 GRU baseline에서 과거 XMV 기록은 model seed 42–44에 걸쳐 반복적이고, 단순 용량 증가로 재현되지 않는 고장탐지 정보를 보였다.

Phase 1 F0/F1 실험은 여기서 종료한다. 추가 seed, hidden dimension, threshold/window 변경 또는 backbone 비교는 수행하지 않는다.

## 산출물

- `artifacts/tables/reinartz_capacity_control_results.csv`
- `artifacts/tables/reinartz_capacity_control_fault_results.csv`
- `artifacts/tables/reinartz_capacity_control_comparison.csv`
- `checkpoints/reinartz_f0_c_seed_42.pt` (로컬 artifact; Git 제외)
- `logs/reinartz_f0_f1/capacity_control_seed_42.log` (로컬 artifact; Git 제외)
