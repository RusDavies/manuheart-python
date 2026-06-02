# TODO

## Product process / Class 2 internal tool setup

- [ ] Create lightweight product/problem framing.
- [ ] Define requirements and acceptance criteria.
- [ ] Capture UX/workflow notes if a UI exists.
- [ ] Capture security/privacy notes.
- [ ] Capture lightweight architecture/deployment notes.
- [ ] Create implementation checklist.
- [ ] Record basic QA evidence for completed work.
- [ ] Add rollback/disable note.
- [ ] Add AI-agent operation boundary note, unless Russ explicitly exempts it.

## Project discovery

- [ ] Define scope: what Manuheart Python is responsible for.
- [ ] Capture baseline inventory, current access assumptions, and dependencies.
- [ ] Identify initial implementation or audit tasks.
- [ ] Prioritize remediation/build items with Russ.


## Python rewrite backlog

- [x] Understand the original Bash implementation and document its behavior.
- [x] Propose a clean Python architecture for the rewrite.
- [ ] Create Python project skeleton with `pyproject.toml`, `src/manuheart/`, and `tests/`.
- [ ] Port sample localhost config fixtures from `manuheart-bash`.
- [ ] Implement typed domain models for hosts, groups, systems, statuses, and checks.
- [ ] Implement compatible config, group, and host parsers.
- [ ] Implement pure health rollup logic with fake-checker tests.
- [ ] Implement real ICMP and HTTP(S) checkers.
- [ ] Implement previous-state loading and atomic JSON report writing.
- [ ] Implement CLI commands and compatibility flags.
- [ ] Add smoke test for one-shot localhost run.
- [ ] Add daemon mode only after one-shot mode is solid.
