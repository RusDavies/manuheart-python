# Manuheart Python Architecture Proposal

Status: Historical draft proposal; superseded where it mentions legacy Bash config input.
Target class: Class 2 — Small Internal Tool.

Current config posture: JSON and YAML are the supported Manuheart Python configuration formats. Legacy Bash `.conf` plus pipe-delimited `groups`/`hosts` files are no longer part of the Python product surface.

## Product goal

Recreate Manuheart as a sensible, well-architected Python internal tool that preserves the useful behavior of the Bash health checker while replacing shell-era mechanics with clean domain models, typed configuration, testable health-check execution, and maintainable packaging.

Manuheart Python should initially be boring in the best possible way: read config, check hosts, roll up health, write JSON, exit. No cathedral, no distributed observability fever dream, no “just one Kubernetes operator” nonsense.

## Recommended design posture

Build this as a reusable Python library with a CLI on top, not as a CLI that happens to have importable files. The CLI is an adapter; the library API is the product core.

Recommended defaults:

- Python 3.11+.
- Source layout under `src/manuheart/`.
- A stable, documented public library API exposed from `manuheart` and/or `manuheart.api`.
- `pyproject.toml` packaging.
- `pytest` tests.
- `ruff` for lint/format.
- `mypy` or `pyright` later if useful; do not block the first implementation on maximal typing ceremony.
- One-shot command as the default execution path.
- Optional daemon loop implemented as a thin wrapper over the one-shot runner.

## Architecture overview

```text
CLI adapter
 │
 ▼
Public library API
 │
 ▼
Application service / runner
 │
 ├── configuration loader
 │    ├── JSON config parser
 │    └── YAML config parser
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
│   ├── localhost/
│   │   ├── manuheart.json
│   │   └── manuheart.yaml
│   └── deployment-test/
│       └── public-smoke.json
├── src/
│   └── manuheart/
│       ├── __init__.py
│       ├── __main__.py
│       ├── api.py
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

#### `api.py`

Defines the public reusable library API. This should be the stable surface that other Python code can import without knowing or caring about CLI parsing, terminal output, process exit codes, or argparse/click details.

The API should be small, explicit, and versioned by behaviour rather than vibes. Initial public functions/classes should be enough to support the CLI and downstream library users without exposing internal implementation clutter.

Recommended initial API shape:

```python
from pathlib import Path
from manuheart.api import (
    CheckRunResult,
    ConfigFormat,
    LoadedConfiguration,
    load_config,
    run_check,
    run_check_from_config,
    validate_config,
)

loaded = load_config(Path("manuheart.yaml"), config_format=ConfigFormat.AUTO)
result = run_check(loaded)
```

Candidate public API:

- `load_config(path, *, config_format=ConfigFormat.AUTO, overrides=None) -> LoadedConfiguration`
- `validate_config(path, *, config_format=ConfigFormat.AUTO, overrides=None) -> ValidationResult`
- `run_check(config: LoadedConfiguration, *, checkers: CheckerMap | None = None, clock: ClockSource | None = None) -> CheckRunResult`
- `run_check_from_config(path, *, config_format=ConfigFormat.AUTO, overrides: ConfigOverridesInput | None = None, checkers: CheckerMap | None = None, clock: ClockSource | None = None) -> CheckRunResult`
- `write_reports(result: CheckRunResult, destinations: ReportDestinations | None = None) -> None`
- `run_daemon(config: LoadedConfiguration, *, checkers: CheckerMap | None = None, clock: ClockSource | None = None, sleep: SleepFunction | None = None, max_cycles: int | None = None, on_event: DaemonEventCallback | None = None) -> int`

Public API model exports:

- `ConfigFormat`
- `CheckType`
- `Status`
- `HostDefinition`
- `GroupDefinition`
- `HostState`
- `GroupState`
- `SystemState`
- `CheckResult`
- `Checker`
- `CheckerMap`
- `ClockSource`
- `ConfigOverrides`
- `ConfigOverridesInput`
- `DaemonEventCallback`
- `LoadedConfiguration`
- `CheckRunResult`
- `ValidationResult`
- `ReportDestinations`
- `SleepFunction`

API design rules:

- no CLI-only concepts in public API return values;
- no direct printing from library functions;
- no `sys.exit()` from library code;
- return structured warnings/errors where practical;
- raise typed exceptions only for boundary failures that callers cannot reasonably ignore;
- allow dependency injection for checkers, clock sources, daemon sleepers, and daemon event callbacks through named public types;
- keep internal modules importable but not part of the supported API contract unless exported deliberately.

The CLI should be implemented by calling this API. If a feature cannot be used through the API, it should not be considered properly implemented.

#### `cli.py`

Owns command-line parsing only.

Current CLI:

```bash
manuheart check --config ./etc/manuheart/manuheart.json
manuheart check --config ./etc/manuheart/manuheart.yaml
manuheart daemon --config ./etc/manuheart/manuheart.json --check-period 30
manuheart validate-config --config ./etc/manuheart/manuheart.json
```

The CLI infers config format from `.json`, `.yaml`, or `.yml` by default, with an optional explicit override such as `--config-format json|yaml` for unusual file names.

Do not put business logic in CLI handlers. Parse arguments, call the public library API, render output, and translate API results into process exit codes. The CLI should use the same API that a Python caller would use.

#### `models.py`

Defines typed domain objects.

Suggested models:

- `CheckType`: enum: `ICMP`, `HTTP`, `HTTPS`.
- `Status`: enum: `UP`, `DOWN`, `UNKNOWN`.
- `GroupDefinition`.
- `HostDefinition`.
- `HostState`, including checker diagnostic `detail` text.
- `GroupState`.
- `SystemState`.
- `CheckResult`.
- `EffectiveConfig`.

Use dataclasses or Pydantic. For this internal tool, standard-library dataclasses are probably enough. Use Pydantic only if config validation gets more complex.

#### `config.py`

Loads and validates:

- defaults;
- structured JSON configuration;
- structured YAML configuration, if PyYAML is installed;
- CLI overrides.

It should return an explicit `EffectiveConfig` plus parsed definitions. Structured JSON/YAML should be strict by default because users choosing structured config are asking for less shell-era ambiguity, not a more decorative failure mode.

Current design:

- JSON loader for a single structured JSON file.
- YAML loader for a single structured YAML file.
- Shared validation/normalization after format-specific parsing so both formats feed the same domain models.

Structured JSON/YAML use the same logical model, for example:

```yaml
runtime:
  var_dir: ./var/manuheart
  check_period: 30
  status_files:
    hosts: status/hoststatus
    groups: status/groupstatus
    systems: status/sysstatus
