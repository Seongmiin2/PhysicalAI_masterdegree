from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path

import requests

URL = "https://phm-datasets.s3.amazonaws.com/NASA/6.+Turbofan+Engine+Degradation+Simulation+Data+Set.zip"
DEST = Path("data/raw/cmapss")


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    archive = DEST / "cmapss.zip"
    if not archive.exists():
        with requests.get(URL, stream=True, timeout=60) as response:
            response.raise_for_status()
            with archive.open("wb") as output:
                shutil.copyfileobj(response.raw, output)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    with zipfile.ZipFile(archive) as bundle:
        bundle.extractall(DEST)
    print(f"Downloaded {archive} (sha256={digest})")


if __name__ == "__main__":
    main()

