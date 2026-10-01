from pathlib import Path

from src.data.cmapss import NAMES, load_split


def test_load_split(tmp_path: Path) -> None:
    sample = tmp_path / "train_FD001.txt"
    sample.write_text(" ".join(str(i) for i in range(1, 27)) + "\n", encoding="utf-8")
    frame = load_split(sample)
    assert list(frame.columns) == NAMES
    assert frame.shape == (1, 26)

