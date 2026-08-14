# 폐루프 산업 시스템의 제어 맥락을 활용한 조기 고장탐지 연구
## 문제 정의, 예비실험 결과 및 방법론 개발 계획

## 1. 연구 배경

자동제어 산업 시스템은 센서로 현재 상태를 측정하고, 제어기가 목표 상태를 유지하도록 조작변수를 계속 변경하는 폐루프 시스템이다. 이때 저장되는 시계열에는 크게 두 종류의 정보가 섞인다.

- 센서값: 온도, 압력, 유량처럼 공정의 현재 상태를 나타내는 측정값
- 제어기록: 밸브 개도, 공급량처럼 제어기가 공정을 조절하기 위해 변경한 조작변수

고장이 발생하면 센서값이 달라지지만, 제어기도 이를 보상하려고 움직인다. 따라서 관측된 변화는 고장 영향만이 아니라 정상적인 제어 반응까지 포함한다. 센서값만 감시하면 제어기가 의도적으로 만든 변화와 고장 때문에 생긴 변화를 혼동할 수 있다.

본 연구는 제어기록을 독립적인 인과적 개입으로 가정하지 않는다. 제어기록은 공정 상태에 반응한 controller response일 수 있으며, 여기서는 정상 상태변화를 설명하는 추가 맥락 정보로만 사용한다.

## 2. 연구 질문

> 과거 제어기록으로 설명되는 정상 반응과 설명하기 어려운 고장성 변화를 구분하면, 고장을 더 일찍 찾을 수 있는가?

이를 두 단계로 나누어 확인한다.

1. 과거 제어기록이 실제 고장탐지에 추가 정보를 제공하는가?
2. 제공한다면, 제어로 설명되지 않는 residual의 시간적 변화를 어떻게 정의하고 학습해야 기존 방법과 구별되는가?

첫 질문은 Phase 1 예비실험에서 일부 Fault에 한해 제한적으로 지지됐다. 두 번째 질문은 현재 Phase 2 수학적 차별성 검증 단계에 있다.

## 3. 데이터

예비실험에는 AIRI FDDBenchmark에 포함된 Reinartz Tennessee Eastman Process 공개 산업공정 시뮬레이션 전처리 데이터를 사용했다. 실제 플랜트 계측 데이터가 아니다.

- 총 2,800개 run
- run당 2,000개 시점
- 41개 XMEAS 센서값
- 11개 XMV 제어기록
- fault onset: 각 fault run의 600번째 sample
- 정상 구간으로 모델을 학습하고 validation 정상 예측오차로 anomaly threshold를 정함
- fault test 데이터로 threshold를 조정하지 않음
- run 경계를 넘는 window를 만들지 않음

제약도 명확하다. 이 전처리본은 공식 Extended TEP 전체 데이터가 아니며 XMV12가 없고 operating mode 정보도 없다. 따라서 결과를 모든 산업공정이나 모든 TEP 설정으로 일반화할 수 없다.

## 4. 완료된 예비실험

### 4.1 비교 모델

- F0: 과거 41개 센서값 → GRU → 다음 센서값 예측
- F1: 과거 41개 센서값과 11개 제어기록 → 같은 GRU → 다음 센서값 예측
- F0-C: 센서값만 사용하되 hidden dimension을 68로 늘려 F1과 모델 크기를 맞춘 통제모델

F0/F1은 model seed 42, 43, 44에서 비교했고 데이터 split은 Seed 42로 고정했다. F0-C는 지시된 1회 통제로 Seed 42에서만 실행했다.

### 4.2 반복 결과

| Seed | 모델 | AUROC | AUPRC | 탐지 Run 비율 | 탐지 지연 |
|---:|:---:|---:|---:|---:|---:|
| 42 | F0 | 0.7508 | 0.8995 | 0.6482 | 51.87 |
| 42 | F1 | 0.8196 | 0.9312 | 0.6804 | 24.58 |
| 43 | F0 | 0.7497 | 0.8991 | 0.6482 | 53.07 |
| 43 | F1 | 0.8240 | 0.9333 | 0.6839 | 27.42 |
| 44 | F0 | 0.7533 | 0.9009 | 0.6554 | 53.96 |
| 44 | F1 | 0.8150 | 0.9290 | 0.6786 | 24.09 |

