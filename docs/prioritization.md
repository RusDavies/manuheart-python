# Prioritization Notes

Status: Current direction — good internal Python implementation, not drop-in Bash replacement.

## Priority decision

Russ clarified that Manuheart Python does **not** need to be a drop-in replacement for an existing Bash deployment because there are no existing installations of the original Bash version to replace.

The Bash implementation remains useful reference material for:

- the host/group/system health model;
- legacy config import support;
- rollup semantics worth preserving;
- migration-risk checks for anyone who does have old files later.

It is no longer the primary product constraint.

## Current priority order

1. Keep the Python library/API clean, typed, and reusable.
2. Keep the CLI as a thin adapter over the public API.
3. Prefer first-class JSON/YAML configuration for new use.
4. Keep legacy config loading as an import/convenience path, not the default product identity.
5. Preserve useful report continuity where cheap, but do not contort the implementation for exact Bash-shaped output.
6. Keep the release posture internal/private unless Russ explicitly approves wider publication.
7. Use public-smoke or approved internal configs for deployment validation.

## Current recommendation

Treat the current project as a working internal-tool product that is ready for controlled deployment testing, not as a production replacement exercise. The next useful proof is running it in a real target environment with either the public smoke config or an approved internal config, then deciding whether any operational polish is needed.

Release posture is documented in `docs/release-posture.md`: private/internal by default, no public publishing, and no deployment against real monitored hosts without explicit approval.

## Fixture-source decision

Russ decided to continue with **synthetic compatibility fixtures only** for now. Real-world Manuheart Bash configs should not be used unless separately approved and sanitized.

Implication: the existing synthetic fixtures are enough for regression coverage and historical-reference checks. Future fixture work should focus on realistic new-product scenarios unless real legacy configs are explicitly approved.

## Compatibility depth decision

Previous compatibility work is now treated as regression evidence, not as the main product objective.

Implication: keep `scripts/check_localhost_compatibility.py` because it catches accidental changes to report surfaces and health semantics. Do not add more exact Bash-output work unless a real consumer appears.

## Output-format decision

Russ decided to **go cleaner from the get-go**.

Implication: Bash output can be used as historical reference, but Python does not need to preserve ugly legacy output details as the default. The default Python report format should prefer clean typed JSON where practical.

## Report-format implementation priority

Clean typed report output is the default.

Implication: fields that are naturally numeric or boolean should be emitted as typed JSON values, with stable names and structure. Exact Bash-shaped report output should only be added if a concrete downstream consumer requires it.

## Report structure decision

Russ confirmed clean typed reports should keep the same top-level report files and keys:

- `hoststatus` containing `hosts`
- `groupstatus` containing `groups`
- `sysstatus` containing `systems`

Implication: report continuity is useful, but it is not a mandate to preserve every Bash-era inner-field wart.

## Status value decision

Russ confirmed status values should remain enum-like strings:

- `"up"`
- `"down"`
- `"unknown"`

Implication: clean typed output should convert numeric and boolean fields to JSON numbers/booleans where practical, but status remains a human-readable string value.

## Timestamp value decision

Russ confirmed timestamp fields such as `lastUp` and `lastChecked` should remain strings, but should be consistently ISO-8601.

Implication: clean typed output should keep timestamps human-readable and JSON-native while avoiding inconsistent legacy timestamp formats where possible.

## Report field-name decision

Russ decided clean typed report fields should use Pythonic `snake_case` names.

Examples:

- `last_up` instead of `lastUp`
- `last_checked` instead of `lastChecked`
- `fail_count` instead of `failCount`
- `min_count` instead of `minCount`
- `failure_grace` instead of `failGrace`
- `instance_count` instead of `instanceCount`
- `failure_count` instead of `failureCount`

Implication: the clean default report format should preserve useful outer surfaces, but use Pythonic field names and typed JSON values inside each record.

## Legacy report mode decision

Decision: do **not** add an explicit legacy-compatible report mode now.

Rationale:

- Russ chose clean typed reports as the default from the start.
- There is no known deployed Bash installation or downstream consumer requiring exact Bash-shaped output.
- Previous-state loading already accepts both clean snake_case fields and legacy Bash field names, so old state can still be consumed if it appears later.
- Adding a legacy-output mode now would increase API/CLI surface area without evidence of need.

Revisit this only if a concrete consumer requires strict legacy inner-field output such as `lastUp`, `failCount`, stringified numbers, or `critical: "yes" / "no"`. If that happens, implement it as an explicit opt-in mode, not as the default.
