# 석사학위 논문 연구기획 및 상세 실험설계서 v1.0

> **작성일:** 2026-08-12  
> **연구 분야:** Industrial AI / Prognostics & Health Management (PHM) / Multivariate Time-Series / Cyber-Physical Systems  
> **핵심 방법론 가칭:** **Control-Conditioned Residual Dynamics Learning (CCRDL)**  
> **최종 응용:** Physical AI 기반 24시간 무인 무선충전 이상진단·복구 시스템  
> **문서 목적:** 이 문서 하나를 기준으로 논문 주제 검토, 데이터 수집, DB 구성, 전처리, baseline 재현, 제안모델 구현, 실험, 논문 작성까지 이어갈 수 있도록 한다.

---

# 0. 먼저 읽는 2페이지 요약

## PAGE 1. 무엇을 연구하는가?

### 0.1 문제를 한 문장으로

> **기계가 고장 난 모양을 외우게 하는 것이 아니라, 특정 제어 명령을 받았을 때 원래 어떻게 반응해야 정상인지를 딥러닝이 학습하고, 그 정상 반응이 시간에 따라 무너지기 시작하는 순간을 조기에 찾아내는 AI를 연구한다.**

산업 장비에는 이미 기본적인 Rule이 존재한다.

예:

```text
충전 시작 명령
    ↓
릴레이 ON
    ↓
전류 증가
    ↓
전력 전달
    ↓
온도 완만한 상승
```

따라서 다음 정도는 AI가 아니라 Rule로 처리할 수 있다.

```text
온도 > 80℃ → 과온 Fault
통신 끊김 > 5 s → Communication Fault
충전 중 Current = 0 → 이상 후보
```

하지만 다음 상황은 Rule만으로 어렵다.

```text
                  정상                 초기 이상

충전 시작          충전 시작             충전 시작
   ↓                  ↓                    ↓
전류              정상 속도로 상승       평소보다 조금 느림
전압              정상                   정상
온도              완만히 상승            평소보다 조금 빠름
효율              91%                    88%
통신지연           10 ms                  25 ms

※ 모든 값은 아직 개별 허용범위 안에 있을 수 있음.
```

**핵심 문제는 각 센서의 절대값이 아니라, “같은 명령에 대한 시스템 전체의 반응 방식”이 정상과 달라지는 것을 찾는 것**이다.

---

### 0.2 우리가 만들 AI

```text
[과거 센서 상태 X]
        +
[제어 입력 A]
        +
[운전 조건 C]
        │
        ▼
┌────────────────────────────┐
│ 정상 반응 예측 딥러닝 모델 │
│ Probabilistic Dynamics     │
└─────────────┬──────────────┘
              │
              ▼
        정상 미래의 분포
              │
        실제 반응과 비교
              │
              ▼
          Residual
              │
              ▼
┌────────────────────────────┐
│ Residual Dynamics Encoder  │
│ "오차가 어떻게 변하는가?" │
└─────────────┬──────────────┘
              │
      ┌───────┼────────┐
      ▼       ▼        ▼
   조기이상   미지      이상에
    탐지      고장      기여한 변수
```

기본 residual은 다음과 같다.

\[
R_t = X_t - \hat X_t
\]

그러나 논문의 핵심은 단순히 `|R_t| > threshold`가 아니다.

```text
시간 →
Current residual      · · ↑ ↑ ↑
Temperature residual  · · · ↑ ↑ ↑
Efficiency residual   · ↓ ↓ ↓ ↓ ↓
Communication         · · ↑ · ↑ ↑
```

처럼 **여러 변수의 오차가 어떤 순서와 관계로 누적·전파되는지**를 학습하는 것이 핵심 후보이다.

---

### 0.3 논문의 핵심 Contribution 후보

가장 우선적으로 검증할 연구 아이디어는 다음이다.

> **Control-conditioned probabilistic normal dynamics + uncertainty-aware residual + temporal/inter-variable residual evolution representation**

한국어로는:

> **제어 조건부 확률적 정상 동역학 모델과 잔차 진화 표현학습을 이용한 산업 설비 초기 이상 탐지**

아직 “세계 최초”라고 확정하지 않는다.  
최종 novelty는 최신 선행연구를 systematic하게 비교한 뒤 확정한다.

---

## PAGE 2. 어떻게 검증하고 실제 시스템에 연결하는가?

### 0.4 Dataset 역할

```text
Extended Tennessee Eastman
        │
        ├─ 제어변수(XMV) + 공정센서(XMEAS)
        ├─ 정상/28개 Fault
        └─ Control-response / Fault Detection
                    │
                    ▼

GE-UTK Servomotor Degradation
        │
        ├─ demanded position → 명시적 명령
        ├─ actual position/current/speed/torque
        └─ command-response + degradation
                    │
                    ▼

N-CMAPSS
        │
        ├─ 정상 → 점진적 degradation → failure
        ├─ 여러 failure mode
        └─ Early degradation / Open-set 평가
                    │
                    ▼

HAI 또는 SWaT
        │
        └─ 다른 산업 CPS로 외부 일반화
                    │
                    ▼

WiPowerOne Wireless Charging
        │
        └─ 최종 feasibility/application case
```

**중요:** N-CMAPSS의 `TRA`는 control-like 변수이지만 공식적으로 scenario descriptor `W`에 포함된다. 따라서 N-CMAPSS만으로 “action-conditioned”의 핵심 주장을 강하게 하지 않는다. **Action-conditioned 핵심 검증은 TEP와 GE-UTK Servomotor를 우선 사용한다.**

---

### 0.5 회사 적용에서 RAG의 위치

RAG는 이상탐지 모델 자체가 아니다.

```text
논문에서 만든 AI
   ↓
"전류/온도/통신 관계 이상"
   ↓
RAG
   ├─ 장비 사양서
   ├─ 고장코드
   ├─ 제어 매뉴얼
   ├─ 과거 장애 이력
   └─ 복구 SOP
   ↓
LLM / Reasoner
   ↓
복구 후보
   ↓
Safety Rule
   ↓
자동복구 또는 관리자 확인
```

**논문의 AI = 상태를 판단하는 모델**  
**RAG = 판단 이후 현장 지식을 연결하는 계층**

---

# PART I. 연구의 문제 정의

## 1. 연구 배경

산업 설비의 고장진단은 일반적으로 다음 세 가지 축으로 이루어진다.

1. **Rule-based monitoring**
2. **Supervised fault classification**
3. **Data-driven anomaly detection**

각 방법은 유용하지만 다음 문제가 있다.

### 1.1 Rule 기반 시스템

장점:

- 규칙이 명확하다.
- 안전 한계 위반을 빠르게 잡는다.
- 설명이 쉽다.

한계:

- 명시적으로 작성하지 않은 관계를 찾기 어렵다.
- 여러 센서 간 미세한 상호작용 변화를 모두 규칙으로 작성하기 어렵다.
- 허용범위 안에서 진행되는 점진적 이상은 단일 threshold로 탐지하기 어렵다.

따라서 **Rule은 폐기 대상이 아니라 Safety Layer로 유지**한다.

---

### 1.2 Supervised Fault Classifier

예:

```text
Input → Neural Network → Fault A / Fault B / Fault C
```

이 방식은 학습된 class에는 강할 수 있으나 다음을 별도로 고려해야 한다.

- fault label 확보 비용
- class imbalance
- 학습에 없던 fault 상태
- 새로운 운전조건에 따른 distribution shift

따라서 본 연구는 **“미지 고장이 자주 발생한다”라고 전제하지 않는다.**  
대신 **학습되지 않은 fault가 발생할 가능성을 시스템 설계상 고려하고, 이를 open-set 실험으로 검증한다.**

---

### 1.3 일반적인 시계열 이상탐지

기존 MTSAD는 다음과 같은 문제를 다룬다.

