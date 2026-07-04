# -*- coding: utf-8 -*-
"""PERM-06: account unlock API must call the real lockout service."""

from datetime import datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints import account_unlock
from app.models.login_attempt import LoginAttempt
from app.models.user import User
from app.services.account_lockout_service import AccountLockoutService


def _admin(db: Session) -> User:
    suffix = uuid4().hex[:8]
    user = User(
        username=f"perm06-admin-{suffix}",
        password_hash="test",
        real_name="PERM06 Admin",
        is_active=True,
        is_superuser=True,
    )
    db.add(user)
    db.flush()
    return user


def _normal_user(db: Session) -> User:
    suffix = uuid4().hex[:8]
    user = User(
        username=f"perm06-user-{suffix}",
        password_hash="test",
        real_name="PERM06 User",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()
    return user


def _seed_locked_attempts(db: Session, username: str) -> None:
    now = datetime.now()
    db.add_all(
        [
            LoginAttempt(
                username=username,
                ip_address="127.0.0.1",
                success=False,
                failure_reason="wrong_password",
                locked=index == AccountLockoutService.LOCKOUT_THRESHOLD - 1,
                created_at=now - timedelta(minutes=1),
            )
            for index in range(AccountLockoutService.LOCKOUT_THRESHOLD)
        ]
    )
    db.commit()


def test_account_unlock_router_exposes_real_routes():
    routes = {
        (route.path, tuple(sorted(route.methods or [])))
        for route in account_unlock.router.routes
        if hasattr(route, "methods")
    }

    assert ("/locked-accounts", ("GET",)) in routes
    assert ("/{username}/status", ("GET",)) in routes
    assert ("/{username}/history", ("GET",)) in routes
    assert ("/{username}/unlock", ("POST",)) in routes


def test_unlock_endpoint_clears_db_fallback_lockout(db_session: Session):
    admin = _admin(db_session)
    username = f"locked-{uuid4().hex[:8]}"
    _seed_locked_attempts(db_session, username)

    with patch("app.services.account_lockout_service.get_redis_client", return_value=None):
        before = AccountLockoutService.check_lockout(username, db_session)
        assert before["locked"] is True

        response = account_unlock.unlock_account(
            username=username,
            db=db_session,
            current_user=admin,
        )

        after = AccountLockoutService.check_lockout(username, db_session)

    assert response["username"] == username
    assert response["unlocked"] is True
    assert after["locked"] is False
    assert after["remaining_attempts"] == AccountLockoutService.LOCKOUT_THRESHOLD


def test_account_unlock_requires_super_admin(db_session: Session):
    user = _normal_user(db_session)

    with pytest.raises(HTTPException) as exc_info:
        account_unlock.get_account_lockout_status(
            username="someone",
            db=db_session,
            current_user=user,
        )

    assert exc_info.value.status_code == 403
