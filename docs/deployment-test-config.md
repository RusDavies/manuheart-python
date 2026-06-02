# Deployment Test Configuration

Status: public smoke-test example, not a production monitoring policy.

## Goal

Use a harmless, synthetic configuration to prove that a deployment can:

- load structured JSON configuration;
- perform HTTP(S) checks;
- perform ICMP checks where local privileges/network policy allow it;
- write reports to a disposable directory;
- exercise group/system rollup logic without exposing real infrastructure.

## Public smoke config

Example config:

```bash
examples/deployment-test/public-smoke.json
```

Run it manually from the project root:

```bash
.venv/bin/python -m manuheart check --config examples/deployment-test/public-smoke.json
```

Reports are written under the config directory:

```bash
examples/deployment-test/tmp/public-smoke-reports/
```

## Why public servers are acceptable here

Well-known public endpoints can be useful for deployment smoke testing because they avoid leaking internal topology and require no real Manuheart host list.

Use them carefully:

- keep the check count tiny;
- run manually or at very low frequency;
- prefer HTTP `GET` for endpoints known to tolerate it;
- treat failures as deployment/network signal, not proof that the public service is broken;
- do not use this as production monitoring.

The public smoke config currently checks:

- `https://example.com/`
- `https://www.iana.org/`
- `https://www.cloudflare.com/cdn-cgi/trace`
- ICMP to `1.1.1.1` and `8.8.8.8`

ICMP may fail depending on local privileges, firewall policy, network egress rules, or provider rate limiting. If ICMP is flaky in a deployment environment, use the HTTP-only groups first and treat ICMP as a separate capability check.

## Production config shape

For real deployment testing, start from this public smoke config and replace targets with a sanitized internal target set only after approval.

Recommended production-ish shape:

- one `system` per monitored service or environment;
- one `group` per role/check type, such as `api-http`, `db-tcp` if added later, or `edge-icmp`;
- `critical: true` only for groups that should make the system fail;
- `min_count` set to the smallest healthy quorum;
- `failure_grace` set high enough to avoid one transient packet/web blip turning into noise;
- `report_dir` pointed at the compatibility report directory expected by downstream consumers.

Do not commit real hostnames, service names, generated reports, or topology-bearing configs to the repository.
