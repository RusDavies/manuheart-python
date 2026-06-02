"""Configuration loaders for legacy, JSON, and YAML Manuheart config."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

from manuheart.errors import ConfigError, UnsupportedConfigFormatError
from manuheart.models import (
    CheckType,
    ConfigFormat,
    ConfigOverrides,
    EffectiveConfig,
    GroupDefinition,
    HostDefinition,
    HttpCheckSettings,
    IcmpCheckSettings,
    LoadedConfiguration,
    ReportDestinations,
)

_CONFIG_KEYS = {
    "CONFIGDIR",
    "CONFIGFILE",
    "VARDIR",
    "LOGFILE",
    "LOGLEVEL",
    "CHECKPERIOD",
    "RUNMODE",
    "GROUPFILE",
    "HOSTFILE",
    "HOSTSTATUSOUTFILE",
    "GROUPSTATUSOUTFILE",
    "SYSSTATUSOUTFILE",
}


def _strip_comment(line: str) -> str:
    stripped = line.lstrip()
    if stripped.startswith("#"):
        return ""
    for idx, char in enumerate(line):
        if char == "#" and idx > 0 and line[idx - 1].isspace():
            return line[:idx]
    return line


def _split_fields(line: str) -> list[str]:
    return [part.strip() for part in line.split("|")]


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"yes", "true", "1"}:
        return True
    if normalized in {"no", "false", "0"}:
        return False
    raise ConfigError(f"invalid boolean value: {value!r}")


def _int(value: Any, name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"invalid integer for {name}: {value!r}") from exc


def _float(value: Any, name: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"invalid number for {name}: {value!r}") from exc


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ConfigError(f"{name} must be an object")
    return value


def _list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ConfigError(f"{name} must be a list")
    return value


def _required(item: Mapping[str, Any], field: str, path: str) -> Any:
    value = item.get(field)
    if value is None or value == "":
        raise ConfigError(f"{path}.{field} is required")
    return value


def _expand(value: str, macros: Mapping[str, Path]) -> str:
    result = str(value).strip().strip('"').strip("'")
    for key, replacement in macros.items():
        result = result.replace(f"_{key}_", str(replacement))
        result = result.replace(f"{{{key}}}", str(replacement))
    return result


def _resolve_path(value: str | Path | None, base: Path | None = None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if not path.is_absolute() and base is not None:
        path = base / path
    return path


def _infer_format(path: Path, requested: ConfigFormat) -> ConfigFormat:
    if requested != ConfigFormat.AUTO:
        return requested
    suffix = path.suffix.lower()
    if suffix == ".json":
        return ConfigFormat.JSON
    if suffix in {".yaml", ".yml"}:
        return ConfigFormat.YAML
    return ConfigFormat.LEGACY


def normalize_overrides(overrides: Mapping[str, Any] | ConfigOverrides | None) -> ConfigOverrides:
    if overrides is None:
        return ConfigOverrides()
    if isinstance(overrides, ConfigOverrides):
        return overrides
    allowed = {field for field in ConfigOverrides.__dataclass_fields__}
    unknown = set(overrides) - allowed
    if unknown:
        raise ConfigError(f"unknown config override(s): {', '.join(sorted(unknown))}")
    return ConfigOverrides(
        **{
            key: Path(value) if key.endswith(("dir", "file")) and value is not None else value
            for key, value in overrides.items()
        }
    )


def apply_overrides(config: EffectiveConfig, overrides: ConfigOverrides) -> EffectiveConfig:
    var_dir = overrides.var_dir or config.var_dir
    reports = ReportDestinations(
        hosts=overrides.host_status_file or config.reports.hosts,
        groups=overrides.group_status_file or config.reports.groups,
        systems=overrides.system_status_file or config.reports.systems,
    )
    return replace(
        config,
        var_dir=var_dir,
        log_file=overrides.log_file or config.log_file,
        log_level=overrides.log_level if overrides.log_level is not None else config.log_level,
        check_period=(
            overrides.check_period if overrides.check_period is not None else config.check_period
        ),
        run_mode=overrides.run_mode or config.run_mode,
        group_file=overrides.group_file or config.group_file,
        host_file=overrides.host_file or config.host_file,
        reports=reports,
    )


def _parse_groups(path: Path) -> tuple[dict[str, GroupDefinition], list[str]]:
    warnings: list[str] = []
    groups: dict[str, GroupDefinition] = {}
    for line_no, raw in enumerate(path.read_text().splitlines(), start=1):
        line = _strip_comment(raw).strip()
        if not line:
            continue
        fields = _split_fields(line)
        if len(fields) != 6:
            warnings.append(f"{path}:{line_no}: expected 6 group fields, got {len(fields)}")
            continue
        name, system, critical, check_type, min_count, failure_grace = fields
        if not name or not system:
            warnings.append(f"{path}:{line_no}: group and system are required")
            continue
        if name in groups:
            warnings.append(f"{path}:{line_no}: duplicate group {name!r} ignored")
            continue
        try:
            groups[name] = GroupDefinition(
                name=name,
                system=system,
                critical=_bool(critical),
                check_type=CheckType(check_type.lower()),
                min_count=_int(min_count, "min_count"),
                failure_grace=_int(failure_grace, "failure_grace"),
            )
        except (ConfigError, ValueError) as exc:
            warnings.append(f"{path}:{line_no}: {exc}")
    return groups, warnings


def _parse_hosts(
    path: Path, groups: Mapping[str, GroupDefinition]
) -> tuple[dict[str, HostDefinition], list[str]]:
    warnings: list[str] = []
    hosts: dict[str, HostDefinition] = {}
    for line_no, raw in enumerate(path.read_text().splitlines(), start=1):
        line = _strip_comment(raw).strip()
        if not line:
            continue
        fields = _split_fields(line)
        if len(fields) != 3:
            warnings.append(f"{path}:{line_no}: expected 3 host fields, got {len(fields)}")
            continue
        name, group, url = fields
        key = f"{group}/{name}"
        if not name or not group or not url:
            warnings.append(f"{path}:{line_no}: host, group, and url are required")
            continue
        if group not in groups:
            warnings.append(f"{path}:{line_no}: unknown group {group!r} ignored")
            continue
        if key in hosts:
            warnings.append(f"{path}:{line_no}: duplicate host {key!r} ignored")
            continue
        if groups[group].check_type in {CheckType.HTTP, CheckType.HTTPS} and not url.startswith(
            ("http://", "https://")
        ):
            warnings.append(f"{path}:{line_no}: HTTP host {key!r} has invalid URL")
            continue
        hosts[key] = HostDefinition(name=name, group=group, url=url)
    return hosts, warnings


def _structured_definitions(
    data: Mapping[str, Any],
) -> tuple[dict[str, GroupDefinition], dict[str, HostDefinition]]:
    groups: dict[str, GroupDefinition] = {}
    for idx, raw_item in enumerate(_list(data.get("groups", []), "groups")):
        path = f"groups[{idx}]"
        item = _mapping(raw_item, path)
        name = str(_required(item, "name", path))
        system = str(_required(item, "system", path))
        critical = _bool(_required(item, "critical", path))
        check_type_value = str(_required(item, "type", path)).lower()
        try:
            check_type = CheckType(check_type_value)
        except ValueError as exc:
            raise ConfigError(
                f"{path}.type has unsupported check type: {check_type_value!r}"
            ) from exc
        definition = GroupDefinition(
            name=name,
            system=system,
            critical=critical,
            check_type=check_type,
            min_count=_int(_required(item, "min_count", path), f"{path}.min_count"),
            failure_grace=_int(
                _required(item, "failure_grace", path), f"{path}.failure_grace"
            ),
        )
        if definition.name in groups:
            raise ConfigError(f"duplicate group {definition.name!r}")
        groups[definition.name] = definition
    hosts: dict[str, HostDefinition] = {}
    for idx, raw_item in enumerate(_list(data.get("hosts", []), "hosts")):
        path = f"hosts[{idx}]"
        item = _mapping(raw_item, path)
        definition = HostDefinition(
            name=str(_required(item, "name", path)),
            group=str(_required(item, "group", path)),
            url=str(_required(item, "url", path)),
        )
        if definition.group not in groups:
            raise ConfigError(f"host {definition.key!r} references unknown group")
        if definition.key in hosts:
            raise ConfigError(f"duplicate host {definition.key!r}")
        if groups[definition.group].check_type in {
            CheckType.HTTP,
            CheckType.HTTPS,
        } and not definition.url.startswith(("http://", "https://")):
            raise ConfigError(f"{path} URL must start with http:// or https://")
        hosts[definition.key] = definition
    return groups, hosts


def _effective_from_structured(path: Path, data: Mapping[str, Any]) -> EffectiveConfig:
    path = path.resolve()
    config_dir = path.parent
    runtime = _mapping(data.get("runtime", {}), "runtime")
    checks = _mapping(data.get("checks", {}), "checks")
    http = _mapping(checks.get("http", {}), "checks.http")
    icmp = _mapping(checks.get("icmp", {}), "checks.icmp")
    var_dir = _resolve_path(runtime.get("var_dir", "var/manuheart"), config_dir) or Path(
        "var/manuheart"
    )
    status_files = _mapping(runtime.get("status_files", {}), "runtime.status_files")
    return EffectiveConfig(
        config_file=path,
        config_dir=config_dir,
        var_dir=var_dir,
        log_file=_resolve_path(runtime.get("log_file"), config_dir),
        log_level=_int(runtime.get("log_level", 3), "log_level"),
        check_period=_int(runtime.get("check_period", 3), "check_period"),
        run_mode=str(runtime.get("run_mode", "once")),
        reports=ReportDestinations(
            hosts=_resolve_path(
                status_files.get("hosts", var_dir / "status/hoststatus"), config_dir
            )
            or var_dir / "status/hoststatus",
            groups=_resolve_path(
                status_files.get("groups", var_dir / "status/groupstatus"), config_dir
            )
            or var_dir / "status/groupstatus",
            systems=_resolve_path(
                status_files.get("systems", var_dir / "status/sysstatus"), config_dir
            )
            or var_dir / "status/sysstatus",
        ),
        http=HttpCheckSettings(
            connect_timeout=_float(http.get("connect_timeout", 3), "checks.http.connect_timeout"),
            max_time=_float(http.get("max_time", 5), "checks.http.max_time"),
        ),
        icmp=IcmpCheckSettings(
            timeout=_float(icmp.get("timeout", 1), "checks.icmp.timeout"),
            count=_int(icmp.get("count", 1), "icmp.count"),
            privileged=_bool(icmp.get("privileged", False)),
        ),
    )


def _load_legacy(path: Path, overrides: ConfigOverrides) -> LoadedConfiguration:
    path = path.resolve()
    config_dir = path.parent
    macros: dict[str, Path] = {"CONFIGDIR": config_dir, "CONFIGFILE": path}
    values: dict[str, str] = {"CONFIGDIR": str(config_dir), "CONFIGFILE": str(path)}
    for raw in path.read_text().splitlines():
        line = _strip_comment(raw).strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key not in _CONFIG_KEYS:
            continue
        macros = {
            **macros,
            **{k: Path(v) for k, v in values.items() if k.endswith(("DIR", "FILE"))},
        }
        values[key] = _expand(value, macros)
        if key.endswith(("DIR", "FILE")):
            macros[key] = Path(values[key])
    var_dir = _resolve_path(values.get("VARDIR", "var/manuheart"), config_dir) or Path(
        "var/manuheart"
    )
    group_file = overrides.group_file or _resolve_path(
        values.get("GROUPFILE", config_dir / "groups"), config_dir
    )
    host_file = overrides.host_file or _resolve_path(
        values.get("HOSTFILE", config_dir / "hosts"), config_dir
    )
    effective = EffectiveConfig(
        config_file=path,
        config_dir=config_dir,
        var_dir=var_dir,
        log_file=_resolve_path(values.get("LOGFILE"), config_dir),
        log_level=_int(values.get("LOGLEVEL", 3), "LOGLEVEL"),
        check_period=_int(values.get("CHECKPERIOD", 3), "CHECKPERIOD"),
        run_mode=values.get("RUNMODE", "once"),
        group_file=group_file,
        host_file=host_file,
        reports=ReportDestinations(
            hosts=_resolve_path(
                values.get("HOSTSTATUSOUTFILE", var_dir / "status/hoststatus"), config_dir
            )
            or var_dir / "status/hoststatus",
            groups=_resolve_path(
                values.get("GROUPSTATUSOUTFILE", var_dir / "status/groupstatus"), config_dir
            )
            or var_dir / "status/groupstatus",
            systems=_resolve_path(
                values.get("SYSSTATUSOUTFILE", var_dir / "status/sysstatus"), config_dir
            )
            or var_dir / "status/sysstatus",
        ),
    )
    effective = apply_overrides(effective, overrides)
    if effective.group_file is None or effective.host_file is None:
        raise ConfigError("legacy configuration requires group and host files")
    groups, group_warnings = _parse_groups(effective.group_file)
    hosts, host_warnings = _parse_hosts(effective.host_file, groups)
    return LoadedConfiguration(
        effective=effective,
        groups=groups,
        hosts=hosts,
        warnings=tuple(group_warnings + host_warnings),
    )


def _load_json(path: Path, overrides: ConfigOverrides) -> LoadedConfiguration:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON config: {exc.msg}") from exc
    data = _mapping(data, "top-level config")
    groups, hosts = _structured_definitions(data)
    effective = apply_overrides(_effective_from_structured(path, data), overrides)
    return LoadedConfiguration(effective=effective, groups=groups, hosts=hosts)


def _load_yaml(path: Path, overrides: ConfigOverrides) -> LoadedConfiguration:
    try:
        import yaml  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise UnsupportedConfigFormatError(
            "YAML config requires the optional PyYAML dependency"
        ) from exc
    data = yaml.safe_load(path.read_text()) or {}
    data = _mapping(data, "top-level config")
    groups, hosts = _structured_definitions(data)
    effective = apply_overrides(_effective_from_structured(path, data), overrides)
    return LoadedConfiguration(effective=effective, groups=groups, hosts=hosts)


def load_config(
    path: Path,
    *,
    config_format: ConfigFormat = ConfigFormat.AUTO,
    overrides: Mapping[str, Any] | ConfigOverrides | None = None,
) -> LoadedConfiguration:
    normalized_overrides = normalize_overrides(overrides)
    selected = _infer_format(path, config_format)
    if selected == ConfigFormat.LEGACY:
        return _load_legacy(path, normalized_overrides)
    if selected == ConfigFormat.JSON:
        return _load_json(path, normalized_overrides)
    if selected == ConfigFormat.YAML:
        return _load_yaml(path, normalized_overrides)
    raise UnsupportedConfigFormatError(f"unsupported config format: {selected}")
