# -*- coding: utf-8 -*-
"""VendorService 单元测试"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestVendorServiceToResponse:
    """_to_response 方法测试"""

    def _make_service(self):
        from app.services.vendor_service import VendorService
        db = MagicMock()
        svc = VendorService(db)
        return svc

    def test_to_response_defaults_applied(self):
        """None 评分字段应默认为 Decimal('0')，状态默认为 'ACTIVE'"""
        svc = self._make_service()
        vendor = MagicMock()
        vendor.quality_rating = None
        vendor.delivery_rating = None
        vendor.service_rating = None
        vendor.overall_rating = None
        vendor.supplier_level = None
        vendor.status = None
        vendor.id = 1
        vendor.supplier_code = "V001"
        vendor.supplier_name = "测试供应商"
        vendor.supplier_short_name = "测试"
        vendor.supplier_type = "MATERIAL"
        vendor.contact_person = "张三"
        vendor.contact_phone = "13800000000"
        vendor.contact_email = "test@test.com"
        vendor.address = "北京"
        vendor.cooperation_start = None
        vendor.last_order_date = None
        vendor.created_at = None
        vendor.updated_at = None

        result = svc._to_response(vendor)
        assert result.quality_rating == Decimal("0")
        assert result.delivery_rating == Decimal("0")
        assert result.supplier_level == "B"
        assert result.status == "ACTIVE"

    def test_to_response_preserves_values(self):
        """非空字段应原样保留"""
        svc = self._make_service()
        vendor = MagicMock()
        vendor.quality_rating = Decimal("4.5")
        vendor.delivery_rating = Decimal("4.0")
        vendor.service_rating = Decimal("3.5")
        vendor.overall_rating = Decimal("4.0")
        vendor.supplier_level = "A"
        vendor.status = "INACTIVE"
        vendor.id = 2
        vendor.supplier_code = "V002"
        vendor.supplier_name = "优质供应商"
        vendor.supplier_short_name = "优质"
        vendor.supplier_type = "SERVICE"
        vendor.contact_person = "李四"
        vendor.contact_phone = "13900000000"
        vendor.contact_email = "good@test.com"
        vendor.address = "上海"
        vendor.cooperation_start = None
        vendor.last_order_date = None
        vendor.created_at = None
        vendor.updated_at = None

        result = svc._to_response(vendor)
        assert result.quality_rating == Decimal("4.5")
        assert result.supplier_level == "A"
        assert result.status == "INACTIVE"


class TestVendorServiceListSuppliers:
    """list_suppliers 方法测试"""

    def _make_service_with_list_result(self, items=None, total=0):
        from app.services.vendor_service import VendorService
        db = MagicMock()
        svc = VendorService(db)
        list_result = MagicMock()
        list_result.items = items or []
        list_result.total = total
        list_result.page = 1
        list_result.page_size = 20
        svc.list = MagicMock(return_value=list_result)
        return svc

    def test_list_suppliers_returns_dict(self):
        """list_suppliers 返回包含 items/total/page/page_size/pages 的字典"""
        svc = self._make_service_with_list_result(items=[], total=0)
        result = svc.list_suppliers()
        assert "items" in result
        assert "total" in result
        assert "page" in result
        assert "page_size" in result
        assert "pages" in result

    def test_list_suppliers_pagination_calc(self):
        """pages 计算正确"""
        svc = self._make_service_with_list_result(items=[], total=45)
        result = svc.list_suppliers(page_size=20)
        assert result["pages"] == 3  # ceil(45/20) = 3

    def test_list_suppliers_passes_filters(self):
        """传入的过滤参数应透传给 self.list"""
        svc = self._make_service_with_list_result(items=[], total=0)
        svc.list_suppliers(keyword="ABC", supplier_type="MATERIAL", status="ACTIVE")
        call_args = svc.list.call_args[0][0]
        assert call_args.search == "ABC"
        assert call_args.filters.get("supplier_type") == "MATERIAL"
        assert call_args.filters.get("status") == "ACTIVE"

    def test_list_suppliers_default_vendor_type(self):
        """默认 vendor_type 为 MATERIAL"""
        svc = self._make_service_with_list_result()
        svc.list_suppliers()
        call_args = svc.list.call_args[0][0]
        assert call_args.filters.get("vendor_type") == "MATERIAL"

    def test_list_suppliers_empty_result(self):
        """空结果时返回 0 total 和空 items"""
        svc = self._make_service_with_list_result(items=[], total=0)
        result = svc.list_suppliers()
        assert result["total"] == 0
        assert result["items"] == []
        assert result["pages"] == 0
