"""CLI adapter for the Manuheart public API."""

from __future__ import annotations

import argparse
import sys

from manuheart.api import ConfigFormat, load_config, run_check, validate_config, write_reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="manuheart")
    parser.add_argument("--once", action="store_true", help="run one check cycle (compatibility)")
    parser.add_argument(
        "--daemon", action="store_true", help="run daemon mode (not implemented yet)"
    )
    parser.add_argument("--config", help="configuration file")
    parser.add_argument(
        "--config-format", choices=[x.value for x in ConfigFormat], default=ConfigFormat.AUTO.value
    )
    sub = parser.add_subparsers(dest="command")
    for name in ("check", "validate-config"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--config", required=True)
        cmd.add_argument(
            "--config-format",
            choices=[x.value for x in ConfigFormat],
            default=ConfigFormat.AUTO.value,
        )
    daemon = sub.add_parser("daemon")
    daemon.add_argument("--config", required=True)
    daemon.add_argument("--check-period", type=int, default=None)
    daemon.add_argument(
        "--config-format", choices=[x.value for x in ConfigFormat], default=ConfigFormat.AUTO.value
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command
    if args.once:
        command = "check"
    if args.daemon or command == "daemon":
        parser.error("daemon mode is not implemented yet")
    if command is None:
        parser.print_help()
        return 0
    if command == "validate-config":
        result = validate_config(args.config, config_format=args.config_format)
        for warning in result.warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        for error in result.errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 0 if result.valid else 1
    if command == "check":
        loaded = load_config(args.config, config_format=args.config_format)
        result = run_check(loaded)
        write_reports(result)
        for warning in result.warnings:
            print(f"WARNING: {warning}", file=sys.stderr)
        return 0
    parser.error(f"unknown command: {command}")
    return 2
