# Product Framing

Status: Draft — internal-tool framing.

## Problem

The original Manuheart implementation provides useful host, group, and system health checking, but it is implemented in Bash. That makes the core behaviour harder to test, reuse, extend, and integrate cleanly from other Python tools.

## Goal

Create Manuheart Python as a reusable Python health-checking library with a well-defined public API and a CLI adapter. It should preserve the useful Bash health model where it still makes sense while prioritizing maintainability, testability, and configuration ergonomics over drop-in replacement behaviour.

## Target users

- Russ / Blakemere operators using Manuheart as an internal health checker.
- Python code that wants to load Manuheart config, run health checks, and consume structured results.
- CLI users who need straightforward one-shot checks or supervised daemon operation.

## Success criteria

- JSON and YAML config can describe the health model cleanly for new use.
- Existing legacy config can be loaded as an import/convenience path if old files appear later.
- Library callers can use the public API without invoking the CLI.
- CLI behaviour is implemented through the public API.
- Health rollup semantics are documented and tested.
- Reports are written atomically as clean typed JSON.

## Non-goals for initial release

- Web UI.
- Alerting engine.
- Time-series database.
- Metrics exporter.
- Distributed scheduler.
- Public SaaS or internet-facing service.
