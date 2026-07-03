# -*- coding: utf-8 -*-
"""Tenant isolation contracts for role management endpoints."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.tenant import Tenant
from app.models.user import ApiPermission, Role, RoleApiPermission, User, UserRole


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


def _create_tenant_permission(db: Session, code: str, name: str, tenant_id: int) -> ApiPermission:
    permission = ApiPermission(
        tenant_id=tenant_id,
        perm_code=code,
        perm_name=name,
        module=code.split(":", 1)[0],
        action=code.split(":", 1)[1] if ":" in code else "read",
        is_system=False,
        is_active=True,
    )
    db.add(permission)
    db.flush()
    return permission


def _create_tenant(db: Session, code: str, name: str) -> Tenant:
    tenant = Tenant(
        tenant_code=code,
        tenant_name=name,
        status="ACTIVE",
        plan_type="ENTERPRISE",
        max_users=100,
        max_roles=100,
    )
    db.add(tenant)
    db.flush()
    return tenant


def _create_role(
    db: Session,
    code: str,
    name: str,
    *,
    tenant_id: int | None = None,
    permissions: list[ApiPermission] | None = None,
    is_system: bool = False,
) -> Role:
    role = Role(
        tenant_id=tenant_id,
        role_code=code,
        role_name=name,
        description="tenant isolation contract",
        is_system=is_system,
        is_active=True,
    )
    db.add(role)
    db.flush()

    for permission in permissions or []:
        db.add(RoleApiPermission(role_id=role.id, permission_id=permission.id))
    db.flush()
    return role


def _create_user(
    db: Session,
    username: str,
    password: str,
    *,
    tenant_id: int,
    permissions: list[ApiPermission],
    role_code: str,
) -> User:
    user = User(
        tenant_id=tenant_id,
        username=username,
        password_hash=get_password_hash(password),
        auth_type="password",
        real_name="租户角色边界测试用户",
        department="测试部",
        position="测试岗",
        email=f"{username}@example.test",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()

    role = _create_role(
        db,
        role_code,
        f"租户角色管理员-{username}",
        tenant_id=tenant_id,
        permissions=permissions,
    )
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.flush()
    return user


def _cleanup(
    db: Session,
    *,
    usernames: list[str],
    role_codes: list[str],
    tenant_codes: list[str],
) -> None:
    role_ids = [row[0] for row in db.query(Role.id).filter(Role.role_code.in_(role_codes)).all()]
    user_ids = [row[0] for row in db.query(User.id).filter(User.username.in_(usernames)).all()]
    tenant_ids = [
        row[0]
        for row in db.query(Tenant.id).filter(Tenant.tenant_code.in_(tenant_codes)).all()
    ]

    if user_ids:
        db.query(UserRole).filter(UserRole.user_id.in_(user_ids)).delete(synchronize_session=False)
        db.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)
    if role_ids:
        db.query(RoleApiPermission).filter(RoleApiPermission.role_id.in_(role_ids)).delete(
            synchronize_session=False
        )
        db.query(UserRole).filter(UserRole.role_id.in_(role_ids)).delete(synchronize_session=False)
        db.query(Role).filter(Role.id.in_(role_ids)).delete(synchronize_session=False)
    if tenant_ids:
        tenant_permission_ids = [
            row[0]
            for row in db.query(ApiPermission.id).filter(ApiPermission.tenant_id.in_(tenant_ids)).all()
        ]
        if tenant_permission_ids:
            db.query(RoleApiPermission).filter(
                RoleApiPermission.permission_id.in_(tenant_permission_ids)
            ).delete(synchronize_session=False)
            db.query(ApiPermission).filter(ApiPermission.id.in_(tenant_permission_ids)).delete(
                synchronize_session=False
            )
        db.query(Tenant).filter(Tenant.id.in_(tenant_ids)).delete(synchronize_session=False)
    db.commit()


def _seed_tenant_role_manager(db: Session, suffix: str, password: str):
    tenant_a_code = f"QA_TENANT_A_{suffix}"
    tenant_b_code = f"QA_TENANT_B_{suffix}"
    username = f"qa_tenant_role_mgr_{suffix}"
    actor_role_code = f"QA_TENANT_ACTOR_{suffix}"

    role_permissions = [
        _ensure_permission(db, "role:read", "查看角色"),
        _ensure_permission(db, "role:create", "创建角色"),
        _ensure_permission(db, "role:update", "编辑角色"),
        _ensure_permission(db, "role:delete", "删除角色"),
        _ensure_permission(db, "role:assign", "分配角色"),
    ]
    user_read = _ensure_permission(db, "user:read", "查看用户")
    tenant_a = _create_tenant(db, tenant_a_code, "租户A")
    tenant_b = _create_tenant(db, tenant_b_code, "租户B")
    other_tenant_permission = _create_tenant_permission(
        db,
        f"qa:tenant-other:{suffix}",
        "其他租户自定义权限",
        tenant_b.id,
    )

    _create_user(
        db,
        username,
        password,
        tenant_id=tenant_a.id,
        permissions=role_permissions,
        role_code=actor_role_code,
    )
    own_role = _create_role(
        db,
        f"QA_TENANT_OWN_{suffix}",
        "本租户角色",
        tenant_id=tenant_a.id,
    )
    other_role = _create_role(
        db,
        f"QA_TENANT_OTHER_{suffix}",
        "其他租户角色",
        tenant_id=tenant_b.id,
    )
    other_delete_role = _create_role(
        db,
        f"QA_TENANT_OTHER_DEL_{suffix}",
        "其他租户删除目标",
        tenant_id=tenant_b.id,
    )
    shared_role = _create_role(
        db,
        f"QA_TENANT_SHARED_{suffix}",
        "系统共享角色",
        tenant_id=None,
    )
    db.commit()
    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "username": username,
        "actor_role_code": actor_role_code,
        "own_role": own_role,
        "other_role": other_role,
        "other_delete_role": other_delete_role,
        "shared_role": shared_role,
        "user_read": user_read,
        "other_tenant_permission": other_tenant_permission,
    }


def test_tenant_role_list_and_detail_are_scoped(
    client: TestClient,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    password = "TenantRole123!"
    role_codes = [
        f"QA_TENANT_ACTOR_{suffix}",
        f"QA_TENANT_OWN_{suffix}",
        f"QA_TENANT_OTHER_{suffix}",
        f"QA_TENANT_OTHER_DEL_{suffix}",
        f"QA_TENANT_SHARED_{suffix}",
    ]
    tenant_codes = [f"QA_TENANT_A_{suffix}", f"QA_TENANT_B_{suffix}"]
    username = f"qa_tenant_role_mgr_{suffix}"
    _cleanup(db_session, usernames=[username], role_codes=role_codes, tenant_codes=tenant_codes)
    seeded = _seed_tenant_role_manager(db_session, suffix, password)

    try:
        token = _login(client, username, password)
        headers = _auth_headers(token)

        response = client.get(
            f"{settings.API_V1_PREFIX}/roles/",
            params={"keyword": f"QA_TENANT_", "page_size": 200},
            headers=headers,
        )
        assert response.status_code == 200, response.text
        role_codes_seen = {item["role_code"] for item in _unwrap_data(response)["items"]}
        assert seeded["own_role"].role_code in role_codes_seen
        assert seeded["shared_role"].role_code in role_codes_seen
        assert seeded["other_role"].role_code not in role_codes_seen
        assert seeded["other_delete_role"].role_code not in role_codes_seen

        own_response = client.get(
            f"{settings.API_V1_PREFIX}/roles/{seeded['own_role'].id}",
            headers=headers,
        )
        assert own_response.status_code == 200, own_response.text

        shared_response = client.get(
            f"{settings.API_V1_PREFIX}/roles/{seeded['shared_role'].id}",
            headers=headers,
        )
        assert shared_response.status_code == 200, shared_response.text

        other_response = client.get(
            f"{settings.API_V1_PREFIX}/roles/{seeded['other_role'].id}",
            headers=headers,
        )
        assert other_response.status_code == 404, other_response.text
    finally:
        _cleanup(db_session, usernames=[username], role_codes=role_codes, tenant_codes=tenant_codes)


def test_tenant_role_writes_cannot_mutate_other_tenant_roles(
    client: TestClient,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    password = "TenantRole123!"
    role_codes = [
        f"QA_TENANT_ACTOR_{suffix}",
        f"QA_TENANT_OWN_{suffix}",
        f"QA_TENANT_OTHER_{suffix}",
        f"QA_TENANT_OTHER_DEL_{suffix}",
        f"QA_TENANT_SHARED_{suffix}",
    ]
    tenant_codes = [f"QA_TENANT_A_{suffix}", f"QA_TENANT_B_{suffix}"]
    username = f"qa_tenant_role_mgr_{suffix}"
    _cleanup(db_session, usernames=[username], role_codes=role_codes, tenant_codes=tenant_codes)
    seeded = _seed_tenant_role_manager(db_session, suffix, password)

    try:
        token = _login(client, username, password)
        headers = _auth_headers(token)

        update_response = client.put(
            f"{settings.API_V1_PREFIX}/roles/{seeded['other_role'].id}",
            json={"description": "不应被其他租户更新"},
            headers=headers,
        )
        assert update_response.status_code == 404, update_response.text

        permissions_response = client.put(
            f"{settings.API_V1_PREFIX}/roles/{seeded['other_role'].id}/permissions",
            json={"permission_ids": [seeded["user_read"].id]},
            headers=headers,
        )
        assert permissions_response.status_code == 404, permissions_response.text
        leaked_permission = (
            db_session.query(RoleApiPermission)
            .filter(
                RoleApiPermission.role_id == seeded["other_role"].id,
                RoleApiPermission.permission_id == seeded["user_read"].id,
            )
            .first()
        )
        assert leaked_permission is None

        other_permission_response = client.put(
            f"{settings.API_V1_PREFIX}/roles/{seeded['own_role'].id}/permissions",
            json={"permission_ids": [seeded["other_tenant_permission"].id]},
            headers=headers,
        )
        assert other_permission_response.status_code == 404, other_permission_response.text
        leaked_tenant_permission = (
            db_session.query(RoleApiPermission)
            .filter(
                RoleApiPermission.role_id == seeded["own_role"].id,
                RoleApiPermission.permission_id == seeded["other_tenant_permission"].id,
            )
            .first()
        )
        assert leaked_tenant_permission is None

        delete_response = client.delete(
            f"{settings.API_V1_PREFIX}/roles/{seeded['other_delete_role'].id}",
            headers=headers,
        )
        assert delete_response.status_code == 404, delete_response.text
        assert db_session.query(Role).filter(Role.id == seeded["other_delete_role"].id).first()
    finally:
        _cleanup(db_session, usernames=[username], role_codes=role_codes, tenant_codes=tenant_codes)


def test_tenant_role_create_uses_current_tenant(
    client: TestClient,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    password = "TenantRole123!"
    created_role_code = f"QA_TENANT_CREATED_{suffix}"
    role_codes = [
        f"QA_TENANT_ACTOR_{suffix}",
        f"QA_TENANT_OWN_{suffix}",
        f"QA_TENANT_OTHER_{suffix}",
        f"QA_TENANT_OTHER_DEL_{suffix}",
        f"QA_TENANT_SHARED_{suffix}",
        created_role_code,
    ]
    tenant_codes = [f"QA_TENANT_A_{suffix}", f"QA_TENANT_B_{suffix}"]
    username = f"qa_tenant_role_mgr_{suffix}"
    _cleanup(db_session, usernames=[username], role_codes=role_codes, tenant_codes=tenant_codes)
    seeded = _seed_tenant_role_manager(db_session, suffix, password)

    try:
        token = _login(client, username, password)
        response = client.post(
            f"{settings.API_V1_PREFIX}/roles/",
            json={
                "role_code": created_role_code,
                "role_name": "租户内新角色",
                "description": "tenant-owned role",
            },
            headers=_auth_headers(token),
        )
        assert response.status_code == 201, response.text
        created = _unwrap_data(response)
        assert created["tenant_id"] == seeded["tenant_a"].id

        db_role = db_session.query(Role).filter(Role.role_code == created_role_code).first()
        assert db_role is not None
        assert db_role.tenant_id == seeded["tenant_a"].id
    finally:
        _cleanup(db_session, usernames=[username], role_codes=role_codes, tenant_codes=tenant_codes)
