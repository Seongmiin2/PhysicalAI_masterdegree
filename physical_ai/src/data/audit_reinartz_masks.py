from __future__ import annotations

from pathlib import Path

import duckdb


def source(root: Path, name: str) -> str:
    path = (root / f"{name}.csv").resolve().as_posix().replace("'", "''")
    return f"read_csv_auto('{path}',header=true,sample_size=-1)"


def main() -> None:
    root = Path("data/external/fddbenchmark/reinartz_tep")
    connection = duckdb.connect()
    train, test = source(root, "train_mask"), source(root, "test_mask")
    labels, labeled = source(root, "labels"), source(root, "labeled_train_mask")
    print(
        "mask_combinations",
        connection.execute(
            f"SELECT train_mask,test_mask,count(*) FROM {train} JOIN {test} "
            "USING(run_id,sample) GROUP BY ALL ORDER BY ALL"
        ).fetchall(),
    )
    print(
        "labeled_train_by_fault",
        connection.execute(
            f"SELECT l.labels,sum(m.labeled_train_mask),"
            "count(DISTINCT CASE WHEN labeled_train_mask=1 THEN run_id END) "
            f"FROM {labels} AS l JOIN {labeled} AS m USING(run_id,sample) "
            "GROUP BY l.labels ORDER BY l.labels"
        ).fetchall(),
    )
    print(
        "runs_with_row_varying_train_mask",
        connection.execute(
            f"SELECT count(*) FROM (SELECT run_id FROM {train} GROUP BY run_id "
            "HAVING min(train_mask)<>max(train_mask))"
        ).fetchone()[0],
    )


if __name__ == "__main__":
    main()
