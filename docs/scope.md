# Scope

Status: Draft.

## In scope

- Python library for Manuheart health checking.
- CLI adapter over the public API.
- Legacy config loading for drop-in migration.
- JSON and optional YAML config loading.
- ICMP and HTTP/S checks.
- Host, group, and system rollup semantics.
- Compatibility JSON reports.
- One-shot and daemon operation.
- Local tests, examples, and migration-readiness checks.

## Out of scope for now

- Web UI.
- Alerting engine.
- Time-series storage.
- Metrics exporter.
- Distributed scheduler.
- SaaS/product hosting.
- Public internet exposure.
- Secret management beyond avoiding obvious leaks.
