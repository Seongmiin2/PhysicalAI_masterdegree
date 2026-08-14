# Mathematical Distinction Gate

## 1. 후보 구조와 최종 판정

```text
xhat_0 = f_x(X_t)
xhat_1 = f_xu(X_t, U_t)
c_t = xhat_1 - xhat_0
e_t = x_(t+1) - xhat_1
```

최종 판정은 **`INCONCLUSIVE`**이다. Chen 2016 전체 원문은 확보했지만 Mercer 2002와 Ji 2024는 여전히 초록만 확인됐다. 또한 Chen의 DCCA residual은 input-conditioned prediction residual과 수학적으로 강하게 겹치며, 현재 후보에는 `c_t`를 제어 영향으로 식별하거나 `e_t`를 기존 residual과 구별하는 제약이 없다.

## 2. 표 1 — 기존 방법 수식 비교

| 항목 | Chen 2016 | Mercer 2002 | Patel 2018 | Ji 2024 |
|:---|:---:|:---:|:---:|:---:|
| 센서 이력 사용 | YES | NOT_CONFIRMED | YES | YES |
| 제어/입력 사용 | YES | NOT_CONFIRMED | YES | NOT_CONFIRMED |
| 센서 전용 예측 | NO | NOT_CONFIRMED | NO | NOT_CONFIRMED |
| 제어 조건부 예측 | YES | NOT_CONFIRMED | YES | NOT_CONFIRMED |
| 두 예측의 차이 사용 | NO | NOT_CONFIRMED | NO | NOT_CONFIRMED |
| residual 정의 | YES | YES | YES | YES |
| residual 시간 누적 | NO | NOT_CONFIRMED | YES | YES |
| residual 시간모델 학습 | NO | NOT_CONFIRMED | NO | NOT_CONFIRMED |
| 조기탐지 평가 | YES | NOT_CONFIRMED | NO | YES |
| delay 직접 최적화 | NO | NOT_CONFIRMED | NO | NOT_CONFIRMED |

`NO`는 전체 원문에서 해당 구조의 부재를 확인한 Chen/Patel에만 사용했다. Mercer/Ji의 상세 요소는 원문 미확보 때문에 `NOT_CONFIRMED`이다.

## 3. Chen et al. (2016) 원문 수식 검토

### 3.1 입력과 출력

Chen은 `u(k)`를 process input, `y(k)`를 process output으로 정의한다. 정적 모델은 다음과 같다.

\[
y(k)=\Psi_u u(k)+\Psi_y v(k) \tag{2}
\]

근거: journal p. 52, Section 3, Eq. (2). Table 1은 CCA가 온라인 측정 가능한 input과 output을 모두 사용해 input/output/process 변화를 탐지한다고 명시한다. AEP 사례의 Table 4는 fresh steam flow와 evaporator liquor inlet flows를 manipulated variables로 명시하므로, 논문의 input block에는 실제 조작변수가 포함된다.

### 3.2 정적 residual

일반 parity residual을 소개한 뒤 Chen은 CCA residual을 다음처럼 정의한다.

\[
r(k)=L^T y(k)-M^T u(k) \tag{1}
\]

CCA로 `L`과 `M`을 구한 뒤 동일 형식이 Eq. (9)로 다시 제시된다. residual의 quadratic statistic은

\[
Q_{cca}(k)=r^T(k)r(k) \tag{10}
\]

이며 Eq. (11)의 threshold와 비교한다. 근거: journal pp. 51–53, Sections 2–3, Eqs. (1), (9)–(11).

공통 표기로 보면 `M^Tu(k)`가 input으로 설명되는 output canonical component이고 `L^Ty(k)`와의 차이가 residual이다. 그러나 이는 `y(k)` 자체에 대한 두 예측기의 차이가 아니라 한 CCA projection residual이다.

### 3.3 동적 시계열 구성과 residual

DCCA는 미래 output block `y_f(k)`의 의존성을 다음 두 입력 묶음으로 모델링한다.

- `z_p(k)`: 과거 input과 output의 lagged block
- `u_f(k)`: 현재/미래 input block

근거: journal p. 53, Section 4.1, Eq. (14)와 그 직전 설명. 논문은 미래 output `y_f`가 past inputs/outputs `z_p`와 future inputs `u_f`에 의존한다고 명시한다.

Eq. (21)의 관계를 CCA로 식별하고, DCCA residual을 다음처럼 정의한다.

\[
r(k)=L_d^T y_f(k)-M_d^T
\begin{bmatrix}
z_p(k)\\
u_f(k)
\end{bmatrix} \tag{24}
\]

그 뒤 residual covariance를 Eq. (25)로 계산하고

\[
T_r^2(k)=(N-1)r^T(k)(I-\Lambda_n^2)^{-1}r(k) \tag{26}
\]

을 Eq. (27)의 threshold와 비교한다. 근거: journal pp. 53–54, Sections 4.1–4.2, Eqs. (21)–(27), Table 2.

