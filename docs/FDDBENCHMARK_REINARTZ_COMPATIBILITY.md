# FDDBenchmark `reinartz_tep` Compatibility Assessment

## 1. 조사 목적

이 문서는 AIRI-Institute FDDBenchmark의 전처리된 `reinartz_tep`가 다음 최소
pilot에 적합한지 검증한다.

- F0: past XMEAS → future XMEAS
- F1: past XMEAS + past XMV → future XMEAS

모델 학습은 수행하지 않았다.

## 2. Dataset source

- Benchmark repository: <https://github.com/AIRI-Institute/fddbenchmark>
- 조사한 repository commit: `a536b027e69983d197469a642f57f120c3c6c6c3`
- Repository license: MIT (코드 라이선스이며 데이터 재배포 라이선스와 동일하다고 단정하지 않음)
- FDDBenchmark 설명의 upstream: Reinartz, Kulahci, Ravn (2021), Extended TEP
- FDDBenchmark README의 source link: <https://web.mit.edu/braatzgroup/links.html>
- 실제 archive URL은 loader 코드에서 확인:
  `https://industrial-makarov.obs.ru-moscow-1.hc.sbercloud.ru/reinartz_tep.zip`
- ZIP 크기: `2,013,615,713` bytes
- 서버 checksum: 제공되지 않음. HTTP ETag는 multipart 형태라 MD5로 해석하지 않음.
- 검증: Content-Length 일치, ZIP 전체 CRC `testzip() = None`.

## 3. Data lineage

직접 확인한 loader 흐름은 다음과 같다.

```text
SberCloud reinartz_tep.zip
  -> ZIP extraction
  -> dataset.csv / labels.csv / train_mask.csv / test_mask.csv
  -> pandas read_csv(index_col=[run_id, sample])
```

실제 ZIP에는 문서에 드러나지 않은 `labeled_train_mask.csv`도 포함된다.
FDDBenchmark 저장소에는 이 archive를 생성한 preprocessing script가 없다. 따라서 raw
Reinartz HDF5에서 CSV를 생성한 구체적인 feature 제거, run 선택, shuffle 알고리즘은
**UNKNOWN**이다. 공개 loader는 다운로드·압축해제·CSV 로딩만 한다.

## 4. 다운로드 파일

데이터는 공식 DTU 경로와 분리해 다음 위치에 저장했다.

```text
data/external/fddbenchmark/reinartz_tep.zip
data/external/fddbenchmark/reinartz_tep/
```

다운로드 전에 C: 여유 공간 약 899 GB를 확인했다. 서버는 byte range를 지원하며
`.partial`로 재개 가능하게 받은 후 검증 성공 시 최종 파일명으로 이동했다. TLS 검증은
끄지 않았다.

## 5. 실제 file structure

| File | Rows | Columns | Size (bytes) |
|---|---:|---:|---:|
| dataset.csv | 5,600,000 | 54 | 5,247,567,494 |
| labels.csv | 5,600,000 | 3 | 98,918,321 |
| train_mask.csv | 5,600,000 | 3 | 96,256,425 |
| test_mask.csv | 5,600,000 | 3 | 96,256,424 |
| labeled_train_mask.csv | 5,600,000 | 3 | 96,256,433 |

모든 파일은 `(run_id, sample)` key에 대해 5,600,000행이 정렬·정합된다.

## 6. Feature structure

`dataset.csv`는 index 2개와 telemetry feature 52개를 가진다.

- `run_id`
- `sample`
- `xmeas_1` ... `xmeas_41` (41개)
- `xmv_1` ... `xmv_11` (11개)

모든 telemetry column은 CSV에서 `float64`로 읽히며 missing value는 0개다.
상수 feature는 `xmv_5 = 1.0`, `xmv_9 = 1.0` 두 개다. 원시 물리 단위 규모의 값이며
archive에서 사전 normalization된 흔적은 보이지 않지만, preprocessing 생성 코드가 없어
“전혀 변환되지 않았다”고 확정할 수는 없다.

전체 정확 통계는 `reinartz_feature_inventory.csv`에 기록했다.

## 7. XMEAS/XMV mapping

