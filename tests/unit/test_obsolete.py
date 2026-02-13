# -*- coding: utf-8 -*-
"""obsolete material risk 单元测试"""
from decimal import Decimal
from unittest.mock import MagicMock
import pytest

from app.services.ecn_bom_analysis_service.obsolete import (
    check_obsolete_material_risk,
    calculate_obsolete_risk_level,
)


class TestCalculateObsoleteRiskLevel:
    def test_critical(self):
        assert calculate_obsolete_risk_level(Decimal(100), Decimal(200000)) == "CRITICAL"

    def test_high(self):
        assert calculate_obsolete_risk_level(Decimal(100), Decimal(60000)) == "HIGH"

    def test_medium(self):
        assert calculate_obsolete_risk_level(Decimal(100), Decimal(20000)) == "MEDIUM"

    def test_low(self):
        assert calculate_obsolete_risk_level(Decimal(100), Decimal(5000)) == "LOW"


class TestCheckObsoleteMaterialRisk:
    def test_ecn_not_found(self):
        service = MagicMock()
        service.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError):
            check_obsolete_material_risk(service, 999)

    def test_no_affected_materials(self):
        service = MagicMock()
        ecn = MagicMock()
        service.db.query.return_value.filter.return_value.first.return_value = ecn
        service.db.query.return_value.filter.return_value.all.return_value = []
        result = check_obsolete_material_risk(service, 1)
        assert result["has_obsolete_risk"] is False

    def test_with_affected_materials(self):
        service = MagicMock()
        ecn = MagicMock()

        mat_affected = MagicMock()
        mat_affected.material_id = 10
        mat_affected.change_type = "DELETE"

        material = MagicMock()
        material.id = 10
        material.material_code = "MAT001"
        material.material_name = "Test Material"
        material.current_stock = 100
        material.last_price = 500
        material.standard_price = 500

        # Setup query chain
        service.db.query.return_value.filter.return_value.first.side_effect = [ecn, material]
        service.db.query.return_value.filter.return_value.all.side_effect = [[mat_affected], []]  # affected_materials, po_items

        # Need to handle the join query for PO items
        service.db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        result = check_obsolete_material_risk(service, 1)
        assert result["ecn_id"] == 1
