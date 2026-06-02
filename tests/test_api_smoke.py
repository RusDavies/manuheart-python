import subprocess
import sys

import manuheart
import manuheart.api as api


def test_public_api_imports():
    assert manuheart.__version__
    assert api.ConfigFormat.AUTO == "auto"
    assert callable(api.load_config)


def test_module_help_runs():
    completed = subprocess.run(
        [sys.executable, "-m", "manuheart", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    assert "usage:" in completed.stdout
