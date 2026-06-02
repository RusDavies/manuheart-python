from pathlib import Path

import pytest

from manuheart.api import ConfigFormat, load_config

FIXTURES = Path("examples/localhost")


def _shape(loaded):
    return {
        "groups": sorted(
            (g.name, g.system, g.critical, g.check_type.value, g.min_count, g.failure_grace)
            for g in loaded.groups.values()
        ),
        "hosts": sorted((h.name, h.group, h.url) for h in loaded.hosts.values()),
    }


def test_legacy_config_loads():
    loaded = load_config(FIXTURES / "manuheart.conf")
    assert "localhost-icmp" in loaded.groups
    assert "localhost-icmp/127.0.0.1" in loaded.hosts


def test_json_config_loads():
    loaded = load_config(FIXTURES / "manuheart.json")
    assert "localhost-icmp" in loaded.groups
    assert "localhost-icmp/127.0.0.1" in loaded.hosts


def test_yaml_config_loads_if_dependency_available():
    pytest.importorskip("yaml")
    loaded = load_config(FIXTURES / "manuheart.yaml")
    assert "localhost-icmp" in loaded.groups


def test_legacy_and_json_are_equivalent():
    assert _shape(load_config(FIXTURES / "manuheart.conf")) == _shape(
        load_config(FIXTURES / "manuheart.json")
    )


def test_json_and_yaml_are_equivalent_if_dependency_available():
    pytest.importorskip("yaml")
    assert _shape(load_config(FIXTURES / "manuheart.json")) == _shape(
        load_config(FIXTURES / "manuheart.yaml")
    )


def test_format_override_for_json():
    loaded = load_config(FIXTURES / "manuheart.json", config_format=ConfigFormat.JSON)
    assert loaded.groups["optional-example"].min_count == 0
