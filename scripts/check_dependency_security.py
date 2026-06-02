#!/usr/bin/env python3
"""Audit releasable Manuheart dependencies for known vulnerabilities."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"


def releasable_requirements() -> list[str]:
    """Return runtime dependencies plus optional runtime extras, excluding dev tools."""

    project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
    requirements = list(project.get("dependencies", []))
    requirements.extend(project.get("optional-dependencies", {}).get("yaml", []))
    return requirements


def main() -> int:
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt") as requirements:
        requirements.write("\n".join(releasable_requirements()))
        requirements.write("\n")
        requirements.flush()
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pip_audit",
                "--requirement",
                requirements.name,
                "--strict",
                "--progress-spinner",
                "off",
                "--desc",
                "off",
                "--aliases",
                "off",
            ],
            cwd=ROOT,
            check=False,
        )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
