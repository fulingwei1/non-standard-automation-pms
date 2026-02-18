# -*- coding: utf-8 -*-
"""第三批覆盖率测试 - kit_rate_service"""
import pytest
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date

pytest.importorskip("app.services.kit_rate.kit_rate_service")

from app.services.kit_rate.kit_rate_service import KitRateService


def make_db():
    return MagicMock()


def make_bom_item(
    material_id=1, required_qty=10, stock_qty=8, in_transit_qty=0,
    is_critical=False, unit_price=100
):
    item = MagicMock()
    item.material_id = material_id
    item.quantity = Decimal(str(required_qty))
    item.received_qty = Decimal("0")
    item.unit_price = Decimal(str(unit_price))
    item.material = MagicMock()
    item.material.current_stock = Decimal(str(stock_qty))
    item.material.material_name = "TestMaterial"
    item.material.material_code = "M001"
    item.is_critical = is_critical
    return item


class TestCalculateKitRate:
    def test_empty_bom_items(self):
        db = make_db()
        svc = KitRateService(db)
        result = svc.calculate_kit_rate([])
        assert result["kit_rate"] == 0.0
        assert result["total_items"] == 0

    def test_invalid_calculate_by(self):
        db = make_db()
        svc = KitRateService(db)
        with pytest.raises(Exception):
            svc.calculate_kit_rate([make_bom_item()], calculate_by="invalid")

    def test_all_fulfilled_by_quantity(self):
        db = make_db()
        svc = KitRateService(db)
        items = [make_bom_item(required_qty=5, stock_qty=10)]
        with patch.object(svc, "_get_in_transit_qty", return_value=Decimal("0")):
            result = svc.calculate_kit_rate(items, calculate_by="quantity")
        assert result["kit_rate"] == 100.0

    def test_partial_fulfilled_by_quantity(self):
        db = make_db()
        svc = KitRateService(db)
        items = [
            make_bom_item(material_id=1, required_qty=10, stock_qty=10),
            make_bom_item(material_id=2, required_qty=10, stock_qty=0),  # no stock at all = shortage
        ]
        with patch.object(svc, "_get_in_transit_qty", return_value=Decimal("0")):
            result = svc.calculate_kit_rate(items, calculate_by="quantity")
        assert result["fulfilled_items"] == 1
        assert result["shortage_items"] == 1


class TestGetMachineKitRate:
    def test_machine_not_found(self):
        db = make_db()
        svc = KitRateService(db)
        from fastapi import HTTPException
        with patch.object(svc, "_get_machine", side_effect=HTTPException(status_code=404, detail="机台不存在")):
            with pytest.raises(HTTPException):
                svc.get_machine_kit_rate(999, "quantity")

    def test_no_bom_raises(self):
        db = make_db()
        svc = KitRateService(db)
        from fastapi import HTTPException
        with patch.object(svc, "_get_machine", return_value=MagicMock(id=1, machine_code="M001")), \
             patch.object(svc, "_get_latest_bom", return_value=None):
            with pytest.raises(HTTPException):
                svc.get_machine_kit_rate(1, "quantity")

    def test_with_bom_items(self):
        db = make_db()
        svc = KitRateService(db)
        machine = MagicMock(id=1, machine_code="M001", machine_name="Machine 1")
        machine.machine_no = "M001"
        bom = MagicMock()
        bom.id = 1
        bom.bom_no = "B001"
        bom.bom_name = "BOM1"
        items = [make_bom_item(required_qty=5, stock_qty=5)]
        bom.items.all.return_value = items

        with patch.object(svc, "_get_machine", return_value=machine), \
             patch.object(svc, "_get_latest_bom", return_value=bom), \
             patch.object(svc, "calculate_kit_rate", return_value={"kit_rate": 100.0, "kit_status": "complete"}):
            result = svc.get_machine_kit_rate(1, "quantity")
        assert result["kit_rate"] == 100.0


class TestGetProjectKitRate:
    def test_project_not_found(self):
        db = make_db()
        svc = KitRateService(db)
        from fastapi import HTTPException
        with patch.object(svc, "_get_project", side_effect=HTTPException(status_code=404)):
            with pytest.raises(HTTPException):
                svc.get_project_kit_rate(999, "quantity")

    def test_no_machines(self):
        db = make_db()
        project = MagicMock(id=1, project_code="P001", project_name="Test")
        svc = KitRateService(db)
        with patch.object(svc, "_get_project", return_value=project):
            db.query.return_value.filter.return_value.all.return_value = []
            result = svc.get_project_kit_rate(1, "quantity")
        assert result["kit_rate"] == 0.0


class TestGetInTransitQty:
    def test_no_material_id_returns_zero(self):
        db = make_db()
        svc = KitRateService(db)
        result = svc._get_in_transit_qty(None)
        assert result == Decimal(0)

    def test_with_po_items(self):
        db = make_db()
        po_item = MagicMock()
        po_item.quantity = Decimal("10")
        po_item.received_qty = Decimal("4")
        db.query.return_value.filter.return_value.filter.return_value.all.return_value = [po_item]
        svc = KitRateService(db)
        result = svc._get_in_transit_qty(1)
        assert result == Decimal("6")
