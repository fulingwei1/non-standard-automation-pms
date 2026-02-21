# -*- coding: utf-8 -*-
"""
API依赖测试

测试覆盖：
1. 正常流程 - 用户认证、权限检查
2. 错误处理 - 未认证、权限不足
3. 边界条件 - 超级管理员、租户管理员
4. 安全性 - 权限隔离、越权防护
"""

import pytest
from fastapi import HTTPException, Request, status
from unittest.mock import Mock, MagicMock
from app.api.deps import (
    get_current_user_from_state,
    get_tenant_id,
    require_tenant_id,
    require_tenant_admin,
    require_super_admin,
)
from app.models.user import User


@pytest.fixture
def mock_request():
    """创建模拟请求"""
    request = Mock(spec=Request)
    request.state = Mock()
    return request


@pytest.fixture
def mock_normal_user():
    """创建普通用户"""
    user = Mock(spec=User)
    user.id = 1
    user.username = "normal_user"
    user.email = "user@example.com"
    user.is_active = True
    user.is_superuser = False
    user.is_tenant_admin = False
    user.tenant_id = 100
    return user


@pytest.fixture
def mock_tenant_admin():
    """创建租户管理员"""
    user = Mock(spec=User)
    user.id = 2
    user.username = "tenant_admin"
    user.email = "admin@tenant.com"
    user.is_active = True
    user.is_superuser = False
    user.is_tenant_admin = True
    user.tenant_id = 100
    return user


@pytest.fixture
def mock_superuser():
    """创建超级管理员"""
    user = Mock(spec=User)
    user.id = 999
    user.username = "superadmin"
    user.email = "super@admin.com"
    user.is_active = True
    user.is_superuser = True
    user.is_tenant_admin = False
    user.tenant_id = None
    return user


class TestGetCurrentUserFromState:
    """测试从request.state获取当前用户"""
    
    def test_get_user_success(self, mock_request, mock_normal_user):
        """测试成功获取用户"""
        mock_request.state.user = mock_normal_user
        
        user = get_current_user_from_state(mock_request)
        
        assert user is mock_normal_user
        assert user.id == 1
    
    def test_get_user_not_authenticated(self, mock_request):
        """测试未认证用户"""
        # request.state没有user属性
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_from_state(mock_request)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "未认证" in exc_info.value.detail
    
    def test_get_user_none(self, mock_request):
        """测试user为None"""
        mock_request.state.user = None
        
        # 这种情况可能返回None或抛异常，取决于实现
        # 如果中间件正确工作，不应该有这种情况
        result = get_current_user_from_state(mock_request)
        # 可能是None或抛异常


class TestGetTenantId:
    """测试获取租户ID"""
    
    def test_normal_user_tenant_id(self, mock_normal_user):
        """测试普通用户的租户ID"""
        tenant_id = get_tenant_id(current_user=mock_normal_user)
        
        assert tenant_id == 100
    
    def test_superuser_tenant_id_none(self, mock_superuser):
        """测试超级管理员租户ID为None"""
        tenant_id = get_tenant_id(current_user=mock_superuser)
        
        assert tenant_id is None
    
    def test_tenant_admin_tenant_id(self, mock_tenant_admin):
        """测试租户管理员的租户ID"""
        tenant_id = get_tenant_id(current_user=mock_tenant_admin)
        
        assert tenant_id == 100