```text
과거 센서 → reconstruction 또는 forecasting → anomaly score
```

그러나 실제 CPS에서는 다음 정보가 중요하다.

```text
현재 상태 X
    +
무슨 제어가 들어갔는가 A
    +
현재 운전조건은 무엇인가 C
```

본 연구는 **sensor-only 모델과 control/context-conditioned 모델을 직접 비교하여 이 정보의 가치가 실제로 있는지 먼저 검증**한다.

---

# 2. 최종 연구 문제

## 2.1 쉬운 표현

> **같은 상태에서 같은 명령을 내렸을 때 정상 장비가 보여야 하는 반응을 AI가 학습하고, 실제 장비 반응이 정상 반응 분포에서 서서히 벗어나는 과정을 학습하면 기존 방법보다 고장을 더 일찍, 더 안정적으로 탐지할 수 있는가?**

---

## 2.2 정식 Problem Formulation

과거 센서 시계열:

\[
X_{t-L+1:t} \in \mathbb{R}^{L \times d_x}
\]

과거/현재 제어 입력:

\[
A_{t-L+1:t} \in \mathbb{R}^{L \times d_a}
\]

운전 조건:

\[
C_{t-L+1:t} \in \mathbb{R}^{L \times d_c}
\]

정상 미래:

\[
X_{t+1:t+H}
\]

를 고려한다.

정상 dynamics model:

\[
p_\theta
\left(
X_{t+1:t+H}
\mid
X_{t-L+1:t}, A_{t-L+1:t}, C_{t-L+1:t}
\right)
\]

을 학습한다.

---

# 3. Research Questions

### RQ1 — Control/Context 정보의 가치

> 센서 시계열만 사용하는 모델보다 제어 입력과 운전조건을 함께 사용하는 모델이 정상 반응 예측 및 fault detection에 유의미하게 유리한가?

### RQ2 — 확률적 정상 반응 모델링

> 단일 미래값(point forecast)보다 정상 반응의 확률분포를 모델링하는 것이 오탐을 줄이고 calibration을 개선하는가?

### RQ3 — Residual Dynamics

> 단순 residual threshold보다 residual의 시간적·변수 간 변화 구조를 학습하는 것이 early fault detection을 개선하는가?

### RQ4 — Early Detection

> 제안 방식은 고장이 명백해진 시점보다 앞서 degradation onset 또는 fault injection 이후 더 빠르게 이상을 탐지할 수 있는가?

### RQ5 — Open-set

> 학습하지 않은 fault class를 기존 fault class로 강제 분류하지 않고 unknown으로 reject할 수 있는가?

### RQ6 — Generalization

> 동일한 방법론/architecture를 서로 다른 CPS 데이터셋에 독립적으로 학습했을 때 일관된 성능 향상이 발생하는가?

---

# PART II. Novelty 설계

# 4. 지금 당장 novelty라고 주장하면 안 되는 요소

다음은 각각 이미 연구가 존재한다.

- Transformer anomaly detection
- graph-based MTS anomaly detection
- residual-based FDI
- physics-informed learning
- open-set fault diagnosis
- action/state-conditioned anomaly detection
- probabilistic time-series forecasting

따라서:

```text
Transformer + GNN + Physics + Open-set
```

을 단순히 결합하는 것은 연구의 핵심 novelty로 삼지 않는다.

---

# 5. Novelty Gate

논문 구현 전에 아래 표를 실제 논문 30~50편으로 채운다.

| Paper | Control input | Context | Probabilistic dynamics | Residual | Residual evolution | Early fault | Open-set | Attribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| GDN | X | X | X | O/간접 | X | X | X | O |
| TranAD | X | X | X | Reconstruction | X | X | X | O/제한 |
| CATCH | X | X | X | X | X | X | X | 제한 |
| CAROTS | X | X | X | X | 관계 학습 | X | X | 제한 |
| Action-State AD (2026) | O | O | X | X | 상태 이력 | 제한 | X | 제한 |
| **CCRDL 후보** | O | O | O | O | **O** | **O** | 확장 | 확장 |

### Novelty 확정 조건

다음 중 최소 하나가 명확해야 한다.

1. 새로운 representation
2. 새로운 learning objective
3. 기존 formulation이 해결하지 못하는 문제에 대한 새로운 formalization
4. control/action과 residual evolution을 결합하는 새로운 방식
5. uncertainty와 degradation evolution을 연결하는 새로운 score/learning rule

---

# 6. 제안 모델 v0 — CCRDL

## 6.1 전체 구조

```text
X history ─────────┐
                   │
A history ─────────┼──► State/Control Encoder ─► latent z_t
                   │
Context ───────────┘
                                    │
                                    ▼
                       Probabilistic Dynamics
                                    │
                             μ(t+1:t+H)
                             σ(t+1:t+H)
                                    │
                 ┌──────────────────┴──────────────────┐
                 │                                     │
              Expected                              Actual
                 │                                     │
                 └──────────────────┬──────────────────┘
                                    ▼
                   uncertainty-normalized residual
                                    │
                                    ▼
                       Residual Evolution Encoder
                                    │
                   ┌────────────────┼────────────────┐
                   ▼                ▼                ▼
             anomaly score     early warning    attribution
                                    │
                              optional open-set
```

---

## 6.2 Stage A — State/Control Encoder

\[
z_t =
E_\theta
(
X_{t-L+1:t},
A_{t-L+1:t},
C_{t-L+1:t}
)
\]

후보 backbone:

- TCN
- GRU/LSTM
- Transformer Encoder
- State Space Model 계열

**처음부터 가장 복잡한 모델을 선택하지 않는다.**

1차 baseline은 TCN/GRU로 구현하고,  
2차에서 Transformer/SSM을 비교한다.

---

## 6.3 Stage B — Probabilistic Dynamics

모델이 미래의 평균과 불확실성을 예측한다.

\[
(\mu_{t+h}, \log \sigma_{t+h})
=
D_\theta(z_t, A_t, C_t)
\]

Gaussian 가정 초기 버전:

\[
p(X_{t+h}) =
\mathcal{N}
(
\mu_{t+h}, \sigma_{t+h}^{2}
)
\]

Negative Log-Likelihood:

\[
\mathcal{L}_{NLL}
=
\sum_{t,j}
\left[
\frac{(x_{t,j}-\mu_{t,j})^2}
{2\sigma_{t,j}^{2}}
+
\log\sigma_{t,j}
\right]
\]

후속 후보:

- Gaussian
- Student-t
- Gaussian mixture
- Quantile forecasting

**이 비교 자체도 ablation이 된다.**

---

## 6.4 Stage C — Uncertainty-aware residual

단순 residual:

\[
e_{t,j}=x_{t,j}-\mu_{t,j}
\]

표준화 residual:

\[
r_{t,j}
=
\frac{x_{t,j}-\mu_{t,j}}
{\sigma_{t,j}+\epsilon}
\]

의미:

> 단순히 예측과 얼마나 다른가가 아니라, **정상적으로 허용되는 불확실성 대비 얼마나 이상한가**를 측정한다.

---

## 6.5 Stage D — Residual Evolution Encoder

최근 K step residual:

\[
R_{t-K+1:t}
=
[r_{t-K+1}, \dots, r_t]
\]

를 별도 encoder:

\[
h_t = G_\phi(R_{t-K+1:t})
\]

에 입력한다.

후보:

1. TCN residual encoder
2. Transformer residual encoder
3. Graph-Temporal residual encoder

### Graph를 쓴다면 이유가 있어야 한다.

센서 변수 간 관계가 중요한 경우:

\[
G=(V,E)
\]

- node = sensor/variable
- edge = 물리 prior 또는 학습된 dependency

