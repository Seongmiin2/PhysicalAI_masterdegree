# CHUM 연구 기획서

## 신뢰 가능한 산업 시계열 이상 탐지를 위한 아키텍처 강건형 제어 이력 유용성 감사

**영문 제목:** *CHUM: Architecture-Robust Auditing of Control-History Utility for Reliable Industrial Time-Series Anomaly Detection*  
**지도교수 검토용 확정안 · 2026-08-23**  
**현재 단계:** 필수 실험 완료 · 논문 집필 착수 가능

---

## 0. 교수님께 먼저 보고할 결론

> **산업 이상 탐지에서 제어 이력은 모든 사건에 보편적으로 유용하지 않다. 그러나 TEP의 특정 fault–channel 조합에서는 모델 용량, 비현실적 masking, threshold, 오경보율, seed와 architecture를 통제한 뒤에도 추가 탐지 정보가 재현된다. 이 결과는 HAI 21.03의 전역 성능과 일부 직접 공격 channel에서도 제한적으로 반복된다.**

본 연구의 기여는 새로운 최고성능 detector가 아니다. **추가 context가 실제로 사용되는지**를 사건·채널별로 감사하는 CHUM(Control-History Utility Mapping) 프로토콜과, 그 결론이 여러 모델 구조와 교란 설정을 넘어 유지되는지를 보여 주는 실증이다.

논문 집필 전 필수 보강으로 정한 `TEP primary consensus sensitivity`도 완료했다. residual block length `5/10/20`, conditional draws `1/3/10`, TCN/Transformer, seed `42–46`을 교차한 390개 model-condition task에서 네 개 locked cell이 모두 동일한 robustness 기준을 통과했다. 390은 360개 perturbation과 세 fault에 공유되는 30개 original baseline의 합이다. 이 기준은 Git 이력상 결과보다 먼저 등록되었음을 입증할 수 없으므로 **post-hoc이지만 전 셀과 설정에 동일하게 적용한 규칙**으로 보고한다. 따라서 현재 남은 필수 실험은 없으며, 추가 seed나 세 번째 데이터셋은 일반성을 넓히는 후속 연구다.

---

## 1. 초록

산업 시계열 이상 탐지에서는 센서 상태뿐 아니라 제어 이력까지 입력하면 성능이 향상될 수 있다. 그러나 단순한 평균 성능 비교는 어떤 사건에서 어떤 제어 채널이 실제 정보를 제공했는지, 향상이 단순한 모델 용량 증가인지, 특정 architecture의 inductive bias인지, 또는 비현실적인 feature masking이 만든 분포 이동인지 구분하지 못한다. 본 연구는 이를 해결하기 위해 **Control-History Utility Mapping(CHUM)**을 제안한다. CHUM은 sensor-only 모델(F0), sensor+control 모델(F1), capacity-matched sensor-only 모델(F0-C)을 비교하고, 정상 학습 데이터만으로 구축한 leave-one-channel-out 조건부 대치, 조건별 validation threshold, pre-fault FPR guardrail, seed/run 계층 bootstrap, cross-architecture consensus를 결합해 event–channel별 추가 예측 정보의 유용성을 판정한다.

Tennessee Eastman Process(TEP)의 2,800 runs와 28 faults에서 GRU·TCN·compact Transformer를 비교한 결과, TCN과 Transformer가 동일한 7개 event-level GAIN faults를 식별했다. 더 엄격한 channel-level 판정에서는 `F4/XMV10`, `F19/XMV7`, `F19/XMV8`, `F25/XMV2`의 네 셀이 두 architecture에서 합의됐다. 기준 설정에서 ΔAUROC는 TCN `0.0555–0.2899`, Transformer `0.0531–0.2637`이었고 모든 셀에서 5/5 seed가 같은 방향이며 run-level bootstrap CI 하한이 0보다 컸다. 224개 quality-gated 후보 전체에 BH-FDR을 적용했을 때 네 locked cell은 q=0.05와 q=0.10에서 모두 생존했다. Integrated Gradients는 locked primary architecture–fault 셀 8개 중 7개에서 CHUM과 동일한 top channel을 선택했다. HAI 21.03 corrected v2에서는 F1이 F0보다 AUROC `+0.0187`, AUPRC `+0.0306`, eTaF1 `+0.0267` 높았고, 직접 공격된 5개 event–channel 셀에서 조건부 대치 후 score 감소가 3/3 seed에서 반복됐다. 마지막으로 3개 block length와 3개 draw count를 교차한 민감도 실험에서 네 locked cell 모두 두 architecture의 9/9 설정을 통과했다.

증거 강도는 같게 취급하지 않는다. TEP는 다중 architecture·run-level CI·BH-FDR·민감도 격자를 통과한 **확립된 주 근거**이고, HAI는 3 seeds와 직접 공격 channel에 제한된 **제한적 외부 지지**다.

이 결과는 제어 이력의 유용성이 사건과 채널에 따라 이질적이며, 일부 조합에서는 모델 구조와 대치 hyperparameter에 강건한 추가 정보를 제공한다는 점을 지지한다. 단, CHUM은 조건부 예측 정보의 감사 방법이며 물리적 인과, controller causality 또는 root-cause identification을 주장하지 않는다.

---

## 2. 추현승 교수·연구실 최근 연구 경향과 본 연구의 적합성

### 2.1 조사 범위

