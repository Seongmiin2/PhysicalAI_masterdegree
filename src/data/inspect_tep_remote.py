from __future__ import annotations

import argparse
import json
from pathlib import Path

import fsspec
import h5py
import truststore

truststore.inject_into_ssl()


def describe(node: h5py.Group | h5py.Dataset, depth: int, max_depth: int) -> dict:
    if isinstance(node, h5py.Dataset):
        return {"type": "dataset", "shape": list(node.shape), "dtype": str(node.dtype)}
    result: dict = {"type": "group", "children": {}}
    if depth < max_depth:
        for name in node:
            result["children"][name] = describe(node[name], depth + 1, max_depth)
    else:
        result["child_names"] = list(node.keys())
    return result


def inspect(url: str, output: Path, max_depth: int) -> dict:
    with (
        fsspec.open(
            url, mode="rb", block_size=8 * 1024 * 1024, cache_type="readahead"
        ) as remote,
        h5py.File(remote, "r") as handle,
    ):
        result = describe(handle, 0, max_depth)
        for label_name in ("Processdata_Labels", "Additional_Meas_Labels"):
            if label_name in handle:
                values = handle[label_name][...]
                result[label_name] = [
                    value.decode(errors="replace") if isinstance(value, bytes) else str(value)
                    for value in values.reshape(-1)
                ]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="https://ndownloader.figshare.com/files/26003087")
    parser.add_argument("--output", type=Path, default=Path("data/raw/tep/mode1_remote_structure.json"))
    parser.add_argument("--max-depth", type=int, default=5)
    args = parser.parse_args()
    result = inspect(args.url, args.output, args.max_depth)
    print({"root": list(result.get("children", {})), "output": str(args.output)})


if __name__ == "__main__":
    main()
