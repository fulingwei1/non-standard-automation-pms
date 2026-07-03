# -*- coding: utf-8 -*-
"""Role/permission workflow contracts used by the live Role Management UI."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.organization import Employee
from app.models.tenant import Tenant
from app.models.user import ApiPermission, Role, RoleApiPermission, User, UserRole
from app.services.permission_cache_service import get_permission_cache_service


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _unwrap_data(response) -> dict:
    body = response.json()
    return body.get("data", body)


def _login(client: TestClient, username: str, password: str) -> str:
    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def _ensure_permission(db: Session, code: str, name: str) -> tuple[ApiPermission, bool]:
    permission = db.query(ApiPermission).filter(ApiPermission.perm_code == code).first()
    if permission:
        return permission, False

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
    return permission, True


def _create_role(
    db: Session,
    code: str,
    name: str,
    *,
    tenant_id: int | None = None,
    permissions: list[ApiPermission] | None = None,
) -> Role:
    role = Role(
        tenant_id=tenant_id,
        role_code=code,
        role_name=name,
        description="role permission workflow contract",
        is_system=False,
        is_active=True,
    )
    db.add(role)
    db.flush()

    for permission in permissions or []:
        db.add(RoleApiPermission(role_id=role.id, permission_id=permission.id))
    db.flush()
    return role


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


def _create_user(
    db: Session,
    username: str,
    password: str,
    *,
    tenant_id: int | None = None,
) -> User:
    user = User(
        tenant_id=tenant_id,
        username=username,
        password_hash=get_password_hash(password),
        auth_type="password",
        real_name="权限组合测试用户",
        department="测试部",
        position="测试岗",
        email=f"{username}@example.test",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()
    return user


def _cleanup(
    db: Session,
    *,
    role_codes: list[str],
    usernames: list[str],
    permission_id: int | None = None,
    tenant_codes: list[str] | None = None,
) -> None:
    role_ids = [row[0] for row in db.query(Role.id).filter(Role.role_code.in_(role_codes)).all()]
    user_rows = db.query(User.id, User.employee_id).filter(User.username.in_(usernames)).all()
    user_ids = [row[0] for row in user_rows]
    employee_ids = [row[1] for row in user_rows if row[1] is not None]
    tenant_ids = []
    if tenant_codes:
        tenant_ids = [
            row[0] for row in db.query(Tenant.id).filter(Tenant.tenant_code.in_(tenant_codes)).all()
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
    if employee_ids:
        db.query(Employee).filter(Employee.id.in_(employee_ids)).delete(synchronize_session=False)
    if permission_id is not None:
        db.query(RoleApiPermission).filter(RoleApiPermission.permission_id == permission_id).delete(
            synchronize_session=False
        )
        db.query(ApiPermission).filter(ApiPermission.id == permission_id).delete(synchronize_session=False)
    if tenant_ids:
        db.query(Tenant).filter(Tenant.id.in_(tenant_ids)).delete(synchronize_session=False)
    db.commit()


def _attach_role_to_user(db: Session, user: User, role: Role) -> None:
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.flush()


def test_role_nav_groups_can_be_saved_from_role_management(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    role_code = f"QA_ROLE_NAV_{suffix}"
    headers = _auth_headers(admin_token)

    _cleanup(db_session, role_codes=[role_code], usernames=[])
    role = _create_role(db_session, role_code, f"导航角色-{suffix}")
    db_session.commit()

    try:
        nav_groups = [{"key": "system", "title": "系统管理", "menus": ["users", "roles"]}]
        response = client.put(
            f"{settings.API_V1_PREFIX}/roles/{role.id}/nav-groups",
            json=nav_groups,
            headers=headers,
        )
        assert response.status_code == 200, response.text

        get_response = client.get(
            f"{settings.API_V1_PREFIX}/roles/{role.id}/nav-groups",
            headers=headers,
        )
        assert get_response.status_code == 200, get_response.text
        assert _unwrap_data(get_response) == nav_groups
    finally:
        _cleanup(db_session, role_codes=[role_code], usernames=[])


def test_role_compare_returns_common_and_role_specific_permissions(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    role_a_code = f"QA_ROLE_COMPARE_A_{suffix}"
    role_b_code = f"QA_ROLE_COMPARE_B_{suffix}"
    headers = _auth_headers(admin_token)

    _cleanup(db_session, role_codes=[role_a_code, role_b_code], usernames=[])
    permission, created_permission = _ensure_permission(
        db_session,
        f"qa:compare:{suffix}",
        "角色比较测试权限",
    )
    role_a = _create_role(db_session, role_a_code, f"比较角色A-{suffix}", permissions=[permission])
    role_b = _create_role(db_session, role_b_code, f"比较角色B-{suffix}")
    db_session.commit()

    try:
        response = client.post(
            f"{settings.API_V1_PREFIX}/roles/compare",
            json=[role_a.id, role_b.id],
            headers=headers,
        )
        assert response.status_code == 200, response.text
        data = _unwrap_data(response)
        assert {item["role_id"] for item in data["roles"]} == {role_a.id, role_b.id}
        assert data["common_permissions"] == []
        assert f"qa:compare:{suffix}" in data["diff_permissions"][str(role_a.id)]
        assert data["diff_permissions"][str(role_b.id)] == []
    finally:
        _cleanup(
            db_session,
            role_codes=[role_a_code, role_b_code],
            usernames=[],
            permission_id=permission.id if created_permission else None,
        )


def test_role_assignment_grants_and_revokes_user_read_permission(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    username = f"qa_perm_user_{suffix}"
    password = "PermUser123!"
    role_code = f"QA_ROLE_USER_READ_{suffix}"
    headers = _auth_headers(admin_token)

    _cleanup(db_session, role_codes=[role_code], usernames=[username])
    permission, created_permission = _ensure_permission(db_session, "user:read", "查看用户")
    role = _create_role(db_session, role_code, f"用户查看角色-{suffix}", permissions=[permission])
    user = _create_user(db_session, username, password)
    db_session.commit()

    try:
        user_token = _login(client, username, password)
        denied = client.get(
            f"{settings.API_V1_PREFIX}/users/",
            headers=_auth_headers(user_token),
        )
        assert denied.status_code == 403, denied.text

        assign_response = client.put(
            f"{settings.API_V1_PREFIX}/users/{user.id}/roles",
            json={"role_ids": [role.id]},
            headers=headers,
        )
        assert assign_response.status_code == 200, assign_response.text

        granted_token = _login(client, username, password)
        granted = client.get(
            f"{settings.API_V1_PREFIX}/users/",
            headers=_auth_headers(granted_token),
        )
        assert granted.status_code == 200, granted.text

        revoke_response = client.put(
            f"{settings.API_V1_PREFIX}/users/{user.id}/roles",
            json={"role_ids": []},
            headers=headers,
        )
        assert revoke_response.status_code == 200, revoke_response.text

        revoked_token = _login(client, username, password)
        revoked = client.get(
            f"{settings.API_V1_PREFIX}/users/",
            headers=_auth_headers(revoked_token),
        )
        assert revoked.status_code == 403, revoked.text
    finally:
        _cleanup(
            db_session,
            role_codes=[role_code],
            usernames=[username],
            permission_id=permission.id if created_permission else None,
        )


def test_direct_user_role_assignment_requires_role_assign_permission(
    client: TestClient,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    tenant_code = f"QA_USER_ROLE_ASSIGN_TENANT_{suffix}"
    actor_username = f"qa_role_actor_{suffix}"
    target_username = f"qa_role_target_{suffix}"
    actor_role_code = f"QA_USER_UPDATE_ONLY_{suffix}"
    assignable_role_code = f"QA_ASSIGNABLE_ROLE_{suffix}"
    password = "PermUser123!"

    _cleanup(
        db_session,
        role_codes=[actor_role_code, assignable_role_code],
        usernames=[actor_username, target_username],
        tenant_codes=[tenant_code],
    )
    permission, created_permission = _ensure_permission(db_session, "user:update", "更新用户")
    tenant = _create_tenant(db_session, tenant_code, "用户角色分配边界租户")
    actor_role = _create_role(
        db_session,
        actor_role_code,
        f"仅用户更新角色-{suffix}",
        tenant_id=tenant.id,
        permissions=[permission],
    )
    assignable_role = _create_role(
        db_session,
        assignable_role_code,
        f"待分配角色-{suffix}",
        tenant_id=tenant.id,
    )
    actor = _create_user(db_session, actor_username, password, tenant_id=tenant.id)
    target = _create_user(db_session, target_username, password, tenant_id=tenant.id)
    _attach_role_to_user(db_session, actor, actor_role)
    db_session.commit()

    try:
        actor_token = _login(client, actor_username, password)
        response = client.put(
            f"{settings.API_V1_PREFIX}/users/{target.id}/roles",
            json={"role_ids": [assignable_role.id]},
            headers=_auth_headers(actor_token),
        )
        assert response.status_code == 403, response.text
        assert "role:assign" in response.text

        leaked_assignment = (
            db_session.query(UserRole)
            .filter(UserRole.user_id == target.id, UserRole.role_id == assignable_role.id)
            .first()
        )
        assert leaked_assignment is None
    finally:
        _cleanup(
            db_session,
            role_codes=[actor_role_code, assignable_role_code],
            usernames=[actor_username, target_username],
            permission_id=permission.id if created_permission else None,
            tenant_codes=[tenant_code],
        )


def test_batch_user_role_assignment_requires_role_assign_permission(
    client: TestClient,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    tenant_code = f"QA_BATCH_ROLE_ASSIGN_TENANT_{suffix}"
    actor_username = f"qa_batch_role_actor_{suffix}"
    target_username = f"qa_batch_role_target_{suffix}"
    actor_role_code = f"QA_BATCH_USER_UPDATE_ONLY_{suffix}"
    assignable_role_code = f"QA_BATCH_ASSIGNABLE_ROLE_{suffix}"
    password = "PermUser123!"

    _cleanup(
        db_session,
        role_codes=[actor_role_code, assignable_role_code],
        usernames=[actor_username, target_username],
        tenant_codes=[tenant_code],
    )
    permission, created_permission = _ensure_permission(db_session, "user:update", "更新用户")
    tenant = _create_tenant(db_session, tenant_code, "批量用户角色分配边界租户")
    actor_role = _create_role(
        db_session,
        actor_role_code,
        f"仅批量用户更新角色-{suffix}",
        tenant_id=tenant.id,
        permissions=[permission],
    )
    assignable_role = _create_role(
        db_session,
        assignable_role_code,
        f"批量待分配角色-{suffix}",
        tenant_id=tenant.id,
    )
    actor = _create_user(db_session, actor_username, password, tenant_id=tenant.id)
    target = _create_user(db_session, target_username, password, tenant_id=tenant.id)
    _attach_role_to_user(db_session, actor, actor_role)
    db_session.commit()

    try:
        actor_token = _login(client, actor_username, password)
        response = client.put(
            f"{settings.API_V1_PREFIX}/users/batch-roles",
            json={"user_ids": [target.id], "role_ids": [assignable_role.id], "mode": "replace"},
            headers=_auth_headers(actor_token),
        )
        assert response.status_code == 403, response.text
        assert "role:assign" in response.text

        leaked_assignment = (
            db_session.query(UserRole)
            .filter(UserRole.user_id == target.id, UserRole.role_id == assignable_role.id)
            .first()
        )
        assert leaked_assignment is None
    finally:
        _cleanup(
            db_session,
            role_codes=[actor_role_code, assignable_role_code],
            usernames=[actor_username, target_username],
            permission_id=permission.id if created_permission else None,
            tenant_codes=[tenant_code],
        )


def test_batch_user_role_assignment_rejects_unknown_mode_without_role_changes(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    username = f"qa_batch_mode_user_{suffix}"
    password = "PermUser123!"
    existing_role_code = f"QA_BATCH_MODE_EXISTING_{suffix}"
    replacement_role_code = f"QA_BATCH_MODE_REPLACEMENT_{suffix}"
    headers = _auth_headers(admin_token)

    _cleanup(
        db_session,
        role_codes=[existing_role_code, replacement_role_code],
        usernames=[username],
    )
    existing_role = _create_role(
        db_session,
        existing_role_code,
        f"批量模式原角色-{suffix}",
    )
    replacement_role = _create_role(
        db_session,
        replacement_role_code,
        f"批量模式误替换角色-{suffix}",
    )
    user = _create_user(db_session, username, password)
    _attach_role_to_user(db_session, user, existing_role)
    db_session.commit()

    try:
        response = client.put(
            f"{settings.API_V1_PREFIX}/users/batch-roles",
            json={"user_ids": [user.id], "role_ids": [replacement_role.id], "mode": "append"},
            headers=headers,
        )
        assert response.status_code == 422, response.text

        existing_link = (
            db_session.query(UserRole)
            .filter(UserRole.user_id == user.id, UserRole.role_id == existing_role.id)
            .first()
        )
        replacement_link = (
            db_session.query(UserRole)
            .filter(UserRole.user_id == user.id, UserRole.role_id == replacement_role.id)
            .first()
        )
        assert existing_link is not None
        assert replacement_link is None
    finally:
        _cleanup(
            db_session,
            role_codes=[existing_role_code, replacement_role_code],
            usernames=[username],
        )


def test_user_update_role_ids_requires_role_assign_permission(
    client: TestClient,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    tenant_code = f"QA_UPDATE_ROLE_IDS_TENANT_{suffix}"
    actor_username = f"qa_update_role_actor_{suffix}"
    target_username = f"qa_update_role_target_{suffix}"
    actor_role_code = f"QA_UPDATE_USER_ONLY_{suffix}"
    assignable_role_code = f"QA_UPDATE_ASSIGNABLE_ROLE_{suffix}"
    password = "PermUser123!"

    _cleanup(
        db_session,
        role_codes=[actor_role_code, assignable_role_code],
        usernames=[actor_username, target_username],
        tenant_codes=[tenant_code],
    )
    permission, created_permission = _ensure_permission(db_session, "user:update", "更新用户")
    tenant = _create_tenant(db_session, tenant_code, "用户更新角色边界租户")
    actor_role = _create_role(
        db_session,
        actor_role_code,
        f"仅用户更新角色-{suffix}",
        tenant_id=tenant.id,
        permissions=[permission],
    )
    assignable_role = _create_role(
        db_session,
        assignable_role_code,
        f"更新待分配角色-{suffix}",
        tenant_id=tenant.id,
    )
    actor = _create_user(db_session, actor_username, password, tenant_id=tenant.id)
    target = _create_user(db_session, target_username, password, tenant_id=tenant.id)
    _attach_role_to_user(db_session, actor, actor_role)
    db_session.commit()

    try:
        actor_token = _login(client, actor_username, password)
        response = client.put(
            f"{settings.API_V1_PREFIX}/users/{target.id}",
            json={"role_ids": [assignable_role.id]},
            headers=_auth_headers(actor_token),
        )
        assert response.status_code == 403, response.text
        assert "role:assign" in response.text

        leaked_assignment = (
            db_session.query(UserRole)
            .filter(UserRole.user_id == target.id, UserRole.role_id == assignable_role.id)
            .first()
        )
        assert leaked_assignment is None
    finally:
        _cleanup(
            db_session,
            role_codes=[actor_role_code, assignable_role_code],
            usernames=[actor_username, target_username],
            permission_id=permission.id if created_permission else None,
            tenant_codes=[tenant_code],
        )


def test_user_create_with_role_ids_requires_role_assign_permission(
    client: TestClient,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    tenant_code = f"QA_CREATE_ROLE_IDS_TENANT_{suffix}"
    actor_username = f"qa_create_role_actor_{suffix}"
    created_username = f"qa_create_role_target_{suffix}"
    actor_role_code = f"QA_CREATE_USER_ONLY_{suffix}"
    assignable_role_code = f"QA_CREATE_ASSIGNABLE_ROLE_{suffix}"
    password = "PermUser123!"

    _cleanup(
        db_session,
        role_codes=[actor_role_code, assignable_role_code],
        usernames=[actor_username, created_username],
        tenant_codes=[tenant_code],
    )
    permission, created_permission = _ensure_permission(db_session, "user:create", "创建用户")
    tenant = _create_tenant(db_session, tenant_code, "用户创建角色边界租户")
    actor_role = _create_role(
        db_session,
        actor_role_code,
        f"仅用户创建角色-{suffix}",
        tenant_id=tenant.id,
        permissions=[permission],
    )
    assignable_role = _create_role(
        db_session,
        assignable_role_code,
        f"创建待分配角色-{suffix}",
        tenant_id=tenant.id,
    )
    actor = _create_user(db_session, actor_username, password, tenant_id=tenant.id)
    _attach_role_to_user(db_session, actor, actor_role)
    db_session.commit()

    try:
        actor_token = _login(client, actor_username, password)
        response = client.post(
            f"{settings.API_V1_PREFIX}/users/",
            json={
                "username": created_username,
                "password": password,
                "real_name": "创建角色边界用户",
                "employee_no": f"QA-CREATE-ROLE-{suffix}",
                "department": "测试部",
                "position": "测试岗",
                "role_ids": [assignable_role.id],
            },
            headers=_auth_headers(actor_token),
        )
        assert response.status_code == 403, response.text
        assert "role:assign" in response.text

        created_user = db_session.query(User).filter(User.username == created_username).first()
        assert created_user is None
    finally:
        _cleanup(
            db_session,
            role_codes=[actor_role_code, assignable_role_code],
            usernames=[actor_username, created_username],
            permission_id=permission.id if created_permission else None,
            tenant_codes=[tenant_code],
        )


def test_batch_role_remove_invalidates_user_permission_cache(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    username = f"qa_batch_cache_user_{suffix}"
    password = "PermUser123!"
    role_code = f"QA_BATCH_CACHE_{suffix}"
    headers = _auth_headers(admin_token)
    cache_service = get_permission_cache_service()

    _cleanup(db_session, role_codes=[role_code], usernames=[username])
    permission, created_permission = _ensure_permission(db_session, "user:read", "查看用户")
    role = _create_role(db_session, role_code, f"批量缓存角色-{suffix}", permissions=[permission])
    user = _create_user(db_session, username, password)
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.commit()

    try:
        user_token = _login(client, username, password)
        user_headers = _auth_headers(user_token)

        granted = client.get(
            f"{settings.API_V1_PREFIX}/users/",
            headers=user_headers,
        )
        assert granted.status_code == 200, granted.text

        cache_service.set_user_permissions(user.id, {"user:read"}, user.tenant_id)
        batch_remove = client.put(
            f"{settings.API_V1_PREFIX}/users/batch-roles",
            json={"user_ids": [user.id], "role_ids": [role.id], "mode": "remove"},
            headers=headers,
        )
        assert batch_remove.status_code == 200, batch_remove.text

        removed_role = (
            db_session.query(UserRole)
            .filter(UserRole.user_id == user.id, UserRole.role_id == role.id)
            .first()
        )
        assert removed_role is None

        revoked = client.get(
            f"{settings.API_V1_PREFIX}/users/",
            headers=user_headers,
        )
        assert revoked.status_code == 403, revoked.text
    finally:
        cache_service.invalidate_user_role_change(user.id, [role.id], [], user.tenant_id)
        _cleanup(
            db_session,
            role_codes=[role_code],
            usernames=[username],
            permission_id=permission.id if created_permission else None,
        )


def test_updating_role_permissions_invalidates_existing_user_permission_cache(
    client: TestClient,
    admin_token: str,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    username = f"qa_role_cache_user_{suffix}"
    password = "PermUser123!"
    role_code = f"QA_ROLE_CACHE_{suffix}"
    headers = _auth_headers(admin_token)

    _cleanup(db_session, role_codes=[role_code], usernames=[username])
    permission, created_permission = _ensure_permission(db_session, "user:read", "查看用户")
    role = _create_role(db_session, role_code, f"权限缓存角色-{suffix}", permissions=[permission])
    user = _create_user(db_session, username, password)
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.commit()

    try:
        user_token = _login(client, username, password)
        granted = client.get(
            f"{settings.API_V1_PREFIX}/users/",
            headers=_auth_headers(user_token),
        )
        assert granted.status_code == 200, granted.text

        revoke_response = client.put(
            f"{settings.API_V1_PREFIX}/roles/{role.id}/permissions",
            json={"permission_ids": []},
            headers=headers,
        )
        assert revoke_response.status_code == 200, revoke_response.text

        revoked = client.get(
            f"{settings.API_V1_PREFIX}/users/",
            headers=_auth_headers(user_token),
        )
        assert revoked.status_code == 403, revoked.text
    finally:
        _cleanup(
            db_session,
            role_codes=[role_code],
            usernames=[username],
            permission_id=permission.id if created_permission else None,
        )
