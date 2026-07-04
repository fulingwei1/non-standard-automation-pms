# -*- coding: utf-8 -*-
"""APPR-20: legacy approval instance creation must not create orphan PENDING rows."""

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.api.v1.endpoints.approvals.legacy_compat import create_legacy_instance
from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.user import User


def _user(db: Session, username: str) -> User:
    user = User(
        username=username,
        password_hash="x",
        real_name=username,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def test_legacy_create_instance_creates_real_pending_task(db_session: Session):
    initiator = _user(db_session, "appr20_initiator")
    approver = _user(db_session, "appr20_approver")
    db_session.commit()

    payload = {
        "title": "APPR-20 旧兼容审批",
        "business_type": "LEGACY_ORDER",
        "business_id": 1001,
        "data": {"amount": 1000},
        "approver_id": approver.id,
    }

    result = create_legacy_instance(payload, db_session, initiator)

    instance = db_session.get(ApprovalInstance, result["id"])
    tasks = (
        db_session.query(ApprovalTask)
        .filter(ApprovalTask.instance_id == instance.id)
        .all()
    )
    assert instance.status == "PENDING"
    assert instance.current_node_id is not None
    assert len(tasks) == 1
    assert tasks[0].status == "PENDING"
    assert tasks[0].assignee_id == approver.id


def test_legacy_create_instance_rejects_missing_approver(db_session: Session):
    initiator = _user(db_session, "appr20_missing_approver_initiator")
    db_session.commit()

    with pytest.raises(HTTPException) as exc:
        create_legacy_instance(
            {"title": "孤儿审批", "business_type": "LEGACY_ORDER", "business_id": 1002},
            db_session,
            initiator,
        )

    assert exc.value.status_code == 400
    assert "审批人" in exc.value.detail
    assert (
        db_session.query(ApprovalInstance)
        .filter(ApprovalInstance.title == "孤儿审批")
        .count()
        == 0
    )
