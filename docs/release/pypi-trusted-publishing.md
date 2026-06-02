# PyPI Trusted Publishing Setup

Status: repository-side setup prepared; PyPI/TestPyPI web setup still requires a human logged into the relevant package-index accounts.

## Current package identity

- Distribution name: `manuheart`
- GitHub owner: `RusDavies`
- GitHub repository: `manuheart-python`
- Workflow file: `.github/workflows/publish.yml`
- TestPyPI environment: `testpypi`
- PyPI environment: `pypi`

As of this setup pass, `https://pypi.org/pypi/manuheart/json` returned 404, so the name appears unclaimed on PyPI. PyPI can still reject names for policy, normalization, reservation, or similarity reasons at publish time. Tiny bureaucracy goblin, naturally.

## What the workflow does

The workflow builds and checks distribution artifacts on:

- manual `workflow_dispatch`; and
- GitHub Release publication.

Publishing behavior:

- manual `workflow_dispatch` publishes to **TestPyPI** through the `testpypi` GitHub environment;
- publishing a non-prerelease GitHub Release publishes to **PyPI** through the `pypi` GitHub environment.

No PyPI API token is stored in GitHub. Publishing uses GitHub OIDC trusted publishing via `pypa/gh-action-pypi-publish`.

## Required PyPI/TestPyPI web setup

Do this once while logged into the relevant index accounts.

### 1. TestPyPI pending trusted publisher

On TestPyPI:

1. Go to account publishing settings / trusted publishers.
2. Add a pending publisher for a new project.
3. Use these values:
   - PyPI project name: `manuheart`
   - Owner: `RusDavies`
   - Repository name: `manuheart-python`
   - Workflow name: `publish.yml`
   - Environment name: `testpypi`
4. Save.

Then run the GitHub workflow manually:

```text
Actions → Publish Python package → Run workflow
```

That should create/publish `manuheart` on TestPyPI if the name is accepted.

### 2. PyPI pending trusted publisher

On real PyPI:

1. Go to account publishing settings / trusted publishers.
2. Add a pending publisher for a new project.
3. Use these values:
   - PyPI project name: `manuheart`
   - Owner: `RusDavies`
   - Repository name: `manuheart-python`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
4. Save.

Then publish through a GitHub Release, not by manually running the workflow.

Recommended first real release flow:

1. Bump version if `v0.1.0` was already used only as an internal source-control baseline.
2. Commit and tag the release version.
3. Create a GitHub Release from that tag.
4. Confirm the release is **not** marked prerelease.
5. The workflow publishes to PyPI using the `pypi` trusted publisher.

## GitHub environment recommendations

Create two GitHub environments:

- `testpypi`
- `pypi`

For `pypi`, strongly recommended:

- require reviewer approval before deployment;
- restrict deployment branches/tags to release tags; and
- keep it separate from `testpypi` so a manual test run cannot hit real PyPI.

## Local release gate before a real package publish

Run this before cutting a release tag intended for package publication:

```bash
.venv/bin/python -m ruff check src tests scripts
.venv/bin/python -m mypy src/manuheart
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_localhost_compatibility.py
.venv/bin/python scripts/check_dependency_security.py
.venv/bin/python -m manuheart validate-config --config examples/deployment-test/public-smoke.json
.venv/bin/python -m manuheart check --config examples/deployment-test/public-smoke.json
.venv/bin/python scripts/check_clean_install.py
python -m build
python -m twine check dist/*
```

## Boundary reminder

This setup enables the trusted publisher route. It is not, by itself, a decision to make the repository public, publish operational configs, or deploy Manuheart against real monitored hosts.
