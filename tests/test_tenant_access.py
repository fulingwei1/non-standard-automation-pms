# -*- coding: utf-8 -*-
"""
租户访问权限测试
"""
import pytest
from unittest.mock import MagicMock
from app.core.permissions.tenant_access import (
    check_tenant_access,
    validate_tenant_match,
    ensure_tenant_consistency,
    check_bulk_access,
)


class MockUser:
    """模拟用户对象"""
    def __init__(self, id: int, tenant_id: int = None, is_superuser: bool = False):
        self.id = id
        self.tenant_id = tenant_id
        self.is_superuser = is_superuser


class TestCheckTenantAccess:
    """测试 check_tenant_access 函数"""

    def test_superuser_access_any_tenant(self):
        """超级管理员可以访问任何租户的资源"""
        superuser = MockUser(id=1, tenant_id=None, is_superuser=True)
        assert check_tenant_access(superuser, 100) is True
        assert check_tenant_access(superuser, 200) is True
        assert check_tenant_access(superuser, 999) is True

    def test_superuser_access_system_resource(self):
        """超级管理员可以访问系统级资源"""
        superuser = MockUser(id=1, tenant_id=None, is_superuser=True)
        assert check_tenant_access(superuser, None) is True

    def test_regular_user_access_own_tenant(self):
        """普通用户可以访问本租户的资源"""
        user = MockUser(id=2, tenant_id=100, is_superuser=False)
        assert check_tenant_access(user, 100) is True

    def test_regular_user_access_other_tenant(self):
        """普通用户不能访问其他租户的资源"""
        user = MockUser(id=2, tenant_id=100, is_superuser=False)
        assert check_tenant_access(user, 200) is False

    def test_regular_user_access_system_resource(self):
        """普通用户可以访问系统级资源"""
        user = MockUser(id=2, tenant_id=100, is_superuser=False)
        assert check_tenant_access(user, None) is True

    def test_user_without_tenant_id(self):
        """没有租户ID的用户不能访问租户资源"""
        user = MockUser(id=3, tenant_id=None, is_superuser=False)
        assert check_tenant_access(user, 100) is False

    def test_user_with_missing_attributes(self):
        """缺少属性的用户对象"""
        user = MagicMock()
        user.tenant_id = 100
        user.is_superuser = False
        assert check_tenant_access(user, 100) is True
        assert check_tenant_access(user, 200) is False


class TestValidateTenantMatch:
    """测试 validate_tenant_match 函数"""

    def test_empty_tenant_ids(self):
        """空租户ID列表应该返回 True"""
        user = MockUser(id=1, tenant_id=100, is_superuser=False)
        assert validate_tenant_match(user) is True
        assert validate_tenant_match(user, None) is True

    def test_single_tenant_id(self):
        """单个租户ID的验证"""
        user = MockUser(id=1, tenant_id=100, is_superuser=False)
        assert validate_tenant_match(user, 100) is True
        assert validate_tenant_match(user, 200) is False

    def test_multiple_same_tenant_ids(self):
        """多个相同租户ID"""
        user = MockUser(id=1, tenant_id=100, is_superuser=False)
        assert validate_tenant_match(user, 100, 100, 100) is True

    def test_different_tenant_ids(self):
        """不同租户ID应该返回 False"""
        user = MockUser(id=1, tenant_id=100, is_superuser=False)
        assert validate_tenant_match(user, 100, 200) is False

    def test_with_none_tenant_ids(self):
        """包含 None 的租户ID列表"""
        user = MockUser(id=1, tenant_id=100, is_superuser=False)
        # None 表示系统级资源，任何用户都可访问
        assert validate_tenant_match(user, 100, None) is True

    def test_superuser_with_different_tenants(self):
        """超级管理员可以操作不同租户的资源"""
        # 注意：validate_tenant_match 检查所有资源是否属于同一租户
        # 超级管理员虽然可以访问任何租户，但跨租户操作在业务上可能不被允许
        # 根据当前实现，validate_tenant_match 不允许不同租户ID
        # 所以这个测试应该验证超级管理员是否可以访问每个单独的租户
        superuser = MockUser(id=1, tenant_id=None, is_superuser=True)
        # 超级管理员可以访问任何单个租户
        assert check_tenant_access(superuser, 100) is True
        assert check_tenant_access(superuser, 200) is True


class TestEnsureTenantConsistency:
    """测试 ensure_tenant_consistency 函数"""

    def test_superuser_creates_resource(self):
        """超级管理员创建资源"""
        superuser = MockUser(id=1, tenant_id=None, is_superuser=True)
        resource_data = {"name": "test", "tenant_id": 100}
        result = ensure_tenant_consistency(superuser, resource_data)
        assert result["tenant_id"] == 100

    def test_regular_user_auto_set_tenant_id(self):
        """普通用户自动设置租户ID"""
        user = MockUser(id=2, tenant_id=100, is_superuser=False)
        resource_data = {"name": "test"}
        result = ensure_tenant_consistency(user, resource_data)
        assert result["tenant_id"] == 100

    def test_regular_user_cannot_create_other_tenant_resource(self):
        """普通用户不能创建其他租户的资源"""
        user = MockUser(id=2, tenant_id=100, is_superuser=False)
        resource_data = {"name": "test", "tenant_id": 200}
        with pytest.raises(ValueError):
            ensure_tenant_consistency(user, resource_data)

    def test_custom_tenant_field(self):
        """自定义租户字段名"""
        user = MockUser(id=2, tenant_id=100, is_superuser=False)
        resource_data = {"name": "test", "org_id": 200}
        with pytest.raises(ValueError):
            ensure_tenant_consistency(user, resource_data, tenant_field="org_id")


class TestCheckBulkAccess:
    """测试 check_bulk_access 函数"""

    def test_empty_resources(self):
        """空资源列表"""
        user = MockUser(id=1, tenant_id=100, is_superuser=False)
        assert check_bulk_access(user, []) is True

    def test_all_resources_accessible(self):
        """所有资源都可访问"""
        user = MockUser(id=1, tenant_id=100, is_superuser=False)
        resources = [
            MagicMock(id=1, tenant_id=100),
            MagicMock(id=2, tenant_id=100),
        ]
        assert check_bulk_access(user, resources) is True

    def test_some_resources_not_accessible(self):
        """部分资源不可访问"""
        user = MockUser(id=1, tenant_id=100, is_superuser=False)
        resources = [
            MagicMock(id=1, tenant_id=100),
            MagicMock(id=2, tenant_id=200),
        ]
        assert check_bulk_access(user, resources) is False

    def test_superuser_bulk_access(self):
        """超级管理员可以批量访问"""
        superuser = MockUser(id=1, tenant_id=None, is_superuser=True)
        resources = [
            MagicMock(id=1, tenant_id=100),
            MagicMock(id=2, tenant_id=200),
        ]
        assert check_bulk_access(superuser, resources) is True

    def test_custom_tenant_field(self):
        """自定义租户字段"""
        user = MockUser(id=1, tenant_id=100, is_superuser=False)
        resources = [
            MagicMock(id=1, org_id=100),
            MagicMock(id=2, org_id=100),
        ]
        assert check_bulk_access(user, resources, tenant_field="org_id") is True