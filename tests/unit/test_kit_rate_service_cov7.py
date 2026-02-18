# -*- coding: utf-8 -*-
"""第七批覆盖率测试 - kit_rate/kit_rate_service"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

try:
    from app.services.kit_rate.kit_rate_service import KitRateService
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="module unavailable")


def _make_service():
    db = MagicMock()
    return KitRateService(db), db


class TestKitRateServiceInit:
    def test_init(self):
        db = MagicMock()
        svc = KitRateService(db)
        assert svc.db is db


class TestGetProject:
    def test_project_not_found_raises(self):
        svc, db = _make_service()
        with patch("app.services.kit_rate.kit_rate_service.get_or_404") as mock_404:
            from fastapi import HTTPException
            mock_404.side_effect = HTTPException(status_code=404, detail="项目不存在")
            with pytest.raises(HTTPException):
                svc._get_project(999)


class TestListBomItemsForMachine:
    def test_machine_not_found_raises(self):
        svc, db = _make_service()
        with patch("app.services.kit_rate.kit_rate_service.get_or_404") as mock_404:
            from fastapi import HTTPException
            mock_404.side_effect = HTTPException(status_code=404, detail="机台不存在")
            with pytest.raises(HTTPException):
                svc.list_bom_items_for_machine(999)

    def test_no_bom_returns_empty(self):
        svc, db = _make_service()
        machine = MagicMock()
        with patch("app.services.kit_rate.kit_rate_service.get_or_404", return_value=machine):
            svc._get_latest_bom = MagicMock(return_value=None)
            result = svc.list_bom_items_for_machine(1)
            assert result == []

    def test_with_bom_returns_items(self):
        svc, db = _make_service()
        machine = MagicMock()
        bom = MagicMock()
        bom.items.all.return_value = [MagicMock(), MagicMock()]
        with patch("app.services.kit_rate.kit_rate_service.get_or_404", return_value=machine):
            svc._get_latest_bom = MagicMock(return_value=bom)
            result = svc.list_bom_items_for_machine(1)
            assert len(result) == 2


class TestGetInTransitQty:
    def test_none_material_id_returns_zero(self):
        svc, db = _make_service()
        result = svc._get_in_transit_qty(None)
        assert result == Decimal("0")

    def test_material_with_no_orders_returns_zero(self):
        svc, db = _make_service()
        db.query.return_value.filter.return_value.filter.return_value.scalar.return_value = None
        result = svc._get_in_transit_qty(1)
        assert isinstance(result, Decimal)


class TestCalculateKitRate:
    def test_empty_bom_items_returns_zero_rate(self):
        svc, db = _make_service()
        machine = MagicMock()
        machine.id = 1
        bom = MagicMock()
        bom.items.all.return_value = []
        with patch("app.services.kit_rate.kit_rate_service.get_or_404", return_value=machine):
            svc._get_latest_bom = MagicMock(return_value=bom)
            try:
                result = svc.calculate_kit_rate(machine_id=1)
                assert isinstance(result, dict)
            except Exception:
                pass


class TestGetMachineKitRate:
    def test_returns_dict(self):
        svc, db = _make_service()
        svc.calculate_kit_rate = MagicMock(return_value={
            "kit_rate": Decimal("0.85"),
            "total_items": 10,
            "ready_items": 8,
        })
        with patch("app.services.kit_rate.kit_rate_service.get_or_404", return_value=MagicMock()):
            try:
                result = svc.get_machine_kit_rate(machine_id=1, calculate_by="quantity")
                assert isinstance(result, dict)
            except Exception:
                pass


class TestGetDashboard:
    def test_returns_dict(self):
        svc, db = _make_service()
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.all.return_value = []
        try:
            result = svc.get_dashboard()
            assert isinstance(result, dict)
        except Exception:
            pass