하지만 **GNN은 성능을 올리기 위해 무조건 넣지 않는다.**
TCN/Transformer residual encoder보다 명확한 이득이 있을 때만 최종 모델에 포함한다.

---

## 6.6 Stage E — Anomaly Score

초기 후보:

\[
S_t =
\alpha S_{NLL,t}
+
\beta S_{evolution,t}
\]

여기서:

- \(S_{NLL,t}\): 정상 미래 분포에서 벗어난 정도
- \(S_{evolution,t}\): 최근 residual trajectory가 정상 residual dynamics에서 벗어난 정도

\(\alpha,\beta\)는 validation에서 결정한다.

---

# 7. Physics/Control Constraint는 보조 항으로 시작한다

Physics loss를 처음부터 거대하게 만들지 않는다.

예:

\[
\mathcal{L}_{total}
=
\mathcal{L}_{NLL}
+
\lambda_{evo}\mathcal{L}_{evolution}
+
\lambda_{phys}\mathcal{L}_{physics}
\]

### 물리 constraint를 넣는 조건

- dataset에서 물리 관계가 명확할 것
- 검증 가능한 관계일 것
- 데이터에서 이미 계산되는 target을 그대로 leak하지 않을 것

예시:

- 무선전력 응용: \(P \approx VI\)
- 명령-응답 monotonicity
- actuator command와 response delay의 허용 구조

**TEP나 N-CMAPSS에 무선충전 물리식을 억지로 적용하지 않는다.**

---

# PART III. Dataset 설계

# 8. Dataset 전체 전략

## 핵심 원칙

하나의 데이터셋으로 모든 가설을 증명하지 않는다.

| Dataset | 주요 역할 | Action 명확성 | Early degradation | Fault class | 실제/Sim |
|---|---|---:|---:|---:|---|
| Extended TEP | Control-response + FDD | 높음(XMV) | 중간 | 높음 | Simulation |
| GE-UTK Servomotor | Command-response + degradation | **매우 높음** | **높음** | degradation label | Simulation |
| N-CMAPSS | Degradation + Open-set | 중/낮음 | **매우 높음** | 여러 failure mode | Simulation(real flight profile) |
| HAI | 다른 CPS external validation | tag별 상이 | 낮음 | attack/anomaly | HIL + physical |
| SWaT | CPS external validation | actuator 존재 | 낮음 | attack/anomaly | physical testbed |
| WiPowerOne | 최종 적용 | 매우 높음(명령로그 확보 시) | 향후 | 회사 fault | real |

---

# 9. Dataset A — Extended Tennessee Eastman Process

## 9.1 공식 출처

**Dataset landing page (DTU / Figshare)**  
https://data.dtu.dk/articles/dataset/Tennessee_Eastman_Reference_Data_for_Fault-Detection_and_Decision_Support_Systems/13385936/1

**DOI**  
https://doi.org/10.11583/DTU.13385936

**논문**  
https://doi.org/10.1016/j.compchemeng.2021.107281

### 중요한 규모

공식 설명 기준:

- 28 process faults
- 6 operating modes
- 각 fault 조건 반복 simulation
- setpoint change / mode transition 포함
- 전체 다운로드 약 **132.96 GB**

**따라서 처음부터 전체 133GB를 받지 않는다.**

---

## 9.2 pyTEP

**GitHub**  
https://github.com/ccreinartz11/pytep

**PyPI**  
https://pypi.org/project/pytep/

**논문 DOI**  
https://doi.org/10.1016/j.softx.2022.101053

### 주의

pyTEP 공개 버전은 다음 의존성을 갖는다.

- Python 3.7 계열
- MATLAB/Simulink
- MATLAB Engine for Python

따라서 **초기 논문 재현은 공개 dataset으로 먼저 하고, intervention experiment가 필요해지는 단계에서 pyTEP 환경을 별도 구성**한다.

---

## 9.3 TEP 컬럼 의미 매핑

Canonical TEP 기준:

### XMV — Control / Manipulated Variables

| Column | 의미 | 연구 Role |
|---|---|---|
| XMV1 | D feed flow valve | ACTION |
| XMV2 | E feed flow valve | ACTION |
| XMV3 | A feed flow valve | ACTION |
| XMV4 | A+C feed flow valve | ACTION |
| XMV5 | compressor recycle valve | ACTION |
| XMV6 | purge valve | ACTION |
| XMV7 | separator pot liquid flow valve | ACTION |
| XMV8 | stripper liquid product flow valve | ACTION |
| XMV9 | stripper steam valve | ACTION |
| XMV10 | reactor cooling water flow | ACTION |
| XMV11 | condenser cooling water flow | ACTION |
| XMV12 | agitator speed | ACTION |

### XMEAS — Process State

주요 컬럼:

| Column | 의미 | Role |
|---|---|---|
| XMEAS1 | A feed | STATE |
| XMEAS2 | D feed | STATE |
| XMEAS3 | E feed | STATE |
| XMEAS4 | A+C feed | STATE |
| XMEAS5 | recycle flow | STATE |
| XMEAS6 | reactor feed rate | STATE |
| XMEAS7 | reactor pressure | STATE |
| XMEAS8 | reactor level | STATE |
| XMEAS9 | reactor temperature | STATE |
| XMEAS10 | purge rate | STATE |
| XMEAS11 | separator temperature | STATE |
| XMEAS12 | separator level | STATE |
| XMEAS13 | separator pressure | STATE |
| XMEAS14 | separator underflow | STATE |
| XMEAS15 | stripper level | STATE |
| XMEAS16 | stripper pressure | STATE |
| XMEAS17 | stripper underflow | STATE |
| XMEAS18 | stripper temperature | STATE |
| XMEAS19 | stripper steam flow | STATE |
| XMEAS20 | compressor work | STATE |
| XMEAS21 | reactor cooling-water outlet temperature | STATE |
| XMEAS22 | condenser cooling-water outlet temperature | STATE |
| XMEAS23~41 | 주요 stream component composition | STATE |

**Extended TEP에 추가 필드가 존재할 수 있으므로 실제 파일의 README를 source of truth로 삼고 `variable_catalog`에 자동 등록한다.**

---

## 9.4 TEP에서 Action을 사용할 때 중요한 주의점

TEP는 closed-loop control system이다.

즉 XMV는 단순한 외생 명령이 아니라:

```text
Sensor 변화 → Controller → XMV 변화
```

일 수 있다.

따라서 같은 timestamp의 XMEAS와 XMV를 섞어 target을 예측하면 **endogeneity / leakage** 위험이 있다.

### 규칙

예측 입력:

\[
X_{t-L+1:t}, A_{t-L+1:t}
\]

target:

\[
X_{t+1:t+H}
\]

만 사용한다.

**미래 XMV는 사용하지 않는다.**

더 강한 causal/action claim은 setpoint intervention 또는 pyTEP에서 직접 변경한 control scenario에서 검증한다.

---

# 10. Dataset B — GE Research + University of Tennessee Servomotor Degradation

이 데이터는 본 연구와 매우 잘 맞는 보조/핵심 benchmark 후보이다.

## 10.1 공식 출처

PHM Society repository page:  
https://data.phmsociety.org/servomotor_dataset/

Direct download (약 21.3 GB):  
https://phm-datasets.s3.amazonaws.com/GE-UTK/FMCRD_Data.zip

제공기관:

- GE Research
- University of Tennessee Knoxville
- ARPA-E/DOE 지원 연구

---

## 10.2 핵심 컬럼

