# Code Analysis Improvement Opportunities

Status: Review refreshed 2026-06-02 after legacy config removal.

## Scope reviewed

Reviewed current `src/manuheart/`, tests, scripts, docs, packaging metadata, and examples on `main` after the legacy Bash config surface was removed.

Verification during review:

- `ruff check src tests scripts`: passed.
- `mypy src/manuheart`: passed.
- `pytest -q`: 43 passed.

Overall finding: Manuheart Python is now in good shape for a small internal tool. The code is compact and separated cleanly across configuration, domain models, health rollup, checkers, previous-state loading, reporting, API, and CLI adapter layers. The remaining work is mostly semantics hardening and operational polish rather than structural repair.

## Recommended next improvements

### 1. Implement documented `unknown` and grace state semantics

`docs/health-state-semantics.md` records the intended model:

- hosts become `down` only after remaining non-`up` longer than grace allows;
- `unknown` means insufficient stable evidence, not healthy;
- group rollup must preserve host grace by allowing `unknown` hosts to keep a group `unknown` when they could still satisfy `min_count`;
- critical `unknown` groups should make the parent system `unknown`, not `up`;
- empty groups with `min_count > 0` should become `down` because they cannot satisfy their configured minimum.

Current implementation is close for host state but too blunt in group/system rollup. It can make systems `up` when critical groups are `unknown`, and group rollup does not distinguish "could still meet min_count if pending hosts recover" from "cannot meet min_count anymore".

Suggested fix: update host/group/system rollup tests first, then adjust `health.py` to match the state-semantics document.

### 2. Add stricter structured config validation for unknown keys and numeric bounds

The JSON/YAML loader validates shape and required fields, but still accepts extra keys silently. It also does not consistently enforce numeric bounds.

Examples worth catching:

- typo fields such as `min_cout`, `fallbak_to_get`, or `status_file`;
- `min_count < 0`;
- `check_period <= 0`;
- HTTP/ICMP timeouts <= 0;
- ICMP count <= 0;
- ambiguous `failure_grace` values if the intended model is `-1` for infinite grace or positive integers otherwise.

Impact: a small typo can produce a config that validates while not doing what the operator meant. That is how dashboards get haunted.

Suggested fix: add allowed-key checks for top-level, `runtime`, `runtime.status_files`, `checks`, `checks.http`, `checks.icmp`, group entries, and host entries. Add numeric-bound helpers and targeted tests.

### 3. Catch per-host checker crashes in the health engine

Built-in checkers generally return failed `CheckResult`s instead of raising, but injected or future checker implementations can still raise exceptions.

Impact: one broken checker or one unexpected host failure can abort the whole health cycle and prevent report writing.

Suggested fix: wrap each `checker.check(host, group)` call in `run_health_cycle()`. Convert exceptions into non-`up` check results with safe diagnostic details. This keeps the health cycle pessimistic but resilient.

### 4. Surface previous-state/report read degradation as warnings

Previous-state loading now degrades safely when reports are missing, malformed, or contain bad values. That is good. It is also silent.

Impact: operators may not know Manuheart ignored corrupt prior state, which affects grace/failure-count continuity.

Suggested fix: return state-load warnings, or add a small state-loading result object, and include warnings in `CheckRunResult.warnings` / CLI stderr.

### 5. Clarify or adjust relative path semantics for status files

`var_dir` is resolved relative to the config file directory. Explicit `runtime.status_files.*` paths are also resolved relative to the config file directory, not relative to `var_dir`.

Impact: defensible, but easy to misread. Operators may expect status files inside `var_dir` unless absolute.

Suggested fix: either document this explicitly in config docs/examples, or change explicit relative status file paths to resolve relative to `var_dir`. If changing behaviour, add tests and migration notes.

### 6. Tighten public API typing around extension points

The project defines a `Checker` protocol, but public API signatures still use `Mapping[CheckType, Any]` for checker maps and `Any` for clocks, sleepers, and daemon event callbacks.

Impact: the implementation passes mypy, but the API contract is looser than the code intends.

Suggested fix: add type aliases/protocols such as `CheckerMap`, `Clock`, `Sleeper`, and `DaemonEventCallback`; use them in `api.py` and `health.py`.

### 7. Consider adding checker details to host reports

`CheckResult.detail` currently influences no report output. Details such as `http status 503`, timeout text, DNS failure, or packet loss would make reports more useful during diagnosis.

Impact: downstream users see `down` but not why.

Suggested fix: add an optional `detail` field to `HostState` and host reports, or add a separate diagnostic report if keeping status reports minimal matters more.

### 8. Consider bounded check concurrency after deployment pressure appears

Checks are sequential today. That is fine for localhost and small smoke configs.

Impact: once a real config contains many hosts, cycle duration becomes the sum of slow checks/timeouts.

Suggested fix: defer until needed, then add bounded concurrency with deterministic report ordering. Do not add async machinery merely for decorative complexity. We are writing a health checker, not summoning Kubernetes in a trench coat.

## Recommended priority

1. Implement documented `unknown`/grace state semantics.
2. Add stricter config unknown-key and numeric-bound validation.
3. Catch per-host checker crashes.
4. Surface previous-state/report read warnings.
5. Clarify status-file path semantics.
6. Tighten API typing.
7. Add checker details to reports if operators need them.
8. Add bounded concurrency only after scale justifies it.
