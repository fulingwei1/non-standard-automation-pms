# -*- coding: utf-8 -*-
"""TEN-07 契约：租户生命周期/配额的管理面已存在，但此前从未被任何流程消费。

TenantService.check_tenant_login_allowed / check_user_quota 是 TEN-07 新增的
两个判定函数：前者供登录流程判断租户是否 SUSPENDED/已过期，后者供建用户
流程判断是否超过 max_users。本文件只测服务层逻辑本身；登录端点/建用户端点
的接线各有一条独立的集成测试（见 tests/api/test_auth_tenant_lifecycle_ten07.py）。
"""
import uuid
from datetime import datetime, timedelta

import pytest

from app.core.security import get_password_hash
from app.models.tenant import Tenant, TenantPlan, TenantStatus
from app.models.user import User
from app.services.tenant_service import TenantService


def _make_tenant(db, suffix, status=TenantStatus.ACTIVE.value, expired_at=None, max_users=None):
    tenant = Tenant(
        tenant_code=f"ten07_{suffix}",
        tenant_name=f"ten07 tenant {suffix}",
        status=status,
        plan_type=TenantPlan.FREE.value,
        expired_at=expired_at,
        max_users=max_users,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def _make_user(db, suffix, tenant_id):
    user = User(
        tenant_id=tenant_id,
        username=f"ten07_{suffix}",
        password_hash=get_password_hash("x"),
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


class TestCheckTenantLoginAllowed:
    def test_active_tenant_allowed(self, db):
        suffix = uuid.uuid4().hex[:8]
        tenant = _make_tenant(db, suffix)

        result = TenantService(db).check_tenant_login_allowed(tenant.id)

        assert result.allowed is True
        assert result.reason == "ok"

    def test_suspended_tenant_denied(self, db):
        suffix = uuid.uuid4().hex[:8]
        tenant = _make_tenant(db, suffix, status=TenantStatus.SUSPENDED.value)

        result = TenantService(db).check_tenant_login_allowed(tenant.id)

        assert result.allowed is False
        assert result.reason == "suspended"

    def test_expired_tenant_denied(self, db):
        suffix = uuid.uuid4().hex[:8]
        tenant = _make_tenant(
            db, suffix, expired_at=datetime.utcnow() - timedelta(days=1)
        )

        result = TenantService(db).check_tenant_login_allowed(tenant.id)

        assert result.allowed is False
        assert result.reason == "expired"

    def test_not_yet_expired_tenant_allowed(self, db):
        suffix = uuid.uuid4().hex[:8]
        tenant = _make_tenant(
            db, suffix, expired_at=datetime.utcnow() + timedelta(days=1)
        )

        result = TenantService(db).check_tenant_login_allowed(tenant.id)

        assert result.allowed is True

    def test_missing_tenant_denied(self, db):
        result = TenantService(db).check_tenant_login_allowed(999999999)

        assert result.allowed is False
        assert result.reason == "tenant-not-found"


class TestCheckUserQuota:
    def test_under_quota_allowed(self, db):
        suffix = uuid.uuid4().hex[:8]
        tenant = _make_tenant(db, suffix, max_users=2)
        _make_user(db, f"a{suffix}", tenant.id)

        result = TenantService(db).check_user_quota(tenant.id)

        assert result.allowed is True
        assert result.current == 1
        assert result.limit == 2

    def test_at_quota_denied(self, db):
        suffix = uuid.uuid4().hex[:8]
        tenant = _make_tenant(db, suffix, max_users=1)
        _make_user(db, f"a{suffix}", tenant.id)

        result = TenantService(db).check_user_quota(tenant.id)

        assert result.allowed is False
        assert result.current == 1
        assert result.limit == 1

    def test_no_quota_configured_allowed(self, db):
        """max_users 列有 default=5，ORM 构造时传 None 会被列默认值顶掉；
        用原生 SQL 强制置 NULL 才能复现真正"未配置配额"的存量数据场景。"""
        from sqlalchemy import text

        suffix = uuid.uuid4().hex[:8]
        tenant = _make_tenant(db, suffix, max_users=5)
        db.execute(
            text("UPDATE tenants SET max_users = NULL WHERE id = :tid"), {"tid": tenant.id}
        )
        db.commit()
        _make_user(db, f"a{suffix}", tenant.id)

        result = TenantService(db).check_user_quota(tenant.id)

        assert result.allowed is True
        assert result.limit is None

    def test_missing_tenant_allowed(self, db):
        """租户不存在时不拦截（与既有 get_tenant_stats 的宽容口径一致，避免误伤）。"""
        result = TenantService(db).check_user_quota(999999999)

        assert result.allowed is True
