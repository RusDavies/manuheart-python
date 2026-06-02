from manuheart.api import CheckResult, CheckType, Status, load_config, run_check


class FakeChecker:
    def __init__(self, healthy=True):
        self.healthy = healthy

    def check(self, host, group):
        return CheckResult(self.healthy, "fake")


def test_health_rollup_up():
    loaded = load_config("examples/localhost/manuheart.json")
    result = run_check(loaded, checkers={CheckType.ICMP: FakeChecker(True)}, clock=lambda: "now")
    assert result.hosts["localhost-icmp/127.0.0.1"].status == Status.UP
    assert result.groups["localhost-icmp"].status == Status.UP
    assert result.groups["optional-example"].status == Status.UNKNOWN
    assert result.systems["localhost-system"].status == Status.UP


def test_health_rollup_down_after_grace():
    loaded = load_config("examples/localhost/manuheart.json")
    result = run_check(loaded, checkers={CheckType.ICMP: FakeChecker(False)}, clock=lambda: "now")
    assert result.hosts["localhost-icmp/127.0.0.1"].status == Status.DOWN
    assert result.groups["localhost-icmp"].status == Status.DOWN
    assert result.systems["localhost-system"].status == Status.DOWN
