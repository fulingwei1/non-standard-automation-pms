# -*- coding: utf-8 -*-
"""TEN-02 契约：ORM 查询层框架级租户过滤。

背景：原 TenantQuery 只重写了 __iter__，SQLAlchemy 2.0 下 .all()/.first()/
.count() 等常用方法都不经过 __iter__，过滤形同虚设（已用最小复现脚本验证）。
本测试证明新的 do_orm_execute + with_loader_criteria 实现覆盖这些常用方法。

未复用 tests/fixtures/tenant_fixtures.py 的固定用户名 fixture（user_a/user_b等）：
共享内存 SQLite 在同一 pytest 进程内跨用例持久化已提交数据，固定用户名会在
多个用例间产生不可预期的交叉污染（已实测复现，与本模块实现无关，是既有测试
基建债）。改为每个用例内用 uuid 后缀创建独立数据，规避该问题。
"""
import os
import uuid
from unittest.mock import patch

import pytest

from app.core.middleware.tenant_middleware import (
    set_current_tenant_id,
    set_current_user_is_superuser,
)
from app.core.security import get_password_hash
from app.models.tenant import Tenant, TenantPlan, TenantStatus
from app.models.user import User


@pytest.fixture(autouse=True)
def _reset_tenant_context():
    """确保每个用例前后上下文干净，不受其他用例污染。"""
    set_current_tenant_id(None)
    set_current_user_is_superuser(None)
    yield
    set_current_tenant_id(None)
    set_current_user_is_superuser(None)


