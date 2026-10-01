# CHUM 마무리 현황

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