공식 Superintelligence Laboratory publication 목록의 2024–2026년 자료를 전수 수집했다. Journal/Conference 목록에는 동일 논문이 중복 등록된 경우가 있어 **82개 등록, 제목 기준 65편**으로 구분했다. 제목 기반 재현 가능한 규칙 코딩 결과, 1차 주제는 6G·네트워크 AI 24편, 의료 AI 21편, 신뢰 AI·RAG·에이전트 6편, 기타 응용 AI 13편, 산업·시계열 이상 진단 1편이었다. 이 수치는 연구 품질이나 인용 영향력이 아니라 연구축의 반복 빈도를 보는 용도다. 원자료는 `deliverables/professor_research/`에 보존했다.

### 2.2 최근 연구에서 반복되는 네 가지 선호

| 반복 경향 | 최근 연구의 구체적 형태 | CHUM과의 직접 접점 |
| --- | --- | --- |
| 시계열 문맥을 운용 결정에 연결 | mobile traffic·mobility 예측을 MEC resource allocation, handover timing, traffic engineering에 사용 | 제어 이력이 탐지 판단에 주는 추가 정보를 사건·채널별로 분리 |
| 신뢰성과 조건 변화에 대한 검증 | architecture benchmark, domain robustness, inference confidence, evidence reliability | TCN/Transformer consensus, 조건부 대치 품질, FPR guardrail, sensitivity grid |
| 다중 모델·다중 데이터 환경 비교 | 의료 AI에서 여러 backbone·dataset·cross-dataset 평가 | GRU/TCN/Transformer, TEP/HAI, F0/F1/F0-C 통제 비교 |
| AI-native system과 실용성 | NWDAF, emulated B5G testbed, edge resource control, 의료기기 제품화 | 향후 network telemetry context audit 및 운영 의사결정 모듈로 확장 가능 |

최근 공저 논문에서도 이 경향이 명확하다.

- *Curated Collaborative AI Edge*는 B5G/6G RAN에서 network data analytics를 이용해 협업과 자원 제어를 연결한다.
- *Deep Resource Localization*은 지역 traffic pattern을 예측한 뒤 PPO 기반 MEC 자원 할당으로 이어 간다.
- *In-time Conditional Handover*는 과거 mobility context를 이용해 대상 기지국과 dwell time을 함께 예측하고 resource reservation timing을 결정한다.
- *Urban Mobile Data Prediction with GECOS*는 geospatial clustering과 residual TCN-LSTM을 결합하고 real-world traffic data에서 검증한다.
- *Inductive Bias Matters*는 CNN·Transformer·hybrid architecture를 같은 조건에서 비교한다. 이는 CHUM이 단일 architecture의 attribution을 최종 결론으로 삼지 않는 이유와 직접 맞닿는다.
- *Post-training Feature Pruning*은 5개 fundus dataset과 EfficientNetV2·ViT·CoAtNet을 사용하고 cross-dataset transfer까지 확인한다. 이는 성능 최고점보다 compactness와 generalization을 함께 보는 경향을 보여 준다.
- AAMAS 2026의 *EG-RAG*는 evidence graph를 이용한 reliable multi-document reasoning을 다룬다. CHUM은 다른 도메인이지만, “context가 존재한다”와 “신뢰할 수 있게 사용된다”를 구분한다는 문제 구조가 같다.
- EV battery diagnostics의 Mixture-of-Agents 연구는 실제 시계열 로그의 의미적 grouping과 자동 보고를 결합한다. CHUM의 event–channel utility map은 이러한 보고 시스템에 검증 가능한 근거층을 제공할 수 있다.

진행 과제도 같은 방향을 강화한다. 연구실은 2026–2031년 차세대 네트워크 AI Foundation Model, 2024–2028년 6G 통합 지능평면, 2024–2027년 네트워크 상태·구조 학습과 추론 신뢰도·조건 변화 강건성·NWDAF 통합, 망막 Foundation Model 중심의 의료기기 제품화 과제를 수행하고 있다.

### 2.3 교수님께 가장 설득력 있는 포지셔닝

CHUM을 “산업 공정의 새 모델”로 소개하면 연구실의 핵심 흐름과 연결이 약하다. 다음처럼 정의해야 한다.

> **CHUM은 industrial multivariate time series를 대상으로 한 trustworthy context-utilization audit다. 추가 context의 유용성을 모델 용량, perturbation-induced distribution shift, false alarms, optimization variability, architecture-specific behavior와 분리한다.**

이 문장은 연구실의 네트워크 AI, 신뢰 AI, 의료 AI 검증 성향을 하나의 방법론으로 연결하면서도 현재 실험 범위를 넘지 않는다.

---

## 3. 배경

산업 시스템의 관측치는 대체로 두 종류다.

- **Sensor state:** 온도, 압력, 유량, 진동 등 시스템의 상태를 관측한 값
- **Control history:** valve position, setpoint, motor command처럼 시스템에 가해진 조작의 시간 이력

sensor-only 모델은 결과 상태만 보고, sensor+control 모델은 시스템이 어떤 조작을 받았는지까지 본다. 따라서 control history는 이상을 더 일찍 또는 더 명확하게 구분하는 context가 될 수 있다. 하지만 입력 차원을 추가하면 모델 파라미터와 표현력이 함께 바뀌므로, 성능 향상만으로는 제어 이력 자체의 정보라고 결론 낼 수 없다.

또한 단순 feature occlusion은 해당 채널을 0으로 바꿔 학습 분포 밖의 시계열을 만들 수 있다. 이때 성능 저하가 해당 채널의 정보 손실이 아니라 비현실적 입력 충격에서 발생할 수 있고, 정상 구간의 false alarm도 증가한다. 단일 attribution map은 이런 교란을 직접 통제하지 못한다.

---

## 4. 문제의식과 연구 공백

