import json

from manuheart.api import CheckResult, CheckType, load_config, run_check, write_reports
from manuheart.models import ReportDestinations, Status
from manuheart.state import (
    load_previous_groups,
    load_previous_hosts,
    load_previous_state,
    load_previous_systems,
)


class FakeChecker:
    def check(self, host, group):
        return CheckResult(True, "fake")


def test_write_reports(tmp_path):
    loaded = load_config("examples/localhost/manuheart.json")
    result = run_check(loaded, checkers={CheckType.ICMP: FakeChecker()}, clock=lambda: "now")
    destinations = ReportDestinations(
        hosts=tmp_path / "hoststatus",
        groups=tmp_path / "groupstatus",
        systems=tmp_path / "sysstatus",
    )
    write_reports(result, destinations)
    assert json.loads(destinations.hosts.read_text())["hosts"]
    assert json.loads(destinations.groups.read_text())["groups"]
    assert json.loads(destinations.systems.read_text())["systems"]


def test_write_reports_default_to_clean_typed_records(tmp_path):
    loaded = load_config("examples/localhost/manuheart.json")
    result = run_check(
        loaded,
        checkers={CheckType.ICMP: FakeChecker()},
        clock=lambda: "2026-06-02T00:00:00Z",
    )
    destinations = ReportDestinations(
        hosts=tmp_path / "hoststatus",
        groups=tmp_path / "groupstatus",
        systems=tmp_path / "sysstatus",
    )
    write_reports(result, destinations)

    host = json.loads(destinations.hosts.read_text())["hosts"][0]
    group = json.loads(destinations.groups.read_text())["groups"][0]
    system = json.loads(destinations.systems.read_text())["systems"][0]

    assert host["last_up"] == "2026-06-02T00:00:00Z"
    assert host["last_checked"] == "2026-06-02T00:00:00Z"
    assert isinstance(host["fail_count"], int)
    assert "lastUp" not in host
    assert "failCount" not in host

    assert isinstance(group["critical"], bool)
    assert isinstance(group["min_count"], int)
    assert isinstance(group["failure_grace"], int)
    assert isinstance(group["instance_count"], int)
    assert "minCount" not in group
    assert "failGrace" not in group

    assert isinstance(system["failure_count"], int)
    assert system["status"] in {"up", "down", "unknown"}
    assert "failureCount" not in system


def test_previous_state_loads_clean_and_legacy_report_fields(tmp_path):
    loaded = load_config(
        "examples/localhost/manuheart.json",
        overrides={
            "host_status_file": tmp_path / "hoststatus",
            "group_status_file": tmp_path / "groupstatus",
            "system_status_file": tmp_path / "sysstatus",
        },
    )
    loaded.effective.reports.hosts.write_text(
        json.dumps(
            {
                "hosts": [
                    {
                        "name": "clean",
                        "group": "g",
                        "url": "clean.example",
                        "last_up": "t1",
                        "last_checked": "t2",
                        "fail_count": 3,
                        "status": "down",
                    },
                    {
                        "name": "legacy",
                        "group": "g",
                        "url": "legacy.example",
                        "lastUp": "t3",
                        "lastChecked": "t4",
                        "failCount": "4",
                        "status": "up",
                    },
                ]
            }
        )
    )
    loaded.effective.reports.groups.write_text(
        json.dumps(
            {
                "groups": [
                    {
                        "name": "clean-group",
                        "system": "s",
                        "critical": True,
                        "type": "icmp",
                        "min_count": 1,
                        "failure_grace": 2,
                        "last_up": "t1",
                        "last_checked": "t2",
                        "instance_count": 3,
                        "status": "up",
                    },
                    {
                        "name": "legacy-group",
                        "system": "s",
                        "critical": "yes",
                        "type": "icmp",
                        "minCount": "2",
                        "failGrace": "3",
                        "lastUp": "t3",
                        "lastChecked": "t4",
                        "instanceCount": "4",
                        "status": "down",
                    },
                ]
            }
        )
    )
    loaded.effective.reports.systems.write_text(
        json.dumps(
            {
                "systems": [
                    {
                        "name": "clean-system",
                        "last_up": "t1",
                        "last_checked": "t2",
                        "failure_count": 5,
                        "status": "down",
                    },
                    {
                        "name": "legacy-system",
                        "lastUp": "t3",
                        "lastChecked": "t4",
                        "failureCount": "6",
                        "status": "up",
                    },
                ]
            }
        )
    )

    hosts = load_previous_hosts(loaded.effective)
    groups = load_previous_groups(loaded.effective)
    systems = load_previous_systems(loaded.effective)

    assert hosts["g/clean"].fail_count == 3
    assert hosts["g/legacy"].fail_count == 4
    assert groups["clean-group"].critical is True
    assert groups["legacy-group"].failure_grace == 3
    assert systems["clean-system"].failure_count == 5
    assert systems["legacy-system"].failure_count == 6


