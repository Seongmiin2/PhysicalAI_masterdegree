# Reinartz TEP F0/F1 Model-Seed 반복 실험

## 실험 조건

- 데이터 분할: Seed 42 split 고정
- Split manifest SHA-256: `AE0DF7F78D27E5EDFF805C8AA68205FA16C2C10749EA8BD6888610E75A105DDD`
- Model seed: 42, 43, 44
- 각 seed에서 F0와 F1을 30 epochs 학습
- 기존 window, batch size, optimizer, threshold percentile, alarm 조건 유지
- GPU: NVIDIA GeForce RTX 5060 Ti, PyTorch CUDA 13.0

## 전체 결과

| Seed | 모델 | MAE | RMSE | AUROC | AUPRC | 탐지 Run 비율 | 탐지 지연 | 정상 구간 오경보율 |
|---:|:---:|---:|---:|---:|---:|---:|---:|---:|
| 42 | F0 | 0.497480 | 0.736070 | 0.750770 | 0.899502 | 0.648214 | 51.865 | 0.010125 |
| 42 | F1 | 0.496841 | 0.733787 | 0.819648 | 0.931234 | 0.680357 | 24.583 | 0.010051 |
| 43 | F0 | 0.492040 | 0.734693 | 0.749719 | 0.899123 | 0.648214 | 53.072 | 0.010023 |
| 43 | F1 | 0.523993 | 0.748115 | 0.824017 | 0.933303 | 0.683929 | 27.423 | 0.009909 |
| 44 | F0 | 0.507871 | 0.739856 | 0.753336 | 0.900868 | 0.655357 | 53.965 | 0.009959 |
| 44 | F1 | 0.494597 | 0.733468 | 0.815017 | 0.929027 | 0.678571 | 24.087 | 0.010020 |

## F1 - F0 변화

| Seed | ΔAUROC | ΔAUPRC | Δ탐지 비율 | Δ탐지 지연 |
|---:|---:|---:|---:|---:|
| 42 | +0.068878 | +0.031732 | +0.032143 | -27.282 |
| 43 | +0.074297 | +0.034180 | +0.035714 | -25.649 |
| 44 | +0.061682 | +0.028159 | +0.023214 | -29.878 |

세 Seed에서 모두 F1의 AUROC, AUPRC, 탐지 Run 비율이 증가했고 탐지 지연은 감소했다. 정상 구간 오경보율은 거의 동일하다. 반면 MAE와 RMSE는 Seed 43에서 F1이 더 나빠졌으므로 예측 오차 개선은 반복되지 않았다.

## 지정 Fault 결과

아래 값은 `F1 AUROC - F0 AUROC`이다.

| Fault | Seed 42 | Seed 43 | Seed 44 | 세 Seed 반복 개선 |
|---:|---:|---:|---:|:---:|
| 4 | +0.462555 | +0.468637 | +0.306098 | Yes |
| 7 | +0.487463 | +0.487232 | +0.485583 | Yes |
| 19 | +0.214807 | +0.229498 | +0.208489 | Yes |
| 24 | +0.079713 | +0.083090 | +0.071853 | Yes |
| 25 | +0.204409 | +0.232878 | +0.241209 | Yes |
| 26 | +0.411112 | +0.417680 | +0.401513 | Yes |

Fault별 탐지율은 Fault 26에서 `0.20→1.00`, `0.15→1.00`, `0.25→1.00`으로 세 Seed 모두 크게 개선됐다. Fault 25는 Seed 42에서 `0.95→1.00`이었고 Seed 43/44에서는 F0부터 1.00이라 추가 개선 여지가 없었다. Fault 4, 7, 19, 24는 두 모델 모두 세 Seed에서 1.00이었다. 따라서 지정 Fault의 **AUROC 개선은 모두 반복**됐지만, 탐지율의 추가 개선은 주로 Fault 26에서 반복됐다.

## 질문별 결론

1. **Yes.** 세 Seed 모두 F1의 AUROC와 AUPRC가 F0보다 높았다.
2. **Yes.** 세 Seed 모두 탐지 Run 비율은 높아지고 탐지 지연은 짧아졌다.
3. **AUROC 기준 Yes.** Fault 4, 7, 19, 24, 25, 26 모두 세 Seed에서 개선됐다. 탐지율 기준의 반복적인 큰 개선은 Fault 26에서 확인됐다.
4. **크게 흔들리지 않았다.** F1의 seed 간 범위는 AUROC 0.0090, AUPRC 0.0043, 탐지 비율 0.0054, 탐지 지연 3.34 samples였다. 관찰된 F1 우위보다 seed 변동 폭이 작다.

## 판정

세 Seed에서 고장 탐지 성능 개선이 같은 방향으로 반복됐다. 따라서 현재 결과는 model seed 우연에 의한 단발성 결과로 보이지 않는다. 지시된 판정 규칙에 따라 다음 단계의 후보는 **모델 크기 차이 확인**이다. 이번 작업에서는 해당 실험을 수행하지 않는다.

## 원본 결과

- `artifacts/tables/reinartz_f0_f1_results.csv` — Seed 42
- `artifacts/tables/reinartz_f0_f1_results_seed_43.csv` — Seed 43
- `artifacts/tables/reinartz_f0_f1_results_seed_44.csv` — Seed 44
- `artifacts/tables/reinartz_fault_results.csv` — Seed 42 fault별 결과
- `artifacts/tables/reinartz_fault_results_seed_43.csv` — Seed 43 fault별 결과
- `artifacts/tables/reinartz_fault_results_seed_44.csv` — Seed 44 fault별 결과
- `logs/reinartz_f0_f1/seed_43.log`
- `logs/reinartz_f0_f1/seed_44.log`
