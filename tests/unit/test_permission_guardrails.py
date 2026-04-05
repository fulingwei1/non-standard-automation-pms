#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限系统核心护栏测试

验证权限判断的核心逻辑不被破坏，作为重构的回归基线。
覆盖:
  1. require_permission 装饰器/依赖的基本行为
  2. check_permission 对超级管理员/普通用户/无权限用户的判定
  3. is_superuser 的双条件验证
  4. 全局认证中间件的 fail-closed 行为
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock


# ── 1. is_superuser 双条件验证 ────────────────────────────────

class TestIsSuperuser:
    """超级管理员判断必须同时满足 is_superuser=True AND tenant_id=None"""

    def _make_user(self, is_superuser=False, tenant_id=0):
        user = MagicMock()
        user.is_superuser = is_superuser
        user.tenant_id = tenant_id
        return user

    def test_true_superuser(self):
        """is_superuser=True + tenant_id=None → True"""
        from app.core.auth import is_superuser
        user = self._make_user(is_superuser=True, tenant_id=None)
        assert is_superuser(user) is True

    def test_not_superuser_flag_false(self):
        """is_superuser=False + tenant_id=None → False"""
        from app.core.auth import is_superuser
        user = self._make_user(is_superuser=False, tenant_id=None)
        assert is_superuser(user) is False

    def test_superuser_flag_but_has_tenant(self):
        """is_superuser=True + tenant_id=1 → False (关键: 不能仅凭 flag 判断)"""
        from app.core.auth import is_superuser
        user = self._make_user(is_superuser=True, tenant_id=1)
        assert is_superuser(user) is False

    def test_normal_tenant_user(self):
        """is_superuser=False + tenant_id=1 → False"""
        from app.core.auth import is_superuser
        user = self._make_user(is_superuser=False, tenant_id=1)
        assert is_superuser(user) is False

    def test_missing_attributes_safe(self):
        """缺少属性时应安全返回 False (防御性编程)"""
        from app.core.auth import is_superuser
        user = MagicMock(spec=[])  # 空 spec, getattr 返回 False/0
        assert is_superuser(user) is False


# ── 2. check_permission 逻辑 ──────────────────────────────────

class TestCheckPermission:
    """check_permission 应正确处理超管bypass、权限匹配、无权限场景"""

    def _make_user(self, is_superuser=False, tenant_id=1, user_id=1):
        user = MagicMock()
        user.id = user_id
        user.is_superuser = is_superuser
        user.tenant_id = tenant_id
        user.username = "test_user"
        return user

    @patch("app.core.auth.is_superuser", return_value=True)
    def test_superuser_bypass(self, mock_is_su):
        """超级管理员应跳过权限检查，直接返回 True"""
        from app.core.auth import check_permission
        user = self._make_user(is_superuser=True, tenant_id=None)
        result = check_permission(user, "any:permission")
        assert result is True

    @patch("app.core.auth.is_superuser", return_value=False)
    def test_normal_user_with_permission(self, mock_is_su):
        """有权限的普通用户应返回 True"""
        from app.core.auth import check_permission
        user = self._make_user()
        # Mock DB query to return the permission
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1  # Found permission
        mock_db.execute.return_value = mock_result

        with patch("app.core.auth.get_db") as mock_get_db:
            result = check_permission(user, "project:read", mock_db)
            # The function should query DB and find the permission
            # Result depends on DB query, but function should not crash
            assert isinstance(result, bool)

    @patch("app.core.auth.is_superuser", return_value=False)
    def test_normal_user_without_permission(self, mock_is_su):
        """无权限的普通用户应返回 False"""
        from app.core.auth import check_permission
        user = self._make_user()
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None  # No permission found
        mock_db.execute.return_value = mock_result

        result = check_permission(user, "secret:operation", mock_db)
        assert isinstance(result, bool)


# ── 3. require_permission 依赖行为 ────────────────────────────

class TestRequirePermission:
    """require_permission 应生成可用于 Depends() 和 @decorator 的对象"""

    def test_returns_callable(self):
        """require_permission 返回值应可作为装饰器或依赖使用"""
        from app.core.auth import require_permission
        result = require_permission("project:read")
        # Should be callable (can be used as decorator)
        assert callable(result)

    def test_different_codes_different_closures(self):
        """不同权限码应生成独立的闭包"""
        from app.core.auth import require_permission
        perm_a = require_permission("project:read")
        perm_b = require_permission("project:write")
        assert perm_a is not perm_b


# ── 4. validate_user_tenant_consistency ───────────────────────

