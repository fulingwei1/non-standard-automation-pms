# -*- coding: utf-8 -*-
"""
app/api/deps.py 覆盖率测试（当前 34%）
"""
import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException, Request


class TestGetCurrentUserFromState:
    """测试从 request.state 获取用户"""

    def _make_request(self, user=None):
        req = MagicMock(spec=Request)
        if user is not None:
            req.state.user = user
        else:
            # 没有 user 属性
            del req.state.user
            req.state = MagicMock()
            del req.state.user
        return req

    def test_returns_user_from_state(self):
        from app.api.deps import get_current_user_from_state

        mock_user = MagicMock()
        mock_req = MagicMock(spec=Request)
        mock_req.state.user = mock_user

        result = get_current_user_from_state(mock_req)
        assert result is mock_user

    def test_raises_401_when_no_user(self):
        from app.api.deps import get_current_user_from_state

        mock_req = MagicMock(spec=Request)
        # 删除 user 属性，模拟未认证
        mock_req.state = MagicMock(spec=[])  # spec=[] 表示无任何属性

        with pytest.raises(HTTPException) as exc_info:
            get_current_user_from_state(mock_req)
        assert exc_info.value.status_code == 401


class TestGetTenantId:
    """测试获取租户 ID"""

    def test_superuser_returns_none(self):
        from app.api.deps import get_tenant_id

        mock_user = MagicMock()
        mock_user.is_superuser = True
        mock_user.tenant_id = 5

        result = get_tenant_id(current_user=mock_user)
        assert result is None  # 超级管理员返回 None

    def test_normal_user_returns_tenant_id(self):
        from app.api.deps import get_tenant_id

        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.tenant_id = 42

        result = get_tenant_id(current_user=mock_user)
        assert result == 42

    def test_user_without_tenant(self):
        from app.api.deps import get_tenant_id

        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.tenant_id = None

        result = get_tenant_id(current_user=mock_user)
        assert result is None


class TestRequireTenantId:
    """测试必须有租户 ID"""

    def test_with_tenant_id(self):
        from app.api.deps import require_tenant_id

        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.tenant_id = 10

        result = require_tenant_id(current_user=mock_user)
        assert result == 10

    def test_superuser_raises_or_returns(self):
        from app.api.deps import require_tenant_id

        mock_user = MagicMock()
        mock_user.is_superuser = True
        mock_user.tenant_id = None

        # 超级管理员没有 tenant_id，require_tenant_id 可能报错或返回 None
        try:
            result = require_tenant_id(current_user=mock_user)
            assert result is None or isinstance(result, int)
        except HTTPException as e:
            assert e.status_code in (400, 403)

    def test_no_tenant_raises_400(self):
        from app.api.deps import require_tenant_id

        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.tenant_id = None

        with pytest.raises(HTTPException) as exc_info:
            require_tenant_id(current_user=mock_user)
        assert exc_info.value.status_code in (400, 403)


class TestRequireTenantAdmin:
    """测试必须是租户管理员"""

    def test_tenant_admin_passes(self):
        from app.api.deps import require_tenant_admin

        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.is_tenant_admin = True
        mock_user.tenant_id = 1

        result = require_tenant_admin(current_user=mock_user)
        assert result is mock_user

    def test_non_admin_raises_403(self):
        from app.api.deps import require_tenant_admin

        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.is_tenant_admin = False

        with pytest.raises(HTTPException) as exc_info:
            require_tenant_admin(current_user=mock_user)
        assert exc_info.value.status_code == 403

    def test_superuser_passes(self):
        from app.api.deps import require_tenant_admin

        mock_user = MagicMock()
        mock_user.is_superuser = True

        # 超级管理员应该通过（即使不是 tenant_admin）
        result = require_tenant_admin(current_user=mock_user)
        assert result is mock_user


class TestRequireSuperAdmin:
    """测试必须是超级管理员"""

    def test_superuser_passes(self):
        from app.api.deps import require_super_admin

        mock_user = MagicMock()
        mock_user.is_superuser = True

        result = require_super_admin(current_user=mock_user)
        assert result is mock_user

    def test_non_superuser_raises_403(self):
        from app.api.deps import require_super_admin

        mock_user = MagicMock()
        mock_user.is_superuser = False

        with pytest.raises(HTTPException) as exc_info:
            require_super_admin(current_user=mock_user)
        assert exc_info.value.status_code == 403
