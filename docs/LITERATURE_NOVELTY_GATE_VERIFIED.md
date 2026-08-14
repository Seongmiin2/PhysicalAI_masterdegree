# Literature Novelty Gate — Verified

## 검토 범위

서지정보와 연구 직접성이 검증된 9편만 사용했다. 원문 전체를 확인하지 못한 논문은 공식 초록이 말하는 범위 밖의 목적함수·residual 구조를 추정하지 않았다.

## 핵심 논문 비교

| 논문 | 연구 문제 | 입력 | 정상 모델 | Residual | 탐지 방식 | 시간 변화·조기탐지 | 우리 연구와 중복 | 남은 차이 | 검증 근거 |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| [Wang, Seborg & Larimore, 1997](https://doi.org/10.1016/S1474-6670(17)43211-3) | input-output data에서 동적 공정 모델을 식별하고 정상 모델 차이를 감시 | 공정 input/output | 선형 stochastic CVA state-space | 공식 초록은 별도 residual 정의를 상세히 밝히지 않음 | 여러 시계열에서 식별된 모델의 통계적 차이 | 조기탐지 직접 최적화는 확인 안 됨 | 입력과 출력을 함께 사용한 정상 동역학 모델 | learned control-unexplained residual 및 그 evolution 없음 | IFAC/Elsevier 공식 초록, Seborg publication list; `ABSTRACT_VERIFIED` |
| [Negiz & Çinar, 1998](https://doi.org/10.1016/S0959-1524(98)00006-7) | 폐루프 연속공정의 autocorrelated, cross-correlated, collinear data 감시 | 과거 process measurements | 과거 측정의 선형결합인 CV states가 미래 측정 변동을 최대 설명 | state model의 noise/residual space 개념 | CV state의 T² statistic | 시간 동역학은 다루지만 지연 목적함수는 아님 | 폐루프 정상 과거→미래 설명이라는 핵심 문제 설정 | manipulated variables를 별도 conditioning block으로 분리하지 않음 | Elsevier 공식 초록; `ABSTRACT_VERIFIED` |
| [Chen et al., 2016](https://doi.org/10.1016/j.conengprac.2015.10.006) | 명시적 input-output 관계가 있는 static/dynamic process fault detection | 온라인 측정 가능한 input/output blocks | 정상 input-output canonical correlation | CCA 관계에서 벗어난 residual signal | residual-based monitoring statistic/control limit | dynamic method가 더 나은 탐지를 보이나 지연 직접 최적화는 확인 안 됨 | input/control과 output을 공동 모델링해 unexplained component를 감시 | 비선형 sequence forecast와 residual evolution 학습은 확인 안 됨 | Elsevier 공식 초록; `ABSTRACT_VERIFIED` |
| [Mercer, Martin & Morris, 2002](https://doi.org/10.1016/S1570-7946(02)80149-3) | dynamic PCA/CVA statistic의 serial correlation과 false alarm/delay 문제 | 공정 시계열; 사례에서 manipulated variable 포함 | CVA state-space model | model mismatch 및 output prediction residual | residual에 PCA를 적용한 T²/SPE 계열 statistic | serial correlation이 false alarm 또는 detection time에 미치는 영향 | output prediction residual 감시와 직접 중복 | control-only explainability 분리 및 learned residual evolution 없음 | Elsevier 공식 초록·section preview; `ABSTRACT_VERIFIED` |
| [Alcala, Dunia & Qin, 2012](https://doi.org/10.3182/20120829-3-MX-2028.00238) | dynamic transient의 false alarm을 줄이는 process monitoring/diagnosis | TEP dynamic process data | PCA 기반 subspace identification (SIMPCA) | parity space와 complemental space | 두 공간의 multivariate statistics | 동적 transient를 다루지만 조기지연 직접 최적화는 아님 | 정상 동적 모델로 설명되지 않는 성분 감시 | input/manipulated-variable-conditioned forecast 및 temporal residual learner 없음 | IFAC/Elsevier 초록·대학 메타데이터; `ABSTRACT_VERIFIED` |
| [Bin Shams, Budman & Duever, 2011](https://doi.org/10.1016/j.ces.2011.05.028) | 기존 방법이 놓친 TEP fault의 detection/identification/diagnosis | 모든 available process measurements | normal PCA model | PCA T²/Q statistic에 들어가는 deviation | variable-wise CUSUM을 누적한 PCA monitoring | 누적 통계와 average run length로 어려운 fault 탐지 | 시간 누적을 이용한 민감도 및 탐지시점 개선 | 제어로 설명되는 정상 반응을 먼저 제거하지 않음 | Elsevier 공식 초록·section preview; `ABSTRACT_VERIFIED` |
| [Bin Shams, Budman & Duever, 2011, feedback observability](https://doi.org/10.1021/ie101238q) | feedback control을 이용해 TEP의 관측하기 어려운 fault를 더 잘 드러냄 | closed-loop process measurements와 controller setting | 표준 monitoring charts와 feedback retuning | 별도 learned residual 정의는 확인 안 됨 | feedback tuning으로 fault observability 변화 | detection time과 product variability/economics trade-off | controller response가 fault visibility에 영향을 준다는 직접 근거 | 과거 control history로 passive normal prediction을 수행하는 연구는 아님 | ACS 공식 초록; `ABSTRACT_VERIFIED` |
| [Patel et al., 2018](https://doi.org/10.1109/IROS.2018.8593375) | learning-based autonomous controller/system의 online anomaly 감시 | sensor images와 actuator commands | actuator command에 condition된 future observation/video prediction | predicted future와 observed evolution의 차이 | controller-focused와 system-focused anomaly monitors | online monitoring이나 industrial incipient delay 목적은 아님 | action-conditioned future observation prediction과 prediction error가 직접 중복 | 영상 자율주행 맥락; control-explainable residual 분리와 산업 fault evolution objective 없음 | IEEE metadata 및 공개 author manuscript; `FULL_TEXT_VERIFIED` |
| [Ji et al., 2024](https://doi.org/10.1016/j.chemolab.2024.105189) | dynamic process의 incipient fault 민감도 개선 | past/future projected process vectors | CVDA로 canonical variate residual 생성 | canonical variate residual | residual sliding-window statistics로 matrix를 만들고 Mahalanobis index | residual 자체 대신 시간창 통계를 감시하여 incipient fault 탐지 | residual의 시간적 변화로 조기/미세 fault를 감시한다는 점이 직접 중복 | control history로 residual의 설명가능 성분을 분리하지 않음 | Elsevier 공식 초록·method preview; `ABSTRACT_VERIFIED` |

## 연구 질문별 검증

### 1. 입력과 센서를 함께 사용하는 기존 방법이 이미 같은 문제를 해결하는가?

상당 부분 해결한다. Wang은 input-output state-space identification을, Chen은 input-output CCA residual fault detection을 다룬다. Patel은 actuator-command-conditioned future observation prediction으로 anomaly를 판단한다. 따라서 “제어변수를 넣어 미래 센서를 예측하고 오차를 본다” 자체는 연구 차별점이 아니다.

### 2. 기존 residual은 제어로 설명되지 않는 변화만 남기는가?

부분적으로만 그렇다. CCA/CVA/state-space residual은 정상 input-output 또는 과거-미래 관계에서 설명되지 않는 성분이다. 그러나 이번에 확인한 문헌에서 controller response와 fault effect를 명시적으로 두 표현으로 분해하고 각 성분에 별도 학습 제약을 주는 구조는 확인하지 못했다. 이 차이는 원문 수식 정밀대조 전에는 확정할 수 없다.

### 3. residual의 시간 변화를 이미 학습하거나 누적하는가?

그렇다. Bin Shams 등은 CUSUM 누적 통계를 사용하고, Ji 등은 residual sliding-window statistics를 구성한다. 따라서 residual의 시간 누적 또는 시간창 통계 자체도 차별점이 아니다. “temporal model을 붙인다”는 설명만으로는 부족하다.

### 4. 기존 방법이 조기탐지 지연을 직접 최적화하는가?

검증된 핵심 문헌은 빠른/incipient detection과 detection time을 평가하지만, 정상 예측 손실과 fault onset 이후의 detection delay를 함께 직접 최적화하는 학습 목적함수는 확인하지 못했다. 다만 원문 전체를 보지 못한 논문에는 이 부재를 단정하지 않는다.

### 5. 구별되는 학습 목적함수를 만들 연구 여지가 있는가?

후보는 있다. 단, 다음 세 조건을 동시에 만족해야 한다.

1. 단순 input-output forecast 또는 CCA/CVA residual과 수학적으로 달라야 한다.
2. 단순 CUSUM/sliding-window residual statistics와 달리 control-unexplained component의 evolution을 학습해야 한다.
3. 동일 false-alarm 정책 아래 detection delay 개선을 검증 가능한 목표로 연결해야 한다.

### 6. GRU나 새로운 신경망을 사용하는 것이 차이인가?

아니다. backbone 변경, 비선형화, attention 또는 더 큰 모델은 연구 공백이 아니다.

## 판정

**`VIABLE_GAP_CANDIDATE`**

판정 이유:

- 강한 중복: input-output dynamics, action-conditioned prediction, prediction residual, residual 시간 누적은 모두 이미 존재한다.
- 제한된 잔여 후보: 산업 폐루프 데이터에서 control-explainable transition과 control-unexplained residual을 학습 목적상 명시적으로 분리하고, 후자의 evolution을 동일 false-alarm 조건의 detection-delay 목표와 연결하는 조합은 이번 검증 범위에서 확인하지 못했다.
- 따라서 연구 방향은 유지할 수 있지만, 아직 제안 방법의 독창성이나 학술적 차별성이 확정된 것은 아니다.

## 다음 단계

새 모델 구현 전에 다음 한 가지를 수행한다.

> Wang 1997, Chen 2016, Mercer 2002, Patel 2018의 수식과 목적함수를 원문 기준으로 나란히 재구성하여, proposed objective가 기존 input-output residual monitoring과 정확히 어디서 달라지는지 한 페이지의 mathematical distinction table로 확정한다.
