"""Pure-ish health engine for Manuheart."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from manuheart.checkers import default_checkers
from manuheart.models import (
    CheckResult,
    CheckRunResult,
    CheckType,
    GroupDefinition,
    GroupState,
    HostDefinition,
    HostState,
    LoadedConfiguration,
    Status,
    SystemState,
)


def _now(clock: Any | None = None) -> str:
    if clock is None:
        return datetime.now(UTC).isoformat()
    value = clock() if callable(clock) else clock.now()
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def update_host_state(
    previous: HostState | None,
    definition: HostDefinition,
    group: GroupDefinition,
    result: CheckResult,
    now: str,
) -> HostState:
    base = previous or HostState(name=definition.name, group=definition.group, url=definition.url)
    if result.healthy:
        return HostState(
            name=definition.name,
            group=definition.group,
            url=definition.url,
            last_up=now,
            last_checked=now,
            fail_count=0,
            status=Status.UP,
        )

    fail_count = base.fail_count + 1
    status = base.status
    if base.status == Status.DOWN:
        status = Status.DOWN
    elif group.failure_grace >= 0 and fail_count > group.failure_grace:
        status = Status.DOWN
    return HostState(
        name=definition.name,
        group=definition.group,
        url=definition.url,
        last_up=base.last_up or "unknown",
        last_checked=now,
        fail_count=fail_count,
        status=status,
    )


def rollup_groups(
    group_defs: Mapping[str, GroupDefinition],
    host_states: Mapping[str, HostState],
    previous: Mapping[str, GroupState] | None,
    now: str,
) -> dict[str, GroupState]:
    previous = previous or {}
    result: dict[str, GroupState] = {}
    for name in sorted(group_defs):
        definition = group_defs[name]
        prior = previous.get(name)
        group_hosts = [host for host in host_states.values() if host.group == name]
        up_count = sum(1 for host in group_hosts if host.status == Status.UP)
        unknown_count = sum(1 for host in group_hosts if host.status == Status.UNKNOWN)
        if definition.min_count == 0:
            status = Status.UP
            last_up = now
        elif up_count >= definition.min_count:
            status = Status.UP
            last_up = now
        elif up_count + unknown_count >= definition.min_count:
            status = Status.UNKNOWN
            last_up = prior.last_up if prior else "unknown"
        else:
            status = Status.DOWN
            last_up = prior.last_up if prior else "unknown"
        result[name] = GroupState(
            name=definition.name,
            system=definition.system,
            critical=definition.critical,
            check_type=definition.check_type,
            min_count=definition.min_count,
            failure_grace=definition.failure_grace,
            last_up=last_up,
            last_checked=now,
            instance_count=up_count,
            status=status,
        )
    return result


def rollup_systems(
    group_states: Mapping[str, GroupState],
    previous: Mapping[str, SystemState] | None,
    now: str,
) -> dict[str, SystemState]:
    previous = previous or {}
    systems = sorted({group.system for group in group_states.values()})
    result: dict[str, SystemState] = {}
    for system in systems:
        groups = [group for group in group_states.values() if group.system == system]
        if any(g.critical and g.status == Status.DOWN for g in groups):
            status = Status.DOWN
        elif any(g.critical and g.status == Status.UNKNOWN for g in groups):
            status = Status.UNKNOWN
        else:
            status = Status.UP
        prior = previous.get(system)
        if status == Status.UP:
            failure_count = 0
            last_up = now
        else:
            failure_count = (prior.failure_count if prior else 0) + 1
            last_up = prior.last_up if prior else "unknown"
        result[system] = SystemState(
            name=system,
            last_up=last_up,
            last_checked=now,
            failure_count=failure_count,
            status=status,
        )
    return result


def run_health_cycle(
    config: LoadedConfiguration,
    *,
    checkers: Mapping[CheckType, Any] | None = None,
    clock: Any | None = None,
    previous_hosts: Mapping[str, HostState] | None = None,
    previous_groups: Mapping[str, GroupState] | None = None,
    previous_systems: Mapping[str, SystemState] | None = None,
) -> CheckRunResult:
    now = _now(clock)
    checker_map = checkers or default_checkers(config.effective)
    host_states: dict[str, HostState] = {}
    try:
        for key in sorted(config.hosts):
            host = config.hosts[key]
            group = config.groups[host.group]
            checker = checker_map[group.check_type]
            check_result = checker.check(host, group)
            host_states[key] = update_host_state(
                (previous_hosts or {}).get(key), host, group, check_result, now
            )
    finally:
        if checkers is None:
            seen: set[int] = set()
            for checker in checker_map.values():
                checker_id = id(checker)
                if checker_id in seen:
                    continue
                seen.add(checker_id)
                close = getattr(checker, "close", None)
                if close is not None:
                    close()
    group_states = rollup_groups(config.groups, host_states, previous_groups, now)
    system_states = rollup_systems(group_states, previous_systems, now)
    return CheckRunResult(
        config=config,
        hosts=host_states,
        groups=group_states,
        systems=system_states,
        warnings=config.warnings,
    )
