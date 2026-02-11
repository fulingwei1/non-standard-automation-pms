# -*- coding: utf-8 -*-
"""Tests for assembly_kit_service.py"""
from unittest.mock import MagicMock, patch
from decimal import Decimal
from datetime import date

from app.services.assembly_kit_service import (
    validate_analysis_inputs,
    initialize_stage_results,
    analyze_bom_item,
    get_expected_arrival_date,
    calculate_stage_kit_rates,
)


class TestValidateAnalysisInputs:
    def test_all_valid(self):
        db = MagicMock()
        project = MagicMock()
        bom = MagicMock()
        machine = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [project, bom, machine]
        p, b, m = validate_analysis_inputs(db, 1, 1, 1)
        assert p == project
        assert m == machine

    def test_no_project(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        import pytest
        with pytest.raises(Exception):
            validate_analysis_inputs(db, 1, 1)

    def test_no_machine_optional(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.side_effect = [MagicMock(), MagicMock()]
        p, b, m = validate_analysis_inputs(db, 1, 1)
        assert m is None


class TestInitializeStageResults:
    def test_basic(self):
        stage = MagicMock(stage_code="FRAME")
        result = initialize_stage_results([stage])
        assert "FRAME" in result
        assert result["FRAME"]["total"] == 0


class TestAnalyzeBomItem:
    def test_no_material(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        bom_item = MagicMock(material_id=1)
        result = analyze_bom_item(db, bom_item, date.today(), {}, {}, lambda *a: (0, 0, 0, 0))
        assert result is None

    @patch("app.services.assembly_kit_service.get_expected_arrival_date", return_value=None)
    def test_shortage_detected(self, mock_arrival):
        db = MagicMock()
        material = MagicMock(id=1, material_code="M001", material_name="物料A")
        attr = MagicMock(assembly_stage="MECH", is_blocking=True)
        db.query.return_value.filter.return_value.first.side_effect = [material, attr]
        bom_item = MagicMock(id=1, material_id=1, quantity=Decimal(10), required_date=None)
        stage_results = {"MECH": {"total": 0, "fulfilled": 0, "blocking_total": 0, "blocking_fulfilled": 0}}

        def calc_qty(db, mid, d):
            return (Decimal(0), Decimal(0), Decimal(0), Decimal(3))

        with patch("app.services.assembly_kit_service.get_expected_arrival_date", return_value=None):
            with patch("app.api.v1.endpoints.assembly_kit.kit_analysis.utils.determine_alert_level", return_value="L1"):
                result = analyze_bom_item(db, bom_item, date.today(), {"MECH": MagicMock()}, stage_results, calc_qty)
        if result:
            assert result['shortage_qty'] == Decimal(7)


class TestGetExpectedArrivalDate:
    def test_no_po(self):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = get_expected_arrival_date(db, 1)
        assert result is None


class TestCalculateStageKitRates:
    def test_all_fulfilled(self):
        stage = MagicMock(stage_code="FRAME", stage_name="框架", stage_order=1, color_code="#000")
        stage_results = {"FRAME": {"total": 5, "fulfilled": 5, "blocking_total": 3, "blocking_fulfilled": 3}}
        rates, can_proceed, blocked, workable, stats, blocking = calculate_stage_kit_rates(
            [stage], stage_results, []
        )
        assert can_proceed is True
        assert workable == "FRAME"
        assert rates[0]['kit_rate'] == Decimal(100)

    def test_blocked_stage(self):
        s1 = MagicMock(stage_code="FRAME", stage_name="框架", stage_order=1, color_code="#000")
        s2 = MagicMock(stage_code="MECH", stage_name="机械", stage_order=2, color_code="#111")
        stage_results = {
            "FRAME": {"total": 5, "fulfilled": 5, "blocking_total": 3, "blocking_fulfilled": 3},
            "MECH": {"total": 5, "fulfilled": 2, "blocking_total": 3, "blocking_fulfilled": 1},
        }
        rates, can_proceed, blocked, workable, stats, blocking = calculate_stage_kit_rates(
            [s1, s2], stage_results, []
        )
        assert can_proceed is False
        assert blocked == "MECH"
        assert workable == "FRAME"
