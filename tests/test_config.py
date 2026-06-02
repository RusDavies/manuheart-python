from pathlib import Path

import pytest

from manuheart.api import ConfigFormat, load_config

FIXTURES = Path("examples/localhost")
SYNTHETIC_FIXTURES = Path("examples/synthetic-compat")


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


def test_synthetic_legacy_and_json_are_equivalent():
    assert _shape(load_config(SYNTHETIC_FIXTURES / "manuheart.conf")) == _shape(
        load_config(SYNTHETIC_FIXTURES / "manuheart.json")
    )


def test_synthetic_json_and_yaml_are_equivalent_if_dependency_available():
    pytest.importorskip("yaml")
    assert _shape(load_config(SYNTHETIC_FIXTURES / "manuheart.json")) == _shape(
        load_config(SYNTHETIC_FIXTURES / "manuheart.yaml")
    )


def test_legacy_edge_case_fixture_emits_parser_warnings():
    loaded = load_config(Path("tests/fixtures/legacy-edge-cases/manuheart.conf"))
    assert sorted(loaded.groups) == ["edge-http"]
    assert sorted(loaded.hosts) == ["edge-http/edge-a"]
    assert any("duplicate group" in warning for warning in loaded.warnings)
    assert any("invalid boolean" in warning for warning in loaded.warnings)
    assert any("expected 6 group fields" in warning for warning in loaded.warnings)
    assert any("duplicate host" in warning for warning in loaded.warnings)
    assert any("unknown group" in warning for warning in loaded.warnings)
    assert any("invalid URL" in warning for warning in loaded.warnings)
    assert any("expected 3 host fields" in warning for warning in loaded.warnings)
