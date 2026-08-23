from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


SKILL_RENDERER = Path(
    r"C:\Users\Master\.codex\plugins\cache\openai-primary-runtime\documents\26.601.10930\skills\documents\render_docx.py"
)
spec = importlib.util.spec_from_file_location("skill_render_docx", SKILL_RENDERER)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Cannot load renderer: {SKILL_RENDERER}")
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


def convert_to_pdf_windows(
    doc_path: str,
    user_profile: str,
    convert_tmp_dir: str,
    stem: str,
    verbose: bool,
) -> tuple[str, str]:
    """Windows-safe equivalent of the packaged renderer's converter.

    The packaged script concatenates ``file://`` with a Windows path, which
    produces an invalid LibreOffice profile URI and can hang. ``Path.as_uri``
    preserves the same isolated-profile behavior with a valid file URI.
    """
    env = renderer._build_lo_env(user_profile)
    profile_uri = Path(user_profile).resolve().as_uri()
    command = [
        "soffice",
        f"-env:UserInstallation={profile_uri}",
        "--invisible",
        "--headless",
        "--norestore",
        "--convert-to",
        "pdf",
        "--outdir",
        convert_tmp_dir,
        doc_path,
    ]
    process = renderer._run_cmd(command, env=env, verbose=verbose)
    pdf_path = os.path.join(convert_tmp_dir, f"{stem}.pdf")
    debug = "CMD: " + " ".join(command)
    if process.stdout:
        debug += "\nSTDOUT:\n" + process.stdout
    if process.stderr:
        debug += "\nSTDERR:\n" + process.stderr
    if process.returncode == 0 and os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
        return pdf_path, debug
    return "", debug


renderer.convert_to_pdf = convert_to_pdf_windows
renderer.main()
