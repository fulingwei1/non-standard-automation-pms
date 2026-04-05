# -*- coding: utf-8 -*-
"""
租户隔离装饰器测试
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi import HTTPException
from app.core.decorators.tenant_isolation import (
    require_tenant_isolation,
    allow_cross_tenant,
    tenant_resource_check,
)


class MockUser:
    def __init__(self, id: int, tenant_id: int = None, is_superuser: bool = False):
        self.id = id
        self.tenant_id = tenant_id
        self.is_superuser = is_superuser


class MockDB:
    def __init__(self):
        self.info = {}


class TestRequireTenantIsolation:
    """测试 require_tenant_isolation 装饰器"""

    @pytest.mark.asyncio
    async def test_no_db_raises_error(self):
        """没有数据库会话应该抛出错误"""
        
        @require_tenant_isolation
        async def func(db, current_user):
            return {"status": "ok"}
        
        user = MockUser(id=1, tenant_id=100)
        with pytest.raises(HTTPException) as exc_info:
            await func(db=None, current_user=user)
        
        assert exc_info.value.status_code == 500
        assert "Database session not available" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_no_user_raises_error(self):
        """没有用户应该抛出错误"""
        
        @require_tenant_isolation
        async def func(db, current_user):
            return {"status": "ok"}
        
        db = MockDB()
        with pytest.raises(HTTPException) as exc_info:
            await func(db=db, current_user=None)
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_sets_tenant_info(self):
        """测试设置租户信息"""
        
        @require_tenant_isolation
        async def func(db, current_user):
            return {"tenant_id": db.info.get("tenant_id")}
        
        user = MockUser(id=1, tenant_id=100)
        db = MockDB()
        result = await func(db=db, current_user=user)
        
        assert result["tenant_id"] == 100
        assert db.info["current_user"].id == 1


class TestAllowCrossTenant:
    """测试 allow_cross_tenant 装饰器"""

    @pytest.mark.asyncio
    async def test_no_user_raises_error(self):
        """没有用户应该抛出错误"""
        
        @allow_cross_tenant()
        async def func(current_user):
            return {"status": "ok"}
        
        with pytest.raises(HTTPException) as exc_info:
            await func(current_user=None)
        
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_non_admin_denied(self):
        """非管理员应该被拒绝"""
        
        @allow_cross_tenant(admin_only=True)
        async def func(current_user):
            return {"status": "ok"}
        
        user = MockUser(id=1, is_superuser=False)
        with pytest.raises(HTTPException) as exc_info:
            await func(current_user=user)
        
        assert exc_info.value.status_code == 403
        assert "Superuser access required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_admin_allowed(self):
        """管理员应该被允许"""
        
        @allow_cross_tenant(admin_only=True)
        async def func(current_user):
            return {"status": "ok"}
        
        user = MockUser(id=1, is_superuser=True)
        result = await func(current_user=user)
        
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_non_admin_allowed_when_admin_only_false(self):
        """admin_only=False 时非管理员也可以访问"""
        
        @allow_cross_tenant(admin_only=False)
        async def func(current_user):
            return {"status": "ok"}
        
        user = MockUser(id=1, is_superuser=False)
        result = await func(current_user=user)
        
        assert result["status"] == "ok"


class TestTenantResourceCheck:
    """测试 tenant_resource_check 函数"""

    def test_superuser_can_access_any(self):
        """超级管理员可以访问任何资源"""
        user = MockUser(id=1, tenant_id=None, is_superuser=True)
        # 不应该抛出异常
        tenant_resource_check(user, 100, "project")
        tenant_resource_check(user, 200, "project")

    def test_regular_user_same_tenant(self):
        """同租户用户可以访问"""
        user = MockUser(id=1, tenant_id=100, is_superuser=False)
        tenant_resource_check(user, 100, "project")

    def test_regular_user_different_tenant_raises(self):
        """不同租户用户应该抛出异常"""
        user = MockUser(id=1, tenant_id=100, is_superuser=False)
        with pytest.raises(HTTPException) as exc_info:
            tenant_resource_check(user, 200, "project")
        
        assert exc_info.value.status_code == 403
        assert "Access denied" in exc_info.value.detail

    def test_system_resource_accessible(self):
        """系统级资源可以被所有用户访问"""
        user = MockUser(id=1, tenant_id=100, is_superuser=False)
        # None 表示系统级资源
        tenant_resource_check(user, None, "system_config")

    def test_custom_resource_name(self):
        """自定义资源名称"""
        user = MockUser(id=1, tenant_id=100, is_superuser=False)
        with pytest.raises(HTTPException) as exc_info:
            tenant_resource_check(user, 200, "customer")
        
        assert "customer" in exc_info.value.detail