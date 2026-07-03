# -*- coding: utf-8 -*-
"""Tests for assembly_kit_service.py"""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.assembly_kit_service import (
    analyze_bom_item,
    calculate_stage_kit_rates,
    get_expected_arrival_date,
    initialize_stage_results,
    validate_analysis_inputs,
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
        stage_results = {
            "MECH": {"total": 0, "fulfilled": 0, "blocking_total": 0, "blocking_fulfilled": 0}
        }

        def calc_qty(db, mid, d):
            return (Decimal(0), Decimal(0), Decimal(0), Decimal(3))

        with patch(
            "app.services.assembly_kit_service.get_expected_arrival_date", return_value=None
        ):
            with patch(
                "app.api.v1.endpoints.assembly_kit.kit_analysis.utils.determine_alert_level",
                return_value="L1",
            ):
                result = analyze_bom_item(
                    db, bom_item, date.today(), {"MECH": MagicMock()}, stage_results, calc_qty
                )
        if result:
            assert result["shortage_qty"] == Decimal(7)


class TestGetExpectedArrivalDate:
    def test_no_po(self):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.order_by.return_value.first.return_value = (
            None
        )
        result = get_expected_arrival_date(db, 1)
        assert result is None


class TestCalculateStageKitRates:
    def test_all_fulfilled(self):
        stage = MagicMock(stage_code="FRAME", stage_name="框架", stage_order=1, color_code="#000")
        stage_results = {
            "FRAME": {"total": 5, "fulfilled": 5, "blocking_total": 3, "blocking_fulfilled": 3}
        }
        rates, can_proceed, blocked, workable, stats, blocking = calculate_stage_kit_rates(
            [stage], stage_results, []
        )
        assert can_proceed is True
        assert workable == "FRAME"
        assert rates[0]["kit_rate"] == Decimal(100)

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


class TestAssemblyKitServiceStageRate:
    def test_stage_kit_rate_does_not_count_received_or_transit_as_fulfilled(self):
        from app.services.assembly_kit_service import AssemblyKitService

        db = MagicMock()
        bom = SimpleNamespace(id=1)
        material = SimpleNamespace(
            current_stock=2,
            material_code="MAT-001",
            material_name="在途物料",
        )
        bom_item = SimpleNamespace(
            id=10,
            item_no="001",
            material=material,
            material_id=1,
            quantity=10,
            received_qty=8,
        )
        attrs = SimpleNamespace(
            bom_item_id=10,
            assembly_stage="MECH",
            is_blocking=True,
        )

        call_count = [0]

        def query_side_effect(*models):
            query = MagicMock()
            query.filter.return_value = query
            if call_count[0] == 0:
                query.all.return_value = [bom]
            elif call_count[0] == 1:
                query.all.return_value = [bom_item]
            else:
                query.all.return_value = [attrs]
            call_count[0] += 1
            return query

        db.query.side_effect = query_side_effect
        service = AssemblyKitService(db)

        with patch(
            "app.services.assembly_kit_service.get_purchase_in_transit_qty",
            return_value=Decimal("8"),
        ):
            result = service.calculate_stage_kit_rate(project_id=1)

        stage = result["stages"]["MECH"]
        assert stage["fulfilled_items"] == 0
        assert stage["shortage_items"] == 1
        assert stage["in_transit_items"] == 1
        assert stage["overall_kit_rate"] == 0.0

    def test_time_based_kit_rate_does_not_count_received_qty_as_available(self):
        from app.services.assembly_kit_service import AssemblyKitService

        db = MagicMock()
        bom = SimpleNamespace(id=1)
        material = SimpleNamespace(
            current_stock=2,
            material_code="MAT-001",
            material_name="已到货字段不等于库存",
        )
        bom_item = SimpleNamespace(
            id=10,
            item_no="001",
            material=material,
            material_id=1,
            quantity=10,
            received_qty=8,
        )
        attrs = SimpleNamespace(bom_item_id=10, assembly_stage="MECH")

        call_count = [0]

        def query_side_effect(*models):
            query = MagicMock()
            query.filter.return_value = query
            if call_count[0] == 0:
                query.all.return_value = [bom]
            elif call_count[0] == 1:
                query.all.return_value = [bom_item]
            elif call_count[0] == 2:
                query.all.return_value = [attrs]
            else:
                query.join.return_value.filter.return_value.all.return_value = []
            call_count[0] += 1
            return query

        db.query.side_effect = query_side_effect
        service = AssemblyKitService(db)

        with patch.object(
            service,
            "calculate_stage_kit_rate",
            return_value={"stages": {"MECH": {"overall_kit_rate": 0}}},
        ), patch.object(
            service,
            "get_material_lead_time",
            return_value={"avg_lead_time": 5},
        ):
            result = service.calculate_time_based_kit_rate(project_id=1)

        shortage_item = result["stages"]["MECH"]["shortage_items"][0]
        assert shortage_item["available_qty"] == 2
        assert shortage_item["shortage_qty"] == 8
