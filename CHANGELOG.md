# Changelog

## Unreleased

### Security

- Fixed the OSV repository-manifest scan to include the current git root with OSV Scanner 2.3.x.
- Fixed OSV Scanner dependency-gate handling so generated resolved requirement lockfiles are scanned directly without a second resolver pass.
- Hardened the GitHub Actions PyPI release workflow to fail if the GitHub Release tag does not match `pyproject.toml` package version.
- Added a local publish-workflow policy check covering trusted-publishing and tag/version-alignment requirements.
- Added pinned OSV Scanner coverage for runtime, optional, dev/release dependencies, repository manifests, and release CI.
- Added an explicit `idna>=3.15` runtime constraint so `httpx` cannot resolve vulnerable transitive IDNA versions.

## v0.1.1 - PyPI trusted publishing release

Status: public package publishing release.

### Changed

- Added GitHub Actions trusted publishing workflow for TestPyPI and PyPI.
- Added PyPI/TestPyPI trusted-publisher setup documentation.
- Changed README documentation links to absolute GitHub URLs so they render correctly on PyPI.
- Added package project URLs for repository and changelog.
- Added local release tooling extras for `build` and `twine`.

### Verification

- TestPyPI trusted publishing for `manuheart==0.1.0` was verified before this release.
- `manuheart[yaml]==0.1.0` installed successfully from TestPyPI with real PyPI as dependency fallback.

## v0.1.0 - Internal baseline

Status: internal/private baseline; not a public release.

### Added

- Python package and CLI for Manuheart health checks.
- JSON configuration as the primary supported config format.
- Optional YAML configuration support via the `yaml` extra.
- Typed domain models for hosts, groups, systems, statuses, checks, reports, and config.
- ICMP checker backed by `icmplib`.
- HTTP/S checker backed by `httpx`, with configurable `HEAD`/`GET` behavior and safe `HEAD` to `GET` fallback.
- Clean typed JSON reports for `hoststatus`, `groupstatus`, and `sysstatus`.
- Previous-state loading from clean Python reports and legacy-shaped Bash reports.
- Host/group/system `unknown`, grace, critical-group, and rollup semantics.
- Per-host checker error isolation and missing-checker warnings.
- Warning-aware previous-state degradation.
- Semantic config warnings for valid-but-suspicious health models.
- API override validation.
- Minimal check/daemon logging through `runtime.log_file` and `runtime.log_level`.
- Checker diagnostic details in host reports, with normalization and length bounding.
- Shared report metadata (`run_id`, `generated_at`) across report files.
- Public API extension types for injected checkers, clocks, sleepers, daemon event callbacks, config overrides, and previous state.
- CLI commands: `check`, `daemon`, and `validate-config`.
- Public deployment smoke config using harmless well-known endpoints.
- Local QA gates for linting, typing, tests, localhost Bash/Python comparison, dependency audit, and clean install smoke.

### Removed / intentionally not included

- Legacy Bash config parsing as a product surface.
- Drop-in Bash replacement requirement.
- Public PyPI or public repository release posture.
- Real infrastructure fixtures or reports.
- Bounded check concurrency; deferred until real deployment scale justifies it.

### Verification for baseline

The baseline is considered releasable internally only after the documented release-readiness gate passes:

```bash
.venv/bin/python -m ruff check src tests scripts
.venv/bin/python -m mypy src/manuheart
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_localhost_compatibility.py
.venv/bin/python scripts/check_dependency_security.py
.venv/bin/python -m manuheart validate-config --config examples/deployment-test/public-smoke.json
.venv/bin/python -m manuheart check --config examples/deployment-test/public-smoke.json
.venv/bin/python scripts/check_clean_install.py
```
