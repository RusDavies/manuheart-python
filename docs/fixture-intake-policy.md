# Fixture Intake Policy

Status: Real-world fixture intake is blocked by default.

## Default rule

Use synthetic fixtures only unless Russ explicitly approves a specific sanitized real-world config set for this project.

Do **not** copy, commit, paste, summarize, or transform real Manuheart Bash configs, host lists, group lists, status reports, logs, or generated health reports into this repository by default.

## Why this exists

Manuheart configuration can expose operational topology:

- internal hostnames and IP addresses;
- service names and health endpoints;
- system/group relationships;
- criticality and failure-grace behaviour;
- live or historical health state.

That is enough to be sensitive even if it does not contain passwords. Tiny monitoring configs are still infrastructure maps wearing a cheap disguise.

## Approved path, if Russ later wants real-world coverage

Only ingest real-world material when all of these are true:

1. Russ explicitly approves the specific source set.
2. The material is sanitized before it enters the repository.
3. Sanitization removes or replaces hostnames, IPs, domains, internal URLs, customer/service identifiers, secrets, tokens, and organization-specific topology names.
4. The sanitized fixture is reviewed as synthetic/test data before commit.
5. The commit message and QA notes say the fixture is sanitized and approved.

If any condition is unclear, stop and ask. Do not be clever. Clever is how monkeys invented incident reports.

## Preferred replacement pattern

When compatibility needs more coverage, create synthetic fixtures that model the behaviour rather than copying the real topology.

Examples of acceptable synthetic behaviours:

- multi-host group rollups;
- HTTP and HTTPS check types;
- optional/non-critical groups;
- duplicate legacy rows;
- invalid legacy rows;
- unknown group references;
- failure-grace thresholds;
- multiple systems with mixed criticality.

The current synthetic coverage lives under `examples/synthetic-compat/` and `tests/fixtures/legacy-edge-cases/`.
