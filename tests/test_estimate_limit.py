"""Per-visitor cap on brief reads. Tests elsewhere disable the cap."""
import pytest
from fastapi import HTTPException

from parallax.main import _estimate_hits, enforce_estimate_limit


class _Request:
    def __init__(self, ip: str):
        self.headers = {"x-forwarded-for": ip}
        self.client = None


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
