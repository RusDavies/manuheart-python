"""Previous-state loading from compatibility JSON reports."""

from __future__ import annotations

import json
from pathlib import Path

from manuheart.models import (
    EffectiveConfig,
    GroupState,
    HostState,
    Status,
    SystemState,
)


def _safe_json(path: Path) -> dict:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def load_previous_hosts(config: EffectiveConfig) -> dict[str, HostState]:
    payload = _safe_json(config.reports.hosts)
    result: dict[str, HostState] = {}
    for item in payload.get("hosts", []):
        state = HostState(
            name=str(item.get("name", "")),
            group=str(item.get("group", "")),
            url=str(item.get("url", "")),
            last_up=str(item.get("lastUp", "unknown")),
            last_checked=str(item.get("lastChecked", "unknown")),
            fail_count=int(item.get("failCount", 0)),
            status=Status(str(item.get("status", Status.UNKNOWN.value))),
        )
        if state.name and state.group:
            result[state.key] = state
    return result


def load_previous_groups(config: EffectiveConfig) -> dict[str, GroupState]:
    from manuheart.models import CheckType

    payload = _safe_json(config.reports.groups)
    result: dict[str, GroupState] = {}
    for item in payload.get("groups", []):
        name = str(item.get("name", ""))
        if not name:
            continue
        result[name] = GroupState(
            name=name,
            system=str(item.get("system", "")),
            critical=str(item.get("critical", "no")).lower() in {"yes", "true", "1"},
            check_type=CheckType(str(item.get("type", "icmp"))),
            min_count=int(item.get("minCount", 0)),
            failure_grace=int(item.get("failGrace", 0)),
            last_up=str(item.get("lastUp", "unknown")),
            last_checked=str(item.get("lastChecked", "unknown")),
            instance_count=int(item.get("instanceCount", 0)),
            status=Status(str(item.get("status", Status.UNKNOWN.value))),
        )
    return result


def load_previous_systems(config: EffectiveConfig) -> dict[str, SystemState]:
    payload = _safe_json(config.reports.systems)
    result: dict[str, SystemState] = {}
    for item in payload.get("systems", []):
        name = str(item.get("name", ""))
        if not name:
            continue
        result[name] = SystemState(
            name=name,
            last_up=str(item.get("lastUp", "unknown")),
            last_checked=str(item.get("lastChecked", "unknown")),
            failure_count=int(item.get("failureCount", 0)),
            status=Status(str(item.get("status", Status.UNKNOWN.value))),
        )
    return result