def test_previous_state_malformed_values_degrade_to_defaults(tmp_path):
    loaded = load_config(
        "examples/localhost/manuheart.json",
        overrides={
            "host_status_file": tmp_path / "hoststatus",
            "group_status_file": tmp_path / "groupstatus",
            "system_status_file": tmp_path / "sysstatus",
        },
    )
    loaded.effective.reports.hosts.write_text(
        json.dumps(
            {
                "hosts": [
                    "not-a-record",
                    {
                        "name": "bad-host",
                        "group": "g",
                        "url": None,
                        "fail_count": "not-an-int",
                        "status": "sideways",
                    },
                ]
            }
        )
    )
    loaded.effective.reports.groups.write_text(
        json.dumps(
            {
                "groups": [
                    {
                        "name": "bad-group",
                        "system": None,
                        "critical": "definitely",
                        "type": "smtp",
                        "min_count": "nope",
                        "failure_grace": "also-nope",
                        "instance_count": "still-nope",
                        "status": "sideways",
                    }
                ]
            }
        )
    )
    loaded.effective.reports.systems.write_text(
        json.dumps(
            {
                "systems": [
                    {
                        "name": "bad-system",
                        "failure_count": "not-an-int",
                        "status": "sideways",
                    }
                ]
            }
        )
    )

    hosts = load_previous_hosts(loaded.effective)
    groups = load_previous_groups(loaded.effective)
    systems = load_previous_systems(loaded.effective)
    previous = load_previous_state(loaded.effective)

    assert hosts["g/bad-host"].url == "unknown"
    assert hosts["g/bad-host"].fail_count == 0
    assert hosts["g/bad-host"].status == Status.UNKNOWN
    assert groups["bad-group"].system == "unknown"
    assert groups["bad-group"].critical is False
    assert groups["bad-group"].check_type == CheckType.ICMP
    assert groups["bad-group"].min_count == 0
    assert groups["bad-group"].failure_grace == 0
    assert groups["bad-group"].instance_count == 0
    assert groups["bad-group"].status == Status.UNKNOWN
    assert systems["bad-system"].failure_count == 0
    assert systems["bad-system"].status == Status.UNKNOWN
    assert "hoststatus: previous state hosts[0] is not an object; ignoring" in previous.warnings
    assert (
        "hoststatus g/bad-host.fail_count: invalid integer 'not-an-int'; using 0"
        in previous.warnings
    )
    assert (
        "hoststatus g/bad-host.status: invalid status 'sideways'; using unknown"
        in previous.warnings
    )
    assert (
        "groupstatus bad-group.critical: invalid boolean 'definitely'; using False"
        in previous.warnings
    )
    assert "groupstatus bad-group.type: invalid check type 'smtp'; using icmp" in previous.warnings
    assert (
        "sysstatus bad-system.failure_count: invalid integer 'not-an-int'; using 0"
        in previous.warnings
    )


def test_previous_state_ignores_non_object_payloads(tmp_path):
    loaded = load_config(
        "examples/localhost/manuheart.json",
        overrides={
            "host_status_file": tmp_path / "hoststatus",
            "group_status_file": tmp_path / "groupstatus",
            "system_status_file": tmp_path / "sysstatus",
        },
    )
    loaded.effective.reports.hosts.write_text(json.dumps(["not", "an", "object"]))
    loaded.effective.reports.groups.write_text(json.dumps({"groups": "not-a-list"}))
    loaded.effective.reports.systems.write_text(json.dumps({"systems": ["not-a-record"]}))

    assert load_previous_hosts(loaded.effective) == {}
    assert load_previous_groups(loaded.effective) == {}
    assert load_previous_systems(loaded.effective) == {}

    previous = load_previous_state(loaded.effective)
    assert previous.hosts == {}
    assert previous.groups == {}
    assert previous.systems == {}
    assert previous.warnings == (
        f"hoststatus: previous state file {loaded.effective.reports.hosts} "
        "is not an object; ignoring",
        "groupstatus: previous state field 'groups' is not a list; ignoring",
        "sysstatus: previous state systems[0] is not an object; ignoring",
    )


def test_run_check_surfaces_previous_state_warnings(tmp_path):
    loaded = load_config(
        "examples/localhost/manuheart.json",
        overrides={
            "host_status_file": tmp_path / "hoststatus",
            "group_status_file": tmp_path / "groupstatus",
            "system_status_file": tmp_path / "sysstatus",
        },
    )
    loaded.effective.reports.hosts.write_text("not-json")
    loaded.effective.reports.groups.write_text(json.dumps({"groups": []}))
    loaded.effective.reports.systems.write_text(json.dumps({"systems": []}))

    result = run_check(loaded, checkers={CheckType.ICMP: FakeChecker()}, clock=lambda: "now")

    assert result.hosts["localhost-icmp/127.0.0.1"].status == Status.UP
    assert result.warnings == (
        f"hoststatus: previous state file {loaded.effective.reports.hosts} "
        "is invalid JSON; ignoring",
    )
