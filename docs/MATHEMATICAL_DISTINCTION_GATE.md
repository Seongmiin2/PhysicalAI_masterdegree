# Mathematical Distinction Gate

## 1. 검토 대상과 판정

검토 후보는 다음과 같다.

\[
\hat{x}^{(0)}_{t+1}=f_x(X_t),\qquad
\hat{x}^{(1)}_{t+1}=f_{xu}(X_t,U_t)
\]

\[
c_t=\hat{x}^{(1)}_{t+1}-\hat{x}^{(0)}_{t+1},\qquad
e_t=x_{t+1}-\hat{x}^{(1)}_{t+1}
\]

\[
E_t=[e_{t-L+1},\ldots,e_t],\qquad s_t=\operatorname{TemporalModel}(E_t)
\]

최종 판정은 **`INCONCLUSIVE`**이다. Patel 2018은 전체 원문을 검토했지만 Chen 2016, Mercer 2002, Ji 2024는 초록/미리보기만 확보했다. 지정 기준에 따라 원문 미확보 논문에서 수식이나 방법 요소의 부재를 추정하지 않았다.

## 2. 표 1 — 기존 방법 수식 비교

| 항목 | Chen 2016 | Mercer 2002 | Patel 2018 | Ji 2024 |
|:---|:---:|:---:|:---:|:---:|
| 센서 이력 사용 | NOT_CONFIRMED | NOT_CONFIRMED | YES | YES |
| 제어/입력 사용 | YES | NOT_CONFIRMED | YES | NOT_CONFIRMED |
| 센서 전용 예측 | NOT_CONFIRMED | NOT_CONFIRMED | NO | NOT_CONFIRMED |
| 제어 조건부 예측 | NOT_CONFIRMED | NOT_CONFIRMED | YES | NOT_CONFIRMED |
| 두 예측의 차이 사용 | NOT_CONFIRMED | NOT_CONFIRMED | NO | NOT_CONFIRMED |
| residual 정의 | YES | YES | YES | YES |
| residual 시간 누적 | NOT_CONFIRMED | NOT_CONFIRMED | YES | YES |
| residual 시간모델 학습 | NOT_CONFIRMED | NOT_CONFIRMED | NO | NOT_CONFIRMED |
| 조기탐지 평가 | NOT_CONFIRMED | NOT_CONFIRMED | NO | YES |
| delay 직접 최적화 | NOT_CONFIRMED | NOT_CONFIRMED | NO | NOT_CONFIRMED |

`YES`는 해당 요소의 존재만 뜻하며 후보 수식과 동일하다는 뜻이 아니다. `NO`는 전체 원문을 확인한 Patel에서만 사용했다. 출처 상태는 [MATHEMATICAL_SOURCE_STATUS.md](MATHEMATICAL_SOURCE_STATUS.md)에 기록했다.

## 3. 논문별 검토

### 3.1 Chen et al. (2016)

- 상태: `ABSTRACT_ONLY`.
- 입력: 공정 input/output 블록을 사용한다는 점은 출판사 초록에서 확인했다. 과거 블록의 정확한 구성은 `NOT_CONFIRMED`이다.
- 정상관계 모델: static 및 dynamic CCA로 input-output 관계를 모델링한다.
- residual: 초록은 CCA로 residual signals를 구축한다고 명시하지만 원 수식과 식 번호는 확인하지 못했다. 공통 기호로의 정확한 변환도 보류한다.
- 점수·시간처리·학습목적·평가: 상세 원문 미확보로 `NOT_CONFIRMED`이다.
- 근거: publisher abstract, pp. 51–58의 서지정보. 실제 PDF page/section/equation은 확보하지 못했다.

### 3.2 Mercer, Martin & Morris (2002)

- 상태: `ABSTRACT_ONLY`.
- 입력: 공정 시계열을 다루지만 manipulated-variable block의 정확한 사용 여부는 `NOT_CONFIRMED`이다.
- 정상관계 모델: CVA로 얻은 state-space model을 사용한다는 범위까지 확인했다.
- residual: 초록 수준에서 model mismatch residual과 output prediction residual을 사용하고, residual에 PCA를 적용해 monitoring statistics를 만든다는 점만 확인했다. 원 수식은 확인하지 못했다.
- 시간처리: serial correlation과 false alarm/detection time 문제를 다루지만 구체적인 누적 또는 학습 시간모델은 `NOT_CONFIRMED`이다.
- 근거: publisher abstract 및 ESCAPE 12 proceedings metadata, pp. 727–732. 실제 PDF page/section/equation은 확보하지 못했다.

