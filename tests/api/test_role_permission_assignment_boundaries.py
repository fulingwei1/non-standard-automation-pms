# -*- coding: utf-8 -*-
"""Role permission-assignment boundaries for non-admin users."""

import json
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import ApiPermission, Role, RoleApiPermission, RoleTemplate, User, UserRole


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _unwrap_data(response) -> dict | list:
    body = response.json()
    return body.get("data", body)


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _ensure_permission(db: Session, code: str, name: str) -> ApiPermission:
    permission = db.query(ApiPermission).filter(ApiPermission.perm_code == code).first()
    if permission:
        return permission

    permission = ApiPermission(
        perm_code=code,
        perm_name=name,
        module=code.split(":", 1)[0],
        action=code.split(":", 1)[1] if ":" in code else "read",
        is_system=True,
        is_active=True,
    )
    db.add(permission)
    db.flush()
    return permission


def _create_role(
    db: Session,
    code: str,
    name: str,
    *,
    permissions: list[ApiPermission] | None = None,
) -> Role:
    role = Role(
        role_code=code,
        role_name=name,
        description="role assignment boundary contract",
        is_system=False,
        is_active=True,
    )
    db.add(role)
    db.flush()

    for permission in permissions or []:
        db.add(RoleApiPermission(role_id=role.id, permission_id=permission.id))
    db.flush()
    return role


def _create_user_with_permissions(
    db: Session,
    username: str,
    password: str,
    *,
    role_code: str,
    permissions: list[ApiPermission],
) -> User:
    user = User(
        username=username,
        password_hash=get_password_hash(password),
        auth_type="password",
        real_name="权限边界测试用户",
        department="测试部",
        position="测试岗",
        email=f"{username}@example.test",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()

    role = _create_role(db, role_code, f"边界角色-{username}", permissions=permissions)
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.flush()
    return user


def _create_template(
    db: Session,
    code: str,
    name: str,
    *,
    permission_codes: list[str] | None = None,
) -> RoleTemplate:
    template = RoleTemplate(
        template_code=code,
        template_name=name,
        role_type="BUSINESS",
        scope_type="GLOBAL",
        data_scope="PROJECT",
        level=2,
        permission_snapshot=json.dumps(permission_codes or []),
        is_active=True,
        version=1,
    )
    db.add(template)
    db.flush()
    return template


def _cleanup(
    db: Session,
    *,
    usernames: list[str],
    role_codes: list[str],
    template_codes: list[str],
) -> None:
    role_ids = [row[0] for row in db.query(Role.id).filter(Role.role_code.in_(role_codes)).all()]
    user_ids = [row[0] for row in db.query(User.id).filter(User.username.in_(usernames)).all()]
    template_ids = [
        row[0]
        for row in db.query(RoleTemplate.id).filter(RoleTemplate.template_code.in_(template_codes)).all()
    ]

    if role_ids:
        db.query(RoleApiPermission).filter(RoleApiPermission.role_id.in_(role_ids)).delete(
            synchronize_session=False
        )
        db.query(UserRole).filter(UserRole.role_id.in_(role_ids)).delete(synchronize_session=False)
        db.query(Role).filter(Role.id.in_(role_ids)).delete(synchronize_session=False)
    if user_ids:
        db.query(UserRole).filter(UserRole.user_id.in_(user_ids)).delete(synchronize_session=False)
        db.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)
    if template_ids:
        db.query(RoleTemplate).filter(RoleTemplate.id.in_(template_ids)).delete(
            synchronize_session=False
        )
    db.commit()