### 4.1 한 문장 문제정의

> **어떤 산업 이상 사건에서 어떤 제어 채널의 과거 이력이, 모델 용량·분포 교란·오경보율을 통제한 뒤에도 재현 가능한 추가 탐지 정보를 제공하는가?**

### 4.2 기존 접근이 구분하지 못하는 것

1. 전체 평균 성능 향상과 event별 이질성
2. control information과 모델 capacity 증가
3. 실제 정보 손실과 OOD masking 충격
4. 특정 seed·run의 우연과 반복 가능한 효과
5. 특정 architecture의 inductive bias와 구조를 넘는 공통 신호
6. predictive utility와 물리적 인과·root cause

### 4.3 선행연구 대비 정확한 신규성

FIT·TimeSHAP·learned perturbation 연구는 conditional context와 시계열 attribution의 중요성을 이미 제기했다. OOD explainability 연구는 feature removal이 비현실적 샘플을 만들 수 있음을 보였다. 따라서 조건부 perturbation 자체를 새로운 원리로 주장하지 않는다.

본 연구의 신규성은 다음 요소를 **산업 이상 탐지의 하나의 판정 프로토콜**로 결합한 데 있다.

- capacity-matched sensor-only control
- 정상 train-only conditional replacement
- condition-specific validation calibration
- event/run 단위 효과와 hierarchical uncertainty
- pre-fault FPR guardrail
- imputer distribution·lag quality gate
- cross-architecture consensus
- IG 보조 삼각검증
- 외부 HIL 데이터에서의 제한적 반복
- 전 셀에 동일 적용한 post-hoc sensitivity grid

---

## 5. 연구질문과 가설

| ID | 연구질문·가설 | 반증 조건 |
| --- | --- | --- |
| RQ1 / H1 | control history의 이득은 fault/event별로 이질적이다 | 모든 event에서 유사한 gain이 나타나거나 안정된 GAIN subset이 없음 |
| RQ2 / H2 | 일부 gain은 capacity 증가로 설명되지 않는다 | F1−F0 효과가 F1−F0-C에서 소멸 |
| RQ3 / H3 | 정상분포 조건부 대치 후에도 특정 channel utility가 남는다 | ΔAUROC가 material gate 미달, seed 방향 불안정, CI에 0 포함, FPR guardrail 위반 |
| RQ4 / H4 | 핵심 channel mapping은 architecture에 강건하다 | TCN과 Transformer가 같은 fault에서 합의하지 못함 |
| RQ5 / H5 | 핵심 결론은 replacement hyperparameter에 강건하다 | block length 또는 draw count 변화에서 효과 방향·크기·FPR 기준 붕괴 |
| RQ6 / H6 | 다른 HIL 환경에서도 제한적 external support가 보인다 | HAI corrected v2의 F1 gain과 targeted channel score loss가 seed 간 반복되지 않음 |

---

## 6. 해결 방식: CHUM

### 6.1 모델 통제

- `F0`: sensor history만 입력
- `F1`: sensor history와 control history를 함께 입력
- `F0-C`: sensor만 입력하지만 hidden width를 늘려 F1과 parameter 수를 맞춘 capacity control

F1이 F0보다 좋고 F0-C보다도 좋을 때만 control history의 추가 정보 가능성을 인정한다.

### 6.2 조건부 대치

채널을 0으로 지우지 않는다. 정상 training window에서 대상 control channel을 제외한 나머지 sensor/control history로 해당 채널을 예측하는 leave-one-channel-out ridge imputer를 만든다. 여기에 정상 residual sequence를 block 단위로 sampling해 평균과 분산뿐 아니라 단기 자기상관을 최대한 보존한다. imputer는 test label이나 fault 구간을 학습에 사용하지 않는다.

### 6.3 utility estimand

architecture `a`, event `e`, control channel `c`에 대해 higher-is-better metric `M`의 utility를 다음처럼 정의한다.

`U(a,e,c;M) = M(original F1 score) − M(F1 score after conditional replacement of c)`

`U > 0`이면 해당 channel history를 정상 조건부 대안으로 바꿨을 때 탐지력이 감소했음을 뜻한다. 이는 **모델이 해당 history에서 조건부 예측 정보를 사용했다는 조작적 정의**이지 인과 효과가 아니다.

### 6.4 판정 gate

TEP channel-level primary 판정은 다음을 모두 요구한다.

1. mean ΔAUROC `≥ 0.02`
2. 5 seeds 중 `≥ 4`가 positive
3. 최대 절대 pre-fault ΔFPR `≤ 0.005`
4. paired hierarchical seed→run bootstrap 95% CI 하한 `> 0`
5. imputer의 held-out distribution·lag quality 통과
6. TCN과 Transformer 모두 위 기준 통과

이 구조는 큰 숫자 하나가 아니라 **효과 크기·반복성·오경보·대치 현실성·모델 합의**를 동시에 요구한다.

---

## 7. 아이디어 검증 과정

| 검증 단계 | 질문 | 실행 | 결과 |
| --- | --- | --- | --- |
| Capacity gate | 입력 차원 증가 때문인가 | F0/F1/F0-C, 5 seeds, 28 faults | 7개 fault gain이 F0-C 대비 유지 |
| Architecture gate | GRU만의 현상인가 | TCN·Transformer 30 models | 동일 7개 GAIN faults, PASS |
| Conditional CHUM | zero masking 충격인가 | 정상-only LOO residual sampling | 4개 two-architecture consensus cells |
| Quality gate | imputer가 비현실적인가 | R²·variance·Wasserstein·KS·lag 검사 | 품질 미달 F26/XMV4 실제 제외 |
| Attribution triangulation | CHUM만 그렇게 보이는가 | Integrated Gradients | primary top-1 7/8 일치 |
| External support | 다른 HIL 환경에서도 보이는가 | HAI 21.03 corrected v2 | global gain + targeted 5 cells |
| Integrity audit | 누수·버그·집계 오류가 남았는가 | overlap 제거, v1 무효화, raw 재계산 | 18/18 checks PASS |
| Sensitivity gate | block/draw 고정값 의존인가 | 3×3×2×5 locked grid | 4/4 cells, 두 architecture PASS |

