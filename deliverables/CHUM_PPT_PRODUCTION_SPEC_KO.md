# CHUM 12장 PPT 정밀 제작 설계서

**용도:** 전문 PPT 제작자/사이트에 그대로 전달하는 production brief  
**발표 대상:** 추현승 교수 및 Superintelligence Laboratory  
**발표 시간:** 10–12분 + 질의응답  
**핵심 원칙:** 설명문을 줄이고 `문제 → 통제 → 증거 → 판정`이 한 번에 보이게 한다.

---

## A. 전체 디자인 시스템

### A.1 캔버스와 그리드

- 화면비: 16:9
- PowerPoint size: `13.333 × 7.5 in`
- safe margin: 좌우 `0.55 in`, 상단 `0.45 in`, 하단 `0.35 in`
- 12-column grid, gutter `0.16 in`
- 모든 slide title baseline: `y=0.48 in`
- 본문 시작: `y=1.35 in`
- source footer: `y=7.10 in`, 7.5–8 pt
- slide number: 우하단 `x=12.65, y=7.08`, 8 pt

### A.2 색상

| 역할 | HEX | 사용 |
| --- | --- | --- |
| Navy | `#17324D` | 제목, 핵심 문장, 테두리 |
| Primary blue | `#2F6BFF` | TCN, PASS, 주 방법 |
| Teal | `#278A78` | Transformer, external support |
| Cyan | `#3AA7B8` | HAI channel, 신뢰 AI 연결 |
| Amber | `#E4A11B` | gate, 한계, 의사결정 요청 |
| Light gray | `#EEF3F8` | 패널 배경, gridline |
| Mid gray | `#C8D5E3` | 연결선, 비활성 요소 |
| Dark text | `#12202F` | 본문 |
| Secondary text | `#5D6B78` | 보조 설명, source |

배경은 전 장 `#FFFFFF`. gradient, 그림자, 3D chart, 장식용 stock image를 사용하지 않는다. PASS를 초록색으로 표시하지 않는다. 본 deck의 PASS는 primary blue, 제한적 support는 amber로 구분한다.

### A.3 글꼴과 크기

- 1순위: `Pretendard`
- 2순위: `Noto Sans KR`
- 영문/숫자도 같은 family 사용
- slide title: 29–32 pt, Bold, Navy
- takeaway subtitle: 15–17 pt, Medium, Secondary gray
- section label: 13–15 pt, Bold
- body: 13–16 pt
- hero number: 30–44 pt, Bold
- chart label: 10–12 pt
- source/footer: 7.5–8 pt
- 한 슬라이드에서 3개 이상의 font size hierarchy를 만들지 않는다.

### A.4 공통 표현 규칙

- 각 장의 제목은 주제가 아니라 **결론 문장**으로 쓴다.
- 본문 bullet은 최대 3개, bullet 하나는 최대 2줄.
- 숫자는 소수 셋째 자리까지, 원 raw 값이 중요한 경우 넷째 자리까지.
- `CHUM`, `F0`, `F1`, `F0-C`, `TEP`, `HAI`, `ΔAUROC`, `FPR` 표기를 전 장 동일하게 유지한다.
- `causal`, `root cause`, `universal`은 주장 금지 영역으로만 사용한다.
- 모든 결과 chart의 0 기준 또는 material gate를 명시한다.
- 결과 장의 source에는 `corrected HAI v2 only`와 commit/checksum 근거를 남긴다.

---

## B. 슬라이드별 제작 명세

## Slide 1 — 표지이자 결론

**목적:** 15초 안에 연구 질문, 방법의 차별점, 현재 상태를 전달한다.  
**제목:** `CHUM: 제어 이력의 ‘실제 정보 유용성’을 감사한다`  
**한 줄 결론:** `4개 핵심 event–channel이 두 architecture와 9개 replacement 설정에서 모두 재현됐다.`

### 배치

| 요소 | x | y | w | h |
| --- | ---: | ---: | ---: | ---: |
| eyebrow `MASTER'S THESIS PROPOSAL` | 0.65 | 0.42 | 4.0 | 0.25 |
| title | 0.65 | 0.85 | 8.0 | 1.25 |
| subtitle | 0.68 | 2.18 | 7.5 | 0.75 |
| hero metric card | 9.15 | 0.82 | 3.45 | 2.30 |
| three evidence chips | 0.68 | 4.62 | 11.9 | 1.10 |
| author/date/status | 0.68 | 6.52 | 7.0 | 0.35 |

