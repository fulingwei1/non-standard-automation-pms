# -*- coding: utf-8 -*-
"""
N6组 - 深度覆盖测试：齐套分析服务（辅助函数）
Coverage target: app/services/assembly_kit_service.py

分支覆盖：
1. validate_analysis_inputs — 项目不存在/BOM不存在/机台不存在
2. initialize_stage_results — 多阶段初始化
3. analyze_bom_item — 无物料/有attr/无attr(默认MECH)/缺料/齐备
4. calculate_stage_kit_rates — 各阶段can_start逻辑
5. get_expected_arrival_date — 有/无PO
"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.assembly_kit_service import (
    validate_analysis_inputs,
    initialize_stage_results,
    analyze_bom_item,
    calculate_stage_kit_rates,
    get_expected_arrival_date,
)


# ─────────────────────────────────────────────────
# validate_analysis_inputs
# ─────────────────────────────────────────────────

class TestValidateAnalysisInputs:

    def _make_db(self, project=None, bom=None, machine=None):
        db = MagicMock()
        call_seq = [0]

        def side_effect(model):
            q = MagicMock()
            q.filter.return_value = q
            idx = call_seq[0]; call_seq[0] += 1
            # Determine by call order: project(0), bom(1), machine(2)
            if idx == 0:
                q.first.return_value = project
            elif idx == 1:
                q.first.return_value = bom
            else:
                q.first.return_value = machine
            return q

        db.query.side_effect = side_effect
        return db

    def test_project_not_found_raises_404(self):
        db = self._make_db(project=None)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            validate_analysis_inputs(db, 1, 1)
        assert exc.value.status_code == 404
        assert "项目" in exc.value.detail

    def test_bom_not_found_raises_404(self):
        project = MagicMock()
        db = self._make_db(project=project, bom=None)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            validate_analysis_inputs(db, 1, 1)
        assert exc.value.status_code == 404
        assert "BOM" in exc.value.detail

    def test_machine_not_found_raises_404(self):
        project = MagicMock()
        bom = MagicMock()
        db = self._make_db(project=project, bom=bom, machine=None)
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            validate_analysis_inputs(db, 1, 1, machine_id=99)
        assert exc.value.status_code == 404
        assert "机台" in exc.value.detail

    def test_no_machine_id_skips_machine_check(self):
        project = MagicMock()
        bom = MagicMock()
        db = self._make_db(project=project, bom=bom)
        result = validate_analysis_inputs(db, 1, 1)
        assert result[2] is None  # machine is None

    def test_all_found_returns_tuple(self):
        project = MagicMock()
        bom = MagicMock()
        machine = MagicMock()
        db = self._make_db(project=project, bom=bom, machine=machine)
        p, b, m = validate_analysis_inputs(db, 1, 1, machine_id=1)
        assert p is project
        assert b is bom
        assert m is machine


# ─────────────────────────────────────────────────
# initialize_stage_results
# ─────────────────────────────────────────────────

class TestInitializeStageResults:

    def _make_stage(self, code, order):
        s = MagicMock()
        s.stage_code = code
        s.stage_order = order
        return s

    def test_creates_entry_for_each_stage(self):
        stages = [
            self._make_stage("FRAME", 1),
            self._make_stage("MECH", 2),
            self._make_stage("ELECTRIC", 3),
        ]
        result = initialize_stage_results(stages)
        assert "FRAME" in result
        assert "MECH" in result
        assert "ELECTRIC" in result

    def test_all_counts_start_at_zero(self):
        stages = [self._make_stage("MECH", 1)]
        result = initialize_stage_results(stages)
        assert result["MECH"]["total"] == 0
        assert result["MECH"]["fulfilled"] == 0
        assert result["MECH"]["blocking_total"] == 0
        assert result["MECH"]["blocking_fulfilled"] == 0

    def test_empty_stages_returns_empty_dict(self):
        result = initialize_stage_results([])
        assert result == {}

    def test_stage_object_stored(self):
        stage = self._make_stage("WIRING", 4)
        result = initialize_stage_results([stage])
        assert result["WIRING"]["stage"] is stage


# ─────────────────────────────────────────────────
# analyze_bom_item
# ─────────────────────────────────────────────────

class TestAnalyzeBomItem:

    def _make_simple_calc(self, stock, allocated, in_transit, available):
        def calc(db, material_id, check_date):
            return (Decimal(str(stock)), Decimal(str(allocated)),
                    Decimal(str(in_transit)), Decimal(str(available)))
        return calc

    def test_no_material_returns_none(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        bom_item = MagicMock(); bom_item.material_id = 99
        stage_map = {}; stage_results = {"MECH": {"total": 0, "fulfilled": 0, "blocking_total": 0, "blocking_fulfilled": 0}}

        result = analyze_bom_item(db, bom_item, date.today(), stage_map, stage_results,
                                   self._make_simple_calc(0, 0, 0, 0))
        assert result is None

    def test_fulfilled_item_returns_none(self):
        """有足够库存 → 返回 None（无缺料）"""
        db = MagicMock()
        material = MagicMock(); material.id = 1
        db.query.return_value.filter.return_value.first.side_effect = [material, None]

        bom_item = MagicMock()
        bom_item.id = 1; bom_item.material_id = 1
        bom_item.quantity = Decimal("10")
        bom_item.required_date = None

        stage_results = {"MECH": {"total": 0, "fulfilled": 0, "blocking_total": 0, "blocking_fulfilled": 0}}

        # available = 20 >= required = 10 → fulfilled
        result = analyze_bom_item(db, bom_item, date.today(), {}, stage_results,
                                   self._make_simple_calc(20, 0, 0, 20))
        assert result is None
        assert stage_results["MECH"]["fulfilled"] == 1

    def test_shortage_item_returns_dict(self):
        """库存不足 → 返回缺料信息字典"""
        db = MagicMock()
        material = MagicMock(); material.id = 1
        material.material_code = "MAT001"; material.material_name = "物料A"
        # First query: material, second query: BomItemAssemblyAttrs
        db.query.return_value.filter.return_value.first.side_effect = [material, None]

        bom_item = MagicMock()
        bom_item.id = 1; bom_item.material_id = 1
        bom_item.quantity = Decimal("10")
        bom_item.required_date = date.today()

        stage_results = {"MECH": {"total": 0, "fulfilled": 0, "blocking_total": 0, "blocking_fulfilled": 0}}

        with patch("app.services.assembly_kit_service.get_expected_arrival_date", return_value=None), \
             patch("app.api.v1.endpoints.assembly_kit.kit_analysis.utils.determine_alert_level", return_value="HIGH"):
            result = analyze_bom_item(db, bom_item, date.today(), {}, stage_results,
                                       self._make_simple_calc(0, 0, 0, 0))

        assert result is not None
        assert result["shortage_qty"] == Decimal("10")
        assert result["assembly_stage"] == "MECH"

    def test_default_stage_is_mech_when_no_attr(self):
        db = MagicMock()
        material = MagicMock(); material.id = 1
        material.material_code = "MAT001"; material.material_name = "物料B"
        # BomItemAssemblyAttrs returns None → default MECH
        db.query.return_value.filter.return_value.first.side_effect = [material, None]

        bom_item = MagicMock()
        bom_item.id = 2; bom_item.material_id = 1
        bom_item.quantity = Decimal("5"); bom_item.required_date = date.today()

        stage_results = {"MECH": {"total": 0, "fulfilled": 0, "blocking_total": 0, "blocking_fulfilled": 0}}

        with patch("app.services.assembly_kit_service.get_expected_arrival_date", return_value=None), \
             patch("app.api.v1.endpoints.assembly_kit.kit_analysis.utils.determine_alert_level", return_value="MEDIUM"):
            result = analyze_bom_item(db, bom_item, date.today(), {}, stage_results,
                                       self._make_simple_calc(0, 0, 0, 0))

        if result:
            assert result["assembly_stage"] == "MECH"


# ─────────────────────────────────────────────────
# calculate_stage_kit_rates
# ─────────────────────────────────────────────────

class TestCalculateStageKitRates:

    def _make_stage(self, code, order):
        s = MagicMock()
        s.stage_code = code
        s.stage_order = order
        s.stage_name = f"{code} 阶段"
        s.color_code = "#000"
        return s

    def test_all_fulfilled_can_proceed(self):
        stages = [self._make_stage("FRAME", 1), self._make_stage("MECH", 2)]
        stage_results = {
            "FRAME": {"total": 5, "fulfilled": 5, "blocking_total": 5, "blocking_fulfilled": 5, "stage": stages[0]},
            "MECH":  {"total": 8, "fulfilled": 8, "blocking_total": 8, "blocking_fulfilled": 8, "stage": stages[1]},
        }
        rates, can_proceed, first_blocked, workable, overall, blocking_items = \
            calculate_stage_kit_rates(stages, stage_results, [])

        assert can_proceed is True
        assert first_blocked is None
        assert workable == "MECH"

    def test_first_stage_blocked_stops_all(self):
        stages = [self._make_stage("FRAME", 1), self._make_stage("MECH", 2)]
        stage_results = {
            "FRAME": {"total": 5, "fulfilled": 3, "blocking_total": 5, "blocking_fulfilled": 3, "stage": stages[0]},
            "MECH":  {"total": 8, "fulfilled": 8, "blocking_total": 8, "blocking_fulfilled": 8, "stage": stages[1]},
        }
        rates, can_proceed, first_blocked, workable, overall, blocking_items = \
            calculate_stage_kit_rates(stages, stage_results, [])

        assert can_proceed is False
        assert first_blocked == "FRAME"

    def test_overall_stats_summed(self):
        stages = [self._make_stage("FRAME", 1)]
        stage_results = {
            "FRAME": {"total": 10, "fulfilled": 7, "blocking_total": 6, "blocking_fulfilled": 6, "stage": stages[0]},
        }
        _, _, _, _, overall, _ = calculate_stage_kit_rates(stages, stage_results, [])
        assert overall["total"] == 10
        assert overall["fulfilled"] == 7

    def test_empty_stage_has_100pct_kit_rate(self):
        stages = [self._make_stage("COSMETIC", 5)]
        stage_results = {
            "COSMETIC": {"total": 0, "fulfilled": 0, "blocking_total": 0, "blocking_fulfilled": 0, "stage": stages[0]},
        }
        rates, _, _, _, _, _ = calculate_stage_kit_rates(stages, stage_results, [])
        assert rates[0]["kit_rate"] == Decimal("100")
        assert rates[0]["blocking_rate"] == Decimal("100")

    def test_blocking_items_collected_for_blocked_stage(self):
        stages = [self._make_stage("MECH", 1)]
        stage_results = {
            "MECH": {"total": 3, "fulfilled": 2, "blocking_total": 2, "blocking_fulfilled": 1, "stage": stages[0]},
        }
        shortage_details = [
            {"assembly_stage": "MECH", "is_blocking": True, "material_code": "M001"},
        ]
        _, _, _, _, _, blocking_items = calculate_stage_kit_rates(stages, stage_results, shortage_details)
        assert len(blocking_items) == 1
        assert blocking_items[0]["material_code"] == "M001"


# ─────────────────────────────────────────────────
# get_expected_arrival_date
# ─────────────────────────────────────────────────

class TestGetExpectedArrivalDate:

    def test_no_po_returns_none(self):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = get_expected_arrival_date(db, 1)
        assert result is None

    def test_po_with_promised_date_returns_date(self):
        db = MagicMock()
        po_item = MagicMock()
        po_item.order = MagicMock()
        po_item.order.promised_date = date(2026, 3, 15)
        db.query.return_value.join.return_value.filter.return_value.order_by.return_value.first.return_value = po_item

        result = get_expected_arrival_date(db, 1)
        assert result == date(2026, 3, 15)

    def test_exception_returns_none(self):
        """异常不应传播，返回 None"""
        db = MagicMock()
        db.query.side_effect = Exception("DB error")
        result = get_expected_arrival_date(db, 1)
        assert result is None
