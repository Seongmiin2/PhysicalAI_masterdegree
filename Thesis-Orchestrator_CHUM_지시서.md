# Thesis-Orchestrator (CHUM) 작업 지시서

대상 저장소: `Seongmiin2/Thesis-Orchestrator`
목적: 교수 면담 전, CHUM의 **다중비교 방어선을 세우고 음성 결과를 공개**한다.
작성일: 2026-08-25

---

## 0. 이 작업의 성격

CHUM은 실험 증거가 가장 많이 쌓인 후보다. 그런데 **교수님과 리뷰어의 첫 질문에 답할 자료가 지금 저장소에 없다.**

> "전체 후보 cell이 몇 개였고, 그중 4개가 남은 건가?"

이 질문에 답하지 못하면 390 tasks도 2,000회 부트스트랩도 방어가 안 된다. 새 실험은 거의 필요 없다. **이미 계산된 것을 복원하고 정직하게 배치하는 작업**이다.

---

## 작업 1. G3 후보 cell 전수 복원 + 분모 확정 【최우선】

### 문제

커밋 `87bdb24` "Consolidate research evidence and remove generated artifacts"로 G3 단계 산출물이 저장소에서 제거되었다. 현재 남은 것은 이미 **선택이 끝난 4개 cell**에 대한 민감도 결과뿐이다.

```
outputs/architecture_chum_g3/
├ normal_xmv_loo_imputer_weights.npy    ← 남아 있음
├ normal_xmv_loo_residual_bank.npy      ← 남아 있음
└ (cell-level 결과 CSV 없음)            ← 복원 대상
```

즉 **선택 과정 자체를 저장소만으로 재현할 수 없다.**

### 작업

1. `experiments/analyze_architecture_chum_g3.py`를 재실행하거나 로컬 백업에서 cell-level 결과를 복원한다.
2. 다음 수치를 확정한다.

```
전체 후보 cell 수 = (평가 대상 fault 수) × (대치 가능 channel 수)

TEP 기준 확인 사항:
- XMV 총 11개
- XMV12 부재
- XMV5, XMV9 상수 → 대치 대상에서 제외되는가?
- 실제 imputer quality gate를 통과한 channel은 몇 개인가?
- fault는 28개 전부 평가했는가, 아니면 사전 필터가 있었는가?
```

**추정하지 말고 코드와 산출물에서 확정한다.** 이 숫자가 논문 표에 들어간다.

3. gate 탈락 channel 수를 별도 보고한다. `현재 한계`에 이미 "imputer gate 탈락 channel에는 결론을 못 낸다"고 적혀 있으므로, **몇 개가 탈락했는지**가 필요하다.

### 산출물

```
outputs/architecture_chum_g3/G3_CELL_RESULTS.csv        # 전수
outputs/architecture_chum_g3/G3_SELECTION_MANIFEST.json # 분모·필터·탈락 내역
```

---

## 작업 2. BH-FDR 적용 【최우선】

### 작업

작업 1의 전수 결과에 Benjamini–Hochberg FDR을 적용한다.

- 각 cell의 p-value 산출 근거를 명시 (run-level bootstrap 기반 / permutation 등)
- `q = 0.05`, `q = 0.10` 두 수준에서 생존 cell 보고
- 기존 4개 locked cell이 BH 통과 집합에 **포함되는지** 확인

### 함께 제시할 결합 논증

BH만으로 부족할 수 있으므로, **3중 필터의 결합 확률**을 별도로 계산한다.

```
locked cell 4개는 다음을 동시에 통과했다:
  ① 5/5 seed 동일 방향
  ② TCN·Transformer 2개 architecture 합의
  ③ 9/9 sensitivity 설정 (block 5/10/20 × draws 1/3/10)

귀무가설 하에서 하나의 cell이 ①②③을 모두 통과할 확률을 계산하고,
후보 분모를 곱한 기대 위양성 수를 제시한다.
```

이 수치가 작으면 다중비교 공격이 **오히려 강점으로 전환된다.** 단, 계산 가정(독립성 등)을 명시하고 보수적으로 잡는다.

### 산출물

```
outputs/chum_multiplicity/BH_FDR_RESULTS.csv
outputs/chum_multiplicity/MULTIPLICITY_REPORT.md
```

---

## 작업 3. GRU 결과 공개 【최우선】

### 문제

문서는 "GRU·TCN·Transformer 3개 architecture"라고 쓰는데, locked decision은 **TCN·Transformer 2개 합의**다. GRU가 왜 빠졌는지 현재 문서에 없다.

이건 교수님이 반드시 묻는다. 그리고 **숨기면 cherry-picking, 밝히면 정직성 근거**가 되는 전형적인 항목이다.

### 작업