핵심은 성공 결과만 남긴 것이 아니다. 예를 들어 TEP `F26/XMV4`는 raw effect가 컸지만 imputer quality gate를 통과하지 못해 최종 consensus에서 제외했고, HAI v1은 feature column order bug를 발견한 뒤 전체를 무효화했다. corrected v2만 최종 주장에 사용한다.

---

## 8. Dataset과 split

| 항목 | TEP | HAI 21.03 |
| --- | --- | --- |
| 환경 | simulated chemical process faults | hardware-in-the-loop cyber-physical attacks |
| 규모 | 2,800 runs, 28 faults | 8 episodes, 1,323,608 rows, 50 global attack events |
| 변수 역할 | 41 XMEAS sensors, 11 XMV controls | 29 sensor targets, 28 active control histories |
| 분할 | run 단위 1,792/448/560 train/validation/test | episode/time-aware 분리, train 내부 80/20 |
| 반복 | seeds 42–46 | seeds 42–44 |
| 주요 위험 | 동일 run window leakage | train–test telemetry exact overlap, role/target ambiguity |
| 대응 | run-before-window split | exact-overlap 43,202 train rows 제거, role/target audit |

TEP는 방법 개발과 strict consensus의 주 근거다. HAI는 산업·HIL 맥락의 외부 지지지만, 모든 process subgroup과 모든 비공격 control history에 대한 보편 검증으로 해석하지 않는다.

---

## 9. 전처리 방식

### 9.1 공통 원칙

1. split을 먼저 확정하고 window를 생성한다.
2. scaler와 imputer는 training 정상 데이터에만 fit한다.
3. threshold는 validation 정상 score percentile로만 정한다.
4. 각 perturbation condition의 score distribution에 맞춰 validation threshold를 다시 보정한다.
5. test label은 metric 계산에만 사용하고 training·scaling·imputation·threshold selection에 사용하지 않는다.

### 9.2 TEP

- window length: 20
- fault onset: sample 600
- channel 분석 구간: sample 400–900
- threshold: validation-normal 99th percentile
- alarm: threshold 3회 연속 초과
- conditional replacement: LOO ridge prediction + normal residual block sampling
- 기준 설정: residual block 20, draws 3

### 9.3 HAI

- window length: 30
- train stride: 10
- threshold: validation-normal 99.5th percentile
- alarm: threshold 3회 연속 초과
- official time-aware eTaF1을 AUROC·AUPRC와 함께 사용
- point-role·attack-target manifest를 먼저 검증
- exact duplicate telemetry가 test와 겹친 43,202 training rows 제거

---

## 10. 모델링

| Architecture | 목적 | 공정한 비교 장치 |
| --- | --- | --- |
| GRU | 최초 event-level 현상 확인 | F0 23,209 / F1 25,321 / F0-C 25,473 parameters |
| two-layer TCN | convolutional temporal inductive bias | F0 8,425 / F1 9,481 / F0-C 9,526 parameters |
| compact two-layer Transformer | attention 기반 구조 검증 | F0/F0-C 20,489 / F1 20,841 parameters, 1.7% 차이 |
| HAI compact sequence forecaster | 외부 HIL 반복 | F1 30,941 / F0-C 31,021 parameters, 약 0.26% 차이 |

본 논문은 architecture 최고점 경쟁을 하지 않는다. 동일 split·preprocessing·threshold 원칙 아래 서로 다른 inductive bias에서 **결론의 방향이 반복되는지**를 검증한다.

---

## 11. 실험 설계와 평가 지표

### 11.1 실험 행렬

| 실험 | 단위 | 모델/조건 | 반복·규모 | 판정 목적 |
| --- | --- | --- | --- | --- |
| TEP capacity | fault | F0/F1/F0-C × GRU | 5 seeds × 28 faults | event heterogeneity와 capacity 통제 |
| TEP architecture | fault | F0/F1/F0-C × TCN/Transformer | 30 trained models | 구조를 넘는 event gain |
| TEP G3 CHUM | fault–channel | conditional/LOO-sample/zero | 340 tasks, 9,520 fault rows, 190,400 run rows | channel consensus |
| IG baseline | architecture–fault–channel | Integrated Gradients | 880 rows | 보조 attribution 일치 |
| HAI external v2 | global/event | F0/F1/F0-C | 9 models, 450 event rows | 제한적 외부 지지 |
| HAI conditional | attack–channel | LOO-sample/zero | 171 tasks, 8,550 event rows | 직접 공격 channel utility |
| Primary sensitivity | locked cell | block 5/10/20 × draws 1/3/10 | 390 tasks = 360 perturbation + 30 shared original, 7,800 run rows | 고정값 의존성 반증 |

### 11.2 지표

- sample ranking: AUROC, AUPRC
- event-aware detection: eTaF1, detected-run ratio, detection delay
- safety guardrail: pre-fault FPR 및 condition 간 절대 변화
- attribution effect: original−conditional ΔAUROC/ΔAUPRC, normalized event-score loss
- uncertainty: 2,000회 paired hierarchical seed→run/event bootstrap
- consistency: positive seed count, architecture consensus, IG top-1 agreement
- imputer quality: predictive R², SD ratio, mean shift, lag-1 error, train-range violation, Wasserstein, KS

