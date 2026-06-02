"""Health checker implementations."""

from __future__ import annotations

import re
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass

from manuheart.models import CheckResult, EffectiveConfig, GroupDefinition, HostDefinition

_HOST_RE = re.compile(r"^[A-Za-z0-9_.:-]+$")


@dataclass(slots=True)
class IcmpChecker:
    timeout: float = 0.1

    def check(self, host: HostDefinition, group: GroupDefinition) -> CheckResult:
        if not host.name or not _HOST_RE.match(host.name):
            return CheckResult(False, "invalid host")
        try:
            completed = subprocess.run(
                ["ping", "-c", "1", "-W", str(self.timeout), host.name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=max(self.timeout + 1, 1),
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return CheckResult(False, str(exc))
        return CheckResult(completed.returncode == 0, f"ping exit {completed.returncode}")


@dataclass(slots=True)
class HttpChecker:
    config: EffectiveConfig

    def check(self, host: HostDefinition, group: GroupDefinition) -> CheckResult:
        if not host.url.startswith(("http://", "https://")):
            return CheckResult(False, "invalid url")
        request = urllib.request.Request(host.url, method="HEAD")
        try:
            opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())
            with opener.open(request, timeout=self.config.http.max_time) as response:
                status = response.getcode()
        except (OSError, urllib.error.URLError, ValueError) as exc:
            return CheckResult(False, str(exc))
        return CheckResult(200 <= status <= 299, f"http status {status}")


def default_checkers(config: EffectiveConfig):
    from manuheart.models import CheckType

    http = HttpChecker(config)
    return {CheckType.ICMP: IcmpChecker(), CheckType.HTTP: http, CheckType.HTTPS: http}
