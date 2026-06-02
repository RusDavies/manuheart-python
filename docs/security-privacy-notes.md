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