---

## 12. 완료된 실험 결과

### 12.1 TEP event-level architecture robustness

TCN과 Transformer는 동일한 7개 GAIN faults `4, 7, 19, 23, 24, 25, 26`을 식별했다. 모든 fault에서 두 architecture 모두 5/5 seed가 같은 방향이었다.

| Fault | TCN F1−F0-C ΔAUROC | Transformer F1−F0-C ΔAUROC | 해석 |
| ---: | ---: | ---: | --- |
| 4 | +0.1663 | +0.1087 | 두 구조에서 material gain |
| 7 | +0.4880 | +0.4845 | 가장 큰 공통 gain |
| 19 | +0.1783 | +0.1970 | 안정적 공통 gain |
| 23 | +0.0300 | +0.0234 | GRU strict set과 달라 architecture-dependent로 표시 |
| 24 | +0.1091 | +0.0877 | 안정적 공통 gain |
| 25 | +0.2916 | +0.2776 | 큰 공통 gain |
| 26 | +0.3868 | +0.4154 | event gain은 크지만 channel quality gate에서 주의 |

GRU의 대표 seed-42 event-level 결과도 숨기지 않는다.

| GRU variant | 입력 | AUROC | AUPRC | 탐지 지연 |
|---|---|---:|---:|---:|
| F0 | XMEAS | 0.7508 | 0.8995 | 51.9 |
| F1 | XMEAS+XMV | 0.8196 | 0.9312 | 24.6 |
| F0-C | XMEAS, capacity-matched | 0.7493 | 0.8989 | 49.4 |

F0→F1의 event-level 방향은 model seed 42–44에서 반복됐고 F0-C는 이득을
재현하지 못했다. 이는 추가 예측 정보의 근거이지 인과적 controller effect의
근거가 아니다.

### 12.2 TEP channel-level consensus

| Locked cell | TCN ΔAUROC | Transformer ΔAUROC | TCN CI 하한 | Transformer CI 하한 | 기준 설정 최대 abs(ΔFPR) |
| --- | ---: | ---: | ---: | ---: | ---: |
| F4/XMV10 | +0.1653 | +0.1055 | +0.1241 | +0.0882 | 0.00075 |
| F19/XMV7 | +0.1355 | +0.1237 | +0.1270 | +0.1135 | 0.00075 |
| F19/XMV8 | +0.0555 | +0.0531 | +0.0505 | +0.0467 | 0.00050 |
| F25/XMV2 | +0.2899 | +0.2637 | +0.2850 | +0.2547 | 0.00125 |

모든 architecture–cell에서 5/5 seed가 positive였다. `F26/XMV4`는 raw effect가 컸지만 imputer distribution quality를 만족하지 못해 최종 셀에서 제외했다. 즉 gate가 형식적 장식이 아니라 실제 탈락 기준으로 작동했다.

#### 후보 분모와 BH-FDR

G3는 28 faults × archive XMV 11개 = 308개 raw cell을 전수 계산했다.
XMV5·XMV9는 상수이고 XMV4는 primary LOO-residual imputer quality gate를
통과하지 못했다. 따라서 confirmatory candidate family는 28 faults ×
8 reliable channels = **224 cells**다. 20개 held-out run을 paired cluster로
삼아 두 architecture와 5 seeds의 delta를 평균한 뒤 200,000회 단측
sign-flip permutation을 시행하고, 224개 p-value 전체에 BH를 적용했다.

- q=0.05: 42/224 cells 생존
- q=0.10: 48/224 cells 생존
- 기존 locked cells: q=0.05에서 4/4, q=0.10에서 4/4 생존
- locked cell BH q-value: 모두 `0.000056`(Monte Carlo resolution 기준)

상세 결과는 `outputs/chum_multiplicity/BH_FDR_RESULTS.csv`와
`MULTIPLICITY_REPORT.md`에 공개했다.

#### GRU channel 결과 공개와 consensus 제외 사유

| Locked cell | GRU conditional ΔAUROC | TCN LOO ΔAUROC | Transformer LOO ΔAUROC | GRU raw 방향 | GRU consensus 사용 |
|---|---:|---:|---:|:---:|:---:|
| F4/XMV10 | +0.4191 | +0.1653 | +0.1055 | 5/5 positive | 제외 |
| F19/XMV7 | +0.0143 | +0.1355 | +0.1237 | 5/5 positive | 제외 |
| F19/XMV8 | +0.0289 | +0.0555 | +0.0531 | 5/5 positive | 제외 |
| F25/XMV2 | +0.0217 | +0.2899 | +0.2637 | 5/5 positive | 제외 |

GRU raw 방향은 4/4 cell에서 TCN·Transformer locked 방향과 같았다. 그러나
GRU는 legacy conditional-mean 대치이고 TCN·Transformer 확정판은 LOO
residual sampling이다. GRU에는 동일한 paired hierarchical run CI가 없고,
legacy imputer gate에서 XMV8·XMV10이 탈락했다. 따라서 이를 3-architecture
consensus로 승격하지 않았다. 이는 GRU 불일치나 음성 결과 은폐가 아니라
**조건 상이로 인한 비교 제외**다. 전량 표는
`outputs/architecture_consensus/THREE_ARCH_COMPARISON.csv`에 있다.

### 12.3 IG 교차검증

