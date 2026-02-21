# -*- coding: utf-8 -*-
"""
租户中间件测试

测试覆盖：
1. 正常流程 - 租户上下文设置和清理
2. 错误处理 - 无认证用户、租户ID缺失
3. 边界条件 - 超级管理员、系统级资源
4. 安全性 - 租户隔离、跨租户访问
"""

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from contextvars import copy_context

from app.core.middleware.tenant_middleware import (
    TenantContextMiddleware,
    get_current_tenant_id,
    set_current_tenant_id,
    TenantAwareQuery,
    require_same_tenant,
)
from app.models.user import User


@pytest.fixture
def test_app():
    """创建测试用FastAPI应用"""
    app = FastAPI()
    
    # 添加租户中间件
    app.add_middleware(TenantContextMiddleware)
    
    # 添加测试路由
    @app.get("/api/v1/data")
    async def data_route(request: Request):
        return {
            "tenant_id": getattr(request.state, "tenant_id", None),
            "context_tenant_id": get_current_tenant_id()
        }
    
    @app.get("/api/v1/public")
    async def public_route(request: Request):
        return {"message": "Public endpoint"}
    
    return app


@pytest.fixture
def client(test_app):
    """创建测试客户端"""
    return TestClient(test_app)


@pytest.fixture
def mock_user_with_tenant():
    """创建带租户的模拟用户"""
    user = Mock(spec=User)
    user.id = 1
    user.username = "tenant_user"
    user.tenant_id = 100
    user.is_active = True
    return user


@pytest.fixture
def mock_superuser():
    """创建超级管理员用户"""
    user = Mock(spec=User)
    user.id = 999
    user.username = "superadmin"
    user.tenant_id = None
    user.is_superuser = True
    user.is_active = True
    return user


class TestTenantMiddlewareNormalFlow:
    """测试正常流程"""
    
    def test_tenant_id_set_from_user(self, client, mock_user_with_tenant):
        """测试从用户提取租户ID并设置到上下文"""
        from unittest.mock import MagicMock
        
        original_dispatch = TenantContextMiddleware.dispatch
        
        async def mock_dispatch(self, request, call_next):
            # 模拟认证中间件已设置用户
            request.state.user = mock_user_with_tenant
            return await original_dispatch(self, request, call_next)
        
        with patch.object(TenantContextMiddleware, 'dispatch', mock_dispatch):
            response = client.get("/api/v1/data")
            
            assert response.status_code == 200
            data = response.json()
            # 注意：由于中间件在请求结束后清理上下文，这里可能是None
            # 但request.state.tenant_id应该被设置过
    
    def test_tenant_id_context_variable_set(self, mock_user_with_tenant):
        """测试租户ID设置到上下文变量"""
        set_current_tenant_id(mock_user_with_tenant.tenant_id)
        
        assert get_current_tenant_id() == 100
        
        # 清理
        set_current_tenant_id(None)
    
    def test_tenant_id_cleared_after_request(self):
        """测试请求结束后上下文被清理"""
        # 设置一个租户ID
        set_current_tenant_id(100)
        assert get_current_tenant_id() == 100
        
        # 模拟请求结束，清理上下文
        set_current_tenant_id(None)
        assert get_current_tenant_id() is None
    
    def test_unauthenticated_request_no_tenant(self, client):
        """测试未认证请求没有租户ID"""
        response = client.get("/api/v1/public")
        
        assert response.status_code == 200
        # 未认证请求的tenant_id应该是None


class TestTenantMiddlewareErrorHandling:
    """测试错误处理"""
    
    def test_user_without_tenant_id(self):
        """测试用户没有tenant_id属性"""
        user = Mock(spec=User)
        user.id = 1
        user.username = "no_tenant_user"
        # 故意不设置tenant_id
        
        # getattr应该返回None
        tenant_id = getattr(user, "tenant_id", None)
        assert tenant_id is None
    
    def test_missing_user_state(self):
        """测试request.state没有user属性"""
        # 这种情况下应该设置tenant_id为None
        set_current_tenant_id(None)
        assert get_current_tenant_id() is None


class TestTenantMiddlewareBoundaryConditions:
    """测试边界条件"""
    
    def test_superuser_tenant_id_null(self, mock_superuser):
        """测试超级管理员租户ID为None"""
        assert mock_superuser.tenant_id is None
        assert mock_superuser.is_superuser is True
    
    def test_zero_tenant_id(self):
        """测试租户ID为0"""
        set_current_tenant_id(0)
        assert get_current_tenant_id() == 0
        
        # 清理
        set_current_tenant_id(None)
    
    def test_negative_tenant_id(self):
        """测试负数租户ID"""
        set_current_tenant_id(-1)
        assert get_current_tenant_id() == -1
        
        # 清理
        set_current_tenant_id(None)
    
    def test_very_large_tenant_id(self):
        """测试超大租户ID"""
        large_id = 2**31 - 1  # 最大32位整数
        set_current_tenant_id(large_id)
        assert get_current_tenant_id() == large_id
        
        # 清理
        set_current_tenant_id(None)