세 seed 모두에서 F1의 AUROC, AUPRC와 탐지율이 증가하고 탐지 지연이 감소했다. 반면 정상 미래예측의 MAE/RMSE는 일관되게 개선되지 않았다. 특히 Seed 43에서는 F1의 정상 예측오차가 F0보다 나빴다. 따라서 제어기록이 정상 예측을 보편적으로 개선한다고 결론 내릴 수는 없다.

탐지 지연 단위는 sample이며 1 sample은 3분이다. 탐지 지연은 탐지에 성공한 Run만 대상으로 계산했으므로 탐지율과 반드시 함께 해석해야 한다.

### 4.3 모델 크기 통제

| 모델 | 입력 | Parameters | AUROC | AUPRC | 탐지율 | 탐지 지연 |
|:---:|:---|---:|---:|---:|---:|---:|
| F0 | XMEAS | 23,209 | 0.7508 | 0.8995 | 0.6482 | 51.87 |
| F0-C | XMEAS | 25,473 | 0.7493 | 0.8989 | 0.6482 | 49.44 |
| F1 | XMEAS+XMV | 25,321 | 0.8196 | 0.9312 | 0.6804 | 24.58 |

F0-C는 F1보다 0.60% 큰 모델이지만 성능은 F0와 비슷했다. 이번 1회 통제에서는 단순 파라미터 증가가 F1의 탐지 향상을 설명하지 못했다.

### 4.4 Fault 26 사례

Seed 42에서 Fault 26 탐지율은 F0 20%, F0-C 15%, F1 100%였다. AUROC도 각각 0.5411, 0.5387, 0.9522였다. 이 fault에서는 제어기록의 추가 정보가 매우 크게 나타났다.

그러나 Fault 26 한 사례를 전체 fault나 다른 공정으로 일반화하지 않는다. 전체 결과는 일부 fault에서 효과가 집중된다는 제한을 가진다.

## 5. 예비실험의 제한된 결론

> 제어기록이 모든 고장에 보편적으로 유용하다고 증명한 것은 아니지만, 일부 고장에서 반복적이고 모델 크기만으로 재현되지 않는 탐지 정보를 보였다.

Phase 1의 `PASS`는 제안 방법을 증명했다는 뜻이 아니다. 다음 연구 Gate로 넘어갈 실증적 근거가 생겼다는 의미다. 추가 GRU seed, hidden dimension, threshold, window 또는 backbone 탐색은 종료했다.

## 6. 선행연구와 남은 문제

검증된 핵심 문헌은 다음 사실을 보여준다.

- CVA/CCA 연구는 공정의 과거-미래 또는 input-output 관계를 모델링하고 residual을 감시한다.
- state-space residual monitoring은 output prediction residual과 serial correlation 문제를 다룬다.
- subspace identification은 정상 동역학에서 벗어난 parity-space 성분을 감시한다.
- CUSUM-PCA와 CV residual statistics는 residual 또는 monitoring statistic의 시간 누적을 이용해 미세 고장을 탐지한다.
- Patel 등의 연구는 actuator command에 condition된 미래 관측을 예측하고 실제 관측과의 차이로 anomaly를 감시한다.

따라서 다음은 연구 차별점이 아니다.

- 센서와 제어변수를 함께 입력하는 것
- GRU 등 새로운 신경망을 사용하는 것
- prediction residual을 계산하는 것
- residual에 시간창이나 누적 통계를 적용하는 것

아직 방법론적으로 구분해야 할 부분은 다음과 같다.

1. 정상 state transition 중 과거 제어기록으로 설명되는 성분을 어떻게 정의할 것인가?
2. 설명되지 않는 residual을 기존 CCA/CVA prediction error와 다르게 만드는 학습 제약은 무엇인가?
3. residual evolution의 학습이 단순 CUSUM이나 sliding-window statistic과 어떻게 다른가?
4. 동일한 정상 오경보 조건에서 detection delay 개선을 학습 목표 및 평가와 어떻게 연결할 것인가?

