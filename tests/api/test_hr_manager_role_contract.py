# -*- coding: utf-8 -*-
"""Contracts for the built-in HR manager role package."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
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
        module=code.split(":", 1)[0],
        action=code.split(":", 1)[1] if ":" in code else "read",
        permission_type="API",
        is_system=True,
        is_active=True,
    )
    db.add(permission)
    db.flush()
    return permission


def _get_or_create_hr_manager_role(db: Session) -> Role:
    role = db.query(Role).filter(Role.role_code == "hr_manager").first()
    if role:
        return role

    role = Role(
        role_code="hr_manager",
        role_name="HR",
        description="HR标准角色包",
        data_scope="DEPARTMENT",
        is_system=True,
        is_active=True,
    )
    db.add(role)
    db.flush()
    return role


def _create_hr_manager_user(db: Session) -> User:
    role = _get_or_create_hr_manager_role(db)
    username = f"hr_role_contract_{uuid.uuid4().hex[:8]}"
    user = User(
        username=username,
        password_hash="not-used",
        auth_type="password",
        real_name="HR角色合同测试用户",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    db.refresh(user)
    return user


def test_hr_manager_role_can_read_hr_self_service_endpoints(
    client: TestClient,
    db_session: Session,
):
    """Built-in hr_manager should include hr:read for HR dashboard pages."""
    _get_or_create_hr_manager_role(db_session)
    init_api_permissions_data(db_session)
    user = _create_hr_manager_user(db_session)
    headers = _auth_headers_for_user(user)

    endpoints = [
        "/hr/dashboard",
        "/hr/contracts?page=1&page_size=10",
        "/hr/contracts/expiring?days=60",
        "/hr/transactions?page=1&page_size=10",
    ]

    for endpoint in endpoints:
        response = client.get(f"{settings.API_V1_PREFIX}{endpoint}", headers=headers)
        assert response.status_code == 200, (endpoint, response.text)


def test_hr_manager_role_is_seeded_with_hr_read_permission(db_session: Session):
    """Regression guard for the role package itself, not just ad-hoc test users."""
    role = _get_or_create_hr_manager_role(db_session)
    init_api_permissions_data(db_session)
    permission = _ensure_api_permission(db_session, "hr:read", "HR管理查看")
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
