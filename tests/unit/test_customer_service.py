# -*- coding: utf-8 -*-
"""
Tests for customer_service
客户服务测试
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.models.project.customer import Customer


@pytest.mark.unit
class TestCustomerService:
    """客户服务测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        """创建 CustomerService 实例"""
        from app.services.customer_service import CustomerService
        return CustomerService(mock_db)

    def test_init(self, mock_db):
        """测试服务初始化"""
        from app.services.customer_service import CustomerService
        service = CustomerService(mock_db)
        assert service.db == mock_db
        assert service.model == Customer
        assert service.resource_name == "客户"

    def test_list_customers_basic(self, service, mock_db):
        """测试基本客户列表"""
        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 0
            mock_result.page = 1
            mock_result.page_size = 20
            mock_list.return_value = mock_result

            result = service.list_customers()

            assert result["total"] == 0
            assert result["page"] == 1
            assert result["page_size"] == 20
            mock_list.assert_called_once()

    def test_list_customers_with_keyword(self, service, mock_db):
        """测试带关键词的客户列表"""
        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 5
            mock_result.page = 1
            mock_result.page_size = 20
            mock_list.return_value = mock_result

            result = service.list_customers(keyword="华为")

            call_args = mock_list.call_args[0][0]
            assert call_args.search == "华为"
            assert "customer_name" in call_args.search_fields
            assert "customer_code" in call_args.search_fields
            assert "short_name" in call_args.search_fields

    def test_list_customers_with_filters(self, service, mock_db):
        """测试带过滤条件的客户列表"""
        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 3
            mock_result.page = 1
            mock_result.page_size = 20
            mock_list.return_value = mock_result

            result = service.list_customers(
                customer_type="ENTERPRISE",
                industry="ELECTRONICS",
                status="ACTIVE"
            )

            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get("customer_type") == "ENTERPRISE"
            assert call_args.filters.get("industry") == "ELECTRONICS"
            assert call_args.filters.get("status") == "ACTIVE"

    def test_list_customers_pagination(self, service, mock_db):
        """测试客户列表分页"""
        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 45
            mock_result.page = 2
            mock_result.page_size = 10
            mock_list.return_value = mock_result

            result = service.list_customers(page=2, page_size=10)

            assert result["page"] == 2
            assert result["page_size"] == 10
            assert result["total"] == 45
            assert result["pages"] == 5  # (45 + 10 - 1) // 10 = 5

    def test_before_delete_no_projects(self, service, mock_db):
        """测试删除前检查（无关联项目）"""
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        # Should not raise
        service._before_delete(1)

    def test_before_delete_has_projects(self, service, mock_db):
        """测试删除前检查（有关联项目）"""
        from fastapi import HTTPException

        mock_db.query.return_value.filter.return_value.count.return_value = 3

        with pytest.raises(HTTPException) as exc_info:
            service._before_delete(1)

        assert exc_info.value.status_code == 400
        assert "3 个项目" in exc_info.value.detail

    def test_set_auto_sync(self, service, mock_db):
        """测试设置自动同步"""
        service.set_auto_sync(False)
        assert service._auto_sync is False

        service.set_auto_sync(True)
        assert service._auto_sync is True

    def test_after_update_with_auto_sync(self, service, mock_db):
        """测试更新后自动同步"""
        mock_customer = Mock(id=1, customer_name="测试客户")
        service._auto_sync = True

        with patch('app.services.data_sync_service.DataSyncService') as MockSyncService:
            mock_sync = Mock()
            MockSyncService.return_value = mock_sync

            result = service._after_update(mock_customer)

            assert result == mock_customer
            MockSyncService.assert_called_once_with(mock_db)
            mock_sync.sync_customer_to_projects.assert_called_once_with(1)
            mock_sync.sync_customer_to_contracts.assert_called_once_with(1)

    def test_after_update_auto_sync_disabled(self, service, mock_db):
        """测试更新后禁用自动同步"""
        mock_customer = Mock(id=1, customer_name="测试客户")
        service.set_auto_sync(False)

        with patch('app.services.data_sync_service.DataSyncService') as MockSyncService:
            result = service._after_update(mock_customer)

            assert result == mock_customer
            MockSyncService.assert_not_called()

    def test_after_update_sync_error_handled(self, service, mock_db):
        """测试更新后同步错误处理"""
        mock_customer = Mock(id=1, customer_name="测试客户")
        service._auto_sync = True

        with patch('app.services.data_sync_service.DataSyncService') as MockSyncService:
            MockSyncService.return_value.sync_customer_to_projects.side_effect = Exception("同步失败")

            # Should not raise, error is logged
            result = service._after_update(mock_customer)

            assert result == mock_customer

    def test_generate_code(self, service, mock_db):
        """测试生成客户编码"""
        with patch('app.utils.number_generator.generate_customer_code') as mock_gen:
            mock_gen.return_value = "CUS2601001"

            result = service.generate_code()

            assert result == "CUS2601001"
            mock_gen.assert_called_once_with(mock_db)