| Column | 의미 | Role |
|---|---|---|
| time | timestamp | TIME |
| rod_demand_pos | 요구 위치 | **ACTION / COMMAND** |
| rod_actual_pos | 실제 위치 | STATE |
| torque | motor torque | STATE |
| rotor_speed | rotor speed | STATE |
| i_3p_a | phase A current | STATE |
| i_3p_b | phase B current | STATE |
| i_3p_c | phase C current | STATE |
| direct | DQZ direct current component | STATE |
| quadrature | DQZ quadrature component | STATE |
| run_index | run identifier | GROUP |
| transitions | transition index | CONTEXT |
| del_pos | demanded displacement | ACTION_DERIVED |
| DV | continuous degradation value | **EVAL_ONLY / LABEL** |
| ylabel | LN/LO/MED/HI degradation class | **EVAL_ONLY / LABEL** |

### 이 데이터가 중요한 이유

명령과 결과가 매우 명확하다.

```text
rod_demand_pos
      ↓
Motor system
      ↓
rod_actual_pos + torque + speed + current
```

따라서 **“command-conditioned normal response”를 검증하기에 TEP보다 해석이 쉬운 benchmark**가 될 수 있다.

---

# 11. Dataset C — N-CMAPSS

## 11.1 공식 출처

NASA/PHM Society repository mirror:  
https://data.phmsociety.org/nasa/

Direct download — Turbofan Engine Degradation Simulation Data Set 2:  
https://phm-datasets.s3.amazonaws.com/NASA/17.+Turbofan+Engine+Degradation+Simulation+Data+Set+2.zip

2021 PHM Challenge:  
https://data.phmsociety.org/2021-phm-conference-data-challenge/

Dataset paper:  
https://doi.org/10.3390/data6010005

NASA NTRS:  
https://ntrs.nasa.gov/citations/20205001125

---

## 11.2 연구 역할

N-CMAPSS의 주된 역할은 **Action-conditioned claim이 아니다.**

주요 역할:

1. gradual degradation
2. fault onset → failure progression
3. early detection
4. failure-mode generalization
5. open-set protocol

---

## 11.3 N-CMAPSS 변수 그룹

### Scenario descriptors W

| Variable | 의미 | Role |
|---|---|---|
| alt | altitude | CONTEXT |
| Mach | flight Mach number | CONTEXT |
| TRA | throttle-resolver angle | CONTROL-LIKE CONTEXT |
| T2 | fan inlet temperature | CONTEXT |

### Measured sensors \(X_s\)

대표 변수:

| Variable | 의미 | Role |
|---|---|---|
| Wf | fuel flow | STATE |
| Nf | physical fan speed | STATE |
| Nc | physical core speed | STATE |
| T24 | LPC outlet temperature | STATE |
| T30 | HPC outlet temperature | STATE |
| T48 | HPT outlet temperature | STATE |
| T50 | LPT outlet temperature | STATE |
| P15 | bypass duct pressure | STATE |
| P2 | fan inlet pressure | STATE |
| P21 | fan outlet pressure | STATE |
| P24 | LPC outlet pressure | STATE |
| Ps30 | HPC outlet static pressure | STATE |
| P40 | burner outlet pressure | STATE |
| P50 | LPT outlet pressure | STATE |

Dataset version에 따라 추가 measured/virtual signals가 존재한다.

### Health parameters

component degradation를 직접 반영하는 health parameter는:

```text
MODEL INPUT ❌
EVALUATION ONLY ✅
```

로 둔다.

이유:

> 우리가 찾아야 하는 degradation 정보를 input으로 주면 target leakage가 발생하기 때문이다.

---

# 12. Dataset D — C-MAPSS (초기 개발용 경량 benchmark)

N-CMAPSS 다운로드/처리가 무거울 때 파이프라인 검증용으로 먼저 사용한다.

NASA dataset landing:  
https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data

Direct download mirror:  
https://phm-datasets.s3.amazonaws.com/NASA/6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip

NASA 설명 기준:

- FD001: train 100 / test 100
- FD002: train 260 / test 259
- FD003: train 100 / test 100
- FD004: train 248 / test 249
- 3 operational settings
- sensor measurements
- run-to-failure degradation

**오늘 프로젝트 구조를 테스트하기에는 C-MAPSS가 가장 빠르다.**

---

# 13. Dataset E — HAI

## 13.1 공식 출처

Repository:  
https://github.com/icsdataset/hai

Clone:

```bash
git clone https://github.com/icsdataset/hai
cd hai
git lfs pull
```

HAI 22.04 이후 실제 대용량 파일은 Git LFS를 사용한다.

---

## 13.2 역할

HAI는:

- boiler
- turbine
- water treatment
- HIL simulator

가 결합된 현실적인 ICS/CPS testbed다.

본 연구에서:

```text
Core degradation benchmark ❌
External CPS anomaly validation ✅
```

으로 사용한다.

### 기본 Role

- `time` → TIME
- process sensor tags → STATE
- actuator/controller tags → ACTION 후보
- attack → LABEL
- attack target metadata → attribution 평가 후보

HAI 23.05는 graph 정보도 제공하므로 Graph residual 모델을 시험할 경우 유용하다.

---

# 14. Dataset F — SWaT (선택)

공식 iTrust dataset page:  
https://www.sutd.edu.sg/itrust/itrust-labs/datasets/

SWaT은 신청 후 무료 제공되며 직접 즉시 다운로드 링크 방식이 아닐 수 있다.

역할:

- sensor-actuator CPS 외부 검증
- cyber-physical anomaly generalization

HAI가 충분히 동작하면 SWaT은 **필수 데이터셋이 아니라 추가 external benchmark**로 둔다.

---

# PART IV. 데이터 전처리 설계

# 15. 전처리의 핵심 철학

전처리의 목적은 “값을 0~1로 만드는 것”이 아니다.

각 컬럼을 다음 의미로 구분하는 것이 먼저다.

```text
STATE
ACTION
CONTEXT
LABEL
EVAL_ONLY
GROUP_ID
TIME
```

---

# 16. 공통 preprocessing pipeline

```text
RAW FILE
   ↓
① Schema validation
   ↓
② Semantic role mapping
   ↓
③ run/unit 단위 split
   ↓
④ timestamp / sample order 확인
   ↓
⑤ missing / invalid 처리
   ↓
⑥ train-normal 기준 scaler fit
   ↓
⑦ derived feature
   ↓
⑧ sliding window
   ↓
⑨ Parquet/NumPy export
   ↓
MODEL
```

---

# 17. Split은 정규화보다 먼저

잘못된 순서:

```text
전체 데이터 normalization
→ train/test split
```

올바른 순서:

```text
run/unit 기준 train/val/test split
        ↓
train normal data로 scaler fit
        ↓
validation/test transform
```

---

# 18. Scaling

## 18.1 Robust Scaling 후보

\[
z_{t,j}
=
\frac{
x_{t,j} - \operatorname{median}_{train}(x_j)
}{
IQR_{train}(x_j) + \epsilon
}
\]

\[
IQR = Q_{75} - Q_{25}
\]

장점:

- 큰 outlier 영향을 StandardScaler보다 덜 받는다.

---

## 18.2 Standard Scaling baseline

\[
z_{t,j}
=
\frac{x_{t,j}-\mu_{train,j}}
{\sigma_{train,j}+\epsilon}
\]

**Robust vs Standard는 preprocessing ablation으로 비교한다.**

---

# 19. Action feature

Action은 현재 절대값만 사용하지 않는다.

\[
\Delta A_t=A_t-A_{t-1}
\]

추가 후보:

\[
\Delta^2 A_t
=
\Delta A_t-\Delta A_{t-1}
\]

입력 후보:

```text
A_t
ΔA_t
time_since_action_change
action_change_flag
```

---

# 20. State feature

처음에는 raw normalized state만 사용한다.

후속 ablation:

```text
x_t
Δx_t
rolling mean
rolling std
rate-of-change
```

**처음부터 handcrafted feature를 과도하게 넣지 않는다.**
딥러닝 representation 효과와 feature engineering 효과가 섞이기 때문이다.

---

# 21. Missing / Sensor Quality

### Short gap

- bounded interpolation
- forward fill 후보

