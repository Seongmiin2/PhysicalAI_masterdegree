# Physical AI Thesis — CCRDL

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