| 집합 | 셀 수 | Spearman 중앙값 | top-1 일치 |
| --- | ---: | ---: | ---: |
| Locked primary | 8 | 0.5434 | 7/8, 87.5% |
| Negative/exploratory | 8 | 0.1005 | 1/8, 12.5% |

IG와 CHUM은 estimand가 다르므로 동일값을 기대하지 않는다. 중요한 점은 모든 fault에서 자동으로 일치한 것이 아니라 CHUM 효과가 강한 primary 집합에서만 높은 top-1 합의가 나타났다는 것이다.

불일치 1건은 **TCN/F4**다. IG는 XMV6을 top-1
(`normalized XMV IG=0.2608`)로, CHUM은 XMV10을 top-1로 선택했다. IG에서
XMV10도 0.2481로 근접한 2위였지만, conditional replacement의 ΔAUROC는
XMV10 `+0.1653`, XMV6 `+0.0021`로 크게 달랐다. 즉 순간 score gradient는
XMV6에도 민감했지만 정상 조건부 대치 후 탐지 utility는 XMV10에 집중됐다.
상관·중복 입력에서 local sensitivity와 conditional necessity가 갈릴 수
있다는 사례이며, IG를 보조 삼각검증으로만 사용한 이유다.

### 12.4 HAI 21.03 corrected v2

| Variant | Parameters | AUROC | AUPRC | eTaF1 | FPR | 평균 지연 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| F0 | 26,909 | 0.8331 | 0.4743 | 0.5895 | 0.00267 | 47.48 |
| F0-C | 31,021 | 0.8301 | 0.4663 | 0.5807 | 0.00264 | 49.18 |
| F1 | 30,941 | 0.8518 | 0.5049 | 0.6162 | 0.00270 | 43.74 |

- F1−F0: AUROC `+0.018745`, AUPRC `+0.030608`, eTaF1 `+0.026722`
- F1−F0-C: AUROC `+0.021744`, AUPRC `+0.038605`, eTaF1 `+0.035477`
- 모든 전역 차이는 3/3 seed에서 같은 방향
- 직접 공격된 5개 event–channel 셀의 normalized score loss: `+0.0588–+0.2146`, 모두 3/3 seed positive

3개 model seed에 대한 t 기반 95% CI는 다음과 같다. 표본이 3개뿐이므로
분포 가정에 민감한 기술적 불확실성 구간이며 독립 데이터셋 반복으로
해석하지 않는다.

| F1−F0 metric | mean delta | 95% t CI |
|---|---:|---:|
| AUROC | +0.018745 | [+0.008222, +0.029269] |
| AUPRC | +0.030608 | [+0.023288, +0.037927] |
| eTaF1 | +0.026722 | [−0.009483, +0.062926] |

HAI 결과는 **제한적 외부 지지**다. AUROC/AUPRC 구간은 양수지만 eTaF1
구간은 0을 포함하고, attack target이 직접 control point인 셀을 포함한다.
따라서 공격받지 않은 control context의 보편적 유용성이나 TEP와 동급의
확립된 증거로 해석하지 않는다.

---

## 13. 새로 완료한 최종 민감도 실험

### 13.1 전 셀에 동일 적용한 post-hoc 설계

- locked cells: `F4/XMV10`, `F19/XMV7`, `F19/XMV8`, `F25/XMV2`
- block length: `5, 10, 20`
- conditional draws: `1, 3, 10`
- architecture: TCN, Transformer
- seeds: `42–46`
- 기존 checkpoint 재사용, 재학습 없음
- paired hierarchical bootstrap 2,000회

실행 task 390개의 구성은 **360 perturbation + 30 original baseline**이다.
360은 4 cells × 2 architectures × 5 seeds × 9 settings이고, original은
두 F19 channel이 같은 fault baseline을 공유하므로 3 unique faults ×
2 architectures × 5 seeds = 30이다. `SENSITIVITY_CELL_RESULTS.csv`의
360행은 delta가 정의되는 perturbation만 담고, raw fault/run 표의 390
task에는 공유 baseline 30개가 포함된다. 추가 30개는 negative control,
실패 재실행 또는 누락분이 아니다.

Git 이력에서는 config·판정 JSON·결과 CSV가 같은 커밋에 처음 등장해
prospective preregistration을 입증할 수 없다. 따라서 이 절의 기준은
post-hoc robustness rule로 보고하며, 감사 근거는
`docs/PREREGISTRATION_AUDIT.md`에 공개한다.

architecture–cell 하나가 robust하려면 다음을 요구했다.

- positive mean ΔAUROC: 9/9 settings
- material ΔAUROC `≥ 0.02`: 최소 8/9
- positive seeds `≥ 4/5`: 최소 8/9
- hierarchical run CI 하한 `> 0`: 최소 8/9
- absolute FPR shift `≤ 0.005`: 9/9
- 기준 설정 block 20/draws 3이 모든 setting gate 통과

최종 PASS는 네 셀 모두에서 두 architecture가 robust해야 한다.

### 13.2 결과

**PASS — 4/4 locked cells가 두 architecture에서 통과했다.** 실제로 8개 architecture–cell 모두 positive/material/seed-stable/CI-positive/FPR guardrail을 9/9 설정에서 만족했다.