예비 문헌 판정 `VIABLE_GAP_CANDIDATE`는 잠정 판정이었다. Chen 2016 전체 원문을 추가 검증한 결과, 정적 Eq. (1)/(9)의 `r(k)=L^Ty(k)-M^Tu(k)`와 동적 Eq. (24)의 과거 input/output 및 미래 input 조건부 residual이 현재 `e_t`와 강하게 겹친다. Chen에는 두 예측기의 차이 `c_t`나 residual evolution 학습은 없지만, `c_t`를 제어 영향으로 식별하는 제약도 현재 후보에는 없다. Mercer 2002와 Ji 2024의 전체 원문은 확보하지 못했으므로 Gate는 `INCONCLUSIVE`를 유지하고 Phase 3 진입을 보류한다.

### 검증된 참고문헌

- Chen et al. (2016), DOI: 10.1016/j.conengprac.2015.10.006
- Mercer, Martin & Morris (2002), DOI: 10.1016/S1570-7946(02)80149-3
- Patel et al. (2018), DOI: 10.1109/IROS.2018.8593375
- Ji et al. (2024), DOI: 10.1016/j.chemolab.2024.105189

## 7. 제안 연구 방향

아직 확정 모델이 아니라 다음 설계 가설로만 유지한다.

```text
정상 상태 이력 + 과거 제어 이력
    → 정상적인 다음 상태 예측
    → 실제 다음 상태와 비교
    → 제어 맥락으로 설명되지 않는 residual 구성
    → residual의 시간적 변화 분석
    → 동일 오경보 조건에서 조기 고장탐지
```

이 구조를 구현하기 전에 기존 input-output residual 방법과의 수학적 차이를 먼저 확정해야 한다. 차이가 단순히 신경망 backbone이나 비선형 함수 사용에 그친다면 연구 방향을 수정해야 한다.

## 8. 앞으로의 연구 단계

1. Mercer 2002와 Ji 2024의 합법적 전체 원문 확보
2. 네 논문의 원 수식과 목적함수를 같은 표기법으로 대조해 mathematical gate 재개
3. `DISTINCTION_SURVIVES`일 때만 정확한 loss function 설계

현재 판정에서는 제안 방법을 구현하지 않는다.

## 9. 연구 가능성과 위험

### 가능성

- 560만 sample 규모의 공개 산업공정 시뮬레이션 전처리 데이터가 확보되어 있다.
- run-safe split, train-only scaling, 정상 threshold 정책이 구현되어 있다.
- seed 반복 가능한 baseline과 GPU 실험환경이 확보되어 있다.
- 제어기록의 추가 정보 신호가 세 seed와 모델 크기 통제에서 확인됐다.

### 위험

- CCA/CVA 및 input-output residual monitoring과 깊게 중복될 수 있다.
- action-conditioned prediction 자체는 기존 연구에 존재한다.
- Reinartz 데이터에는 XMV12와 operating mode가 없다.
- 효과가 일부 fault에 집중되어 있다.
- 제안 목적함수의 수학적 차별성이 아직 확정되지 않았다.

이 위험들은 모델을 먼저 구현해 해결할 문제가 아니다. 다음 단계에서 원문 수식 대조로 먼저 해소해야 한다.

## 10. 현재 결론

본 연구는 완성된 방법론을 주장하는 단계가 아니다. 공개 산업공정 시뮬레이션 데이터의 반복 예비실험은 일부 Fault에서 제어 맥락의 후속 연구 가치를 제한적으로 지지했다. Chen 원문에서 input-conditioned residual과의 직접 중복을 확인했지만 Mercer와 Ji의 전체 수식 대조가 완료되지 않았고 현재 residual 정의도 식별 가능한 분해로 정당화되지 않아 수학적 차별성은 `INCONCLUSIVE`이다.


## Mechanism and simulator feasibility audit (2026-08-14)

- F1 mechanism verdict: `MIXED_MECHANISM` (fault-specific XMV pattern plus early-warning behavior); this is not a causal control-effect claim.
- Candidate A: `INCONCLUSIVE / NOT ADOPTED`; Candidate B: `PROMISING_MODEL_CANDIDATE / NOT YET AUTHORIZED`.
- Pure-Python TEP normal/fault paired smoke test passed on Windows; simulator verdict: `SIMULATOR_READY_WITH_MINOR_WORK`.
- Primary direction: mechanism-first Reinartz analysis. Fallback: small same-seed paired simulation. No model or loss is authorized yet.
