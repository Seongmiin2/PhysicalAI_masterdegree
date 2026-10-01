# PhysicalAI 석사 연구 — CHUM

산업 시계열에서 제어 이력이 언제 탐지에 도움이 되는지 연구하는 단일 프로젝트입니다. 최신 Thesis-Orchestrator와 PhysicalAI 학습 엔진을 통합했습니다.

- **공식 저장소:** https://github.com/Seongmiin2/PhysicalAI_masterdegree
- **작업 브랜치:** `main` 하나
- **현재 로컬 작업 폴더:** `Thesis-Orchestrator` — 실행 중 실험과 IDE 경로를 유지하기 위한 이름이며 별도 프로젝트가 아닙니다.
- **연구 방향과 다음 실험:** [로드맵](state/CHUM_EXPERIMENT_ROADMAP_KO.md), [도메인 간 방법론 검토](deliverables/CHUM_CROSS_DOMAIN_METHODS_20261001_KO.md)
- **실제 진행 상태:** [1B LIVE_STATUS](outputs/chum_window_extension_20261001/LIVE_STATUS.json). 실행 중인 로컬 파일은 Git 배포본에 없을 수 있습니다.
- **운영 하네스:** [사용 방법](docs/CHUM_HARNESS_KO.md), [운영 모델 v2 평가](outputs/chum_ops_training_v2_20261001/IMPROVEMENT_REPORT_KO.md)
- **논문 자료:** [교수 브리프](outputs/PROFESSOR_BRIEF_KO.md), [초안](deliverables/CHUM_THESIS_DRAFT_KO.md). 작성일과 현재 실험 상태를 구분합니다.

## 구조

```text
physical_ai/     # 통합된 학습 엔진(src), 원본 데이터 준비 코드와 테스트
experiments/     # CHUM/TEP/HAI 연구 실행 및 평가
configs/        # 현재 실행 설정; 프로젝트 내부 경로 사용
harness/        # SQLite 작업 기록, 실행 잠금, 근거 검색
providers/      # 운영 모델 인터페이스
outputs/        # 결과와 실행 근거
state/          # 로드맵·판정 기록
deliverables/   # 논문 및 방법론 검토 문서
tests/          # 프로젝트 테스트
```

새 clone에서는 Python 3.11 이상 환경에서 `python -m pip install -e ".[dev,research]"`로 설치합니다. 운영 모델 파인튜닝 의존성은 `configs/requirements-chum-finetune.txt`에 별도로 있습니다. GPU 환경은 `configs/requirements-research-gpu.txt`를 참고합니다. 버전·장치 가용성을 확인하고 설치 환경에 맞게 사용합니다.

```powershell
python -m pytest -q
python -m harness status
python -m harness index
python experiments/run_chum_window_extension.py --config configs/chum_window_extension.yaml --dry-run
```

실제 데이터·모델 가중치·SQLite DB는 Git에서 제외합니다. 데이터 준비 후 `physical_ai/data/`와 `physical_ai/checkpoints/`를 사용합니다. 기존 엔진의 독립 실행 설정은 `physical_ai` 디렉터리에서 사용하는 경로입니다. 다른 clone에 데이터가 자동으로 생겼다고 가정하지 않습니다.

## 통합과 보관

2026-10-01 기준 최신 개발은 Thesis-Orchestrator에 있었지만 PhysicalAI에 학습 엔진과 고유 결과가 있었습니다. 엔진과 고유 문서 7개를 통합하고, 양쪽 Git 이력을 보존합니다. 이전 상태·provider 파일로 최신 구현을 덮어쓰지 않았습니다. [통합 파일 manifest](outputs/REPOSITORY_CONSOLIDATION_20261001.json)를 참고합니다.

DeMo-Med, FAVE-Med, FAVE-RAG, 외부 reference/export checkout과 전체 Git bundle은 작업 공간의 형제 폴더 `C:/Users/FORYOUCOM/Desktop/master_degree_archive_20261001`에 보관합니다. 다른 프로젝트의 미커밋 변경도 유지합니다. 이 프로젝트에서 더 이상 자동 export용 nested 저장소를 만들지 않습니다.

현재 GPU 작업은 이전 PhysicalAI 데이터 파일을 메모리 매핑하고 있습니다. 작업 종료 전에는 데이터를 옮기지 않고 `physical_ai/data`, `physical_ai/checkpoints`의 임시 junction으로 같은 파일을 사용합니다. `experiments/finalize_workspace_consolidation.py --wait`가 실행 잠금 해제 후 데이터를 프로젝트 안으로 옮기고 구 PhysicalAI 폴더를 바깥으로 보관합니다. 진행 상태는 `outputs/harness/WORKSPACE_CONSOLIDATION_STATUS.json`입니다.

통합 전 실행 소스는 `outputs/chum_window_extension_20261001/EXECUTED_SOURCES`에 해시와 함께 보존했습니다. 현재 실행은 메모리에 로드한 원본으로 계속됩니다. 경로가 바뀐 코드로 기존 output에 재개하면 fingerprint 검증이 거부하는 것이 정상이며, 새 실행에는 새 output 디렉터리를 사용합니다.

2026-10-01 통합 `main`을 공식 저장소에 게시하고 기본 브랜치를 `main`으로 변경했습니다. 양쪽 Git 이력을 확인한 뒤 옛 원격 브랜치 `master`, `agent/thesis-final-gate`를 삭제했습니다. 사용자 승인 후 중복 `Seongmiin2/Thesis-Orchestrator` 원격 저장소를 삭제하고 GitHub API의 404 응답을 확인했습니다. 해당 저장소의 모든 브랜치 이력은 공식 `main`과 별도 Git bundle에 보존되어 있습니다. 옛 가상환경과 중복 문서 등 22개 항목은 작업 공간 밖 `PhysicalAI_legacy_assets`에 보관했습니다. 원격 작업 결과는 통합 manifest와 Git remote 상태를 확인합니다.
