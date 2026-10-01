# CHUM: 도메인 간 방법론 검토와 적용 논의안

검토일: 2026-10-01. 상태: 문헌 조사와 실험 설계 제안. 아래 제안 모델은 구현·평가·채택 완료 상태가 아니다.

## 1. 연구 질문과 판단

지금 가장 적합한 질문은 “제어 문맥을 추가하면 평균적으로 좋아지는가”에서 한 단계 나아간 **“어떤 문맥은 이상을 드러내고 어떤 문맥은 이상을 설명해 가리는가, 이를 정상 학습 자료만으로 구별할 수 있는가”**다. 이는 이 문서의 연구 가설이며 이미 입증된 사실이 아니다.

이전 운영 LoRA의 정확도 개선은 로그 형식 적응이다. 단일 실행·두 행동에서 얻은 100%를 논문 탐지 성능이나 자체 모델의 일반 지능으로 해석하지 않는다. 운영 모델과 논문 탐지 모델을 각각의 평가 문제로 관리한다.

현재 논문 기반은 F0(sensor only), F1(sensor+control), F0-C(capacity matched), 조건부 대치, 오경보 제약, 사건별 평가다. 1A 학습 연장은 seed47에서 F1 AUROC를 개선하지 못했다. 1B window 비교는 진행 중이다. 근거는 `outputs/chum_harness_20261001/TRAINING_BUDGET_REVIEW.json`, `state/CHUM_EXPERIMENT_ROADMAP_KO.md`, `outputs/chum_window_extension_20261001/LIVE_STATUS.json`이다. 완료 전 성능을 추정하지 않는다.

최신 방법이라는 이유만으로 채택하지 않는다. **문제 적합성, 가장 가까운 선행연구, 필요한 정답·가정, 실패 가능성, 계산비, 반증 실험**을 기준으로 고른다. 아래 SOTA 언급은 원 논문의 해당 벤치마크 주장에 한정하며 CHUM에서 검증됐다는 뜻이 아니다. 조사 범위는 대표 1차 문헌의 표적 검토이며 완전한 체계적 문헌고찰은 아니다.

## 2. 후보 방법론 비교

### A. 선택적 문맥 사용 — RAG와 멀티모달 학습에서 전이