중요한 차이는 Chen DCCA가 **미래 input `u_f`를 사용한다는 점**이다. 우리 실험 정책은 미래 XMV를 입력으로 금지하고 과거 `U_t`만 사용한다.

### 3.4 시간 처리와 평가

Chen은 lagged interval로 동역학을 CCA residual에 포함하지만 residual sequence의 evolution을 별도 모델로 학습하지 않는다. 각 시점의 `T_r^2`를 threshold와 비교하며, 실제 false alarm 억제를 위해 여섯 연속 초과 시 fault를 선언하는 기존 규칙을 언급한다. FDR과 detection delay를 평가하지만 delay를 학습목적으로 직접 최적화하지 않는다. 근거: journal pp. 54, 56, Sections 4.2, 6.2, Table 2 및 Section 7 직전 논의.

## 4. 우리 구조와 Chen의 직접 비교

| 후보 요소 | Chen과 중복 | 근거와 남은 차이 |
|:---|:---:|:---|
| `xhat_0=f_x(X_t)` | NO | Chen에는 sensor/output history만으로 미래 output을 예측하는 병렬 모델이 없다. |
| `xhat_1=f_xu(X_t,U_t)` | YES | Eq. (24)는 past input/output와 future input으로 future output canonical component를 설명한다. 단, full-state neural forecast가 아닌 선형 CCA projection이고 미래 input도 사용한다. |
| `c_t=xhat_1-xhat_0` | NO | Chen은 sensor-only predictor와 input-conditioned predictor를 함께 두거나 그 차이를 계산하지 않는다. |
| `e_t=x_(t+1)-xhat_1` | YES | Eq. (24)는 변환된 future output과 input-conditioned 설명항의 차이다. 좌표와 horizon은 다르지만 조건부 prediction residual이라는 핵심은 겹친다. |
| `TemporalModel(E_t)` | NO | lagged block을 사용하지만 residual evolution에 별도 학습모델이나 목적함수를 두지 않는다. |

따라서 Chen에서 **겹치는 부분**은 input/manipulated-variable-conditioned output relation, 동적 lag block, residual과 threshold 기반 fault detection이다. **겹치지 않는다고 확인된 부분**은 두 병렬 예측기의 차이 `c_t`와 residual evolution을 별도 학습하는 구조다. 하지만 이 부재만으로 우리 후보의 차별성이 성립하지는 않는다.

## 5. 나머지 논문 상태

### Mercer, Martin & Morris (2002)

상태는 `ABSTRACT_ONLY`다. 합법적인 공개 전체 원문을 다시 검색했지만 출판사 초록과 proceedings metadata를 넘는 원문을 확보하지 못했다. state-space model mismatch와 output prediction residual을 PCA 통계로 감시한다는 초록 범위만 유지하며, 상세 수식이나 두 예측 구조의 부재를 추정하지 않는다.

### Patel et al. (2018)

상태는 `FULL_TEXT_AVAILABLE`이다. `x_{t-3:t}`와 `u_{t-2:t+1}`로 `x_{t+1}`을 예측하고 prediction/observation DSSIM을 감시한다. action-conditioned prediction residual은 직접 중복되지만 sensor-only 병렬 predictor나 `c_t`는 없다. 자세한 근거는 기존 원문 검토 기록과 동일하다.

### Ji et al. (2024)

상태는 `ABSTRACT_ONLY`다. ResearchGate에는 “No full-text available”로 표시된다. 출판사 공개 범위에서 CVDA residual, sliding-window statistics matrix, Mahalanobis index, FAR/FDR은 확인되지만 상세 수식과 학습목적은 추정하지 않는다.

## 6. 수학적 의미와 Gate 판정

Chen 원문으로 다음은 분명해졌다.

1. input/output-conditioned residual은 이미 존재한다. 현재 `e_t=x_{t+1}-f_{xu}(X_t,U_t)`는 그 일반적 형태와 강하게 겹친다.
2. Chen에는 두 예측기의 차이 `c_t`가 없다. 그러나 `c_t`는 현재 서로 다른 두 모델의 근사·최적화 오차까지 포함하므로 제어 영향으로 식별되지 않는다.
3. `TemporalModel(E_t)`라는 표기만으로는 residual window/statistics와 구별되는 학습목적이 아니다.
4. XMV는 controller response일 수 있으므로 causal intervention으로 해석하지 않는다.

**최종 판정: `INCONCLUSIVE`**

원문 근거는 Chen Eq. (24)가 `e_t`와 강하게 겹치고 Chen에는 `c_t`가 없다는 것이다. 그러나 Mercer/Ji 전체 원문이 없고, 더 근본적으로 현재 후보에는 `c_t/e_t`를 식별 가능한 분해로 만드는 제약이 없다. 따라서 `DISTINCTION_SURVIVES`도 `OVERLAP_TOO_HIGH`도 확정하지 않는다.

Phase 3 및 loss 설계로 넘어가지 않는다. 다음 단일 작업은 Mercer 2002와 Ji 2024의 합법적 전체 원문을 확보해 equation-level 비교를 완료하는 것이다.
