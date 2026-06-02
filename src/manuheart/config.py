"""Configuration loaders for legacy, JSON, and YAML Manuheart config."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from manuheart.errors import ConfigError, UnsupportedConfigFormatError
from manuheart.models import (
    CheckType,
    ConfigFormat,
    EffectiveConfig,
    GroupDefinition,
    HostDefinition,
    HttpCheckSettings,
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
    for item in data.get("groups", []):
        definition = GroupDefinition(
            name=str(item["name"]),
            system=str(item["system"]),
            critical=_bool(item["critical"]),
            check_type=CheckType(str(item["type"]).lower()),
            min_count=_int(item["min_count"], "min_count"),
            failure_grace=_int(item["failure_grace"], "failure_grace"),
        )
        if definition.name in groups:
            raise ConfigError(f"duplicate group {definition.name!r}")
        groups[definition.name] = definition
    hosts: dict[str, HostDefinition] = {}
    for item in data.get("hosts", []):
        definition = HostDefinition(
            name=str(item["name"]), group=str(item["group"]), url=str(item["url"])
        )
        if definition.group not in groups:
            raise ConfigError(f"host {definition.key!r} references unknown group")
        if definition.key in hosts:
            raise ConfigError(f"duplicate host {definition.key!r}")
        hosts[definition.key] = definition
    return groups, hosts


def _effective_from_structured(path: Path, data: Mapping[str, Any]) -> EffectiveConfig:
    runtime = data.get("runtime", {}) or {}
    checks = data.get("checks", {}) or {}
    http = (checks.get("http", {}) or {}) if isinstance(checks, Mapping) else {}
    path = path.resolve()
    config_dir = path.parent
    var_dir = _resolve_path(runtime.get("var_dir", "var/manuheart"), config_dir) or Path(
        "var/manuheart"
    )
    status_files = runtime.get("status_files", {}) or {}
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
            connect_timeout=float(http.get("connect_timeout", 3)),
            max_time=float(http.get("max_time", 5)),
        ),
    )


def _load_legacy(path: Path) -> LoadedConfiguration:
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
    macros["VARDIR"] = var_dir
    group_file = _resolve_path(values.get("GROUPFILE", config_dir / "groups"), config_dir)
    host_file = _resolve_path(values.get("HOSTFILE", config_dir / "hosts"), config_dir)
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
    if group_file is None or host_file is None:
        raise ConfigError("legacy configuration requires group and host files")
    groups, group_warnings = _parse_groups(group_file)
    hosts, host_warnings = _parse_hosts(host_file, groups)
    return LoadedConfiguration(
        effective=effective,
        groups=groups,
        hosts=hosts,
        warnings=tuple(group_warnings + host_warnings),
    )


def _load_json(path: Path) -> LoadedConfiguration:
    data = json.loads(path.read_text())
    groups, hosts = _structured_definitions(data)
    return LoadedConfiguration(
        effective=_effective_from_structured(path, data), groups=groups, hosts=hosts
    )


def _load_yaml(path: Path) -> LoadedConfiguration:
    try:
        import yaml  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise UnsupportedConfigFormatError(
            "YAML config requires the optional PyYAML dependency"
        ) from exc
    data = yaml.safe_load(path.read_text()) or {}
    groups, hosts = _structured_definitions(data)
    return LoadedConfiguration(
        effective=_effective_from_structured(path, data), groups=groups, hosts=hosts
    )


def load_config(
    path: Path,
    *,
    config_format: ConfigFormat = ConfigFormat.AUTO,
    overrides: Mapping[str, Any] | None = None,
) -> LoadedConfiguration:
    selected = _infer_format(path, config_format)
    if selected == ConfigFormat.LEGACY:
        loaded = _load_legacy(path)
    elif selected == ConfigFormat.JSON:
        loaded = _load_json(path)
    elif selected == ConfigFormat.YAML:
        loaded = _load_yaml(path)
    else:
        raise UnsupportedConfigFormatError(f"unsupported config format: {selected}")
    # Placeholder for future override normalization; keep public API stable now.
    _ = overrides
    return loaded
