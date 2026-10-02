# CHUM 마무리 현황

## 2026-10-02 갱신: 졸업 준비 우선순위

현재 상태는 **후속 결과를 반영한 교수 검토용 논문 초안 준비**입니다. 학교·학과 요건, 심사·제출 마감, 지도교수 승인 여부는 미확인입니다. 현재 자료만으로 졸업 가능 여부를 판정하지 않습니다.

### 이번에 끝낸 작업

- 1B window 20/60/120 비교 18/18 작업 완료를 확인했습니다. 18개 RESULT·METRICS·학습 기록과 실행 소스 8개의 해시를 대조했으며 결과는 [검토 JSON](../outputs/chum_window_extension_20261001/REVIEW_20261002.json)에 있습니다. 재학습·원시 score 재계산·새 신뢰구간 추정은 하지 않았습니다.
- [논문 초안](CHUM_THESIS_DRAFT_KO.md) §9.5에 1A의 부정 결과와 1B의 F1 6행을 추가하고 [Word](CHUM_THESIS_DRAFT_KO.docx)를 재생성했습니다. 현재 13장·13표이며 기존 12개 표의 수치는 유지했습니다. [검토용 PDF](CHUM_THESIS_DRAFT_KO.pdf) 16페이지를 생성하고 전체 페이지 미리보기·텍스트 경계·페이지 번호를 확인했습니다. 절의 목록 번호와 보충표 배치도 교정했습니다.
- 일곱 GAIN fault에 관한 표현을 전체 fault로 오해하지 않도록 한정했습니다. 기존 TEP test의 반복 관찰, 단일 seed, Transformer F0=F0-C, AP와 정확도의 차이 및 미탐지 한계를 공개했습니다.
- 검증 보고서의 과도한 재계산 표현을 실제 범위로 교정했습니다. 기존 18개 검증을 새로 실행한 것은 아닙니다. 과거 ARCHIVE_PROVENANCE의 hash는 당시 실행 증거로 보존합니다.
- 저장소·main 통합 및 데이터 이전은 완료됐습니다. 작업 공간에는 프로젝트 하나만 남았고 데이터·DB·가중치는 로컬에 유지합니다.

### 다음 세 단계와 완료 기준

| 순서 | 작업 | 완료 기준 | 아직 필요한 입력 |
| --- | --- | --- | --- |
| 1 | 교수 검토로 제목·핵심 주장·추가 실험 범위를 확정 | 수정할 주장과 필수 보완 비교가 구체적으로 정해짐. 추가 실험이 필요 없다는 확인도 가능 | 교수 의견, 학교 필수 실적 요건 |
| 2 | 원고와 제출 문서를 완성 | 본문-표-근거 대응, 용어·참고문헌·목차·페이지 확인, 학교 양식 적용 후 Word/PDF 렌더링 검수 | 학교 양식, 저자·학과·지도교수 표기, 제출 마감 |
| 3 | 심사 발표를 준비 | 승인된 주장과 한계에 맞는 슬라이드·발표문·예상 질의응답, 정해진 시간 내 리허설 | 심사 날짜, 발표 시간, 심사 요구사항 |

검토용 최신 요약은 [교수 브리프](../outputs/PROFESSOR_BRIEF_KO.md)에 있습니다. 현 자료에서 새 탐지 모델 개발이 졸업의 필수 조건이라는 근거는 확인되지 않았습니다. 새 gate·foundation model·운영 LoRA 추가 학습은 후속 연구 후보로 분리할 것을 제안합니다. 추가 실험은 교수 검토에서 확인된 특정 주장 결손과 종료 기준에 맞춰 한정합니다.

### 문서 편집·검증 경계

현재 편집 기준은 `experiments/build_thesis_draft.py`와 그 입력 기획서입니다. 생성기가 논문 Markdown·Word를 함께 생성하므로 생성된 Markdown만 수정한 뒤 재생성하지 않습니다. 이번 문서 확인은 원본 CSV와 보충표 값 일치·기존 표 보존·문자 인코딩·Word 구조 및 검토용 PDF의 16페이지 렌더링을 포함합니다. 보충표는 12페이지 한 장에 배치했습니다. [문서 QA](../outputs/closeout_validation/DOCUMENT_QA.json)에 범위를 기록했습니다. **학교 양식 적용과 그 이후 제출용 PDF의 최종 검수는 아직 남아 있습니다.**

## 2026-09-21 기록
작성일: 2026-09-21

## 현재 결과

기존 필수 실험 결과를 재검증하고 국문 논문 초안과 Word 문서를 작성했다. 현재 상태는 **검증 완료·교수 검토용 초안 작성 완료**다. 학위논문 최종 제출 완료로 표시하지 않는다.

