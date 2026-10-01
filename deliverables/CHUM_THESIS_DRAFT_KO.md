# 산업 시계열 이상 탐지에서 제어 이력의 조건부 유용성 감사

CHUM: Architecture-Robust Auditing of Control-History Utility for Industrial Time-Series Anomaly Detection

검토용 논문 초안 · 2026-09-21

기존 연구의 방법과 결과를 논문 순서로 재구성한 초안이다. 제목과 최종 주장에 대한 지도교수 승인 또는 학교 제출 완료를 뜻하지 않는다. 2026-09-21에 보존 원자료 기반 18개 검증, 224-cell 다중비교, 민감도 bootstrap을 재실행했다. 모델 재학습과 원시 telemetry 전처리는 재실행하지 않았다.

## 초록

산업 이상 탐지에서 제어 이력의 추가 효과를 평균 성능만으로 평가하면 사건별 이질성, 모델 용량, 비현실적인 입력 대치와 오경보의 영향을 구분하기 어렵다. 본 연구는 Control-History Utility Mapping(CHUM)을 통해 센서 전용 모델, 센서·제어 결합 모델, 용량을 맞춘 센서 전용 대조군을 비교하고, 정상 데이터 기반 조건부 대치와 대치 품질·오경보·반복성·모델 구조 합의를 결합한다. TEP의 28개 fault에서 TCN과 Transformer는 동일한 7개 fault의 event-level gain을 보였다. 채널 수준에서는 F4/XMV10, F19/XMV7, F19/XMV8, F25/XMV2가 두 구조의 판정 기준을 충족했다. 대치 품질을 통과한 224개 후보에 BH 보정을 적용한 결과 네 셀이 모두 q=0.05에서 유지됐다. 세 residual block 길이와 세 draw 수를 교차한 민감도 분석에서도 네 셀이 유지됐다. HAI corrected v2에서는 전역 AUROC와 AUPRC 개선 및 직접 공격된 5개 채널 셀의 score 감소가 관찰됐으나, 3개 seed와 직접 공격 조건의 제한 때문에 외부 지지로 한정한다. CHUM은 평가한 모델과 대치 분포 아래의 예측 유용성을 감사하며 물리적 원인이나 인과적 제어 효과를 식별하지 않는다.

주요어: 산업 시계열, 이상 탐지, 제어 이력, 조건부 대치, 설명 가능성, 강건성

## 1. 서론

산업 시계열에는 센서가 관측한 상태와 제어 시스템의 조작 이력이 함께 기록된다. 제어 이력은 현재 센서 상태만으로는 구분하기 어려운 동작 조건을 제공할 수 있다. 그러나 제어 변수를 입력에 추가해 평균 탐지 성능이 개선됐다는 사실만으로 어느 사건에서 어느 채널을 모델이 활용했는지는 알 수 없다. 입력 차원과 함께 변한 모델 용량도 분리해야 한다.

채널을 제거한 뒤 탐지력이 감소하는지 측정하는 접근에도 교란이 있다. 비현실적인 대치 값은 정상 구간의 score를 변화시키고 오경보를 증가시킬 수 있다. 또한 한 모델의 중요도가 다른 구조에서도 유지된다는 보장은 없다. 따라서 유용성은 효과크기 하나가 아니라 대치 품질, 정상 구간 변화, 반복 실행의 안정성과 함께 평가해야 한다.

본 연구의 질문은 어떤 사건과 제어 채널에서 이러한 통제 뒤에도 추가 탐지 정보가 유지되는가이다. 이를 위해 CHUM 평가 프로토콜을 구성하고 TEP에서 주 분석을, HAI 21.03에서 제한적 외부 검증을 수행했다. 기여는 새 검출기의 최고 성능이 아니라 용량 대조군, 정상 조건부 대치, 조건별 임계값 보정, FPR 제한과 구조 간 합의를 결합한 감사 절차 및 그 실증이다.

## 2. 관련 연구

FIT는 시간에 따른 예측 분포 변화를 통해 다변량 시계열 관측의 중요도를 평가하며 시간 의존적 분포 변화를 통제할 필요성을 다룬다. TimeSHAP은 KernelSHAP을 순차 입력으로 확장해 feature·timestep·cell 수준 attribution을 산출한다. CHUM은 산업 fault별 탐지력 손실과 오경보 제한을 함께 평가한다는 점에서 평가 대상이 다르다. [1, 2]

