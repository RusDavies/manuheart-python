from types import SimpleNamespace

import httpx

from manuheart.checkers import HttpChecker, IcmpChecker
from manuheart.models import CheckType, EffectiveConfig, GroupDefinition, HostDefinition


def group(check_type=CheckType.ICMP):
    return GroupDefinition(
        name="g",
        system="s",
        critical=True,
        check_type=check_type,
        min_count=1,
        failure_grace=1,
    )


def test_icmp_checker_uses_icmplib(monkeypatch):
    calls = {}

    def fake_ping(address, count, timeout, privileged):
        calls.update(
            {
                "address": address,
                "count": count,
                "timeout": timeout,
                "privileged": privileged,
            }
        )
        return SimpleNamespace(is_alive=True, packet_loss=0.0)

    monkeypatch.setattr("manuheart.checkers.ping", fake_ping)
    result = IcmpChecker(EffectiveConfig()).check(HostDefinition("127.0.0.1", "g", "n/a"), group())
    assert result.healthy is True
    assert calls["address"] == "127.0.0.1"


def test_http_checker_uses_httpx_mock_transport():
    def handler(request):
        assert request.method == "HEAD"
        return httpx.Response(204)

    transport = httpx.MockTransport(handler)

    # Patch the module-level client constructor without touching network.
    import manuheart.checkers as checkers

    original = checkers.httpx.Client

    class ClientFactory:
        def __call__(self, *args, **kwargs):
            kwargs["transport"] = transport
            return original(*args, **kwargs)

    checkers.httpx.Client = ClientFactory()
    try:
        result = HttpChecker(EffectiveConfig()).check(
            HostDefinition("example", "g", "https://example.test/health"),
            group(CheckType.HTTPS),
        )
    finally:
        checkers.httpx.Client = original
    assert result.healthy is True


def test_http_checker_rejects_non_2xx(monkeypatch):
    class FakeResponse:
        status_code = 503

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def head(self, url):
            return FakeResponse()

    monkeypatch.setattr("manuheart.checkers.httpx.Client", FakeClient)
    result = HttpChecker(EffectiveConfig()).check(
        HostDefinition("example", "g", "https://example.test/health"),
        group(CheckType.HTTPS),
    )
    assert result.healthy is False
