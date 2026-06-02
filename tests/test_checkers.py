from types import SimpleNamespace

import httpx

from manuheart.checkers import HttpChecker, IcmpChecker
from manuheart.models import (
    CheckType,
    EffectiveConfig,
    GroupDefinition,
    HostDefinition,
    HttpCheckSettings,
)


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


def test_http_checker_accepts_injected_client():
    calls = []

    class FakeResponse:
        status_code = 204

    class FakeClient:
        def request(self, method, url):
            calls.append((method, url))
            return FakeResponse()

    result = HttpChecker(EffectiveConfig(), client=FakeClient()).check(
        HostDefinition("example", "g", "https://example.test/health"),
        group(CheckType.HTTPS),
    )

    assert result.healthy is True
    assert calls == [("HEAD", "https://example.test/health")]


def test_http_checker_can_use_configured_get_method():
    def handler(request):
        assert request.method == "GET"
        return httpx.Response(200)

    transport = httpx.MockTransport(handler)

    import manuheart.checkers as checkers

    original = checkers.httpx.Client

    class ClientFactory:
        def __call__(self, *args, **kwargs):
            kwargs["transport"] = transport
            return original(*args, **kwargs)

    checkers.httpx.Client = ClientFactory()
    try:
        result = HttpChecker(EffectiveConfig(http=HttpCheckSettings(method="GET"))).check(
            HostDefinition("example", "g", "https://example.test/health"),
            group(CheckType.HTTPS),
        )
    finally:
        checkers.httpx.Client = original
    assert result.healthy is True


def test_http_checker_falls_back_to_get_when_head_is_not_supported(monkeypatch):
    calls = []

    class FakeResponse:
        def __init__(self, status_code):
            self.status_code = status_code

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def request(self, method, url):
            calls.append((method, url))
            return FakeResponse(405)

        def get(self, url):
            calls.append(("GET", url))
            return FakeResponse(200)

    result = HttpChecker(EffectiveConfig(), client=FakeClient()).check(
        HostDefinition("example", "g", "https://example.test/health"),
        group(CheckType.HTTPS),
    )

    assert result.healthy is True
    assert calls == [
        ("HEAD", "https://example.test/health"),
        ("GET", "https://example.test/health"),
    ]


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

        def request(self, method, url):
            return FakeResponse()

    result = HttpChecker(EffectiveConfig(), client=FakeClient()).check(
        HostDefinition("example", "g", "https://example.test/health"),
        group(CheckType.HTTPS),
    )
    assert result.healthy is False


def test_http_checker_rejects_invalid_runtime_method():
    result = HttpChecker(EffectiveConfig(http=HttpCheckSettings(method="POST"))).check(
        HostDefinition("example", "g", "https://example.test/health"),
        group(CheckType.HTTPS),
    )

    assert result.healthy is False
    assert "invalid http method" in result.detail
