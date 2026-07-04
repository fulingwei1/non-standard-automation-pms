# -*- coding: utf-8 -*-
"""TEN-03（全量铺开第五批）契约：STRICT 活动记录表 + SHARED-DEFAULT 模板/规则/字典表。

第四批把 392 张真正的业务实体表加了 tenant_id，但用关键词（"_log"/"_template"/
"_config" 等）粗暴排除了剩余约 101 张表，交付说明里写的是"有意排除"——但复核
后发现这批表里大多数并不是真的应该被排除：
- 进度日志/状态变更日志/AI生成任务/登录尝试 等，本质是"某个已归户的业务对象
  的活动记录"，跟 customers/contracts 一样是租户业务数据，不该被排除（STRICT
  子集，27 张，严格按租户过滤，存量数据回填到默认租户）。
- 合同模板/奖金规则/工序字典 等，才是真正"可复用定义"性质的表，套用 Role/
  ApiPermission 已验证过的 NULL=系统级共享 模式（SHARED-DEFAULT 子集，72 张，
  只加列不回填，查询时 tenant_id==当前租户 OR tenant_id IS NULL）。

本文件用各一张代表表验证两种子集的行为差异。
"""
import uuid

import pytest

from app.core.middleware.tenant_middleware import (
    set_current_tenant_id,
    set_current_user_is_superuser,
)
from app.models.bonus import BonusRule
from app.models.login_attempt import LoginAttempt
from app.models.tenant import Tenant, TenantPlan, TenantStatus


@pytest.fixture(autouse=True)
def _reset_tenant_context():
    set_current_tenant_id(None)
    set_current_user_is_superuser(None)
    yield
    set_current_tenant_id(None)
    set_current_user_is_superuser(None)


def _make_tenant(db, suffix):
    tenant = Tenant(
        tenant_code=f"ten03b5_{suffix}",
        tenant_name=f"batch5 tenant {suffix}",
        status=TenantStatus.ACTIVE.value,
        plan_type=TenantPlan.FREE.value,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def two_tenants(db):
    suffix = uuid.uuid4().hex[:8]
    return _make_tenant(db, f"a{suffix}"), _make_tenant(db, f"b{suffix}")


class TestStrictActivityRecordScope:
    """STRICT 子集代表：LoginAttempt（登录尝试记录）——本质是某个已归户账号
    的安全审计事件，跟 customers/contracts 一样是租户业务数据，严格按租户
    过滤，不放行 NULL（不套用 Role 那种共享默认语义）。"""

    def test_cross_tenant_login_attempt_isolation(self, db, two_tenants):
        tenant_a, tenant_b = two_tenants
        suffix = uuid.uuid4().hex[:8]

        attempt_a = LoginAttempt(
            tenant_id=tenant_a.id, username=f"user_a_{suffix}", ip_address="10.0.0.1"
        )
        attempt_b = LoginAttempt(
            tenant_id=tenant_b.id, username=f"user_b_{suffix}", ip_address="10.0.0.2"
        )
        db.add_all([attempt_a, attempt_b])
        db.commit()

        set_current_tenant_id(tenant_a.id)
        set_current_user_is_superuser(False)

        visible = (
            db.query(LoginAttempt)
            .filter(LoginAttempt.id.in_([attempt_a.id, attempt_b.id]))
            .all()
        )
        assert [x.id for x in visible] == [attempt_a.id]

    def test_new_login_attempt_auto_gets_tenant_id(self, db, two_tenants):
        tenant_a, _tenant_b = two_tenants
        suffix = uuid.uuid4().hex[:8]
        set_current_tenant_id(tenant_a.id)
        set_current_user_is_superuser(False)

        attempt = LoginAttempt(username=f"auto_{suffix}", ip_address="10.0.0.3")
        db.add(attempt)
        db.commit()

        assert attempt.tenant_id == tenant_a.id


class TestSharedDefaultTemplateScope:
    """SHARED-DEFAULT 子集代表：BonusRule（奖金规则）。存量/系统默认规则
    tenant_id=NULL，必须对所有租户可见；租户自定义规则显式传 tenant_id 后
    只对该租户可见，不影响其他租户看到共享默认规则。"""

    def test_shared_default_rule_visible_to_any_tenant(self, db, two_tenants):
        tenant_a, tenant_b = two_tenants
        suffix = uuid.uuid4().hex[:8]

        shared_rule = BonusRule(
            tenant_id=None,
            rule_code=f"SHARED_{suffix}",
            rule_name="系统默认奖金规则",
            bonus_type="performance",
        )
        db.add(shared_rule)
        db.commit()

        for tenant in (tenant_a, tenant_b):
            set_current_tenant_id(tenant.id)
            set_current_user_is_superuser(False)
            found = db.query(BonusRule).filter(BonusRule.id == shared_rule.id).first()
            assert found is not None, f"共享默认规则必须对租户 {tenant.id} 可见"

    def test_tenant_specific_rule_not_visible_to_other_tenant(self, db, two_tenants):
        tenant_a, tenant_b = two_tenants
        suffix = uuid.uuid4().hex[:8]

        tenant_rule = BonusRule(
            tenant_id=tenant_a.id,
            rule_code=f"CUSTOM_{suffix}",
            rule_name="租户A自定义奖金规则",
            bonus_type="performance",
        )
        db.add(tenant_rule)
        db.commit()

        set_current_tenant_id(tenant_b.id)
        set_current_user_is_superuser(False)

        found = db.query(BonusRule).filter(BonusRule.id == tenant_rule.id).first()
        assert found is None, "租户A的自定义规则不应对租户B可见"

        set_current_tenant_id(tenant_a.id)
        found_own = db.query(BonusRule).filter(BonusRule.id == tenant_rule.id).first()
        assert found_own is not None, "租户A应能看到自己的自定义规则"
