# -*- coding: utf-8 -*-
"""Stub endpoint 行为回归测试。"""

from __future__ import annotations

import importlib
import os

from fastapi import FastAPI
from fastapi.testclient import TestClient



def _build_client(allow_stub_success: bool) -> TestClient:
    os.environ["ALLOW_STUB_SUCCESS"] = "true" if allow_stub_success else "false"

    mod = importlib.import_module("app.api.v1.endpoints.stub_endpoints")
    mod = importlib.reload(mod)

    app = FastAPI()
    app.include_router(mod.router)
    return TestClient(app)


def test_stub_returns_501_by_default() -> None:
    client = _build_client(allow_stub_success=False)

    resp = client.get("/not-implemented-path")

    assert resp.status_code == 501
    body = resp.json()
    assert body.get("_stub") is True
    assert "尚未实现" in body.get("message", "")
    assert resp.headers.get("X-Stub-Endpoint") == "1"


def test_auth_path_in_stub_returns_404() -> None:
    client = _build_client(allow_stub_success=False)

    resp = client.get("/auth/login")

    assert resp.status_code == 404
    body = resp.json()
    assert body.get("_auth_expected") is True
    assert resp.headers.get("X-Stub-Endpoint") == "1"


def test_stub_can_return_200_in_compat_mode() -> None:
    client = _build_client(allow_stub_success=True)

    resp = client.get("/legacy-page-api")

    assert resp.status_code == 200
    body = resp.json()
    assert body.get("_stub") is True
    assert "此 API 尚未实现" in body.get("_message", "")
