# Health State Semantics

Status: Draft decision record.

## Startup behaviour

Manuheart does not write an initial blank or synthetic status report before it knows anything.

The runtime sequence is:

1. Load configuration.
2. Load previous reports if present.
3. Run the configured checks.
4. Roll host state into group state and group state into system state.
5. Write reports atomically.

Therefore, the first report from a fresh process is written after a check cycle has completed. It may still contain `unknown`, but not because Manuheart emitted an unobserved startup placeholder.

## Meaning of states

`up` means the object currently satisfies its health requirement.

`down` means the object has been non-healthy for longer than its configured grace allows, or it is otherwise impossible for a required parent object to satisfy its health requirement.

`unknown` means Manuheart has insufficient stable evidence to say `up` or `down` yet. It is a pending/indeterminate monitoring state, not a green state.

External monitoring systems may choose to alert on `unknown`, but within Manuheart it should mean "not enough evidence yet", while `down` means "bad beyond grace".

## Host state diagram

Host grace applies to non-`up` observations, including failed checks, timeouts, DNS failures, checker exceptions, or future inconclusive checker results.

A host should be marked `down` only when it has remained `down` or `unknown` for more than the configured grace allows.

```text
No previous state
  successful check
    -> UP, fail_count = 0

  non-UP check
    -> UNKNOWN, fail_count = 1

UP
  successful check
    -> UP, fail_count = 0

  non-UP check within grace
    -> UP, fail_count += 1
    # preserve last known good state during grace

  non-UP check beyond grace
    -> DOWN

UNKNOWN
  successful check
    -> UP, fail_count = 0

  non-UP check within grace
    -> UNKNOWN, fail_count += 1

  non-UP check beyond grace
    -> DOWN

DOWN
  successful check
    -> UP, fail_count = 0

  non-UP check
    -> DOWN, fail_count += 1
```

## Group rollup semantics

Group rollup must preserve host grace semantics. A group should not become `down` merely because a host is temporarily `unknown` within grace if that host could still satisfy `min_count`.

Recommended group state rules:

```text
if min_count == 0:
  UP
elif UP hosts >= min_count:
  UP
elif UP hosts + UNKNOWN hosts >= min_count:
  UNKNOWN
else:
  DOWN
```

This means:

- `unknown` hosts are not counted as healthy;
- `unknown` hosts can keep a group in `unknown` while grace is still active;
- once too many hosts are `down`, the group becomes `down`;
- empty critical groups with `min_count > 0` become `down` because they cannot satisfy the required minimum;
- empty optional groups with `min_count > 0` are still unable to satisfy their configured minimum, so callers should configure `min_count: 0` for truly optional empty groups.

## System rollup semantics

Recommended system state rules:

```text
if any critical group is DOWN:
  DOWN
elif any critical group is UNKNOWN:
  UNKNOWN
else:
  UP
```

Non-critical group failures should not make the system `down`, but they should remain visible in group reports.

## Current implementation note

As of this decision record, the code does not fully implement these semantics. In particular, group and system rollups still need to be adjusted so host grace and critical `unknown` states are represented correctly. Track implementation through `TODO.md`.
