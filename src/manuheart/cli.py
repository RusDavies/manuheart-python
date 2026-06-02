"""CLI adapter for the Manuheart public API."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from manuheart.api import (
    ConfigFormat,
    load_config,
    run_check,
    run_daemon,
    validate_config,
    write_reports,
)


def _print_error(exc: Exception) -> None:
    print(f"ERROR: {exc}", file=sys.stderr)


def _print_daemon_event(message: str) -> None:
    print(message, file=sys.stderr)


def _add_config_args(parser: argparse.ArgumentParser, *, required: bool = True) -> None:
    parser.add_argument("--config", required=required, help="JSON or YAML configuration file")
    parser.add_argument(
        "--config-format",
        choices=[x.value for x in ConfigFormat],
        default=ConfigFormat.AUTO.value,
    )
    parser.add_argument("--var-dir", type=Path)
    parser.add_argument("--log-file", type=Path)
    parser.add_argument("--log-level", type=int)
    parser.add_argument("--check-period", type=int)
    parser.add_argument("--host-status-file", type=Path)
    parser.add_argument("--group-status-file", type=Path)
    parser.add_argument("--sys-status-file", type=Path)


def _overrides(args: argparse.Namespace, *, run_mode: str | None = None) -> dict:
    values = {
        "var_dir": args.var_dir,
        "log_file": args.log_file,
        "log_level": args.log_level,
        "check_period": args.check_period,
        "run_mode": run_mode,
        "host_status_file": args.host_status_file,
        "group_status_file": args.group_status_file,
        "system_status_file": args.sys_status_file,
    }
    return {key: value for key, value in values.items() if value is not None}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="manuheart")
    sub = parser.add_subparsers(dest="command")
    _add_config_args(sub.add_parser("check"), required=True)
    _add_config_args(sub.add_parser("validate-config"), required=True)
    daemon = sub.add_parser("daemon")
    _add_config_args(daemon, required=True)
    # Test/support escape hatch; not advertised in help.
    daemon.add_argument("--max-cycles", type=int, default=None, help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command
    if command is None:
        parser.print_help()
        return 0
    if not args.config:
        parser.error("--config is required")

    run_mode = "daemon" if command == "daemon" else "once"
    overrides = _overrides(args, run_mode=run_mode)

    if command == "validate-config":
        validation = validate_config(
            args.config,
            config_format=args.config_format,
            overrides=overrides,
        )
        for warning in validation.warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        for error in validation.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 0 if validation.valid else 1

    if command == "check":
        try:
            loaded = load_config(args.config, config_format=args.config_format, overrides=overrides)
            check_result = run_check(loaded)
            write_reports(check_result)
            for warning in check_result.warnings:
                print(f"WARNING: {warning}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001 - CLI boundary prints clean operational errors
            _print_error(exc)
            return 1
        return 0

    if command == "daemon":
        try:
            loaded = load_config(args.config, config_format=args.config_format, overrides=overrides)
            cycles = getattr(args, "max_cycles", None)
            run_daemon(loaded, max_cycles=cycles, on_event=_print_daemon_event)
        except Exception as exc:  # noqa: BLE001 - CLI boundary prints clean operational errors
            _print_error(exc)
            return 1
        return 0

    parser.error(f"unknown command: {command}")
    return 2
