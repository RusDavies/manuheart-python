# Manuheart Python

Project folder for the Discord channel `#blakemere-healthcheck`.

Purpose: track Manuheart Python work, notes, and backlog for this channel.


## Quick start

Install for local development:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev,yaml]'
```

Run one check cycle with JSON config:

```bash
.venv/bin/python -m manuheart check --config examples/localhost/manuheart.json
```

Validate config without running checks:

```bash
.venv/bin/python -m manuheart validate-config --config examples/localhost/manuheart.json
```

Structured JSON/YAML configs can tune HTTP checks under `checks.http`:

```json
{
  "checks": {
    "http": {
      "method": "HEAD",
      "fallback_to_get": true,
      "connect_timeout": 3,
      "max_time": 5
    }
  }
}
```

`method` may be `HEAD` or `GET`. The default remains `HEAD`, with safe `GET` fallback enabled for servers that reject or do not implement `HEAD`.

Compatibility-style legacy invocation:

```bash
.venv/bin/python -m manuheart --once --config examples/localhost/manuheart.conf
```

Daemon mode prints lifecycle/cycle messages to stderr and exits cleanly on keyboard interrupt:

```bash
.venv/bin/python -m manuheart daemon --config examples/localhost/manuheart.json
```

Use the library API directly:

```python
from manuheart.api import load_config, run_check, write_reports

config = load_config("examples/localhost/manuheart.json")
result = run_check(config)
write_reports(result)
```

Run the local verification gate:

```bash
.venv/bin/python -m ruff check src tests scripts
.venv/bin/python -m mypy src/manuheart
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_localhost_compatibility.py
.venv/bin/python scripts/check_clean_install.py
```

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