| Architecture · cell | 9개 설정 ΔAUROC 범위 | 최악 abs(ΔFPR) | 결과 |
| --- | ---: | ---: | --- |
| TCN · F4/XMV10 | +0.16527–+0.16534 | 0.00075 | PASS |
| Transformer · F4/XMV10 | +0.10550–+0.10556 | 0.00075 | PASS |
| TCN · F19/XMV7 | +0.13541–+0.13579 | 0.00150 | PASS |
| Transformer · F19/XMV7 | +0.12356–+0.12388 | 0.00075 | PASS |
| TCN · F19/XMV8 | +0.05543–+0.05554 | 0.00050 | PASS |
| Transformer · F19/XMV8 | +0.05304–+0.05310 | 0.00075 | PASS |
| TCN · F25/XMV2 | +0.28979–+0.29017 | 0.00125 | PASS |
| Transformer · F25/XMV2 | +0.26343–+0.26442 | 0.00150 | PASS |

최악 설정에서도 최소 ΔAUROC는 `+0.05304`로 material gate `+0.02`의 2.65배였다. 이 결과는 본 논문의 중심 결론이 block length나 stochastic draw count의 한 고정값에서만 생겼다는 반론을 직접 차단한다.

---

## 14. 연구 무결성과 재현성

- TEP/HAI 모두 split 전에 window를 섞지 않는다.
- scaler·imputer·threshold는 train/validation만 사용한다.
- HAI train–test exact overlap 43,202 rows를 제거했다.
- HAI feature-order bug가 발견된 v1은 전량 무효화하고 최종 집계에서 격리했다.
- G3 340 tasks, IG 880 rows, HAI v2 9 models, HAI conditional 171 tasks를 key duplicate 없이 완료했다.
- 기존 최종 raw evidence validator 18/18 checks가 PASS했다.
- 새 sensitivity는 config·runner·analyzer·manifest·raw tables·2,000회 bootstrap 요약을 보존했다.
- sensitivity 기준은 사전등록으로 주장하지 않고, 전 cell/setting에 동일 적용한 post-hoc rule로 표시했다.
- G3 raw 308 cells와 quality-gated 224-cell 분모, BH-FDR 결과를 공개했다.
- 연구실 publication 전수표와 분류 규칙도 코드로 재생성 가능하다.

---

## 15. 핵심 기여

1. **문제정의 기여:** “control을 추가하면 성능이 오르는가”를 “어떤 event–channel에서 control history가 조건부 정보를 제공하는가”로 바꾼다.
2. **방법 기여:** capacity control, 정상분포 대치, condition calibration, FPR guardrail, hierarchical uncertainty, architecture consensus를 하나의 audit protocol로 결합한다.
3. **실증 기여:** TEP에서 224-cell BH-FDR을 포함해 4개 architecture-robust channel cells와 7개 event-level gain faults를 확립한다.
4. **강건성 기여:** 3×3 replacement sensitivity에서 4/4 locked cells가 두 architecture에서 유지됨을 보인다.
5. **제한적 외부 지지:** HAI corrected v2의 3 seeds에서 global gain과 5개 directly attacked control cells의 conditional support를 제시하되 TEP와 동급으로 두지 않는다.
6. **연구 관행 기여:** 실패한 imputer cell과 잘못된 HAI v1을 숨기지 않고 exclusion rule과 invalidation trail을 공개한다.

---

## 16. 의의와 한계

### 16.1 의의

- 운영자가 모든 control channel을 동일하게 설명·감시할 필요 없이 event별 핵심 context를 좁힐 수 있다.
- attribution을 heatmap 하나가 아니라 탐지력 손실·오경보·대치 품질·모델 합의로 검증한다.
- 네트워크 AI에서도 telemetry/context를 foundation model이나 NWDAF에 넣기 전에 실제 utility를 감사하는 형태로 확장할 수 있다.
- 의료 AI의 multi-backbone·cross-dataset 검증 철학을 산업 시계열 context 분석으로 옮긴다.

### 16.2 한계

- conditional replacement는 observational test이며 intervention이 아니다.
- 선택된 channel은 fault의 물리적 원인이나 최적 제어변수라는 뜻이 아니다.
- TEP 5 seeds는 최적화 변동성 반복이지 독립 dataset 5개가 아니다. 양측 exact sign-flip test 최소 p값은 0.0625이므로 seed-level `p<0.05`를 주장하지 않는다.
- HAI는 3 seeds이고 직접 공격 control 셀을 포함하며 eTaF1 차이의 t 기반 95% CI가 0을 포함하므로 external evidence의 범위가 제한된다.
- imputer quality gate를 통과하지 못하는 channel에는 CHUM의 결론을 내리지 않는다.
- 전체 산업·통신·의료 도메인으로의 보편 일반화는 후속 검증이 필요하다.

---

## 17. 발전 가능성

### 17.1 논문 이후 1순위: Network Context Utility Audit

6G/NWDAF traffic·mobility·resource telemetry를 state와 action/context로 분리하고, time-series foundation model 또는 network predictor가 어떤 context를 실제로 사용하는지 CHUM gate로 감사한다. 연구실의 NFM·6G 지능평면·추론 신뢰도 과제와 가장 직접적으로 연결된다.

### 17.2 2순위: Drift-aware online CHUM

정상분포 imputer와 utility map의 변화를 online drift signal로 이용한다. channel utility가 붕괴하거나 FPR이 이동할 때 recalibration 또는 human review를 요청한다.

### 17.3 3순위: Causal/digital-twin extension

TEP simulator나 실제 digital twin에서 명시적 intervention을 수행해 predictive utility와 causal effect를 분리한다. 이것이 root-cause 주장으로 넘어가기 위한 필수 단계다.

### 17.4 4순위: Evidence-grounded automated reporting

CHUM의 event–channel evidence와 uncertainty를 graph 또는 structured evidence로 만들어 EV/industrial diagnostic LLM의 보고 근거로 사용한다. LLM은 결론을 생성하되, utility gate를 통과하지 못한 channel은 근거로 제시하지 않도록 제한한다.

