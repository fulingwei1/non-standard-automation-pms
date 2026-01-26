# -*- coding: utf-8 -*-
"""
租户服务单元测试

测试 TenantService 的业务逻辑
"""

from unittest.mock import MagicMock

import pytest

from app.models.tenant import Tenant, TenantStatus
from app.schemas.tenant import TenantCreate, TenantUpdate
from app.services.tenant_service import TenantService


class TestTenantServiceCreate:
    """租户创建测试"""

    def test_generate_tenant_code(self):
        """测试生成租户编码"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = TenantService(mock_db)
        code = service.generate_tenant_code()

        assert code.startswith("T")
        assert len(code) == 9  # T + 8 hex chars

    def test_create_tenant_success(self):
        """测试成功创建租户"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = TenantService(mock_db)
        tenant_in = TenantCreate(
            tenant_name="测试租户",
            plan_type="STANDARD",
            contact_name="张三",
            contact_email="zhangsan@example.com",
        )

        tenant = service.create_tenant(tenant_in)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_tenant_duplicate_code(self):
        """测试创建重复编码的租户"""
        mock_db = MagicMock()
        existing_tenant = Tenant(id=1, tenant_code="T12345678", tenant_name="已存在")
        mock_db.query.return_value.filter.return_value.first.return_value = existing_tenant

        service = TenantService(mock_db)
        tenant_in = TenantCreate(
            tenant_code="T12345678",
            tenant_name="新租户",
        )

        with pytest.raises(ValueError, match="已存在"):
            service.create_tenant(tenant_in)

    def test_create_tenant_with_plan_limits(self):
        """测试不同套餐的限制"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = TenantService(mock_db)

        # 测试免费套餐
        tenant_in = TenantCreate(tenant_name="免费租户", plan_type="FREE")
        service.create_tenant(tenant_in)

        # 验证调用了 add
        call_args = mock_db.add.call_args
        tenant = call_args[0][0]
        assert tenant.max_users == 5
        assert tenant.max_roles == 5


class TestTenantServiceRead:
    """租户查询测试"""

    def test_get_tenant_exists(self):
        """测试获取存在的租户"""
        mock_db = MagicMock()
        expected_tenant = Tenant(id=1, tenant_code="T12345678", tenant_name="测试")
        mock_db.query.return_value.filter.return_value.first.return_value = expected_tenant

        service = TenantService(mock_db)
        tenant = service.get_tenant(1)

        assert tenant == expected_tenant

    def test_get_tenant_not_exists(self):
        """测试获取不存在的租户"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = TenantService(mock_db)
        tenant = service.get_tenant(999)

        assert tenant is None

    def test_get_tenant_by_code(self):
        """测试根据编码获取租户"""
        mock_db = MagicMock()
        expected_tenant = Tenant(id=1, tenant_code="T12345678", tenant_name="测试")
        mock_db.query.return_value.filter.return_value.first.return_value = expected_tenant

        service = TenantService(mock_db)
        tenant = service.get_tenant_by_code("T12345678")

        assert tenant == expected_tenant

    def test_list_tenants(self):
        """测试获取租户列表"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            Tenant(id=1, tenant_code="T001", tenant_name="租户1"),
            Tenant(id=2, tenant_code="T002", tenant_name="租户2"),
        ]

        service = TenantService(mock_db)
        result = service.list_tenants(page=1, page_size=20)

        assert result["total"] == 2
        assert len(result["items"]) == 2
        assert result["page"] == 1
        assert result["page_size"] == 20

    def test_list_tenants_with_filter(self):
        """测试带筛选条件的租户列表"""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [
            Tenant(id=1, tenant_code="T001", tenant_name="活跃租户", status="ACTIVE"),
        ]

        service = TenantService(mock_db)
        result = service.list_tenants(status="ACTIVE", keyword="活跃")

        assert result["total"] == 1


class TestTenantServiceUpdate:
    """租户更新测试"""

    def test_update_tenant_success(self):
        """测试成功更新租户"""
        mock_db = MagicMock()
        existing_tenant = Tenant(
            id=1,
            tenant_code="T12345678",
            tenant_name="原名称",
            contact_name="原联系人"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing_tenant

        service = TenantService(mock_db)
        tenant_in = TenantUpdate(
            tenant_name="新名称",
            contact_name="新联系人"
        )

        tenant = service.update_tenant(1, tenant_in)

        assert tenant.tenant_name == "新名称"
        assert tenant.contact_name == "新联系人"
        mock_db.commit.assert_called_once()

    def test_update_tenant_not_exists(self):
        """测试更新不存在的租户"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = TenantService(mock_db)
        tenant_in = TenantUpdate(tenant_name="新名称")

        result = service.update_tenant(999, tenant_in)

        assert result is None


class TestTenantServiceDelete:
    """租户删除测试"""

    def test_delete_tenant_success(self):
        """测试成功删除租户（软删除）"""
        mock_db = MagicMock()
        existing_tenant = Tenant(
            id=1,
            tenant_code="T12345678",
            tenant_name="待删除",
            status="ACTIVE"
        )
        mock_db.query.return_value.filter.return_value.first.return_value = existing_tenant

        service = TenantService(mock_db)
        result = service.delete_tenant(1)

        assert result is True
        assert existing_tenant.status == TenantStatus.DELETED.value
        mock_db.commit.assert_called_once()

    def test_delete_tenant_not_exists(self):
        """测试删除不存在的租户"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = TenantService(mock_db)
        result = service.delete_tenant(999)

        assert result is False


class TestTenantServiceStats:
    """租户统计测试"""

    def test_get_tenant_stats_not_exists(self):
        """测试获取不存在租户的统计信息"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = TenantService(mock_db)
        stats = service.get_tenant_stats(999)

        assert stats is None
