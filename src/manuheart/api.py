"""Public Manuheart library API."""

from __future__ import annotations

from pathlib import Path

from manuheart.config import load_config as _load_config
from manuheart.health import run_health_cycle
from manuheart.models import (
    Checker,
    CheckerMap,
    CheckResult,
    CheckRunResult,
    CheckType,
    ClockSource,
    ConfigFormat,
    ConfigOverrides,
    ConfigOverridesInput,
    DaemonEventCallback,
    EffectiveConfig,
    GroupDefinition,
    GroupState,
    HostDefinition,
    HostState,
    LoadedConfiguration,
    ReportDestinations,
    SleepFunction,
    Status,
    SystemState,
    ValidationResult,
)
from manuheart.reporting import write_reports as _write_reports
from manuheart.state import load_previous_state

__all__ = [
    "CheckResult",
    "CheckRunResult",
    "CheckType",
    "Checker",
    "CheckerMap",
    "ClockSource",
    "ConfigFormat",
    "ConfigOverrides",
    "ConfigOverridesInput",
    "DaemonEventCallback",
    "EffectiveConfig",
    "GroupDefinition",
    "GroupState",
    "HostDefinition",
    "HostState",
    "LoadedConfiguration",
    "ReportDestinations",
    "SleepFunction",
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
    overrides: ConfigOverridesInput | None = None,
) -> LoadedConfiguration:
    """Load and normalize a Manuheart configuration file."""

    return _load_config(Path(path), config_format=ConfigFormat(config_format), overrides=overrides)


def validate_config(
    path: str | Path,
    *,
    config_format: ConfigFormat | str = ConfigFormat.AUTO,
    overrides: ConfigOverridesInput | None = None,
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
    checkers: CheckerMap | None = None,
    clock: ClockSource | None = None,
) -> CheckRunResult:
    """Run one health-check cycle using a loaded configuration."""

    previous = load_previous_state(config.effective)
    return run_health_cycle(
        config,
        checkers=checkers,
        clock=clock,
        previous_hosts=previous.hosts,
        previous_groups=previous.groups,
        previous_systems=previous.systems,
        previous_warnings=previous.warnings,
    )


def run_check_from_config(
    path: str | Path,
    *,
    config_format: ConfigFormat | str = ConfigFormat.AUTO,
    overrides: ConfigOverridesInput | None = None,
    checkers: CheckerMap | None = None,
    clock: ClockSource | None = None,
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
    checkers: CheckerMap | None = None,
    clock: ClockSource | None = None,
    sleep: SleepFunction | None = None,
    max_cycles: int | None = None,
    on_event: DaemonEventCallback | None = None,
) -> int:
    """Run repeated check cycles. Primarily used by the CLI daemon adapter."""

    import time

    sleeper = sleep or time.sleep
    cycles = 0
    emit = on_event or (lambda _message: None)
    emit("daemon starting")
    try:
        while True:
            result = run_check(config, checkers=checkers, clock=clock)
            write_reports(result)
            cycles += 1
            emit(f"daemon cycle {cycles} completed")
            if max_cycles is not None and cycles >= max_cycles:
                emit(f"daemon stopped after {cycles} cycle{'s' if cycles != 1 else ''}")
                return cycles
            sleeper(config.effective.check_period)
    except KeyboardInterrupt:
        emit(f"daemon stopped after {cycles} cycle{'s' if cycles != 1 else ''}")
        return cycles
