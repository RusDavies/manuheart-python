import json
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


def test_structured_status_files_are_relative_to_var_dir(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "runtime": {
                    "var_dir": "runtime-var",
                    "status_files": {
                        "hosts": "custom/hoststatus",
                        "groups": "custom/groupstatus",
                        "systems": "custom/sysstatus",
                    },
                },
                "groups": [],
                "hosts": [],
            }
        )
    )

    loaded = load_config(config)

    assert loaded.effective.var_dir == tmp_path / "runtime-var"
    assert loaded.effective.reports.hosts == tmp_path / "runtime-var/custom/hoststatus"
    assert loaded.effective.reports.groups == tmp_path / "runtime-var/custom/groupstatus"
    assert loaded.effective.reports.systems == tmp_path / "runtime-var/custom/sysstatus"


def test_structured_status_files_can_be_absolute(tmp_path):
    hoststatus = tmp_path / "absolute-hoststatus"
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "runtime": {
                    "var_dir": "runtime-var",
                    "status_files": {"hosts": str(hoststatus)},
                },
                "groups": [],
                "hosts": [],
            }
        )
    )

    loaded = load_config(config)

    assert loaded.effective.reports.hosts == hoststatus
    assert loaded.effective.reports.groups == tmp_path / "runtime-var/status/groupstatus"
    assert loaded.effective.reports.systems == tmp_path / "runtime-var/status/sysstatus"


def test_structured_config_rejects_unknown_http_method(tmp_path):
    config = tmp_path / "bad.json"
    config.write_text('{"checks": {"http": {"method": "POST"}}, "groups": [], "hosts": []}')
    with pytest.raises(ConfigError, match="checks.http.method must be HEAD or GET"):
        load_config(config)


@pytest.mark.parametrize(
    ("patch", "message"),
    [
        ({"surprise": True}, "top-level config has unknown key"),
        ({"runtime": {"status_file": "bad"}}, "runtime has unknown key"),
        (
            {"runtime": {"status_files": {"host": "bad"}}},
            "runtime.status_files has unknown key",
        ),
        ({"checks": {"smtp": {}}}, "checks has unknown key"),
        ({"checks": {"http": {"verb": "GET"}}}, "checks.http has unknown key"),
        ({"checks": {"icmp": {"packets": 2}}}, "checks.icmp has unknown key"),
        ({"groups": [{"extra": True}]}, r"groups\[0\] has unknown key"),
        ({"hosts": [{"extra": True}]}, r"hosts\[0\] has unknown key"),
    ],
)
def test_structured_config_rejects_unknown_keys(tmp_path, patch, message):
    data = {
        "runtime": {},
        "checks": {},
        "groups": [
            {
                "name": "g",
                "system": "s",
                "critical": True,
                "type": "icmp",
                "min_count": 1,
                "failure_grace": 1,
            }
        ],
        "hosts": [{"name": "h", "group": "g", "url": "n/a"}],
    }
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(data.get(key), dict):
            data[key].update(value)
        elif isinstance(value, list) and isinstance(data.get(key), list):
            data[key][0].update(value[0])
        else:
            data[key] = value
    config = tmp_path / "bad.json"
    config.write_text(json.dumps(data))
    with pytest.raises(ConfigError, match=message):
        load_config(config)


@pytest.mark.parametrize(
    ("patch", "message"),
    [
        ({"runtime": {"log_level": -1}}, "runtime.log_level must be >= 0"),
        ({"runtime": {"check_period": 0}}, "runtime.check_period must be > 0"),
        ({"runtime": {"run_mode": "sometimes"}}, "runtime.run_mode must be once or daemon"),
        ({"checks": {"http": {"connect_timeout": 0}}}, "checks.http.connect_timeout must be > 0"),
        ({"checks": {"http": {"max_time": 0}}}, "checks.http.max_time must be > 0"),
        ({"checks": {"icmp": {"timeout": 0}}}, "checks.icmp.timeout must be > 0"),
        ({"checks": {"icmp": {"count": 0}}}, "checks.icmp.count must be > 0"),
        ({"groups": [{"min_count": -1}]}, r"groups\[0\]\.min_count must be >= 0"),
        ({"groups": [{"failure_grace": -2}]}, r"groups\[0\]\.failure_grace must be >= -1"),
    ],
)
def test_structured_config_rejects_invalid_numeric_bounds(tmp_path, patch, message):
    data = {
        "runtime": {},
        "checks": {},
        "groups": [
            {
                "name": "g",
                "system": "s",
                "critical": True,
                "type": "icmp",
                "min_count": 1,
                "failure_grace": 1,
            }
        ],
        "hosts": [{"name": "h", "group": "g", "url": "n/a"}],
    }
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(data.get(key), dict):
            for nested_key, nested_value in value.items():
                if isinstance(nested_value, dict) and isinstance(data[key].get(nested_key), dict):
                    data[key][nested_key].update(nested_value)
                else:
                    data[key][nested_key] = nested_value
        elif isinstance(value, list) and isinstance(data.get(key), list):
            data[key][0].update(value[0])
        else:
            data[key] = value
    config = tmp_path / "bad.json"
    config.write_text(json.dumps(data))
    with pytest.raises(ConfigError, match=message):
        load_config(config)
