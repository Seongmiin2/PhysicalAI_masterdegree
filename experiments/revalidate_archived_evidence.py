"""Revalidate the frozen evidence without restoring artifacts into the working tree."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

import validate_final_evidence


ROOT = Path(__file__).resolve().parents[1]
SOURCE = "bc6166f792e3faceb060a50de6219dddca393fd6"
INPUTS = {
    "architecture_chum_g3": ["RUN_MANIFEST.json", "G3_ANALYSIS_MANIFEST.json", "G3_FAULT_RESULTS.csv", "G3_RUN_RESULTS.csv", "G3_CELL_SUMMARY.csv", "G3_ARCHITECTURE_CONSENSUS.csv"],
    "integrated_gradients_baseline": ["RUN_MANIFEST.json", "ANALYSIS_MANIFEST.json", "INTEGRATED_GRADIENTS.csv", "IG_CHUM_RANK_AGREEMENT.csv"],
    "hai_2103_prepared": ["HAI_2103_PREPARATION_MANIFEST.json", "HAI_2103_ROLE_MANIFEST.json", "HAI_2103_ATTACK_TARGET_MANIFEST.json"],
    "hai_external_validation": ["RUN_MANIFEST.json"],
    "hai_external_validation_v2": ["RUN_MANIFEST.json", "HAI_EXTERNAL_ANALYSIS_MANIFEST.json", "HAI_EXTERNAL_METRICS.csv", "HAI_EXTERNAL_TARGET_EVENTS.csv"],
    "hai_conditional_chum": ["RUN_MANIFEST.json", "HAI_IMPUTER_MANIFEST.json", "HAI_CONDITIONAL_ANALYSIS_MANIFEST.json", "HAI_IMPUTER_QUALITY.csv", "HAI_CONDITIONAL_METRICS.csv", "HAI_CONDITIONAL_EVENTS.csv", "HAI_CONDITIONAL_TARGETED_SUMMARY.csv"],
}


def main() -> None:
    output = ROOT / "outputs/closeout_validation"
    records = []
    original_root = validate_final_evidence.ROOT
    with tempfile.TemporaryDirectory(prefix="chum-evidence-") as directory:
        archive = Path(directory)
        for group, names in INPUTS.items():
            for name in names:
                relative = f"outputs/{group}/{name}"
                data = subprocess.run(
                    ["git", "show", f"{SOURCE}:{relative}"], cwd=ROOT,
                    check=True, capture_output=True,
                ).stdout
                target = archive / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
                records.append({"path": relative, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        try:
            validate_final_evidence.ROOT = archive
            validate_final_evidence.main()
        finally:
            validate_final_evidence.ROOT = original_root
        output.mkdir(parents=True, exist_ok=True)
        for result in (archive / "outputs/final_evidence_validation").iterdir():
            shutil.copy2(result, output / result.name)
    manifest = {
        "source_commit": SOURCE,
        "validator_sha256": hashlib.sha256(Path(validate_final_evidence.__file__).read_bytes()).hexdigest(),
        "inputs": records,
        "scope": "Archived result-table and manifest validation; no model retraining, raw telemetry reprocessing, or fresh confidence-interval estimation.",
    }
    (output / "ARCHIVE_PROVENANCE.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print((output / "VALIDATION_MANIFEST.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