- 논문 원문: [CHUM_THESIS_DRAFT_KO.md](CHUM_THESIS_DRAFT_KO.md)
- 편집 가능한 문서: [CHUM_THESIS_DRAFT_KO.docx](CHUM_THESIS_DRAFT_KO.docx)
- 기존 연구 기획서: [CHUM_RESEARCH_PROPOSAL_KO.md](CHUM_RESEARCH_PROPOSAL_KO.md)
- 검증 결과: [FINAL_EVIDENCE_VALIDATION.md](../outputs/closeout_validation/FINAL_EVIDENCE_VALIDATION.md)
- 추가 강건성 재검증: [ROBUSTNESS_VALIDATION.json](../outputs/closeout_validation/ROBUSTNESS_VALIDATION.json)

## 완료한 작업

| 항목 | 확인 결과 |
|---|---|
| 기존 원자료 복구·검증 | Git bc6166f의 표·manifest 25개를 임시 폴더에서 읽고 18/18 검사 PASS |
| 후보 분모와 다중비교 | 원시 308셀, 품질 gate 통과 224셀; 200,000회 permutation 재계산 표 전체 일치 |
| BH 보정 결과 | q=0.05에서 42/224, q=0.10에서 48/224; locked 4셀 모두 통과 |
| 민감도 | 2,000회 bootstrap 재실행; 4/4 consensus PASS; 8개 architecture–cell의 9/9 설정 유지 |
| HAI 불확실성 | AUROC·AUPRC 구간 양수; eTaF1의 95% t 구간은 0 포함 |
| GRU 공개 | 기존 3구조 비교표와 다른 대치 조건에 따른 consensus 제외 사유를 초안에 포함 |
| IG 불일치 | TCN/F4의 XMV6 대 XMV10 불일치를 포함; IG를 순간 gradient라고 부르지 않도록 수정 |
| 사전등록 경계 | 민감도는 post-hoc 규칙으로 표시, 기존 Git 감사 문서 유지 |
| 집필 | 초록, 서론, 관련 연구, 방법, 데이터, 결과, 논의, 결론과 참고문헌; 12개 표 |
| 전달 형식 | 한글 Markdown과 편집 가능한 Word 생성 |

## 검증 범위

기존 validator는 결과 표의 중복·완료 여부, 효과·FPR·판정 등을 점검한다. G3의 원래 run CI는 보존된 요약값을 읽으며 이번에 다시 추정하지 않았다. HAI 데이터 중복 제거·역할 분류도 manifest 확인이다. 모델 재학습 또는 원시 telemetry 전체 전처리를 이번에 다시 실행하지 않았다.

민감도 CI와 BH permutation은 별도 스크립트에서 새로 계산했다. 학습 seed, architecture, 9개 민감도 설정을 독립 연구 반복으로 간주하지 않는다. 문서의 수치는 기존 결론을 유지하며 새로운 인과·root-cause 주장을 추가하지 않았다.

## 재실행

Thesis-Orchestrator 폴더에서 실행한다. 기존 분석용 Python 환경의 numpy, pandas, scipy, pyyaml, tabulate와 문서용 python-docx가 필요하다.

```powershell
python experiments/revalidate_archived_evidence.py
python experiments/revalidate_closeout_robustness.py
python experiments/build_thesis_draft.py
```

Git 이력에 원 증거 커밋이 있어야 한다. 분석 산출물은 outputs/closeout_validation에 기록한다. 초안 생성기는 기존 기획서의 방법·결과를 재사용하므로 초안의 장기 수정 시 생성기와 원문 중 어느 것을 편집 기준으로 삼을지 먼저 정해야 한다. 현재 생성기를 다시 실행하면 초안 Markdown·Word가 재생성된다.

## 최종 제출까지 남는 일

1. 지도교수의 제목·주장 범위·논문 구성 검토를 반영한다. 승인 여부를 추정하지 않았다.
2. 학교 양식, 저자·학과·지도교수 표기, 요구 분량을 받아 제출 형식을 적용한다. 현재 Word는 편집용이며 페이지별 인쇄 렌더링 검수는 아직 하지 않았다.
3. 최종 형식 적용 뒤 목차·표 번호·참고문헌 양식·페이지 나눔을 확인하고 제출 PDF를 만든다.

기존 PPT 제작 명세와 업체 전달 패키지는 보존했다. 실제 발표 슬라이드 제작 또는 외부 발송은 이번 작업에 포함하지 않았다. 추가 seed나 비공격 제어 채널을 가진 새 데이터셋은 기존 연구 범위를 확장하는 선택 작업이다.
