"""Configuration loaders for JSON and YAML Manuheart config."""

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
    ConfigOverridesInput,
    EffectiveConfig,
    GroupDefinition,
    HostDefinition,
    HttpCheckSettings,
    IcmpCheckSettings,
    LoadedConfiguration,
    ReportDestinations,
)


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


def _int_at_least(value: Any, name: str, minimum: int) -> int:
    parsed = _int(value, name)
    if parsed < minimum:
        raise ConfigError(f"{name} must be >= {minimum}")
    return parsed


def _int_greater_than(value: Any, name: str, minimum: int) -> int:
    parsed = _int(value, name)
    if parsed <= minimum:
        raise ConfigError(f"{name} must be > {minimum}")
    return parsed


def _float_greater_than(value: Any, name: str, minimum: float) -> float:
    parsed = _float(value, name)
    if parsed <= minimum:
        raise ConfigError(f"{name} must be > {minimum:g}")
    return parsed


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ConfigError(f"{name} must be an object")
    return value


def _validate_keys(item: Mapping[str, Any], allowed: set[str], path: str) -> None:
    unknown = sorted(set(item) - allowed)
    if unknown:
        raise ConfigError(f"{path} has unknown key(s): {', '.join(unknown)}")


def _list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ConfigError(f"{name} must be a list")
    return value


def _required(item: Mapping[str, Any], field: str, path: str) -> Any:
    value = item.get(field)
    if value is None or value == "":
        raise ConfigError(f"{path}.{field} is required")
    return value


def _http_method(value: Any, name: str) -> str:
    method = str(value).strip().upper()
    if method not in {"HEAD", "GET"}:
        raise ConfigError(f"{name} must be HEAD or GET")
    return method


def _run_mode(value: Any, name: str) -> str:
    mode = str(value).strip().lower()
    if mode not in {"once", "daemon"}:
        raise ConfigError(f"{name} must be once or daemon")
    return mode