class TestRequireTenantId:
    """测试要求租户ID"""
    
    def test_normal_user_has_tenant(self, mock_normal_user):
        """测试普通用户有租户ID"""
        tenant_id = require_tenant_id(current_user=mock_normal_user)
        
        assert tenant_id == 100
    
    def test_superuser_no_tenant(self, mock_superuser):
        """测试超级管理员没有租户ID"""
        with pytest.raises(HTTPException) as exc_info:
            require_tenant_id(current_user=mock_superuser)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "未关联租户" in exc_info.value.detail
    
    def test_user_without_tenant_id(self):
        """测试用户没有tenant_id属性"""
        user = Mock(spec=User)
        user.tenant_id = None
        
        with pytest.raises(HTTPException) as exc_info:
            require_tenant_id(current_user=user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestRequireTenantAdmin:
    """测试要求租户管理员权限"""
    
    def test_tenant_admin_success(self, mock_tenant_admin):
        """测试租户管理员通过"""
        user = require_tenant_admin(current_user=mock_tenant_admin)
        
        assert user is mock_tenant_admin
        assert user.is_tenant_admin is True
    
    def test_superuser_success(self, mock_superuser):
        """测试超级管理员通过"""
        user = require_tenant_admin(current_user=mock_superuser)
        
        assert user is mock_superuser
        assert user.is_superuser is True
    
    def test_normal_user_forbidden(self, mock_normal_user):
        """测试普通用户被拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            require_tenant_admin(current_user=mock_normal_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "租户管理员权限" in exc_info.value.detail


class TestRequireSuperAdmin:
    """测试要求超级管理员权限"""
    
    def test_superuser_success(self, mock_superuser):
        """测试超级管理员通过"""
        user = require_super_admin(current_user=mock_superuser)
        
        assert user is mock_superuser
        assert user.is_superuser is True
    
    def test_tenant_admin_forbidden(self, mock_tenant_admin):
        """测试租户管理员被拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            require_super_admin(current_user=mock_tenant_admin)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "超级管理员权限" in exc_info.value.detail
    
    def test_normal_user_forbidden(self, mock_normal_user):
        """测试普通用户被拒绝"""
        with pytest.raises(HTTPException) as exc_info:
            require_super_admin(current_user=mock_normal_user)
        
        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestDependencyChaining:
    """测试依赖链"""
    
    def test_get_tenant_id_from_state(self, mock_request, mock_normal_user):
        """测试从state获取用户再获取租户ID"""
        from unittest.mock import patch
        
        mock_request.state.user = mock_normal_user
        
        # 先获取用户
        user = get_current_user_from_state(mock_request)
        
        # 再获取租户ID
        tenant_id = get_tenant_id(current_user=user)
        
        assert tenant_id == 100
    
    def test_require_admin_after_get_user(self, mock_request, mock_tenant_admin):
        """测试获取用户后检查管理员权限"""
        mock_request.state.user = mock_tenant_admin
        
        user = get_current_user_from_state(mock_request)
        admin = require_tenant_admin(current_user=user)
        
        assert admin is mock_tenant_admin


class TestBoundaryConditions:
    """测试边界条件"""
    
    def test_user_with_zero_tenant_id(self):
        """测试租户ID为0"""
        user = Mock(spec=User)
        user.tenant_id = 0
        user.is_superuser = False
        
        tenant_id = get_tenant_id(current_user=user)
        assert tenant_id == 0
        
        required_id = require_tenant_id(current_user=user)
        assert required_id == 0
    
    def test_user_with_negative_tenant_id(self):
        """测试负数租户ID"""
        user = Mock(spec=User)
        user.tenant_id = -1
        user.is_superuser = False
        
        tenant_id = get_tenant_id(current_user=user)
        assert tenant_id == -1
    
    def test_both_superuser_and_tenant_admin(self):
        """测试同时是超级管理员和租户管理员"""
        user = Mock(spec=User)
        user.is_superuser = True
        user.is_tenant_admin = True
        user.tenant_id = None
        
        # 超级管理员优先
        tenant_id = get_tenant_id(current_user=user)
        assert tenant_id is None
        
        # 两个权限检查都应该通过
        require_tenant_admin(current_user=user)
        require_super_admin(current_user=user)


class TestSecurity:
    """测试安全性"""
    
    def test_privilege_escalation_prevention(self, mock_normal_user):
        """测试防止权限提升"""
        # 普通用户不能伪装成管理员
        with pytest.raises(HTTPException):
            require_tenant_admin(current_user=mock_normal_user)
        
        with pytest.raises(HTTPException):
            require_super_admin(current_user=mock_normal_user)
    
    def test_tenant_isolation(self):
        """测试租户隔离"""
        user1 = Mock(spec=User)
        user1.tenant_id = 100
        user1.is_superuser = False
        
        user2 = Mock(spec=User)
        user2.tenant_id = 200
        user2.is_superuser = False
        
        tenant_id_1 = get_tenant_id(current_user=user1)
        tenant_id_2 = get_tenant_id(current_user=user2)
        
        # 不同租户应该有不同ID
        assert tenant_id_1 != tenant_id_2
    
    def test_superuser_bypass_tenant_isolation(self, mock_superuser):
        """测试超级管理员绕过租户隔离"""
        tenant_id = get_tenant_id(current_user=mock_superuser)
        
        # 超级管理员tenant_id为None，可访问所有租户
        assert tenant_id is None


class TestIntegrationScenarios:
    """测试集成场景"""
    
    def test_complete_authentication_flow(self, mock_request, mock_normal_user):
        """测试完整认证流程"""
        # 1. 中间件设置用户到state
        mock_request.state.user = mock_normal_user
        
        # 2. 从state获取用户
        user = get_current_user_from_state(mock_request)
        assert user.id == 1
        
        # 3. 获取租户ID
        tenant_id = get_tenant_id(current_user=user)
        assert tenant_id == 100
        
        # 4. 要求有租户ID
        required_id = require_tenant_id(current_user=user)
        assert required_id == 100
    
    def test_admin_operation_flow(self, mock_request, mock_tenant_admin):
        """测试管理员操作流程"""
        mock_request.state.user = mock_tenant_admin
        
        # 获取用户
        user = get_current_user_from_state(mock_request)
        
        # 检查管理员权限
        admin = require_tenant_admin(current_user=user)
        assert admin.is_tenant_admin is True
        
        # 获取租户ID
        tenant_id = get_tenant_id(current_user=admin)
        assert tenant_id == 100
    
    def test_superuser_operation_flow(self, mock_request, mock_superuser):
        """测试超级管理员操作流程"""
        mock_request.state.user = mock_superuser
        
        user = get_current_user_from_state(mock_request)
        
        # 检查超级管理员权限
        superuser = require_super_admin(current_user=user)
        assert superuser.is_superuser is True
        
        # 获取租户ID（应该是None）
        tenant_id = get_tenant_id(current_user=superuser)
        assert tenant_id is None


class TestErrorMessages:
    """测试错误消息"""
    
    def test_unauthorized_error_message(self, mock_request):
        """测试未认证错误消息"""
        with pytest.raises(HTTPException) as exc_info:
            get_current_user_from_state(mock_request)
        
        assert "认证" in exc_info.value.detail or "登录" in exc_info.value.detail
    
    def test_no_tenant_error_message(self, mock_superuser):
        """测试无租户错误消息"""
        with pytest.raises(HTTPException) as exc_info:
            require_tenant_id(current_user=mock_superuser)
        
        assert "租户" in exc_info.value.detail
    
    def test_permission_denied_message(self, mock_normal_user):
        """测试权限拒绝消息"""
        with pytest.raises(HTTPException) as exc_info:
            require_tenant_admin(current_user=mock_normal_user)
        
        assert "权限" in exc_info.value.detail or "管理员" in exc_info.value.detail


class TestEdgeCases:
    """测试边缘情况"""
    
    def test_user_object_without_attributes(self):
        """测试用户对象缺少属性"""
        user = Mock()
        # 故意不设置必要属性
        
        # 应该有默认处理或抛出异常
        with pytest.raises(AttributeError):
            get_tenant_id(current_user=user)
    
    def test_inactive_user(self):
        """测试非活跃用户"""
        user = Mock(spec=User)
        user.id = 1
        user.is_active = False
        user.is_superuser = False
        user.tenant_id = 100
        
        # 依赖函数本身不检查is_active
        # is_active应该在get_current_active_user中检查
        tenant_id = get_tenant_id(current_user=user)
        assert tenant_id == 100
    
    def test_request_state_mutation(self, mock_request, mock_normal_user):
        """测试request.state被修改"""
        mock_request.state.user = mock_normal_user
        
        # 获取用户
        user1 = get_current_user_from_state(mock_request)
        
        # 修改state
        new_user = Mock(spec=User)
        new_user.id = 999
        mock_request.state.user = new_user
        
        # 再次获取应该得到新用户
        user2 = get_current_user_from_state(mock_request)
        assert user2.id == 999


class TestDependencyExports:
    """测试依赖导出"""
    
    def test_exported_dependencies_exist(self):
        """测试导出的依赖存在"""
        from app.api.deps import (
            get_current_user,
            get_current_active_user,
            get_current_active_superuser,
            get_db,
        )
        
        # 应该都能导入
        assert get_current_user is not None
        assert get_current_active_user is not None
        assert get_current_active_superuser is not None
        assert get_db is not None
    
    def test_db_dependency_reexported(self):
        """测试get_db依赖被重新导出"""
        from app.api.deps import get_db
        from app.dependencies import get_db as original_get_db
        
        # 应该是同一个函数
        assert get_db is original_get_db


class TestPerformance:
    """测试性能"""
    
    def test_dependency_call_overhead(self, mock_normal_user):
        """测试依赖调用开销"""
        import time
        
        iterations = 10000
        
        start = time.time()
        for _ in range(iterations):
            get_tenant_id(current_user=mock_normal_user)
        elapsed = time.time() - start
        
        # 应该很快
        avg_time = elapsed / iterations
        assert avg_time < 0.001  # 每次应该小于1ms
    
    def test_permission_check_overhead(self, mock_tenant_admin):
        """测试权限检查开销"""
        import time
        
        iterations = 10000
        
        start = time.time()
        for _ in range(iterations):
            require_tenant_admin(current_user=mock_tenant_admin)
        elapsed = time.time() - start
        
        avg_time = elapsed / iterations
        assert avg_time < 0.001
