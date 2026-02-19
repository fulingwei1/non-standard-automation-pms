# -*- coding: utf-8 -*-
"""
Unit tests for app/services/ecn_bom_analysis_service/analysis.py (cov52)
"""
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch

try:
    from app.services.ecn_bom_analysis_service.analysis import (
        analyze_bom_impact,
        analyze_single_bom,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_service():
    service = MagicMock()
    service.db = MagicMock()
    return service


# ──────────────────────── analyze_bom_impact ────────────────────────

def test_analyze_bom_impact_ecn_not_found():
    """ECN 不存在时抛出 ValueError"""
    service = _make_service()
    service.db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="不存在"):
        analyze_bom_impact(service, ecn_id=999)


def test_analyze_bom_impact_no_machine_id():
    """ECN 无 machine_id 且参数未提供时抛出 ValueError"""
    service = _make_service()
    ecn = MagicMock(id=1, machine_id=None, project_id=10)
    service.db.query.return_value.filter.return_value.first.return_value = ecn

    with pytest.raises(ValueError, match="设备ID"):
        analyze_bom_impact(service, ecn_id=1)


def test_analyze_bom_impact_no_affected_materials():
    """无受影响物料时返回 has_impact=False"""
    service = _make_service()
    ecn = MagicMock(id=1, machine_id=5, project_id=10)
    service.db.query.return_value.filter.return_value.first.return_value = ecn
    # affected_materials query → []
    service.db.query.return_value.filter.return_value.all.return_value = []

    result = analyze_bom_impact(service, ecn_id=1)

    assert result["has_impact"] is False
    assert "没有受影响的物料" in result["message"]


def test_analyze_bom_impact_machine_not_found():
    """设备不存在时抛出 ValueError"""
    service = _make_service()
    ecn = MagicMock(id=1, machine_id=5, project_id=10)

    affected_mat = MagicMock()
    service.db.query.return_value.filter.return_value.all.return_value = [affected_mat]
    # Machine query → None
    service.db.query.return_value.filter.return_value.first.side_effect = [ecn, None]

    with pytest.raises(ValueError, match="设备"):
        analyze_bom_impact(service, ecn_id=1)


def test_analyze_bom_impact_no_bom_headers():
    """设备没有已发布的 BOM 时返回 has_impact=False"""
    service = _make_service()
    ecn = MagicMock(id=1, machine_id=5, project_id=10)
    machine = MagicMock(id=5)
    affected_mat = MagicMock()

    service.db.query.return_value.filter.return_value.first.side_effect = [ecn, machine]
    service.db.query.return_value.filter.return_value.all.side_effect = [
        [affected_mat],   # affected_materials
        [],               # bom_headers
    ]

    result = analyze_bom_impact(service, ecn_id=1)

    assert result["has_impact"] is False


# ──────────────────────── analyze_single_bom ────────────────────────

@patch("app.services.ecn_bom_analysis_service.analysis.analyze_cascade_impact", return_value=[])
@patch("app.services.ecn_bom_analysis_service.analysis.calculate_cost_impact", return_value=Decimal("0"))
@patch("app.services.ecn_bom_analysis_service.analysis.calculate_schedule_impact", return_value=0)
@patch("app.services.ecn_bom_analysis_service.analysis.get_impact_description", return_value="修改")
def test_analyze_single_bom_no_match(mock_desc, mock_sched, mock_cost, mock_cascade):
    """BOM 无匹配物料时 has_impact=False"""
    service = _make_service()
    service.db.query.return_value.filter.return_value.all.return_value = []

    bom_header = MagicMock(id=1, bom_no="BOM-001", bom_name="测试BOM")
    affected_mat = MagicMock(material_code="MAT-999", material_id=None)
    affected_mat.material_code = "MAT-999"
    affected_mat.material_id = None

    result = analyze_single_bom(service, ecn_id=1, bom_header=bom_header,
                                affected_materials=[affected_mat], include_cascade=True)

    assert result["has_impact"] is False
    assert result["bom_id"] == 1
