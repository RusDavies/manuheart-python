"""Previous-state loading from compatibility JSON reports."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from manuheart.models import (
    CheckType,
    EffectiveConfig,
    GroupState,
    HostState,
    PreviousStateSnapshot,
    Status,
    SystemState,
)


@dataclass(frozen=True, slots=True)
class PreviousState(PreviousStateSnapshot):
    hosts: dict[str, HostState]
    groups: dict[str, GroupState]
    systems: dict[str, SystemState]


def _safe_json(path: Path, label: str, warnings: list[str]) -> dict[str, Any]:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError:
        warnings.append(f"{label}: previous state file {path} is invalid JSON; ignoring")
        return {}
    if not isinstance(payload, dict):
        warnings.append(f"{label}: previous state file {path} is not an object; ignoring")
        return {}
    return payload


def _items(
    payload: dict[str, Any], key: str, label: str, warnings: list[str]
) -> list[dict[str, Any]]:
    value = payload.get(key, [])
    if not isinstance(value, list):
        warnings.append(f"{label}: previous state field {key!r} is not a list; ignoring")
        return []
    result = []
    for idx, item in enumerate(value):
        if isinstance(item, dict):
            result.append(item)
        else:
            warnings.append(f"{label}: previous state {key}[{idx}] is not an object; ignoring")
    return result


def _pick(item: dict[str, Any], preferred: str, legacy: str, default: object) -> object:
    return item.get(preferred, item.get(legacy, default))


def _safe_str(value: object, default: str = "unknown") -> str:
    if value is None:
        return default
    text = str(value)
    return text if text else default


def _safe_int(
    value: object, default: int = 0, warnings: list[str] | None = None, context: str = "value"
) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        if warnings is not None:
            warnings.append(f"{context}: invalid integer {value!r}; using {default}")
        return default


def _bool_value(
    value: object, default: bool = False, warnings: list[str] | None = None, context: str = "value"
) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"yes", "true", "1"}:
        return True
    if normalized in {"no", "false", "0"}:
        return False
    if warnings is not None:
        warnings.append(f"{context}: invalid boolean {value!r}; using {default}")
    return default


def _safe_status(
    value: object, warnings: list[str] | None = None, context: str = "status"
) -> Status:
    try:
        return Status(str(value))
    except ValueError:
        if warnings is not None:
            warnings.append(f"{context}: invalid status {value!r}; using unknown")
        return Status.UNKNOWN


def _safe_check_type(
    value: object, warnings: list[str] | None = None, context: str = "type"
) -> CheckType:
    try:
        return CheckType(str(value).lower())
    except ValueError:
        if warnings is not None:
            warnings.append(f"{context}: invalid check type {value!r}; using icmp")
        return CheckType.ICMP


def _load_previous_hosts(config: EffectiveConfig, warnings: list[str]) -> dict[str, HostState]:
    payload = _safe_json(config.reports.hosts, "hoststatus", warnings)
    result: dict[str, HostState] = {}
    for item in _items(payload, "hosts", "hoststatus", warnings):
        name = _safe_str(item.get("name"), "")
        group = _safe_str(item.get("group"), "")
        context = f"hoststatus {group}/{name}" if name and group else "hoststatus record"
        state = HostState(
            name=name,
            group=group,
            url=_safe_str(item.get("url"), "unknown"),
            last_up=_safe_str(_pick(item, "last_up", "lastUp", "unknown")),
            last_checked=_safe_str(_pick(item, "last_checked", "lastChecked", "unknown")),
            fail_count=_safe_int(
                _pick(item, "fail_count", "failCount", 0),
                warnings=warnings,
                context=f"{context}.fail_count",
            ),
            status=_safe_status(
                item.get("status", Status.UNKNOWN.value),
                warnings=warnings,
                context=f"{context}.status",
            ),
            detail=_safe_str(item.get("detail"), ""),
        )
        if state.name and state.group:
            result[state.key] = state
        else:
            warnings.append(
                "hoststatus: previous state host record missing name or group; ignoring"
            )
    return result


def load_previous_hosts(config: EffectiveConfig) -> dict[str, HostState]:
    return _load_previous_hosts(config, [])


def _load_previous_groups(config: EffectiveConfig, warnings: list[str]) -> dict[str, GroupState]:
    payload = _safe_json(config.reports.groups, "groupstatus", warnings)
    result: dict[str, GroupState] = {}
    for item in _items(payload, "groups", "groupstatus", warnings):
        name = _safe_str(item.get("name"), "")
        if not name:
            warnings.append("groupstatus: previous state group record missing name; ignoring")
            continue
        result[name] = GroupState(
            name=name,
            system=_safe_str(item.get("system"), "unknown"),
            critical=_bool_value(
                item.get("critical", False),
                warnings=warnings,
                context=f"groupstatus {name}.critical",
            ),
            check_type=_safe_check_type(
                item.get("type", CheckType.ICMP.value),
                warnings=warnings,
                context=f"groupstatus {name}.type",
            ),
            min_count=_safe_int(
                _pick(item, "min_count", "minCount", 0),
                warnings=warnings,
                context=f"groupstatus {name}.min_count",
            ),
            failure_grace=_safe_int(
                _pick(item, "failure_grace", "failGrace", 0),
                warnings=warnings,
                context=f"groupstatus {name}.failure_grace",
            ),
            last_up=_safe_str(_pick(item, "last_up", "lastUp", "unknown")),
            last_checked=_safe_str(_pick(item, "last_checked", "lastChecked", "unknown")),
            instance_count=_safe_int(
                _pick(item, "instance_count", "instanceCount", 0),
                warnings=warnings,
                context=f"groupstatus {name}.instance_count",
            ),
            status=_safe_status(
                item.get("status", Status.UNKNOWN.value),
                warnings=warnings,
                context=f"groupstatus {name}.status",
            ),
        )
    return result


def load_previous_groups(config: EffectiveConfig) -> dict[str, GroupState]:
    return _load_previous_groups(config, [])


def _load_previous_systems(config: EffectiveConfig, warnings: list[str]) -> dict[str, SystemState]:
    payload = _safe_json(config.reports.systems, "sysstatus", warnings)
    result: dict[str, SystemState] = {}
    for item in _items(payload, "systems", "sysstatus", warnings):
        name = _safe_str(item.get("name"), "")
        if not name:
            warnings.append("sysstatus: previous state system record missing name; ignoring")
            continue
        result[name] = SystemState(
            name=name,
            last_up=_safe_str(_pick(item, "last_up", "lastUp", "unknown")),
            last_checked=_safe_str(_pick(item, "last_checked", "lastChecked", "unknown")),
            failure_count=_safe_int(
                _pick(item, "failure_count", "failureCount", 0),
                warnings=warnings,
                context=f"sysstatus {name}.failure_count",
            ),
            status=_safe_status(
                item.get("status", Status.UNKNOWN.value),
                warnings=warnings,
                context=f"sysstatus {name}.status",
            ),
        )
    return result


def load_previous_systems(config: EffectiveConfig) -> dict[str, SystemState]:
    return _load_previous_systems(config, [])


def load_previous_state(config: EffectiveConfig) -> PreviousState:
    warnings: list[str] = []
    hosts = _load_previous_hosts(config, warnings)
    groups = _load_previous_groups(config, warnings)
    systems = _load_previous_systems(config, warnings)
    return PreviousState(hosts=hosts, groups=groups, systems=systems, warnings=tuple(warnings))
