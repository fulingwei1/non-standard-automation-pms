import json
import uuid
from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.models.user import PermissionAudit, User


def _operator(db: Session) -> User:
    user = User(
        username=f"audit_user_{uuid.uuid4().hex[:8]}",
        password_hash="hash",
        is_active=True,
        is_superuser=True,
    )
    db.add(user)
    db.flush()
    return user


def _audit(db: Session, operator: User, *, action: str, target_id: int = 7) -> PermissionAudit:
    audit = PermissionAudit(
        operator_id=operator.id,
        action=action,
        target_type="role",
        target_id=target_id,
        detail=json.dumps({"role_code": "TEST", "tenant_id": 3}, ensure_ascii=False),
        ip_address="10.0.0.8",
        user_agent="pytest",
    )
    db.add(audit)
    db.flush()
    return audit


def _data(response):
    if hasattr(response, "model_dump"):
        return response.model_dump(mode="json")["data"]
    return response["data"]


def test_read_audits_lists_and_filters_permission_audits(db_session: Session):
    from app.api.v1.endpoints.audits import read_audits

    operator = _operator(db_session)
    matching = _audit(db_session, operator, action="ROLE_UPDATED", target_id=10)
    _audit(db_session, operator, action="USER_UPDATED", target_id=20)
    db_session.commit()

    response = read_audits(
        page=1,
        page_size=10,
        operator_id=operator.id,
        target_type="role",
        target_id=10,
        action="ROLE_UPDATED",
        start_date=datetime.utcnow() - timedelta(days=1),
        end_date=datetime.utcnow() + timedelta(days=1),
        db=db_session,
        current_user=operator,
    )

    data = _data(response)
    assert data["total"] == 1
    assert data["items"][0]["id"] == matching.id
    assert data["items"][0]["operator_id"] == operator.id
    assert data["items"][0]["detail"]["role_code"] == "TEST"


def test_read_audit_returns_detail_or_404(db_session: Session):
    from app.api.v1.endpoints.audits import read_audit

    operator = _operator(db_session)
    audit = _audit(db_session, operator, action="ROLE_CREATED")
    db_session.commit()

    data = _data(read_audit(audit_id=audit.id, db=db_session, current_user=operator))
    assert data["id"] == audit.id
    assert data["action"] == "ROLE_CREATED"

    with pytest.raises(Exception):
        read_audit(audit_id=999999, db=db_session, current_user=operator)
