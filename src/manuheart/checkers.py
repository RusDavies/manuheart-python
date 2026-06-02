"""Health checker implementations."""

from __future__ import annotations

import re
from dataclasses import dataclass

import httpx
from icmplib import ping

from manuheart.models import CheckResult, EffectiveConfig, GroupDefinition, HostDefinition

_HOST_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")
_HEAD_FALLBACK_STATUS_CODES = {405, 501}


@dataclass(slots=True)
class IcmpChecker:
    """ICMP checker backed by icmplib, not shell ping."""

    config: EffectiveConfig

    def check(self, host: HostDefinition, group: GroupDefinition) -> CheckResult:
        _ = group
        if not host.name or not _HOST_RE.match(host.name):
            return CheckResult(False, "invalid host")
        try:
            response = ping(
                host.name,
                count=self.config.icmp.count,
                timeout=self.config.icmp.timeout,
                privileged=self.config.icmp.privileged,
            )
        except Exception as exc:  # noqa: BLE001 - checker boundary returns detail
            return CheckResult(False, str(exc))
        return CheckResult(bool(response.is_alive), f"packet_loss={response.packet_loss}")


@dataclass(slots=True)
class HttpChecker:
    """HTTP(S) checker backed by httpx."""

    config: EffectiveConfig

    def check(self, host: HostDefinition, group: GroupDefinition) -> CheckResult:
        _ = group
        if not host.url.startswith(("http://", "https://")):
            return CheckResult(False, "invalid url")
        timeout = httpx.Timeout(
            timeout=self.config.http.max_time,
            connect=self.config.http.connect_timeout,
        )
        try:
            with httpx.Client(follow_redirects=True, timeout=timeout) as client:
                method = self.config.http.method.upper()
                if method not in {"HEAD", "GET"}:
                    return CheckResult(False, f"invalid http method {method!r}")
                response = client.request(method, host.url)
                if (
                    method == "HEAD"
                    and self.config.http.fallback_to_get
                    and response.status_code in _HEAD_FALLBACK_STATUS_CODES
                ):
                    response = client.get(host.url)
        except httpx.HTTPError as exc:
            return CheckResult(False, str(exc))
        return CheckResult(
            200 <= response.status_code <= 299, f"http status {response.status_code}"
        )


def default_checkers(config: EffectiveConfig):
    from manuheart.models import CheckType

    http = HttpChecker(config)
    icmp = IcmpChecker(config)
    return {CheckType.ICMP: icmp, CheckType.HTTP: http, CheckType.HTTPS: http}