def _make_tenant(db, suffix):
    tenant = Tenant(
        tenant_code=f"ten02_{suffix}",
        tenant_name=f"ten02 tenant {suffix}",
        status=TenantStatus.ACTIVE.value,
        plan_type=TenantPlan.FREE.value,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def _make_user(db, suffix, tenant_id, is_superuser=False):
    user = User(
        tenant_id=tenant_id,
        username=f"ten02_{suffix}",
        password_hash=get_password_hash("x"),
        is_active=True,
        is_superuser=is_superuser,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def two_tenant_users(db):
    """两个不同租户各一个普通用户，供跨租户隔离断言使用。"""
    suffix = uuid.uuid4().hex[:8]
    tenant_a = _make_tenant(db, f"a{suffix}")
    tenant_b = _make_tenant(db, f"b{suffix}")
    user_a = _make_user(db, f"ua{suffix}", tenant_a.id)
    user_b = _make_user(db, f"ub{suffix}", tenant_b.id)
    return user_a, user_b


class TestTenantQueryScopeAll:
    """.all() / .first() / .count() 都必须被过滤——这正是原实现绕过的方法。"""

    def test_all_filters_by_tenant(self, db, two_tenant_users):
        user_a, user_b = two_tenant_users
        set_current_tenant_id(user_a.tenant_id)
        set_current_user_is_superuser(False)

        results = db.query(User).filter(User.id.in_([user_a.id, user_b.id])).all()

        assert [u.id for u in results] == [user_a.id]

    def test_first_filters_by_tenant(self, db, two_tenant_users):
        user_a, user_b = two_tenant_users
        set_current_tenant_id(user_b.tenant_id)
        set_current_user_is_superuser(False)

        result = db.query(User).filter(User.id == user_a.id).first()

        assert result is None, ".first() 必须也被过滤，不能只有 __iter__ 生效"

    def test_count_filters_by_tenant(self, db, two_tenant_users):
        user_a, user_b = two_tenant_users
        set_current_tenant_id(user_a.tenant_id)
        set_current_user_is_superuser(False)

        count = db.query(User).filter(User.id.in_([user_a.id, user_b.id])).count()

        assert count == 1

    def test_cross_tenant_user_not_visible(self, db, two_tenant_users):
        """租户B上下文下查询租户A的用户ID必须查不到（核心隔离契约）。"""
        user_a, user_b = two_tenant_users
        set_current_tenant_id(user_b.tenant_id)
        set_current_user_is_superuser(False)

        result = db.query(User).filter(User.id == user_a.id).first()

        assert result is None


class TestTenantQueryScopeBypass:
    def test_superuser_sees_all_tenants(self, db, two_tenant_users):
        user_a, user_b = two_tenant_users
        set_current_tenant_id(None)
        set_current_user_is_superuser(True)

        ids = {
            u.id for u in db.query(User).filter(User.id.in_([user_a.id, user_b.id])).all()
        }

        assert ids == {user_a.id, user_b.id}

    def test_no_request_context_bypasses_filter(self, db, two_tenant_users):
        """后台任务/脚本场景：无请求上下文（is_superuser 上下文变量保持默认 None）不过滤。"""
        user_a, user_b = two_tenant_users
        set_current_tenant_id(None)
        # 不调用 set_current_user_is_superuser，保持 ContextVar 默认值 None

        ids = {
            u.id for u in db.query(User).filter(User.id.in_([user_a.id, user_b.id])).all()
        }

        assert ids == {user_a.id, user_b.id}

    def test_model_without_tenant_id_unaffected(self, db):
        """没有 tenant_id 字段的模型不受过滤影响，且不会被误判为 WHERE NULL。"""
        assert not hasattr(Tenant, "tenant_id"), "本用例前提：Tenant 自身不应有 tenant_id 字段"

        set_current_tenant_id(999999)
        set_current_user_is_superuser(False)

        # 断言的重点是"没有因为回退成 WHERE NULL 而恒为空"：用新建记录探测过滤器
        # 是否正确返回 true()（不过滤）而不是把无关模型也过滤成空结果。
        suffix = uuid.uuid4().hex[:8]
        _make_tenant(db, f"probe{suffix}")

        found_probe = db.query(Tenant).filter(Tenant.tenant_code == f"ten02_probe{suffix}").first()
        assert found_probe is not None, "无 tenant_id 字段的模型不应被过滤成空结果"


class TestTenantIdAutoPopulate:
    """TEN-03 铺开配套：新建对象带 tenant_id 字段但未显式赋值时自动补全。"""

    def test_new_object_gets_tenant_id_from_context(self, db):
        suffix = uuid.uuid4().hex[:8]
        tenant = _make_tenant(db, suffix)
        set_current_tenant_id(tenant.id)
        set_current_user_is_superuser(False)

        user = User(
            username=f"ten02_autofill_{suffix}",
            password_hash="x",
            is_active=True,
            is_superuser=False,
        )
        db.add(user)
        db.commit()

        assert user.tenant_id == tenant.id

    def test_explicit_tenant_id_not_overridden(self, db):
        suffix = uuid.uuid4().hex[:8]
        tenant_a = _make_tenant(db, f"a{suffix}")
        tenant_b = _make_tenant(db, f"b{suffix}")
        set_current_tenant_id(tenant_a.id)
        set_current_user_is_superuser(False)

        user = User(
            username=f"ten02_explicit_{suffix}",
            password_hash="x",
            is_active=True,
            is_superuser=False,
            tenant_id=tenant_b.id,
        )
        db.add(user)
        db.commit()

        assert user.tenant_id == tenant_b.id

    def test_no_context_leaves_tenant_id_none(self, db):
        suffix = uuid.uuid4().hex[:8]
        set_current_tenant_id(None)
        set_current_user_is_superuser(True)

        user = User(
            username=f"ten02_nocontext_{suffix}",
            password_hash="x",
            is_active=True,
            is_superuser=True,
        )
        db.add(user)
        db.commit()

        assert user.tenant_id is None


class TestTenantQueryScopeEnforceMode:
    """已认证非超管却无租户（不应出现的存量异常态）：strict 拒绝 / log 放行。"""

    def test_strict_mode_fails_closed(self, db, two_tenant_users):
        user_a, _user_b = two_tenant_users
        set_current_tenant_id(None)
        set_current_user_is_superuser(False)

        with patch.dict(os.environ, {"TENANT_ENFORCE_MODE": "strict"}):
            result = db.query(User).filter(User.id == user_a.id).first()

        assert result is None

    def test_log_mode_fails_open_with_warning(self, db, two_tenant_users):
        user_a, _user_b = two_tenant_users
        set_current_tenant_id(None)
        set_current_user_is_superuser(False)

        with patch.dict(os.environ, {"TENANT_ENFORCE_MODE": "log"}):
            result = db.query(User).filter(User.id == user_a.id).first()

        assert result is not None
