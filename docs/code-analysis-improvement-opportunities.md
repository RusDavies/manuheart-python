# Code Analysis Improvement Opportunities

Status: Review completed 2026-06-02.

## Scope reviewed

Reviewed current `src/manuheart/`, tests, scripts, docs, packaging metadata, and ignored/generated files. Verification during review:

- `ruff check src tests scripts`: passed.
- `pytest -q`: 28 passed.
- grep for `TODO`, `FIXME`, broad exception handlers, `type: ignore`, and `noqa` found only known boundary cases.

Overall finding: the project is in good shape for a small internal tool. The architecture is clean: config parsing, domain models, health rollup, checkers, state loading, reporting, API, and CLI are separated. The improvement opportunities below are hardening/polish items, not structural panic. Refreshing, frankly.

## Improvement opportunities

### 1. Harden previous-state loading against malformed report values

`state.py` tolerates missing and invalid JSON files, but individual malformed record values can still raise during `int(...)`, `Status(...)`, or `CheckType(...)` conversion.

Examples:

- `fail_count: "not-an-int"` can raise while loading previous host state.
- unknown `status` values can raise instead of being treated as `unknown`.
- malformed group `type` can raise while loading previous group state.

Impact: a bad or manually edited prior report can crash a check cycle before new reports are written.

Suggested fix: add safe conversion helpers for int, status, and check type, plus tests proving corrupted previous-state fields degrade to defaults with warnings or silent safe defaults.

### 2. Make HTTP checking less HEAD-only

`HttpChecker` currently uses `client.head(host.url)` for every HTTP/S check. Some perfectly valid health endpoints reject `HEAD`, only implement `GET`, or return method-specific responses.

Impact: false negatives for health endpoints that are healthy but do not support `HEAD`.

Suggested fix: add configurable HTTP method support, probably defaulting to `HEAD` for Bash-ish compatibility but allowing `GET`, or add `GET` fallback for `405 Method Not Allowed` / selected responses. Add tests with `httpx.MockTransport`.

### 3. Add stricter structured config validation and clearer errors

JSON/YAML config parsing directly indexes required fields and converts values. Missing fields, wrong container types, invalid URLs for HTTP/S hosts, or invalid runtime/check settings can currently surface as generic `KeyError`, `TypeError`, or `ValueError` instead of clear `ConfigError`s.

Legacy host parsing validates HTTP/S URLs, but structured JSON/YAML host parsing does not currently apply the same URL check.

Impact: user-facing validation can be less actionable, especially through CLI `validate-config`.

Suggested fix: validate structured config shape explicitly, report field paths in `ConfigError`s, and apply the same HTTP/S URL checks used by legacy parsing.

### 4. Improve CLI error handling for operational commands

`validate-config` returns structured errors, but `check` and `daemon` let config/check/report exceptions propagate as Python tracebacks.

Impact: poor operator experience and noisy automation logs when configs or report destinations are wrong.

Suggested fix: catch expected `ConfigError`, unsupported format errors, checker/report write errors, print concise stderr messages, and return nonzero exit codes. Keep tracebacks available only under a debug flag if needed.

### 5. Improve daemon observability and shutdown behaviour

Daemon mode runs repeated cycles but currently does not print warnings, log cycle start/end, summarize results, or handle graceful shutdown explicitly.

Impact: harder to operate as a long-running internal service; failure diagnosis depends on external wrappers.

Suggested fix: add minimal logging hooks or structured stderr output, print config warnings once, handle `KeyboardInterrupt`/termination cleanly, and add bounded daemon tests around warning/error behaviour.

### 6. Reuse/inject HTTP clients for efficiency and testability

`HttpChecker` creates a new `httpx.Client` per host check. That is simple but inefficient for many HTTP/S hosts and makes transport injection awkward in tests.

Impact: more connection setup than necessary and clunkier tests/mocking.

Suggested fix: allow a client factory or shared client lifecycle inside the checker, while preserving simple defaults. This can pair naturally with configurable method/fallback behaviour.

### 7. Add static typing gate and package typing marker

The code uses type hints heavily, but there is no mypy/pyright-style gate and no `py.typed` marker for downstream typed consumers.

Impact: type regressions may slip through, and installed package typing support is incomplete.

Suggested fix: add `py.typed`, include it in package data, and add a lightweight static type check gate once annotations are ready.

### 8. Add dependency/security review gate before release

Runtime dependencies are small (`httpx`, `icmplib`, optional `PyYAML`), but release posture should include dependency review.

Impact: small internal tools still inherit supply-chain risk. Annoying, but computers do that.

Suggested fix: add a release-readiness gate using an available scanner (`pip-audit`, `uv pip compile`/lock review, or equivalent) and document accepted dependency posture.

## Recommended priority

1. Harden previous-state loading.
2. Improve structured config validation/errors.
3. Make HTTP checking configurable or add GET fallback.
4. Improve CLI operational error handling.
5. Then daemon observability, HTTP client reuse, static typing, and dependency review.

Rationale: the first four reduce surprise crashes and false negatives, which matter most before treating this as a real replacement for the Bash tool.
