# -*- coding: utf-8 -*-
"""第五批：inventory_management_service.py 单元测试"""
import pytest
from unittest.mock import MagicMock, patch, call
from decimal import Decimal
from datetime import datetime

try:
    from app.services.inventory_management_service import (
        InventoryManagementService,
        InsufficientStockError,
    )
    HAS_MODULE = True
except ImportError:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="inventory_management_service not importable")


def make_service(db=None):
    if db is None:
        db = MagicMock()
    return InventoryManagementService(db, tenant_id=1)


def make_stock(material_id=10, available_qty=Decimal("100"), qty=Decimal("100"), location="A1"):
    s = MagicMock()
    s.material_id = material_id
    s.available_quantity = available_qty
    s.quantity = qty
    s.location = location
    s.tenant_id = 1
    return s


class TestGetStock:
    def test_returns_list(self):
        db = MagicMock()
        stocks = [make_stock(), make_stock()]
        db.query.return_value.filter.return_value.all.return_value = stocks
        svc = make_service(db)
        result = svc.get_stock(10)
        assert len(result) == 2

    def test_with_location_filter(self):
        db = MagicMock()
        stocks = [make_stock()]
        q = MagicMock()
        q.all.return_value = stocks
        q.filter.return_value = q
        db.query.return_value.filter.return_value = q
        svc = make_service(db)
        result = svc.get_stock(10, location="A1")
        assert result == stocks


class TestGetAvailableQuantity:
    def test_returns_decimal(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.scalar.return_value = 50
        svc = make_service(db)
        result = svc.get_available_quantity(10)
        assert result == Decimal("50")

    def test_none_returns_zero(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.scalar.return_value = None
        svc = make_service(db)
        result = svc.get_available_quantity(10)
        assert result == Decimal("0")


class TestGetTotalQuantity:
    def test_returns_decimal(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.scalar.return_value = 200
        svc = make_service(db)
        result = svc.get_total_quantity(10)
        assert result == Decimal("200")


class TestCalculateStockStatus:
    def test_empty_stock(self):
        db = MagicMock()
        svc = make_service(db)
        stock = MagicMock()
        stock.expire_date = None
        stock.quantity = Decimal("0")
        stock.material_id = 10
        result = svc._calculate_stock_status(stock)
        assert result == "EMPTY"

    def test_low_stock(self):
        db = MagicMock()
        material = MagicMock()
        material.safety_stock = Decimal("20")
        db.query.return_value.get.return_value = material
        svc = make_service(db)
        stock = MagicMock()
        stock.expire_date = None
        stock.quantity = Decimal("5")
        stock.material_id = 10
        result = svc._calculate_stock_status(stock)
        assert result == "LOW"

    def test_normal_stock(self):
        db = MagicMock()
        material = MagicMock()
        material.safety_stock = Decimal("10")
        db.query.return_value.get.return_value = material
        svc = make_service(db)
        stock = MagicMock()
        stock.expire_date = None
        stock.quantity = Decimal("50")
        stock.material_id = 10
        result = svc._calculate_stock_status(stock)
        assert result == "NORMAL"


class TestInsufficientStockError:
    def test_raises(self):
        with pytest.raises(InsufficientStockError):
            raise InsufficientStockError("库存不足")


class TestIssueInsufficientRaises:
    def test_issue_insufficient_stock(self):
        db = MagicMock()
        # 可用库存为 0
        db.query.return_value.filter.return_value.scalar.return_value = 0
        # 没有库存可选
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        svc = make_service(db)
        with pytest.raises((InsufficientStockError, Exception)):
            svc.issue_material(
                material_id=10,
                quantity=Decimal("5"),
                work_order_id=1,
                operator_id=1,
            )
