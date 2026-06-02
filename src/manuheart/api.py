"""Public Manuheart library API."""

from __future__ import annotations

from datetime import UTC, datetime
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
    PreviousStateSnapshot,
    ReportDestinations,
    SleepFunction,
    Status,
    SystemState,
    ValidationResult,
)
from manuheart.reporting import write_reports as _write_reports
from manuheart.state import PreviousState
from manuheart.state import load_previous_state as _load_previous_state

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
    "PreviousState",
    "PreviousStateSnapshot",
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


def _log_event(config: EffectiveConfig, level: int, message: str) -> None:
    if config.log_file is None or config.log_level < level:
        return
    config.log_file.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).isoformat()
    with config.log_file.open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} {message}\n")


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
    previous_state: PreviousStateSnapshot | None = None,
    load_previous: bool = True,
) -> CheckRunResult:
    """Run one health-check cycle using a loaded configuration."""

    if previous_state is not None:
        previous = previous_state
    elif load_previous:
        previous = _load_previous_state(config.effective)
    else:
        previous = PreviousStateSnapshot()
    result = run_health_cycle(
        config,
        checkers=checkers,
        clock=clock,
        previous_hosts=previous.hosts,
        previous_groups=previous.groups,
        previous_systems=previous.systems,
        previous_warnings=previous.warnings,
    )
    _log_event(
        config.effective,
        2,
        f"check run {result.run_id} completed: "
        f"systems={len(result.systems)} warnings={len(result.warnings)}",
    )
    return result


def run_check_from_config(
    path: str | Path,
    *,
    config_format: ConfigFormat | str = ConfigFormat.AUTO,
    overrides: ConfigOverridesInput | None = None,
    checkers: CheckerMap | None = None,
    clock: ClockSource | None = None,
    previous_state: PreviousStateSnapshot | None = None,
    load_previous: bool = True,
) -> CheckRunResult:
    """Load configuration and run one health-check cycle."""

    return run_check(
        load_config(path, config_format=config_format, overrides=overrides),
        checkers=checkers,
        clock=clock,
        previous_state=previous_state,
        load_previous=load_previous,
    )


def write_reports(result: CheckRunResult, destinations: ReportDestinations | None = None) -> None:
    """Write host, group, and system JSON reports atomically."""

    _write_reports(result, destinations=destinations)
    _log_event(result.config.effective, 2, f"check run {result.run_id} reports written")


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
    _log_event(config.effective, 2, "daemon starting")
    emit("daemon starting")
    try:
        while True:
            result = run_check(config, checkers=checkers, clock=clock)
            write_reports(result)
            cycles += 1
            _log_event(config.effective, 2, f"daemon cycle {cycles} completed")
            emit(f"daemon cycle {cycles} completed")
            if max_cycles is not None and cycles >= max_cycles:
                _log_event(config.effective, 2, f"daemon stopped after {cycles} cycle(s)")
                emit(f"daemon stopped after {cycles} cycle{'s' if cycles != 1 else ''}")
                return cycles
            sleeper(config.effective.check_period)
    except KeyboardInterrupt:
        _log_event(config.effective, 2, f"daemon stopped after {cycles} cycle(s)")
        emit(f"daemon stopped after {cycles} cycle{'s' if cycles != 1 else ''}")
        return cycles
