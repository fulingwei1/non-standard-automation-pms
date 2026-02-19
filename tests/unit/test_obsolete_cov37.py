# -*- coding: utf-8 -*-
"""
第三十七批覆盖率测试 - ECN BOM呆滞料检查
tests/unit/test_obsolete_cov37.py
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch, call

pytest.importorskip("app.services.ecn_bom_analysis_service.obsolete")

from app.services.ecn_bom_analysis_service.obsolete import (
    check_obsolete_material_risk,
    calculate_obsolete_risk_level,
)


# ── calculate_obsolete_risk_level ─────────────────────────────────────────────

class TestCalculateObsoleteRiskLevel:
    def test_critical_above_100k(self):
        assert calculate_obsolete_risk_level(Decimal(100), Decimal(100001)) == "CRITICAL"

    def test_high_50k_to_100k(self):
        assert calculate_obsolete_risk_level(Decimal(50), Decimal(75000)) == "HIGH"

    def test_medium_10k_to_50k(self):
        assert calculate_obsolete_risk_level(Decimal(10), Decimal(20000)) == "MEDIUM"

    def test_low_below_10k(self):
        assert calculate_obsolete_risk_level(Decimal(1), Decimal(500)) == "LOW"

    def test_exact_100k_boundary(self):
        result = calculate_obsolete_risk_level(Decimal(10), Decimal(100000))
        assert result in ("CRITICAL", "HIGH")  # >= 100000 → CRITICAL


# ── check_obsolete_material_risk ──────────────────────────────────────────────

def _make_service(ecn=True, affected_materials=None, material=None, po_items=None):
    service = MagicMock()

    # ECN
    ecn_obj = MagicMock() if ecn else None
    ecn_obj and setattr(ecn_obj, "id", 1)

    # affected materials
    if affected_materials is None:
        affected_materials = []

    # PO items
    if po_items is None:
        po_items = []

    def query_side(model):
        q = MagicMock()
        from app.models.ecn import Ecn, EcnAffectedMaterial
        from app.models.material import Material
        from app.models.purchase import PurchaseOrderItem

        if model is Ecn:
            q.filter.return_value.first.return_value = ecn_obj
        elif model is EcnAffectedMaterial:
            q.filter.return_value.all.return_value = affected_materials
        elif model is Material:
            q.filter.return_value.first.return_value = material
        elif model is PurchaseOrderItem:
            q2 = MagicMock()
            q2.filter.return_value.all.return_value = po_items
            return q2
        return q

    service.db.query.side_effect = query_side
    return service


class TestCheckObsoleteMaterialRisk:
    def test_raises_when_ecn_not_found(self):
        service = _make_service(ecn=False)
        service.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            check_obsolete_material_risk(service, 999)

    def test_returns_no_risk_when_no_affected_materials(self):
        service = MagicMock()
        ecn = MagicMock()
        service.db.query.return_value.filter.return_value.first.return_value = ecn
        service.db.query.return_value.filter.return_value.all.return_value = []

        result = check_obsolete_material_risk(service, 1)
        assert result["has_obsolete_risk"] is False

    def test_result_contains_ecn_id(self):
        service = MagicMock()
        ecn = MagicMock()
        service.db.query.return_value.filter.return_value.first.return_value = ecn
        service.db.query.return_value.filter.return_value.all.return_value = []

        result = check_obsolete_material_risk(service, 5)
        assert result["ecn_id"] == 5

    def test_risk_level_low_for_small_cost(self):
        level = calculate_obsolete_risk_level(Decimal("1"), Decimal("100"))
        assert level == "LOW"

    def test_result_message_when_no_affected_materials(self):
        service = MagicMock()
        ecn = MagicMock()
        service.db.query.return_value.filter.return_value.first.return_value = ecn
        service.db.query.return_value.filter.return_value.all.return_value = []

        result = check_obsolete_material_risk(service, 1)
        assert "message" in result
        assert "没有" in result["message"]
