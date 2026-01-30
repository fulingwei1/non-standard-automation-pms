# -*- coding: utf-8 -*-
"""
VendorService 综合单元测试

测试覆盖:
- __init__: 初始化服务
- _to_response: 转换响应对象
- list_suppliers: 获取供应商列表
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch
from datetime import datetime

import pytest


class TestVendorServiceInit:
    """测试 VendorService 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.vendor_service import VendorService

        mock_db = MagicMock()

        service = VendorService(mock_db)

        assert service.db == mock_db
        assert service.resource_name == "供应商"

    def test_sets_correct_model(self):
        """测试设置正确的模型"""
        from app.services.vendor_service import VendorService
        from app.models.vendor import Vendor

        mock_db = MagicMock()

        service = VendorService(mock_db)

        assert service.model == Vendor


class TestToResponse:
    """测试 _to_response 方法"""

    def test_converts_vendor_to_response(self):
        """测试转换供应商对象为响应"""
        from app.services.vendor_service import VendorService

        mock_db = MagicMock()
        service = VendorService(mock_db)

        mock_vendor = MagicMock()
        mock_vendor.id = 1
        mock_vendor.supplier_code = "SUP001"
        mock_vendor.supplier_name = "测试供应商"
        mock_vendor.supplier_short_name = "测试"
        mock_vendor.supplier_type = "MANUFACTURER"
        mock_vendor.contact_person = "张三"
        mock_vendor.contact_phone = "13800138000"
        mock_vendor.contact_email = "test@example.com"
        mock_vendor.address = "测试地址"
        mock_vendor.quality_rating = Decimal("4.5")
        mock_vendor.delivery_rating = Decimal("4.0")
        mock_vendor.service_rating = Decimal("4.2")
        mock_vendor.overall_rating = Decimal("4.3")
        mock_vendor.supplier_level = "A"
        mock_vendor.status = "ACTIVE"
        mock_vendor.cooperation_start = datetime(2024, 1, 1)
        mock_vendor.last_order_date = datetime(2024, 6, 1)
        mock_vendor.created_at = datetime(2024, 1, 1)
        mock_vendor.updated_at = datetime(2024, 1, 1)

        result = service._to_response(mock_vendor)

        assert result.id == 1
        assert result.supplier_code == "SUP001"
        assert result.supplier_name == "测试供应商"
        assert result.quality_rating == Decimal("4.5")
        assert result.supplier_level == "A"
        assert result.status == "ACTIVE"

    def test_handles_none_ratings(self):
        """测试处理空评分"""
        from app.services.vendor_service import VendorService

        mock_db = MagicMock()
        service = VendorService(mock_db)

        mock_vendor = MagicMock()
        mock_vendor.id = 1
        mock_vendor.supplier_code = "SUP002"
        mock_vendor.supplier_name = "新供应商"
        mock_vendor.supplier_short_name = None
        mock_vendor.supplier_type = "TRADER"
        mock_vendor.contact_person = None
        mock_vendor.contact_phone = None
        mock_vendor.contact_email = None
        mock_vendor.address = None
        mock_vendor.quality_rating = None
        mock_vendor.delivery_rating = None
        mock_vendor.service_rating = None
        mock_vendor.overall_rating = None
        mock_vendor.supplier_level = None
        mock_vendor.status = None
        mock_vendor.cooperation_start = None
        mock_vendor.last_order_date = None
        mock_vendor.created_at = datetime(2024, 1, 1)
        mock_vendor.updated_at = datetime(2024, 1, 1)

        result = service._to_response(mock_vendor)

        assert result.quality_rating == Decimal("0")
        assert result.delivery_rating == Decimal("0")
        assert result.service_rating == Decimal("0")
        assert result.overall_rating == Decimal("0")
        assert result.supplier_level == "B"
        assert result.status == "ACTIVE"


class TestListSuppliers:
    """测试 list_suppliers 方法"""

    def test_returns_paginated_list(self):
        """测试返回分页列表"""
        from app.services.vendor_service import VendorService

        mock_db = MagicMock()
        service = VendorService(mock_db)

        mock_result = MagicMock()
        mock_result.items = [MagicMock(), MagicMock()]
        mock_result.total = 2
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result):
            result = service.list_suppliers(page=1, page_size=20)

            assert result['items'] == mock_result.items
            assert result['total'] == 2
            assert result['page'] == 1
            assert result['page_size'] == 20

    def test_filters_by_supplier_type(self):
        """测试按供应商类型过滤"""
        from app.services.vendor_service import VendorService

        mock_db = MagicMock()
        service = VendorService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_suppliers(supplier_type="MANUFACTURER")

            mock_list.assert_called_once()
            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get('supplier_type') == "MANUFACTURER"

    def test_filters_by_status(self):
        """测试按状态过滤"""
        from app.services.vendor_service import VendorService

        mock_db = MagicMock()
        service = VendorService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_suppliers(status="ACTIVE")

            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get('status') == "ACTIVE"

    def test_filters_by_supplier_level(self):
        """测试按供应商级别过滤"""
        from app.services.vendor_service import VendorService

        mock_db = MagicMock()
        service = VendorService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_suppliers(supplier_level="A")

            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get('supplier_level') == "A"

    def test_filters_by_vendor_type(self):
        """测试按供应商类别过滤"""
        from app.services.vendor_service import VendorService

        mock_db = MagicMock()
        service = VendorService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_suppliers(vendor_type="OUTSOURCING")

            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get('vendor_type') == "OUTSOURCING"

    def test_searches_by_keyword(self):
        """测试关键字搜索"""
        from app.services.vendor_service import VendorService

        mock_db = MagicMock()
        service = VendorService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result) as mock_list:
            result = service.list_suppliers(keyword="华为")

            call_args = mock_list.call_args[0][0]
            assert call_args.search == "华为"
            assert "supplier_name" in call_args.search_fields
            assert "supplier_code" in call_args.search_fields

    def test_calculates_pages(self):
        """测试计算总页数"""
        from app.services.vendor_service import VendorService

        mock_db = MagicMock()
        service = VendorService(mock_db)

        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 45
        mock_result.page = 1
        mock_result.page_size = 20

        with patch.object(service, 'list', return_value=mock_result):
            result = service.list_suppliers()

            # (45 + 20 - 1) // 20 = 3
            assert result['pages'] == 3
