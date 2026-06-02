# Manuheart Python

## Quick start

Install for local development:

```bash
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev,yaml]'
```

Validate the example config:

```bash
.venv/bin/python -m manuheart validate-config --config examples/localhost/manuheart.json
```

Run one check cycle:

```bash
.venv/bin/python -m manuheart check --config examples/localhost/manuheart.json
```

Run the public deployment smoke config:

```bash
.venv/bin/python -m manuheart check --config examples/deployment-test/public-smoke.json
```

Run the compatibility-style legacy invocation:

```bash
.venv/bin/python -m manuheart --once --config examples/localhost/manuheart.conf
```

Run daemon mode:

```bash
.venv/bin/python -m manuheart daemon --config examples/localhost/manuheart.json
```

Use the library API:

```python
from manuheart.api import load_config, run_check, write_reports

config = load_config("examples/localhost/manuheart.json")
result = run_check(config)
write_reports(result)
```

Run the local verification gate:

```bash
.venv/bin/python -m ruff check src tests scripts
.venv/bin/python -m mypy src/manuheart
.venv/bin/python -m pytest -q
.venv/bin/python scripts/check_localhost_compatibility.py
.venv/bin/python scripts/check_dependency_security.py
.venv/bin/python scripts/check_clean_install.py
```