[Adaptive-RAG, NAACL 2024](https://aclanthology.org/2024.naacl-long.389/)는 질문 복잡도에 따라 검색 전략을 선택한다. [Self-RAG, ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/file/25f7be9694d7b32d5cc670927b8091e1-Paper-Conference.pdf)는 검색 필요성과 검색·생성 결과 평가를 학습한다. [Predictive Dynamic Fusion, ICML 2024](https://proceedings.mlr.press/v235/cao24c.html)는 단일 모달리티와 결합의 신뢰도 관계를 이용해 동적으로 융합한다.

CHUM 전이안은 작은 gate가 센서·제어의 과거만 보고 F0/F1 활용 비중을 정하는 것이다. 독립 정상 구간에서 두 모델의 손실 차이를 학습 표적으로 삼는다. 제어입력 누락·고정·시간 지연 여부와 상대적 예측 이득을 분리한다. 원 논문의 방법을 그대로 재현한 모델이 아니라, 해당 원리를 이식한 후보임을 명시해야 한다.

장점은 기존 전문가를 유지하면서 저비용으로 검증할 수 있다는 점이다. 최대 위험은 정상 예측오차를 줄이는 문맥이 고장 잔차도 줄일 수 있다는 것이다. gate와 confidence fusion 자체는 이미 알려져 있어 신규성이 아니다. “센서 표현에 attention을 추가했다”는 수준이면 논문 기여가 약하다. 두 전문가를 항상 계산하면 라우팅해도 계산 절감은 없으므로 비용 주장은 별도 측정한다.

**권고: 첫 비교군으로 사용. 이를 바로 최종 신규 방법으로 확정하지 않는다.**

### B. 조건부 대조와 문맥 효용의 이탈 — 통계·유전체 OOD에서 전이

[Model-X knockoffs, JRSSB 2018](https://academic.oup.com/jrsssb/article/80/3/551/7048447)는 변수 의존관계를 보존하는 대조 변수를 이용한다. [Conditional Feature Importance revisited, 2025 최초·2026 개정 preprint](https://arxiv.org/abs/2501.17520)는 조건부 중요도 추정·검정의 효율과 강건성을 다룬다. [Likelihood Ratios for OOD Detection, NeurIPS 2019](https://proceedings.neurips.cc/paper/2019/hash/1e79596878b2320cac26dd792a6c51c9-Abstract.html)는 유전체·영상에서 배경 통계에 교란되는 단일 likelihood를 대조 모델과 비교한다.

가져올 원리는 “입력을 없앤 결과”보다 **현실적인 대조 문맥과 관측 문맥의 차이**를 보는 것이다. 원문 likelihood ratio와 CHUM의 손실 차이는 같은 통계량이 아니다. 현재 모델이 점예측만 출력한다면 손실 차이를 likelihood ratio 또는 상호정보량이라고 부르지 않는다.

기존 CHUM은 주로 사건 후 문맥의 기여도를 감사했다. 새 가설은 정상 상태에서 얻은 문맥 효용의 기준 분포를 만들고, 운영 중 그 효용 패턴이 무너지는지도 탐지하는 것이다. 잔차가 작은데 센서–제어 관계가 비정상인 경우를 찾을 가능성이 있다. 반대로 sampler가 부정확하면 대치 인공물을 탐지하는 모델이 될 수 있다.

knockoff의 교환성·FDR, CPI의 i.i.d. 및 nuisance estimation 조건은 겹치는 시계열 창에 자동 적용되지 않는다. block sampling만 추가했다고 이론적 보장이 생기지 않는다. 제어는 센서 상태에 반응하므로 관측 조건부 대치를 물리적 제어 개입이나 인과효과라고 주장하지 않는다.

**권고: 기존 CHUM을 탐지 방법으로 발전시키는 핵심 가설 후보. A보다 온라인 대치 비용이 크지만 질문 적합성이 높다.**

### C. 문맥으로 인한 표현 소실 방지 — 영상·멀티모달 표현학습에서 전이

[A Closer Look at Multimodal Representation Collapse, ICML 2025](https://proceedings.mlr.press/v267/chaudhuri25a.html)는 잡음·유용 정보와 표현 rank 병목을 분석한다. [Rank-targeted Fusion, WACV 2026](https://openaccess.thecvf.com/content/WACV2026/html/Kim_Countering_Multi-modal_Representation_Collapse_through_Rank-targeted_Fusion_WACV_2026_paper.html)는 보완 특징을 선택하는 결합을 다룬다.

CHUM에서는 센서/제어별 표현의 effective rank, 입력 제거 민감도, frozen feature probe를 먼저 측정한다. F1이 제어정보를 학습하지 못한다는 증거가 있으면 별도 인코더와 센서 표현을 보존하는 residual fusion을 비교한다. 보조손실·인코더·gate를 한꺼번에 추가하지 않는다.

표현 rank와 attention map은 정보 활용의 진단 단서이지 탐지 효용의 정답이 아니다. 새 구조는 파라미터·학습량을 맞춘 F0-C와 비교한다.

**권고: 표현 소실 진단이 양성일 때만 진행하는 후속 구조 후보. 현재 무조건 추가할 근거는 없다.**

### D. 정상 오경보 보정과 판단 보류 — 통계·의료 의사결정에서 전이

[Conformal Risk Control, ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/file/f3549ef9b5ff520a7e41ff3cc306ab2b-Paper-Conference.pdf)는 교환가능성 등 가정 아래 단조 bounded loss의 기대위험을 보정한다. [DtACI, JMLR 2024](https://www.jmlr.org/papers/volume25/22-1218/22-1218.pdf)는 분포 변화에 대응해 온라인 prediction set을 조절한다.

CHUM에서는 새로운 결합 점수도 정상 calibration 구간에서 다시 임계값을 정한다. 정상 자료만으로 미탐률을 보장할 수 없다. 시계열 의존성·운전점 변화 아래서는 이론 가정을 따로 확인한다. 고장 구간을 온라인 calibration에 무조건 편입하면 고장을 새 정상으로 흡수할 수 있어 초기에는 고정 calibration을 우선한다.

운영 모델에는 [Learning to Defer, ICML 2020](https://proceedings.mlr.press/v119/mozannar20b.html)의 “틀린 자동 결정의 비용과 전문가 검토 비용을 함께 평가한다”는 원리가 더 직접적이다. 현재 사람 정답 자료가 충분하지 않으므로 학습형 위임기를 이미 구축했다고 주장하지 않는다. 높은 softmax만으로 자동화를 허용하지 않는다.

**권고: 탐지 방법의 보정·평가 기반으로 채택. 운영 라우터에서는 별도 우선 실험.**

### E. 문맥 조건부 생성모델과 잠재 동역학 — 가까운 직접 경쟁법

[ContextFlow++, UAI 2024](https://proceedings.mlr.press/v244/gudovskiy24a.html)는 generalist/specialist 지식을 분리하고 문맥 조건을 더하는 flow 구조를 제안했으며, 영상·ATM 유지보수·SMAP에서 평가했다. **기본 모델 + 문맥 보정 모델이라는 구조 자체도 새롭지 않다.**

[Conditional flow의 잠재 동역학 제약, UAI 2026](https://proceedings.mlr.press/v337/baumgartner26a.html)은 관측 likelihood보다 정해진 잠재 시간 동역학과의 일치 여부를 검사한다. “예측 가능해도 이상일 수 있다”는 문제에 직접 가까운 후보다. 잠재 동역학을 잘못 정하면 정상 운전 변화도 이상으로 볼 수 있다.

두 논문은 이번에 공식 초록·방법 요지를 검토했다. 재현 코드, 정확한 temporal split, hyperparameter와 metric 구현까지 감사한 상태는 아니다. 채택 전에 이 부분을 검토해야 한다.

**권고: B의 신규성 검토 및 직접 비교 후보. 현재 backbone 전체를 곧바로 flow로 교체하지 않는다.**

### F. 최신 foundation model — 강한 비교군과 표현 제공자

[Chronos-2, 2025 technical report](https://arxiv.org/abs/2510.15821)는 시간/그룹 attention으로 다변량과 공변량 정보를 공유한다. [TimesFM-3, Google Research 2026-08-31 발표](https://research.google/blog/timesfm-3-a-zero-shot-foundation-model-for-multivariate-forecasting/)는 330M 모델에서 시간/변수 attention과 다변량·과거 공변량을 지원한다. 후자는 공식 발표에서 예측 벤치마크 선두를 보고한 것이며, 이 조사에서 독립적인 CHUM 탐지 검증을 확인한 것은 아니다.

첫 foundation 비교군은 과거 공변량을 명시적으로 분리하는 Chronos-2 frozen inference를 제안한다. TimesFM-3는 최신 대안으로 남긴다. 제어입력은 past-only로 제한하고 실제 추론 시 알려지지 않은 미래 제어값을 known-future covariate에 넣지 않는다. 8GB GPU에서의 실행 가능성과 처리량은 작은 배치 실측 전까지 확정하지 않는다. backbone 크기, 사전학습 자원, F0/F1별 실행 비용을 공개한다.

[When Foundation Models are One-Liners, ICLR 2026](https://proceedings.iclr.cc/paper_files/paper/2026/hash/cf70320e93c08b39b1b29a348097a376-Abstract-Conference.html)은 조사한 TSFM 계열의 잔차 기반 탐지가 단순 이동 분산·차분 기준선을 유의하게 능가하지 않는 경우를 보였다. 이 결론을 이후 출시 모델 전체의 실패로 확대하지 않지만, 예측 성능과 탐지 성능을 분리해야 한다는 근거다. [ModernTCN, ICLR 2024](https://github.com/luodhhh/ModernTCN)는 큰 convolution kernel과 분리된 특징/변수 처리를 사용하는 재현 가능한 학습형 비교 후보다. 논문의 원래 탐지 프로토콜과 우리의 causal prediction 프로토콜 차이를 공개해야 한다.

**권고: 사전학습 모델을 새 기여로 포장하지 않고 동일 탐지 프로토콜의 경쟁 비교군으로 사용.**

## 3. 가장 추천하는 연구안

우선 **문맥 효용의 변화로 잔차 탐지의 약점을 보완할 수 있는지**를 검증하고, 선택적 gate를 대조군으로 두는 안을 추천한다. 이유는 기존 CHUM 자산을 직접 활용하면서도 “문맥이 왜/언제 유용한가”를 “그 사실로 탐지를 개선할 수 있는가”에 연결하기 때문이다. 이 판단은 프로젝트 적합성에 관한 제안이며 문헌이 보장한 성능이 아니다.

센서 과거 H_t, 제어 과거 C_t로 현재 센서 Y_t를 예측한다. H_t와 C_t는 t 이전에 관측 가능한 정보만 포함한다. 정상 train으로 f0(H_t), f1(H_t,C_t), 대치기 q(C_t|H_t)를 학습한다. 제어 history의 순차 구조를 보존하며 q에 Y_t 또는 이후 정보를 주지 않는다.

관측 문맥과 대체 문맥의 손실 차이를 다음과 같이 정의한다.

U_t = mean_k loss(Y_t, f1(H_t, C_t^(k))) - loss(Y_t, f1(H_t, C_t)),  C_t^(k) ~ q(.|H_t)

U_t는 Y_t가 도착한 후 계산하는 진단값이다. 사전 라우팅 gate의 입력으로 쓰면 시간적 누출이므로 분리한다. gate 비교군은 과거만으로 두 전문가의 향후 손실 차이를 예측한다. 단일 U_t 값이 크거나 작다는 이유만으로 고장이라고 정하지 않는다. 별도 정상 점수설계 구간에서 센서 잔차·문맥 효용의 결합 분포를 확인한다. 효용 기준분포·스케일·결합 가중치는 이 점수설계 구간에서 정하고, 최종 threshold calibration 구간에서는 고정된 점수의 임계값만 추정한다.

문맥 효용 이탈의 초기 후보는 정상 점수설계 구간의 median과 MAD로 표준화한 U_t의 양측 편차다. 이는 확률이나 유의확률이 아니다. 단측/양측 선택, 작은 MAD의 수치 처리, pooled/운전점 조건부 기준 중 어느 것을 사용할지 개발 단계에서 고정하고 최종 평가 뒤 바꾸지 않는다. 정상 운전점 변화가 pooled 기준에서 고장처럼 보일 수 있으므로 운전점 변화 실험을 따로 둔다.

최소 후보는 센서-only 잔차 경보, 원문맥 잔차 경보, 문맥 효용 이탈 경보다. 결합은 먼저 단순 고정 가중치 및 max로 시작한다. F0 경보를 OR로 추가하면 오경보도 늘기 때문에, 공통 정상 오경보율로 재보정한 뒤 비교한다. 이때 F0보다 항상 나쁘지 않다는 보장은 없다. 복잡한 결합기를 붙이기 전에 단순 결합으로 추가 정보가 있는지 검증한다.

이 안의 창의성 후보는 **예측에 도움이 된 문맥도 탐지에는 해로울 수 있는 상황을 분리하고, 그 실패를 정상 문맥 효용의 변화로 검출하는 것**이다. 조건부 대치·gate·conformal 각각을 최초라고 주장하지 않는다. ContextFlow++, 동적 multimodal fusion, 최신 latent dynamics 방법과 차이가 실제로 남는지 가까운 선행연구 검토와 대조실험으로 확인해야 한다.

## 4. 적용 전에 고정할 최소 실험

| 단계 | 질문과 산출물 | 확대·중단 기준 |
|---|---|---|
| 0. 데이터와 점수 감사 | 사용 이력 있는 test/없는 run 구분, tie-aware 지표 재계산, 목표 시점·센서 출력 동일성 점검 | 미사용 자료가 확인되지 않으면 모든 개선은 탐색 결과로 한정 |
| 1. 저비용 기전 진단 | 동일 window F0/F1에서 정상 예측 이득과 사건 탐지 이득의 부호가 일치하는지, 문맥 손상에 따른 변화 | 예측·탐지 불일치가 관찰되지 않으면 이상 은폐를 주제로 확대하지 않음 |
| 2. 작은 방법 비교 | F0/F1/F0-C, 고정 결합, 과거정보 gate, residual+utility 이탈, 각 구성 제거 | 동일 오경보율에서 고정 결합보다 못하면 복잡한 방법 채택 중단 |
| 3. 근접 경쟁법 | 검토를 마친 ContextFlow++ 계열 또는 PDF식 gate, 단순 차분/분산, ModernTCN 또는 frozen Chronos-2 | 학습/추론 예산과 프로토콜을 맞추고 부정 결과도 유지 |
| 4. 독립 평가 | 새 run/운전 조건, 외부 데이터, TCN·Transformer 반복 | 기존에 본 네 fault/channel 셀만으로 일반화 주장 금지 |

학습·모델 선택·gate 학습·임계값 calibration·최종 평가의 역할을 나눈다. 이미 checkpoint 선택에 쓴 validation을 “새 calibration 자료”로 다시 부르지 않는다. 정상 run별 cross-fitting 또는 별도 정상 holdout이 필요하며, 기존 checkpoint 재사용이 이 독립성을 자동으로 충족하지 않는다. 경계에는 적어도 최대 history 길이의 간격을 두고 필요하면 잔여 상관 길이까지 늘린다.

초기 진단은 완성된 동일 window F0/F1 쌍 하나에서 시작한다. 현재 1B가 수행 중이므로 임의로 중단하거나 다른 backbone 학습을 GPU에 겹쳐 실행하지 않는다. score cache와 sampler가 재사용 가능한지 먼저 확인하고, 없다면 추가 학습 비용을 명시한다. 3 normal folds를 쓰면 F0/F1만으로 최대 6회 학습이 추가될 수 있다. 시간·메모리·forward 수는 실측 전 추정치로 포장하지 않는다.

제안 primary 운영점은 기존 설정과 맞춘 정상 point exceedance 1% 및 3연속 alarm이다. point FPR과 연속 alarm의 event-level false-alarm rate는 다르므로 둘 다 보고한다. 모든 후보는 최종 결합 점수를 정상 calibration에서 다시 보정하고 fault label로 threshold를 고르지 않는다. 사건별 recall, 미탐을 포함한 지연, AUROC/AUPRC, 실제 정상 오경보, 문맥 사용률, latency/메모리를 보고한다. point adjustment로 고장 구간 전체를 맞힌 것처럼 확장하지 않는다.

결과는 run/episode 단위 paired bootstrap으로 비교하고 seed 반복을 독립 사건 수로 더하지 않는다. conditional sampler는 조건부 모멘트·분산·시차/자기상관·범위 위반과 조건부 overlap을 검사한다. 폐루프에서 C가 H로 거의 결정되어 유효 조건부 변동성이 없으면 대치 문맥이 원문맥과 같아 U가 0에 가까워질 수 있다. 이 경우 해당 문맥 효용은 이 설계로 구별하기 어렵다고 보고하며 문맥이 무용하다고 결론내리지 않는다. control delay/stale/missing/block shuffle은 합성 문맥 손상 강건성 실험으로 따로 보고하고 실제 고장 성능과 섞지 않는다.

채택 기준은 사전에 정한 1차 사건 탐지 지표의 독립 run 개선과 정상 오경보 제약 충족이다. 정상 MSE만 좋아지거나, 단순 고정 결합보다 이득이 없거나, sampler 품질이 나쁘거나, 개선 대비 비용이 과도하면 해당 후보를 중단한다. 실용적 최소 효과·추론 예산은 적용 논의에서 수치로 정한 뒤 실행 manifest에 동결한다. 아직 정하지 않은 수치를 사전등록 완료라고 쓰지 않는다.

## 5. 운영용 자체 모델은 별도로 개선

지금 필요한 비교는 rule-only, 작은 구조화 분류기, 현재 LoRA, LoRA+보류 정책이다. 명시적 상태는 규칙이 정확하고 저렴하므로 규칙 결과를 LLM 성능으로 합산하지 않는다. 모호한 사례에서만 모델의 기여를 측정한다. rule label과 human label을 분리하고, 실제 실패·중단·재개 사례와 무작위 감사 표본을 함께 수집한다. 불확실한 사례만 수집하면 선택 편향이 생긴다.

목적함수는 전체 정확도만이 아니라 잘못된 재개·실패 누락 비용, 사람 검토 비용, 자동 처리 비율, 클래스별 오류와 지연이다. 새로운 run 그룹을 평가용으로 남기며 confidence calibration과 임계값 선택도 최종 평가에서 분리한다. 현재 PARTIAL 오분류의 확률이 98.18%였으므로 높은 확률만으로 승인하는 정책은 근거가 없다. RAG는 과거 근거 검색을 지원하지만 과거 모델의 답을 새 정답으로 재학습하는 순환은 막는다.

## 6. 적용 논의에서 결정할 사항

1. 논문 탐지 방법을 먼저 강화할지, 운영용 자체 모델을 먼저 강화할지 구분한다.
2. 논문 쪽 권고는 B의 기전 진단을 먼저 하고 A를 비교군으로 두는 것이다. 빠른 구현만 우선하면 A부터 시작할 수 있으나 신규성은 더 약하다.
3. 최종 실험 전 미사용 데이터 확보 경로, 허용 오경보와 최소 탐지 이득, 계산 예산을 고정한다.
4. C/E는 기전 진단에서 필요성이 확인될 때 확대한다. 여러 기법을 동시에 붙여 원인을 분리할 수 없게 만들지 않는다.

현재 결정은 방법론 검토·제안의 완료이며, 새 대형 실험이나 논문 핵심 주장 변경을 승인받았다는 뜻이 아니다. 기존에 승인된 1B 실행은 계속된다.
