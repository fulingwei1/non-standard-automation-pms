# -*- coding: utf-8 -*-
"""
CustomerService 综合单元测试

测试覆盖:
- __init__: 初始化服务
- list_customers: 获取客户列表
- _before_delete: 删除前检查
- set_auto_sync: 设置自动同步
- _after_update: 更新后同步
- generate_code: 生成客户编码
"""

from unittest.mock import MagicMock, patch

import pytest


class TestCustomerServiceInit:
    """测试 CustomerService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()

        service = CustomerService(mock_db)

        assert service.db == mock_db
        assert service.resource_name == "客户"

    def test_sets_correct_model(self):
        """测试设置正确的模型"""
        from app.services.customer_service import CustomerService
        from app.models.project.customer import Customer

        mock_db = MagicMock()

        service = CustomerService(mock_db)

        assert service.model == Customer


class TestListCustomers:
    """测试 list_customers 方法"""

    def test_returns_paginated_list(self):
        """测试返回分页列表"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        service = CustomerService(mock_db)

        mock_result = MagicMock()
        mock_result.items = [MagicMock(), MagicMock()]
        mock_result.total = 2
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result):
            result = service.list_customers(page=1, page_size=20)

            assert result['items'] == mock_result.items
            assert result['total'] == 2
            assert result['page'] == 1
            assert result['page_size'] == 20

    def test_filters_by_customer_type(self):
        """测试按客户类型过滤"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        service = CustomerService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_customers(customer_type="ENTERPRISE")

            mock_list.assert_called_once()
            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get('customer_type') == "ENTERPRISE"

    def test_filters_by_industry(self):
        """测试按行业过滤"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        service = CustomerService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_customers(industry="ELECTRONICS")

            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get('industry') == "ELECTRONICS"

    def test_filters_by_status(self):
        """测试按状态过滤"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        service = CustomerService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_customers(status="ACTIVE")

            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get('status') == "ACTIVE"

    def test_searches_by_keyword(self):
        """测试关键字搜索"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        service = CustomerService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_customers(keyword="华为")

            call_args = mock_list.call_args[0][0]
            assert call_args.search == "华为"
            assert "customer_name" in call_args.search_fields
            assert "customer_code" in call_args.search_fields

    def test_calculates_pages(self):
        """测试计算总页数"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        service = CustomerService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 45
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result):
            result = service.list_customers()

            # (45 + 20 - 1) // 20 = 3
            assert result['pages'] == 3


class TestBeforeDelete:
    """测试 _before_delete 方法"""

    def test_raises_error_when_projects_exist(self):
        """测试有关联项目时抛出错误"""
        from app.services.customer_service import CustomerService
        from fastapi import HTTPException

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 5

        service = CustomerService(mock_db)

        with pytest.raises(HTTPException) as exc_info:
            service._before_delete(1)

        assert exc_info.value.status_code == 400
        assert "5 个项目" in exc_info.value.detail

    def test_allows_delete_when_no_projects(self):
        """测试无关联项目时允许删除"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        service = CustomerService(mock_db)

        # 应该不抛出异常
        service._before_delete(1)


class TestSetAutoSync:
    """测试 set_auto_sync 方法"""

    def test_sets_auto_sync_true(self):
        """测试设置自动同步为True"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        service = CustomerService(mock_db)

        service.set_auto_sync(True)

        assert service._auto_sync is True

    def test_sets_auto_sync_false(self):
        """测试设置自动同步为False"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        service = CustomerService(mock_db)

        service.set_auto_sync(False)

        assert service._auto_sync is False


class TestAfterUpdate:
    """测试 _after_update 方法"""

    def test_syncs_data_when_auto_sync_enabled(self):
        """测试自动同步启用时同步数据"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        service = CustomerService(mock_db)
        service._auto_sync = True

        mock_customer = MagicMock()
        mock_customer.id = 1

        with patch('app.services.customer_service.DataSyncService') as mock_sync_class:
            mock_sync_service = MagicMock()
            mock_sync_class.return_value = mock_sync_service

            result = service._after_update(mock_customer)

            mock_sync_service.sync_customer_to_projects.assert_called_once_with(1)
            mock_sync_service.sync_customer_to_contracts.assert_called_once_with(1)
            assert result == mock_customer

    def test_skips_sync_when_auto_sync_disabled(self):
        """测试自动同步禁用时跳过同步"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        service = CustomerService(mock_db)
        service._auto_sync = False

        mock_customer = MagicMock()
        mock_customer.id = 1

        with patch('app.services.customer_service.DataSyncService') as mock_sync_class:
            result = service._after_update(mock_customer)

            mock_sync_class.assert_not_called()
            assert result == mock_customer

    def test_handles_sync_error_gracefully(self):
        """测试优雅处理同步错误"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        service = CustomerService(mock_db)
        service._auto_sync = True

        mock_customer = MagicMock()
        mock_customer.id = 1

        with patch('app.services.customer_service.DataSyncService') as mock_sync_class:
            mock_sync_class.side_effect = Exception("同步失败")

            # 不应抛出异常
            result = service._after_update(mock_customer)

            assert result == mock_customer


class TestGenerateCode:
    """测试 generate_code 方法"""

    def test_generates_customer_code(self):
        """测试生成客户编码"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        service = CustomerService(mock_db)

        with patch('app.services.customer_service.generate_customer_code', return_value="CUS20260101001") as mock_gen:
            result = service.generate_code()

            mock_gen.assert_called_once_with(mock_db)
            assert result == "CUS20260101001"
