from __future__ import annotations

import json
import stat
from pathlib import Path

import pytest
from scripts import check_osv_scanner, install_osv_scanner


def test_osv_runtime_dependencies_include_yaml_extra_and_idna_constraint() -> None:
    requirements = check_osv_scanner.dependency_group(check_osv_scanner.RUNTIME_EXTRAS)

    assert "httpx>=0.27" in requirements
    assert "icmplib>=3.0" in requirements
    assert "PyYAML>=6.0" in requirements
    assert "idna>=3.15" in requirements


def test_osv_tooling_dependencies_include_release_and_dev_extras() -> None:
    requirements = check_osv_scanner.dependency_group(check_osv_scanner.TOOLING_EXTRAS)

    assert "build>=1.2" in requirements
    assert "twine>=5.1" in requirements
    assert "pip-audit>=2.10" in requirements
    assert len(requirements) == len(set(requirements))


def test_requirements_inputs_are_named_for_osv_extraction(tmp_path: Path) -> None:
    paths = check_osv_scanner.requirements_inputs(tmp_path)

    assert sorted(paths) == ["runtime", "tooling"]
    assert paths["runtime"].name == "runtime-direct-requirements.txt"
    assert paths["tooling"].name == "tooling-direct-requirements.txt"
    assert paths["runtime"].read_text(encoding="utf-8").endswith("\n")


def test_osv_dependency_scan_uses_resolved_lockfiles_without_reresolving(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lockfile = tmp_path / "runtime-requirements.txt"
    lockfile.write_text("pytest==9.0.3\n", encoding="utf-8")
    calls: list[tuple[str, list[str]]] = []

    def fake_run(scanner: str, args: list[str]) -> int:
        calls.append((scanner, args))
        return 0

    monkeypatch.setattr(check_osv_scanner, "run", fake_run)

    assert check_osv_scanner.scan_requirements("osv-scanner", {"runtime": lockfile}) == 0
    assert calls == [
        (
            "osv-scanner",
            [
                "scan",
                "source",
                "--lockfile",
                str(lockfile),
                "--no-resolve",
                "--format",
                "json",
                "--verbosity",
                "error",
            ],
        )
    ]


def test_osv_repository_scan_includes_git_root(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, list[str]]] = []

    def fake_run(scanner: str, args: list[str]) -> int:
        calls.append((scanner, args))
        return 0

    monkeypatch.setattr(check_osv_scanner, "run", fake_run)

    assert check_osv_scanner.scan_repository("osv-scanner") == 0
    assert calls
    args = calls[0][1]
    assert "--include-git-root" in args
    assert args[-1] == "."


def test_osv_scanner_path_prefers_explicit_path() -> None:
    assert check_osv_scanner.scanner_path("/tmp/osv-scanner-test") == "/tmp/osv-scanner-test"


def test_installer_verifies_pinned_checksum_and_marks_executable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = b"fake-osv-scanner"
    digest = install_osv_scanner.hashlib.sha256(payload).hexdigest()
    lock = {
        "assets": {
            "linux_amd64": {
                "name": "osv-scanner_linux_amd64",
                "url": "https://example.invalid/osv-scanner_linux_amd64",
                "sha256": digest,
            }
        }
    }
    lock_path = tmp_path / "lock.json"
    lock_path.write_text(json.dumps(lock), encoding="utf-8")
    monkeypatch.setattr(install_osv_scanner, "LOCK_PATH", lock_path)
    monkeypatch.setattr(install_osv_scanner, "host_asset_key", lambda: "linux_amd64")

    def fake_urlretrieve(url: str, filename: Path) -> tuple[Path, object | None]:
        assert url == "https://example.invalid/osv-scanner_linux_amd64"
        Path(filename).write_bytes(payload)
        return Path(filename), None

    monkeypatch.setattr(install_osv_scanner.urllib.request, "urlretrieve", fake_urlretrieve)
    destination = tmp_path / "bin" / "osv-scanner"

    installed = install_osv_scanner.install(destination)

    assert installed == destination
    assert installed.read_bytes() == payload
    assert installed.stat().st_mode & stat.S_IXUSR
