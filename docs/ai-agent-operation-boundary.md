# AI-Agent Operation Boundary

Status: Draft.

## Agents may do autonomously

- Inspect source, tests, docs, and local fixtures.
- Create branches and commits for implementation work.
- Add or update tests.
- Run local verification gates.
- Update internal docs and TODO items.
- Add compatibility checks that do not touch external systems.

## Human approval required

- Deploying Manuheart Python to shared infrastructure.
- Replacing or deleting the Bash implementation.
- Changing real monitored host lists.
- Publishing the package externally.
- Sending alerts/messages externally.
- Accepting compatibility gaps or known broken health reporting.
- Handling secrets or sensitive infrastructure credentials.

## Default operating mode

Prefer local implementation, tests, and documentation work. Treat deployment and real monitoring changes as human-approved actions only.
