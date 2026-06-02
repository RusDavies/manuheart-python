# Manuheart Python Architecture Proposal

Status: Draft proposal.
Target class: Class 2 — Small Internal Tool.

## Product goal

Recreate Manuheart as a sensible, well-architected Python internal tool that preserves the useful behavior of the Bash health checker while replacing shell-era mechanics with clean domain models, typed configuration, testable health-check execution, and maintainable packaging.

Manuheart Python should initially be boring in the best possible way: read config, check hosts, roll up health, write JSON, exit. No cathedral, no distributed observability fever dream, no “just one Kubernetes operator” nonsense.

## Recommended design posture

Build this as a small Python package with a CLI, not as a web app and not as a daemon-first service.

Recommended defaults:

- Python 3.11+.
- Source layout under `src/manuheart/`.
- `pyproject.toml` packaging.
- `pytest` tests.
- `ruff` for lint/format.
- `mypy` or `pyright` later if useful; do not block the first implementation on maximal typing ceremony.
- One-shot command as the default execution path.
- Optional daemon loop implemented as a thin wrapper over the one-shot runner.

## Architecture overview

```text
CLI
 │
 ▼
Application service / runner
 │
 ├── configuration loader
 │    ├── main config parser
 │    ├── groups parser
 │    └── hosts parser
 │
 ├── state store
 │    ├── previous host/group/system state
 │    └── current in-memory state
 │
 ├── health engine
 │    ├── checker registry
 │    ├── host check execution
 │    ├── group rollup
 │    └── system rollup
 │
 └── reporters
      ├── host JSON report
      ├── group JSON report
      └── system JSON report
```

Keep the core health engine pure where possible. Network checks are inherently impure; everything after receiving check results should be deterministic and unit-testable.

## Proposed package structure

```text
manuheart-python/
├── pyproject.toml
├── README.md
├── TODO.md
├── docs/
│   ├── bash-implementation-understanding.md
│   ├── product-process-classification.md
│   └── python-architecture-proposal.md
├── examples/
│   └── localhost/
│       ├── manuheart.conf
│       ├── groups
│       └── hosts
├── src/
│   └── manuheart/
│       ├── __init__.py
│       ├── __main__.py
│       ├── cli.py
│       ├── app.py
│       ├── config.py
│       ├── models.py
│       ├── health.py
│       ├── checkers.py
│       ├── state.py
│       ├── reporting.py
│       ├── locking.py
│       ├── logging.py
│       └── errors.py
└── tests/
    ├── test_config.py
    ├── test_health_rollup.py
    ├── test_reporting.py
    ├── test_cli.py
    └── fixtures/
```

### Module responsibilities

#### `cli.py`

Owns command-line parsing only.

Recommended CLI:

```bash
manuheart check --config ./etc/manuheart/manuheart.conf --var-dir ./var/manuheart
manuheart daemon --config ./etc/manuheart/manuheart.conf --check-period 30
manuheart validate-config --config ./etc/manuheart/manuheart.conf
```

For Bash compatibility, also allow:

```bash
manuheart --once --config ...
manuheart --daemon --config ...
```

Do not put business logic in CLI handlers. Parse arguments, build an application config, call `app.run_once()` or `app.run_daemon()`.

#### `models.py`

Defines typed domain objects.

Suggested models:

- `CheckType`: enum: `ICMP`, `HTTP`, `HTTPS`.
- `Status`: enum: `UP`, `DOWN`, `UNKNOWN`.
- `GroupDefinition`.
- `HostDefinition`.
- `HostState`.
- `GroupState`.
- `SystemState`.
- `CheckResult`.
- `EffectiveConfig`.

Use dataclasses or Pydantic. For this internal tool, standard-library dataclasses are probably enough. Use Pydantic only if config validation gets more complex.

#### `config.py`

Loads and validates:

- defaults;
- main `KEY: value` config file;
- CLI overrides;
- group definitions;
- host definitions.

It should return an explicit `EffectiveConfig` plus parsed definitions and a list of warnings. Invalid records should usually be skipped with warnings to preserve Bash behavior.

Important compatibility rules:

- strip comments like the Bash parser: leading `#`, and whitespace-before-`#` inline comments;
- preserve `#` inside URLs/fragments;
- split on `|`;
- trim whitespace;
- forbid extra fields;
- warn/ignore duplicate group names;
- warn/ignore duplicate `group/host` records;
- validate host group references after groups are loaded.

#### `checkers.py`

Defines checker interfaces and concrete implementations.

Suggested interface:

```python
class Checker(Protocol):
    def check(self, host: HostDefinition, group: GroupDefinition) -> CheckResult: ...
```

Implementations:

- `IcmpChecker`: probably calls system `ping` initially for compatibility and simplicity.
- `HttpChecker`: use `urllib`/`http.client` or `requests`/`httpx`.

Recommendation: use standard-library HTTP initially unless redirect/timeout behavior becomes annoying; then use `httpx`. Avoid dragging in a dependency just to cosplay as enterprise software.

The checker layer should be easy to fake in tests.

#### `health.py`

Core health engine.

Responsibilities:

- execute host checks using a checker registry;
- update host state using failure grace;
- roll host states into group states;
- roll group states into system states.

Design these as pure-ish functions:

```python
update_host_state(previous, definition, group, result, now) -> HostState
rollup_groups(group_defs, host_states, previous_group_states, now) -> dict[str, GroupState]
rollup_systems(group_states, previous_system_states, now) -> dict[str, SystemState]
```

That gives us precise tests for the tricky stuff: grace thresholds, non-critical groups, min instance count, unknown groups, and failure count resets.

#### `state.py`

