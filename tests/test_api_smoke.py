import subprocess
import sys
import tomllib
from pathlib import Path

import manuheart
import manuheart.api as api


def test_public_api_imports():
    assert manuheart.__version__
    assert api.ConfigFormat.AUTO == "auto"
    assert callable(api.load_config)


def test_public_version_matches_project_metadata():
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert manuheart.__version__ == pyproject["project"]["version"]


def test_module_help_runs():
    completed = subprocess.run(
        [sys.executable, "-m", "manuheart", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "usage:" in completed.stdout
