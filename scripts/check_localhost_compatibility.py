#!/usr/bin/env python3
"""Check Python output shape against the Bash localhost fixture contract."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASH_ROOT = ROOT.parent / "manuheart-bash"
BASH_RUN = BASH_ROOT / "bin" / "manuheart.sh"
BASH_CONFIG = BASH_ROOT / "examples" / "localhost" / "manuheart.conf"
PY_CONFIG = ROOT / "examples" / "localhost" / "manuheart.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def summarize(payload: dict, key: str, name_field: str = "name") -> dict[str, str]:
    return {str(item[name_field]): str(item.get("status", "")) for item in payload[key]}


def run_python(tmp: Path) -> tuple[dict, dict, dict]:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "manuheart",
            "check",
            "--config",
            str(PY_CONFIG),
            "--host-status-file",
            str(tmp / "python" / "hoststatus"),
            "--group-status-file",
            str(tmp / "python" / "groupstatus"),
            "--sys-status-file",
            str(tmp / "python" / "sysstatus"),
        ],
        cwd=ROOT,
        check=True,
    )
    return (
        load(tmp / "python" / "hoststatus"),
        load(tmp / "python" / "groupstatus"),
        load(tmp / "python" / "sysstatus"),
    )


def run_bash(tmp: Path) -> tuple[dict, dict, dict] | None:
    if not BASH_RUN.exists() or not shutil.which("bash"):
        return None
    config_dir = tmp / "bash-config"
    out = tmp / "bash"
    config_dir.mkdir(parents=True)
    out.mkdir(parents=True)
    shutil.copy(BASH_ROOT / "examples" / "localhost" / "groups", config_dir / "groups")
    shutil.copy(BASH_ROOT / "examples" / "localhost" / "hosts", config_dir / "hosts")
    (config_dir / "manuheart.conf").write_text(
        "\n".join(
            [
                f"VARDIR: {out}",
                "LOGLEVEL: 3",
                "CHECKPERIOD: 3",
                "RUNMODE: once",
                f"GROUPFILE: {config_dir / 'groups'}",
                f"HOSTFILE: {config_dir / 'hosts'}",
                f"HOSTSTATUSOUTFILE: {out / 'hoststatus'}",
                f"GROUPSTATUSOUTFILE: {out / 'groupstatus'}",
                f"SYSSTATUSOUTFILE: {out / 'sysstatus'}",
                "",
            ]
        )
    )
    subprocess.run(
        ["bash", str(BASH_RUN), "--once", "--config", str(config_dir / "manuheart.conf")],
        cwd=BASH_ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    return load(out / "hoststatus"), load(out / "groupstatus"), load(out / "sysstatus")


def assert_shape(hosts: dict, groups: dict, systems: dict) -> None:
    assert "hosts" in hosts and isinstance(hosts["hosts"], list)
    assert "groups" in groups and isinstance(groups["groups"], list)
    assert "systems" in systems and isinstance(systems["systems"], list)
    assert summarize(hosts, "hosts")
    assert summarize(groups, "groups")
    assert summarize(systems, "systems")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="manuheart-compat-") as tmp_name:
        tmp = Path(tmp_name)
        py_hosts, py_groups, py_systems = run_python(tmp)
        assert_shape(py_hosts, py_groups, py_systems)
        bash_result = run_bash(tmp)
        if bash_result is None:
            print("Bash reference unavailable; Python output shape check passed")
            return 0
        bash_hosts, bash_groups, bash_systems = bash_result
        assert_shape(bash_hosts, bash_groups, bash_systems)
        # Compare stable, consumer-relevant names. Live statuses may differ by platform/network.
        assert set(summarize(py_hosts, "hosts")) == set(summarize(bash_hosts, "hosts"))
        assert set(summarize(py_groups, "groups")) == set(summarize(bash_groups, "groups"))
        assert set(summarize(py_systems, "systems")) == set(summarize(bash_systems, "systems"))
    print("localhost compatibility check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
