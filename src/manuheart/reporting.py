"""JSON report serialization and atomic writes."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from manuheart.models import CheckRunResult, ReportDestinations


def _atomic_write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


def hosts_payload(result: CheckRunResult) -> dict:
    return {
        "hosts": [
            {
                "name": state.name,
                "group": state.group,
                "url": state.url,
                "last_up": state.last_up,
                "last_checked": state.last_checked,
                "fail_count": state.fail_count,
                "status": state.status.value,
            }
            for state in result.hosts.values()
        ]
    }


def groups_payload(result: CheckRunResult) -> dict:
    return {
        "groups": [
            {
                "name": state.name,
                "system": state.system,
                "critical": state.critical,
                "type": state.check_type.value,
                "min_count": state.min_count,
                "failure_grace": state.failure_grace,
                "last_up": state.last_up,
                "last_checked": state.last_checked,
                "instance_count": state.instance_count,
                "status": state.status.value,
            }
            for state in result.groups.values()
        ]
    }


def systems_payload(result: CheckRunResult) -> dict:
    return {
        "systems": [
            {
                "name": state.name,
                "last_up": state.last_up,
                "last_checked": state.last_checked,
                "failure_count": state.failure_count,
                "status": state.status.value,
            }
            for state in result.systems.values()
        ]
    }


def write_reports(result: CheckRunResult, destinations: ReportDestinations | None = None) -> None:
    destinations = destinations or result.config.effective.reports
    _atomic_write_json(destinations.hosts, hosts_payload(result))
    _atomic_write_json(destinations.groups, groups_payload(result))
    _atomic_write_json(destinations.systems, systems_payload(result))