### 화면 문구

왼쪽 title 아래:

`Architecture-Robust Auditing of Control-History Utility`  
`for Reliable Industrial Time-Series Anomaly Detection`

오른쪽 hero card:

`4 / 4`  
`locked cells PASS`  
`TCN + Transformer × 9/9 settings`

하단 evidence chips:

- `2 datasets · TEP + HAI 21.03`
- `3 architectures · GRU + TCN + Transformer`
- `18/18 evidence checks · sensitivity PASS`

**시각 지시:** hero card는 amber 얇은 테두리와 매우 옅은 amber 배경. 로고나 공장 사진을 넣지 않는다.  
**발표자 노트:** “제어 변수를 넣으면 좋아진다는 평균 비교가 아니라, 어떤 사건과 채널의 이력이 실제 정보를 제공하는지를 감사했습니다. 논문 집필 전에 필요했던 마지막 민감도 실험까지 통과했습니다.”  
**source footer:** `TEP G3 · HAI corrected v2 · locked sensitivity, 2026-08-23`

---

## Slide 2 — 교수·연구실 적합성

**목적:** 왜 이 연구가 교수님의 최근 연구 흐름 안에 자연스럽게 들어가는지 보여 준다.  
**제목:** `최근 연구의 공통축은 ‘문맥 활용 → 신뢰성 검증 → 시스템 결정’이다`  
**한 줄 결론:** `CHUM은 산업 시계열에서 이 공통축을 검증 가능한 audit protocol로 구현한다.`

### 배치

- 상단 78%: `ppt_assets/06_PROFESSOR_FIT_MAP.png`를 비율 유지해 `x=0.45, y=1.22, w=12.45, h=5.55`에 배치.
- 우하단 작은 source tag만 PPT native text로 덧붙인다.

### 제작 보정

- asset 안의 숫자 `24/21/6`은 연구실 목록의 unique title 수임을 유지한다.
- 세 패널 위에 작은 기간 label `2024–2026 official lab list`를 9 pt로 추가한다.
- 제목 기반 분류이므로 “논문 비중” 대신 “unique titles”라고 쓴다.

**발표자 노트:** “연구실의 응용축은 네트워크와 의료로 나뉘지만 방법론적으로는 시간 문맥, 조건 변화에 대한 신뢰성, 다중 모델 검증, 그리고 운용 의사결정 연결이 반복됩니다. CHUM을 공정 전용 모델이 아니라 trustworthy context-utilization audit로 제안하는 이유입니다.”  
**source footer:** `Superintelligence Lab official publications/projects; SKKU Pure; 82 registrations, 65 unique titles`

---

## Slide 3 — 배경과 문제의식

**목적:** “입력에 넣었다”와 “정보를 사용했다”의 차이를 시각적으로 고정한다.  
**제목:** `Control history를 입력했다고, 모델이 유용하게 쓴 것은 아니다`  
**한 줄 결론:** `평균 성능 향상에는 네 가지 대안 설명이 섞여 있다.`

### 배치

| 요소 | x | y | w | h |
| --- | ---: | ---: | ---: | ---: |
| 왼쪽 input diagram | 0.65 | 1.55 | 4.15 | 4.75 |
| 중앙 `≠` | 5.05 | 2.95 | 0.8 | 0.8 |
| 오른쪽 four confounders | 6.05 | 1.45 | 6.55 | 4.95 |
| bottom RQ band | 0.65 | 6.45 | 11.95 | 0.55 |

### 왼쪽 native diagram

`Sensor history`와 `Control history` 두 개의 얇은 time strip이 `F1 detector` box로 들어간다. output은 `anomaly score ↑`. 그 아래 작은 회색 문구:

`Observed: F1 > F0`

### 오른쪽 2×2 confounder cards

1. `Capacity` — 입력 증가와 함께 parameter도 증가
2. `Architecture` — 특정 inductive bias에서만 효과
3. `Perturbation OOD` — zero masking이 비현실적 충격 생성
4. `False alarms` — 정상 구간 FPR 상승이 gain처럼 보임

### bottom band 정확 문구

