"""Redaction helpers for persisted operational output."""

from __future__ import annotations

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_SENSITIVE_QUERY_KEYS = {
    "access_token",
    "apikey",
    "api_key",
    "auth",
    "authorization",
    "client_secret",
    "credential",
    "key",
    "password",
    "secret",
    "token",
}
_URL_IN_TEXT_RE = re.compile(r"https?://[^\s]+")


def redact_url(value: str) -> str:
    """Redact URL credentials and common token query parameters."""

    try:
        parts = urlsplit(value)
    except ValueError:
        return value
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return value

    netloc = parts.netloc
    if "@" in netloc:
        host = parts.hostname or ""
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        if parts.port is not None:
            host = f"{host}:{parts.port}"
        netloc = f"[redacted]@{host}"

    query = urlencode(
        [
            (key, "[redacted]" if key.lower() in _SENSITIVE_QUERY_KEYS else value)
            for key, value in parse_qsl(parts.query, keep_blank_values=True)
        ]
    )
    return urlunsplit((parts.scheme, netloc, parts.path, query, parts.fragment))


def redact_urls_in_text(value: str) -> str:
    """Redact URLs embedded in operational messages."""

    return _URL_IN_TEXT_RE.sub(lambda match: redact_url(match.group(0)), value)
