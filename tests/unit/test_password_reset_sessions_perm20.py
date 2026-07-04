import uuid
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models.organization import Employee
from app.models.session import UserSession
from app.models.user import User


def _user_with_employee(db: Session) -> User:
    suffix = uuid.uuid4().hex[:8]
    employee = Employee(
        employee_code=f"E{suffix[:6]}",
        name="PERM20 员工",
        id_card="110101199001019876",
        is_active=True,
    )
    db.add(employee)
    db.flush()

    user = User(
        username=f"perm20_{suffix}",
        email=f"perm20_{suffix}@example.com",
        password_hash="old-hash",
        employee_id=employee.id,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def _active_session(db: Session, user_id: int) -> UserSession:
    session = UserSession(
        user_id=user_id,
        access_token_jti=f"access_{uuid.uuid4().hex}",
        refresh_token_jti=f"refresh_{uuid.uuid4().hex}",
        is_active=True,
        login_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=1),
    )
    db.add(session)
    db.commit()
    return session


def test_admin_password_reset_revokes_target_user_sessions(db_session, monkeypatch):
    """PERM-20: password reset must force the target user to log in again."""
    from app.api.v1.endpoints.users.sync import reset_user_password
    from app.services.session_service import SessionService

    target_user = _user_with_employee(db_session)
    session = _active_session(db_session, target_user.id)
    admin = SimpleNamespace(id=999)
    request = MagicMock()
    request.client.host = "127.0.0.1"
    request.headers = {"user-agent": "pytest"}

    monkeypatch.setattr(SessionService, "_add_to_blacklist", lambda *args, **kwargs: None)
    monkeypatch.setattr(SessionService, "_remove_session_cache", lambda *args, **kwargs: None)

    response = reset_user_password(
        db=db_session,
        user_id=target_user.id,
        request=request,
        current_user=admin,
    )

    db_session.expire_all()
    assert response.code == 200
    assert db_session.get(UserSession, session.id).is_active is False