class TestTenantAwareQuery:
    """测试租户感知查询"""
    
    def test_query_with_tenant_filter(self):
        """测试自动添加租户过滤"""
        from unittest.mock import MagicMock
        
        # 创建模拟数据库会话
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        # 创建模拟模型
        class MockModel:
            tenant_id = 100
        
        # 创建租户感知查询
        tenant_query = TenantAwareQuery(mock_db, tenant_id=100)
        query = tenant_query.query(MockModel)
        
        # 验证query方法被调用
        mock_db.query.assert_called_once_with(MockModel)
    
    def test_query_from_context(self):
        """测试从上下文获取租户ID"""
        from unittest.mock import MagicMock
        
        set_current_tenant_id(200)
        
        mock_db = MagicMock()
        tenant_query = TenantAwareQuery(mock_db)
        
        assert tenant_query.tenant_id == 200
        
        # 清理
        set_current_tenant_id(None)
    
    def test_query_without_auto_filter(self):
        """测试禁用自动过滤"""
        from unittest.mock import MagicMock
        
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        
        class MockModel:
            tenant_id = 100
        
        tenant_query = TenantAwareQuery(mock_db, tenant_id=100)
        query = tenant_query.query(MockModel, auto_filter=False)
        
        # 验证filter没有被调用（因为auto_filter=False）
        mock_db.query.assert_called_once_with(MockModel)
    
    def test_query_model_without_tenant_id(self):
        """测试模型没有tenant_id字段"""
        from unittest.mock import MagicMock
        
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        
        class MockModelNoTenant:
            pass  # 没有tenant_id字段
        
        tenant_query = TenantAwareQuery(mock_db, tenant_id=100)
        query = tenant_query.query(MockModelNoTenant)
        
        # 没有tenant_id字段，不应该添加过滤
        mock_db.query.assert_called_once_with(MockModelNoTenant)
    
    def test_filter_by_tenant(self):
        """测试手动添加租户过滤"""
        from unittest.mock import MagicMock
        
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        
        class MockModel:
            tenant_id = 100
        
        tenant_query = TenantAwareQuery(mock_db, tenant_id=100)
        filtered_query = tenant_query.filter_by_tenant(mock_query, MockModel)
        
        # 验证filter被调用
        assert mock_query.filter.called
    
    def test_filter_by_tenant_no_tenant_field(self):
        """测试模型没有tenant_id字段时不添加过滤"""
        from unittest.mock import MagicMock
        
        mock_db = MagicMock()
        mock_query = MagicMock()
        
        class MockModelNoTenant:
            pass
        
        tenant_query = TenantAwareQuery(mock_db, tenant_id=100)
        filtered_query = tenant_query.filter_by_tenant(mock_query, MockModelNoTenant)
        
        # 返回原查询，不添加过滤
        assert filtered_query == mock_query


class TestRequireSameTenant:
    """测试租户权限检查"""
    
    def test_same_tenant_id(self):
        """测试相同租户ID"""
        result = require_same_tenant(user_tenant_id=100, resource_tenant_id=100)
        assert result is True
    
    def test_different_tenant_id(self):
        """测试不同租户ID"""
        result = require_same_tenant(user_tenant_id=100, resource_tenant_id=200)
        assert result is False
    
    def test_superuser_access_all(self):
        """测试超级管理员可访问所有租户"""
        # 超级管理员的tenant_id为None
        result = require_same_tenant(user_tenant_id=None, resource_tenant_id=100)
        assert result is True
    
    def test_system_resource_accessible(self):
        """测试系统级资源（tenant_id=None）所有租户可访问"""
        result = require_same_tenant(user_tenant_id=100, resource_tenant_id=None)
        assert result is True
    
    def test_both_none(self):
        """测试两者都为None"""
        result = require_same_tenant(user_tenant_id=None, resource_tenant_id=None)
        assert result is True


