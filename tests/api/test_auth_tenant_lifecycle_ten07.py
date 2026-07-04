# -*- coding: utf-8 -*-
"""TEN-07 契约：租户暂停/过期拒绝登录，配额满拒绝建用户（接线层集成测试）。

管理端（TEN-01）早就能把租户置为 SUSPENDED、设 expired_at、配 max_users，
但此前登录流程和建用户流程都从未读取过这几个字段——套餐/配额形同虚设。
服务层判定逻辑本身的单测见 tests/unit/test_tenant_lifecycle_ten07.py。
"""
import uuid
from datetime import datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.tenant import Tenant, TenantPlan, TenantStatus
from app.models.user import ApiPermission, Role, RoleApiPermission, User, UserRole


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _make_tenant(db: Session, suffix: str, **overrides) -> Tenant:
    tenant = Tenant(
        tenant_code=f"ten07api_{suffix}",
        tenant_name=f"ten07 api tenant {suffix}",
        status=overrides.pop("status", TenantStatus.ACTIVE.value),
        plan_type=TenantPlan.ENTERPRISE.value,
        max_users=overrides.pop("max_users", 100),
        **overrides,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def _make_login_user(db: Session, suffix: str, tenant_id: int, password: str) -> User:
    user = User(
        tenant_id=tenant_id,
        username=f"ten07api_{suffix}",
        password_hash=get_password_hash(password),
        real_name="TEN07 login test",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


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


def _make_actor_with_permission(
    db: Session, suffix: str, tenant_id: int, password: str, perm_code: str
) -> User:
    """建一个属于该租户、有指定权限的普通用户，供以它身份调用受权限保护的接口。"""
    permission = _ensure_permission(db, perm_code, perm_code)
    user = User(
        tenant_id=tenant_id,
        username=f"ten07actor_{suffix}",
        password_hash=get_password_hash(password),
        real_name="TEN07 actor",
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()
    role = Role(
        tenant_id=tenant_id,
        role_code=f"TEN07_ACTOR_{suffix}",
        role_name="ten07 actor role",
        is_system=False,
        is_active=True,
    )
    db.add(role)
    db.flush()
    db.add(RoleApiPermission(role_id=role.id, permission_id=permission.id))
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    return user


class TestTenantLoginLifecycle:
    def test_active_tenant_user_can_login(self, client: TestClient, db_session: Session):
        suffix = uuid.uuid4().hex[:8]
        password = "Ten07Login123!"
        tenant = _make_tenant(db_session, suffix)
        _make_login_user(db_session, suffix, tenant.id, password)

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"username": f"ten07api_{suffix}", "password": password},
        )

        assert response.status_code == 200, response.text
        assert "access_token" in response.json()

    def test_suspended_tenant_user_cannot_login(self, client: TestClient, db_session: Session):
        suffix = uuid.uuid4().hex[:8]
        password = "Ten07Login123!"
        tenant = _make_tenant(db_session, suffix, status=TenantStatus.SUSPENDED.value)
        _make_login_user(db_session, suffix, tenant.id, password)

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"username": f"ten07api_{suffix}", "password": password},
        )

        assert response.status_code == 403, response.text
        assert response.json()["detail"]["error_code"] == "TENANT_SUSPENDED"

    def test_expired_tenant_user_cannot_login(self, client: TestClient, db_session: Session):
        suffix = uuid.uuid4().hex[:8]
        password = "Ten07Login123!"
        tenant = _make_tenant(
            db_session, suffix, expired_at=datetime.utcnow() - timedelta(days=1)
        )
        _make_login_user(db_session, suffix, tenant.id, password)

        response = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"username": f"ten07api_{suffix}", "password": password},
        )

        assert response.status_code == 403, response.text
        assert response.json()["detail"]["error_code"] == "TENANT_EXPIRED"


class TestTenantUserQuota:
    def test_create_user_blocked_at_quota(self, client: TestClient, db_session: Session):
        suffix = uuid.uuid4().hex[:8]
        password = "Ten07Actor123!"
        tenant = _make_tenant(db_session, suffix, max_users=1)
        actor = _make_actor_with_permission(
            db_session, suffix, tenant.id, password, "user:create"
        )
        assert (
            db_session.query(User).filter(User.tenant_id == tenant.id).count() == 1
        ), "配额上限应设为已有用户数，保证下一次创建正好触发拦截"

        login_resp = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"username": actor.username, "password": password},
        )
        assert login_resp.status_code == 200, login_resp.text
        token = login_resp.json()["access_token"]

        response = client.post(
            f"{settings.API_V1_PREFIX}/users/",
            json={
                "username": f"ten07newuser_{suffix}",
                "password": "NewUser123!",
                "real_name": "should be blocked",
            },
            headers=_auth_headers(token),
        )

        assert response.status_code == 400, response.text
        assert "配额" in response.json()["detail"] or "上限" in response.json()["detail"]

    def test_create_user_allowed_under_quota(self, client: TestClient, db_session: Session):
        suffix = uuid.uuid4().hex[:8]
        password = "Ten07Actor123!"
        tenant = _make_tenant(db_session, suffix, max_users=10)
        actor = _make_actor_with_permission(
            db_session, suffix, tenant.id, password, "user:create"
        )

        login_resp = client.post(
            f"{settings.API_V1_PREFIX}/auth/login",
            data={"username": actor.username, "password": password},
        )
        assert login_resp.status_code == 200, login_resp.text
        token = login_resp.json()["access_token"]

        response = client.post(
            f"{settings.API_V1_PREFIX}/users/",
            json={
                "username": f"ten07newuser_{suffix}",
                "password": "NewUser123!",
                "real_name": "should be allowed",
            },
            headers=_auth_headers(token),
        )

        assert response.status_code in (200, 201), response.text
