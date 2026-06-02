"""Previous-state loading from compatibility JSON reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from manuheart.models import (
    CheckType,
    EffectiveConfig,
    GroupState,
    HostState,
    Status,
    SystemState,
)


def _safe_json(path: Path) -> dict[str, Any]:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _items(payload: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = payload.get(key, [])
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _pick(item: dict[str, Any], preferred: str, legacy: str, default: object) -> object:
    return item.get(preferred, item.get(legacy, default))


def _safe_str(value: object, default: str = "unknown") -> str:
    if value is None:
        return default
    text = str(value)
    return text if text else default


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _bool_value(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"yes", "true", "1"}:
        return True
    if normalized in {"no", "false", "0"}:
        return False
    return default


def _safe_status(value: object) -> Status:
    try:
        return Status(str(value))
    except ValueError:
        return Status.UNKNOWN


def _safe_check_type(value: object) -> CheckType:
    try:
        return CheckType(str(value).lower())
    except ValueError:
        return CheckType.ICMP


def load_previous_hosts(config: EffectiveConfig) -> dict[str, HostState]:
    payload = _safe_json(config.reports.hosts)
    result: dict[str, HostState] = {}
    for item in _items(payload, "hosts"):
        state = HostState(
            name=_safe_str(item.get("name"), ""),
            group=_safe_str(item.get("group"), ""),
            url=_safe_str(item.get("url"), "unknown"),
            last_up=_safe_str(_pick(item, "last_up", "lastUp", "unknown")),
            last_checked=_safe_str(_pick(item, "last_checked", "lastChecked", "unknown")),
            fail_count=_safe_int(_pick(item, "fail_count", "failCount", 0)),
            status=_safe_status(item.get("status", Status.UNKNOWN.value)),
        )
        if state.name and state.group:
            result[state.key] = state
    return result


def load_previous_groups(config: EffectiveConfig) -> dict[str, GroupState]:
    payload = _safe_json(config.reports.groups)
    result: dict[str, GroupState] = {}
    for item in _items(payload, "groups"):
        name = _safe_str(item.get("name"), "")
        if not name:
            continue
        result[name] = GroupState(
            name=name,
            system=_safe_str(item.get("system"), "unknown"),
            critical=_bool_value(item.get("critical", False)),
            check_type=_safe_check_type(item.get("type", CheckType.ICMP.value)),
            min_count=_safe_int(_pick(item, "min_count", "minCount", 0)),
            failure_grace=_safe_int(_pick(item, "failure_grace", "failGrace", 0)),
            last_up=_safe_str(_pick(item, "last_up", "lastUp", "unknown")),
            last_checked=_safe_str(_pick(item, "last_checked", "lastChecked", "unknown")),
            instance_count=_safe_int(_pick(item, "instance_count", "instanceCount", 0)),
            status=_safe_status(item.get("status", Status.UNKNOWN.value)),
        )
    return result


def load_previous_systems(config: EffectiveConfig) -> dict[str, SystemState]:
    payload = _safe_json(config.reports.systems)
    result: dict[str, SystemState] = {}
    for item in _items(payload, "systems"):
        name = _safe_str(item.get("name"), "")
        if not name:
            continue
        result[name] = SystemState(
            name=name,
            last_up=_safe_str(_pick(item, "last_up", "lastUp", "unknown")),
            last_checked=_safe_str(_pick(item, "last_checked", "lastChecked", "unknown")),
            failure_count=_safe_int(_pick(item, "failure_count", "failureCount", 0)),
            status=_safe_status(item.get("status", Status.UNKNOWN.value)),
        )
    return result
