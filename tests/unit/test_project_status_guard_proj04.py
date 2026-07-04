from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.projects.status.status_crud import _update_project_field
from app.models import Project
from app.services.stage_advance_service import validate_stage_advancement


def test_stage_advance_rejects_non_adjacent_jump():
    validate_stage_advancement("S1", "S2")

    with pytest.raises(HTTPException) as exc_info:
        validate_stage_advancement("S1", "S9")

    assert exc_info.value.status_code == 400
    assert "只能推进到下一阶段" in exc_info.value.detail


def test_direct_project_stage_update_rejects_non_adjacent_jump(db_session, monkeypatch):
    project = Project(
        project_code="PJ-PROJ04-STAGE",
        project_name="项目阶段守卫测试",
        customer_name="测试客户",
        stage="S1",
        status="ST01",
        health="H1",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    monkeypatch.setattr(
        "app.utils.permission_helpers.check_project_access_or_raise",
        lambda db, current_user, project_id: project,
    )

    with pytest.raises(HTTPException) as exc_info:
        _update_project_field(
            db_session,
            SimpleNamespace(id=1),
            project.id,
            field="stage",
            new_value="S9",
            valid_values=["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9"],
            change_type="STAGE_CHANGE",
            reason="非法直跳",
            label="阶段",
        )

    assert exc_info.value.status_code == 400
    assert "不允许的阶段转换" in exc_info.value.detail
    db_session.refresh(project)
    assert project.stage == "S1"


def test_direct_project_status_update_rejects_non_adjacent_jump(db_session, monkeypatch):
    project = Project(
        project_code="PJ-PROJ04-STATUS",
        project_name="项目状态守卫测试",
        customer_name="测试客户",
        stage="S1",
        status="ST01",
        health="H1",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    monkeypatch.setattr(
        "app.utils.permission_helpers.check_project_access_or_raise",
        lambda db, current_user, project_id: project,
    )

    with pytest.raises(HTTPException) as exc_info:
        _update_project_field(
            db_session,
            SimpleNamespace(id=1),
            project.id,
            field="status",
            new_value="ST30",
            valid_values=[f"ST{i:02d}" for i in range(1, 31)],
            change_type="STATUS_CHANGE",
            reason="非法直跳",
            label="状态",
        )

    assert exc_info.value.status_code == 400
    assert "不允许的状态转换" in exc_info.value.detail
    db_session.refresh(project)
    assert project.status == "ST01"