checks:
  http:
    connect_timeout: 3
    max_time: 5
groups:
  - name: elasticsearch-host
    system: elasticsearch
    critical: true
    type: icmp
    min_count: 1
    failure_grace: 3
hosts:
  - name: burns
    group: elasticsearch-host
    url: n/a
```

Equivalent JSON should be accepted with the same keys. Internally, both JSON and YAML normalize booleans, enum values, paths, and counts into the same `GroupDefinition`, `HostDefinition`, and `EffectiveConfig` objects.

Format policy:

- JSON is first-class and requires no extra runtime dependency;
- YAML is first-class when the optional YAML extra is installed, e.g. `manuheart[yaml]`;
- unsupported config formats fail clearly;
- do not reintroduce historical Bash quirks unless there is a concrete user need.

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

`run_daemon()` should just sleep and repeatedly call the same API-backed one-shot runner with signal-aware shutdown.

## Product strategy

### Build the clean product first

The supported product contract is now:

- JSON/YAML config formats;
- explicit CLI subcommands;
- JSON report locations;
- JSON top-level structure;
- one-shot default;
- daemon option;
- rollup semantics.

### Keep configuration structured

JSON and YAML configuration should be supported as inputs to the same normalized domain model, not as separate product behavior. The health engine must not care whether definitions came from JSON or YAML.

Recommended precedence remains:

1. CLI overrides
2. selected config file
3. defaults

For structured config, group and host definitions should normally live in the same file. If later needed, add includes/imports carefully; do not start with recursive config includes unless we have an actual use case. Recursive includes are where sanity goes to die.

### Improve behind the contract

Internally, Python should use:

- typed dataclasses/enums;
- explicit return values;
- exceptions only at boundaries;
- warnings collection instead of scattered shell output;
- deterministic ordering;
- dependency injection for checkers and clock;
- a documented reusable library API with the CLI implemented as a thin adapter over it.

### Defer unless needed

Do not build these in v1:

- web UI;
- time-series storage;
- alerting engine;
- distributed scheduler;
- plugin framework;
- TOML migration;
- metrics exporter.

Those may become good ideas later. Right now they are how small tools wake up owning a pager.

## Proposed implementation phases

### Phase 1: Project skeleton, public API shell, and fixtures

Deliverables:

- `pyproject.toml`;
- `src/manuheart/` package;
- `src/manuheart/api.py` with initial public API placeholders and exported models once available;
- `pytest` setup;
- sample `examples/localhost` JSON/YAML fixtures;
- tests that parse structured sample config.

Gate:

- `python -m pytest` passes;
- `python -m manuheart --help` works;
- a smoke import such as `python -c "import manuheart; import manuheart.api"` works.

### Phase 2: Config parser and domain models

Deliverables:

- dataclasses/enums;
- normalized loaded-configuration model;
- JSON config parser;
- YAML config parser behind an optional dependency;
- warning/error model;
- duplicate/invalid record handling.

Gate:

- JSON/YAML parser tests cover equivalent valid structured config, type validation, missing required keys, duplicate groups/hosts, invalid enum values, and CLI override precedence;
- JSON and YAML produce equivalent normalized domain objects for equivalent input.

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

### Phase 5: API-backed CLI, daemon loop, and docs

Deliverables:

- `manuheart check`;
- `manuheart daemon`;
- validate-config command;
- README quick start;
- rollback/disable note;
- basic operations notes.

Gate:

- CLI tests prove commands call API-level functions rather than duplicating business logic.
- public API smoke tests pass.
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
