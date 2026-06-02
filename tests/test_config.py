from pathlib import Path

import pytest

from manuheart.api import ConfigFormat, load_config
from manuheart.errors import ConfigError, UnsupportedConfigFormatError

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


def test_json_config_loads():
    loaded = load_config(FIXTURES / "manuheart.json")
    assert "localhost-icmp" in loaded.groups
    assert "localhost-icmp/127.0.0.1" in loaded.hosts


def test_yaml_config_loads_if_dependency_available():
    pytest.importorskip("yaml")
    loaded = load_config(FIXTURES / "manuheart.yaml")
    assert "localhost-icmp" in loaded.groups


def test_json_and_yaml_are_equivalent_if_dependency_available():
    pytest.importorskip("yaml")
    assert _shape(load_config(FIXTURES / "manuheart.json")) == _shape(
        load_config(FIXTURES / "manuheart.yaml")
    )


def test_format_override_for_json():
    loaded = load_config(FIXTURES / "manuheart.json", config_format=ConfigFormat.JSON)
    assert loaded.groups["optional-example"].min_count == 0


def test_synthetic_json_and_yaml_are_equivalent_if_dependency_available():
    pytest.importorskip("yaml")
    assert _shape(load_config(SYNTHETIC_FIXTURES / "manuheart.json")) == _shape(
        load_config(SYNTHETIC_FIXTURES / "manuheart.yaml")
    )


def test_legacy_config_format_is_not_supported(tmp_path):
    config = tmp_path / "manuheart.conf"
    config.write_text("VARDIR: ./var\n")
    with pytest.raises(UnsupportedConfigFormatError, match="unsupported config format"):
        load_config(config)


def test_structured_config_requires_top_level_object(tmp_path):
    config = tmp_path / "bad.json"
    config.write_text("[]")
    with pytest.raises(ConfigError, match="top-level config must be an object"):
        load_config(config)


def test_structured_config_reports_missing_group_field(tmp_path):
    config = tmp_path / "bad.json"
    config.write_text('{"groups": [{"name": "g"}], "hosts": []}')
    with pytest.raises(ConfigError, match=r"groups\[0\]\.system is required"):
        load_config(config)


def test_structured_config_requires_groups_and_hosts_lists(tmp_path):
    config = tmp_path / "bad.json"
    config.write_text('{"groups": {}, "hosts": []}')
    with pytest.raises(ConfigError, match="groups must be a list"):
        load_config(config)


def test_structured_config_validates_http_host_url(tmp_path):
    config = tmp_path / "bad.json"
    config.write_text(
        """
        {
          "groups": [
            {
              "name": "web",
              "system": "s",
              "critical": true,
              "type": "http",
              "min_count": 1,
              "failure_grace": 1
            }
          ],
          "hosts": [
            {"name": "web-a", "group": "web", "url": "n/a"}
          ]
        }
        """
    )
    with pytest.raises(ConfigError, match=r"hosts\[0\] URL must start with http"):
        load_config(config)


def test_structured_runtime_sections_must_be_objects(tmp_path):
    config = tmp_path / "bad.json"
    config.write_text('{"runtime": [], "groups": [], "hosts": []}')
    with pytest.raises(ConfigError, match="runtime must be an object"):
        load_config(config)


def test_structured_yaml_parse_errors_are_config_errors(tmp_path):
    pytest.importorskip("yaml")
    config = tmp_path / "bad.yaml"
    config.write_text("groups: [")
    with pytest.raises(ConfigError, match="invalid YAML config"):
        load_config(config)


def test_structured_config_loads_http_method_settings(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(
        """
        {
          "checks": {
            "http": {
              "method": "get",
              "fallback_to_get": false
            }
          },
          "groups": [],
          "hosts": []
        }
        """
    )
    loaded = load_config(config)
    assert loaded.effective.http.method == "GET"
    assert loaded.effective.http.fallback_to_get is False


def test_structured_config_rejects_unknown_http_method(tmp_path):
    config = tmp_path / "bad.json"
    config.write_text('{"checks": {"http": {"method": "POST"}}, "groups": [], "hosts": []}')
    with pytest.raises(ConfigError, match="checks.http.method must be HEAD or GET"):
        load_config(config)
