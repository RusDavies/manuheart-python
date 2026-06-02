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
