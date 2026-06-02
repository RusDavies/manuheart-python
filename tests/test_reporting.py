import json

from manuheart.api import CheckResult, CheckType, load_config, run_check, write_reports
from manuheart.models import ReportDestinations


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
