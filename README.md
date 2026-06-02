# Manuheart Python

Project folder for the Discord channel `#blakemere-healthcheck`.

Purpose: track Manuheart Python work, notes, and backlog for this channel.

## Product process

Target class: **Class 2 — Small Internal Tool**.

This project follows the workspace Software Product Development Process. See `docs/product-process-classification.md` for the tailoring notes, required lightweight artifacts, and approval boundaries.

## Rewrite direction

The goal is to recreate the original Bash Manuheart health checker from `../manuheart-bash` as a clean Python internal tool.

Initial architecture proposal:

- understand/preserve the Bash health model and report contract;
- default to one-shot execution;
- use typed Python domain models instead of shell-global associative arrays and delimiter serialization;
- expose most functionality through a reusable, well-defined Python library API;
- implement the CLI as a thin adapter over that API;
- keep parsing, health rollup, checking, state, reporting, API, and CLI concerns separate;
- preserve compatible legacy config and JSON outputs first;
- add first-class JSON/YAML configuration options that normalize into the same domain model.

See:

- `docs/bash-implementation-understanding.md`
- `docs/python-architecture-proposal.md`
