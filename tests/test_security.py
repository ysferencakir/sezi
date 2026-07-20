import pytest
from fastapi import HTTPException

from core import security


def test_disabled_when_admin_token_unset(monkeypatch):
    monkeypatch.setattr(security.settings, "admin_token", "")
    with pytest.raises(HTTPException) as exc:
        security.require_admin_token(x_admin_token="anything")
    assert exc.value.status_code == 503


def test_rejects_wrong_token(monkeypatch):
    monkeypatch.setattr(security.settings, "admin_token", "secret")
    with pytest.raises(HTTPException) as exc:
        security.require_admin_token(x_admin_token="wrong")
    assert exc.value.status_code == 401


def test_accepts_correct_token(monkeypatch):
    monkeypatch.setattr(security.settings, "admin_token", "secret")
    security.require_admin_token(x_admin_token="secret")
