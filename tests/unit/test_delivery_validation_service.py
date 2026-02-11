# -*- coding: utf-8 -*-
"""Tests for delivery_validation_service.py"""
from unittest.mock import MagicMock, patch
from datetime import date

from app.services.delivery_validation_service import DeliveryValidationService


class TestGetMaterialLeadTime:
    def setup_method(self):
        self.db = MagicMock()

    def test_by_material_id(self):
        mat = MagicMock(lead_time_days=21, material_name="物料A")
        self.db.query.return_value.filter.return_value.first.return_value = mat
        days, remark = DeliveryValidationService.get_material_lead_time(self.db, material_id=1)
        assert days == 21

    def test_by_material_code(self):
        mat = MagicMock(lead_time_days=10, material_name="物料B")
        self.db.query.return_value.filter.return_value.first.return_value = mat
        days, _ = DeliveryValidationService.get_material_lead_time(self.db, material_code="M001")
        assert days == 10

    def test_by_material_type_default(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        days, _ = DeliveryValidationService.get_material_lead_time(self.db, material_type="标准件")
        assert days == 7

    def test_fallback_default(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        days, remark = DeliveryValidationService.get_material_lead_time(self.db)
        assert days == 14
        assert "默认值" in remark


class TestEstimateProjectCycle:
    def test_simple_project(self):
        db = MagicMock()
        result = DeliveryValidationService.estimate_project_cycle(db, complexity_level="SIMPLE")
        assert result['estimated_total_days'] == 45
        assert len(result['stage_details']) == 8

    def test_complex_with_amount(self):
        db = MagicMock()
        result = DeliveryValidationService.estimate_project_cycle(
            db, contract_amount=6000000, complexity_level="COMPLEX"
        )
        assert result['estimated_total_days'] > 105  # 105 * 1.2

    def test_with_project_type(self):
        db = MagicMock()
        result = DeliveryValidationService.estimate_project_cycle(
            db, project_type="线体类", complexity_level="MEDIUM"
        )
        assert result['estimated_total_days'] > 75  # 75 * 1.3


class TestValidateDeliveryDate:
    def setup_method(self):
        self.db = MagicMock()

    def test_no_lead_time_error(self):
        quote = MagicMock(opportunity=None)
        version = MagicMock(lead_time_days=0, total_price=100000)
        items = []
        result = DeliveryValidationService.validate_delivery_date(self.db, quote, version, items)
        assert result['status'] == 'ERROR'

    def test_valid_lead_time(self):
        quote = MagicMock(opportunity=None)
        version = MagicMock(lead_time_days=90, total_price=100000)
        items = []
        result = DeliveryValidationService.validate_delivery_date(self.db, quote, version, items)
        assert result['quoted_lead_time'] == 90


class TestGetSuggestions:
    def test_short_quoted(self):
        suggestions = DeliveryValidationService._get_suggestions(10, 30, 60)
        assert any("37" in s for s in suggestions)

    def test_no_quoted(self):
        suggestions = DeliveryValidationService._get_suggestions(None, 20, 60)
        assert len(suggestions) > 0
