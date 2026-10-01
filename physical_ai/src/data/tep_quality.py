from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from src.data.tep import XMEAS, XMV


def create_reports(frame: pd.DataFrame, report: Path, variable_csv: Path, run_csv: Path) -> None:
    numeric = XMEAS + XMV
    values = frame[numeric].replace([np.inf, -np.inf], np.nan)
    variable = values.describe().T
    variable["missing"] = values.isna().sum()
    variable["inf"] = np.isinf(frame[numeric].to_numpy()).sum(axis=0)
    variable["constant"] = values.nunique(dropna=True).le(1)
    runs = frame.groupby("run_id").agg(rows=("sample_idx", "size"), operating_mode=("operating_mode", "first"), fault_id=("fault_id", "first"), fault_onset=("fault_onset", "first"), time_start=("time", "min"), time_end=("time", "max"))
    variable_csv.parent.mkdir(parents=True, exist_ok=True)
    run_csv.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    variable.to_csv(variable_csv)
    runs.to_csv(run_csv)
    intervals = frame.groupby("run_id")["time"].apply(lambda series: series.sort_values().diff().dropna().median())
    text = f"""# TEP Pilot Data Quality

- Rows: {len(frame)}
- Runs: {frame['run_id'].nunique()}
- Missing values: {int(values.isna().sum().sum())}
- NaN/Inf: {int(values.isna().sum().sum())}/{int(np.isinf(frame[numeric].to_numpy()).sum())}
- Constant variables: {', '.join(variable.index[variable['constant']]) or 'none'}
- Median sampling interval by run: {intervals.to_dict()}
- Fault distribution: {frame.groupby('run_id')['fault_id'].first().value_counts().sort_index().to_dict()}
- Operating-mode distribution: {frame.groupby('run_id')['operating_mode'].first().value_counts().sort_index().to_dict()}
- Fault onset values: {frame.groupby('run_id')['fault_onset'].first().to_dict()}

Variable and run details are in `{variable_csv}` and `{run_csv}`.
"""
    report.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    create_reports(pd.read_parquet(args.input), Path("reports/tep_data_quality.md"), Path("artifacts/tables/tep_variable_summary.csv"), Path("artifacts/tables/tep_run_summary.csv"))


if __name__ == "__main__":
    main()
