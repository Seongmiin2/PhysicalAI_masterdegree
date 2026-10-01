# Physical AI Thesis — CCRDL

> **저장소 상태: 완료된 선행 단계 (2026-08 중순)**
>
> 이 저장소는 제어 이력의 fault 탐지 기여를 검증한 단계이며,
> 결과는 재현되었으나 인과 주장은 하지 않았습니다(`MIXED_MECHANISM`).
> 후속 연구는 event–channel utility audit으로 질문을 좁힌
> [CHUM](https://github.com/Seongmiin2/Thesis-Orchestrator)입니다.
>
> 이 저장소의 GRU 결과는 CHUM의 3-architecture 비교표에 인용됩니다.

Control-conditioned normal dynamics and residual evolution for early anomaly
detection in industrial cyber-physical systems.

## Current milestone

Phase 0 establishes a reproducible project skeleton and a small C-MAPSS sanity
benchmark. Large datasets (Extended TEP, GE-UTK, and N-CMAPSS) are intentionally
not downloaded yet.

## Quick start

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m src.data.download_cmapss
python -m src.data.validate --dataset cmapss
pytest
```

To start metadata services after Docker is installed:

```powershell
Copy-Item .env.example .env
docker compose up -d
```

Research design: `docs/RESEARCH_DESIGN_v1.md` (copy of the supplied source).

## TEP-first recovery pipeline

The active milestone models recovery episodes as:

```text
State + Fault + Recovery Action -> Success / Failure / Unsafe
```

The default baseline generates deterministic synthetic TEP-like episodes; it does
not download the 132.96 GB Extended TEP archive. Telemetry is stored as
Parquet/NPZ, while episode and experiment records are stored in
`db/experiment.db` (SQLite).

```powershell
PowerShell -ExecutionPolicy Bypass -File scripts\setup.ps1
PowerShell -ExecutionPolicy Bypass -File scripts\run_experiment.ps1 -Background
Get-Content logs\runner.log -Wait
```

The background PID is written to `run.pid`. Configure episode count and epochs in
`configs/baseline.yaml` before starting an overnight run.
