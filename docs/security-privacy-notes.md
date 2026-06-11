# Security and Privacy Notes

Status: Draft.

## Data handled

Manuheart configuration and reports may contain internal hostnames, IP addresses, service names, health endpoints, and topology. Treat these as internal operational data.

## Security requirements

- Do not execute configuration as code.
- Validate config formats before use.
- Do not invoke shell commands for health checks when a Python library is available.
- Avoid logging secrets embedded in URLs.
- Use atomic report writes to avoid consumers reading partial JSON.
- Keep CLI external effects limited to configured report writes.
- Require human approval before deploying into shared infrastructure or changing real monitored host lists.

## Privacy requirements

- No personal data is required for normal operation.
- Do not publish health reports or configs outside trusted internal contexts.
- Keep real-world config/report fixture intake blocked unless Russ explicitly approves a specific sanitized source set; see `docs/fixture-intake-policy.md`.

## Current dependency posture

- ICMP checks use `icmplib`.
- HTTP/S checks use `httpx`.
- YAML support uses optional `PyYAML`.

Dependencies should be reviewed during release readiness because tiny internal tools still deserve not to become dependency confetti cannons.

Release-readiness dependency gates:

```bash
.venv/bin/python scripts/check_dependency_security.py
.venv/bin/python scripts/check_osv_scanner.py
```

`check_dependency_security.py` audits the releasable dependency set from `pyproject.toml`: normal runtime dependencies plus the optional YAML runtime extra. It intentionally excludes development tooling and the local unpublished package itself.

`check_osv_scanner.py` adds OSV database coverage for the runtime dependency set, the release/development tooling dependency set, and repository manifests. The script resolves the direct dependency ranges in temporary clean virtual environments and scans exact `pip freeze --all` outputs, so OSV evaluates a concrete install set instead of the oldest version satisfying a loose range. CI installs OSV Scanner from `tools/osv-scanner.lock.json`, which pins the release asset URL and SHA-256 instead of trusting a moving installer or `latest` URL.

`idna>=3.15` is an explicit runtime constraint because `httpx` can otherwise resolve older transitive `idna` versions affected by GHSA-65pc-fj4g-8rjx / CVE-2026-45409. The direct constraint keeps both `pip-audit` and OSV resolution on the patched line.
