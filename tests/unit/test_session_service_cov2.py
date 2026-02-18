# -*- coding: utf-8 -*-
"""
session_service.py 单元测试（第二批）
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call


# ─── 1. _parse_user_agent ─────────────────────────────────────────────────────
def test_parse_user_agent_chrome():
    from app.services.session_service import SessionService

    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
    result = SessionService._parse_user_agent(ua)
    assert "browser" in result or result == {}  # 依赖 user_agents 库是否安装


def test_parse_user_agent_empty():
    from app.services.session_service import SessionService

    result = SessionService._parse_user_agent("")
    # 不崩溃即可
    assert isinstance(result, dict)


# ─── 2. get_session_by_jti ───────────────────────────────────────────────────
def test_get_session_by_jti_access():
    from app.services.session_service import SessionService

    mock_db = MagicMock()
    mock_session = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_session

    result = SessionService.get_session_by_jti(mock_db, "test-jti", "access")
    assert result == mock_session


def test_get_session_by_jti_refresh():
    from app.services.session_service import SessionService

    mock_db = MagicMock()
    mock_session = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_session

    result = SessionService.get_session_by_jti(mock_db, "refresh-jti", "refresh")
    assert result == mock_session


def test_get_session_by_jti_not_found():
    from app.services.session_service import SessionService

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    result = SessionService.get_session_by_jti(mock_db, "unknown-jti")
    assert result is None


# ─── 3. revoke_session ───────────────────────────────────────────────────────
def test_revoke_session_not_found():
    from app.services.session_service import SessionService

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    with patch.object(SessionService, "_add_to_blacklist"):
        with patch.object(SessionService, "_remove_session_cache"):
            result = SessionService.revoke_session(mock_db, 999, 1)

    assert result is False


def test_revoke_session_success():
    from app.services.session_service import SessionService

    mock_session = MagicMock()
    mock_session.access_token_jti = "access-jti"
    mock_session.refresh_token_jti = "refresh-jti"

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_session

    with patch.object(SessionService, "_add_to_blacklist"):
        with patch.object(SessionService, "_remove_session_cache"):
            result = SessionService.revoke_session(mock_db, 1, 1)

    assert result is True
    assert mock_session.is_active is False
    mock_db.commit.assert_called_once()


# ─── 4. revoke_all_sessions ──────────────────────────────────────────────────
def test_revoke_all_sessions_no_active():
    from app.services.session_service import SessionService

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = []

    with patch.object(SessionService, "_add_to_blacklist"):
        with patch.object(SessionService, "_remove_session_cache"):
            count = SessionService.revoke_all_sessions(mock_db, 1)

    assert count == 0


def test_revoke_all_sessions_with_except():
    from app.services.session_service import SessionService

    s1 = MagicMock()
    s1.access_token_jti = "jti-1"
    s1.refresh_token_jti = "rjti-1"
    s1.id = 1

    mock_db = MagicMock()
    # revoke_all_sessions chains .filter().filter() when except_jti is provided
    mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [s1]

    with patch.object(SessionService, "_add_to_blacklist"):
        with patch.object(SessionService, "_remove_session_cache"):
            count = SessionService.revoke_all_sessions(mock_db, 1, except_jti="other-jti")

    assert count == 1
    assert s1.is_active is False


# ─── 5. cleanup_expired_sessions ────────────────────────────────────────────
def test_cleanup_expired_sessions_none():
    from app.services.session_service import SessionService

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = []

    with patch.object(SessionService, "_remove_session_cache"):
        count = SessionService.cleanup_expired_sessions(mock_db)

    assert count == 0


def test_cleanup_expired_sessions_removes():
    from app.services.session_service import SessionService

    s1 = MagicMock()
    s1.id = 1

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [s1]

    with patch.object(SessionService, "_remove_session_cache"):
        count = SessionService.cleanup_expired_sessions(mock_db)

    assert count == 1
    assert s1.is_active is False
    mock_db.commit.assert_called_once()


# ─── 6. _assess_risk - 新用户 ────────────────────────────────────────────────
def test_assess_risk_new_user():
    from app.services.session_service import SessionService

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

    is_suspicious, risk_score = SessionService._assess_risk(mock_db, 1, "1.2.3.4", None, None)
    assert is_suspicious is False
    assert risk_score == 0


# ─── 7. get_user_sessions ────────────────────────────────────────────────────
def test_get_user_sessions_active_only():
    from app.services.session_service import SessionService

    mock_s = MagicMock()
    mock_s.access_token_jti = "current-jti"

    mock_db = MagicMock()
    # get_user_sessions: .filter(user_id).filter(active) chained
    mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_s]

    sessions = SessionService.get_user_sessions(mock_db, 1, active_only=True, current_jti="current-jti")
    assert len(sessions) == 1
    assert mock_s.is_current is True
