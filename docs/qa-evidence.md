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

Added `examples/synthetic-compat/` with equivalent JSON and YAML fixtures covering multi-host HTTP, HTTPS, ICMP, multiple systems, optional empty group, and failure-grace behaviour. Legacy edge-case fixtures were later removed when legacy Bash config input was dropped from the product surface.

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

## Evidence for dependency/security review gate

Pre-merge gate on branch `dependency-security-gate`:

- `ruff check src tests scripts`: passed.
- `mypy src/manuheart`: passed with no issues across 11 source files.
- `pytest`: 46 passed.
- `scripts/check_localhost_compatibility.py`: passed and printed accepted migration differences.
- `scripts/check_dependency_security.py`: passed; no known vulnerabilities found in releasable runtime dependencies plus optional YAML extra.
- `scripts/check_clean_install.py`: passed and verifies installed package contains `manuheart/py.typed`.

Added `pip-audit` to the development extra and added `scripts/check_dependency_security.py`, which audits the releasable dependency set from `pyproject.toml` while intentionally excluding dev-only tooling and the unpublished local package itself.

## Evidence for remote repository and release posture decision

Pre-merge gate on branch `release-posture-docs`:

- `ruff check src tests scripts`: passed.
- `mypy src/manuheart`: passed with no issues across 11 source files.
- `pytest`: 46 passed.
- `scripts/check_localhost_compatibility.py`: passed and printed accepted migration differences.
- `scripts/check_dependency_security.py`: passed; no known vulnerabilities found in releasable runtime dependencies plus optional YAML extra.
- `scripts/check_clean_install.py`: passed and verifies installed package contains `manuheart/py.typed`.

Documented the release posture in `docs/release-posture.md`: internal-only by default, no public repository or public PyPI publication, private repository only with explicit Russ approval, internal wheel/sdist artifacts only after the release-readiness gate, and no deployment against real monitored hosts without human approval.

## Evidence for private remote and public deployment-smoke config

Pre-merge gate on branch `remote-and-public-smoke-config`:

- Private GitHub remote created: `https://github.com/RusDavies/manuheart-python`.
- `manuheart validate-config --config examples/deployment-test/public-smoke.json`: passed.
- `manuheart check --config examples/deployment-test/public-smoke.json`: passed; generated disposable reports under `examples/deployment-test/tmp/public-smoke-reports/`.
- Public smoke result at run time: `public-smoke` system status `up`; HTTP checks for `example.com`, `www.iana.org`, and Cloudflare trace were `up`; ICMP checks for `1.1.1.1` and `8.8.8.8` were `up`.
- `ruff check src tests scripts`: passed.
- `mypy src/manuheart`: passed with no issues across 11 source files.
- `pytest`: 46 passed.
- `scripts/check_localhost_compatibility.py`: passed and printed accepted migration differences.
- `scripts/check_dependency_security.py`: passed; no known vulnerabilities found in releasable runtime dependencies plus optional YAML extra.
- `scripts/check_clean_install.py`: passed and verifies installed package contains `manuheart/py.typed`.

Added `examples/deployment-test/public-smoke.json` and `docs/deployment-test-config.md` for deployment smoke testing against a tiny set of well-known public endpoints. Generated smoke-test reports are ignored via `.gitignore`.

## Evidence for product-direction reframing away from drop-in replacement

Pre-merge gate on branch `reframe-away-from-drop-in-replacement`:

- `ruff check src tests scripts`: passed.
- `mypy src/manuheart`: passed with no issues across 11 source files.
- `pytest`: 46 passed.
- `scripts/check_localhost_compatibility.py`: passed and printed accepted migration differences.
- `scripts/check_dependency_security.py`: passed; no known vulnerabilities found in releasable runtime dependencies plus optional YAML extra.
- `scripts/check_clean_install.py`: passed and verifies installed package contains `manuheart/py.typed`.

Updated product framing, scope, requirements, prioritization, release posture, fixture intake, and architecture notes to reflect Russ's decision that Manuheart Python does not need to be a drop-in Bash replacement because there are no existing Bash installations to replace. Bash compatibility is now treated as historical reference/regression evidence, while the main goal is a clean internal Python health-checking implementation.

## Evidence for removing legacy Bash config input

