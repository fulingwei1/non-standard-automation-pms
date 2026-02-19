# -*- coding: utf-8 -*-
"""第四十六批 - KPI采集计算单元测试"""
import pytest
from decimal import Decimal

pytest.importorskip("app.services.strategy.kpi_collector.calculation",
                    reason="依赖不满足，跳过")

from unittest.mock import MagicMock, patch
from app.services.strategy.kpi_collector.calculation import (
    calculate_formula,
    collect_kpi_value,
    auto_collect_kpi,
    batch_collect_kpis,
)


class TestCalculateFormula:
    def test_returns_none_for_empty_formula(self):
        result = calculate_formula("", {})
        assert result is None

    def test_calculates_simple_expression(self):
        with patch("app.services.strategy.kpi_collector.calculation.HAS_SIMPLEEVAL", True), \
             patch("app.services.strategy.kpi_collector.calculation.simple_eval",
                   return_value=50.0):
            result = calculate_formula("a / b * 100", {"a": 10, "b": 20})
        assert result == Decimal("50.0")

    def test_raises_runtime_error_without_simpleeval(self):
        with patch("app.services.strategy.kpi_collector.calculation.HAS_SIMPLEEVAL", False):
            with pytest.raises(RuntimeError, match="simpleeval"):
                calculate_formula("a + b", {"a": 1, "b": 2})

    def test_returns_none_on_eval_exception(self):
        with patch("app.services.strategy.kpi_collector.calculation.HAS_SIMPLEEVAL", True), \
             patch("app.services.strategy.kpi_collector.calculation.simple_eval",
                   side_effect=Exception("bad formula")):
            result = calculate_formula("invalid!!!", {})
        assert result is None


class TestCollectKpiValue:
    def test_returns_none_when_kpi_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = collect_kpi_value(db, 99)
        assert result is None

    def test_returns_none_when_data_source_not_found(self):
        db = MagicMock()
        kpi = MagicMock()
        kpi.is_active = True
        call_count = [0]

        def query_side(model):
            call_count[0] += 1
            q = MagicMock()
            if call_count[0] == 1:
                q.filter.return_value.first.return_value = kpi
            else:
                q.filter.return_value.first.return_value = None
            return q

        db.query.side_effect = query_side
        result = collect_kpi_value(db, 1)
        assert result is None

    def test_manual_source_returns_current_value(self):
        db = MagicMock()
        kpi = MagicMock()
        kpi.current_value = Decimal("42")
        data_source = MagicMock()
        data_source.source_type = "MANUAL"
        data_source.formula = None

        call_count = [0]

        def query_side(model):
            call_count[0] += 1
            q = MagicMock()
            if call_count[0] == 1:
                q.filter.return_value.first.return_value = kpi
            else:
                q.filter.return_value.first.return_value = data_source
            return q

        db.query.side_effect = query_side
        result = collect_kpi_value(db, 1)
        assert result == Decimal("42")


class TestAutoCollectKpi:
    def test_returns_none_when_collect_value_returns_none(self):
        db = MagicMock()
        with patch("app.services.strategy.kpi_collector.calculation.collect_kpi_value",
                   return_value=None):
            result = auto_collect_kpi(db, 1)
        assert result is None

    def test_updates_kpi_current_value(self):
        db = MagicMock()
        kpi = MagicMock()
        kpi.id = 1
        db.query.return_value.filter.return_value.first.return_value = kpi

        with patch("app.services.strategy.kpi_collector.calculation.collect_kpi_value",
                   return_value=Decimal("55")), \
             patch("app.services.strategy.kpi_collector.calculation.create_kpi_snapshot"):
            result = auto_collect_kpi(db, 1, recorded_by=10)

        assert kpi.current_value == Decimal("55")
        db.commit.assert_called()


class TestBatchCollectKpis:
    def test_returns_stats_dict(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []

        result = batch_collect_kpis(db)
        assert result["total"] == 0
        assert result["success"] == 0
        assert result["failed"] == 0

    def test_counts_success_and_failure(self):
        db = MagicMock()
        kpi1 = MagicMock()
        kpi1.id = 1
        kpi1.code = "K1"
        kpi1.name = "KPI1"
        kpi2 = MagicMock()
        kpi2.id = 2
        kpi2.code = "K2"
        kpi2.name = "KPI2"
        db.query.return_value.filter.return_value.all.return_value = [kpi1, kpi2]

        side_effects = [MagicMock(), None]

        with patch("app.services.strategy.kpi_collector.calculation.auto_collect_kpi",
                   side_effect=side_effects):
            result = batch_collect_kpis(db)

        assert result["success"] == 1
        assert result["failed"] == 1
        assert len(result["failed_kpis"]) == 1
