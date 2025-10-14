#!/usr/bin/env python3
"""
Generate a Markdown table of recent commits and store the output under docs/.

The script is intended to run both locally and within CI so keep dependencies
minimal and lean on git CLI output instead of third party libraries.
"""

from __future__ import annotations

import datetime
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = REPO_ROOT / "docs"
OUTPUT_FILE = DOCS_DIR / "commit-history.md"


def repo_has_commits() -> bool:
    """Return True if the repository already contains at least one commit."""
    result = subprocess.run(
        ["git", "rev-parse", "--quiet", "--verify", "HEAD"],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    return result.returncode == 0


def fetch_commits() -> List[Tuple[str, str, str, str]]:
    """
    Fetch commit data as tuples of (short_hash, author, date, subject).

    The git log format uses a unit separator to make parsing reliable even when
    commit subjects contain spaces.
    """
    log_format = "%h%x1f%an%x1f%ad%x1f%s"
    result = subprocess.run(
        ["git", "log", f"--pretty=format:{log_format}", "--date=short"],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )

    commits: List[Tuple[str, str, str, str]] = []
    for raw_line in result.stdout.strip().splitlines():
        if not raw_line:
            continue
        parts = raw_line.split("\x1f")
        if len(parts) != 4:
            # Skip unexpected lines instead of failing the whole run.
            continue
        short_hash, author, date, subject = parts
        commits.append((short_hash, author, date, subject))
    return commits


def normalise_cell(value: str) -> str:
    """Escape pipe characters to keep the markdown table valid."""
    return value.replace("|", "\\|").replace("\n", " ")


def render_markdown(commits: List[Tuple[str, str, str, str]]) -> str:
    """Render the collected commits as a markdown document."""
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )
    lines = [
        "# Commit History",
        "",
        f"> Last updated: {timestamp}",
        "> Generated automatically by scripts/generate_commit_history.py",
        "",
    ]

    if not commits:
        lines.append("No commits have been recorded yet.")
        lines.append("")
        return "\n".join(lines)

    lines.extend(
        [
            "| Hash | Author | Date | Message |",
            "| ---- | ------ | ---- | ------- |",
        ]
    )
    for short_hash, author, date, subject in commits:
        lines.append(
            f"| `{short_hash}` | {normalise_cell(author)} | {normalise_cell(date)} | {normalise_cell(subject)} |"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    try:
        commits = fetch_commits() if repo_has_commits() else []
    except subprocess.CalledProcessError as exc:
        print("Failed to read commit history:", exc, file=sys.stderr)
        return exc.returncode

    markdown = render_markdown(commits)
    OUTPUT_FILE.write_text(markdown, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