- `xmeas_1..41` → `XMEAS_01..41`, role `STATE`: **CONFIRMED by source names**
- `xmv_1..11` → `XMV_01..11`, role `ACTION_CANDIDATE`: **CONFIRMED by source names**
- `run_id` → role `RUN_ID`
- `sample` → role `TIME`은 순서 index 의미로 **LIKELY**; 물리 시간 단위는 CSV에 없음
- label/mask는 telemetry feature와 별도 파일이므로 모델 입력에서 제외 가능

## 8. Missing/removed variables

예상 canonical 53개 중 `XMV_12`가 없다. 정확히 어떤 원본 물리 변수가 왜 제외되었는지는
FDDBenchmark repository와 archive에 metadata/preprocessing code가 없어 **UNKNOWN**이다.
따라서 “원본 XMV12가 제거되었다” 이상으로 물리적 이름이나 이유를 추정하지 않는다.

## 9. Run structure

- Runs: 2,800
- 각 run 길이: 정확히 2,000 samples
- 각 fault ID: 100 runs
- sample index: 1–2,000
- `(run_id, sample)`로 boundary와 시간 순서를 복원할 수 있다.
- CSV loader와 dataloader는 이 MultiIndex를 보존하고 window를 run별로 생성한다.
- 독립적인 all-normal run: 0
- 모든 run은 `label 0 → 해당 fault ID` 구조다.

## 10. Fault/label structure

- Labels: `0`, `1` ... `28`
- Normal samples (`0`): 1,677,200 (29.95%)
- 각 fault: 140,100 samples, 100 runs (각각 약 2.5018%)
- 모든 2,800 run은 하나의 fault class에 대응하며 onset 전에는 label 0이다.
- `Normal`, `IDV1` 등의 문자열이 아니라 정수로 인코딩된다.

`labeled_train_mask`는 각 fault에서 1개 run만 선택하고, 해당 run의 1,401 fault samples를
선택한다. 이 선택 기준을 생성한 코드는 저장소에 없어 **UNKNOWN**이다.

## 11. Train/test mask 구조

- Train: 2,240 runs / 4,480,000 rows
- Test: 560 runs / 1,120,000 rows
- 각 fault별 train 80 runs, test 20 runs
- train/test 양쪽에 걸친 run: 0
- 한 run 내부에서 mask 값이 바뀌는 경우: 0
- row random split이 아니라 run-level, fault-stratified 80/20 split이다.

따라서 기존 test mask는 유지할 수 있다. 그러나 validation mask는 없으므로 training runs
안에서 별도의 **run-level validation split**을 생성해야 한다.

## 12. Fault onset 정보

모든 run에서:

- samples 1–599: label 0
- sample 600부터: 해당 fault ID
- fault onset: sample 600
- fault samples/run: 1,401

즉 run 전체가 fault label인 구조가 아니라 특정 sample 이후 fault인 구조다.

## 13. Operating mode 정보

Operating mode column 또는 별도 metadata는 없다. FDDBenchmark README는 이 자료가
Reinartz TEP 기반이라고만 설명한다. 이 archive가 어떤 operating mode만 포함하는지는
**UNKNOWN**이다.

## 14. 원본 DTU 데이터 대비 preprocessing 차이

직접 확인 가능한 변환:

1. HDF5 hierarchy가 5개 flat CSV로 변환됨.
2. runs가 하나의 CSV로 concatenation되고 `(run_id, sample)`가 부여됨.
3. `XMV_12`에 해당하는 source column이 없음.
4. operating mode, magnitude, completion/stopped status, `idv_init` 등 원본 metadata가 없음.
5. fault profile은 per-sample integer label로 변환되어 모든 run의 onset이 600으로 정렬됨.
6. 2,800 runs = 28 faults × 100 runs로 subset 구성됨.
7. run-level stratified 80/20 train/test mask가 제공됨.

Normalization, run sampling 기준, XMV12 제거 이유, 원본 run ID와 새 run ID의 대응표는
생성 코드가 없으므로 **UNKNOWN**이다. Sampling modification 여부도 CSV만으로 확정할 수 없다.

## 15. Leakage 위험

### 확인 결과

