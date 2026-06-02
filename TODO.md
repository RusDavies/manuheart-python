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
- [x] Create Python project skeleton with `pyproject.toml`, `src/manuheart/`, and `tests/`.
- [x] Define the initial public library API contract in `src/manuheart/api.py`.
- [x] Add API smoke tests proving the package and public API import cleanly.
- [x] Port sample localhost config fixtures from `manuheart-bash`.
- [x] Implement typed domain models for hosts, groups, systems, statuses, and checks.
- [x] Implement compatible legacy config, group, and host parsers.
- [x] Implement first-class JSON configuration parser using the same normalized domain model.
- [x] Implement optional YAML configuration parser, preferably behind a `yaml` package extra.
- [x] Add equivalence tests proving legacy, JSON, and YAML config can describe the same health model.
- [x] Implement pure health rollup logic with fake-checker tests.
- [ ] Implement real ICMP and HTTP(S) checkers.
- [ ] Implement previous-state loading and atomic JSON report writing.
- [ ] Implement CLI commands and compatibility flags as thin adapters over the public API.
- [ ] Add tests proving CLI behavior matches API behavior for equivalent inputs.
- [ ] Add smoke test for one-shot localhost run.
- [ ] Add daemon mode only after one-shot mode is solid.
