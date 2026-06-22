#!/usr/bin/env python3
"""Run OSV Scanner against Manuheart dependency inputs and repository manifests."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import venv
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
LOCAL_SCANNER = ROOT / ".tools" / "osv-scanner"
RUNTIME_EXTRAS = ("yaml",)
TOOLING_EXTRAS = ("release", "dev")
REPO_EXCLUDES = (
    ".git",
    ".mypy_cache",
    ".openclaw-security-audit",
    ".pytest_cache",
    ".ruff_cache",
    ".tools",
    ".venv",
    "dist",
)


def project_metadata() -> dict[str, Any]:
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    return cast("dict[str, Any]", data["project"])


def dependency_group(extra_names: Sequence[str]) -> list[str]:
    """Return base dependencies plus selected optional dependency groups."""

    project = project_metadata()
    requirements = list(project.get("dependencies", []))
    optional = project.get("optional-dependencies", {})
    for extra_name in extra_names:
        requirements.extend(optional.get(extra_name, []))
    return sorted(dict.fromkeys(requirements), key=str.lower)


def direct_requirements_inputs(directory: Path) -> dict[str, Path]:
    """Write direct requirement inputs and return name-to-path mapping."""

    groups = {
        "runtime": dependency_group(RUNTIME_EXTRAS),
        "tooling": dependency_group(TOOLING_EXTRAS),
    }
    paths: dict[str, Path] = {}
    for name, requirements in groups.items():
        path = directory / f"{name}-direct-requirements.txt"
        path.write_text("\n".join(requirements) + "\n", encoding="utf-8")
        paths[name] = path
    return paths


def venv_python(venv_path: Path) -> Path:
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def resolve_requirements(name: str, direct_path: Path, directory: Path) -> Path:
    """Resolve requirements into an exact pip freeze lock for OSV scanning."""

    environment = directory / f"{name}-venv"
    venv.EnvBuilder(with_pip=True).create(environment)
    python = venv_python(environment)
    subprocess.run([str(python), "-m", "pip", "install", "-q", "--upgrade", "pip"], check=True)
    subprocess.run(
        [str(python), "-m", "pip", "install", "-q", "--upgrade", "-r", str(direct_path)],
        check=True,
    )
    frozen = subprocess.run(
        [str(python), "-m", "pip", "freeze", "--all"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    resolved_path = directory / f"{name}-requirements.txt"
    resolved_path.write_text(frozen, encoding="utf-8")
    return resolved_path


def requirements_inputs(directory: Path, *, resolve: bool = False) -> dict[str, Path]:
    """Write OSV-scannable requirement inputs and return name-to-path mapping."""

    direct_paths = direct_requirements_inputs(directory)
    if not resolve:
        return direct_paths
    return {
        name: resolve_requirements(name, direct_path, directory)
        for name, direct_path in direct_paths.items()
    }


def scanner_path(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    if env_path := os.environ.get("OSV_SCANNER"):
        return env_path
    if LOCAL_SCANNER.exists():
        return str(LOCAL_SCANNER)
    discovered = shutil.which("osv-scanner")
    if discovered:
        return discovered
    raise FileNotFoundError(
        "osv-scanner not found; run scripts/install_osv_scanner.py or set OSV_SCANNER"
    )


def run(scanner: str, args: Sequence[str]) -> int:
    completed = subprocess.run([scanner, *args], cwd=ROOT, check=False)
    return completed.returncode


def scan_requirements(scanner: str, paths: dict[str, Path]) -> int:
    failures = 0
    for name, path in paths.items():
        print(f"OSV dependency scan: {name} ({path.name})", flush=True)
        failures += int(
            run(
                scanner,
                [
                    "scan",
                    "source",
                    "--lockfile",
                    str(path),
                    "--no-resolve",
                    "--format",
                    "json",
                    "--verbosity",
                    "error",
                ],
            )
            != 0
        )
    return failures


def scan_repository(scanner: str) -> int:
    args = [
        "scan",
        "source",
        "--recursive",
        "--allow-no-lockfiles",
        "--format",
        "json",
        "--verbosity",
        "error",
    ]
    for exclude in REPO_EXCLUDES:
        args.extend(["--experimental-exclude", exclude])
    args.append(".")
    print("OSV repository manifest scan", flush=True)
    return int(run(scanner, args) != 0)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scanner", help="Path to osv-scanner binary")
    parser.add_argument("--skip-repo", action="store_true", help="Skip recursive repository scan")
    args = parser.parse_args(argv)

    try:
        scanner = scanner_path(args.scanner)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 127

    with tempfile.TemporaryDirectory(prefix="manuheart-osv-") as tmp:
        paths = requirements_inputs(Path(tmp), resolve=True)
        failures = scan_requirements(scanner, paths)
        if not args.skip_repo:
            failures += scan_repository(scanner)
    if failures:
        print(f"OSV scanner gate failed: {failures} scan(s) reported vulnerabilities or errors")
        return 1
    print("OSV scanner gate passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
