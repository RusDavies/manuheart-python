# Prioritization Notes

Status: Accepted initial direction — compatibility-first replacement readiness.

## Priority decision

Russ accepted the recommendation to prioritize **drop-in Bash compatibility first**.

Reasoning: before Manuheart Python is treated as a replacement for the Bash implementation, we need evidence that it preserves the compatibility contract that downstream consumers care about: config loading, report shape, report destinations, rollup semantics, and operational invocation patterns.

Clean Python-library/API quality remains important, but the current public API foundation is good enough to proceed while compatibility evidence is expanded.

## Current priority order

1. Prove Bash-vs-Python compatibility for safe fixtures.
2. Expand compatibility coverage beyond the localhost fixture if Russ can provide or approve safe non-secret configs.
3. Compare generated report structure and stable fields against Bash outputs.
4. Document accepted compatibility differences, if any.
5. Add packaging/install smoke testing from a clean environment.
6. Decide whether to create/push a remote repository.
7. Decide whether Manuheart Python remains internal-only or gets a package/release path.

## Current recommendation

Treat the current project as a working internal-tool foundation, not deployment-approved production replacement. The next decision is whether Russ has safe real-world Bash configs that can be used as compatibility fixtures, or whether compatibility should remain limited to synthetic examples for now.

## Fixture-source decision

Russ decided to continue with **synthetic compatibility fixtures only** for now. Real-world Manuheart Bash configs should not be used unless separately approved and sanitized.

Implication: compatibility work should expand the synthetic fixture suite to cover realistic behaviours without exposing internal topology or operational details. The standing intake guardrail is documented in `docs/fixture-intake-policy.md`.

## Compatibility depth decision

Russ decided to prioritize **exact Bash-output matching first** over broadening the synthetic fixture set.

Implication: the next compatibility work should compare localhost Bash-vs-Python output closely enough to identify migration-relevant differences, while allowing cleaner Python defaults. Any intentional differences should be documented before adding broader synthetic scenarios.

## Output-format decision

Russ decided to **go cleaner from the get-go**.

Implication: Bash output should be used as a compatibility reference, but Python does not need to preserve ugly legacy output details as the default. The default Python report format should prefer clean typed JSON where practical. If strict legacy report compatibility is needed later, add it as an explicit compatibility mode rather than making all users inherit Bash-shaped scars.

## Report-format implementation priority

Russ decided the next implementation priority should be **clean typed report output first**.

Implication: add or revise the default Python report serialization so fields that are naturally numeric or boolean are emitted as typed JSON values, while preserving clear names and stable structure. A legacy-compatible report mode can be considered after the clean default is established.

## Report structure decision

Russ confirmed clean typed reports should keep the same top-level report files and keys:

- `hoststatus` containing `hosts`
- `groupstatus` containing `groups`
- `sysstatus` containing `systems`

Implication: report continuity should be preserved at the file/top-level collection level, while individual fields should become cleaner typed JSON values where practical.

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

Implication: the clean default report format should preserve the outer report files/top-level keys, but use Pythonic field names and typed JSON values inside each record. Legacy field names can be considered only in an explicit compatibility mode if needed later.

## Legacy report mode decision

Decision: do **not** add an explicit legacy-compatible report mode now.

Rationale:

- Russ chose clean typed reports as the default from the start.
- The current compatibility contract preserves the migration-relevant outer surfaces: filenames, top-level keys, record identities, stable descriptive fields, and status strings.
- Previous-state loading already accepts both clean snake_case fields and legacy Bash field names, so existing report state can be consumed during migration.
- Adding a legacy-output mode now would increase API/CLI surface area before there is evidence of a real downstream consumer that requires exact Bash-shaped inner fields.

Revisit this only if a concrete consumer requires strict legacy inner-field output such as `lastUp`, `failCount`, stringified numbers, or `critical: "yes" / "no"`. If that happens, implement it as an explicit opt-in mode, not as the default.
