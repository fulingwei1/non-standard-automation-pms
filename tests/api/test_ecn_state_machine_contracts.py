# -*- coding: utf-8 -*-
"""ECN state-machine API contract regressions."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.models.ecn import Ecn
from app.models.project import Project
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _user_headers(user: User) -> dict:
    return _auth_headers(create_access_token(data={"sub": str(user.id)}))


def _admin_user(db: Session) -> User:
    return db.query(User).filter(User.username == "admin").first()


def _first_project(db: Session) -> Project:
    return db.query(Project).first()


def _create_draft_ecn(db: Session, title: str) -> Ecn:
    suffix = uuid4().hex[:8]
    admin = _admin_user(db)
    project = _first_project(db)
    ecn = Ecn(
        ecn_no=f"SM-ECN-{suffix}",
        ecn_title=title,
        ecn_type="DESIGN",
        source_type="PROJECT",
        source_id=project.id,
        project_id=project.id,
        change_reason="状态机回归",
        change_description="验证当前 ECN 状态契约",
        status="DRAFT",
        applicant_id=admin.id,
        created_by=admin.id,
    )
    db.add(ecn)
    db.commit()
    db.refresh(ecn)
    return ecn


def _create_plain_user(db: Session, username: str) -> User:
    user = User(
        username=username,
        password_hash="not-used",
        auth_type="password",
        real_name=f"ECN权限测试-{username}",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_ecn_state_machine_allows_current_submit_status(
    client: TestClient, admin_token: str, db_session: Session
):
    ecn = _create_draft_ecn(db_session, "ECN 状态机提交契约")
    headers = _auth_headers(admin_token)

    allowed_response = client.get(
        f"{settings.API_V1_PREFIX}/ecn/state-machine/{ecn.id}/allowed-transitions",
        headers=headers,
        follow_redirects=False,
    )
    assert allowed_response.status_code == 200, allowed_response.text
    allowed = allowed_response.json()["data"]["allowed_transitions"]["DRAFT"]
    assert "SUBMITTED" in allowed

    transition_response = client.post(
        f"{settings.API_V1_PREFIX}/ecn/state-machine/{ecn.id}/transition",
        headers=headers,
        json={"target_state": "SUBMITTED", "comment": "提交状态机契约测试"},
        follow_redirects=False,
    )
    assert transition_response.status_code == 200, transition_response.text
    payload = transition_response.json()["data"]
    assert payload["previous_state"] == "DRAFT"
    assert payload["current_state"] == "SUBMITTED"

    detail_response = client.get(
        f"{settings.API_V1_PREFIX}/ecns/{ecn.id}",
        headers=headers,
        follow_redirects=False,
    )
    assert detail_response.status_code == 200, detail_response.text
    assert detail_response.json()["status"] == "SUBMITTED"


def test_ecn_state_machine_invalid_transition_returns_400_not_500(
    client: TestClient, admin_token: str, db_session: Session
):
    ecn = _create_draft_ecn(db_session, "ECN 状态机非法转换契约")

    response = client.post(
        f"{settings.API_V1_PREFIX}/ecn/state-machine/{ecn.id}/transition",
        headers=_auth_headers(admin_token),
        json={"target_state": "APPROVED", "comment": "非法跳转"},
        follow_redirects=False,
    )

    assert response.status_code == 400, response.text


def test_ecn_state_machine_rejects_submitted_to_approved_bypass(
    client: TestClient, admin_token: str, db_session: Session
):
    ecn = _create_draft_ecn(db_session, "ECN 状态机禁止自助审批")
    ecn.status = "SUBMITTED"
    ecn.current_step = "EVALUATION"
    db_session.add(ecn)
    db_session.commit()
    db_session.refresh(ecn)

    headers = _auth_headers(admin_token)
    allowed_response = client.get(
        f"{settings.API_V1_PREFIX}/ecn/state-machine/{ecn.id}/allowed-transitions",
        headers=headers,
        follow_redirects=False,
    )
    assert allowed_response.status_code == 200, allowed_response.text
    allowed = allowed_response.json()["data"]["allowed_transitions"]["SUBMITTED"]
    assert "APPROVED" not in allowed
    assert "REJECTED" not in allowed

    response = client.post(
        f"{settings.API_V1_PREFIX}/ecn/state-machine/{ecn.id}/transition",
        headers=headers,
        json={"target_state": "APPROVED", "comment": "绕过审批任务"},
        follow_redirects=False,
    )

    assert response.status_code == 400, response.text
    assert "审批" in response.text
    db_session.refresh(ecn)
    assert ecn.status == "SUBMITTED"
    assert ecn.approval_result is None


def test_ecn_state_machine_transition_requires_update_permission(
    client: TestClient, db_session: Session
):
    suffix = uuid4().hex[:8]
    ecn = _create_draft_ecn(db_session, "ECN 状态机权限门禁")
    user = _create_plain_user(db_session, f"qa_ecn_no_update_{suffix}")

    response = client.post(
        f"{settings.API_V1_PREFIX}/ecn/state-machine/{ecn.id}/transition",
        headers=_user_headers(user),
        json={"target_state": "SUBMITTED", "comment": "无权限写状态"},
        follow_redirects=False,
    )

    assert response.status_code == 403, response.text
    db_session.refresh(ecn)
    assert ecn.status == "DRAFT"
