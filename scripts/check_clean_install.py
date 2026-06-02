#!/usr/bin/env python3
"""Create a clean venv, install the package, and smoke-test CLI/API entry points."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import venv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(command, cwd=cwd or ROOT, check=True)


def venv_bin(venv_dir: Path, name: str) -> Path:
    return venv_dir / ("Scripts" if sys.platform == "win32" else "bin") / name


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="manuheart-clean-install-") as tmp_name:
        tmp = Path(tmp_name)
        venv_dir = tmp / "venv"
        output_dir = tmp / "out"
        output_dir.mkdir()

        venv.EnvBuilder(with_pip=True).create(venv_dir)
        python = venv_bin(venv_dir, "python")
        manuheart = venv_bin(venv_dir, "manuheart")

        run([str(python), "-m", "pip", "install", "--upgrade", "pip"])
        run([str(python), "-m", "pip", "install", f"{ROOT}[yaml]"])

        run(
            [
                str(python),
                "-c",
                "from importlib.resources import files; "
                "from manuheart.api import load_config, run_check; "
                "assert (files('manuheart') / 'py.typed').is_file(); "
                "cfg = load_config('examples/localhost/manuheart.json'); "
                "result = run_check(cfg); "
                "assert result.hosts and result.groups and result.systems",
            ],
            cwd=ROOT,
        )
        run(
            [
                str(manuheart),
                "validate-config",
                "--config",
                str(ROOT / "examples/localhost/manuheart.json"),
            ]
        )
        run(
            [
                str(manuheart),
                "validate-config",
                "--config",
                str(ROOT / "examples/localhost/manuheart.yaml"),
            ]
        )
        run(
            [
                str(manuheart),
                "check",
                "--config",
                str(ROOT / "examples/localhost/manuheart.json"),
                "--host-status-file",
                str(output_dir / "hoststatus"),
                "--group-status-file",
                str(output_dir / "groupstatus"),
                "--sys-status-file",
                str(output_dir / "sysstatus"),
            ]
        )

        for name, key in (
            ("hoststatus", "hosts"),
            ("groupstatus", "groups"),
            ("sysstatus", "systems"),
        ):
            payload = json.loads((output_dir / name).read_text())
            assert payload[key], f"{name} did not contain {key} records"

        installed = subprocess.check_output(
            [str(python), "-m", "pip", "show", "manuheart"], text=True
        )
        print("clean install smoke passed")
        print(installed.splitlines()[0])
        print(f"venv: {venv_dir}")
        print(f"python: {python}")
        print(f"manuheart: {manuheart}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
