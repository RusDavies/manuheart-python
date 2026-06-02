import json

from manuheart.api import CheckResult, CheckType, Status, load_config, run_check
from manuheart.health import run_health_cycle


class FakeChecker:
    def __init__(self, healthy=True):
        self.healthy = healthy

    def check(self, host, group):
        return CheckResult(self.healthy, "fake")


class NamedFakeChecker:
    def __init__(self, outcomes):
        self.outcomes = outcomes

    def check(self, host, group):
        return CheckResult(self.outcomes.get(host.name, True), "fake")


class ExplodingChecker:
    def check(self, host, group):
        _ = group
        if host.name == "bad-a":
            raise RuntimeError("boom")
        return CheckResult(True, "fake")


def test_health_rollup_up():
    loaded = load_config("examples/localhost/manuheart.json")
    result = run_check(loaded, checkers={CheckType.ICMP: FakeChecker(True)}, clock=lambda: "now")
    assert result.hosts["localhost-icmp/127.0.0.1"].status == Status.UP
    assert result.groups["localhost-icmp"].status == Status.UP
    assert result.groups["optional-example"].status == Status.UP
    assert result.systems["localhost-system"].status == Status.UP


def test_health_rollup_unknown_within_grace_without_previous_state():
    loaded = load_config("examples/localhost/manuheart.json")
    result = run_check(loaded, checkers={CheckType.ICMP: FakeChecker(False)}, clock=lambda: "now")
    assert result.hosts["localhost-icmp/127.0.0.1"].status == Status.UNKNOWN
    assert result.hosts["localhost-icmp/127.0.0.1"].fail_count == 1
    assert result.groups["localhost-icmp"].status == Status.UNKNOWN
    assert result.systems["localhost-system"].status == Status.UNKNOWN


def test_health_rollup_down_after_grace():
    loaded = load_config("examples/localhost/manuheart.json")
    first = run_check(loaded, checkers={CheckType.ICMP: FakeChecker(False)}, clock=lambda: "t1")
    second = run_health_cycle(
        loaded,
        checkers={CheckType.ICMP: FakeChecker(False)},
        clock=lambda: "t2",
        previous_hosts=first.hosts,
        previous_groups=first.groups,
        previous_systems=first.systems,
    )
    assert second.hosts["localhost-icmp/127.0.0.1"].status == Status.DOWN
    assert second.hosts["localhost-icmp/127.0.0.1"].fail_count == 2
    assert second.groups["localhost-icmp"].status == Status.DOWN
    assert second.systems["localhost-system"].status == Status.DOWN


def test_health_rollup_preserves_last_known_up_during_grace():
    loaded = load_config("examples/localhost/manuheart.json")
    first = run_check(loaded, checkers={CheckType.ICMP: FakeChecker(True)}, clock=lambda: "t1")
    second = run_health_cycle(
        loaded,
        checkers={CheckType.ICMP: FakeChecker(False)},
        clock=lambda: "t2",
        previous_hosts=first.hosts,
        previous_groups=first.groups,
        previous_systems=first.systems,
    )
    assert second.hosts["localhost-icmp/127.0.0.1"].status == Status.UP
    assert second.hosts["localhost-icmp/127.0.0.1"].fail_count == 1
    assert second.groups["localhost-icmp"].status == Status.UP
    assert second.systems["localhost-system"].status == Status.UP


def test_synthetic_fixture_rolls_up_multiple_check_types_and_systems():
    loaded = load_config("examples/synthetic-compat/manuheart.json")
    checkers = {
        CheckType.HTTP: NamedFakeChecker({"frontend-a": True, "frontend-b": False}),
        CheckType.HTTPS: NamedFakeChecker({"api-a": True}),
        CheckType.ICMP: NamedFakeChecker({"batch-a": True}),
    }

    result = run_check(loaded, checkers=checkers, clock=lambda: "2026-06-02T00:00:00Z")

    assert result.hosts["frontend-http/frontend-a"].status == Status.UP
    assert result.hosts["frontend-http/frontend-b"].status == Status.UNKNOWN
    assert result.groups["frontend-http"].instance_count == 1
    assert result.groups["frontend-http"].status == Status.UNKNOWN
    assert result.groups["api-https"].status == Status.UP
    assert result.groups["optional-workers"].status == Status.UP
    assert result.systems["synthetic-web"].status == Status.UNKNOWN
    assert result.systems["synthetic-batch"].status == Status.UP


