# Implementation Checklist

Status: Draft.

## Completed foundation

- [x] Python package skeleton.
- [x] Public API shell.
- [x] API smoke tests.
- [x] Legacy localhost fixture.
- [x] JSON localhost fixture.
- [x] YAML localhost fixture.
- [x] Typed domain models.
- [x] Legacy config parser.
- [x] JSON config parser.
- [x] Optional YAML config parser.
- [x] Config equivalence tests.
- [x] Health rollup engine with fake-checker tests.
- [x] Override precedence support.
- [x] Library-backed ICMP checker.
- [x] Library-backed HTTP/S checker.
- [x] Previous-state loading.
- [x] Atomic report writing.
- [x] API-backed CLI commands.
- [x] One-shot smoke path.
- [x] Bounded daemon test path.

## Release-readiness checklist

- [ ] Review README quick start against actual commands.
- [ ] Review Bash-vs-Python compatibility output check.
- [ ] Decide whether legacy output shape is sufficiently compatible for downstream consumers.
- [x] Decide whether the project needs a remote repository.
- [x] Decide whether to publish as an installable package or keep internal-only.
