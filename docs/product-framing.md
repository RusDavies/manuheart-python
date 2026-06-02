# Product Framing

Status: Draft — internal-tool framing.

## Problem

The original Manuheart implementation provides useful host, group, and system health checking, but it is implemented in Bash. That makes the core behaviour harder to test, reuse, extend, and integrate cleanly from other Python tools.

## Goal

Create Manuheart Python as a reusable Python health-checking library with a well-defined public API and a CLI adapter. It should preserve the useful Bash health model and compatibility contract while improving maintainability, testability, and configuration ergonomics.

## Target users

- Russ / Blakemere operators using Manuheart as an internal health checker.
- Python code that wants to load Manuheart config, run health checks, and consume structured results.
- CLI users who need a drop-in-ish command for one-shot checks or supervised daemon operation.

## Success criteria

- Existing legacy config can be loaded for migration/drop-in use.
- JSON and YAML config can describe the same health model.
- Library callers can use the public API without invoking the CLI.
- CLI behaviour is implemented through the public API.
- Health rollup semantics match the documented Bash model unless intentionally changed.
- Reports are written atomically and remain compatible with current JSON consumers.

## Non-goals for initial release

- Web UI.
- Alerting engine.
- Time-series database.
- Metrics exporter.
- Distributed scheduler.
- Public SaaS or internet-facing service.