Hase 등의 연구는 feature removal로 생성된 분포 밖 입력이 중요도 설명과 평가를 왜곡할 수 있음을 다룬다. CHUM은 정상 데이터로 학습한 대치와 품질 검사에 이 문제의식을 반영한다. 다만 정상 구간 품질 검사를 통과했다는 사실이 이상 구간에서 정확한 조건부 분포를 복원했다는 증명은 아니다. [3]

Integrated Gradients는 sensitivity와 implementation invariance를 중심으로 제안된 attribution 방법이다. CHUM의 탐지 utility와 동일한 양을 추정하지 않으므로 채널 순위의 보조 비교로 사용한다. FIT나 TimeSHAP 대비 성능 우위를 실험한 것이 아니며 조건부 대치 자체의 최초 제안도 주장하지 않는다. [4]


## 3. 연구질문과 반증 조건

| ID | 연구질문·가설 | 반증 조건 |
| --- | --- | --- |
| RQ1 / H1 | control history의 이득은 fault/event별로 이질적이다 | 모든 event에서 유사한 gain이 나타나거나 안정된 GAIN subset이 없음 |
| RQ2 / H2 | 일부 gain은 capacity 증가로 설명되지 않는다 | F1−F0 효과가 F1−F0-C에서 소멸 |
| RQ3 / H3 | 정상분포 조건부 대치 후에도 특정 channel utility가 남는다 | ΔAUROC가 material gate 미달, seed 방향 불안정, CI에 0 포함, FPR guardrail 위반 |
| RQ4 / H4 | 핵심 channel mapping은 architecture에 강건하다 | TCN과 Transformer가 같은 fault에서 합의하지 못함 |
| RQ5 / H5 | 핵심 결론은 replacement hyperparameter에 강건하다 | block length 또는 draw count 변화에서 효과 방향·크기·FPR 기준 붕괴 |
| RQ6 / H6 | 다른 HIL 환경에서도 제한적 external support가 보인다 | HAI corrected v2의 F1 gain과 targeted channel score loss가 seed 간 반복되지 않음 |


## 4. CHUM 방법

### 4.1 모델 통제

- `F0`: sensor history만 입력
- `F1`: sensor history와 control history를 함께 입력
- `F0-C`: sensor만 입력하지만 hidden width를 늘려 F1과 parameter 수를 맞춘 capacity control

F1이 F0보다 좋고 F0-C보다도 좋을 때만 control history의 추가 정보 가능성을 인정한다.

### 4.2 조건부 대치

채널을 0으로 지우지 않는다. 정상 training window에서 대상 control channel을 제외한 나머지 sensor/control history로 해당 채널을 예측하는 leave-one-channel-out ridge imputer를 만든다. 여기에 정상 residual sequence를 block 단위로 sampling해 평균과 분산뿐 아니라 단기 자기상관을 최대한 보존한다. imputer는 test label이나 fault 구간을 학습에 사용하지 않는다.

### 4.3 utility estimand

architecture `a`, event `e`, control channel `c`에 대해 higher-is-better metric `M`의 utility를 다음처럼 정의한다.

`U(a,e,c;M) = M(original F1 score) − M(F1 score after conditional replacement of c)`

`U > 0`이면 해당 channel history를 정상 조건부 대안으로 바꿨을 때 탐지력이 감소했음을 뜻한다. 이는 **모델이 해당 history에서 조건부 예측 정보를 사용했다는 조작적 정의**이지 인과 효과가 아니다.

### 4.4 판정 gate

TEP channel-level primary 판정은 다음을 모두 요구한다.

1. mean ΔAUROC `≥ 0.02`
2. 5 seeds 중 `≥ 4`가 positive
3. 최대 절대 pre-fault ΔFPR `≤ 0.005`
4. paired hierarchical seed→run bootstrap 95% CI 하한 `> 0`
5. imputer의 held-out distribution·lag quality 통과
6. TCN과 Transformer 모두 위 기준 통과

이 구조는 큰 숫자 하나가 아니라 **효과 크기·반복성·오경보·대치 현실성·모델 합의**를 동시에 요구한다.


## 5. 데이터와 분할

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


## 6. 전처리와 평가 구간

### 6.1 공통 원칙

