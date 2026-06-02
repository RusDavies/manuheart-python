# QA Evidence

Status: Draft evidence log.

## Current verification gates

The current local verification gate is:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check src tests
rm -rf /tmp/manuheart-smoke
.venv/bin/python -m manuheart check \
  --config examples/localhost/manuheart.json \
  --host-status-file /tmp/manuheart-smoke/hoststatus \
  --group-status-file /tmp/manuheart-smoke/groupstatus \
  --sys-status-file /tmp/manuheart-smoke/sysstatus
.venv/bin/python scripts/check_localhost_compatibility.py
.venv/bin/python scripts/check_clean_install.py
```

## Evidence from previous completed iteration

- `pytest`: 21 passed.
- `ruff check src tests`: passed.
- One-shot JSON smoke wrote parseable `hoststatus`, `groupstatus`, and `sysstatus`.

## Evidence for this readiness iteration

Pre-merge gate on branch `iterate-10-readiness-compat`:

- `ruff check src tests scripts`: passed.
- `pytest`: 21 passed.
- `scripts/check_localhost_compatibility.py`: passed.
- One-shot JSON smoke wrote parseable `hoststatus`, `groupstatus`, and `sysstatus` under `/tmp/manuheart-smoke`.

## Evidence for clean report compatibility tightening

Pre-merge gate on branch `tighten-localhost-compatibility-check`:

- `ruff check src tests scripts`: passed.
- `pytest`: 23 passed.
- `scripts/check_localhost_compatibility.py`: passed and printed accepted migration differences for field renames, typed numeric/boolean values, and ISO-8601 timestamps.

See `docs/localhost-compatibility-differences.md` for the current hard compatibility contract and accepted localhost Bash-vs-Python output differences.

## Evidence for broader synthetic compatibility fixtures

Pre-merge gate on branch `add-synthetic-compat-fixtures`:

- `ruff check src tests scripts`: passed.
- `pytest`: 28 passed.
- `scripts/check_localhost_compatibility.py`: passed and printed accepted migration differences.

Added `examples/synthetic-compat/` with equivalent legacy, JSON, and YAML fixtures covering multi-host HTTP, HTTPS, ICMP, multiple systems, optional empty group, and failure-grace behaviour. Added `tests/fixtures/legacy-edge-cases/` to exercise legacy duplicate rows, invalid rows, unknown groups, and invalid HTTP URL warnings without using real-world configs.

## Evidence for real-world fixture intake guardrail

Pre-merge gate on branch `block-real-world-fixture-intake`:

- `ruff check src tests scripts`: passed.
- `pytest`: 28 passed.
- `scripts/check_localhost_compatibility.py`: passed and printed accepted migration differences.

Added `docs/fixture-intake-policy.md` and linked it from privacy/security and prioritization notes. The policy blocks real-world Manuheart config/report fixture intake unless Russ explicitly approves a specific sanitized source set.

## Evidence for legacy report mode decision

Pre-merge gate on branch `decide-legacy-report-mode`:

- `ruff check src tests scripts`: passed.
- `pytest`: 28 passed.
- `scripts/check_localhost_compatibility.py`: passed and printed accepted migration differences.

Recorded the decision not to add an explicit legacy-compatible report mode now. Clean typed JSON remains the default, previous-state loading can read legacy fields, and exact Bash-shaped output should be added only if a concrete downstream consumer requires it.

## Evidence for clean-venv install/package smoke

Pre-merge gate on branch `add-clean-venv-smoke`:

- `ruff check src tests scripts`: passed.
- `pytest`: 28 passed.
- `scripts/check_localhost_compatibility.py`: passed and printed accepted migration differences.
- `scripts/check_clean_install.py`: passed; it created a temporary clean venv, installed `manuheart[yaml]` from the project root, imported the public API, validated JSON and YAML fixtures via the installed `manuheart` console script, ran a one-shot check, and verified report JSON records were written.

## Evidence for previous-state loading hardening

Pre-merge gate on branch `harden-previous-state-loading`:

- `ruff check src tests scripts`: passed.
- `pytest`: 30 passed.
- `scripts/check_localhost_compatibility.py`: passed and printed accepted migration differences.
- `scripts/check_clean_install.py`: passed.

Added safe previous-state parsing for non-object payloads, non-list report collections, non-record entries, malformed integer fields, unknown statuses, unknown check types, and ambiguous boolean values. Malformed previous report data now degrades to safe defaults instead of crashing the next check cycle.

## Evidence for structured config validation hardening

Pre-merge gate on branch `structured-config-validation`:

- `ruff check src tests scripts`: passed.
- `pytest`: 36 passed.
- `scripts/check_localhost_compatibility.py`: passed and printed accepted migration differences.
- `scripts/check_clean_install.py`: passed.

Structured JSON/YAML config loading now validates top-level object shape, `groups`/`hosts` list shape, group/host item object shape, required fields with path-specific messages, unsupported group check types, HTTP/HTTPS host URL schemes, runtime/checks/status_files section shapes, numeric check settings, malformed JSON, and malformed YAML. Errors are raised as `ConfigError` instead of raw parser/type/key exceptions.

## Evidence for HTTP method and GET fallback hardening

Pre-merge gate on branch `http-method-fallback`:

- `ruff check src tests scripts`: passed.
- `pytest`: 41 passed.
- `scripts/check_localhost_compatibility.py`: passed and printed accepted migration differences.
- `scripts/check_clean_install.py`: passed.

HTTP checks now support structured config fields `checks.http.method` (`HEAD` or `GET`) and `checks.http.fallback_to_get` (boolean). The default remains `HEAD` with GET fallback enabled for servers that return method-not-allowed or not-implemented for HEAD.

## Evidence for CLI operational error handling

Pre-merge gate on branch `cli-error-handling`:

- `ruff check src tests scripts`: passed.
- `pytest`: 43 passed.
- `scripts/check_localhost_compatibility.py`: passed and printed accepted migration differences.
- `scripts/check_clean_install.py`: passed.

The `check` and `daemon` CLI commands now catch operational failures at the adapter boundary, print concise `ERROR: ...` messages to stderr, and exit `1` instead of leaking Python tracebacks. Added subprocess tests for report-write failure and daemon config-load failure.

## Evidence for daemon observability and graceful shutdown

Pre-merge gate on branch `daemon-observability-shutdown`:

- `ruff check src tests scripts`: passed.
- `pytest`: 44 passed.
- `scripts/check_localhost_compatibility.py`: passed and printed accepted migration differences.
- `scripts/check_clean_install.py`: passed.

Daemon mode now emits lifecycle/cycle events (`daemon starting`, `daemon cycle N completed`, and `daemon stopped after N cycle(s)`) through an API callback. The CLI wires those events to stderr. `KeyboardInterrupt` during daemon sleep is handled gracefully and returns the completed cycle count instead of leaking a traceback.

## Evidence for HTTP client reuse/injection

Pre-merge gate on branch `http-client-injection`:

- `ruff check src tests scripts`: passed.
- `pytest`: 46 passed.
- `scripts/check_localhost_compatibility.py`: passed and printed accepted migration differences.
- `scripts/check_clean_install.py`: passed.

`HttpChecker` now accepts an injected HTTP client for cleaner tests and alternate callers. The default checker registry creates one shared `httpx.Client` for HTTP and HTTPS checks in a health cycle, and `run_health_cycle` closes default checker resources after the cycle completes.

## Evidence for static typing gate and typed package marker

Pre-merge gate on branch `typing-gate-pytyped`:

- `ruff check src tests scripts`: passed.
- `mypy src/manuheart`: passed with no issues across 11 source files.
- `pytest`: 46 passed.
- `scripts/check_localhost_compatibility.py`: passed and printed accepted migration differences.
- `scripts/check_clean_install.py`: passed and verifies installed package contains `manuheart/py.typed`.

Added `mypy` and `types-PyYAML` to the development extra, added `src/manuheart/py.typed` as a PEP 561 marker included in the wheel, added mypy configuration, fixed source typing issues surfaced by mypy, and documented mypy in the local verification gate.
