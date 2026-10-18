"""Per-visitor cap on brief reads. Tests elsewhere disable the cap."""
import pytest
from fastapi import HTTPException

from parallax.main import _estimate_hits, enforce_estimate_limit


class _Request:
    def __init__(self, ip: str):
        self.headers = {"x-forwarded-for": ip}
        self.client = type("Client", (), {"host": ip})()


def test_third_estimate_from_one_address_is_refused(monkeypatch):
    monkeypatch.setenv("ESTIMATE_IP_LIMIT_PER_HOUR", "2")
    ip = "198.51.100.44"
    _estimate_hits.pop(ip, None)
    request = _Request(ip)
    enforce_estimate_limit(request)
    enforce_estimate_limit(request)
    with pytest.raises(HTTPException) as caught:
        enforce_estimate_limit(request)
    assert caught.value.status_code == 429
    _estimate_hits.pop(ip, None)


def test_forwarded_ip_only_used_behind_proxy_and_uses_last_address(monkeypatch):
    from parallax.main import _visitor_ip

    request = _Request("198.51.100.44")
    request.headers["x-forwarded-for"] = "192.0.2.99, 203.0.113.12"
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
    assert _visitor_ip(request) == "198.51.100.44"
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "1")
    assert _visitor_ip(request) == "203.0.113.12"
