# Scope

Status: Draft.

## In scope

- Python library for Manuheart health checking.
- CLI adapter over the public API.
- JSON and optional YAML config loading for first-class new use.
- Legacy config loading as a convenience/import path.
- ICMP and HTTP/S checks.
- Host, group, and system rollup semantics.
- Clean typed JSON reports with useful continuity from the Bash report model.
- One-shot and daemon operation.
- Local tests, examples, public smoke config, and regression checks.

## Out of scope for now

- Web UI.
- Alerting engine.
- Time-series storage.
- Metrics exporter.
- Distributed scheduler.
- SaaS/product hosting.
- Public internet exposure.
- Secret management beyond avoiding obvious leaks.
