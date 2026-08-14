# Literature Novelty Gate — Preliminary Review

> **SUPERSEDED — bibliographic mismatches were found.**
>
> Do not use this document for research claims or citations.
>
> See `LITERATURE_SOURCE_AUDIT.md` and `LITERATURE_NOVELTY_GATE_VERIFIED.md`.

## 범위와 판정

Phase 1 통과 후 센서·제어변수 공동 사용, input/action-conditioned dynamics, prediction residual, closed-loop feedback 영향, residual 시간 변화와 조기탐지를 직접 다루는 **14편**을 우선 검토했다. 블로그와 일반 설명자료는 제외했다.

**예비 판정: `PARTIAL_OVERLAP`**

아이디어의 개별 구성요소는 이미 강하게 존재한다. 입력/출력 또는 actuator/sensor를 함께 모델링해 residual로 감시하는 연구, action-conditioned 미래 관측 예측과 prediction error 기반 anomaly detection, closed-loop 상관과 feedback 영향 문제, residual의 시간적 통계와 CUSUM을 이용한 incipient/early detection이 각각 존재한다.

다만 이번 예비 검토에서는 **정상 산업 공정에서 과거 manipulated-variable history로 정상 센서 미래를 조건부 예측하고, control-explainable 변화와 unexplained residual을 명시적으로 분리한 뒤, 그 residual evolution을 조기 고장탐지의 학습 대상으로 삼는 완전한 조합**이 동일하게 제시된 논문은 확인하지 못했다. 이는 `CLEAR_RESEARCH_GAP` 또는 novelty 주장이 아니라 더 체계적인 원문 검토가 필요한 부분 중복 상태다.

## 핵심 논문

