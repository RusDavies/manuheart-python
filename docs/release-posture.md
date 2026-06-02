# Remote Repository and Release Posture

Status: Accepted working posture for the current Class 2 internal-tool phase.

## Decision

Manuheart Python remains an **internal tool** for now.

No public repository, package index publication, or deployment into shared infrastructure should happen without explicit Russ approval.

## Current repository state

- Local repository: `projects/manuheart-python`
- Remote repository: private GitHub repository `https://github.com/RusDavies/manuheart-python`
- Package name in local metadata: `manuheart`
- Versioning scheme for local/internal builds: normal Python package versions, currently `0.1.0`

## Recommended remote posture

Russ approved creating the private remote. Keep it private unless Russ explicitly approves a public release.

Current default:

- private GitHub repository under the existing Russ-owned namespace or agreed internal organization;
- protect `main` once external collaboration starts;
- require the documented local verification gate before merging release-bound changes;
- do not commit real configs, generated health reports, host lists, logs, secrets, or topology.

A public repository is not recommended until the project has been scrubbed for internal assumptions and Russ explicitly wants public release.

## Recommended publishing posture

Do **not** publish to public PyPI for the current internal-tool phase.

Recommended release path:

1. Keep local editable installs for active development.
2. Use wheel/sdist artifacts for internal installs if a second host or user needs the tool.
3. Publish only to a private/internal package index if repeated installs need central distribution.
4. Revisit public PyPI only if Manuheart becomes a general-purpose open-source tool.

## Release-readiness gate

Before any internal release artifact is treated as releasable, run:

```bash
.venv/bin/python -m ruff check src tests scripts
.venv/bin/python -m mypy src/manuheart
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_localhost_compatibility.py
.venv/bin/python scripts/check_dependency_security.py
.venv/bin/python -m manuheart validate-config --config examples/deployment-test/public-smoke.json
.venv/bin/python -m manuheart check --config examples/deployment-test/public-smoke.json
.venv/bin/python scripts/check_clean_install.py
```

## Internal baseline tag posture

The first internal baseline should be tagged as `v0.1.0` only after the release-readiness gate passes on `main`.

The tag is an internal source-control marker, not approval to publish to PyPI, make the repository public, or deploy against real monitored hosts.

For `v0.1.0`, the package metadata version remains `0.1.0` and the changelog entry is maintained in `CHANGELOG.md`.

## Approval boundaries

Human approval is still required before:

- creating or pushing to a remote repository;
- publishing any package artifact outside the local machine;
- deploying Manuheart Python against real monitored hosts;
- importing real Manuheart configs, host lists, status reports, or logs into the repo;
- treating deployment against real monitored hosts as production-approved.

## Rationale

The codebase is now packageable, typed, tested, smoke-tested from a clean install, and covered by a dependency/security audit gate. That is enough for internal release preparation. It is not, by itself, approval to publish operational tooling, deploy against real monitored hosts, or expose internal monitoring assumptions.
