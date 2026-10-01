"""Consolidated research entrypoints must work outside the checkout CWD."""
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("script", [
    "run_architecture_gate_g2.py", "analyze_final_gate_exp1.py",
    "final_gate_capacity_runs.py", "g0_oracle_applicability.py",
    "run_chum_training_budget.py", "run_chum_window_extension.py",
])
def test_research_entrypoint_help_from_other_directory(script, tmp_path):
    pytest.importorskip("torch")
    result = subprocess.run(
        [sys.executable, str(ROOT / "experiments" / script), "--help"],
        cwd=tmp_path, capture_output=True, text=True, timeout=45,
    )
    assert result.returncode == 0, result.stderr
    assert "usage:" in result.stdout


def test_active_physical_paths_stay_inside_consolidated_root():
    seen = 0
    for path in (ROOT / "configs").glob("*.yaml"):
        cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(cfg, dict):
            continue
        for key, value in cfg.get("paths", {}).items():
            if not isinstance(value, str):
                continue
            assert "PhysicalAI_mini" not in value, (path, key, value)
            if value.startswith("physical_ai/"):
                seen += 1
                # Do not resolve junctions: their temporary backing store is external.
                assert ".." not in Path(value).parts
                assert (ROOT / value).is_absolute()
    assert seen >= 10