`RQ. 어떤 event–channel의 과거 control history가 이 네 요인을 통제한 뒤에도 추가 정보를 제공하는가?`

**발표자 노트:** “여기서 문제는 성능 향상 자체가 아닙니다. 그 숫자가 control information인지, 단순 용량인지, 특정 구조인지, 또는 masking 충격인지 분리되지 않는다는 점입니다.”  
**source footer:** `Problem formulation derived from capacity control and OOD perturbation literature`

---

## Slide 4 — 연구 공백과 기여 위치

**목적:** 기존 XAI와 무엇이 같고 무엇이 다른지 과장 없이 정리한다.  
**제목:** `새 attribution 알고리즘이 아니라, 판정 가능한 audit protocol이 필요하다`  
**한 줄 결론:** `CHUM의 신규성은 이미 알려진 통제를 산업 이상 탐지의 하나의 decision gate로 결합한 데 있다.`

### 배치

왼쪽 `x=0.65, y=1.55, w=5.55, h=4.85`: 세 층의 prior-work stack.

- `Time-series attribution` — FIT · TimeSHAP
- `Distribution-aware perturbation` — OOD explainability · learned perturbation
- `Model multiplicity` — architecture/Rashomon importance

오른쪽 `x=6.55, y=1.45, w=6.05, h=5.10`: CHUM contribution card.

### 오른쪽 card 정확 문구

`CHUM =`  
`capacity control`  
`+ normal conditional replacement`  
`+ validation-only calibration`  
`+ FPR guardrail`  
`+ hierarchical uncertainty`  
`+ cross-architecture consensus`

카드 하단 amber label:

`Output: event × control channel utility map`

**발표자 노트:** “조건부 perturbation 자체를 새 원리라고 주장하지 않습니다. 이 연구의 신규성은 산업 탐지에서 용량·분포·오경보·불확실성·구조 합의를 동시에 만족해야 결론을 내리는 통합 protocol입니다.”  
**source footer:** `FIT; TimeSHAP; Hase et al. 2021; Enguehard 2023; Donnelly et al. 2023`

---

## Slide 5 — 방법론

**목적:** CHUM의 전체 계산 흐름을 한 장에 고정한다.  
**제목:** `다섯 단계가 대안 설명을 순서대로 제거한다`  
**한 줄 결론:** `입력 통제 → 정상분포 대치 → 조건별 보정 → 사건별 효과 → 합의 판정`

### 배치

- `ppt_assets/01_CHUM_METHOD_PIPELINE.png`를 `x=0.25, y=1.05, w=12.85, h=6.15`에 full-bleed에 가깝게 사용.
- asset의 자체 제목이 PPT 제목과 중복되므로 제작 시 PNG 상단 13%를 crop하거나, PPT title을 제거하고 asset title을 그대로 쓴다. **둘 중 하나만 남긴다.**

### 필수 강조

- ② `normal train-only`에 작은 amber underline.
- ③ `test label 미사용`에 작은 lock icon은 가능하되 outline형 단색만 사용.
- 최종 산출물의 `utility map`을 15 pt Bold.

**발표자 노트:** “F0/F1/F0-C로 용량을 분리하고, 정상 데이터만으로 해당 control을 대치합니다. 각 조건의 validation score로 threshold를 다시 보정하고, event effect와 FPR을 계산한 뒤 두 architecture의 합의가 있어야 최종 셀로 채택합니다.”  
**source footer:** `CHUM implementation: configs/architecture_chum_g3.yaml`

---

## Slide 6 — Dataset과 전처리

**목적:** 데이터 규모보다 split과 leakage control이 확실하다는 인상을 준다.  
**제목:** `TEP에서 방법을 잠그고, HAI의 HIL attack으로 외부 지지를 확인했다`  
**한 줄 결론:** `두 환경 모두 split-before-window, train-only scaling, validation-only threshold를 사용한다.`

### 배치

- `ppt_assets/02_DATASET_AND_SPLIT_PROTOCOL.png`를 `x=0.30, y=1.08, w=12.75, h=6.05`로 배치.
- asset의 자체 제목 중복 처리 방식은 Slide 5와 동일.

### PPT native callout

HAI card의 overlap 줄 오른쪽에 amber pill:

`43,202 train rows removed`

하단 한계 tag:

`HAI = external support, not universal replication`