### 3.3 Patel et al. (2018)

- 상태: `FULL_TEXT_AVAILABLE`.
- 입력: 센서 영상 `x_t`와 actuator command `u_t`를 사용한다. SFAM은 `x_{t-3:t}`와 `u_{t-2:t+1}`로 `x_{t+1}`을 예측한다. 즉, 우리 금지조건과 달리 **미래 action `u_{t+1}`도 입력한다**. 근거: PDF p. 1, Section II; p. 3, Section III-B.1–2, Figs. 4–5.
- 정상관계 모델: action-conditioned PredNet/ConvLSTM 기반 video prediction과 adversarial optimization이다. 근거: PDF pp. 2–3, Section III-B.1–2.
- 원 residual/error: 각 계층에서 양방향 ReLU prediction error representation을 구성한다. 첫 계층의 공통 표현은 대략 `r_t = x_t-\hat{x}_t`의 부호분리 표현이며, 탐지 시에는 `d_t=(1-SSIM(x_{t+1},\hat{x}_{t+1}\mid u_{t+1}))/2`를 사용한다. 근거: PDF p. 3, Section III-B.1 및 III-B.3, Fig. 3. 논문은 이 식에 별도 equation number를 부여하지 않았다.
- 학습목적: error representations의 평균, `-SSIM(\hat{x}_{t+1},x_{t+1})`, `SSIM(\hat{x}_{t+1},x_t)`의 가중 결합을 먼저 최적화하고 adversarial stage를 추가한다. CFAM의 명시적 목적함수는 Eqs. (1)–(2)이지만 이는 `c_t/e_t` 분해 목적함수가 아니다. 근거: PDF pp. 2–3, Sections III-A.2, III-B.2.
- 탐지점수와 시간처리: action별 미래 frame의 DSSIM을 계산하고 최소 DSSIM action을 실제 action과 비교한다. multiple prediction frame windowing을 사용하지만 `e_t` evolution에 별도 학습목적을 두지는 않는다. 근거: PDF p. 3, Section III-B.3; pp. 4, 6, Figs. 6, 10–11.
- 평가: 실시간 사례와 threshold trigger를 보이지만 산업공정 fault onset 기반 detection delay를 평가하거나 직접 최적화하지 않는다. 근거: PDF pp. 4–6, Section IV-B.
- 직접 중복: `f_{xu}`형 action-conditioned 미래 관측 예측과 prediction dissimilarity는 강하게 중복된다. 그러나 sensor-only predictor `f_x`를 병렬 학습해 두 예측 차이 `c_t`를 쓰지는 않는다.

### 3.4 Ji et al. (2024)

- 상태: `ABSTRACT_ONLY`.
- 입력과 정상관계: CVDA의 past-projected/future-projected vectors로 canonical variate residuals(CVRs)를 만든다는 점까지 확인했다. 제어변수를 별도 block으로 쓰는지는 `NOT_CONFIRMED`이다.
- residual과 점수: CVR에 sliding time window를 적용하고 statistics vector/matrix를 만든 뒤 Mahalanobis distance index로 감시한다.
- 시간처리: residual의 sliding-window statistics가 명시되어 있으므로 시간창 사용은 `YES`이다. 학습되는 temporal model이나 delay 최적화는 원문 미확보로 `NOT_CONFIRMED`이다.
- 평가: 출판사 method/case-study snippet에 FAR와 FDR이 제시되고 incipient fault detection을 직접 다룬다. detection delay 평가는 `NOT_CONFIRMED`이다.
- 근거: publisher abstract, Introduction/Methodology/Case studies/Conclusions snippets. 실제 PDF page/equation은 확보하지 못했다.

## 4. 표 2 — 우리 아이디어와의 직접 비교

