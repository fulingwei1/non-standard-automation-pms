# -*- coding: utf-8 -*-
"""Contracts for project-manager self-service project and task access."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.models.project import Project
from app.models.user import ApiPermission, Role, RoleApiPermission, User, UserRole
from app.services.data_scope import DataScopeService
from app.utils.init_permissions_data import init_api_permissions_data


def _auth_headers_for_user(user: User) -> dict[str, str]:
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def _get_or_create_pm_role(db: Session) -> Role:
    role = db.query(Role).filter(Role.role_code == "pm").first()
    if role:
        role.data_scope = "PROJECT"
        role.is_active = True
        return role

    role = Role(
        role_code="pm",
        role_name="项目经理",
        description="项目经理标准角色包",
        data_scope="PROJECT",
        is_system=True,
        is_active=True,
    )
    db.add(role)
    db.flush()
    return role


def _create_pm_user(db: Session) -> User:
    role = _get_or_create_pm_role(db)
    username = f"pm_self_service_{uuid.uuid4().hex[:8]}"
    user = User(
        username=username,
        password_hash="not-used",
        auth_type="password",
        real_name="PM自服务合同测试用户",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    db.refresh(user)
    return user


def _create_pm_owned_project(db: Session, pm: User) -> Project:
    project = Project(
        project_code=f"PM-SELF-{uuid.uuid4().hex[:8].upper()}",
        project_name="PM自服务合同测试项目",
        customer_name="PM测试客户",
        stage="S1",
        status="ST01",
        health="H1",
        pm_id=pm.id,
        pm_name=pm.real_name,
        is_active=True,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def test_project_scope_includes_projects_managed_by_current_pm(db_session: Session):
    """PROJECT-scope PM users should be able to read projects where pm_id is themselves."""
    pm = _create_pm_user(db_session)
    project = _create_pm_owned_project(db_session, pm)

    assert DataScopeService.check_project_access(db_session, pm, project.id) is True


def test_pm_role_is_seeded_with_task_center_read_permission(db_session: Session):
    """The real lowercase pm role should include the task-center read package."""
    role = _get_or_create_pm_role(db_session)
    init_api_permissions_data(db_session)

    permission = (
        db_session.query(ApiPermission)
        .filter(ApiPermission.perm_code == "task_center:read")
        .first()
    )
    assert permission is not None

    assignment = (
        db_session.query(RoleApiPermission)
        .filter(
            RoleApiPermission.role_id == role.id,
            RoleApiPermission.permission_id == permission.id,
        )
        .first()
    )
    assert assignment is not None


def test_pm_can_open_own_project_workspace_and_task_center(
    client: TestClient,
    db_session: Session,
):
    """Browser PM self-service routes should not 403 on own projects and own tasks."""
    _get_or_create_pm_role(db_session)
    init_api_permissions_data(db_session)
    pm = _create_pm_user(db_session)
    project = _create_pm_owned_project(db_session, pm)
    headers = _auth_headers_for_user(pm)

    workspace_response = client.get(
        f"{settings.API_V1_PREFIX}/project-workspace/projects/{project.id}/workspace",
        headers=headers,
    )
    assert workspace_response.status_code == 200, workspace_response.text

    costs_response = client.get(
        f"{settings.API_V1_PREFIX}/projects/{project.id}/costs/",
        params={"page": 1, "page_size": 10},
        headers=headers,
    )
    assert costs_response.status_code == 200, costs_response.text

    machines_response = client.get(
        f"{settings.API_V1_PREFIX}/projects/{project.id}/machines/",
        params={"page": 1, "page_size": 10},
        headers=headers,
    )
    assert machines_response.status_code == 200, machines_response.text

    tasks_response = client.get(
        f"{settings.API_V1_PREFIX}/task-center/my-tasks",
        params={"page": 1, "page_size": 100},
        headers=headers,
    )
    assert tasks_response.status_code == 200, tasks_response.text
