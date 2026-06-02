# Requirements and Acceptance Criteria

Status: Draft.

## Functional requirements

- Load single-file JSON config.
- Load single-file YAML config when the optional YAML extra is installed.
- Reject unsupported config formats clearly.
- Reject unknown JSON/YAML config keys clearly.
- Validate numeric bounds for runtime/check/group settings.
- Resolve relative `runtime.status_files.*` paths under `runtime.var_dir`.
- Apply CLI/API overrides with precedence over config-file values.
- Run ICMP checks using a Python ICMP library.
- Run HTTP/S checks using a Python HTTP client library.
- Roll host state into group state and group state into system state.
- Preserve failure-grace semantics: hosts become `down` only after remaining non-`up` longer than grace allows.
- Preserve `unknown` as an indeterminate/pending evidence state, not a green state.
- Preserve critical-group system rollup semantics: critical `down` groups make systems `down`, and critical `unknown` groups make systems `unknown`.
- Load previous status from clean or legacy-shaped JSON reports where available.
- Write host, group, and system status reports atomically as clean typed JSON.
- Expose a reusable public Python API.
- Provide CLI commands as adapters over the public API.
- Expose typed public extension points for checker maps, clock sources, daemon sleepers, daemon event callbacks, and config overrides.

## Acceptance criteria

- `pytest` passes.
- `ruff check src tests` passes.
- `python -m manuheart --help` works.
- JSON and YAML fixtures normalize to equivalent host/group definitions.
- Unsupported legacy-style config filenames fail with clear errors.
- Unknown JSON/YAML keys and invalid numeric bounds fail with clear `ConfigError`s.
- Relative status-file paths are covered by tests and resolve under `var_dir`.
- CLI/API override precedence is covered by tests.
- Public API extension-point signatures are covered by type-hint regression tests.
- Fake-checker tests cover up/down/unknown rollup behaviour, including host grace and critical-group unknown propagation.
- Checker implementation tests mock `icmplib` and `httpx` rather than depending on external network state.
- One-shot localhost smoke test writes parseable JSON reports.
- Public deployment-smoke config validates and can run without exposing internal topology.

## Constraints

- Class 2 internal tool.
- One-shot mode remains the operational default.
- Daemon mode is allowed but should remain a thin loop over the same API-backed one-shot operation.
- Library code must not call `sys.exit()` or print directly for normal operation.