**발표자 노트:** “TEP는 2,800 run을 run 단위로 나눈 주 실험이고, HAI는 132만여 row의 HIL 환경입니다. HAI에서는 test와 exact telemetry가 겹친 training row를 제거했고 point role과 attack target을 먼저 검증했습니다.”  
**source footer:** `reinartz_split_manifest.csv; HAI preparation/role/attack-target manifests; corrected v2 only`

---

## Slide 7 — 모델링과 공정한 비교

**목적:** ‘더 큰 모델이라 좋아진 것’과 ‘특정 구조만의 현상’ 반론을 즉시 차단한다.  
**제목:** `모델 크기와 inductive bias를 각각 통제했다`  
**한 줄 결론:** `F1은 두 대조군을 모두 넘어야 하고, 핵심 결론은 TCN과 Transformer가 합의해야 한다.`

### 배치

| 요소 | x | y | w | h |
| --- | ---: | ---: | ---: | ---: |
| F0/F1/F0-C diagram | 0.65 | 1.55 | 5.25 | 4.95 |
| architecture table | 6.25 | 1.48 | 6.35 | 3.95 |
| decision formula band | 6.25 | 5.68 | 6.35 | 0.82 |

### 왼쪽 diagram

세 개 horizontal lane:

- `F0` — 41 sensor histories → detector
- `F1` — 41 sensor + 11 control histories → detector
- `F0-C` — 41 sensor histories → width-adjusted detector

F1과 F0-C 사이에 bracket `capacity matched`.

### 오른쪽 table

| 구조 | F0 | F1 | F0-C | 역할 |
| --- | ---: | ---: | ---: | --- |
| GRU | 23,209 | 25,321 | 25,473 | 최초 현상 |
| TCN | 8,425 | 9,481 | 9,526 | convolutional bias |
| Transformer | 20,489 | 20,841 | 20,489 | attention bias |
| HAI model | 26,909 | 30,941 | 31,021 | external support |

### formula band

`Control-history evidence = (F1 > F0) ∩ (F1 > F0-C) ∩ architecture consensus`

**발표자 노트:** “F0-C가 핵심입니다. sensor-only이면서 F1과 비슷한 용량을 갖게 해 input 정보와 parameter 증가를 분리했습니다. 그 다음 다른 temporal bias에서도 같은 사건과 채널이 남는지 봤습니다.”  
**source footer:** `Final Gate Exp.1; Architecture Gate G2; HAI external corrected v2`

---

## Slide 8 — 실험·판정 구조

**목적:** 많은 실험을 나열하지 않고 각 반론과 대응 검증이 1:1임을 보여 준다.  
**제목:** `각 실험은 하나의 반론을 제거하도록 설계했다`  
**한 줄 결론:** `결론은 큰 숫자 하나가 아니라 여섯 개 독립 guardrail의 교집합이다.`

### 배치

- `ppt_assets/07_EVIDENCE_SCORECARD.png`를 `x=0.30, y=1.05, w=12.75, h=6.08`에 배치.
- asset 상단 제목 중복 시 PPT 제목을 제거하고 asset을 전체 사용.

### 제작 보정

- 첫 5개 PASS는 primary blue, 마지막 `SUPPORT`는 amber 유지.
- 오른쪽 evidence 문구는 최소 11 pt가 되도록 배치한다.
- 하단 claim boundary를 지우지 않는다.

**발표자 노트:** “실험 수를 늘린 목적은 benchmark 경쟁이 아니라 alternative explanation을 하나씩 제거하는 것입니다. 외부 환경만은 PASS가 아니라 SUPPORT로 분리해 claim strength도 차등화했습니다.”  
**source footer:** `18/18 raw-evidence checks PASS; invalid HAI v1 excluded`

---

## Slide 9 — TEP 핵심 결과

**목적:** 본 논문의 가장 강한 정량 근거를 제시한다.  
**제목:** `네 개 channel mapping이 TCN과 Transformer에서 모두 재현됐다`  
**한 줄 결론:** `효과는 material gate의 2.65–14.5배이며, 모든 셀에서 5/5 seed와 run CI가 지지한다.`

### 배치