Owns persistence of previous state between runs.

The Bash tool carries state through in-memory arrays and rendezvous files. A one-shot Python tool needs a clear state persistence decision.

Recommended initial approach:

- read previous state from existing JSON report files if present;
- keep current state in memory during the run;
- write fresh JSON reports atomically.

This preserves `failCount` and `lastUp` across one-shot runs without inventing another database. If the format later needs expansion, add an internal `state.json` alongside compatibility reports.

#### `reporting.py`

Serializes reports and writes them atomically.

Responsibilities:

- convert typed state objects into compatibility JSON;
- preserve top-level keys: `hosts`, `groups`, `systems`;
- decide whether numeric fields are emitted as strings or numbers.

Recommendation for v1: preserve Bash-compatible output as closely as possible, even if that means string values for counts. Add a cleaner typed output later only if someone needs it.

#### `locking.py`

For one-shot mode, use a simple process lock around the run if needed.

Recommended:

- do not reproduce all Bash PID-file machinery;
- use an advisory lock file to prevent overlapping writes when invoked by cron/systemd;
- keep locking small and optional/configurable.

#### `app.py`

Coordinates the application:

```python
def run_once(cli_options) -> RunResult:
    config = load_effective_config(cli_options)
    previous = load_previous_state(config)
    current = run_health_cycle(config, previous)
    write_reports(config, current)
    return result
```

`run_daemon()` should just sleep and repeatedly call `run_once()` with signal-aware shutdown.

## Compatibility strategy

### Preserve first

The first milestone should preserve the Bash contract:

- config formats;
- CLI flags where practical;
- JSON report locations;
- JSON top-level structure;
- one-shot default;
- daemon option;
- rollup semantics.

### Improve behind the contract

Internally, Python should use:

- typed dataclasses/enums;
- explicit return values;
- exceptions only at boundaries;
- warnings collection instead of scattered shell output;
- deterministic ordering;
- dependency injection for checkers and clock.

### Defer unless needed

Do not build these in v1:

- web UI;
- time-series storage;
- alerting engine;
- distributed scheduler;
- plugin framework;
- YAML/TOML migration;
- metrics exporter.

Those may become good ideas later. Right now they are how small tools wake up owning a pager.

## Proposed implementation phases

### Phase 1: Project skeleton and compatibility fixtures

Deliverables:

- `pyproject.toml`;
- `src/manuheart/` package;
- `pytest` setup;
- copy/sample `examples/localhost` fixtures;
- tests that parse Bash sample groups/hosts/config.

Gate:

- `python -m pytest` passes.
- `python -m manuheart --help` works.

### Phase 2: Config parser and domain models

Deliverables:

- dataclasses/enums;
- main config parser;
- groups parser;
- hosts parser;
- warning model;
- duplicate/invalid record handling.

Gate:

- parser tests cover comments, URL fragments, duplicate groups, duplicate hosts, invalid group references, bad critical/type/min/grace fields.

### Phase 3: Health engine with fake checkers

Deliverables:

- host state update logic;
- group rollup logic;
- system rollup logic;
- checker registry interface;
- fake checker tests.

Gate:

- tests cover up/down/unknown, grace thresholds, infinite grace, min instance count, non-critical down groups, system failure count reset/increment.

### Phase 4: Real checkers and report writing

Deliverables:

- ICMP checker;
- HTTP checker;
- JSON report serializer;
- atomic writes;
- previous-state loading from reports.

Gate:

- localhost smoke test writes parseable `hoststatus`, `groupstatus`, `sysstatus`.
- tests mock network behavior; smoke can use localhost only.

### Phase 5: CLI, daemon loop, and docs

Deliverables:

- `manuheart check` / compatibility `--once`;
- `manuheart daemon` / compatibility `--daemon`;
- validate-config command;
- README quick start;
- rollback/disable note;
- basic operations notes.

Gate:

- CLI tests pass.
- one-shot smoke passes.
- daemon loop has a bounded test with fake sleep/checker or is manually smoke-tested with a short interval.

## Security and privacy notes

This is an internal health-checking tool, but it still touches infrastructure details.

Security posture:

- configuration files may reveal hostnames, internal service names, URLs, and topology;
- logs must not include secrets in URLs if credentials accidentally appear;
- no config-as-code execution;
- validate hostnames and URLs before invoking subprocesses;
- if using subprocess `ping`, pass arguments as lists, never through a shell;
- avoid following arbitrary local file paths from untrusted sources;
- warn before deployment/shared use.

Privacy posture:

- no personal data should be required;
- output reports should be treated as internal operational data;
- documentation should avoid publishing internal topology.

## Rollback / disable note

For the initial internal-tool rollout:

- keep the Bash implementation available until Python output is verified against equivalent fixtures;
- run Python in one-shot mode first;
- disable by removing the cron/systemd timer or reverting the wrapper to the Bash command;
- generated JSON status files can be replaced by the Bash output if consumers depend on them.

## AI-agent operation boundary

AI agents may autonomously:

- inspect code and docs;
- create branches;
- add tests;
- implement parser/engine/reporting code;
- run local test/smoke gates;
- update internal docs and TODOs.

Human approval is required before:

- deploying to shared infrastructure;
- changing monitored host lists for real environments;
- sending alerts or messages externally;
- deleting/replacing the Bash implementation;
- handling sensitive infrastructure secrets;
- accepting risk on broken/partial health reporting.

## Recommended first implementation choice

Start with parser + models + pure health engine. That is the hardest logic to get correct and the easiest to test without touching the network. Once that is solid, adding real ICMP/HTTP adapters is straightforward.

In short: port the product behavior, not the Bash trauma.
