#!/usr/bin/env python3
"""Install the pinned OSV Scanner binary for CI/local security gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import stat
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / "tools" / "osv-scanner.lock.json"
DEFAULT_DESTINATION = ROOT / ".tools" / "osv-scanner"


def host_asset_key() -> str:
    """Return the lock-file asset key for the current host."""

    system = platform.system().lower()
    machine = platform.machine().lower()
    if system == "linux" and machine in {"x86_64", "amd64"}:
        return "linux_amd64"
    raise RuntimeError(f"unsupported OSV Scanner install host: {system}/{machine}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def install(destination: Path = DEFAULT_DESTINATION) -> Path:
    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    asset = lock["assets"][host_asset_key()]
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".download")
    urllib.request.urlretrieve(asset["url"], temporary)  # noqa: S310 - pinned HTTPS URL + hash
    actual = sha256(temporary)
    expected = asset["sha256"]
    if actual != expected:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(
            f"OSV Scanner checksum mismatch for {asset['name']}: expected {expected}, got {actual}"
        )
    os.replace(temporary, destination)
    destination.chmod(destination.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=DEFAULT_DESTINATION)
    args = parser.parse_args(argv)
    try:
        installed = install(args.destination)
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        print(f"failed to install pinned OSV Scanner: {exc}", file=sys.stderr)
        return 1
    print(installed)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