- `ppt_assets/03_TEP_ARCHITECTURE_CONSENSUS.png`를 `x=0.30, y=1.02, w=12.78, h=6.12`.
- 그래프 상단 우측에 작은 proof strip을 PPT native로 추가:
  `5/5 seeds` · `CI low > 0` · `|ΔFPR| ≤ 0.00125`

### 발표 중 강조 순서

1. F25/XMV2의 큰 양 구조 효과
2. 가장 작은 F19/XMV8도 +0.02 gate보다 충분히 큼
3. 두 구조의 정확한 크기는 달라도 channel identity와 방향이 같음
4. F26/XMV4는 imputer quality 미달로 제외했다는 보수성

**발표자 노트:** “파란색과 teal의 높이가 완전히 같아야 하는 것이 아니라, 동일한 channel에서 material loss가 반복되는지가 핵심입니다. 가장 작은 셀도 약 +0.053이고, 모든 run CI 하한이 0보다 큽니다.”  
**source footer:** `RECOMPUTED_G3_PRIMARY_CELLS.csv · 5 seeds · 20 test runs/fault`

---

## Slide 10 — HAI 외부 검증

**목적:** 시뮬레이션 전용 현상이 아니라는 제한적 외부 근거를 보여 준다.  
**제목:** `HAI corrected v2에서도 전역 gain과 5개 targeted channel support가 반복됐다`  
**한 줄 결론:** `F1은 두 대조군보다 높았고, 직접 공격 셀의 conditional score loss는 모두 3/3 seed에서 positive였다.`

### 배치

- `ppt_assets/05_HAI_EXTERNAL_SUPPORT.png`를 `x=0.25, y=1.02, w=12.85, h=6.15`.
- 오른쪽 chart 위에 amber outline label `EXTERNAL SUPPORT`.
- 왼쪽 F1−F0-C 세 막대에만 아주 옅은 amber halo 가능.

### 필수 한계 문구

하단 8.5 pt:

`직접 공격 control을 포함하므로 공격받지 않은 control context의 보편적 유용성을 뜻하지 않음.`

**발표자 노트:** “HAI에서는 corrected v2만 사용했습니다. 전역 AUROC·AUPRC·eTaF1이 두 대조군보다 모두 높고, targeted cell 다섯 개가 3/3 seed에서 같은 방향입니다. 다만 이 결과는 제한적 external support로만 표현합니다.”  
**source footer:** `Corrected HAI v2; feature-order-bug v1 invalidated and excluded`

---

## Slide 11 — 최종 민감도 검증

**목적:** 논문 집필 직전 마지막 공격점이 사라졌음을 보여 준다.  
**제목:** `결론은 block length와 stochastic draw count에 의존하지 않았다`  
**한 줄 결론:** `4/4 cells × 2 architectures가 9/9 설정에서 positive·material·CI·FPR 기준을 모두 통과했다.`

### 배치

- `ppt_assets/04_PRIMARY_SENSITIVITY_RANGES.png`를 `x=0.30, y=1.02, w=12.78, h=6.10`.
- 우상단 hero badge:
  `390 tasks`  
  `no retraining`
- 하단 우측 작은 조건 matrix:
  `block {5,10,20} × draws {1,3,10}`

### 해석 지시

- 점은 median, 선은 9개 설정의 min–max 범위라고 legend 한 줄 추가.
- 범위가 매우 좁다는 사실을 강조하되, stochastic draw가 항상 영향이 없다는 보편 문장으로 확장하지 않는다.
- material gate `+0.02` 선을 반드시 유지한다.

**발표자 노트:** “이 실험은 새 모델을 학습한 것이 아니라 기존 checkpoint에서 중앙 방법의 두 고정값을 공격한 것입니다. 최악 조건의 최소 ΔAUROC도 +0.053이어서, 네 셀 모두 사전 기준을 넉넉히 통과했습니다.”  
**source footer:** `SENSITIVITY_DECISION.json · 2,000 paired hierarchical bootstrap repeats`

---

## Slide 12 — 기여·한계·결정 요청

**목적:** 과장 없이 연구를 닫고 교수님에게 필요한 결정을 명확히 요청한다.  
**제목:** `필수 실험은 끝났다 — 이제 claim을 잠그고 집필을 시작한다`  
**한 줄 결론:** `제안: CHUM audit protocol을 주 기여로 확정하고 causal/root-cause 확장은 후속 연구로 분리한다.`

### 배치

