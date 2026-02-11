# -*- coding: utf-8 -*-
"""Tests for urgent_purchase_from_shortage_service"""
import json
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from decimal import Decimal

from app.services.urgent_purchase_from_shortage_service import (
    get_material_supplier,
    get_material_price,
    create_urgent_purchase_request_from_alert,
)


class TestGetMaterialSupplier:
    def setup_method(self):
        self.db = MagicMock()

    def test_preferred_supplier_found(self):
        preferred = MagicMock(supplier_id=10)
        self.db.query.return_value.filter.return_value.first.return_value = preferred
        assert get_material_supplier(self.db, 1) == 10

    def test_default_supplier_fallback(self):
        # First query (preferred) returns None
        query_mock = MagicMock()
        query_mock.filter.return_value.first.side_effect = [None, MagicMock(default_supplier_id=20), None]
        self.db.query.return_value = query_mock
        # We need more precise mocking
        self.db.reset_mock()

        call_count = [0]
        def side_effect_first(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return None  # no preferred
            elif call_count[0] == 2:
                return MagicMock(default_supplier_id=20)  # material with default
            else:
                return None
        self.db.query.return_value.filter.return_value.first.side_effect = side_effect_first
        result = get_material_supplier(self.db, 1)
        assert result == 20

    def test_no_supplier_returns_none(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = get_material_supplier(self.db, 1)
        assert result is None


class TestGetMaterialPrice:
    def setup_method(self):
        self.db = MagicMock()

    def test_supplier_price(self):
        ms = MagicMock(price=Decimal("100.50"))
        self.db.query.return_value.filter.return_value.first.return_value = ms
        result = get_material_price(self.db, 1, supplier_id=5)
        assert result == Decimal("100.50")

    def test_material_last_price(self):
        # No supplier price
        self.db.query.return_value.filter.return_value.first.side_effect = [
            None,  # no supplier price
            MagicMock(last_price=Decimal("50"), standard_price=Decimal("30")),  # material
        ]
        result = get_material_price(self.db, 1, supplier_id=5)
        assert result == Decimal("50")

    def test_no_price_returns_zero(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = get_material_price(self.db, 1)
        assert result == Decimal(0)


class TestCreateUrgentPurchaseRequestFromAlert:
    def setup_method(self):
        self.db = MagicMock()
        self.alert = MagicMock()
        self.alert.alert_no = "ALT-001"
        self.alert.alert_data = json.dumps({
            "shortage_qty": 10,
            "required_date": "2025-01-01",
            "material_code": "MAT-001",
            "material_name": "测试物料",
        })
        self.alert.target_id = 1
        self.alert.target_no = "MAT-001"
        self.alert.target_name = "测试物料"
        self.alert.project_id = 1
        self.alert.alert_level = "CRITICAL"
        self.alert.id = 100
        self.gen_func = MagicMock(return_value="PR-001")

    @patch("app.services.urgent_purchase_from_shortage_service.get_material_supplier", return_value=None)
    def test_no_supplier_sets_pending(self, mock_supplier):
        material = MagicMock(unit="个")
        self.db.query.return_value.filter.return_value.first.return_value = material
        result = create_urgent_purchase_request_from_alert(self.db, self.alert, 1, self.gen_func)
        assert result is None
        assert self.alert.status == "PENDING"

    def test_no_material_id_returns_none(self):
        self.alert.target_id = None
        result = create_urgent_purchase_request_from_alert(self.db, self.alert, 1, self.gen_func)
        assert result is None

    @patch("app.services.urgent_purchase_from_shortage_service.get_material_price", return_value=Decimal("10"))
    @patch("app.services.urgent_purchase_from_shortage_service.get_material_supplier", return_value=5)
    def test_successful_creation(self, mock_supplier, mock_price):
        material = MagicMock(unit="个")
        self.db.query.return_value.filter.return_value.first.return_value = material
        result = create_urgent_purchase_request_from_alert(self.db, self.alert, 1, self.gen_func)
        assert self.db.add.called
        assert self.db.commit.called

    def test_exception_rolls_back(self):
        self.db.query.side_effect = Exception("DB error")
        result = create_urgent_purchase_request_from_alert(self.db, self.alert, 1, self.gen_func)
        assert result is None
        self.db.rollback.assert_called_once()