def test_synthetic_fixture_failure_grace_preserves_unknown_before_threshold():
    loaded = load_config("examples/synthetic-compat/manuheart.json")
    checkers = {
        CheckType.HTTP: NamedFakeChecker({"frontend-a": True, "frontend-b": True}),
        CheckType.HTTPS: NamedFakeChecker({"api-a": False}),
        CheckType.ICMP: NamedFakeChecker({"batch-a": True}),
    }

    result = run_check(loaded, checkers=checkers, clock=lambda: "2026-06-02T00:00:00Z")

    assert result.hosts["api-https/api-a"].fail_count == 1
    assert result.hosts["api-https/api-a"].status == Status.UNKNOWN
    assert result.groups["api-https"].status == Status.UNKNOWN
    assert result.systems["synthetic-web"].status == Status.UNKNOWN


def test_group_goes_down_when_pending_hosts_cannot_satisfy_min_count():
    loaded = load_config("examples/synthetic-compat/manuheart.json")
    checkers = {
        CheckType.HTTP: NamedFakeChecker({"frontend-a": False, "frontend-b": False}),
        CheckType.HTTPS: NamedFakeChecker({"api-a": True}),
        CheckType.ICMP: NamedFakeChecker({"batch-a": True}),
    }
    first = run_check(loaded, checkers=checkers, clock=lambda: "t1")
    second = run_health_cycle(
        loaded,
        checkers=checkers,
        clock=lambda: "t2",
        previous_hosts=first.hosts,
        previous_groups=first.groups,
        previous_systems=first.systems,
    )

    assert first.groups["frontend-http"].status == Status.UNKNOWN
    assert second.hosts["frontend-http/frontend-a"].status == Status.DOWN
    assert second.hosts["frontend-http/frontend-b"].status == Status.DOWN
    assert second.groups["frontend-http"].status == Status.DOWN
    assert second.systems["synthetic-web"].status == Status.DOWN


def test_checker_exception_marks_only_that_host_non_up_and_cycle_continues(tmp_path):
    config = tmp_path / "manuheart.json"
    config.write_text(
        json.dumps(
            {
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
                "hosts": [
                    {"name": "bad-a", "group": "g", "url": "n/a"},
                    {"name": "good-a", "group": "g", "url": "n/a"},
                ],
            }
        )
    )

    result = run_check(
        load_config(config),
        checkers={CheckType.ICMP: ExplodingChecker()},
        clock=lambda: "now",
    )

    assert result.hosts["g/bad-a"].status == Status.UNKNOWN
    assert result.hosts["g/good-a"].status == Status.UP
    assert result.groups["g"].status == Status.UP
    assert result.systems["s"].status == Status.UP
    assert result.warnings == ("g/bad-a: checker error: boom",)


def test_missing_checker_marks_matching_hosts_non_up_and_cycle_continues(tmp_path):
    config = tmp_path / "manuheart.json"
    config.write_text(
        json.dumps(
            {
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
        )
    )

    result = run_check(load_config(config), checkers={}, clock=lambda: "now")

    assert result.hosts["g/h"].status == Status.UNKNOWN
    assert result.groups["g"].status == Status.UNKNOWN
    assert result.systems["s"].status == Status.UNKNOWN
    assert result.warnings == ("g/h: no checker for icmp",)


def test_default_http_checker_reuses_one_client_per_cycle(tmp_path, monkeypatch):
    config = tmp_path / "manuheart.json"
    config.write_text(
        json.dumps(
            {
                "groups": [
                    {
                        "name": "web-http",
                        "system": "web",
                        "critical": True,
                        "type": "http",
                        "min_count": 1,
                        "failure_grace": 1,
                    },
                    {
                        "name": "web-https",
                        "system": "web",
                        "critical": True,
                        "type": "https",
                        "min_count": 1,
                        "failure_grace": 1,
                    },
                ],
                "hosts": [
                    {"name": "http-a", "group": "web-http", "url": "http://example.test/a"},
                    {"name": "https-a", "group": "web-https", "url": "https://example.test/a"},
                ],
            }
        )
    )
    created_clients = []

    class FakeResponse:
        status_code = 200

    class FakeClient:
        def __init__(self, *args, **kwargs):
            self.requests = []
            self.closed = False
            created_clients.append(self)

        def request(self, method, url):
            self.requests.append((method, url))
            return FakeResponse()

        def get(self, url):
            self.requests.append(("GET", url))
            return FakeResponse()

        def close(self):
            self.closed = True

    monkeypatch.setattr("manuheart.checkers.httpx.Client", FakeClient)

    result = run_check(load_config(config), clock=lambda: "now")

    assert sorted(state.status for state in result.hosts.values()) == [Status.UP, Status.UP]
    assert len(created_clients) == 1
    assert created_clients[0].closed is True
    assert created_clients[0].requests == [
        ("HEAD", "http://example.test/a"),
        ("HEAD", "https://example.test/a"),
    ]
