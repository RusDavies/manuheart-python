# Bash Implementation Understanding

Status: Draft analysis for the Manuheart Python rewrite.

Source inspected: `../manuheart-bash`.

## Executive summary

The Bash Manuheart project is a small health-checking tool. It loads host and group configuration, runs ICMP or HTTP(S) checks, rolls individual host health into group health, rolls group health into system health, and writes three JSON status files for other tools to consume.

The current Bash implementation has been stabilized and documented, but its architecture is still constrained by shell: global associative arrays, delimiter-based internal serialization, lock files, rendezvous files, sourced libraries, and shell-specific process handling. The Python rewrite should preserve the useful operating model while replacing the shell machinery with explicit typed domain objects, deterministic pure functions, and testable adapters.

## What the Bash tool does

### Runtime modes

The entry point is `bin/manuheart.sh`.

It supports two modes:

- `--once`: default. Load config, run one health-check cycle, write reports, exit.
- `--daemon`: keep running and schedule repeated health-check cycles using `CHECKPERIOD`.

The Bash docs explicitly recommend one-shot mode for cron, systemd timers, CI smoke tests, and bounded operation. Daemon mode exists for environments that want Manuheart itself to schedule checks.

### Configuration

The main config file is `etc/manuheart/manuheart.conf`. It uses `KEY: value` lines, supports a small allow-list of configurable keys, expands macros such as `_SCRIPTDIR_`, `_CONFIGDIR_`, `_VARDIR_`, and merges configuration in this priority order:

1. CLI options
2. config file
3. defaults

Important values include:

- `CONFIGDIR`
- `CONFIGFILE`
- `VARDIR`
- `LOGFILE`
- `LOGLEVEL`
- `CHECKPERIOD`
- `GROUPFILE`
- `HOSTFILE`
- `HOSTSTATUSFILE`
- `GROUPSTATUSFILE`
- `SYSSTATUSFILE`

The Bash config reader no longer sources config as code, which is the correct survival instinct.

### Group file format

The group file is pipe-delimited:

```text
group | system | critical | type | min instance count | failure count grace
```

Example:

```text
elasticsearch-host | elasticsearch | yes | icmp | 1 | 3
```

Fields:

- `group`: unique group name.
- `system`: system name this group rolls up into.
- `critical`: `yes` or `no`; controls whether a down group can bring down a system.
- `type`: `icmp`, `http`, or `https`; selects checker behavior for hosts in the group.
- `min instance count`: number of hosts that must be up for the group to be up.
- `failure count grace`: consecutive host failures allowed before the host is marked down; negative means infinite grace.

Parsing behavior:

- full-line comments beginning with `#` are ignored;
- inline comments are stripped only when `#` is preceded by whitespace;
- URL fragments such as `path#fragment` are preserved;
- `|` is the delimiter and is forbidden inside fields;
- duplicate group names are ignored with a warning;
- invalid records are ignored with warnings.

### Host file format

The host file is also pipe-delimited:

```text
host | group | uri
```

Example:

```text
localhost | localhost-icmp | n/a
```

For ICMP groups the URI is commonly `n/a`. For HTTP(S) groups it must look like an HTTP endpoint.

Host records are keyed as `group/hostname` to make state transfer deterministic across config reloads. This means the current Bash implementation intentionally treats duplicate `group + host` rows as duplicates, even if the URL differs. That matters for compatibility.

### Health model

The model has three layers:

```text
host status -> group status -> system status
```

#### Host status

Each configured host belongs to one group. The group type determines the checker:

- `icmp`: ping the host name.
- `http` / `https`: run a `curl --head --location` style HTTP check against the URI.

Host state fields:

- `name`
- `group`
- `url`
- `lastUp`
- `lastChecked`
- `failCount`
- `status`

On success:

- `status = up`
- `failCount = 0`
- `lastUp = now`
- `lastChecked = now`

On failure:

- `lastChecked = now`
- `failCount` increments
- `status` changes to `down` only when `failCount >= group.failGrace`
- negative `failGrace` means failures are counted but the threshold never forces `down`

### Group status

Groups count how many member hosts are currently `up`.

Group state fields:

- `name`
- `system`
- `critical`
- `type`
- `minCount`
- `failGrace`
- `lastUp`
- `lastChecked`
- `instanceCount`
- `status`

Rules:

- if no configured hosts are seen for a group, status is `unknown`;
- if `instanceCount >= minCount`, status is `up`;
- otherwise status is `down`;
- when up, `lastUp` and `lastChecked` update;
- when down, `lastChecked` updates and `lastUp` is preserved.

A non-critical group still appears in output, but does not by itself bring the system down.

### System status

Systems are produced by rolling up groups with the same `system` field.

System state fields:

- `name`
- `lastUp`
- `lastChecked`
- `failureCount`
- `status`

Rules:

- if any critical group for the system is `down`, the system is `down`;
- otherwise the system is `up`;
- when up, `failureCount = 0`, `lastUp = now`, `lastChecked = now`;
- when down, `failureCount` increments and `lastChecked = now`.

### Checkers

ICMP checker:

- validates the hostname contains only conservative hostname/IP characters;
- runs one ping with a short timeout;
- treats zero packet loss as success.

HTTP checker:

- validates the URL starts with `http://` or `https://`;
- uses `curl --head --location --connect-timeout 3 --max-time 5`;
- treats only 2xx responses as healthy.

### Output

The Bash tool writes three JSON reports:

- `hoststatus`
- `groupstatus`
- `sysstatus`

Writes are atomic: generate a temp file in the target directory, then move it into place.

The output values are currently string-heavy because they come from shell serialization. The Python rewrite can support a compatibility mode that preserves this shape while also offering typed/internal representations.

### State and IPC

The Bash code uses global associative arrays:

- `VARS`
- `HOSTS`
- `GROUPS`
- `SYSTEMS`

It serializes host/group/system records into pipe-delimited strings internally and stores some state in rendezvous files so config and health tasks can exchange data. This is an implementation workaround, not a product requirement. Python should not copy it unless there is a specific compatibility need.

### Locking and process handling

The Bash implementation uses lock files and a PID file to avoid concurrent config/health work and to clean up daemon children. The Python rewrite should avoid needing most of this by defaulting to one-shot operation. If daemon mode is retained, it should be implemented as a supervised loop with clear signal handling, not shell-style child process bookkeeping.

## Behaviors to preserve initially

The first Python version should preserve these behaviors unless Russ explicitly changes direction:

- one-shot mode as the default;
- optional daemon mode;
- compatible host/group config formats;
- compatible config precedence: CLI > config file > defaults;
- compatible host/group/system rollup semantics;
- compatible JSON report names and top-level keys;
- atomic report writes;
- duplicate and invalid config records are warned and ignored, not fatal by default;
- `failGrace < 0` means infinite grace;
- HTTP checks treat only 2xx as healthy;
- group criticality controls system status.

## Behaviors worth improving

The Python rewrite should deliberately improve:

- typed records instead of delimiter-serialized strings;
- pure, unit-testable rollup logic;
- structured validation errors and warnings;
- explicit state store instead of rendezvous files;
- clearer config schema;
- safer URL/host validation;
- predictable ordering in output for deterministic tests;
- robust logging;
- dependency injection for checkers and clock in tests;
- better packaging and CLI UX.
