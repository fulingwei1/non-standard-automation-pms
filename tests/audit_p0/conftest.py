# -*- coding: utf-8 -*-
"""
Pytest fixtures for the P0 dynamic-reproduction suite.

Safety red lines honoured here:
  * The real database ``data/app.db`` is NEVER opened for writing. Every fixture
    works on a throw-away *copy* placed under a temp dir.
  * A dedicated uvicorn backend is started on an isolated port, pointed at the
    sandbox copy via the ``DATABASE_URL`` / ``SQLITE_DB_PATH`` env vars. It is
    killed on teardown.
  * The admin password of the *copy* is reset to a known value so the tests can
    authenticate; this only ever touches the copy.

Run just this suite (the full test tree OOMs):

    .venv/bin/python -m pytest tests/audit_p0 -m audit_p0

If a backend is already running you can point the suite at it and skip the
60-second cold start:

    AUDIT_P0_BASE_URL=http://127.0.0.1:8123 .venv/bin/python -m pytest tests/audit_p0
"""
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest

try:  # httpx is a project dependency
    import httpx
except Exception:  # pragma: no cover
    httpx = None


REPO_ROOT = Path(__file__).resolve().parents[2]
REAL_DB = REPO_ROOT / "data" / "app.db"
ADMIN_USER = "admin"
ADMIN_PASSWORD = "Audit@P0-Repro"


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "audit_p0: dynamic reproduction of the 17 functional-audit P0 findings",
    )


# ---------------------------------------------------------------------------
# Sandbox database (a copy of data/app.db) — never touches the real file.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def sandbox_db_path(tmp_path_factory) -> Path:
    """A fresh writable copy of the real DB with a known admin password."""
    assert REAL_DB.exists(), f"real db missing: {REAL_DB}"
    dst = tmp_path_factory.mktemp("audit_p0_db") / "sandbox_app.db"
    shutil.copy2(REAL_DB, dst)
    _set_known_admin_password(dst)
    return dst


def _set_known_admin_password(db_path: Path) -> None:
    import sqlite3

    from app.core.security import get_password_hash

    h = get_password_hash(ADMIN_PASSWORD)
    con = sqlite3.connect(str(db_path))
    try:
        con.execute(
            "UPDATE users SET password_hash=?, is_active=1 WHERE username=?",
            (h, ADMIN_USER),
        )
        con.commit()
    finally:
        con.close()


# ---------------------------------------------------------------------------
# Live backend bound to the sandbox DB.
# ---------------------------------------------------------------------------
def _free_port(default: int = 8199) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", default))
            return default
        except OSError:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


def _wait_ready(base_url: str, timeout: float = 150.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = httpx.get(f"{base_url}/docs", timeout=3)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(2)
    return False


@pytest.fixture(scope="session")
def base_url(sandbox_db_path) -> str:
    """Base URL of a backend guaranteed to be reading the sandbox DB."""
    if httpx is None:  # pragma: no cover
        pytest.skip("httpx not available")

    external = os.getenv("AUDIT_P0_BASE_URL")
    if external:
        # Caller vouches this points at a sandbox; we still verify below via login.
        if not _wait_ready(external, timeout=15):
            pytest.skip(f"AUDIT_P0_BASE_URL not reachable: {external}")
        yield external.rstrip("/")
        return

    port = _free_port(int(os.getenv("AUDIT_P0_PORT", "8199")))
    url = f"http://127.0.0.1:{port}"
    env = dict(os.environ)
    env.update(
        {
            "DATABASE_URL": f"sqlite:///{sandbox_db_path}",
            "SQLITE_DB_PATH": str(sandbox_db_path),
            "DEBUG": "true",
            "ENABLE_SCHEDULER": "false",
            "STRICT_API_ROUTER": "false",
            "REDIS_URL": "",
            "RATE_LIMIT_ENABLED": "false",
            "SECRET_KEY": "audit-p0-sandbox-secret-key-0123456789abcdef",
        }
    )
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        if not _wait_ready(url):
            proc.terminate()
            pytest.skip("sandbox backend failed to start within timeout")
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except Exception:  # pragma: no cover
            proc.kill()


@pytest.fixture(scope="session")
def admin_token(base_url) -> str:
    r = httpx.post(
        f"{base_url}/api/v1/auth/login",
        data={"username": ADMIN_USER, "password": ADMIN_PASSWORD},
        timeout=15,
    )
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"]


class ApiClient:
    """Thin authenticated wrapper around httpx bound to the sandbox backend."""

    def __init__(self, base_url: str, token: str):
        self.base = base_url.rstrip("/")
        self.h = {"Authorization": f"Bearer {token}"}

    def _u(self, path: str) -> str:
        if path.startswith("http"):
            return path
        if not path.startswith("/api/"):
            path = "/api/v1" + path
        return self.base + path

    def get(self, path, **kw):
        return httpx.get(self._u(path), headers=self.h, timeout=30, **kw)

    def post(self, path, **kw):
        return httpx.post(self._u(path), headers=self.h, timeout=30, **kw)

    def put(self, path, **kw):
        return httpx.put(self._u(path), headers=self.h, timeout=30, **kw)


@pytest.fixture(scope="session")
def api(base_url, admin_token) -> ApiClient:
    return ApiClient(base_url, admin_token)


@pytest.fixture(scope="session")
def sandbox_conn(sandbox_db_path):
    """Read/verify helper on the sandbox DB (safe; never the real file)."""
    import sqlite3

    con = sqlite3.connect(str(sandbox_db_path))
    yield con
    con.close()
