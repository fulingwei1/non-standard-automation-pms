# -*- coding: utf-8 -*-
"""TEN-06 契约：租户上下文从 fail-open 转可控 fail-closed。

现状：中间件对无 tenant_id 的用户置 None 放行（163 个非超管畅通无阻）。
目标（多租户已拍板）：
1. 决策函数 evaluate_tenant_access：超管放行（跨租户）、有租户放行、
   未认证放行（白名单在前置中间件管）；无租户的非超管——strict 拒绝 / log 放行并告警。
2. 模式由 TENANT_ENFORCE_MODE 控制（默认 log 灰度，归户迁移验证后切 strict）。
3. 归户迁移后存量非超管用户 tenant_id 不再为 NULL。
"""
import os
from types import SimpleNamespace
from unittest.mock import patch


def _user(tenant_id=None, superuser=False):
    return SimpleNamespace(id=1, tenant_id=tenant_id, is_superuser=superuser)


def test_superuser_always_allowed():
    from app.core.middleware.tenant_middleware import evaluate_tenant_access

    allowed, reason = evaluate_tenant_access(_user(tenant_id=None, superuser=True), "strict")
    assert allowed and reason == "superuser"


def test_tenant_user_allowed():
    from app.core.middleware.tenant_middleware import evaluate_tenant_access

    allowed, _ = evaluate_tenant_access(_user(tenant_id=1), "strict")
    assert allowed


def test_unauthenticated_passthrough():
    from app.core.middleware.tenant_middleware import evaluate_tenant_access

    allowed, reason = evaluate_tenant_access(None, "strict")
    assert allowed and reason == "unauthenticated"


def test_no_tenant_user_rejected_in_strict():
    from app.core.middleware.tenant_middleware import evaluate_tenant_access

    allowed, reason = evaluate_tenant_access(_user(tenant_id=None), "strict")
    assert not allowed, "strict 模式下无租户的非超管必须拒绝（fail-closed）"
    assert reason == "no-tenant"


def test_no_tenant_user_allowed_in_log_mode():
    from app.core.middleware.tenant_middleware import evaluate_tenant_access

    allowed, reason = evaluate_tenant_access(_user(tenant_id=None), "log")
    assert allowed, "log 灰度模式放行但记告警"
    assert "no-tenant" in reason


def test_mode_reads_env_default_log():
    from app.core.middleware.tenant_middleware import get_enforce_mode

    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("TENANT_ENFORCE_MODE", None)
        assert get_enforce_mode() == "log", "默认灰度 log（归户迁移验证后切 strict）"
    with patch.dict(os.environ, {"TENANT_ENFORCE_MODE": "strict"}):
        assert get_enforce_mode() == "strict"


def test_backfill_migration_exists_and_targets_non_superusers():
    from pathlib import Path

    sql = Path("migrations/20260704_tenant_user_backfill_sqlite.sql").read_text(encoding="utf-8")
    assert "UPDATE users" in sql and "tenant_id" in sql
    assert "is_superuser" in sql, "超管保留 NULL（跨租户身份），归户只针对非超管"