1. split을 먼저 확정하고 window를 생성한다.
2. scaler와 imputer는 training 정상 데이터에만 fit한다.
3. threshold는 validation 정상 score percentile로만 정한다.
4. 각 perturbation condition의 score distribution에 맞춰 validation threshold를 다시 보정한다.
5. test label은 metric 계산에만 사용하고 training·scaling·imputation·threshold selection에 사용하지 않는다.

### 6.2 TEP

- window length: 20
- fault onset: sample 600
- channel 분석 구간: sample 400–900
- threshold: validation-normal 99th percentile
- alarm: threshold 3회 연속 초과
- conditional replacement: LOO ridge prediction + normal residual block sampling
- 기준 설정: residual block 20, draws 3

### 6.3 HAI

- window length: 30
- train stride: 10
- threshold: validation-normal 99.5th percentile
- alarm: threshold 3회 연속 초과
- official time-aware eTaF1을 AUROC·AUPRC와 함께 사용
- point-role·attack-target manifest를 먼저 검증
- exact duplicate telemetry가 test와 겹친 43,202 training rows 제거


## 7. 모델과 용량 통제

| Architecture | 목적 | 공정한 비교 장치 |
| --- | --- | --- |
| GRU | 최초 event-level 현상 확인 | F0 23,209 / F1 25,321 / F0-C 25,473 parameters |
| two-layer TCN | convolutional temporal inductive bias | F0 8,425 / F1 9,481 / F0-C 9,526 parameters |
| compact two-layer Transformer | attention 기반 구조 검증 | F0/F0-C 20,489 / F1 20,841 parameters, 1.7% 차이 |
| HAI compact sequence forecaster | 외부 HIL 반복 | F1 30,941 / F0-C 31,021 parameters, 약 0.26% 차이 |

본 논문은 architecture 최고점 경쟁을 하지 않는다. 동일 split·preprocessing·threshold 원칙 아래 서로 다른 inductive bias에서 **결론의 방향이 반복되는지**를 검증한다.


## 8. 실험 설계와 평가 지표

### 8.1 실험 행렬

| 실험 | 단위 | 모델/조건 | 반복·규모 | 판정 목적 |
| --- | --- | --- | --- | --- |
| TEP capacity | fault | F0/F1/F0-C × GRU | 5 seeds × 28 faults | event heterogeneity와 capacity 통제 |
| TEP architecture | fault | F0/F1/F0-C × TCN/Transformer | 30 trained models | 구조를 넘는 event gain |
| TEP G3 CHUM | fault–channel | conditional/LOO-sample/zero | 340 tasks, 9,520 fault rows, 190,400 run rows | channel consensus |
| IG baseline | architecture–fault–channel | Integrated Gradients | 880 rows | 보조 attribution 일치 |
| HAI external v2 | global/event | F0/F1/F0-C | 9 models, 450 event rows | 제한적 외부 지지 |
| HAI conditional | attack–channel | LOO-sample/zero | 171 tasks, 8,550 event rows | 직접 공격 channel utility |
| Primary sensitivity | locked cell | block 5/10/20 × draws 1/3/10 | 390 tasks = 360 perturbation + 30 shared original, 7,800 run rows | 고정값 의존성 반증 |

### 8.2 지표

- sample ranking: AUROC, AUPRC
- event-aware detection: eTaF1, detected-run ratio, detection delay
- safety guardrail: pre-fault FPR 및 condition 간 절대 변화
- attribution effect: original−conditional ΔAUROC/ΔAUPRC, normalized event-score loss
- uncertainty: 2,000회 paired hierarchical seed→run/event bootstrap
- consistency: positive seed count, architecture consensus, IG top-1 agreement
- imputer quality: predictive R², SD ratio, mean shift, lag-1 error, train-range violation, Wasserstein, KS


## 9. 결과

### 9.1 TEP event-level architecture robustness

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

### 9.2 TEP channel-level consensus

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

### 9.3 IG 교차검증

| 집합 | 셀 수 | Spearman 중앙값 | top-1 일치 |
| --- | ---: | ---: | ---: |
| Locked primary | 8 | 0.5434 | 7/8, 87.5% |
| Negative/exploratory | 8 | 0.1005 | 1/8, 12.5% |

