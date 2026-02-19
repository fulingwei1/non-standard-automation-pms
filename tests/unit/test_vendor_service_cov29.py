# -*- coding: utf-8 -*-
"""第二十九批 - vendor_service.py 单元测试（VendorService）"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.vendor_service")

from app.services.vendor_service import VendorService


# ─── 辅助工厂 ────────────────────────────────────────────────

def _make_db():
    return MagicMock()


def _make_vendor(**kwargs):
    v = MagicMock()
    v.id = kwargs.get("id", 1)
    v.supplier_code = kwargs.get("supplier_code", "SUP-001")
    v.supplier_name = kwargs.get("supplier_name", "测试供应商")
    v.supplier_short_name = kwargs.get("supplier_short_name", "测试")
    v.supplier_type = kwargs.get("supplier_type", "MATERIAL")
    v.contact_person = kwargs.get("contact_person", "张三")
    v.contact_phone = kwargs.get("contact_phone", "13800138000")
    v.contact_email = kwargs.get("contact_email", "test@example.com")
    v.address = kwargs.get("address", "测试地址")
    v.quality_rating = kwargs.get("quality_rating", Decimal("4.5"))
    v.delivery_rating = kwargs.get("delivery_rating", Decimal("4.0"))
    v.service_rating = kwargs.get("service_rating", Decimal("4.2"))
    v.overall_rating = kwargs.get("overall_rating", Decimal("4.3"))
    v.supplier_level = kwargs.get("supplier_level", "A")
    v.status = kwargs.get("status", "ACTIVE")
    v.cooperation_start = kwargs.get("cooperation_start", None)
    v.last_order_date = kwargs.get("last_order_date", None)
    v.created_at = kwargs.get("created_at", None)
    v.updated_at = kwargs.get("updated_at", None)
    return v


# ─── 测试：初始化 ────────────────────────────────────────────────

class TestVendorServiceInit:
    """测试 VendorService 初始化"""

    @patch("app.services.vendor_service.BaseService.__init__", return_value=None)
    def test_init_sets_model(self, mock_super_init):
        db = _make_db()
        svc = VendorService(db)
        mock_super_init.assert_called_once()


# ─── 测试：_to_response ────────────────────────────────────────────────────────

class TestVendorServiceToResponse:
    """测试 _to_response 方法"""

    @patch("app.services.vendor_service.BaseService.__init__", return_value=None)
    def test_converts_vendor_to_response(self, mock_super_init):
        db = _make_db()
        svc = VendorService(db)
        svc.db = db
        vendor = _make_vendor(supplier_name="精品供应商")
        result = svc._to_response(vendor)
        assert result.supplier_name == "精品供应商"
        assert result.supplier_code == "SUP-001"

    @patch("app.services.vendor_service.BaseService.__init__", return_value=None)
    def test_defaults_ratings_to_zero_when_none(self, mock_super_init):
        db = _make_db()
        svc = VendorService(db)
        vendor = _make_vendor(
            quality_rating=None,
            delivery_rating=None,
            service_rating=None,
            overall_rating=None,
        )
        result = svc._to_response(vendor)
        assert result.quality_rating == Decimal("0")
        assert result.delivery_rating == Decimal("0")
        assert result.service_rating == Decimal("0")
        assert result.overall_rating == Decimal("0")

    @patch("app.services.vendor_service.BaseService.__init__", return_value=None)
    def test_defaults_supplier_level_to_B_when_none(self, mock_super_init):
        db = _make_db()
        svc = VendorService(db)
        vendor = _make_vendor(supplier_level=None)
        result = svc._to_response(vendor)
        assert result.supplier_level == "B"

    @patch("app.services.vendor_service.BaseService.__init__", return_value=None)
    def test_defaults_status_to_active_when_none(self, mock_super_init):
        db = _make_db()
        svc = VendorService(db)
        vendor = _make_vendor(status=None)
        result = svc._to_response(vendor)
        assert result.status == "ACTIVE"


# ─── 测试：list_suppliers ────────────────────────────────────────────────────

class TestListSuppliers:
    """测试 list_suppliers 方法"""

    @patch("app.services.vendor_service.BaseService.__init__", return_value=None)
    def test_list_suppliers_default_params(self, mock_super_init):
        db = _make_db()
        svc = VendorService(db)
        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20
        svc.list = MagicMock(return_value=mock_result)

        result = svc.list_suppliers()

        svc.list.assert_called_once()
        assert result["total"] == 0
        assert result["page"] == 1
        assert result["page_size"] == 20

    @patch("app.services.vendor_service.BaseService.__init__", return_value=None)
    def test_list_suppliers_calculates_pages(self, mock_super_init):
        db = _make_db()
        svc = VendorService(db)
        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 55
        mock_result.page = 1
        mock_result.page_size = 20
        svc.list = MagicMock(return_value=mock_result)

        result = svc.list_suppliers(page=1, page_size=20)

        assert result["pages"] == 3  # ceil(55/20) = 3

    @patch("app.services.vendor_service.BaseService.__init__", return_value=None)
    def test_list_suppliers_with_filters(self, mock_super_init):
        db = _make_db()
        svc = VendorService(db)
        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 5
        mock_result.page = 1
        mock_result.page_size = 10
        svc.list = MagicMock(return_value=mock_result)

        result = svc.list_suppliers(
            keyword="精品",
            supplier_type="MATERIAL",
            status="ACTIVE",
            supplier_level="A",
        )

        call_args = svc.list.call_args[0][0]
        assert call_args.filters.get("status") == "ACTIVE"
        assert call_args.filters.get("supplier_type") == "MATERIAL"
        assert call_args.filters.get("supplier_level") == "A"
        assert call_args.search == "精品"

    @patch("app.services.vendor_service.BaseService.__init__", return_value=None)
    def test_list_suppliers_vendor_type_in_filters(self, mock_super_init):
        db = _make_db()
        svc = VendorService(db)
        mock_result = MagicMock()
        mock_result.items = []
        mock_result.total = 0
        mock_result.page = 1
        mock_result.page_size = 20
        svc.list = MagicMock(return_value=mock_result)

        svc.list_suppliers(vendor_type="SERVICE")

        call_args = svc.list.call_args[0][0]
        assert call_args.filters.get("vendor_type") == "SERVICE"
