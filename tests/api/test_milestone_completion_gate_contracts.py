# -*- coding: utf-8 -*-
"""Milestone completion gate API contracts."""

import json
import uuid
from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project, ProjectMilestone


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_global_milestone_complete_respects_delivery_requirements(
    client: TestClient, admin_token: str, db_session: Session
):
    suffix = uuid.uuid4().hex[:8]
    project = Project(project_code=f"PROJ10-PJ-{suffix}", project_name="PROJ10里程碑门禁")
    db_session.add(project)
    db_session.flush()

    milestone = ProjectMilestone(
        project_id=project.id,
        milestone_code=f"PROJ10-MS-{suffix}",
        milestone_name="交付物待审批里程碑",
        milestone_type="DELIVERY",
        status="IN_PROGRESS",
        planned_date=date.today(),
        deliverables=json.dumps([{"name": "验收资料", "status": "PENDING"}]),
    )
    db_session.add(milestone)
    db_session.commit()

    response = client.put(
        f"{settings.API_V1_PREFIX}/milestones/{milestone.id}/complete",
        headers=_headers(admin_token),
    )

    assert response.status_code == 400, response.text
    assert "交付物未全部审批" in response.text
    db_session.refresh(milestone)
    assert milestone.status == "IN_PROGRESS"
