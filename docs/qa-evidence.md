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
