# TODO

## Product process / Class 2 internal tool setup

- [x] Create lightweight product/problem framing.
- [x] Define requirements and acceptance criteria.
- [x] Capture UX/workflow notes if a UI exists.
- [x] Capture security/privacy notes.
- [x] Capture lightweight architecture/deployment notes.
- [x] Create implementation checklist.
- [x] Record basic QA evidence for completed work.
- [x] Add rollback/disable note.
- [x] Add AI-agent operation boundary note, unless Russ explicitly exempts it.

## Project discovery

- [x] Define scope: what Manuheart Python is responsible for.
- [x] Capture baseline inventory, current access assumptions, and dependencies.
- [x] Add README quick start for library API usage and CLI usage.
- [x] Add Bash-vs-Python output compatibility check for localhost fixtures.
- [x] Identify initial implementation or audit tasks.
- [x] Prioritize remediation/build items with Russ.


## Python rewrite backlog

- [x] Understand the original Bash implementation and document its behavior.
- [x] Propose a clean Python architecture for the rewrite.
- [x] Create Python project skeleton with `pyproject.toml`, `src/manuheart/`, and `tests/`.
- [x] Define the initial public library API contract in `src/manuheart/api.py`.
- [x] Add API smoke tests proving the package and public API import cleanly.
- [x] Port sample localhost config fixtures from `manuheart-bash`.
- [x] Implement typed domain models for hosts, groups, systems, statuses, and checks.
- [x] Implement compatible legacy config, group, and host parsers.
- [x] Implement first-class JSON configuration parser using the same normalized domain model.
- [x] Implement optional YAML configuration parser, preferably behind a `yaml` package extra.
- [x] Add equivalence tests proving legacy, JSON, and YAML config can describe the same health model.
- [x] Implement pure health rollup logic with fake-checker tests.
- [x] Implement CLI/API override application for config values and add precedence tests.
- [x] Implement real ICMP and HTTP(S) checkers.
- [x] Implement previous-state loading and atomic JSON report writing.
- [x] Implement CLI commands and compatibility flags as thin adapters over the public API.
- [x] Add tests proving CLI behavior matches API behavior for equivalent inputs.
- [x] Add smoke test for one-shot localhost run.
- [x] Add daemon mode only after one-shot mode is solid.


## Compatibility-first readiness backlog

- [x] Preserve report filenames and top-level keys while converting inner fields to cleaner typed JSON.
- [x] Use Pythonic snake_case field names in clean typed report records.
- [x] Implement clean typed report output as the default Python report format.
- [x] Keep report status fields as enum-like strings (`up`, `down`, `unknown`).
- [x] Keep report timestamp fields as consistently ISO-8601 strings.
- [x] Add tests proving report fields use typed JSON values where practical.
- [x] Decide whether safe real-world Bash configs can be used as compatibility fixtures.
- [x] Add broader synthetic compatibility fixtures after exact localhost output matching is resolved.
- [x] Add expanded synthetic compatibility fixtures for multi-host, HTTP/S, optional group, duplicate, and failure-grace scenarios.
- [x] Tighten localhost Bash-vs-Python compatibility check to identify and document migration-relevant output differences.
- [x] Keep real-world fixture intake blocked unless Russ separately approves sanitized configs.
- [x] Document accepted compatibility differences between Bash and Python outputs.
- [x] Decide whether to add an explicit legacy-compatible report mode after clean typed output is established.
- [x] Add clean-venv install/package smoke test.
- [ ] Decide remote repository and publishing/release posture.

## Code analysis improvement backlog

- [x] Harden previous-state loading against malformed report values.
- [x] Add stricter structured JSON/YAML config validation and clearer `ConfigError` messages.
- [x] Make HTTP checking less HEAD-only, via configurable method or safe GET fallback.
- [x] Improve CLI error handling for `check` and `daemon` operational failures.
- [x] Improve daemon observability and graceful shutdown behaviour.
- [x] Reuse or inject HTTP clients for efficiency and cleaner checker tests.
- [x] Add static typing gate and package typing marker (`py.typed`).
- [x] Add dependency/security review gate before release.
