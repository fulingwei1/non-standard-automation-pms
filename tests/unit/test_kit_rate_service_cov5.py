# -*- coding: utf-8 -*-
"""第五批：kit_rate/kit_rate_service.py 单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal

try:
    from app.services.kit_rate.kit_rate_service import KitRateService
    from fastapi import HTTPException
    HAS_MODULE = True
except ImportError:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="kit_rate_service not importable")


def make_service(db=None):
    if db is None:
        db = MagicMock()
    return KitRateService(db)


def make_bom_item(required_qty, available_stock, unit_price=Decimal("10")):
    item = MagicMock()
    item.quantity = Decimal(str(required_qty))
    item.unit_price = unit_price
    item.received_qty = Decimal("0")
    item.material_id = 1
    material = MagicMock()
    material.current_stock = Decimal(str(available_stock))
    item.material = material
    return item


class TestCalculateKitRateEmpty:
    def test_empty_list(self):
        svc = make_service()
        result = svc.calculate_kit_rate([], "quantity")
        assert result["total_items"] == 0
        assert result["kit_rate"] == 0.0
        assert result["kit_status"] == "complete"


class TestCalculateKitRateInvalidBy:
    def test_invalid_calculate_by(self):
        svc = make_service()
        with pytest.raises(HTTPException) as exc_info:
            svc.calculate_kit_rate([], "invalid")
        assert exc_info.value.status_code == 400


class TestCalculateKitRateByQuantity:
    def test_all_fulfilled(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = make_service(db)
        items = [make_bom_item(10, 20), make_bom_item(5, 10)]
        result = svc.calculate_kit_rate(items, "quantity")
        assert result["kit_status"] == "complete"
        assert result["fulfilled_items"] == 2
        assert result["shortage_items"] == 0

    def test_partial_fulfilled(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = make_service(db)
        # 第一个有库存，第二个缺货（available=0, no in-transit）
        item1 = make_bom_item(10, 10)
        item2 = make_bom_item(5, 0)
        result = svc.calculate_kit_rate([item1, item2], "quantity")
        assert result["shortage_items"] == 1 or result["kit_status"] in ("partial", "shortage")

    def test_all_shortage(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = make_service(db)
        items = [make_bom_item(10, 0), make_bom_item(5, 0)]
        result = svc.calculate_kit_rate(items, "quantity")
        assert result["kit_status"] == "shortage"
        assert result["fulfilled_items"] == 0


class TestCalculateKitRateByAmount:
    def test_fulfilled_by_amount(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = make_service(db)
        items = [make_bom_item(10, 10, unit_price=Decimal("100"))]
        result = svc.calculate_kit_rate(items, "amount")
        assert result["kit_rate"] == 100.0
        assert result["kit_status"] == "complete"


class TestListBomItemsForMachine:
    def test_no_bom_returns_empty(self):
        db = MagicMock()
        from app.utils.db_helpers import get_or_404
        machine = MagicMock()
        with patch("app.services.kit_rate.kit_rate_service.get_or_404", return_value=machine):
            # _get_latest_bom returns None
            db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
            svc = make_service(db)
            result = svc.list_bom_items_for_machine(1)
            assert result == []


class TestKitRateStatus:
    def test_complete_status(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = make_service(db)
        items = [make_bom_item(1, 5)]
        result = svc.calculate_kit_rate(items, "quantity")
        assert result["kit_rate"] == 100.0
        assert result["kit_status"] == "complete"

    def test_partial_status(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        svc = make_service(db)
        # 9个满足，1个缺货 → 90%
        items = [make_bom_item(1, 1)] * 9 + [make_bom_item(1, 0)]
        result = svc.calculate_kit_rate(items, "quantity")
        assert result["kit_status"] == "partial"