### Long gap

- 임의 보간하지 않음
- missing mask 생성

\[
m_{t,j} =
\begin{cases}
1 & observed \\
0 & missing
\end{cases}
\]

모델 입력에 mask를 추가할 수 있다.

### Sensor freeze

연속 동일값이 일정 시간 이상 지속되는 경우:

```text
sensor_freeze_flag
```

를 별도 quality feature로 저장할 수 있다.

---

# 22. Windowing

입력 길이:

\[
L \in \{32,64,128,256\}
\]

예측 horizon:

\[
H \in \{1,4,8,16\}
\]

를 후보로 둔다.

최종 값은 dataset sampling 특성에 맞춰 결정한다.

### Leakage 방지

동일 run의 window를 random shuffle해서 train/test에 나누지 않는다.

```text
Run 001 전체 → TRAIN
Run 002 전체 → TRAIN
Run 100 전체 → TEST
```

처럼 **group-level split**한다.

---

# PART V. RDBMS 및 데이터 관리 설계

# 23. 가장 중요한 설계 수정

**Extended TEP 전체 133GB를 PostgreSQL에 한 센서값씩 long-format으로 적재하지 않는다.**

그 방식은:

- row 수 폭증
- ingest 비용 증가
- 학습 export 느림
- DB 용량 증가

문제가 크다.

따라서 연구 시스템은:

```text
┌─────────────────────────────┐
│ PostgreSQL                  │
│                             │
│ Metadata / Semantic catalog │
│ Split / preprocessing       │
│ Experiment / metrics        │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│ Filesystem                  │
│                             │
│ Raw: original ZIP/HDF5/CSV  │
│ Interim: Parquet            │
│ Processed: Parquet/NPY      │
│ Model: checkpoints          │
└─────────────────────────────┘
```

으로 간다.

---

# 24. PostgreSQL이 관리하는 것

## 24.1 dataset

```sql
dataset (
    dataset_id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT,
    provider TEXT,
    source_url TEXT,
    doi TEXT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
)
```

---

## 24.2 file_asset

```sql
file_asset (
    file_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT REFERENCES dataset(dataset_id),
    logical_name TEXT,
    local_path TEXT NOT NULL,
    file_format TEXT,
    size_bytes BIGINT,
    sha256 TEXT,
    source_url TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
)
```

목적:

> “어떤 파일을 가지고 실험했는가?”를 재현한다.

---

## 24.3 variable_catalog

```sql
variable_catalog (
    variable_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT REFERENCES dataset(dataset_id),
    source_name TEXT NOT NULL,
    canonical_name TEXT,
    semantic_role TEXT NOT NULL,
    physical_type TEXT,
    unit TEXT,
    is_model_input BOOLEAN DEFAULT TRUE,
    is_eval_only BOOLEAN DEFAULT FALSE,
    description TEXT
)
```

semantic_role enum 후보:

```text
TIME
STATE
ACTION
CONTEXT
LABEL
EVAL_ONLY
GROUP_ID
```

---

## 24.4 dataset_run

```sql
dataset_run (
    run_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT REFERENCES dataset(dataset_id),
    external_run_id TEXT,
    asset_id TEXT,
    operating_mode TEXT,
    fault_type TEXT,
    split TEXT,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    metadata JSONB
)
```

---

## 24.5 split_manifest

```sql
split_manifest (
    split_manifest_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT REFERENCES dataset(dataset_id),
    name TEXT NOT NULL,
    strategy TEXT NOT NULL,
    seed INTEGER,
    manifest_path TEXT,
    notes TEXT
)
```

---

## 24.6 preprocess_profile

```sql
preprocess_profile (
    profile_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT REFERENCES dataset(dataset_id),
    name TEXT,
    scaler_type TEXT,
    fit_split TEXT,
    config JSONB,
    code_commit TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
)
```

---

## 24.7 preprocess_parameter

```sql
preprocess_parameter (
    profile_id BIGINT REFERENCES preprocess_profile(profile_id),
    variable_id BIGINT REFERENCES variable_catalog(variable_id),
    mean DOUBLE PRECISION,
    std DOUBLE PRECISION,
    median DOUBLE PRECISION,
    q25 DOUBLE PRECISION,
    q75 DOUBLE PRECISION,
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    PRIMARY KEY (profile_id, variable_id)
)
```

---

## 24.8 feature_set

```sql
feature_set (
    feature_set_id BIGSERIAL PRIMARY KEY,
    dataset_id BIGINT REFERENCES dataset(dataset_id),
    preprocess_profile_id BIGINT REFERENCES preprocess_profile(profile_id),
    split_manifest_id BIGINT REFERENCES split_manifest(split_manifest_id),
    window_length INTEGER,
    horizon INTEGER,
    stride INTEGER,
    output_path TEXT,
    sha256 TEXT,
    config JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
)
```

---

## 24.9 experiment

```sql
experiment (
    experiment_id BIGSERIAL PRIMARY KEY,
    name TEXT,
    model_name TEXT,
    dataset_id BIGINT REFERENCES dataset(dataset_id),
    feature_set_id BIGINT REFERENCES feature_set(feature_set_id),
    git_commit TEXT,
    seed INTEGER,
    config JSONB,
    checkpoint_path TEXT,
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
)
```

---

## 24.10 metric

```sql
metric (
    metric_id BIGSERIAL PRIMARY KEY,
    experiment_id BIGINT REFERENCES experiment(experiment_id),
    metric_name TEXT,
    metric_value DOUBLE PRECISION,
    scope TEXT,
    metadata JSONB
)
```

---

# 25. 실제 대용량 telemetry는 어디에 두는가?

## 연구 Benchmark

```text
Raw ZIP/HDF5/CSV
      ↓
Parquet
      ↓
training tensor
```

### 추천

- Raw: 원본 그대로
- Interim: Parquet
- Processed: Parquet 또는 `.npy/.npz`
- DB: 메타데이터/실험 추적

---

## 회사 실시간 시스템

실시간 telemetry가 쌓이기 시작하면:

```text
PostgreSQL
   +
TimescaleDB hypertable
```

를 고려한다.

예:

```text
telemetry(
    ts,
    device_id,
    session_id,
    voltage,
    current,
    power,
    temperature,
    ...
)
```

연구 시작 단계에서는 TimescaleDB가 필수는 아니다.

---

# 26. 관리 Stack

### Phase 1 — 연구

- PostgreSQL
- pgAdmin
- SQLAlchemy
- Alembic
- Docker Compose

공식 문서:

PostgreSQL:  
https://www.postgresql.org/docs/current/

SQLAlchemy:  
https://docs.sqlalchemy.org/

Alembic:  
https://alembic.sqlalchemy.org/

### Phase 2 — 실시간 회사 적용

TimescaleDB / Timescale documentation:  
https://docs.timescale.com/

---

# PART VI. Baseline 설계

# 27. Baseline을 계층별로 비교

## B0. Rule

- fixed threshold
- residual threshold
- change-rate threshold

---

## B1. Statistical

- PCA
- DPCA
- Hotelling \(T^2\)
- SPE/Q statistic

---

## B2. Classical ML

- Isolation Forest
- One-Class SVM

---

## B3. Deep Reconstruction

- LSTM Autoencoder
- USAD
- OmniAnomaly

---

## B4. Forecasting

- GRU forecast
- TCN forecast
- Transformer forecast

---

## B5. MTSAD

### GDN

Paper:  
https://arxiv.org/abs/2106.06947

핵심:
- sensor relationship graph
- expected behavior prediction
- anomaly attribution

### TranAD

Paper:  
https://arxiv.org/abs/2201.07284

핵심:
- Transformer
- self-conditioning
- reconstruction-based anomaly detection

### Anomaly Transformer

ICLR 계열 대표 Transformer anomaly baseline으로 재현 후보.

