# Prioritization Notes

Status: Draft pending Russ review.

## Recommended next priorities

1. Confirm compatibility expectations for downstream report consumers.
2. Expand compatibility fixtures if there are real safe configs to test against.
3. Add install/package smoke testing.
4. Decide whether to create/push a remote repository.
5. Decide whether Manuheart Python remains internal-only or gets a package/release path.

## Current recommendation

Treat the current project as a working internal-tool foundation, not deployment-approved production replacement. The next decision should be compatibility acceptance: is Python output close enough to Bash output for the consumers Russ cares about?
