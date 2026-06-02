# Architecture and Deployment Notes

Status: Draft.

## Architecture

Manuheart Python is a reusable Python library with a CLI adapter.

Core layers:

- `manuheart.api`: public import surface.
- `manuheart.config`: legacy/JSON/YAML config loading and normalization.
- `manuheart.models`: typed domain models.
- `manuheart.health`: health-state update and rollup engine.
- `manuheart.checkers`: ICMP/HTTP checker adapters backed by Python libraries.
- `manuheart.state`: previous compatibility-report state loading.
- `manuheart.reporting`: compatibility JSON report serialization and atomic writes.
- `manuheart.cli`: command-line adapter over the public API.

The health engine should remain independent of config file format and CLI parsing.

## Runtime dependencies

- Python 3.11+.
- `httpx` for HTTP/S checks.
- `icmplib` for ICMP checks.
- Optional `PyYAML` for YAML configuration.

## Deployment modes

### Recommended: supervised one-shot

Run `manuheart check --config <file>` from cron, systemd timer, CI, or another supervisor. This gives bounded lifecycle, simple logs, and straightforward rollback.

### Optional: daemon

Run `manuheart daemon --config <file>` only when built-in scheduling is specifically useful. Prefer an external supervisor for restart policy and lifecycle management.

## Report outputs

The tool writes compatibility JSON reports:

- `hoststatus`
- `groupstatus`
- `sysstatus`

Writes are atomic temp-file-and-replace operations.
