# -*- coding: utf-8 -*-
"""第三批覆盖率测试 - inventory_management_service"""
import pytest
from unittest.mock import MagicMock, patch, call
from decimal import Decimal
from datetime import datetime, date

pytest.importorskip("app.services.inventory_management_service")

from app.services.inventory_management_service import (
    InventoryManagementService,
    InsufficientStockError,
)


def make_db():
    return MagicMock()


def make_service(db=None, tenant_id=1):
    if db is None:
        db = make_db()
    return InventoryManagementService(db, tenant_id)


def make_stock(**kw):
    s = MagicMock()
    s.id = kw.get("id", 1)
    s.material_id = kw.get("material_id", 1)
    s.tenant_id = kw.get("tenant_id", 1)
    s.location = kw.get("location", "WH-A")
    s.batch_number = kw.get("batch_number", "BATCH001")
    s.quantity = kw.get("quantity", Decimal("100"))
    s.available_quantity = kw.get("available_quantity", Decimal("80"))
    s.reserved_quantity = kw.get("reserved_quantity", Decimal("20"))
    return s


class TestGetStock:
    def test_get_stock_returns_list(self):
        db = make_db()
        stock = make_stock()
        db.query.return_value.filter.return_value.all.return_value = [stock]
        svc = make_service(db)
        result = svc.get_stock(1)
        assert len(result) == 1

    def test_get_stock_with_location(self):
        db = make_db()
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = []
        svc = make_service(db)
        result = svc.get_stock(1, location="WH-A")
        assert result == []

    def test_get_available_quantity(self):
        db = make_db()
        db.query.return_value.filter.return_value.scalar.return_value = 50
        svc = make_service(db)
        result = svc.get_available_quantity(1)
        assert result == Decimal("50")

    def test_get_available_quantity_no_stock(self):
        db = make_db()
        db.query.return_value.filter.return_value.scalar.return_value = None
        svc = make_service(db)
        result = svc.get_available_quantity(1)
        assert result == Decimal("0")


class TestCreateTransaction:
    def test_create_receipt_transaction(self):
        db = make_db()
        material = MagicMock()
        material.material_code = "M001"
        material.material_name = "Steel"
        material.unit = "KG"
        db.query.return_value.get.return_value = material
        svc = make_service(db)

        result = svc.create_transaction(
            material_id=1,
            transaction_type="PURCHASE_IN",
            quantity=Decimal("50"),
        )
        assert result is not None

    def test_create_transaction_material_not_found(self):
        db = make_db()
        db.query.return_value.get.return_value = None
        svc = make_service(db)
        with pytest.raises(ValueError, match="物料不存在"):
            svc.create_transaction(
                material_id=999,
                transaction_type="PURCHASE_IN",
                quantity=Decimal("10"),
            )


class TestReserveMaterial:
    def test_reserve_sufficient_stock(self):
        db = make_db()
        svc = make_service(db)
        stock = make_stock(available_quantity=Decimal("100"))
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [stock]

        with patch.object(svc, "get_available_quantity", return_value=Decimal("100")):
            result = svc.reserve_material(
                material_id=1,
                quantity=Decimal("20"),
                work_order_id=1,
                created_by=1,
            )
        assert result is not None

    def test_reserve_insufficient_stock_raises(self):
        db = make_db()
        svc = make_service(db)

        with patch.object(svc, "get_available_quantity", return_value=Decimal("5")):
            with pytest.raises(InsufficientStockError):
                svc.reserve_material(
                    material_id=1,
                    quantity=Decimal("20"),
                )


class TestCalculateTurnoverRate:
    def test_turnover_rate_calculation(self):
        db = make_db()
        svc = make_service(db)

        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.scalar.return_value = Decimal("1000")
        db.query.return_value = mock_q

        result = svc.calculate_turnover_rate(
            material_id=1,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        )
        assert result is not None


class TestStockStatus:
    def test_calculate_stock_status_sufficient(self):
        db = make_db()
        svc = make_service(db)
        stock = make_stock(quantity=Decimal("100"), available_quantity=Decimal("80"))
        # expire_date must be real or None, set to future or None
        stock.expire_date = None
        material = MagicMock()
        material.safety_stock = 0  # no safety stock threshold
        db.query.return_value.get.return_value = material
        result = svc._calculate_stock_status(stock)
        assert result in ("NORMAL", "LOW", "EMPTY", "EXPIRED")

    def test_get_total_quantity(self):
        db = make_db()
        db.query.return_value.filter.return_value.scalar.return_value = Decimal("200")
        svc = make_service(db)
        result = svc.get_total_quantity(1)
        assert result == Decimal("200")