Pre-merge gate on branch `remove-legacy-config-format`:

- `ruff check src tests scripts`: passed.
- `mypy src/manuheart`: passed.
- `pytest`: 43 passed.
- `scripts/check_localhost_compatibility.py`: passed; Python side uses JSON config while Bash side remains a historical reference comparison.
- `scripts/check_dependency_security.py`: passed.
- `scripts/check_clean_install.py`: passed.
- `manuheart validate-config --config examples/deployment-test/public-smoke.json`: passed.
- `manuheart check --config examples/deployment-test/public-smoke.json`: passed.

Removed legacy Bash `.conf` plus pipe-delimited `groups`/`hosts` config loading from the Python product surface. JSON and YAML are now the only supported config formats. Removed compatibility root flags `--once`/`--daemon` and legacy host/group file overrides from the CLI. Kept previous-state legacy report-field tolerance because it is isolated report robustness, not config-format support.

## Evidence for documented health state semantics

Pre-merge gate on branch `implement-health-state-semantics`:

- `ruff check src tests scripts`: passed.
- `mypy src/manuheart`: passed.
- `pytest`: 46 passed.
- `scripts/check_localhost_compatibility.py`: passed; accepted migration differences now include `optional-example` reporting `up` for explicit `min_count: 0` semantics instead of Bash `unknown`.
- `scripts/check_dependency_security.py`: passed.
- `scripts/check_clean_install.py`: passed.
- `manuheart validate-config --config examples/deployment-test/public-smoke.json`: passed.

Implemented the documented state model from `docs/health-state-semantics.md`: hosts only become `down` after remaining non-`up` beyond grace, host `unknown` can keep groups/systems `unknown` while grace is pending, `min_count: 0` groups report `up`, and critical `unknown` groups propagate system `unknown` instead of `up`.

## Evidence for stricter structured config validation

Pre-merge gate on branch `stricter-config-validation`:

- `ruff check src tests scripts`: passed.
- `mypy src/manuheart`: passed.
- `pytest`: 63 passed.
- `scripts/check_localhost_compatibility.py`: passed.
- `scripts/check_dependency_security.py`: passed.
- `scripts/check_clean_install.py`: passed.
- `manuheart validate-config --config examples/deployment-test/public-smoke.json`: passed.

Added strict unknown-key checks for top-level config, `runtime`, `runtime.status_files`, `checks`, `checks.http`, `checks.icmp`, group entries, and host entries. Added numeric bounds validation for log level, check period, HTTP/ICMP timeouts, ICMP count, group `min_count`, and group `failure_grace`, plus `runtime.run_mode` validation. Added targeted tests for these cases.

## Evidence for per-host checker exception handling

Pre-merge gate on branch `handle-checker-exceptions`:

- `ruff check src tests scripts`: passed.
- `mypy src/manuheart`: passed.
- `pytest`: 65 passed.
- `scripts/check_localhost_compatibility.py`: passed.
- `scripts/check_dependency_security.py`: passed.
- `scripts/check_clean_install.py`: passed.
- `manuheart validate-config --config examples/deployment-test/public-smoke.json`: passed.

Updated `run_health_cycle()` so checker lookup failures and checker exceptions are converted into per-host non-`up` check results with warnings instead of aborting the whole cycle. Added tests proving one exploding host check does not prevent other hosts/groups/systems from being reported, and that an explicitly empty injected checker map remains empty rather than silently falling back to default checkers.

## Evidence for previous-state warning surfacing

Pre-merge gate on branch `state-load-warnings`:

- `ruff check src tests scripts`: passed.
- `mypy src/manuheart`: passed.
- `pytest`: 67 passed.
- `scripts/check_localhost_compatibility.py`: passed.
- `scripts/check_dependency_security.py`: passed.
- `scripts/check_clean_install.py`: passed.
- `manuheart validate-config --config examples/deployment-test/public-smoke.json`: passed.

Added warning-aware previous-state loading. Malformed JSON, non-object report payloads, non-list report collections, non-object records, malformed integers, invalid booleans, invalid statuses, invalid check types, and missing identity fields now degrade safely and produce warnings. `run_check()` carries those warnings into `CheckRunResult.warnings`, and the CLI prints them to stderr for `check` runs.