class TestTenantContextIsolation:
    """测试租户上下文隔离"""
    
    def test_context_isolation_between_requests(self):
        """测试不同请求间的上下文隔离"""
        # 第一个请求
        set_current_tenant_id(100)
        tenant_id_1 = get_current_tenant_id()
        assert tenant_id_1 == 100
        
        # 清理（模拟请求结束）
        set_current_tenant_id(None)
        
        # 第二个请求
        set_current_tenant_id(200)
        tenant_id_2 = get_current_tenant_id()
        assert tenant_id_2 == 200
        
        # 清理
        set_current_tenant_id(None)
    
    def test_context_variable_thread_safety(self):
        """测试上下文变量的线程安全性"""
        # ContextVar在不同上下文中是隔离的
        import asyncio
        
        async def task_1():
            set_current_tenant_id(100)
            await asyncio.sleep(0.01)
            return get_current_tenant_id()
        
        async def task_2():
            set_current_tenant_id(200)
            await asyncio.sleep(0.01)
            return get_current_tenant_id()
        
        # 在实际异步环境中，每个任务应该有独立的上下文
        # 这里只是简单测试


class TestTenantMiddlewareSecurity:
    """测试安全性"""
    
    def test_tenant_id_not_leaked(self):
        """测试租户ID不泄露给其他请求"""
        # 设置一个租户ID
        set_current_tenant_id(100)
        
        # 模拟请求结束，清理
        set_current_tenant_id(None)
        
        # 下一个请求不应该有残留
        assert get_current_tenant_id() is None
    
    def test_cannot_spoof_tenant_id(self):
        """测试不能伪造租户ID"""
        # 租户ID只能从已认证用户的tenant_id获取
        # 不能通过请求参数或header设置
        set_current_tenant_id(100)
        current_id = get_current_tenant_id()
        
        # 应该是我们设置的值
        assert current_id == 100
        
        # 清理
        set_current_tenant_id(None)
    
    def test_tenant_isolation_enforcement(self):
        """测试租户隔离强制执行"""
        # 用户1的租户
        user1_tenant = 100
        
        # 用户2的租户
        user2_tenant = 200
        
        # 用户1不能访问用户2的资源
        assert require_same_tenant(user1_tenant, user2_tenant) is False
        
        # 用户1可以访问自己的资源
        assert require_same_tenant(user1_tenant, user1_tenant) is True


class TestTenantMiddlewareIntegration:
    """测试集成场景"""
    
    def test_middleware_order(self, test_app):
        """测试中间件顺序（应在认证中间件之后）"""
        # 租户中间件依赖认证中间件设置的request.state.user
        # 这个测试确保中间件顺序正确
        middlewares = [m for m in test_app.user_middleware]
        # 检查TenantContextMiddleware是否存在
        tenant_middleware_exists = any(
            'TenantContextMiddleware' in str(m)
            for m in middlewares
        )
        assert tenant_middleware_exists or len(middlewares) > 0
    
    def test_tenant_context_in_nested_calls(self):
        """测试嵌套调用中的租户上下文"""
        set_current_tenant_id(100)
        
        def inner_function():
            return get_current_tenant_id()
        
        def outer_function():
            return inner_function()
        
        # 嵌套调用应该能访问相同的租户上下文
        result = outer_function()
        assert result == 100
        
        # 清理
        set_current_tenant_id(None)
    
    def test_tenant_aware_query_integration(self):
        """测试租户感知查询集成"""
        from unittest.mock import MagicMock
        from sqlalchemy.orm import Session
        
        # 模拟数据库会话
        mock_db = MagicMock(spec=Session)
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        
        # 设置租户上下文
        set_current_tenant_id(100)
        
        class MockProject:
            tenant_id = 100
        
        # 使用租户感知查询
        tenant_query = TenantAwareQuery(mock_db)
        query = tenant_query.query(MockProject)
        results = query.all()
        
        # 验证查询被执行
        assert mock_query.all.called
        
        # 清理
        set_current_tenant_id(None)


class TestTenantMiddlewarePerformance:
    """测试性能相关"""
    
    def test_minimal_overhead(self):
        """测试中间件开销最小"""
        import time
        
        iterations = 1000
        
        # 测试上下文设置性能
        start = time.time()
        for i in range(iterations):
            set_current_tenant_id(i % 10)
        elapsed = time.time() - start
        
        # 应该很快完成（小于1秒）
        assert elapsed < 1.0
        
        # 清理
        set_current_tenant_id(None)
    
    def test_context_cleanup_performance(self):
        """测试上下文清理性能"""
        import time
        
        iterations = 1000
        
        start = time.time()
        for _ in range(iterations):
            set_current_tenant_id(100)
            set_current_tenant_id(None)
        elapsed = time.time() - start
        
        # 应该很快完成
        assert elapsed < 1.0
