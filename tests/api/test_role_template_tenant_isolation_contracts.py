# -*- coding: utf-8 -*-
"""Tenant isolation contracts for role template endpoints."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.tenant import Tenant
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
    tenant_id: int,
    permissions: list[ApiPermission],
) -> Role:
    role = Role(
        tenant_id=tenant_id,
        role_code=code,
        role_name=name,
        description="role template tenant isolation contract",
        is_active=True,
    )
    db.add(role)
    db.flush()
    for permission in permissions:
        db.add(RoleApiPermission(role_id=role.id, permission_id=permission.id))
    db.flush()
    return role


def _create_user(
    db: Session,
    username: str,
    password: str,
    *,
    tenant_id: int,
    role_code: str,
    permissions: list[ApiPermission],
) -> User:
    user = User(
        tenant_id=tenant_id,
        username=username,
        password_hash=get_password_hash(password),
        auth_type="password",
        real_name="租户角色模板边界测试用户",
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
        f"租户角色模板管理员-{username}",
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
    template_codes: list[str],
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
    if role_ids:
        db.query(RoleApiPermission).filter(RoleApiPermission.role_id.in_(role_ids)).delete(
            synchronize_session=False
        )
        db.query(UserRole).filter(UserRole.role_id.in_(role_ids)).delete(synchronize_session=False)
        db.query(Role).filter(Role.id.in_(role_ids)).delete(synchronize_session=False)
    if template_codes:
        db.query(RoleTemplate).filter(RoleTemplate.template_code.in_(template_codes)).delete(
            synchronize_session=False
        )
    if user_ids:
        db.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)
    if tenant_ids:
        db.query(Tenant).filter(Tenant.id.in_(tenant_ids)).delete(synchronize_session=False)
    db.commit()


def _seed_tenant_template_managers(db: Session, suffix: str, password: str):
    tenant_a = _create_tenant(db, f"QA_TPL_TENANT_A_{suffix}", "模板租户A")
    tenant_b = _create_tenant(db, f"QA_TPL_TENANT_B_{suffix}", "模板租户B")
    permissions = [
        _ensure_permission(db, "role:read", "查看角色"),
        _ensure_permission(db, "role:create", "创建角色"),
        _ensure_permission(db, "role:update", "编辑角色"),
        _ensure_permission(db, "role:delete", "删除角色"),
    ]
    _create_user(
        db,
        f"qa_tpl_mgr_a_{suffix}",
        password,
        tenant_id=tenant_a.id,
        role_code=f"QA_TPL_ACTOR_A_{suffix}",
        permissions=permissions,
    )
    _create_user(
        db,
        f"qa_tpl_mgr_b_{suffix}",
        password,
        tenant_id=tenant_b.id,
        role_code=f"QA_TPL_ACTOR_B_{suffix}",
        permissions=permissions,
    )
    db.commit()
    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "username_a": f"qa_tpl_mgr_a_{suffix}",
        "username_b": f"qa_tpl_mgr_b_{suffix}",
    }


def test_tenant_role_template_list_and_detail_are_scoped(
    client: TestClient,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    password = "TenantTemplate123!"
    template_a_code = f"QA_TPL_A_{suffix}"
    template_b_code = f"QA_TPL_B_{suffix}"
    usernames = [f"qa_tpl_mgr_a_{suffix}", f"qa_tpl_mgr_b_{suffix}"]
    role_codes = [f"QA_TPL_ACTOR_A_{suffix}", f"QA_TPL_ACTOR_B_{suffix}"]
    tenant_codes = [f"QA_TPL_TENANT_A_{suffix}", f"QA_TPL_TENANT_B_{suffix}"]
    template_codes = [template_a_code, template_b_code]
    _cleanup(
        db_session,
        usernames=usernames,
        role_codes=role_codes,
        template_codes=template_codes,
        tenant_codes=tenant_codes,
    )
    seeded = _seed_tenant_template_managers(db_session, suffix, password)

    try:
        token_a = _login(client, seeded["username_a"], password)
        token_b = _login(client, seeded["username_b"], password)
        headers_a = _auth_headers(token_a)
        headers_b = _auth_headers(token_b)

        create_a = client.post(
            f"{settings.API_V1_PREFIX}/roles/templates/",
            json={
                "template_code": template_a_code,
                "template_name": "租户A模板",
                "description": "tenant A template",
            },
            headers=headers_a,
        )
        assert create_a.status_code == 201, create_a.text
        template_a = _unwrap_data(create_a)

        create_b = client.post(
            f"{settings.API_V1_PREFIX}/roles/templates/",
            json={
                "template_code": template_b_code,
                "template_name": "租户B模板",
                "description": "tenant B template",
            },
            headers=headers_b,
        )
        assert create_b.status_code == 201, create_b.text
        template_b = _unwrap_data(create_b)

        list_a = client.get(f"{settings.API_V1_PREFIX}/roles/templates", headers=headers_a)
        assert list_a.status_code == 200, list_a.text
        seen_codes = {item["template_code"] for item in _unwrap_data(list_a)}
        assert template_a_code in seen_codes
        assert template_b_code not in seen_codes

        own_detail = client.get(
            f"{settings.API_V1_PREFIX}/roles/templates/{template_a['id']}",
            headers=headers_a,
        )
        assert own_detail.status_code == 200, own_detail.text

        other_detail = client.get(
            f"{settings.API_V1_PREFIX}/roles/templates/{template_b['id']}",
            headers=headers_a,
        )
        assert other_detail.status_code == 404, other_detail.text
    finally:
        _cleanup(
            db_session,
            usernames=usernames,
            role_codes=role_codes,
            template_codes=template_codes,
            tenant_codes=tenant_codes,
        )


def test_tenant_role_template_writes_cannot_mutate_other_tenant_templates(
    client: TestClient,
    db_session: Session,
):
    suffix = uuid.uuid4().hex[:8]
    password = "TenantTemplate123!"
    template_a_code = f"QA_TPL_A_{suffix}"
    template_b_code = f"QA_TPL_B_{suffix}"
    created_role_code = f"QA_TPL_CREATED_FROM_OTHER_{suffix}"
    usernames = [f"qa_tpl_mgr_a_{suffix}", f"qa_tpl_mgr_b_{suffix}"]
    role_codes = [
        f"QA_TPL_ACTOR_A_{suffix}",
        f"QA_TPL_ACTOR_B_{suffix}",
        created_role_code,
    ]
    tenant_codes = [f"QA_TPL_TENANT_A_{suffix}", f"QA_TPL_TENANT_B_{suffix}"]
    template_codes = [template_a_code, template_b_code]
    _cleanup(
        db_session,
        usernames=usernames,
        role_codes=role_codes,
        template_codes=template_codes,
        tenant_codes=tenant_codes,
    )
    seeded = _seed_tenant_template_managers(db_session, suffix, password)

    try:
        token_a = _login(client, seeded["username_a"], password)
        token_b = _login(client, seeded["username_b"], password)
        headers_a = _auth_headers(token_a)
        headers_b = _auth_headers(token_b)

        create_a = client.post(
            f"{settings.API_V1_PREFIX}/roles/templates/",
            json={
                "template_code": template_a_code,
                "template_name": "租户A模板",
            },
            headers=headers_a,
        )
        assert create_a.status_code == 201, create_a.text
        template_a = _unwrap_data(create_a)

        create_b = client.post(
            f"{settings.API_V1_PREFIX}/roles/templates/",
            json={
                "template_code": template_b_code,
                "template_name": "租户B模板",
            },
            headers=headers_b,
        )
        assert create_b.status_code == 201, create_b.text
        template_b = _unwrap_data(create_b)

        update_other = client.put(
            f"{settings.API_V1_PREFIX}/roles/templates/{template_b['id']}",
            json={"template_name": "不应被其他租户更新"},
            headers=headers_a,
        )
        assert update_other.status_code == 404, update_other.text
        db_session.expire_all()
        persisted_b = db_session.query(RoleTemplate).filter(RoleTemplate.id == template_b["id"]).one()
        assert persisted_b.template_name == "租户B模板"

        create_from_other = client.post(
            f"{settings.API_V1_PREFIX}/roles/templates/{template_b['id']}/create-role",
            json={
                "role_code": created_role_code,
                "role_name": "不应从其他租户模板创建",
            },
            headers=headers_a,
        )
        assert create_from_other.status_code == 404, create_from_other.text
        assert db_session.query(Role).filter(Role.role_code == created_role_code).first() is None

        delete_other = client.delete(
            f"{settings.API_V1_PREFIX}/roles/templates/{template_b['id']}",
            headers=headers_a,
        )
        assert delete_other.status_code == 404, delete_other.text
        assert db_session.query(RoleTemplate).filter(RoleTemplate.id == template_b["id"]).first()

        delete_own = client.delete(
            f"{settings.API_V1_PREFIX}/roles/templates/{template_a['id']}",
            headers=headers_a,
        )
        assert delete_own.status_code == 200, delete_own.text
    finally:
        _cleanup(
            db_session,
            usernames=usernames,
            role_codes=role_codes,
            template_codes=template_codes,
            tenant_codes=tenant_codes,
        )