def _resolve_path(value: str | Path | None, base: Path | None = None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if not path.is_absolute() and base is not None:
        path = base / path
    return path


def _resolve_status_path(value: str | Path | None, var_dir: Path, default_name: str) -> Path:
    if value is None:
        return var_dir / "status" / default_name
    path = Path(value)
    if path.is_absolute():
        return path
    return var_dir / path


def _optional_path(value: object, name: str) -> Path | None:
    if value is None:
        return None
    if isinstance(value, str | Path):
        return Path(value)
    raise ConfigError(f"{name} must be a path string")


def _optional_int_at_least(value: object, name: str, minimum: int) -> int | None:
    if value is None:
        return None
    return _int_at_least(value, name, minimum)


def _optional_int_greater_than(value: object, name: str, minimum: int) -> int | None:
    if value is None:
        return None
    return _int_greater_than(value, name, minimum)


def _optional_run_mode(value: object, name: str) -> str | None:
    if value is None:
        return None
    return _run_mode(value, name)


def _infer_format(path: Path, requested: ConfigFormat) -> ConfigFormat:
    if requested != ConfigFormat.AUTO:
        return requested
    suffix = path.suffix.lower()
    if suffix == ".json":
        return ConfigFormat.JSON
    if suffix in {".yaml", ".yml"}:
        return ConfigFormat.YAML
    raise UnsupportedConfigFormatError(
        f"unsupported config format for {path}; use .json or .yaml/.yml"
    )


def normalize_overrides(overrides: ConfigOverridesInput | None) -> ConfigOverrides:
    if overrides is None:
        return ConfigOverrides()
    if isinstance(overrides, ConfigOverrides):
        return overrides
    allowed = {field for field in ConfigOverrides.__dataclass_fields__}
    unknown = set(overrides) - allowed
    if unknown:
        raise ConfigError(f"unknown config override(s): {', '.join(sorted(unknown))}")
    values = dict(overrides)
    return ConfigOverrides(
        var_dir=_optional_path(values.get("var_dir"), "override.var_dir"),
        log_file=_optional_path(values.get("log_file"), "override.log_file"),
        log_level=_optional_int_at_least(values.get("log_level"), "override.log_level", 0),
        check_period=_optional_int_greater_than(
            values.get("check_period"), "override.check_period", 0
        ),
        run_mode=_optional_run_mode(values.get("run_mode"), "override.run_mode"),
        host_status_file=_optional_path(
            values.get("host_status_file"), "override.host_status_file"
        ),
        group_status_file=_optional_path(
            values.get("group_status_file"), "override.group_status_file"
        ),
        system_status_file=_optional_path(
            values.get("system_status_file"), "override.system_status_file"
        ),
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
        reports=reports,
    )


def semantic_warnings(
    config: EffectiveConfig,
    groups: Mapping[str, GroupDefinition],
    hosts: Mapping[str, HostDefinition],
    *,
    base_run_mode: str | None = None,
    overrides: ConfigOverrides | None = None,
) -> tuple[str, ...]:
    warnings: list[str] = []
    if not groups:
        warnings.append("configuration defines no groups")
    if not hosts:
        warnings.append("configuration defines no hosts")
    for group_name, group in sorted(groups.items()):
        host_count = sum(1 for host in hosts.values() if host.group == group_name)
        if host_count == 0 and group.min_count > 0:
            warnings.append(f"group {group_name!r} has no hosts")
        if group.min_count > host_count:
            warnings.append(
                f"group {group_name!r} min_count {group.min_count} exceeds host count {host_count}"
            )
    for system in sorted({group.system for group in groups.values()}):
        system_groups = [group for group in groups.values() if group.system == system]
        if not any(group.critical for group in system_groups):
            warnings.append(f"system {system!r} has no critical groups")
    if overrides and overrides.run_mode is not None and base_run_mode != config.run_mode:
        warnings.append(
            f"runtime.run_mode {base_run_mode!r} overridden by API/CLI to {config.run_mode!r}"
        )
    return tuple(warnings)


def _structured_definitions(
    data: Mapping[str, Any],
) -> tuple[dict[str, GroupDefinition], dict[str, HostDefinition]]:
    groups: dict[str, GroupDefinition] = {}
    for idx, raw_item in enumerate(_list(data.get("groups", []), "groups")):
        path = f"groups[{idx}]"
        item = _mapping(raw_item, path)
        _validate_keys(
            item,
            {"name", "system", "critical", "type", "min_count", "failure_grace"},
            path,
        )
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
        group_definition = GroupDefinition(
            name=name,
            system=system,
            critical=critical,
            check_type=check_type,
            min_count=_int_at_least(
                _required(item, "min_count", path), f"{path}.min_count", 0
            ),
            failure_grace=_int_at_least(
                _required(item, "failure_grace", path), f"{path}.failure_grace", -1
            ),
        )
        if group_definition.name in groups:
            raise ConfigError(f"duplicate group {group_definition.name!r}")
        groups[group_definition.name] = group_definition
    hosts: dict[str, HostDefinition] = {}
    for idx, raw_item in enumerate(_list(data.get("hosts", []), "hosts")):
        path = f"hosts[{idx}]"
        item = _mapping(raw_item, path)
        _validate_keys(item, {"name", "group", "url"}, path)
        host_definition = HostDefinition(
            name=str(_required(item, "name", path)),
            group=str(_required(item, "group", path)),
            url=str(_required(item, "url", path)),
        )
        if host_definition.group not in groups:
            raise ConfigError(f"host {host_definition.key!r} references unknown group")
        if host_definition.key in hosts:
            raise ConfigError(f"duplicate host {host_definition.key!r}")
        if groups[host_definition.group].check_type in {
            CheckType.HTTP,
            CheckType.HTTPS,
        } and not host_definition.url.startswith(("http://", "https://")):
            raise ConfigError(f"{path} URL must start with http:// or https://")
        hosts[host_definition.key] = host_definition
    return groups, hosts


def _effective_from_structured(path: Path, data: Mapping[str, Any]) -> EffectiveConfig:
    path = path.resolve()
    config_dir = path.parent
    _validate_keys(data, {"runtime", "checks", "groups", "hosts"}, "top-level config")
    runtime = _mapping(data.get("runtime", {}), "runtime")
    checks = _mapping(data.get("checks", {}), "checks")
    _validate_keys(
        runtime,
        {"var_dir", "log_file", "log_level", "check_period", "run_mode", "status_files"},
        "runtime",
    )
    _validate_keys(checks, {"http", "icmp"}, "checks")
    http = _mapping(checks.get("http", {}), "checks.http")
    icmp = _mapping(checks.get("icmp", {}), "checks.icmp")
    _validate_keys(
        http,
        {"connect_timeout", "max_time", "method", "fallback_to_get"},
        "checks.http",
    )
    _validate_keys(icmp, {"timeout", "count", "privileged"}, "checks.icmp")
    var_dir = _resolve_path(runtime.get("var_dir", "var/manuheart"), config_dir) or Path(
        "var/manuheart"
    )
    status_files = _mapping(runtime.get("status_files", {}), "runtime.status_files")
    _validate_keys(status_files, {"hosts", "groups", "systems"}, "runtime.status_files")
    return EffectiveConfig(
        config_file=path,
        config_dir=config_dir,
        var_dir=var_dir,
        log_file=_resolve_path(runtime.get("log_file"), config_dir),
        log_level=_int_at_least(runtime.get("log_level", 3), "runtime.log_level", 0),
        check_period=_int_greater_than(runtime.get("check_period", 3), "runtime.check_period", 0),
        run_mode=_run_mode(runtime.get("run_mode", "once"), "runtime.run_mode"),
        reports=ReportDestinations(
            hosts=_resolve_status_path(status_files.get("hosts"), var_dir, "hoststatus"),
            groups=_resolve_status_path(status_files.get("groups"), var_dir, "groupstatus"),
            systems=_resolve_status_path(status_files.get("systems"), var_dir, "sysstatus"),
        ),
        http=HttpCheckSettings(
            connect_timeout=_float_greater_than(
                http.get("connect_timeout", 3), "checks.http.connect_timeout", 0
            ),
            max_time=_float_greater_than(http.get("max_time", 5), "checks.http.max_time", 0),
            method=_http_method(http.get("method", "HEAD"), "checks.http.method"),
            fallback_to_get=_bool(http.get("fallback_to_get", True)),
        ),
        icmp=IcmpCheckSettings(
            timeout=_float_greater_than(icmp.get("timeout", 1), "checks.icmp.timeout", 0),
            count=_int_greater_than(icmp.get("count", 1), "checks.icmp.count", 0),
            privileged=_bool(icmp.get("privileged", False)),
        ),
    )


def _load_json(path: Path, overrides: ConfigOverrides) -> LoadedConfiguration:
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON config: {exc.msg}") from exc
    data = _mapping(data, "top-level config")
    groups, hosts = _structured_definitions(data)
    base_effective = _effective_from_structured(path, data)
    effective = apply_overrides(base_effective, overrides)
    return LoadedConfiguration(
        effective=effective,
        groups=groups,
        hosts=hosts,
        warnings=semantic_warnings(
            effective, groups, hosts, base_run_mode=base_effective.run_mode, overrides=overrides
        ),
    )


def _load_yaml(path: Path, overrides: ConfigOverrides) -> LoadedConfiguration:
    try:
        import yaml
    except ModuleNotFoundError as exc:
        raise UnsupportedConfigFormatError(
            "YAML config requires the optional PyYAML dependency"
        ) from exc
    try:
        data = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML config: {exc}") from exc
    data = _mapping(data, "top-level config")
    groups, hosts = _structured_definitions(data)
    base_effective = _effective_from_structured(path, data)
    effective = apply_overrides(base_effective, overrides)
    return LoadedConfiguration(
        effective=effective,
        groups=groups,
        hosts=hosts,
        warnings=semantic_warnings(
            effective, groups, hosts, base_run_mode=base_effective.run_mode, overrides=overrides
        ),
    )


def load_config(
    path: Path,
    *,
    config_format: ConfigFormat = ConfigFormat.AUTO,
    overrides: ConfigOverridesInput | None = None,
) -> LoadedConfiguration:
    normalized_overrides = normalize_overrides(overrides)
    selected = _infer_format(path, config_format)
    if selected == ConfigFormat.JSON:
        return _load_json(path, normalized_overrides)
    if selected == ConfigFormat.YAML:
        return _load_yaml(path, normalized_overrides)
    raise UnsupportedConfigFormatError(f"unsupported config format: {selected}")