---

## 18. 논문 집필 구조

1. **Introduction** — 평균 성능 비교가 숨기는 event-level heterogeneity와 context-utilization 문제
2. **Related Work** — controller-aware detection, time-series attribution, conditional perturbation, OOD explainability, model multiplicity
3. **Problem Formulation** — F0/F1/F0-C와 conditional utility estimand
4. **CHUM Method** — imputer, calibration, FPR, uncertainty, consensus gate
5. **Datasets and Integrity Protocol** — TEP/HAI, roles, splits, overlap removal, invalidated v1
6. **Event-Level Results** — capacity and architecture gates
7. **Channel-Level Results** — conditional CHUM, imputer audit, IG triangulation
8. **External and Sensitivity Validation** — HAI corrected v2, 3×3 locked sensitivity
9. **Discussion** — 연구실 방향과의 연결, 운영적 의미, 한계
10. **Conclusion** — 조건부 예측 정보의 범위 안에서 최종 주장

---

## 19. 집필 일정과 종료 기준

| 주차 | 산출물 | 종료 기준 |
| --- | --- | --- |
| 1주차 | Introduction, RQ, Contribution, Methods 도식 | 핵심 claim과 금지 claim을 지도교수와 잠금 |
| 2주차 | Dataset/Preprocessing/Model/Experiment, 표·그림 | 모든 수치가 raw/summary table과 일치 |
| 3주차 | Results, Discussion, Related Work | 각 주장에 effect·uncertainty·guardrail·limitation 연결 |
| 4주차 | 전체 교정, appendix, reproducibility package | 표/그림 번호·source·config·commit 일치, 문장 과장 제거 |

추가 실험은 교수님이 현재 claim보다 더 강한 claim을 요구할 때만 수행한다.

- seed-level `p<0.05`가 필요하면 TEP seed를 늘린다.
- 공격받지 않은 control context의 외부 일반화가 필요하면 새 HIL/실데이터를 추가한다.
- root cause를 주장하려면 intervention 또는 digital twin causal experiment를 새 연구로 설계한다.

---

## 20. 지도교수에게 요청할 세 가지 결정

1. 문제를 **“제어 이력 추가의 평균 효과”가 아니라 “event–channel별 조건부 utility”**로 확정할 것인가?
2. 주 기여를 새 detector가 아니라 **CHUM audit protocol과 architecture-robust evidence**로 둘 것인가?
3. 현재 claim boundary를 유지한 채 본문 집필을 시작하고, 더 강한 causal/generalization claim은 후속 연구로 분리할 것인가?

권고 답은 세 항목 모두 **예**다.

---

## 21. 주요 출처

### 교수·연구실

- Superintelligence Laboratory: http://monet.skku.edu/main/
- 연구 분야: http://monet.skku.edu/main/bbs/board.php?bo_table=areas
- 진행 과제: http://monet.skku.edu/main/bbs/board.php?bo_table=projects
- 2026 Journal 목록: http://monet.skku.edu/main/bbs/board.php?bo_table=public1&sca=2026
- 2026 Conference 목록: http://monet.skku.edu/main/bbs/board.php?bo_table=public2&sca=2026
- SKKU Pure profile: https://pure.skku.edu/en/persons/hyunseung-choo/
- Curated Collaborative AI Edge: https://pure.skku.edu/en/publications/curated-collaborative-ai-edge-with-network-data-analytics-for-b5g/
- Deep Resource Localization: https://pure.skku.edu/en/publications/deep-resource-localization-with-traffic-prediction-for-adaptive-m/
- In-time Conditional Handover: https://pure.skku.edu/en/publications/in-time-conditional-handover-for-b5g6g/
- GECOS: https://pure.skku.edu/en/publications/urban-mobile-data-prediction-with-geospatial-clustering-and-dual-/
- Post-training Feature Pruning, CVPR 2026: https://openaccess.thecvf.com/content/CVPR2026/html/Pham_Post-training_Feature_Pruning_for_Fundus_Images_Classification_CVPR_2026_paper.html
- EG-RAG, AAMAS 2026 proceedings: https://www.ifaamas.org/Proceedings/aamas2026/forms/contents.htm
- Mixture-of-Agents EV diagnostics: https://filuta.ai/papers/CompAI_2025_paper_3.pdf

### 핵심 방법 선행연구

- FIT: https://proceedings.neurips.cc/paper/2020/hash/08fa43588c2571ade19bc0fa5936e028-Abstract.html
- TimeSHAP: https://arxiv.org/abs/2012.00073
- OOD explainability: https://proceedings.neurips.cc/paper/2021/hash/1def1713ebf17722cbe300cfc1c88558-Abstract.html
- Learning Perturbations: https://proceedings.mlr.press/v202/enguehard23a.html
- Rashomon Importance Distribution: https://proceedings.neurips.cc/paper_files/paper/2023/hash/1403ab1a427050538ec59c7f570aec8b-Abstract-Conference.html
- Quantitative explanation evaluation: https://proceedings.mlr.press/v206/jethani23a.html

---

## 최종 판정

**MANUSCRIPT-READY.** 현재 증거는 “일부 산업 이상 사건에서 특정 control history가 조건부 예측 정보를 제공하며, 그 mapping이 capacity·FPR·distribution quality·architecture·replacement hyperparameter 통제 후에도 반복된다”는 석사논문 수준의 주장을 지지한다. 다음 행동은 새 실험 탐색이 아니라 제목·RQ·claim boundary를 지도교수와 잠그고 본문 집필을 시작하는 것이다.