1. GRU의 event-level / channel-level 결과를 표에 **포함**한다. PhysicalAI 단계에서 이미 GRU F0/F1/F0-C를 돌렸으므로 숫자는 존재한다.
2. consensus 기준에서 제외한 이유를 명시한다. 다음 중 어느 것인지 정확히 쓴다.
   - 애초에 consensus 설계가 TCN·Transformer로 사전 결정되었다 → 그 시점의 커밋 근거 제시
   - GRU가 다른 결론을 냈다 → **음성 결과로 명시 보고**
   - GRU는 다른 실험 단계 소속이라 조건이 다르다 → 조건 차이 명시
3. GRU가 4개 locked cell에 대해 같은 방향인지 아닌지를 표로 제시한다.

### 문장 예시

> GRU는 [n]개 cell에서 동일 방향, [m]개에서 불일치했다. consensus를 TCN·Transformer로 한정한 것은 [사유]이며, GRU 결과는 부록 표 X에 전량 수록했다.

### 산출물

```
outputs/architecture_consensus/THREE_ARCH_COMPARISON.csv
deliverables/CHUM_RESEARCH_PROPOSAL_KO.md  # GRU 절 추가
```

---

## 작업 4. 360 vs 390 불일치 해소 【1시간】

### 문제

문서는 sensitivity를 **390 tasks**로 기술한다. 그런데 실제 산출물은:

```
outputs/chum_primary_sensitivity/SENSITIVITY_CELL_RESULTS.csv
→ 361줄 (헤더 1 + 데이터 360)

360 = 4 cells × 2 architectures × 5 seeds × 9 settings
```

**30 tasks 차이가 설명되지 않는다.**

### 작업

- 390의 구성을 분해해 문서에 명시한다 (core 360 + 추가 30이 무엇인지)
- 추가 30이 negative control / 사전점검 / 실패 재실행 중 무엇인지 밝힌다
- 문서와 CSV 중 어느 쪽이 정본인지 확정하고 나머지를 맞춘다

숫자 하나가 안 맞으면 나머지 수치 전체의 신뢰가 떨어진다. **면담 전에 반드시 정리한다.**

---

## 작업 5. Preregistration 시점 감사 【1시간】

### 문제

`SENSITIVITY_DECISION.json`의 임계값이 결과를 본 **뒤에** 정해졌다면 garden of forking paths다.

```json
"material_delta_auroc": 0.02,
"fpr_guardrail": 0.005,
"positive_seeds": 4,
"required_positive_settings": 9
```

### 작업

```bash
# 판정 규칙 커밋 시점 vs 실험 실행 커밋 시점 비교
git log --follow --format="%H %ai %s" -- outputs/chum_primary_sensitivity/SENSITIVITY_DECISION.json
git log --format="%H %ai %s" -- outputs/chum_primary_sensitivity/SENSITIVITY_RUN_RESULTS.csv
```

- 규칙이 결과보다 **먼저** 커밋됨 → 사전등록으로 주장 가능. 해시를 문서에 기록
- 그렇지 않음 → **"post-hoc이지만 전 cell에 동일 기준을 적용했다"** 로 정직하게 기술

후자가 약점이 되지는 않는다. **거짓 사전등록 주장이 훨씬 큰 약점이다.**

### 산출물

```
docs/PREREGISTRATION_AUDIT.md
```

---

## 작업 6. HAI 증거 강도 구분 【1시간】

### 문제

HAI 효과크기가 TEP와 자릿수가 다르다.

```
TEP  ΔAUROC  0.0530 ~ 0.2770
HAI  ΔAUROC  +0.0187,  AUPRC +0.0306,  eTaF1 +0.0267  (3 seeds)
```

HAI를 TEP와 동급 증거로 배치하면 공격받는다.

### 작업

- HAI 지표에 **CI를 명시**한다
- 본문 표현을 통일한다: TEP = "확립", HAI = **"제한적 외부 지지"**
- 초록·결론에서 두 증거의 강도 차이가 드러나게 문장을 수정한다

---

## 작업 7. IG 불일치 1건 분석 【30분】

locked primary cell 8개 중 7개에서 IG가 일치했다. **틀린 1개가 어느 cell이고 왜 갈렸는지** 분석이 필요하다. 리뷰어는 항상 그 1개를 묻는다.

`outputs/`의 IG attribution 결과(880 rows)에서 해당 cell을 특정하고, 한 문단으로 해석을 쓴다.

---

## 완료 기준

- [ ] 전체 후보 cell 분모가 **숫자로** 확정됨
- [ ] BH-FDR 결과표 + 3중 필터 결합 확률
- [ ] GRU 결과가 표에 포함되고 제외 사유가 명시됨
- [ ] 390 vs 360 구성이 문서와 일치
- [ ] preregistration 시점이 git 근거로 판정됨
- [ ] TEP/HAI 증거 강도가 본문에서 구분됨
- [ ] IG 불일치 1건 특정 및 해석

---

## 금지 사항

- 분모를 추정치로 쓰기 (반드시 산출물 기반)
- GRU 결과 누락
- 사전등록 여부를 확인 없이 주장
- HAI를 TEP와 동일 강도로 서술
- BH 통과 실패 cell을 조용히 제외 — 실패했다면 **그 사실을 보고**