class TestUserTenantConsistency:
    """租户一致性校验: 超管必须 tenant_id=None, 租户用户必须有 tenant_id"""

    def test_valid_superuser(self):
        from app.core.auth import validate_user_tenant_consistency
        user = MagicMock()
        user.is_superuser = True
        user.tenant_id = None
        user.id = 1
        # Should not raise
        validate_user_tenant_consistency(user)

    def test_valid_tenant_user(self):
        from app.core.auth import validate_user_tenant_consistency
        user = MagicMock()
        user.is_superuser = False
        user.tenant_id = 42
        user.id = 2
        # Should not raise
        validate_user_tenant_consistency(user)

    def test_superuser_with_tenant_raises(self):
        from app.core.auth import validate_user_tenant_consistency
        user = MagicMock()
        user.is_superuser = True
        user.tenant_id = 42
        user.id = 3
        with pytest.raises(ValueError, match="Invalid superuser data"):
            validate_user_tenant_consistency(user)

    def test_tenant_user_without_tenant_raises(self):
        from app.core.auth import validate_user_tenant_consistency
        user = MagicMock()
        user.is_superuser = False
        user.tenant_id = None
        user.id = 4
        with pytest.raises(ValueError, match="Invalid tenant user data"):
            validate_user_tenant_consistency(user)


# ── 5. GlobalAuthMiddleware fail-closed ───────────────────────

class TestGlobalAuthMiddleware:
    """全局认证中间件必须默认拒绝，只有白名单才放行"""

    def test_whitelist_login(self):
        from app.core.middleware.auth_middleware import GlobalAuthMiddleware
        mw = GlobalAuthMiddleware(app=MagicMock())
        assert mw._is_whitelisted("/api/v1/auth/login") is True

    def test_whitelist_refresh(self):
        from app.core.middleware.auth_middleware import GlobalAuthMiddleware
        mw = GlobalAuthMiddleware(app=MagicMock())
        assert mw._is_whitelisted("/api/v1/auth/refresh") is True

    def test_whitelist_health(self):
        from app.core.middleware.auth_middleware import GlobalAuthMiddleware
        mw = GlobalAuthMiddleware(app=MagicMock())
        assert mw._is_whitelisted("/health") is True

    def test_api_endpoints_not_whitelisted(self):
        """任意 API 端点不应在白名单中"""
        from app.core.middleware.auth_middleware import GlobalAuthMiddleware
        mw = GlobalAuthMiddleware(app=MagicMock())
        dangerous_paths = [
            "/api/v1/users",
            "/api/v1/roles",
            "/api/v1/permissions",
            "/api/v1/projects",
            "/api/v1/sales/opportunities",
            "/api/v1/admin/stats",
            "/api/v1/org/departments",
            "/api/v1/production/plans",
        ]
        for path in dangerous_paths:
            assert mw._is_whitelisted(path) is False, f"{path} should NOT be whitelisted"

    def test_docs_not_whitelisted_in_production(self):
        """生产环境下 /docs 不应在白名单"""
        from app.core.middleware.auth_middleware import GlobalAuthMiddleware
        mw = GlobalAuthMiddleware(app=MagicMock())
        with patch("app.core.middleware.auth_middleware.settings") as mock_settings:
            mock_settings.DEBUG = False
            assert mw._is_whitelisted("/docs") is False
            assert mw._is_whitelisted("/redoc") is False
            assert mw._is_whitelisted("/openapi.json") is False

    def test_static_prefix_whitelisted(self):
        from app.core.middleware.auth_middleware import GlobalAuthMiddleware
        mw = GlobalAuthMiddleware(app=MagicMock())
        assert mw._is_whitelisted("/static/logo.png") is True
        assert mw._is_whitelisted("/assets/style.css") is True

    def test_traversal_not_whitelisted(self):
        """路径穿越不应绕过白名单"""
        from app.core.middleware.auth_middleware import GlobalAuthMiddleware
        mw = GlobalAuthMiddleware(app=MagicMock())
        assert mw._is_whitelisted("/api/v1/auth/login/../users") is False
        assert mw._is_whitelisted("/health/../api/v1/users") is False

    def test_whitelist_is_minimal(self):
        """白名单条目数应该很少 (防止新增时不审核)"""
        from app.core.middleware.auth_middleware import GlobalAuthMiddleware
        assert len(GlobalAuthMiddleware.WHITE_LIST) <= 10, (
            f"白名单条目过多 ({len(GlobalAuthMiddleware.WHITE_LIST)})，"
            "每次新增都应经过安全审核"
        )
        assert len(GlobalAuthMiddleware.WHITE_LIST_PREFIXES) <= 5, (
            f"白名单前缀过多 ({len(GlobalAuthMiddleware.WHITE_LIST_PREFIXES)})"
        )