| 요소 | x | y | w | h |
| --- | ---: | ---: | ---: | ---: |
| contributions card | 0.65 | 1.45 | 3.75 | 4.55 |
| claim boundary card | 4.78 | 1.45 | 3.75 | 4.55 |
| future/decision card | 8.90 | 1.45 | 3.75 | 4.55 |
| bottom decision band | 0.65 | 6.28 | 12.0 | 0.68 |

### 정확 문구

**Contribution**

- `event–channel context utility formulation`
- `capacity + distribution + FPR + uncertainty controls`
- `architecture & sensitivity robust evidence`
- `TEP primary + HAI external support`

**Claim boundary**

- `predictive utility ✓`
- `physical causality ✕`
- `root-cause identification ✕`
- `universal industrial transfer ✕`

**Future fit**

- `Network AI Foundation Model context audit`
- `NWDAF / 6G inference confidence`
- `drift-aware online CHUM`
- `digital-twin causal extension`

**bottom decision band**

`결정 요청 ① RQ 확정  ② CHUM을 주 기여로 확정  ③ 현재 증거로 본문 집필 시작`

**발표자 노트:** “현재 주장 범위 안에서는 필수 실험이 끝났습니다. 교수님께 요청드리는 결정은 연구질문과 기여를 이 형태로 잠그고 집필을 시작하는 것입니다. 더 강한 인과나 보편 일반화는 별도 후속 연구로 남기겠습니다.”  
**source footer:** `Status: MANUSCRIPT-READY · mandatory experiment backlog: none`

---

## C. 제작자에게 제공할 asset 매핑

| Slide | asset | 사용 방식 |
| ---: | --- | --- |
| 2 | `ppt_assets/06_PROFESSOR_FIT_MAP.png` | full-width fit map |
| 5 | `ppt_assets/01_CHUM_METHOD_PIPELINE.png` | method pipeline |
| 6 | `ppt_assets/02_DATASET_AND_SPLIT_PROTOCOL.png` | dataset/split cards |
| 8 | `ppt_assets/07_EVIDENCE_SCORECARD.png` | rebuttal-to-evidence matrix |
| 9 | `ppt_assets/03_TEP_ARCHITECTURE_CONSENSUS.png` | primary result chart |
| 10 | `ppt_assets/05_HAI_EXTERNAL_SUPPORT.png` | external support chart |
| 11 | `ppt_assets/04_PRIMARY_SENSITIVITY_RANGES.png` | sensitivity range chart |

PNG를 screenshot처럼 작은 frame 안에 넣지 말고, slide layout의 주 시각물로 사용한다. raster를 stretch하지 말고 비율을 유지한다. 제작자가 chart를 PowerPoint native vector로 다시 그릴 경우 숫자, 축, gate, source와 색상 mapping을 바꾸지 않는다.

---

## D. 제작 완료 QA checklist

- [ ] 정확히 12장인가
- [ ] 모든 제목이 결론 문장인가
- [ ] 한 장에 핵심 메시지가 하나인가
- [ ] TCN은 blue, Transformer는 teal로 일관되는가
- [ ] PASS와 SUPPORT가 구분되는가
- [ ] Slide 9에 material gate `+0.02`가 보이는가
- [ ] Slide 10에 corrected v2 및 external-support 한계가 보이는가
- [ ] Slide 11에 `390 tasks`, `no retraining`, 3×3 grid가 보이는가
- [ ] Slide 12에 causal/root-cause 금지 범위가 남아 있는가
- [ ] 모든 결과 장에 source footer가 있는가
- [ ] 100% 확대에서 본문 13 pt 이상, source 7.5 pt 이상인가
- [ ] 장식용 이미지·gradient·3D·과도한 icon이 없는가
- [ ] 모든 숫자가 기획서 및 CSV와 일치하는가

---

## E. 전문 제작 사이트에 붙여 넣을 한 문장 주문

> 아래 12장 명세와 제공 PNG 자산을 그대로 사용해, 흰 배경·navy/blue/teal 중심의 기술 연구 제안 deck을 제작해 주세요. 설명문보다 방법 pipeline, dataset/split, 비교 통제, 정량 chart, strict decision gate가 먼저 보이게 하고, 숫자·claim boundary·PASS/SUPPORT 구분은 절대 수정하지 마세요.
