"""Domain models for Manuheart."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from enum import StrEnum
from pathlib import Path
from typing import Protocol, TypeAlias


class ConfigFormat(StrEnum):
    AUTO = "auto"
    JSON = "json"
    YAML = "yaml"


class CheckType(StrEnum):
    ICMP = "icmp"
    HTTP = "http"
    HTTPS = "https"


class Status(StrEnum):
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class HttpCheckSettings:
    connect_timeout: float = 3.0
    max_time: float = 5.0
    method: str = "HEAD"
    fallback_to_get: bool = True


@dataclass(frozen=True, slots=True)
class IcmpCheckSettings:
    timeout: float = 1.0
    count: int = 1
    privileged: bool = False


@dataclass(frozen=True, slots=True)
class ReportDestinations:
    hosts: Path
    groups: Path
    systems: Path


@dataclass(frozen=True, slots=True)
class EffectiveConfig:
    config_file: Path | None = None
    config_dir: Path | None = None
    var_dir: Path = Path("var/manuheart")
    log_file: Path | None = None
    log_level: int = 3
    check_period: int = 3
    run_mode: str = "once"
    reports: ReportDestinations = field(
        default_factory=lambda: ReportDestinations(
            hosts=Path("var/manuheart/status/hoststatus"),
            groups=Path("var/manuheart/status/groupstatus"),
            systems=Path("var/manuheart/status/sysstatus"),
        )
    )
    http: HttpCheckSettings = field(default_factory=HttpCheckSettings)
    icmp: IcmpCheckSettings = field(default_factory=IcmpCheckSettings)


@dataclass(frozen=True, slots=True)
class ConfigOverrides:
    var_dir: Path | None = None
    log_file: Path | None = None
    log_level: int | None = None
    check_period: int | None = None
    run_mode: str | None = None
    host_status_file: Path | None = None
    group_status_file: Path | None = None
    system_status_file: Path | None = None


ConfigOverridesInput: TypeAlias = Mapping[str, object] | ConfigOverrides


@dataclass(frozen=True, slots=True)
class GroupDefinition:
    name: str
    system: str
    critical: bool
    check_type: CheckType
    min_count: int
    failure_grace: int


@dataclass(frozen=True, slots=True)
class HostDefinition:
    name: str
    group: str
    url: str

    @property
    def key(self) -> str:
        return f"{self.group}/{self.name}"


@dataclass(frozen=True, slots=True)
class HostState:
    name: str
    group: str
    url: str
    last_up: str = "unknown"
    last_checked: str = "unknown"
    fail_count: int = 0
    status: Status = Status.UNKNOWN
    detail: str = ""

    @property
    def key(self) -> str:
        return f"{self.group}/{self.name}"


@dataclass(frozen=True, slots=True)
class GroupState:
    name: str
    system: str
    critical: bool
    check_type: CheckType
    min_count: int
    failure_grace: int
    last_up: str = "unknown"
    last_checked: str = "unknown"
    instance_count: int = 0
    status: Status = Status.UNKNOWN


@dataclass(frozen=True, slots=True)
class SystemState:
    name: str
    last_up: str = "unknown"
    last_checked: str = "unknown"
    failure_count: int = 0
    status: Status = Status.UNKNOWN


@dataclass(frozen=True, slots=True)
class CheckResult:
    healthy: bool
    detail: str = ""


class Checker(Protocol):
    def check(self, host: HostDefinition, group: GroupDefinition) -> CheckResult: ...


class ClockWithNow(Protocol):
    def now(self) -> object: ...


CheckerMap: TypeAlias = Mapping[CheckType, Checker]
ClockSource: TypeAlias = Callable[[], object] | ClockWithNow
SleepFunction: TypeAlias = Callable[[float], object]
DaemonEventCallback: TypeAlias = Callable[[str], object]


@dataclass(frozen=True, slots=True)
class LoadedConfiguration:
    effective: EffectiveConfig
    groups: dict[str, GroupDefinition]
    hosts: dict[str, HostDefinition]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidationResult:
    valid: bool
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CheckRunResult:
    config: LoadedConfiguration
    hosts: dict[str, HostState]
    groups: dict[str, GroupState]
    systems: dict[str, SystemState]
    warnings: tuple[str, ...] = ()


def with_report_destinations(
    config: EffectiveConfig, reports: ReportDestinations
) -> EffectiveConfig:
    return replace(config, reports=reports)
