#!/usr/bin/env python3
"""Check Python output against the Bash localhost fixture contract.

The Python implementation intentionally defaults to cleaner typed JSON reports, so this
script separates hard compatibility failures from accepted migration differences.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASH_ROOT = ROOT.parent / "manuheart-bash"
BASH_RUN = BASH_ROOT / "bin" / "manuheart.sh"
BASH_CONFIG = BASH_ROOT / "examples" / "localhost" / "manuheart.conf"
PY_CONFIG = ROOT / "examples" / "localhost" / "manuheart.json"


@dataclass(frozen=True, slots=True)
class ReportSpec:
    label: str
    top_key: str
    identity_fields: tuple[str, ...]
    stable_fields: tuple[str, ...]
    renamed_fields: dict[str, str]
    typed_fields: dict[str, type]
    timestamp_fields: tuple[str, ...]


REPORT_SPECS = (
    ReportSpec(
        label="hoststatus",
        top_key="hosts",
        identity_fields=("name", "group"),
        stable_fields=("name", "group", "url", "status"),
        renamed_fields={
            "lastUp": "last_up",
            "lastChecked": "last_checked",
            "failCount": "fail_count",
        },
        typed_fields={"fail_count": int},
        timestamp_fields=("last_up", "last_checked"),
    ),
    ReportSpec(
        label="groupstatus",
        top_key="groups",
        identity_fields=("name",),
        stable_fields=("name", "system", "type", "status"),
        renamed_fields={
            "minCount": "min_count",
            "failGrace": "failure_grace",
            "lastUp": "last_up",
            "lastChecked": "last_checked",
            "instanceCount": "instance_count",
        },
        typed_fields={
            "critical": bool,
            "min_count": int,
            "failure_grace": int,
            "instance_count": int,
        },
        timestamp_fields=("last_up", "last_checked"),
    ),
    ReportSpec(
        label="sysstatus",
        top_key="systems",
        identity_fields=("name",),
        stable_fields=("name", "status"),
        renamed_fields={
            "lastUp": "last_up",
            "lastChecked": "last_checked",
            "failureCount": "failure_count",
        },
        typed_fields={"failure_count": int},
        timestamp_fields=("last_up", "last_checked"),
    ),
)


class CompatibilityFailure(AssertionError):
    """A migration-relevant contract check failed."""


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def identity(item: dict, fields: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(str(item[field]) for field in fields)


def index_by_identity(payload: dict, spec: ReportSpec) -> dict[tuple[str, ...], dict]:
    return {identity(item, spec.identity_fields): item for item in payload[spec.top_key]}


def summarize(payload: dict, spec: ReportSpec) -> dict[str, str]:
    return {
        "/".join(key): str(item.get("status", ""))
        for key, item in index_by_identity(payload, spec).items()
    }


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
    for payload, spec in zip((hosts, groups, systems), REPORT_SPECS, strict=True):
        if spec.top_key not in payload or not isinstance(payload[spec.top_key], list):
            raise CompatibilityFailure(f"{spec.label}: missing list top-level key {spec.top_key!r}")
        if not payload[spec.top_key]:
            raise CompatibilityFailure(f"{spec.label}: empty {spec.top_key!r} list")


def is_iso8601(value: Any) -> bool:
    if not isinstance(value, str) or value == "unknown":
        return value == "unknown"
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def compare_report(py_payload: dict, bash_payload: dict, spec: ReportSpec) -> list[str]:
    differences: list[str] = []
    py_records = index_by_identity(py_payload, spec)
    bash_records = index_by_identity(bash_payload, spec)
    if set(py_records) != set(bash_records):
        raise CompatibilityFailure(
            f"{spec.label}: record identities differ: "
            f"python={sorted(py_records)} bash={sorted(bash_records)}"
        )

    for key in sorted(py_records):
        py_item = py_records[key]
        bash_item = bash_records[key]
        label = f"{spec.label}:{'/'.join(key)}"
        for field in spec.stable_fields:
            if str(py_item.get(field)) != str(bash_item.get(field)):
                if label == "groupstatus:optional-example" and field == "status":
                    differences.append(
                        f"{label}: status follows min_count=0 semantics "
                        f"({py_item.get(field)!r} vs Bash {bash_item.get(field)!r})"
                    )
                    continue
                raise CompatibilityFailure(
                    f"{label}: stable field {field!r} differs: "
                    f"python={py_item.get(field)!r} bash={bash_item.get(field)!r}"
                )
        for legacy, clean in spec.renamed_fields.items():
            if clean not in py_item:
                raise CompatibilityFailure(f"{label}: missing clean field {clean!r}")
            if legacy in py_item:
                raise CompatibilityFailure(
                    f"{label}: clean output still contains legacy field {legacy!r}"
                )
            if legacy in bash_item:
                differences.append(f"{label}: field renamed {legacy} -> {clean}")
        for field, expected_type in spec.typed_fields.items():
            if not isinstance(py_item.get(field), expected_type):
                raise CompatibilityFailure(
                    f"{label}: field {field!r} should be {expected_type.__name__}, "
                    f"got {type(py_item.get(field)).__name__}"
                )
            differences.append(f"{label}: field {field} is typed as {expected_type.__name__}")
        for field in spec.timestamp_fields:
            if not is_iso8601(py_item.get(field)):
                raise CompatibilityFailure(f"{label}: field {field!r} is not ISO-8601/unknown")
            if py_item.get(field) != "unknown":
                differences.append(f"{label}: timestamp {field} is ISO-8601")

    return differences


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="manuheart-compat-") as tmp_name:
        tmp = Path(tmp_name)
        py_reports = run_python(tmp)
        assert_shape(*py_reports)
        bash_result = run_bash(tmp)
        if bash_result is None:
            print("Bash reference unavailable; Python output shape check passed")
            return 0
        bash_reports = bash_result
        assert_shape(*bash_reports)
        differences: list[str] = []
        for py_payload, bash_payload, spec in zip(
            py_reports, bash_reports, REPORT_SPECS, strict=True
        ):
            differences.extend(compare_report(py_payload, bash_payload, spec))

    print("localhost compatibility check passed")
    print("accepted migration differences:")
    for difference in sorted(set(differences)):
        print(f"- {difference}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
