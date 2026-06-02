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

Implication: compatibility work should expand the synthetic fixture suite to cover realistic behaviours without exposing internal topology or operational details.

## Compatibility depth decision

Russ decided to prioritize **exact Bash-output matching first** over broadening the synthetic fixture set.

Implication: the next compatibility work should tighten the localhost Bash-vs-Python comparison from shape/name checks toward exact report-field compatibility, then document any intentional or unavoidable differences before adding broader synthetic scenarios.
