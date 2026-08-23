# 추현승 교수·Superintelligence Lab 최근 연구 프로파일

## 조사 범위와 판독 원칙

- 공식 연구실 publication 목록 2024–2026: 총 **82개 등록**, 제목 기준 **65편**을 수집했다.
- 공식 연구실 ongoing project 목록을 별도 수집했다.
- 아래 분류는 제목 키워드를 이용한 재현 가능한 규칙 기반 코딩이며, 인용지수 분석이나 논문의 질 평가가 아니다.
- 연구실 페이지의 Journal/Conference 분류와 실제 출판 유형이 일부 다를 수 있어 원래 목록 유형을 그대로 보존했다.

## 연도별 등록 수

| 연도 | 등록 수 |
| ---: | ---: |
| 2024 | 28 |
| 2025 | 20 |
| 2026 | 17 |

## 1차 주제 분포

| 주제 | 등록 수 |
| --- | ---: |
| 6G·네트워크 AI | 24 |
| 의료 AI | 21 |
| 기타 응용 AI | 13 |
| 신뢰 AI·RAG·에이전트 | 6 |
| 산업·시계열 이상 진단 | 1 |

## 반복 방법론 신호

| 방법론 신호 | 제목 출현 수 |
| --- | ---: |
| 전처리·표현학습 | 19 |
| 시계열 | 17 |
| 응용 딥러닝 | 17 |
| 그래프·강화학습 | 12 |
| 생성형 AI·LLM | 5 |
| 멀티태스크·멀티모달 | 5 |
| 신뢰성·강건성 | 4 |
| Transformer·하이브리드 | 4 |

## CHUM과의 직접 적합성 해석

1. **산업·네트워크 시계열:** traffic, mobility, resource 상태처럼 시간 문맥을 예측과 운용 의사결정에 연결하는 연구가 반복된다.
2. **신뢰성과 비교 설계:** architecture benchmark, domain robustness, evidence quality처럼 단일 모델 최고점보다 결과의 안정성과 근거를 분리해 확인하는 흐름이 있다.
3. **AI-native control 연결:** 예측값을 handover·resource allocation·network analytics로 이어 실제 시스템 안정성이나 비용으로 평가하는 프로젝트가 진행 중이다.
4. **의료 AI의 외부 일반화:** 다중 데이터셋·다중 backbone·cross-dataset 검증이 반복돼, CHUM의 2개 데이터 환경·3개 architecture·보수적 gate와 방법론적 궁합이 좋다.

따라서 CHUM은 ‘산업 이상 탐지의 새 분류기’보다 **신뢰 가능한 context-utilization audit**로 제안하는 편이 연구실의 최근 방법론 취향과 더 직접적으로 맞는다.

## 데이터 파일

- `PROFESSOR_PUBLICATION_MATRIX_2024_2026.csv`: 제목·저자·게재처·주제·방법론 태그·원문 링크
- `PROFESSOR_PUBLICATION_MATRIX_2024_2026_UNIQUE.csv`: Journal/Conference 목록 간 중복 제목을 제거한 분석용 표
- `LAB_PROJECT_MATRIX.csv`: 진행 프로젝트·기간·주관기관·원문 링크

## 공식 출처

- http://monet.skku.edu/main/
- http://monet.skku.edu/main/bbs/board.php?bo_table=public1&sca=2026
- http://monet.skku.edu/main/bbs/board.php?bo_table=public2&sca=2026
- http://monet.skku.edu/main/bbs/board.php?bo_table=projects
- https://pure.skku.edu/en/persons/hyunseung-choo/
