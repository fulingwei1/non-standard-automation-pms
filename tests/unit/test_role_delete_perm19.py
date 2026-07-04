import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.session import UserSession
from app.models.user import Role, User, UserRole


def _user(db: Session, *, superuser: bool = False) -> User:
    user = User(
        username=f"perm19_user_{uuid.uuid4().hex[:8]}",
        password_hash="hash",
        is_active=True,
        is_superuser=superuser,
    )
    db.add(user)
    db.flush()
    return user


def test_delete_role_revokes_affected_user_sessions(db_session: Session, monkeypatch):
    from app.api.v1.endpoints.roles import delete_role
    from app.services.session_service import SessionService

    admin = _user(db_session, superuser=True)
    affected_user = _user(db_session)
    role = Role(
        role_code=f"PERM19_{uuid.uuid4().hex[:8]}",
        role_name="PERM19 待删角色",
        is_active=True,
        is_system=False,
    )
    db_session.add(role)
    db_session.flush()
    db_session.add(UserRole(user_id=affected_user.id, role_id=role.id))
    session = UserSession(
        user_id=affected_user.id,
        access_token_jti=f"access_{uuid.uuid4().hex}",
        refresh_token_jti=f"refresh_{uuid.uuid4().hex}",
        is_active=True,
        login_at=datetime.utcnow(),
        last_activity_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=1),
    )
    db_session.add(session)
    db_session.commit()
    role_id = role.id
    affected_user_id = affected_user.id
    session_id = session.id

    monkeypatch.setattr(SessionService, "_add_to_blacklist", lambda *args, **kwargs: None)
    monkeypatch.setattr(SessionService, "_remove_session_cache", lambda *args, **kwargs: None)

    delete_role(role_id=role_id, db=db_session, current_user=admin)

    db_session.expire_all()
    assert (
        db_session.query(UserRole)
        .filter(UserRole.user_id == affected_user_id, UserRole.role_id == role_id)
        .first()
        is None
    )
    assert db_session.get(UserSession, session_id).is_active is False
