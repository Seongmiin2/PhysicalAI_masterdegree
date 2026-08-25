# PhysicalAI / Reinartz 작업 지시서

대상 저장소: `Seongmiin2/PhysicalAI_masterdegree`
목적: CHUM의 **GRU 근거를 공급**하고, 이 단계가 CHUM으로 질문을 좁힌 논리적 전 단계임을 명시한다.
작성일: 2026-08-25
예상 소요: 1시간

---

## 0. 이 작업의 성격

이 저장소는 CHUM 지시서 **작업 3(GRU 결과 공개)의 데이터 출처**다. CHUM 문서는 "GRU·TCN·Transformer 3개 architecture"라고 쓰는데 locked decision은 2개 합의이고, GRU 숫자는 여기 있다.

또한 이 단계는 CHUM의 문제의식이 어디서 나왔는지를 보여준다. **F1이 F0보다 좋다는 결과를 얻고도 인과 주장을 하지 않고 질문을 좁힌 판단** — 이게 교수님께 보여줄 지점이다.

---

## 작업 1. GRU 결과 추출 및 CHUM 연계 【최우선】

### 확보해야 할 수치

문서에 이미 기록된 대표값:

```
F0    AUROC 0.7508   AUPRC 0.8995   delay 51.9
F1    AUROC 0.8196   AUPRC 0.9312   delay 24.6
F0-C  AUROC 0.7493   AUPRC 0.8989
seeds 42–44
```

여기서 **CHUM의 4개 locked cell에 대응하는 GRU 결과**를 뽑아낸다.

| locked cell | GRU가 같은 방향인가 |
|---|---|
| F4 / XMV10 | ? |
| F19 / XMV7 | ? |
| F19 / XMV8 | ? |
| F25 / XMV2 | ? |

### 주의 — 조건 차이를 반드시 기록할 것

GRU 단계는 CHUM과 실험 조건이 다를 수 있다.

```
확인 항목:
- seeds 42–44 (3개) vs CHUM 42–46 (5개)
- 조건부 대치를 적용했는가, zero masking 단계인가
- validation threshold 보정 방식이 동일한가
- imputer quality gate를 통과한 조건인가
```

**조건이 다르면 "GRU가 불일치했다"고 쓸 수 없다.** 조건 차이 때문인지 모델 차이 때문인지 구분되지 않기 때문이다. 이 경우 정직한 서술은 다음과 같다.

> GRU는 [조건 A]에서 평가되었고 TCN·Transformer는 [조건 B]에서 평가되었다.
> 두 조건이 다르므로 GRU를 consensus 기준에 포함하지 않았다.
> GRU 결과는 부록에 원 조건 그대로 수록한다.

### 산출물

```
outputs/gru_baseline/GRU_CELL_RESULTS.csv
outputs/gru_baseline/GRU_CONDITION_MANIFEST.md   # 조건 차이 명세
```

이 두 파일을 Thesis-Orchestrator의 `outputs/architecture_consensus/`로 복사하거나 링크한다.

---

## 작업 2. MIXED_MECHANISM 판정 문서화 【최우선】

### 배경

이 단계의 핵심 판단은 **좋은 결과를 얻고도 인과 주장을 하지 않은 것**이다.

```
F1 이득은 실재 (AUROC +0.0688, delay 절반)
F0-C가 못 따라옴 → 용량 효과로 설명 불가
그러나 효과가 faults 4, 7, 19, 24–26에 집중
정상 미래예측 개선은 작음
→ verdict: MIXED_MECHANISM
```

setpoint, controller error, XMV12, mode, counterfactual trajectory가 없어 강한 기전 주장이 불가능했다. 그래서 **새 모델 발명이 아니라 utility audit으로 질문을 좁혔다.**

### 작업

`docs/REINARTZ_CURRENT_STATUS_AND_NEXT_STAGE.md`에 다음 절을 추가하거나 보강한다.