| 검토 요소 | 기존 연구에 존재하는가 | 가장 가까운 논문 | 우리 후보와 남은 차이 |
|:---|:---:|:---|:---|
| `X_t`로 다음 상태 예측 | YES | Patel 2018 | Patel은 action도 함께 쓰며 sensor-only 병렬 예측기는 없다. |
| `X_t,U_t`로 다음 상태 예측 | YES | Patel 2018 | action-conditioned prediction 자체는 차별점이 아니다. Patel은 `u_{t+1}`도 사용한다. |
| 두 예측의 차이 `c_t` | NOT_CONFIRMED | Patel 2018 | Patel 원문에는 없지만 나머지 세 원문의 부재를 확인하지 못했다. |
| 조건부 예측 residual `e_t` | YES | Patel 2018 | 현재 정의 그대로면 기존 action-conditioned prediction error와 본질적으로 같다. |
| `e_t`의 시간적 evolution 학습 | NOT_CONFIRMED | Ji 2024 / Patel 2018 | Ji는 sliding-window residual statistics, Patel은 temporal predictor와 prediction-frame window를 사용한다. 별도 evolution objective가 있어야 구별 가능하다. |
| 동일 오경보 조건의 조기탐지 | NOT_CONFIRMED | Ji 2024 | Ji는 incipient fault와 FAR/FDR을 다루지만 동일 FAR에서 delay 비교인지는 확인하지 못했다. |
| detection delay 관련 학습목표 | NOT_CONFIRMED | 해당 없음 | 확보된 Patel 원문에는 없으나 세 논문 원문 부재 때문에 전체 부재는 단정할 수 없다. |

## 5. 수학적 의미 검토

### `c_t`를 제어 설명 성분이라 부를 수 있는가

현재 정의만으로는 부를 수 없다. `c_t`는 입력집합과 파라미터가 서로 다른 두 모델의 예측 차이다. 두 모델의 근사오차, 최적화 편차, 모델 용량과 seed 차이도 포함한다. `U_t`가 독립적인 개입도 아니므로 `c_t`를 causal control effect로 해석할 수 없다. 현 단계의 정직한 명칭은 **control-history-associated prediction difference 후보**이다.

### `e_t`는 기존 prediction residual과 다른가

다르지 않다. 현재 식 `e_t=x_{t+1}-f_{xu}(X_t,U_t)`는 전형적인 조건부 prediction residual이다. Patel의 action-conditioned prediction dissimilarity와 직접 중복되며, 별도 구조나 목적함수가 없으면 새로운 residual이라고 주장할 수 없다.

### 별도 제약 없이 residual 분해인가

아니다. `c_t+e_t=x_{t+1}-\hat{x}^{(0)}_{t+1}`이라는 대수적 항등식은 성립하지만, 두 항의 식별 가능성이나 의미적 독립성은 보장하지 않는다. 공유 counterfactual 구조, orthogonality/invariance, 재구성 일관성 등 구체적 제약 후보가 필요하지만 이번 단계에서는 loss를 확정하지 않는다.

### residual evolution은 기존 시간처리와 다른가

`TemporalModel(E_t)`라는 표기만으로는 다르지 않다. Ji의 sliding-window residual statistics와 Patel의 recurrent temporal prediction보다 무엇을 새로 학습하며 왜 조기탐지에 유리한지를 목적함수 수준에서 정의해야 한다. 단순 CUSUM, window summary 또는 sequence backbone 교체는 차별점이 아니다.

### 정상 데이터만으로 가능한가

정상 조건에서 두 예측기와 조건부 prediction residual의 기준분포를 학습하는 것은 가능하다. 그러나 정상 데이터만으로 `c_t`가 제어 영향이고 `e_t`가 고장 영향이라는 의미적 분리를 식별할 수 있다는 보장은 없다. 그 주장은 별도 가정과 검증이 필요하다.

### XMV 해석 위험

XMV는 폐루프 controller response일 수 있다. 따라서 `U_t`를 독립적인 causal action 또는 intervention으로 부르지 않는다. 이 연구에서 허용되는 해석은 **과거 manipulated-variable history라는 관측 맥락**이다.

## 6. 최종 판정과 다음 행동

**판정: `INCONCLUSIVE`**

이유는 두 가지다.

1. 핵심 네 편 중 세 편의 전체 원문과 실제 수식을 확보하지 못해 `c_t`형 분해의 부재를 확인할 수 없다.
2. 현재 `e_t`는 기존 조건부 prediction residual과 같고, `c_t`는 두 독립 예측기의 차이에 불과하다. 이를 식별 가능한 분해로 만드는 구체적 학습 제약도 아직 정의되지 않았다.

따라서 Phase 3로 넘어가지 않는다. 새로운 모델이나 loss를 구현하지 않는다. 다음에 재개하려면 먼저 Chen 2016, Mercer 2002, Ji 2024의 합법적 전체 원문을 확보하고, 그 다음에만 수식 대조를 완료해야 한다. 추가 실험으로 이 불확실성을 덮지 않는다.