IG와 CHUM은 estimand가 다르므로 동일값을 기대하지 않는다. 중요한 점은 모든 fault에서 자동으로 일치한 것이 아니라 CHUM 효과가 강한 primary 집합에서만 높은 top-1 합의가 나타났다는 것이다.

불일치 1건은 **TCN/F4**다. IG는 XMV6을 top-1
(`normalized XMV IG=0.2608`)로, CHUM은 XMV10을 top-1로 선택했다. IG에서
XMV10도 0.2481로 근접한 2위였지만, conditional replacement의 ΔAUROC는
XMV10 `+0.1653`, XMV6 `+0.0021`로 크게 달랐다. 즉 경로 적분 기반 attribution은
XMV6에도 민감했지만 정상 조건부 대치 후 탐지 utility는 XMV10에 집중됐다.
상관·중복 입력에서 경로 기반 score attribution과 조건부 탐지 utility가 갈릴 수
있다는 사례이며, IG를 보조 삼각검증으로만 사용한 이유다.

### 9.4 HAI 21.03 corrected v2

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


## 10. 대치 민감도 분석

### 10.1 전 셀에 동일 적용한 post-hoc 설계

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

### 10.2 결과

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

최악 설정에서도 최소 ΔAUROC는 `+0.05304`로 material gate `+0.02`의 2.65배였다. 이 결과는 본 논문의 중심 결론이 block length나 stochastic draw count의 한 고정값에서만 생겼다는 가능성이 평가한 설정 범위에서는 관찰되지 않았음을 보여 준다.


## 11. 결과 해석과 한계

TEP의 일곱 event-level gain fault와 네 channel-level consensus cell은 서로 다른 결과 단위다. 전자는 제어 입력 전체의 추가 이득이며, 후자는 특정 채널을 조건부로 대치한 뒤 나타나는 탐지력 감소다. event gain이 있어도 imputer 품질 또는 구조 합의를 통과하지 못하면 채널 결론을 내리지 않는다. F26/XMV4의 제외는 이 구분을 보여 준다.

224-cell BH 결과는 동일 TEP test run 분포에 대한 분석이다. run별 두 구조와 다섯 seed의 평균 효과를 사용한 단측 sign-flip 검정은 귀무가설 아래 run-cluster 부호 대칭을 가정한다. 공유 모델과 데이터가 만드는 의존성도 남는다. BH 보정을 모든 의존 구조에서의 오류율 보장으로 해석하거나, 5개 모델 seed를 5개 독립 데이터셋으로 해석하지 않는다. seed·architecture·민감도 설정의 표결을 독립으로 곱한 결합 확률은 정식 유의확률로 사용하지 않는다.

민감도 결과는 선택된 네 셀에 대한 post-hoc 강건성 분석이다. Git 이력에서 규칙의 사전등록을 입증할 수 없으며, 9개 설정의 반복 성공은 독립적인 9개 연구가 아니다. 다른 대치 모델·운전 조건까지 강건성을 보장하지 않는다.

정상 데이터 기반 대치는 관찰적 분석이다. 다른 채널도 fault의 영향을 받는 경우 대치값에 이상 정보가 잔존할 수 있고, 조건부 모델 오차가 효과에 영향을 줄 수 있다. 품질 gate와 FPR 제한은 이를 점검하지만 교란의 제거를 증명하지 않는다. 선택된 채널을 물리적 고장 원인 또는 최적 제어 대상으로 해석하지 않는다.

HAI에서는 AUROC·AUPRC의 3-seed t 구간은 양수지만 eTaF1 구간은 0을 포함한다. 직접 공격된 제어 채널의 utility는 공격받지 않은 제어 이력의 일반적 가치와 구별해야 한다. TEP와 HAI의 수치도 서로 다른 사건 정의와 평가 조건에서 얻었으므로 효과크기를 단순 비교하지 않는다.

## 12. 재현성과 연구 무결성

2026-09-21 재검증은 원 증거 커밋 bc6166f792e3faceb060a50de6219dddca393fd6에서 필요한 표·manifest 25개를 임시 폴더에 읽어 기존 validator를 실행했다. 파일별 SHA-256과 validator 해시는 outputs/closeout_validation/ARCHIVE_PROVENANCE.json에 있다. 총 18개 검증이 통과했다. 무효화된 HAI v1에서는 무효화 상태만 확인하며 성능 수치를 사용하지 않았다.