- telemetry에는 future label, fault ID, mask, anomaly score가 포함되지 않음.
- XMV는 sample별 과거 시계열로 존재하므로 window slicing 시 과거 구간만 선택 가능.
- run-level train/test mask라 동일 run split leakage가 없음.
- label과 mask CSV는 feature 입력에서 명시적으로 제외해야 함.

### 남은 위험 및 guard

- Forecast target 시점 또는 미래의 XMV를 F1 input에 포함하면 leakage이므로 금지.
- fault onset 이후 controller response인 XMV가 탐지를 쉽게 할 수 있다. 이는 causal action이
  아니라 closed-loop reaction일 수 있으므로 결과 해석에서 제한을 명시해야 한다.
- validation threshold는 test fault를 사용하지 않고 training runs의 pre-onset normal 구간을
  run-level로 분리해 결정해야 한다.
- `labeled_train_mask`는 fault-label supervised 용도이므로 normal forecasting F0/F1에는 쓰지 않는다.

## 16. F0/F1 실험에 미치는 영향

| Condition | Result |
|---|---|
| A. XMEAS를 STATE로 식별 | PASS: 41/41 |
| B. XMV를 ACTION_CANDIDATE로 식별 | PARTIAL: 11 columns, expected XMV12 absent |
| C. 시간 순서 보존 | PASS: run_id + sample 1..2000 |
| D. run boundary 확인 | PASS: 2,800 runs |
| E. Normal/Fault 구분 | PASS with limitation: pre-onset normal only, no independent normal run |
| F. future leakage 없음 | PASS if labels/masks excluded and past-only windows enforced |

제한된 F0/F1 pilot은 가능하다. F1은 “all 12 canonical XMV”가 아니라 **available 11 XMV**를
사용한 비교로 명시해야 한다. train/validation/test는 run-level로 유지하고, 정상 학습에는
각 training run의 sample 1–599만 사용해야 한다.

## 17. 핵심 질문 답변과 최종 판정

| Question | Answer |
|---|---|
| Q1. 41 XMEAS 모두 존재? | **YES** |
| Q2. 12 XMV 모두 존재? | **NO**, 11개만 존재 |
| Q3. 52 feature에서 제외된 정확한 변수? | canonical `XMV_12` source column 부재; 물리 변수/제거 이유 **UNKNOWN** |
| Q4. XMEAS/XMV 구분 가능? | **YES**, column prefix로 구분 |
| Q5. XMV 시간 순서 보존? | **YES**, `(run_id, sample)` 순서로 보존 |
| Q6. run boundary 복원 가능? | **YES** |
| Q7. run 길이 동일? | **YES**, 모두 2,000 |
| Q8. Normal run 존재? | **NO**, 독립 normal run은 없고 pre-onset normal segment만 존재 |
| Q9. IDV1–28 label 보존? | **YES**, integer 1–28 |
| Q10. Fault onset? | **YES**, 모든 run sample 600 |
| Q11. Operating mode? | **NO/UNKNOWN**, archive에 없음 |
| Q12. Mask 기준? | **run-level stratified 80/20**, row split 아님 |
| Q13. Preprocessing? | flat CSV, 28×100 subset, concatenation, labels/onset/masks 생성, XMV12 부재; 상세 생성 코드 UNKNOWN |
| Q14. Leakage 위험? | 치명적 feature leakage는 확인되지 않음; past-only XMV 및 label/mask 제외 guard 필요 |

### FINAL DECISION: `PARTIALLY_SUITABLE`

시간 구조, run boundary, 41 XMEAS, 11 XMV, onset label, run-level split이 보존되어 제한된
F0/F1 pilot은 가능하다. 그러나 XMV12 부재 원인, operating mode, 독립 normal run,
preprocessing provenance가 없으므로 `SUITABLE_FOR_F0_F1_PILOT`로 판정하기에는 근거가
부족하다.

## 18. 남아 있는 UNKNOWN

- 누락된 XMV12의 정확한 물리 변수와 제거 이유
- archive 생성 preprocessing source code
- 원본 HDF5 run과 `run_id` 대응
- operating mode
- fault magnitude 및 SimulationCompleted/Stopped 상태
- 원본 sampling이 변경되었는지 여부
- `labeled_train_mask` run 선택 기준
- 데이터 archive 자체의 명시적 checksum 및 데이터 라이선스
