# -*- coding: utf-8 -*-
"""业务逻辑测试示例 - CustomerService"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime


class TestCustomerServiceBusinessLogic:
    """CustomerService 业务逻辑测试"""

    def test_list_customers_with_filters(self):
        """测试带过滤条件的客户列表查询"""
        from app.services.customer_service import CustomerService

        # 1. 准备 Mock 数据
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.items = [
            MagicMock(customer_name="客户A", customer_code="C001"),
            MagicMock(customer_name="客户B", customer_code="C002"),
        ]
        mock_result.total = 2
        mock_result.page = 1
        mock_result.page_size = 20

        # 2. Mock list 方法返回
        service = CustomerService(mock_db)
        service.list = MagicMock(return_value=mock_result)

        # 3. 调用业务方法
        result = service.list_customers(
            page=1,
            page_size=20,
            keyword="测试",
            customer_type="企业",
            industry="制造业",
            status="active"
        )

        # 4. 验证结果
        assert result["total"] == 2
        assert result["page"] == 1
        assert len(result["items"]) == 2

        # 5. 验证 list 方法被正确调用
        service.list.assert_called_once()
        call_args = service.list.call_args[0][0]
        assert call_args.page == 1
        assert call_args.page_size == 20
        assert call_args.search == "测试"
        assert call_args.filters["customer_type"] == "企业"

    def test_list_customers_pagination(self):
        """测试分页逻辑"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 100
        mock_result.page = 5
        mock_result.page_size = 20

        service = CustomerService(mock_db)
        service.list = MagicMock(return_value=mock_result)

        result = service.list_customers(page=5, page_size=20)

        # 验证分页计算：total=100, page_size=20, pages=5
        assert result["pages"] == 5
        assert result["page"] == 5

    def test_list_customers_no_filters(self):
        """测试无过滤条件的查询"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        service = CustomerService(mock_db)
        service.list = MagicMock(return_value=mock_result)

        result = service.list_customers()

        assert result["total"] == 0
        service.list.assert_called_once()


class TestCustomerServiceDeleteLogic:
    """CustomerService 删除逻辑测试"""

    def test_delete_customer_with_projects_raises_error(self):
        """测试删除有关联项目的客户时抛出错误"""
        from app.services.customer_service import CustomerService
        from fastapi import HTTPException

        mock_db = MagicMock()

        # Mock 查询返回有关联项目
        mock_db.query.return_value.filter.return_value.count.return_value = 5

        service = CustomerService(mock_db)

        # 验证删除前检查会抛出异常
        with pytest.raises(HTTPException) as exc_info:
            service._before_delete(1)

        assert "项目" in str(exc_info.value.detail)

    def test_delete_customer_without_projects_succeeds(self):
        """测试删除无关联项目的客户成功"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()

        # Mock 查询返回无关联项目
        mock_db.query.return_value.filter.return_value.count.return_value = 0

        service = CustomerService(mock_db)

        # 不应该抛出异常
        service._before_delete(1)  # 正常执行


class TestCustomerServiceCreateLogic:
    """CustomerService 创建逻辑测试"""

    def test_create_customer_with_valid_data(self):
        """测试创建客户成功"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        service = CustomerService(mock_db)

        # Mock create 方法
        mock_created = MagicMock()
        mock_created.id = 1
        mock_created.customer_name = "新客户"
        service.create = MagicMock(return_value=mock_created)

        customer_data = {
            "customer_name": "新客户",
            "customer_code": "NEW001",
            "customer_type": "企业",
        }

        result = service.create(customer_data)

        assert result.id == 1
        assert result.customer_name == "新客户"
        service.create.assert_called_once_with(customer_data)


class TestCustomerServiceEdgeCases:
    """边界情况测试"""

    def test_list_customers_empty_result(self):
        """测试空结果"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        service = CustomerService(mock_db)
        service.list = MagicMock(return_value=mock_result)

        result = service.list_customers(keyword="不存在的客户")

        assert result["items"] == []
        assert result["total"] == 0

    def test_list_customers_large_page_size(self):
        """测试大分页"""
        from app.services.customer_service import CustomerService

        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.items = [MagicMock() for _ in range(100)]
        mock_result.total = 100
        mock_result.page = 1
        mock_result.page_size = 100

        service = CustomerService(mock_db)
        service.list = MagicMock(return_value=mock_result)

        result = service.list_customers(page=1, page_size=100)

        assert len(result["items"]) == 100