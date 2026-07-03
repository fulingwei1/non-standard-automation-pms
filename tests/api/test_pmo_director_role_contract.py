# -*- coding: utf-8 -*-
"""Contracts for the built-in PMO director role package."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.models.project import Project
from app.models.user import ApiPermission, Role, RoleApiPermission, User, UserRole
from app.utils.init_permissions_data import init_api_permissions_data


def _auth_headers_for_user(user: User) -> dict[str, str]:
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


def _ensure_api_permission(db: Session, code: str, name: str) -> ApiPermission:
    permission = db.query(ApiPermission).filter(ApiPermission.perm_code == code).first()
    if permission:
        return permission

    permission = ApiPermission(
        perm_code=code,
        perm_name=name,
        module=code.split(":", 1)[0].upper(),
        action=code.split(":", 1)[1].upper() if ":" in code else "READ",
        permission_type="API",
        is_system=True,
        is_active=True,
    )
    db.add(permission)
    db.flush()
    return permission


def _get_or_create_pmo_director_role(db: Session) -> Role:
    role = db.query(Role).filter(Role.role_code == "pmo_director").first()
    if role:
        return role

    role = Role(
        role_code="pmo_director",
        role_name="PMO总监",
        description="PMO总监标准角色包",
        data_scope="ALL",
        is_system=True,
        is_active=True,
    )
    db.add(role)
    db.flush()
    return role


def _create_pmo_director_user(db: Session) -> User:
    role = _get_or_create_pmo_director_role(db)
    username = f"pmo_role_contract_{uuid.uuid4().hex[:8]}"
    user = User(
        username=username,
        password_hash="not-used",
        auth_type="password",
        real_name="PMO角色合同测试用户",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    db.refresh(user)
    return user


def _create_project(db: Session) -> Project:
    project = Project(
        project_code=f"PMO-COST-{uuid.uuid4().hex[:8].upper()}",
        project_name="PMO成本权限合同测试项目",
        customer_name="PMO测试客户",
        stage="S1",
        status="ST01",
        health="H1",
        is_active=True,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def test_pmo_director_role_can_read_project_cost_collection(
    client: TestClient,
    db_session: Session,
):
    """PMO director should be able to open project detail budget data."""
    _get_or_create_pmo_director_role(db_session)
    init_api_permissions_data(db_session)
    user = _create_pmo_director_user(db_session)
    project = _create_project(db_session)

    response = client.get(
        f"{settings.API_V1_PREFIX}/projects/{project.id}/costs/",
        params={"page": 1, "page_size": 10},
        headers=_auth_headers_for_user(user),
    )

    assert response.status_code == 200, response.text


def test_pmo_director_role_is_seeded_with_cost_read_permission(db_session: Session):
    """Regression guard for the PMO role package itself."""
    role = _get_or_create_pmo_director_role(db_session)
    init_api_permissions_data(db_session)
    permission = _ensure_api_permission(db_session, "cost:read", "成本查看")
    db_session.commit()

    assignment = (
        db_session.query(RoleApiPermission)
        .filter(
            RoleApiPermission.role_id == role.id,
            RoleApiPermission.permission_id == permission.id,
        )
        .first()
    )

    assert assignment is not None
