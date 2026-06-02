# Requirements and Acceptance Criteria

Status: Draft.

## Functional requirements

- Load first-class single-file JSON config.
- Load first-class single-file YAML config when the optional YAML extra is installed.
- Load legacy Manuheart config (`manuheart.conf` plus pipe-delimited `groups` and `hosts` files) as a convenience/import path.
- Apply CLI/API overrides with precedence over config-file values.
- Run ICMP checks using a Python ICMP library.
- Run HTTP/S checks using a Python HTTP client library.
- Roll host state into group state and group state into system state.
- Preserve failure-grace semantics, including negative grace as infinite grace.
- Preserve critical-group system rollup semantics.
- Load previous status from clean or legacy-shaped JSON reports where available.
- Write host, group, and system status reports atomically as clean typed JSON.
- Expose a reusable public Python API.
- Provide CLI commands as adapters over the public API.

## Acceptance criteria

- `pytest` passes.
- `ruff check src tests` passes.
- `python -m manuheart --help` works.
- JSON and YAML fixtures normalize to equivalent host/group definitions.
- Legacy fixtures remain covered as regression/import-path evidence.
- CLI/API override precedence is covered by tests.
- Fake-checker tests cover up/down rollup behaviour.
- Checker implementation tests mock `icmplib` and `httpx` rather than depending on external network state.
- One-shot localhost smoke test writes parseable JSON reports.
- Public deployment-smoke config validates and can run without exposing internal topology.

## Constraints

- Class 2 internal tool.
- One-shot mode remains the operational default.
- Daemon mode is allowed but should remain a thin loop over the same API-backed one-shot operation.
- Library code must not call `sys.exit()` or print directly for normal operation.
