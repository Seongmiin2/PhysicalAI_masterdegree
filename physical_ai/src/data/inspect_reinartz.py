from __future__ import annotations

import argparse
import csv
from pathlib import Path

import duckdb
import pandas as pd

from src.data.reinartz import semantic_mapping, validate_headers


def header(path: Path) -> list[str]:
    with path.open(newline="", encoding="utf-8") as stream:
        return next(csv.reader(stream))


def csv_sql(path: Path) -> str:
    escaped = path.resolve().as_posix().replace("'", "''")
    return f"read_csv_auto('{escaped}', header=true, sample_size=-1)"


def inspect(root: Path, output: Path) -> dict:
    files = sorted(root.glob("*.csv"))
    expected = {"dataset.csv", "labels.csv", "train_mask.csv", "test_mask.csv", "labeled_train_mask.csv"}
    if {path.name for path in files} != expected:
        raise ValueError(f"Unexpected file set: {[path.name for path in files]}")
    headers = {path.name: header(path) for path in files}
    validate_headers(headers["dataset.csv"], headers["labels.csv"], headers["train_mask.csv"], headers["test_mask.csv"])
    output.mkdir(parents=True, exist_ok=True)
    connection = duckdb.connect()
    connection.execute("PRAGMA threads=4")
    inventory = []
    descriptions = {
        "dataset.csv": "telemetry indexed by run_id,sample",
        "labels.csv": "per-sample fault class",
        "train_mask.csv": "per-sample training mask",
        "test_mask.csv": "per-sample testing mask",
        "labeled_train_mask.csv": "per-sample labeled-training subset mask",
    }
    row_counts = {}
    for path in files:
        count = connection.execute(f"SELECT count(*) FROM {csv_sql(path)}").fetchone()[0]
        row_counts[path.name] = count
        inventory.append({"file_name": path.name, "relative_path": path.relative_to(root.parent.parent.parent).as_posix(), "size_bytes": path.stat().st_size, "row_count": count, "column_count": len(headers[path.name]), "description": descriptions[path.name]})
    pd.DataFrame(inventory).to_csv(output / "reinartz_file_inventory.csv", index=False)

    feature_columns = headers["dataset.csv"][2:]
    aggregates = []
    for column in feature_columns:
        quoted = f'"{column}"'
        aggregates.extend([f"min({quoted}) AS \"{column}__min\"", f"max({quoted}) AS \"{column}__max\"", f"avg({quoted}) AS \"{column}__mean\"", f"stddev_samp({quoted}) AS \"{column}__std\"", f"count(*)-count({quoted}) AS \"{column}__missing\"", f"count(DISTINCT {quoted}) AS \"{column}__unique\""])
    stats = connection.execute(f"SELECT {','.join(aggregates)} FROM {csv_sql(root / 'dataset.csv')}").fetchdf().iloc[0]
    feature_rows = []
    for column in feature_columns:
        feature_rows.append({"source_column": column, "dtype": "float64", "min": stats[f"{column}__min"], "max": stats[f"{column}__max"], "mean": stats[f"{column}__mean"], "std": stats[f"{column}__std"], "missing_count": stats[f"{column}__missing"], "unique_count": stats[f"{column}__unique"], "is_constant": stats[f"{column}__unique"] <= 1})
    pd.DataFrame(feature_rows).to_csv(output / "reinartz_feature_inventory.csv", index=False)
    semantic_mapping(headers["dataset.csv"]).to_csv(output / "reinartz_variable_mapping.csv", index=False)

    dataset, labels = csv_sql(root / "dataset.csv"), csv_sql(root / "labels.csv")
    train, test = csv_sql(root / "train_mask.csv"), csv_sql(root / "test_mask.csv")
    run_query = f"""
        SELECT d.run_id, count(*) n_samples, min(l.labels) label_min, max(l.labels) label_max,
               count(DISTINCT l.labels) label_count, min(d.sample) start_index, max(d.sample) end_index,
               min(CASE WHEN l.labels <> 0 THEN d.sample END) fault_onset,
               max(t.train_mask) has_train, max(e.test_mask) has_test,
               min(t.train_mask) min_train, min(e.test_mask) min_test
        FROM {dataset} d JOIN {labels} l USING(run_id,sample)
        JOIN {train} t USING(run_id,sample) JOIN {test} e USING(run_id,sample)
        GROUP BY d.run_id ORDER BY d.run_id
    """
    runs = connection.execute(run_query).fetchdf()
    runs["label"] = runs.apply(lambda row: row.label_max if row.label_count == 1 else f"{row.label_min}->{row.label_max}", axis=1)
    runs["fault_id"] = runs["label_max"].where(runs["label_max"] != 0, 0)
    runs["is_normal"] = runs["label_max"] == 0
    runs["split"] = runs.apply(lambda row: "LEAKED_BOTH" if row.has_train and row.has_test else "train" if row.has_train else "test" if row.has_test else "unassigned", axis=1)
    runs[["run_id", "n_samples", "label", "fault_id", "is_normal", "start_index", "end_index", "fault_onset", "split"]].to_csv(output / "reinartz_run_summary.csv", index=False)
    label_summary = connection.execute(
        f"SELECT labels AS fault_label,count(*) AS sample_count,"
        f"count(DISTINCT run_id) AS run_count,"
        f"100.0*count(*)/(SELECT count(*) FROM {labels}) AS percentage "
        f"FROM {labels} GROUP BY labels ORDER BY labels"
    ).fetchdf()
    label_summary.to_csv(output / "reinartz_label_summary.csv", index=False)
    alignment = connection.execute(f"SELECT count(*) total, count(l.run_id) labels_matched,count(t.run_id) train_matched,count(e.run_id) test_matched FROM {dataset} d LEFT JOIN {labels} l USING(run_id,sample) LEFT JOIN {train} t USING(run_id,sample) LEFT JOIN {test} e USING(run_id,sample)").fetchone()
    result = {"files": len(files), "rows": row_counts["dataset.csv"], "features": len(feature_columns), "xmeas": sum(name.startswith("xmeas_") for name in feature_columns), "xmv": sum(name.startswith("xmv_") for name in feature_columns), "runs": len(runs), "run_lengths": sorted(runs.n_samples.unique().tolist()), "normal_runs": int(runs.is_normal.sum()), "fault_classes": int(label_summary.fault_label.ne(0).sum()), "split_leak_runs": int(runs.split.eq("LEAKED_BOTH").sum()), "mixed_label_runs": int(runs.label_count.gt(1).sum()), "alignment": alignment, "feature_columns": feature_columns}
    connection.close()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("data/external/fddbenchmark/reinartz_tep"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/tables"))
    args = parser.parse_args()
    print(inspect(args.root, args.output))


if __name__ == "__main__":
    main()
