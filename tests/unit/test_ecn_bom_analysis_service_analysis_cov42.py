# -*- coding: utf-8 -*-
"""第四十二批：ecn_bom_analysis_service/analysis.py 单元测试"""
import pytest

pytest.importorskip("app.services.ecn_bom_analysis_service.analysis")

from unittest.mock import MagicMock, patch
from app.services.ecn_bom_analysis_service.analysis import (
    analyze_bom_impact,
    analyze_single_bom,
)


def make_service():
    svc = MagicMock()
    return svc


# ------------------------------------------------------------------ tests ---

def test_analyze_bom_impact_ecn_not_found():
    svc = make_service()
    svc.db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError, match="不存在"):
        analyze_bom_impact(svc, ecn_id=999)


def test_analyze_bom_impact_no_machine_id_raises():
    svc = make_service()
    ecn = MagicMock()
    ecn.machine_id = None
    svc.db.query.return_value.filter.return_value.first.return_value = ecn
    svc.db.query.return_value.filter.return_value.all.return_value = [MagicMock()]
    with pytest.raises(ValueError, match="设备ID"):
        analyze_bom_impact(svc, ecn_id=1, machine_id=None)


def test_analyze_bom_impact_no_affected_materials():
    svc = make_service()
    ecn = MagicMock()
    ecn.machine_id = 10
    ecn.project_id = 20

    def query_side(*args):
        q = MagicMock()
        from app.models.ecn import Ecn, EcnAffectedMaterial
        if args and args[0] is Ecn:
            q.filter.return_value.first.return_value = ecn
        elif args and args[0] is EcnAffectedMaterial:
            q.filter.return_value.all.return_value = []
        return q

    svc.db.query.side_effect = query_side
    with patch("app.services.ecn_bom_analysis_service.analysis.Ecn"), \
         patch("app.services.ecn_bom_analysis_service.analysis.EcnAffectedMaterial"):
        # Simplified: mock entire chain
        svc.db.query.side_effect = None
        ecn_q = MagicMock()
        ecn_q.filter.return_value.first.return_value = ecn
        mat_q = MagicMock()
        mat_q.filter.return_value.all.return_value = []

        call_count = [0]
        def query_router(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                return ecn_q
            return mat_q

        svc.db.query.side_effect = query_router
        result = analyze_bom_impact(svc, ecn_id=1, machine_id=10)
    assert result["has_impact"] is False


def test_analyze_single_bom_no_affected_items():
    svc = make_service()
    bom = MagicMock()
    bom.id = 1
    bom.bom_no = "B001"
    bom.bom_name = "测试BOM"
    svc.db.query.return_value.filter.return_value.all.return_value = []

    with patch("app.services.ecn_bom_analysis_service.analysis.analyze_cascade_impact", return_value=[]), \
         patch("app.services.ecn_bom_analysis_service.analysis.calculate_cost_impact", return_value=0), \
         patch("app.services.ecn_bom_analysis_service.analysis.calculate_schedule_impact", return_value=0):
        result = analyze_single_bom(svc, ecn_id=1, bom_header=bom, affected_materials=[], include_cascade=False)

    assert result["has_impact"] is False
    assert result["bom_id"] == 1


def test_analyze_single_bom_with_matching_material():
    svc = make_service()
    bom = MagicMock()
    bom.id = 2
    bom.bom_no = "B002"
    bom.bom_name = "BOM2"

    bom_item = MagicMock()
    bom_item.id = 100
    bom_item.material_code = "M001"
    bom_item.material_id = None
    bom_item.material_name = "物料A"

    affected_mat = MagicMock()
    affected_mat.material_code = "M001"
    affected_mat.material_id = None
    affected_mat.change_type = "UPDATE"

    svc.db.query.return_value.filter.return_value.all.return_value = [bom_item]

    with patch("app.services.ecn_bom_analysis_service.analysis.analyze_cascade_impact", return_value=[]), \
         patch("app.services.ecn_bom_analysis_service.analysis.calculate_cost_impact", return_value=100), \
         patch("app.services.ecn_bom_analysis_service.analysis.calculate_schedule_impact", return_value=5), \
         patch("app.services.ecn_bom_analysis_service.analysis.get_impact_description", return_value="修改"):
        result = analyze_single_bom(svc, ecn_id=1, bom_header=bom,
                                    affected_materials=[affected_mat], include_cascade=True)

    assert result["has_impact"] is True
    assert len(result["direct_impact"]) == 1


def test_analyze_bom_impact_machine_not_found():
    svc = make_service()
    ecn = MagicMock()
    ecn.machine_id = None
    ecn.project_id = 1

    affected_mat = MagicMock()
    call_count = [0]

    def query_router(*args):
        call_count[0] += 1
        q = MagicMock()
        if call_count[0] == 1:
            q.filter.return_value.first.return_value = ecn
        elif call_count[0] == 2:
            q.filter.return_value.all.return_value = [affected_mat]
        else:
            q.filter.return_value.first.return_value = None
        return q

    svc.db.query.side_effect = query_router
    with pytest.raises(ValueError):
        analyze_bom_impact(svc, ecn_id=1, machine_id=None)
