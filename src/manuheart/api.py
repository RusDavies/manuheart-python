"""Public Manuheart library API."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from manuheart.config import load_config as _load_config
from manuheart.health import run_health_cycle
from manuheart.models import (
    CheckResult,
    CheckRunResult,
    CheckType,
    ConfigFormat,
    EffectiveConfig,
    GroupDefinition,
    GroupState,
    HostDefinition,
    HostState,
    LoadedConfiguration,
    ReportDestinations,
    Status,
    SystemState,
    ValidationResult,
)
from manuheart.reporting import write_reports as _write_reports
from manuheart.state import load_previous_groups, load_previous_hosts, load_previous_systems

__all__ = [
    "CheckResult",
    "CheckRunResult",
    "CheckType",
    "ConfigFormat",
    "EffectiveConfig",
    "GroupDefinition",
    "GroupState",
    "HostDefinition",
    "HostState",
    "LoadedConfiguration",
    "ReportDestinations",
    "Status",
    "SystemState",
    "ValidationResult",
    "load_config",
    "run_check",
    "run_check_from_config",
    "validate_config",
    "write_reports",
    "run_daemon",
]


def load_config(
    path: str | Path,
    *,
    config_format: ConfigFormat | str = ConfigFormat.AUTO,
    overrides: Mapping[str, Any] | None = None,
) -> LoadedConfiguration:
    """Load and normalize a Manuheart configuration file."""

    return _load_config(Path(path), config_format=ConfigFormat(config_format), overrides=overrides)


def validate_config(
    path: str | Path,
    *,
    config_format: ConfigFormat | str = ConfigFormat.AUTO,
    overrides: Mapping[str, Any] | None = None,
) -> ValidationResult:
    """Validate a Manuheart configuration file without running checks."""

    try:
        loaded = load_config(path, config_format=config_format, overrides=overrides)
    except Exception as exc:  # noqa: BLE001 - public boundary reports structured validation
        return ValidationResult(valid=False, errors=(str(exc),))
    return ValidationResult(valid=True, warnings=loaded.warnings)


def run_check(
    config: LoadedConfiguration,
    *,
    checkers: Mapping[CheckType, Any] | None = None,
    clock: Any | None = None,
) -> CheckRunResult:
    """Run one health-check cycle using a loaded configuration."""

    return run_health_cycle(
        config,
        checkers=checkers,
        clock=clock,
        previous_hosts=load_previous_hosts(config.effective),
        previous_groups=load_previous_groups(config.effective),
        previous_systems=load_previous_systems(config.effective),
    )


def run_check_from_config(
    path: str | Path,
    *,
    config_format: ConfigFormat | str = ConfigFormat.AUTO,
    overrides: Mapping[str, Any] | None = None,
    checkers: Mapping[CheckType, Any] | None = None,
    clock: Any | None = None,
) -> CheckRunResult:
    """Load configuration and run one health-check cycle."""

    return run_check(
        load_config(path, config_format=config_format, overrides=overrides),
        checkers=checkers,
        clock=clock,
    )


def write_reports(result: CheckRunResult, destinations: ReportDestinations | None = None) -> None:
    """Write host, group, and system JSON reports atomically."""

    _write_reports(result, destinations=destinations)


def run_daemon(
    config: LoadedConfiguration,
    *,
    checkers: Mapping[CheckType, Any] | None = None,
    clock: Any | None = None,
    sleep: Any | None = None,
    max_cycles: int | None = None,
) -> int:
    """Run repeated check cycles. Primarily used by the CLI daemon adapter."""

    import time

    sleeper = sleep or time.sleep
    cycles = 0
    while True:
        result = run_check(config, checkers=checkers, clock=clock)
        write_reports(result)
        cycles += 1
        if max_cycles is not None and cycles >= max_cycles:
            return cycles
        sleeper(config.effective.check_period)
