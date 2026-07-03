# -*- coding: utf-8 -*-
"""ECN state-machine API contract regressions."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.ecn import Ecn
from app.models.project import Project
from app.models.user import User


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


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
