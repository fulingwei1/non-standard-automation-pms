# -*- coding: utf-8 -*-
"""assembly_kit_service 单元测试 - 齐套分析工具函数"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestInitializeStageResults:
    """initialize_stage_results 函数测试"""

    def test_empty_stages(self):
        from app.services.assembly_kit_service import initialize_stage_results
        result = initialize_stage_results([])
        assert result == {}

    def test_single_stage(self):
        from app.services.assembly_kit_service import initialize_stage_results
        stage = MagicMock()
        stage.stage_code = "MECH"
        result = initialize_stage_results([stage])
        assert "MECH" in result
        assert result["MECH"]["total"] == 0
        assert result["MECH"]["fulfilled"] == 0
        assert result["MECH"]["blocking_total"] == 0
        assert result["MECH"]["stage"] == stage

    def test_multiple_stages(self):
        from app.services.assembly_kit_service import initialize_stage_results
        codes = ["MECH", "ELEC", "SOFT"]
        stages = [MagicMock(stage_code=c) for c in codes]
        result = initialize_stage_results(stages)
        assert set(result.keys()) == set(codes)


class TestCalculateStageKitRates:
    """calculate_stage_kit_rates 函数测试"""

    def _make_stage(self, code, order, name=None):
        s = MagicMock()
        s.stage_code = code
        s.stage_order = order
        s.stage_name = name or code
        s.color_code = "#000"
        return s

    def test_all_fulfilled_can_proceed(self):
        from app.services.assembly_kit_service import calculate_stage_kit_rates
        stages = [self._make_stage("MECH", 1)]
        stage_results = {
            "MECH": {"total": 2, "fulfilled": 2, "blocking_total": 2, "blocking_fulfilled": 2, "stage": stages[0]}
        }
        rates, can_proceed, first_blocked, workable, overall, blocking_items = calculate_stage_kit_rates(
            stages, stage_results, []
        )
        assert can_proceed is True
        assert first_blocked is None
        assert workable == "MECH"
        assert rates[0]["kit_rate"] == Decimal("100")

    def test_blocking_shortage_blocks_proceed(self):
        from app.services.assembly_kit_service import calculate_stage_kit_rates
        stages = [self._make_stage("MECH", 1), self._make_stage("ELEC", 2)]
        stage_results = {
            "MECH": {"total": 3, "fulfilled": 2, "blocking_total": 2, "blocking_fulfilled": 1, "stage": stages[0]},
            "ELEC": {"total": 2, "fulfilled": 2, "blocking_total": 1, "blocking_fulfilled": 1, "stage": stages[1]},
        }
        shortage_details = [
            {"assembly_stage": "MECH", "is_blocking": True, "material_code": "M001"}
        ]
        rates, can_proceed, first_blocked, workable, overall, blocking_items = calculate_stage_kit_rates(
            stages, stage_results, shortage_details
        )
        assert can_proceed is False
        assert first_blocked == "MECH"
        assert len(blocking_items) == 1

    def test_overall_stats_accumulated(self):
        from app.services.assembly_kit_service import calculate_stage_kit_rates
        stages = [self._make_stage("MECH", 1), self._make_stage("ELEC", 2)]
        stage_results = {
            "MECH": {"total": 3, "fulfilled": 3, "blocking_total": 2, "blocking_fulfilled": 2, "stage": stages[0]},
            "ELEC": {"total": 2, "fulfilled": 2, "blocking_total": 1, "blocking_fulfilled": 1, "stage": stages[1]},
        }
        _, _, _, _, overall, _ = calculate_stage_kit_rates(stages, stage_results, [])
        assert overall["total"] == 5
        assert overall["fulfilled"] == 5


class TestGetExpectedArrivalDate:
    """get_expected_arrival_date 函数测试"""

    def test_returns_none_when_no_po(self):
        from app.services.assembly_kit_service import get_expected_arrival_date
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = get_expected_arrival_date(db, 1)
        assert result is None

    def test_handles_import_error_gracefully(self):
        """当模型不存在时应返回 None 而不是抛出异常"""
        from app.services.assembly_kit_service import get_expected_arrival_date
        db = MagicMock()
        db.query.side_effect = Exception("模型不存在")
        result = get_expected_arrival_date(db, 99)
        assert result is None


class TestValidateAnalysisInputs:
    """validate_analysis_inputs 函数测试"""

    def test_project_not_found_raises_404(self):
        from fastapi import HTTPException
        from app.services.assembly_kit_service import validate_analysis_inputs
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            validate_analysis_inputs(db, project_id=999, bom_id=1)
        assert exc_info.value.status_code == 404

    def test_bom_not_found_raises_404(self):
        from fastapi import HTTPException
        from app.services.assembly_kit_service import validate_analysis_inputs
        db = MagicMock()
        project = MagicMock()
        # First query returns project, second returns None (BOM not found)
        db.query.return_value.filter.return_value.first.side_effect = [project, None, None]
        with pytest.raises(HTTPException) as exc_info:
            validate_analysis_inputs(db, project_id=1, bom_id=999)
        assert exc_info.value.status_code == 404
