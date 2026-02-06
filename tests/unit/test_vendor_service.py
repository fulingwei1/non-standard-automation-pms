# -*- coding: utf-8 -*-
"""
Tests for vendor_service
供应商服务测试
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch
from sqlalchemy.orm import Session

from app.models.vendor import Vendor


@pytest.mark.unit
class TestVendorService:
    """供应商服务测试"""

    @pytest.fixture
    def mock_db(self):
        """创建模拟数据库会话"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, mock_db):
        """创建 VendorService 实例"""
        from app.services.vendor_service import VendorService
        return VendorService(mock_db)

    def test_init(self, mock_db):
        """测试服务初始化"""
        from app.services.vendor_service import VendorService
        service = VendorService(mock_db)
        assert service.db == mock_db
        assert service.model == Vendor
        assert service.resource_name == "供应商"

    def test_to_response_basic(self, service, mock_db):
        """测试基本响应转换"""
        mock_vendor = Mock(
            id=1,
            supplier_code="SUP001",
            supplier_name="测试供应商",
            supplier_short_name="测试",
            supplier_type="MATERIAL",
            contact_person="张三",
            contact_phone="13800138000",
            contact_email="test@example.com",
            address="测试地址",
            quality_rating=Decimal("4.5"),
            delivery_rating=Decimal("4.2"),
            service_rating=Decimal("4.3"),
            overall_rating=Decimal("4.3"),
            supplier_level="A",
            status="ACTIVE",
            cooperation_start=date(2025, 1, 1),
            last_order_date=date(2026, 1, 15),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        result = service._to_response(mock_vendor)

        assert result.id == 1
        assert result.supplier_code == "SUP001"
        assert result.supplier_name == "测试供应商"
        assert result.supplier_level == "A"
        assert result.status == "ACTIVE"
        assert result.quality_rating == Decimal("4.5")

    def test_to_response_with_defaults(self, service, mock_db):
        """测试带默认值的响应转换"""
        mock_vendor = Mock(
            id=1,
            supplier_code="SUP002",
            supplier_name="供应商2",
            supplier_short_name=None,
            supplier_type="PROCESSING",
            contact_person=None,
            contact_phone=None,
            contact_email=None,
            address=None,
            quality_rating=None,
            delivery_rating=None,
            service_rating=None,
            overall_rating=None,
            supplier_level=None,
            status=None,
            cooperation_start=None,
            last_order_date=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        result = service._to_response(mock_vendor)

        assert result.quality_rating == Decimal("0")
        assert result.delivery_rating == Decimal("0")
        assert result.service_rating == Decimal("0")
        assert result.overall_rating == Decimal("0")
        assert result.supplier_level == "B"
        assert result.status == "ACTIVE"

    def test_list_suppliers_basic(self, service, mock_db):
        """测试基本供应商列表"""
        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 0
            mock_result.page = 1
            mock_result.page_size = 20
            mock_list.return_value = mock_result

            result = service.list_suppliers()

            assert result["total"] == 0
            assert result["page"] == 1
            mock_list.assert_called_once()
            # Check default vendor_type filter
            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get("vendor_type") == "MATERIAL"

    def test_list_suppliers_with_filters(self, service, mock_db):
        """测试带过滤条件的供应商列表"""
        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 5
            mock_result.page = 1
            mock_result.page_size = 20
            mock_list.return_value = mock_result

            result = service.list_suppliers(
                supplier_type="MATERIAL",
                status="ACTIVE",
                supplier_level="A"
            )

            assert result["total"] == 5
            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get("supplier_type") == "MATERIAL"
            assert call_args.filters.get("status") == "ACTIVE"
            assert call_args.filters.get("supplier_level") == "A"

    def test_list_suppliers_with_keyword(self, service, mock_db):
        """测试带关键词搜索的供应商列表"""
        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 3
            mock_result.page = 1
            mock_result.page_size = 20
            mock_list.return_value = mock_result

            result = service.list_suppliers(keyword="测试")

            call_args = mock_list.call_args[0][0]
            assert call_args.search == "测试"
            assert "supplier_name" in call_args.search_fields
            assert "supplier_code" in call_args.search_fields

    def test_list_suppliers_pagination(self, service, mock_db):
        """测试供应商列表分页"""
        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 55
            mock_result.page = 3
            mock_result.page_size = 10
            mock_list.return_value = mock_result

            result = service.list_suppliers(page=3, page_size=10)

            assert result["page"] == 3
            assert result["page_size"] == 10
            assert result["total"] == 55
            assert result["pages"] == 6  # (55 + 10 - 1) // 10 = 6

    def test_list_suppliers_vendor_type_filter(self, service, mock_db):
        """测试供应商类型过滤"""
        with patch.object(service, 'list') as mock_list:
            mock_result = Mock()
            mock_result.items = []
            mock_result.total = 10
            mock_result.page = 1
            mock_result.page_size = 20
            mock_list.return_value = mock_result

            result = service.list_suppliers(vendor_type="PROCESSING")

            call_args = mock_list.call_args[0][0]
            assert call_args.filters.get("vendor_type") == "PROCESSING"
