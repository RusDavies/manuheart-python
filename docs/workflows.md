# UX and Workflow Notes

Status: Draft — CLI/API workflows only. No graphical UI exists.

## Primary workflows

### Library caller workflow

1. Import the public API from `manuheart.api`.
2. Load a legacy, JSON, or YAML configuration with `load_config()`.
3. Optionally pass overrides for paths, check period, run mode, or report destinations.
4. Run one check cycle with `run_check()` or `run_check_from_config()`.
5. Consume `CheckRunResult` directly, or write compatibility reports with `write_reports()`.

Library functions should return structured objects and should not print, exit the process, or hide warnings in terminal text.

### CLI one-shot workflow

1. Run `python -m manuheart check --config <file>` or installed `manuheart check --config <file>`.
2. CLI loads config through the public API.
3. CLI runs one check cycle through the public API.
4. CLI writes configured JSON status reports.
5. CLI exits `0` on successful execution.

`--once --config <file>` remains available as a compatibility-style invocation.

### CLI validate-config workflow

1. Run `manuheart validate-config --config <file>`.
2. CLI calls `validate_config()`.
3. Warnings/errors are rendered to stderr.
4. CLI exits `0` for valid config and non-zero for invalid config.

### Daemon workflow

1. Run `manuheart daemon --config <file>` under a supervisor.
2. Daemon mode repeatedly calls the same API-backed check/write path.
3. Shutdown/restart responsibility belongs to the supervisor.

Daemon mode is not the preferred default; one-shot remains safer and easier to supervise.

## UX principles

- Preserve Bash-compatible paths and report names where practical.
- Prefer explicit structured errors and warnings over clever terminal theatre.
- Keep the CLI boring: arguments in, reports out, clear exit code.
- Keep the library reusable: no hidden process exits, no terminal-only results.