별도로 200,000회 sign-flip 기반 BH 표를 재계산해 보존된 224행 전체와 비교했고 수치가 일치했다. 민감도 분석은 현재 보존된 fault/run 표에서 2,000회 bootstrap을 재실행했으며 4/4 consensus PASS가 일치했다. HAI 전역 지표의 t 구간도 원 seed별 지표로 재계산했다.

이 절의 재현은 결과 표에서 분석을 다시 수행하는 재현이다. 모델 재학습, 원시 telemetry 전처리, 기존 G3 신뢰구간의 새 추정은 포함하지 않는다. HAI overlap 제거와 역할 분류는 보존 manifest를 점검한 것이다. 재실행 명령과 상세 범위는 CHUM_CLOSEOUT_KO.md를 따른다.

## 13. 결론

평가한 산업 시계열에서 제어 이력의 이득은 사건과 채널에 따라 달랐다. CHUM은 이 차이를 모델 용량, 정상 조건부 대치의 품질, 오경보 변화, 반복 실행 및 모델 구조 합의를 함께 고려해 측정했다. TEP에서는 네 fault–channel 셀이 두 구조와 민감도 설정에서 유지됐고, HAI에서는 제한적인 외부 지지를 얻었다. 이는 제어 이력의 예측 유용성에 대한 근거이며 인과 또는 root-cause 식별의 근거는 아니다. 향후 확장은 공격받지 않은 제어 이력과 새로운 운전 조건에서 같은 평가 절차가 유지되는지 검증하는 것이다.

## 참고문헌

[1] Tonekaboni, S., Joshi, S., Campbell, K., Duvenaud, D. K., and Goldenberg, A. (2020). What went wrong and when? Instance-wise feature importance for time-series black-box models. NeurIPS 33. https://proceedings.neurips.cc/paper/2020/hash/08fa43588c2571ade19bc0fa5936e028-Abstract.html

[2] Bento, J., Saleiro, P., Cruz, A. F., Figueiredo, M. A. T., and Bizarro, P. (2021). TimeSHAP: Explaining Recurrent Models through Sequence Perturbations. KDD. https://arxiv.org/abs/2012.00073

[3] Hase, P., Xie, H., and Bansal, M. (2021). The Out-of-Distribution Problem in Explainability and Search Methods for Feature Importance Explanations. NeurIPS 34. https://proceedings.neurips.cc/paper/2021/hash/1def1713ebf17722cbe300cfc1c88558-Abstract.html

[4] Sundararajan, M., Taly, A., and Yan, Q. (2017). Axiomatic Attribution for Deep Networks. ICML, PMLR 70:3319–3328. https://proceedings.mlr.press/v70/sundararajan17a.html

[5] Reinartz, C., Kulahci, M., and Ravn, O. (2021). An extended Tennessee Eastman simulation dataset for fault-detection and decision support systems. Computers & Chemical Engineering, 149, 107281. https://doi.org/10.1016/j.compchemeng.2021.107281

[6] AIRI Institute. FDDBenchmark, reinartz_tep distribution. https://github.com/AIRI-Institute/fddbenchmark/blob/main/README.md (접근: 2026-09-21).

[7] ICS Dataset. HIL-based Augmented ICS (HAI) Security Dataset, release 21.03. https://github.com/icsdataset/hai (접근: 2026-09-21).

[8] eTaPR maintainers. eTaPR evaluation implementation. https://github.com/wshw4ng/eTaPR (접근: 2026-09-21; 기존 프로젝트의 saurf4ng/eTaPR 주소가 이 주소로 연결됨).

문헌 [1–4]의 서지 및 요약은 원 출판처 또는 저자 arXiv 초록으로 확인했다. TEP의 upstream 연구 [5]와 실제 사용한 FDDBenchmark 배포 계층 [6]을 구분한다. 본 연구의 2,800 runs·52개 변수는 로컬 배포본 감사 결과이며 upstream 전체 데이터의 모든 모드·변수를 사용했다는 뜻이 아니다. 배포본의 세부 변환 이력이 완전히 입증된 것은 아니다. HAI와 평가 구현의 출처는 [7, 8]이다. 기존 실행에 사용된 upstream commit까지 고정한 원시 데이터 재현은 이번 재검증 범위 밖이다.