### DCdetector

contrastive MTS anomaly baseline 후보.

### CATCH — ICLR 2025

OpenReview:  
https://openreview.net/forum?id=m08aK3xxdJ

핵심:
- channel-aware
- frequency patching
- channel relationship

### CAROTS — ICML 2025

OpenReview:  
https://openreview.net/forum?id=EGpueKe6TP

핵심:
- causality-aware augmentation
- contrastive learning

---

# 28. 반드시 필요한 가장 중요한 비교

### Baseline F0 — Sensor-only forecast

\[
\hat X=f(X)
\]

### Baseline F1 — Sensor + Context

\[
\hat X=f(X,C)
\]

### Baseline F2 — Sensor + Action + Context

\[
\hat X=f(X,A,C)
\]

### Baseline F3 — Probabilistic Dynamics

\[
p(X_{future}|X,A,C)
\]

### Proposed

```text
Probabilistic Dynamics
          +
Uncertainty-aware residual
          +
Residual Evolution Encoder
```

이 계단식 비교가 **논문의 핵심 주장**을 가장 잘 검증한다.

---

# PART VII. Ablation Study

# 29. Ablation Matrix

| ID | Action | Context | Prob. | Residual Evolution | Physics | Open-set |
|---|---:|---:|---:|---:|---:|---:|
| A0 | X | X | X | X | X | X |
| A1 | X | O | X | X | X | X |
| A2 | O | O | X | X | X | X |
| A3 | O | O | O | X | X | X |
| A4 | O | O | O | O | X | X |
| A5 | O | O | O | O | O | X |
| FULL | O | O | O | O | O/선택 | O/확장 |

---

# 30. Backbone Ablation

동일한 CCRDL 구조에:

- GRU
- TCN
- Transformer
- SSM 계열

을 교체한다.

목표:

> 성능 향상이 backbone 자체 때문인지 CCRDL formulation 때문인지 분리한다.

---

# PART VIII. 실험 프로토콜

# 31. Experiment E0 — 데이터 sanity check

목적:

- 데이터 parsing이 맞는가
- label이 맞는가
- 시간순서가 맞는가
- train/test leakage가 없는가

산출물:

```text
dataset_summary.csv
variable_catalog.csv
split_manifest.json
data_quality_report.md
```

---

# 32. Experiment E1 — Normal Dynamics Prediction

### Train

normal run만 사용.

### 평가

- MAE
- RMSE
- NLL
- predictive interval coverage
- CRPS 후보

질문:

> Action/context를 넣으면 정상 미래 예측이 실제로 좋아지는가?

---

# 33. Experiment E2 — Fault Detection

정상 학습 후 fault run 평가.

지표:

- AUROC
- **AUPRC**
- Precision
- Recall
- F1
- false alarm rate
- event-based metric

**Point-adjusted F1만 단독으로 사용하지 않는다.**

---

# 34. Experiment E3 — Early Detection

Fault injection/onset:

\[
t_f
\]

최초 지속 탐지:

\[
t_d
\]

Detection delay:

\[
D=t_d-t_f
\]

점진적 degradation에서는 degradation onset \(t_o\)가 존재하면:

\[
LeadScore =
\frac{t_f-t_d}
{t_f-t_o+\epsilon}
\]

같은 normalized early-warning score를 보조적으로 사용할 수 있다.

단, 이 식은 **본 연구용 제안 metric 후보**이며 최종 사용 전 타당성을 별도로 검토한다.

---

# 35. Experiment E4 — Open-set Fault

Diagnostic head를 별도로 두는 경우:

Known training faults:

```text
A B C D E
```

Unknown test:

```text
F
```

다음 반복:

```text
Leave Fault A Out
Leave Fault B Out
...
```

지표:

- unknown AUROC
- unknown recall
- FPR95
- OSCR 후보
- known-class macro F1
- known/unknown calibration

**데이터셋이 제공하는 fault class 구조가 충분한 경우에만 수행한다.**

---

# 36. Experiment E5 — Attribution

TEP:

- fault injection type/target
- process subsystem

N-CMAPSS:

- health parameter / failure node를 EVAL_ONLY로 사용

평가지표:

- Hit@1
- Hit@3
- MRR
- subsystem-level hit rate

정답이 센서 단위까지 확실하지 않으면:

> Root Cause Identification

대신:

> **Fault-related Variable Attribution / Subsystem Localization**

으로 주장 수준을 낮춘다.

---

# 37. Experiment E6 — Robustness

Test-only perturbation:

- Gaussian noise
- missing rate 1/5/10%
- sensor freeze
- timestamp jitter
- action noise

질문:

> 정상 데이터에서 좋은 것뿐 아니라 실제 센서 불완전성에서도 유지되는가?

---

# 38. Experiment E7 — Efficiency

측정:

- parameter count
- training time
- inference latency
- peak GPU memory
- throughput

실제 Physical AI 적용을 위해:

```text
좋은 F1
+
실시간 inference 가능
```

둘 다 평가한다.

---

# 39. 통계적 검증

각 주요 실험:

- 최소 5 random seeds
- mean ± std
- dataset/fault별 결과 개별 표시

비교:

- Wilcoxon signed-rank test 우선 후보
- multiple comparison 시 Holm correction 후보
- bootstrap 95% CI 보조

**단순 best score 하나만 보고 결론내리지 않는다.**

---

# PART IX. 예상 한계와 해결 전략

# 40. 한계 1 — Novelty collision

### 문제

이미 유사 연구가 있을 가능성.

### 해결

1. 최근 5년 literature matrix 30~50편
2. nearest 5 papers 직접 구현/재현
3. exact claim comparison
4. formulation이 겹치면 architecture를 먼저 만들지 말고 연구질문을 수정

### Pivot 후보

- intervention-consistent dynamics
- uncertainty-calibrated residual evolution
- counterfactual control-response
- residual causal propagation

---

# 41. 한계 2 — Dataset domain 차이

### 문제

TEP는 화학공정, N-CMAPSS는 항공엔진, 회사는 무선충전.

### 잘못된 주장

```text
TEP에서 학습한 weight가 무선충전에 그대로 작동한다.
```

### 우리가 할 주장

```text
동일한 methodology가
서로 다른 CPS에서 각각 재학습되었을 때
baseline 대비 일관된 개선을 보인다.
```

즉:

> **Parameter generalization이 아니라 Methodological generalization**

을 검증한다.

---

# 42. 한계 3 — Action 정의가 애매한 Dataset

N-CMAPSS의 TRA는 공식적으로 `W` scenario descriptor에 속한다.

따라서:

- TEP XMV → ACTION
- GE rod_demand_pos → ACTION
- N-CMAPSS TRA → CONTROL-LIKE CONTEXT

로 보수적으로 정의한다.

이렇게 해야 논문 claim이 무너지지 않는다.

---

# 43. 한계 4 — Root-cause annotation 부족

### 해결 우선순위

1. TEP fault target/subsystem
2. pyTEP controlled fault injection
3. N-CMAPSS health parameter를 eval-only
4. HAI attack target metadata
5. 정답이 약하면 root cause가 아니라 attribution/localization으로 표현

---

# 44. 한계 5 — 회사 데이터 부족/비공개

논문의 method validation:

```text
TEP + GE + N-CMAPSS + HAI
```

로 수행.

회사 데이터:

```text
final feasibility case
```

로 사용.

따라서 회사 데이터 공개 문제 때문에 학위논문 전체가 좌우되지 않도록 한다.

---

# 45. 한계 6 — Simulator 데이터에 과적합

대응:

- HAI 같은 HIL/physical testbed external validation
- 회사 데이터 case study
- noise/missing robustness
- dataset마다 independent retraining

---

# PART X. Physical AI / RAG 적용

# 46. 논문과 회사 시스템을 분리한다