def test_role_create_permission_does_not_grant_permission_assignment(
    client: TestClient,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    username = f"qa_role_create_only_{suffix}"
    password = "PermBoundary123!"
    actor_role_code = f"QA_ASSIGN_BOUNDARY_ACTOR_{suffix}"
    denied_role_code = f"QA_ASSIGN_BOUNDARY_DENIED_{suffix}"
    empty_role_code = f"QA_ASSIGN_BOUNDARY_EMPTY_{suffix}"

    role_create = _ensure_permission(db_session, "role:create", "创建角色")
    user_read = _ensure_permission(db_session, "user:read", "查看用户")
    _cleanup(
        db_session,
        usernames=[username],
        role_codes=[actor_role_code, denied_role_code, empty_role_code],
        template_codes=[],
    )
    _create_user_with_permissions(
        db_session,
        username,
        password,
        role_code=actor_role_code,
        permissions=[role_create],
    )
    db_session.commit()

    try:
        token = _login(client, username, password)
        headers = _auth_headers(token)

        denied = client.post(
            f"{settings.API_V1_PREFIX}/roles/",
            json={
                "role_code": denied_role_code,
                "role_name": "不应带权限创建",
                "permission_ids": [user_read.id],
            },
            headers=headers,
        )
        assert denied.status_code == 403, denied.text

        allowed = client.post(
            f"{settings.API_V1_PREFIX}/roles/",
            json={
                "role_code": empty_role_code,
                "role_name": "允许空权限创建",
                "permission_ids": [],
            },
            headers=headers,
        )
        assert allowed.status_code == 201, allowed.text
        assert _unwrap_data(allowed)["role_code"] == empty_role_code
    finally:
        _cleanup(
            db_session,
            usernames=[username],
            role_codes=[actor_role_code, denied_role_code, empty_role_code],
            template_codes=[],
        )


def test_role_update_permission_does_not_grant_permission_assignment(
    client: TestClient,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    username = f"qa_role_update_only_{suffix}"
    password = "PermBoundary123!"
    actor_role_code = f"QA_ASSIGN_UPDATE_ACTOR_{suffix}"
    target_role_code = f"QA_ASSIGN_UPDATE_TARGET_{suffix}"

    role_update = _ensure_permission(db_session, "role:update", "编辑角色")
    user_read = _ensure_permission(db_session, "user:read", "查看用户")
    _cleanup(
        db_session,
        usernames=[username],
        role_codes=[actor_role_code, target_role_code],
        template_codes=[],
    )
    _create_user_with_permissions(
        db_session,
        username,
        password,
        role_code=actor_role_code,
        permissions=[role_update],
    )
    target_role = _create_role(db_session, target_role_code, "权限更新目标角色")
    db_session.commit()

    try:
        token = _login(client, username, password)
        headers = _auth_headers(token)

        allowed = client.put(
            f"{settings.API_V1_PREFIX}/roles/{target_role.id}",
            json={"description": "普通字段可更新"},
            headers=headers,
        )
        assert allowed.status_code == 200, allowed.text

        denied = client.put(
            f"{settings.API_V1_PREFIX}/roles/{target_role.id}",
            json={"permission_ids": [user_read.id]},
            headers=headers,
        )
        assert denied.status_code == 403, denied.text
    finally:
        _cleanup(
            db_session,
            usernames=[username],
            role_codes=[actor_role_code, target_role_code],
            template_codes=[],
        )


def test_role_template_permission_copies_require_role_assign(
    client: TestClient,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    username = f"qa_template_create_only_{suffix}"
    password = "PermBoundary123!"
    actor_role_code = f"QA_TPL_BOUNDARY_ACTOR_{suffix}"
    source_role_code = f"QA_TPL_BOUNDARY_SOURCE_{suffix}"
    denied_role_code = f"QA_TPL_BOUNDARY_FROM_TEMPLATE_{suffix}"
    denied_template_code = f"QA_TPL_DEN_{suffix}"
    empty_template_code = f"QA_TPL_EMPTY_{suffix}"
    privileged_template_code = f"QA_TPL_PRIV_{suffix}"
    saved_template_code = f"QA_TPL_SAVE_{suffix}"

    role_create = _ensure_permission(db_session, "role:create", "创建角色")
    role_update = _ensure_permission(db_session, "role:update", "编辑角色")
    user_read = _ensure_permission(db_session, "user:read", "查看用户")
    _cleanup(
        db_session,
        usernames=[username],
        role_codes=[actor_role_code, source_role_code, denied_role_code],
        template_codes=[
            denied_template_code,
            empty_template_code,
            privileged_template_code,
            saved_template_code,
        ],
    )
    _create_user_with_permissions(
        db_session,
        username,
        password,
        role_code=actor_role_code,
        permissions=[role_create, role_update],
    )
    source_role = _create_role(
        db_session,
        source_role_code,
        "另存来源角色",
        permissions=[user_read],
    )
    privileged_template = _create_template(
        db_session,
        privileged_template_code,
        "带权限模板",
        permission_codes=["user:read"],
    )
    db_session.commit()

    try:
        token = _login(client, username, password)
        headers = _auth_headers(token)

        denied_create = client.post(
            f"{settings.API_V1_PREFIX}/roles/templates/",
            json={
                "template_code": denied_template_code,
                "template_name": "不应带权限建模板",
                "permission_codes": ["user:read"],
            },
            headers=headers,
        )
        assert denied_create.status_code == 403, denied_create.text

        allowed_create = client.post(
            f"{settings.API_V1_PREFIX}/roles/templates/",
            json={
                "template_code": empty_template_code,
                "template_name": "允许空权限模板",
                "permission_codes": [],
            },
            headers=headers,
        )
        assert allowed_create.status_code == 201, allowed_create.text
        empty_template = _unwrap_data(allowed_create)

        denied_update = client.put(
            f"{settings.API_V1_PREFIX}/roles/templates/{empty_template['id']}",
            json={"permission_codes": ["user:read"]},
            headers=headers,
        )
        assert denied_update.status_code == 403, denied_update.text

        denied_create_role = client.post(
            f"{settings.API_V1_PREFIX}/roles/templates/{privileged_template.id}/create-role",
            json={
                "role_code": denied_role_code,
                "role_name": "不应从带权限模板创建",
            },
            headers=headers,
        )
        assert denied_create_role.status_code == 403, denied_create_role.text

        denied_save = client.post(
            f"{settings.API_V1_PREFIX}/roles/{source_role.id}/save-as-template",
            json={
                "template_code": saved_template_code,
                "template_name": "不应另存带权限角色",
            },
            headers=headers,
        )
        assert denied_save.status_code == 403, denied_save.text
    finally:
        _cleanup(
            db_session,
            usernames=[username],
            role_codes=[actor_role_code, source_role_code, denied_role_code],
            template_codes=[
                denied_template_code,
                empty_template_code,
                privileged_template_code,
                saved_template_code,
            ],
        )
