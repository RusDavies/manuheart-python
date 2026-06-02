# Localhost Bash-vs-Python Compatibility Differences

Status: Current accepted migration notes for the localhost synthetic fixture.

## Hard compatibility contract

The Python implementation must keep these Bash-compatible surfaces for the localhost fixture:

- report filenames remain `hoststatus`, `groupstatus`, and `sysstatus` unless overridden;
- top-level JSON keys remain `hosts`, `groups`, and `systems`;
- record identities match Bash output:
  - hosts by `name` + `group`;
  - groups by `name`;
  - systems by `name`;
- stable descriptive fields match where applicable: `name`, `group`, `url`, `system`, `type`, and `status`;
- status values remain enum-like strings: `up`, `down`, `unknown`.

The compatibility script treats mismatches in those fields as failures.

## Accepted migration differences

The Python implementation intentionally uses a cleaner default report format rather than reproducing every Bash output scar.

Accepted differences:

- record order is not compatibility-significant;
- whitespace/pretty-printing is not compatibility-significant;
- inner record fields use Pythonic `snake_case` instead of Bash camel-ish names:
  - `lastUp` -> `last_up`;
  - `lastChecked` -> `last_checked`;
  - `failCount` -> `fail_count`;
  - `minCount` -> `min_count`;
  - `failGrace` -> `failure_grace`;
  - `instanceCount` -> `instance_count`;
  - `failureCount` -> `failure_count`;
- numeric fields are JSON numbers instead of strings;
- `critical` is a JSON boolean instead of `"yes"` / `"no"`;
- timestamps are ISO-8601 strings instead of locale-formatted date strings;
- live timestamps and live status can vary slightly by runtime environment, but the localhost fixture currently checks stable status equivalence.

## Current verification command

```bash
.venv/bin/python scripts/check_localhost_compatibility.py
```

The script now prints accepted migration differences after passing hard compatibility checks, so future changes are less likely to smuggle in accidental format drift while wearing a fake moustache.

## Legacy-output mode posture

No explicit legacy-compatible report writer is currently planned. The project treats Bash-shaped inner fields as an accepted migration difference, not a default compatibility requirement.

If a real downstream consumer requires exact legacy fields, add a separate opt-in legacy report mode then. Until that evidence exists, the default report path stays clean typed JSON.