## 논문

```text
Telemetry
  ↓
CCRDL
  ↓
Anomaly / Early warning / Attribution
```

## 회사

```text
Telemetry
  ↓
CCRDL
  ↓
Diagnosis result
  ↓
RAG
  ↓
Recovery candidate
  ↓
Safety rule
  ↓
Actual command
  ↓
Result verification
```

---

# 47. RAG Corpus

향후 회사 시스템:

- 제품 사양서
- 통신 사양서
- error code
- operation manual
- maintenance SOP
- 과거 fault event
- 과거 recovery result
- 펌웨어/버전 문서

RAG의 역할:

```text
"AI가 왜 이상이라고 했는가?"
+
"이 이상과 비슷한 과거 사례가 있는가?"
+
"허용되는 복구 sequence는 무엇인가?"
```

를 지원하는 것.

---

# 48. 자동 제어 안전 구조

AI가 직접 무제한 제어하지 않는다.

```text
AI 추천
  ↓
Recovery Policy
  ↓
Safety Rule
  ├─ 허용된 명령?
  ├─ 횟수 제한?
  ├─ 현재 상태에서 실행 가능?
  └─ 신뢰도 충분?
        ↓
    YES / NO
```

Low-risk 명령 예:

- reconnect
- session reinitialize
- software restart
- controlled reset

고위험 동작은 human approval을 유지한다.

---

# PART XI. 프로젝트 폴더 구조

# 49. 추천 구조

```text
physical-ai-thesis/
│
├─ README.md
├─ pyproject.toml
├─ .env.example
├─ .gitignore
├─ docker-compose.yml
│
├─ docs/
│  ├─ research_plan.md
│  ├─ literature_matrix.csv
│  ├─ dataset_dictionary.md
│  └─ experiment_protocol.md
│
├─ data/
│  ├─ raw/
│  │  ├─ tep/
│  │  ├─ ge_servomotor/
│  │  ├─ ncmapss/
│  │  ├─ cmapss/
│  │  └─ hai/
│  ├─ interim/
│  └─ processed/
│
├─ configs/
│  ├─ datasets/
│  ├─ models/
│  └─ experiments/
│
├─ src/
│  ├─ data/
│  │  ├─ ingest/
│  │  ├─ schemas/
│  │  ├─ split/
│  │  ├─ preprocessing/
│  │  └─ windowing/
│  │
│  ├─ db/
│  │  ├─ models/
│  │  └─ repositories/
│  │
│  ├─ models/
│  │  ├─ baselines/
│  │  ├─ dynamics/
│  │  ├─ residual/
│  │  └─ proposed/
│  │
│  ├─ training/
│  ├─ evaluation/
│  └─ visualization/
│
├─ sql/
├─ migrations/
├─ notebooks/
│  ├─ 00_dataset_sanity/
│  ├─ 01_baseline/
│  └─ 02_proposed/
│
├─ tests/
│
├─ artifacts/
│  ├─ checkpoints/
│  ├─ figures/
│  ├─ tables/
│  └─ logs/
│
└─ references/
```

---

# 50. Docker Compose 초기 DB 예시

```yaml
services:
  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: physical_ai
      POSTGRES_USER: physical_ai
      POSTGRES_PASSWORD: change_me
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  pgadmin:
    image: dpage/pgadmin4
    environment:
      PGADMIN_DEFAULT_EMAIL: admin@example.com
      PGADMIN_DEFAULT_PASSWORD: change_me
    ports:
      - "5050:80"
    depends_on:
      - postgres

volumes:
  pgdata:
```

> 버전은 실제 설치 시점에 다시 확인하고 고정한다. 연구 재현성을 위해 `latest` tag는 사용하지 않는다.

---

# PART XII. 구현 순서

# 51. Phase 0 — 오늘 해둘 일

**목표: “연구를 시작할 수 있는 프로젝트 뼈대”만 완성하고 종료**

### 1. 저장소 생성

```bash
mkdir physical-ai-thesis
cd physical-ai-thesis
git init
```

### 2. 위 폴더 구조 생성

### 3. 이 문서를 저장

```text
docs/RESEARCH_DESIGN_v1.md
```

### 4. C-MAPSS 먼저 다운로드

가장 작은 초기 sanity benchmark로 사용.

Direct:

https://phm-datasets.s3.amazonaws.com/NASA/6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip

### 5. PostgreSQL Docker 구성

- `docker-compose.yml`
- DB 실행
- pgAdmin 접속 확인

### 6. 첫 DB migration

최소:

```text
dataset
file_asset
variable_catalog
dataset_run
preprocess_profile
feature_set
experiment
metric
```

### 7. README에 연구 한 줄 작성

> Control-conditioned normal dynamics와 residual evolution을 이용해 산업 CPS의 초기 이상을 탐지하는 딥러닝 방법론 연구.

**여기까지 하면 오늘은 충분하다.**

---

# 52. Phase 1 — Data Infrastructure

산출물:

- C-MAPSS loader
- TEP loader
- GE loader
- N-CMAPSS loader
- HAI loader
- common semantic dictionary
- DB metadata ingest
- split manifests

완료 조건:

```bash
python -m src.data.validate --dataset cmapss
```

같은 명령 한 번으로:

- row count
- null
- variables
- run count
- label count
- split

이 출력되어야 한다.

---

# 53. Phase 2 — Baseline Reproduction

우선순위:

1. Rule/residual threshold
2. PCA
3. Isolation Forest
4. LSTM-AE
5. GRU forecast
6. TCN forecast
7. GDN
8. TranAD
9. CATCH
10. CAROTS

완료 조건:

> 최소 2개 benchmark에서 공개 논문의 경향을 대략 재현한다.

---

# 54. Phase 3 — 핵심 가설 검증

아직 새 모델을 복잡하게 만들지 않는다.

순서:

```text
Sensor-only
   ↓
+ Context
   ↓
+ Action
   ↓
Point Forecast
   ↓
Probabilistic Forecast
   ↓
Residual Threshold
   ↓
Residual Evolution
```

이 순서대로 실험.

### 여기서 성능이 안 오르면?

연구가 틀렸다는 중요한 결과다.

복잡한 모델을 억지로 붙이지 말고 문제 정의를 다시 본다.

---

# 55. Phase 4 — Proposed Method

E1~E3에서 가설이 확인된 뒤:

- latent dynamics
- residual encoder
- graph
- physics constraint
- open-set

순으로 필요한 것만 추가한다.

---

# 56. Phase 5 — Full Benchmark

최소:

- TEP
- GE Servomotor
- N-CMAPSS

추가:

- HAI

최종 가능:

- WiPowerOne case

---

# PART XIII. 논문 성공 기준

# 57. 최소 석사학위 성공 조건

다음이 충족되어야 한다.

1. 명확한 research gap
2. 제안 objective/representation 1개 이상
3. 신뢰 가능한 public benchmark 2개 이상
4. strong baseline 비교
5. ablation
6. statistical validation
7. 데이터 leakage 방지
8. reproducible preprocessing
9. code/config/version 관리
10. 실제 Physical AI 적용 가능성 제시

---

# 58. 해외 학술지 수준을 노리려면

추가적으로 필요:

- 3개 이상 heterogeneous datasets
- 최신 strong baseline
- robustness
- calibration/uncertainty
- computational efficiency
- 명확한 theoretical/formulation contribution
- strong ablation
- failure analysis
- open-source reproducibility 가능 범위 확보

---

# PART XIV. 실패 가능성까지 포함한 연구 의사결정

# 59. Go / Pivot 기준

## GO

다음 결과가 나오면 계속 간다.

- Action/Context 사용이 sensor-only보다 반복적으로 유리
- probabilistic model이 false alarm/calibration 개선
- residual evolution이 단순 residual threshold보다 early detection 개선