```markdown
## 이 단계에서 CHUM으로 질문을 좁힌 이유

F0 → F1 이득은 재현되었고 capacity control(F0-C)도 통과했다.
그러나 다음 이유로 **제어 이력의 일반적 기전**을 주장하지 않았다.

1. 효과가 faults 4, 7, 19, 24–26에 집중되어 보편적이지 않았다
2. 정상 구간 미래예측 개선이 작아, "제어가 정상 동역학을 설명한다"는
   해석을 지지하지 못했다
3. setpoint, controller error, XMV12, operating mode,
   counterfactual trajectory가 데이터에 없어 인과 식별이 불가능했다
4. residual decomposition(c = x̂1 − x̂0)의 방법론적 신규성이 약했다

따라서 질문을 다음과 같이 좁혔다.

> (이전) 제어 이력이 fault 탐지를 개선하는가?
> (이후) 어떤 event와 channel에서 추가 정보의 utility가 재현되는가?

이 전환의 결과가 [CHUM](https://github.com/Seongmiin2/Thesis-Orchestrator)이다.
```

---

## 작업 3. 실험 조건 명세 정리 【20분】

CHUM 문서가 이 저장소의 수치를 인용하므로, **재현 가능한 조건 명세**가 필요하다.

문서화할 항목:

```
데이터
- AIRI fddbenchmark Reinartz TEP, 5.6M rows / 54 columns
- 2,800 runs, 28 faults, fault당 100 runs, run당 2,000 samples
- 41 XMEAS, 11 XMV (XMV12 부재, XMV5·9 상수)
- fault onset 600

분할
- run-level 1,792 train / 448 validation / 560 test
- train 정상 구간 1–599로만 StandardScaler fit
- F0/F1 sensor scaler 공유, XMV도 train-normal fit

모델
- GRU hidden 64, 1 layer, 30 epochs, batch 128, Adam lr 0.001, MSE
- F0 [20, 41] → 41
- F1 [20, 52] → 41
- F0-C sensors-only, F1과 파라미터 수 0.6% 이내

평가
- validation-normal score p99 threshold 고정
- MAE/RMSE, AUROC/AUPRC, normal FPR, delay, detected-run ratio
- seeds 42–44
```

특히 **XMV5·9가 상수이고 XMV12가 부재**라는 사실은 CHUM의 후보 cell 분모 계산에 직접 들어간다. 이 수치를 확정해 CHUM 지시서 작업 1로 넘긴다.

---

## 작업 4. 저장소 상태 배너 【10분】

```markdown
> **저장소 상태: 완료된 선행 단계 (2026-08 중순)**
>
> 이 저장소는 제어 이력의 fault 탐지 기여를 검증한 단계이며,
> 결과는 재현되었으나 인과 주장은 하지 않았습니다(MIXED_MECHANISM).
> 후속 연구는 event–channel utility audit으로 질문을 좁힌
> [CHUM](https://github.com/Seongmiin2/Thesis-Orchestrator)입니다.
>
> 이 저장소의 GRU 결과는 CHUM의 3-architecture 비교표에 인용됩니다.
```

---

## 완료 기준

- [ ] 4개 locked cell에 대한 GRU 방향 확인
- [ ] GRU와 CHUM의 **실험 조건 차이가 명시적으로 문서화됨**
- [ ] 조건이 다르면 "불일치" 대신 "조건 상이"로 정확히 기술
- [ ] MIXED_MECHANISM 판정과 질문 축소 논리가 문서화됨
- [ ] XMV 가용 채널 수가 확정되어 CHUM 분모 계산에 전달됨
- [ ] 상태 배너 추가

---

## 금지 사항

- 조건 차이를 확인하지 않고 GRU를 "불일치"로 단정하지 않는다
- F1 이득(0.7508 → 0.8196)을 인과적 발견으로 서술하지 않는다
- 효과가 일부 fault에 집중된다는 사실을 생략하지 않는다
- MIXED_MECHANISM 판정을 약점으로 기술하지 않는다. **과장을 피한 판단이었다**
