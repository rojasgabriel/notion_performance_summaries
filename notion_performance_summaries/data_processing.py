"""Data processing functions for lab data sessions and MATLAB operations."""

import os
import re
import subprocess
from typing import List


def run_cmd(cmd, dry_run=False):
    """Execute a shell command and return stdout, or print for dry run."""
    print("▶", " ".join(cmd))
    if dry_run:
        print("DRY RUN: Command not executed")
        return "DRY RUN"
    return subprocess.run(
        cmd, capture_output=True, text=True, check=True
    ).stdout.strip()


def ensure_sessions(
    subject, pattern, sessions_back, input_loc, dry_run=False
) -> List[str]:
    """Mimics labdata session checking/downloading logic."""
    # Get list of sessions
    out = run_cmd(["labdata", "sessions", subject, "--files"], dry_run=dry_run)
    if dry_run:
        print("DRY RUN: Skipping session discovery, returning mock session list")
        return [f"{pattern}_000000"]
    sessions = sorted(list(set(re.findall(r"[0-9]{8}_[0-9]{6}", out))), reverse=True)
    # Find pattern match
    match_index = next((i for i, s in enumerate(sessions) if s.startswith(pattern)), -1)
    if match_index < 0:
        print(f"❌ No session found for {subject} with {pattern}")
        return []
    end_index = min(match_index + sessions_back + 1, len(sessions))
    to_download = sessions[match_index:end_index]

    for sess in to_download:
        session_dir = f"{input_loc}/{subject}/{sess}/chipmunk"
        if os.path.exists(session_dir) and any(
            f.endswith(".mat") for f in os.listdir(session_dir)
        ):
            print(f"✅ Already downloaded: {subject} {sess}")
        else:
            print(f"⬇️ Downloading: {subject} {sess}")
            run_cmd(
                [
                    "labdata",
                    "get",
                    subject,
                    "-s",
                    sess,
                    "-d",
                    "chipmunk",
                    "-i",
                    "*.mat",
                ],
                dry_run=dry_run,
            )
    return to_download


def run_matlab(
    subject,
    input_loc,
    labdata_loc,
    subject_output,
    sessions_back,
    pattern,
    dry_run=False,
):
    """Execute MATLAB script for generating performance visualizations."""
    os.makedirs(subject_output, exist_ok=True)
    matlab_cmd = (
        f"batchCopyPlot({{'{subject}'}}, '{input_loc}', '{labdata_loc}', "
        f"'{subject_output}', {sessions_back}, '{pattern}')"
    )
    print("⚙️ Running MATLAB for", subject)
    run_cmd(["matlab", "-batch", matlab_cmd], dry_run=dry_run)
    print("✔️ Finished MATLAB for", subject)