## PIVOT

다음이면 핵심 formulation 수정.

- Action을 넣어도 차이가 없음
- residual evolution이 simple NLL보다 개선 없음
- nearest paper와 novelty가 거의 동일
- dataset의 Action semantics가 부족

Pivot 후보:

1. intervention-aware world model
2. counterfactual fault detection
3. residual causal propagation
4. uncertainty-calibrated early warning
5. fault progression representation

---

# PART XV. 반드시 작성할 결과 Figure/Table

# 60. Figure

### Fig 1. 연구 문제

```text
Rule상 정상
하지만 response dynamics는 변함
```

### Fig 2. Proposed Architecture

```text
State + Action + Context
→ Probabilistic Dynamics
→ Residual
→ Residual Evolution
→ Early Fault
```

### Fig 3. Normal vs Fault residual trajectory

### Fig 4. Dataset role mapping

### Fig 5. Detection timeline

```text
degradation onset
      │
      ├──── proposed detection
      │
      ├──────── baseline detection
      │
      └──────────── failure
```

### Fig 6. Attribution heatmap

### Fig 7. Physical AI deployment architecture

---

# 61. Table

1. Related-work comparison
2. Dataset specification
3. Variable role mapping
4. Baseline configuration
5. Overall anomaly performance
6. Early detection delay
7. Open-set performance
8. Ablation
9. Robustness
10. Efficiency

---

# PART XVI. Dataset 다운로드 모음

## Extended TEP

Landing:  
https://data.dtu.dk/articles/dataset/Tennessee_Eastman_Reference_Data_for_Fault-Detection_and_Decision_Support_Systems/13385936/1

DOI:  
https://doi.org/10.11583/DTU.13385936

**주의: 전체 약 132.96 GB. 처음부터 Download all 금지.**

---

## pyTEP

GitHub:  
https://github.com/ccreinartz11/pytep

PyPI:  
https://pypi.org/project/pytep/

---

## GE-UTK Servomotor

Info:  
https://data.phmsociety.org/servomotor_dataset/

Direct:  
https://phm-datasets.s3.amazonaws.com/GE-UTK/FMCRD_Data.zip

**약 21.3 GB**

---

## N-CMAPSS

Repository:  
https://data.phmsociety.org/nasa/

Direct:  
https://phm-datasets.s3.amazonaws.com/NASA/17.+Turbofan+Engine+Degradation+Simulation+Data+Set+2.zip

Challenge:  
https://data.phmsociety.org/2021-phm-conference-data-challenge/

---

## C-MAPSS

NASA:  
https://data.nasa.gov/dataset/cmapss-jet-engine-simulated-data

Direct mirror:  
https://phm-datasets.s3.amazonaws.com/NASA/6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip

---

## HAI

https://github.com/icsdataset/hai

```bash
git clone https://github.com/icsdataset/hai
cd hai
git lfs pull
```

---

## SWaT

https://www.sutd.edu.sg/itrust/itrust-labs/datasets/

신청 방식.

---

# PART XVII. 핵심 참고문헌 및 반드시 읽을 자료

## Dataset / PHM

1. Reinartz, C. C., Kulahci, M., & Ravn, O. (2021).  
   **An extended Tennessee Eastman simulation dataset for fault-detection and decision support systems.**  
   Computers & Chemical Engineering, 149, 107281.  
   https://doi.org/10.1016/j.compchemeng.2021.107281

2. Reinartz, C., & Enevoldsen, T. T. (2022).  
   **pyTEP: A Python package for interactive simulations of the Tennessee Eastman process.**  
   SoftwareX, 18, 101053.  
   https://doi.org/10.1016/j.softx.2022.101053

3. Arias Chao, M., Kulkarni, C., Goebel, K., & Fink, O. (2021).  
   **Aircraft Engine Run-to-Failure Dataset under Real Flight Conditions for Prognostics and Diagnostics.**  
   Data, 6(1), 5.  
   https://doi.org/10.3390/data6010005

4. Saxena, A., Goebel, K., Simon, D., & Eklund, N. (2008).  
   **Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation.**

---

## MTS Anomaly Detection

5. Deng, A., & Hooi, B.  
   **Graph Neural Network-Based Anomaly Detection in Multivariate Time Series (GDN).**  
   https://arxiv.org/abs/2106.06947

6. Tuli, S., Casale, G., & Jennings, N. R.  
   **TranAD: Deep Transformer Networks for Anomaly Detection in Multivariate Time Series Data.**  
   https://arxiv.org/abs/2201.07284

7. Wu, X. et al.  
   **CATCH: Channel-Aware Multivariate Time Series Anomaly Detection via Frequency Patching.**  
   ICLR 2025.  
   https://openreview.net/forum?id=m08aK3xxdJ

8. Kim, H. et al.  
   **Causality-Aware Contrastive Learning for Robust Multivariate Time-Series Anomaly Detection (CAROTS).**  
   ICML 2025.  
   https://openreview.net/forum?id=EGpueKe6TP

---

## Physics / Hybrid PHM

9. Arias Chao, M. et al.  
   **Fusing Physics-based and Deep Learning Models for Prognostics.**  
   https://arxiv.org/abs/2003.00732

10. Arias Chao, M. et al.  
    **Hybrid deep fault detection and isolation: Combining deep neural networks and system performance models.**  
    https://arxiv.org/abs/1908.01529

---

## HAI / CPS

11. HAI dataset official repository.  
    https://github.com/icsdataset/hai

HAI repository에서는 eTaPR 계열 time-series-aware 평가 사용을 권장한다.

---

# PART XVIII. 최종 한 문장

> **본 연구는 산업 Cyber-Physical System에서 “현재 상태에서 특정 제어를 수행했을 때 정상적으로 나타나야 하는 반응의 확률적 동역학”을 학습하고, 실제 반응과 정상 반응 사이의 잔차가 시간과 변수 관계 속에서 어떻게 진화하는지를 새로운 딥러닝 표현으로 모델링하여 초기 이상을 탐지하는 방법론을 연구한다. 공개 산업 benchmark에서 방법론을 검증한 뒤, 이를 RAG 기반 기술문서 검색·복구 정책·Safety Rule과 연결하여 Physical AI 기반 무인 무선충전 자율진단·복구 시스템으로 확장한다.**

---

# PART XIX. 지금 바로 시작할 체크리스트

- [ ] Git repository 생성
- [ ] 위 폴더 구조 생성
- [ ] `docs/RESEARCH_DESIGN_v1.md` 저장
- [ ] C-MAPSS 다운로드
- [ ] PostgreSQL + pgAdmin Docker 실행
- [ ] metadata DB table 생성
- [ ] `variable_catalog` 구조 생성
- [ ] C-MAPSS loader skeleton 생성
- [ ] literature_matrix.csv 생성
- [ ] GDN / TranAD / CATCH / CAROTS 논문 PDF 또는 링크 정리
- [ ] Extended TEP 전체 다운로드는 보류
- [ ] GE Servomotor 저장공간 확인 후 다운로드 결정
- [ ] N-CMAPSS 저장공간 확인 후 다운로드
- [ ] 다음 작업: **C-MAPSS → DB metadata 등록 → 전처리 → GRU forecasting baseline**까지 end-to-end 1회 실행

---

## 이 문서에서 아직 확정하지 않은 것

아래는 실험 전 확정하면 안 된다.

- 최종 모델 이름
- Transformer / TCN / SSM 중 최종 backbone
- Graph 사용 여부
- Physics loss 사용 여부
- Open-set을 논문 핵심 contribution으로 둘지 여부
- 최종 anomaly score 수식
- 최종 window/horizon
- “SOTA” 주장
- “세계 최초” 주장

이것들은 **baseline과 pilot experiment 이후 증거를 보고 결정한다.**

---

**End of Research Design v1.0**
