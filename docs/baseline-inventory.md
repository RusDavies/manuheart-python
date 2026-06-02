# Baseline Inventory, Access, and Dependencies

Status: Draft.

## Repositories / folders

- Python rewrite: `projects/manuheart-python`.
- Bash source reference: `projects/manuheart-bash`.

## Current Python package

- Package name: `manuheart`.
- Source layout: `src/manuheart`.
- Public API: `manuheart.api`.
- CLI entry point: `manuheart = manuheart.cli:main`.

## Runtime dependencies

- Python 3.11+.
- `httpx`.
- `icmplib`.
- Optional `PyYAML` via `manuheart[yaml]`.

## Development dependencies

- `pytest`.
- `ruff`.

## Access assumptions

- Work is local/internal unless Russ approves deployment or publishing.
- No external messaging, alerting, or infrastructure changes are authorized by default.
- ICMP checks may require platform/network permissions depending on environment; current implementation uses unprivileged `icmplib` by default.