| # | 논문 | 연구 문제 | 입력 데이터 | 방법 | 고장탐지·조기탐지 | 우리 연구와 중복 | 남은 차이 |
|---:|:---|:---|:---|:---|:---|:---|:---|
| 1 | [Negiz & Çinar, 1998](https://doi.org/10.1016/S0959-1524(98)00006-7) | 폐루프 연속공정 동적 모니터링 | 과거 공정 측정; closed-loop 상관 명시 | CV state-space, 과거로 미래 변동 설명 | T² 상태 통계; 지연 특화 아님 | 정상 과거→미래 동역학과 closed-loop 맥락 | 제어변수 조건부 분리와 residual evolution 없음 |
| 2 | [Russell et al., 2000](https://doi.org/10.1016/S0169-7439(00)00058-7) | 동적 산업공정/TEP fault detection | TEP process variables | PCA·DPCA·CVA state/residual space | sensitivity, promptness, robustness | TEP, 동적 residual, promptness | learned action-conditioned predictor 없음 |
| 3 | [Wang et al., 1997](https://doi.org/10.1016/S1474-6670(17)43211-3) | 입력-출력 데이터로 동적 공정 감시 | process input/output | CVA 선형 stochastic state-space 식별 | 통계 가설검정 | 제어/입력과 출력 공동 모델링 | 비선형 learned residual separation 없음 |
| 4 | [Jiang et al., 2016](https://doi.org/10.1016/j.conengprac.2015.10.006) | input-output 관계가 있는 공정 fault detection | 온라인 input/output | CCA residual, static/dynamic scheme | residual control limit | input/control-conditioned output residual과 근접 | sequence forecast와 residual evolution 없음 |
| 5 | [Mercer et al., 2002](https://doi.org/10.1016/S1570-7946(02)80149-3) | serially correlated monitoring statistic | 공정 변수와 manipulated variable | CVA state-space mismatch/output prediction residual에 PCA | false alarm/delay 문제 | output prediction residual 감시 | control-explainable/unexplained 표현 분리 없음 |
| 6 | [Rato & Reis, 2013](https://doi.org/10.1016/j.chemolab.2013.04.002) | autocorrelation을 고려한 공정 감시 | TEP multivariate time series | DPCA와 decorrelated residual | Q/SPE monitoring | residual autocorrelation 제거 | 제어변수 조건부 dynamics가 아님 |
| 7 | [Negiz et al., 2012](https://doi.org/10.3182/20120829-3-MX-2028.00238) | transient false alarm을 줄이는 동적 감시 | TEP dynamic data | subspace identification + PCA, parity spaces | multivariate statistic | 시스템 동역학 기반 residual/parity 감시 | nonlinear action-conditioned forecast 없음 |
| 8 | [Ge et al., 2017](https://doi.org/10.1016/j.chemolab.2016.11.007) | fault root cause와 feedback 영향 구분 | TEP 측정·manipulated variables | DPCA, reconstruction contribution, Granger/DTW | DPCA 탐지 후 진단 | feedback 때문에 변수가 연루될 수 있음을 명시 | control response를 conditioning으로 분리하지 않음 |
| 9 | [Rato et al., 2011](https://doi.org/10.1016/j.ces.2011.05.028) | 기존 방법이 놓치는 TEP fault 탐지 | available TEP measurements | CUSUM-PCA T²/Q | 어려운 fault 탐지와 시간 누적 | 시간 누적으로 민감도 향상 | control-conditioned residual이 아님 |
| 10 | [Dunia et al., 2018](https://doi.org/10.1016/j.ifacol.2018.09.377) | stochastic/미세 fault의 빠른 탐지 | TEP measured variables | EEMD, PCA, CUSUM | 작은 detection delay 평가 | fault signature temporal accumulation | 제어 기록 기반 정상 반응 설명 없음 |
| 11 | [Lee et al., 2008](https://doi.org/10.3182/20080706-5-KR-1001.01252) | 동적 비가우시안 TEP 감시·분류 | lagged process variables | DICA, ARX lag selection, SVM | online detection/classification | 동적 lag와 fault detection | residual 분리·제어 조건부 예측 없음 |
| 12 | [Zhu et al., 2018](https://arxiv.org/abs/1811.04539) | 학습 기반 자율시스템 anomaly 감시 | sensor observations와 actuator commands | sensor→action CFAM, **action-conditioned observation prediction** SFAM | predicted/observed evolution 차이 | 핵심 구조와 가장 직접 중복 | 영상/자율시스템이며 산업공정 residual evolution과 다름 |
| 13 | [Pasqualetti et al., 2013](https://doi.org/10.1109/TAC.2013.2266831) | CPS failure/attack detectability와 monitor 한계 | state/output 및 known/unknown inputs | descriptor-system dynamic monitors, zero dynamics | detectability·identifiability | control-aware dynamic monitoring 이론 | 데이터 기반 정상 dynamics·incipient fault와 목적이 다름 |
| 14 | [Gao et al., 2024](https://doi.org/10.1016/j.chemolab.2024.105189) | dynamic process incipient fault 민감도 | past/future projected process vectors | CV residual, sliding-window statistics, Mahalanobis index | incipient fault/FDR/FAR | residual 시간 변화로 미세 고장 탐지 | 제어변수 조건부 설명과 separation 없음 |

## 직접 아이디어 중복 판정

검토 아이디어: 정상 상태와 과거 제어기록으로 정상 미래 반응을 예측하고, 제어로 설명되는 변화와 설명되지 않는 고장성 변화를 구분한 뒤, 설명되지 않는 residual의 시간적 변화를 이용해 조기 탐지한다.

| 구성요소 | 선행 존재 | 근거 |
|:---|:---:|:---|
| 센서와 제어/입력의 공동 동적 모델 | 있음 | Wang 1997, Negiz 1998, Jiang 2016 |
| action-conditioned 미래 관측 예측으로 anomaly 판단 | 있음 | Zhu 2018 SFAM |
| output prediction residual 기반 공정 감시 | 있음 | Mercer 2002, Jiang 2016 |
| closed-loop feedback가 fault 해석을 교란 | 있음 | Negiz 1998, Ge 2017 |
| residual/통계 시간 변화로 early detection | 있음 | Rato 2011, Dunia 2018, Gao 2024 |
| 위 요소를 산업공정의 learned control-explainable/unexplained representation으로 명시적 결합 | 미확인 | 체계적 원문·인용망 검토 필요 |

## 남은 연구 질문과 위험

단순히 XMV를 입력에 추가하거나 residual을 계산하는 것은 연구 공백이 아니다. 가능한 좁은 질문은 다음과 같다.

> 산업 폐루프 시계열에서 과거 manipulated-variable history가 설명하는 정상 state transition과 설명하지 못하는 residual을 학습 과정에서 구분하고, 후자의 temporal evolution이 동일 false-alarm 조건에서 incipient fault detection delay를 줄이는가?

CCA/CVA input-output residual monitoring과 SFAM action-conditioned prediction이 핵심 구조를 이미 포함하므로 중복 위험이 높다. 이들과의 수학적·실험적 차이가 명확하지 않으면 proposed method를 구현해서는 안 된다. XMV는 controller response일 수 있으므로 causal intervention으로 부르지 않는다.

## 다음 단계 제한

다음 한 단계는 **고중복 논문 4편(Negiz 1998, Jiang 2016, Mercer 2002, Zhu 2018)의 원문 목적함수·residual 정의·탐지 통계를 정밀 대조하는 것**이다. 그 전에는 CDREL 또는 새 네트워크를 구현하지 않는다.
