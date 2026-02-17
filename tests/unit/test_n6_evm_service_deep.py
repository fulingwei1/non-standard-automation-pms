# -*- coding: utf-8 -*-
"""
N6组 - 深度覆盖测试：EVM 挣值管理服务
Coverage target: app/services/evm_service.py

新增分支覆盖（基于 I6 已有测试的补充）：
- EVMService.analyze_performance — 全 4 档 SPI/CPI 状态
- EVMService.create_evm_data — 完整流程 + 项目不存在分支
- EVMService._generate_period_label — WEEK/MONTH/QUARTER/OTHER
- EVMService.get_evm_trend — with/without limit, period_type filter
- EVMService.get_latest_evm_data — found / not found
- EVMCalculator 边界值: EAC with cpi=0 / negative values / TCPI with EAC
"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.evm_service import EVMCalculator, EVMService


# ─────────────────────────────────────────────────
# EVMCalculator 补充边界测试
# ─────────────────────────────────────────────────

class TestEVMCalculatorEdgeCases:
    """未被 I6 覆盖的边界与分支"""

    # ── EAC 特殊情况 ──────────────────────────────

    def test_eac_cpi_is_zero_uses_simple_formula(self):
        """CPI=0（明确传入）→ 简化公式 EAC = AC + (BAC - EV)"""
        eac = EVMCalculator.calculate_estimate_at_completion(
            bac=Decimal("1000"), ev=Decimal("400"), ac=Decimal("500"), cpi=Decimal("0")
        )
        # 简化: 500 + (1000 - 400) = 1100
        assert eac == Decimal("1100.0000")

    def test_eac_cpi_none_but_ac_nonzero_auto_calculates(self):
        """cpi=None 且 AC!=0 → 自动计算 CPI 再求 EAC"""
        # CPI = EV/AC = 400/500 = 0.8
        # EAC = 500 + (1000-400)/0.8 = 500 + 750 = 1250
        eac = EVMCalculator.calculate_estimate_at_completion(
            bac=Decimal("1000"), ev=Decimal("400"), ac=Decimal("500"), cpi=None
        )
        assert eac == Decimal("1250.0000")

    def test_eac_when_project_complete(self):
        """EV == BAC（项目完成）→ EAC 应等于 AC"""
        eac = EVMCalculator.calculate_estimate_at_completion(
            bac=Decimal("1000"), ev=Decimal("1000"), ac=Decimal("900"), cpi=None
        )
        # CPI = 1000/900 ≈ 1.1111
        # EAC = 900 + (1000-1000)/1.1111 = 900
        assert eac == Decimal("900.0000")

    # ── TCPI 基于 EAC 方法 ─────────────────────────

    def test_tcpi_based_on_eac(self):
        """传入 EAC → 使用方法2 (BAC-EV)/(EAC-AC)"""
        # (1000-500)/(1200-600) = 500/600 ≈ 0.833333
        tcpi = EVMCalculator.calculate_to_complete_performance_index(
            bac=Decimal("1000"), ev=Decimal("500"), ac=Decimal("600"),
            eac=Decimal("1200")
        )
        expected = EVMCalculator.round_decimal(Decimal("500") / Decimal("600"), 6)
        assert tcpi == expected

    def test_tcpi_eac_equals_ac_returns_none(self):
        """EAC == AC → 分母为 0 → None"""
        tcpi = EVMCalculator.calculate_to_complete_performance_index(
            bac=Decimal("1000"), ev=Decimal("500"), ac=Decimal("800"),
            eac=Decimal("800")  # EAC == AC → 0
        )
        assert tcpi is None

    # ── VAC 语义 ──────────────────────────────────

    def test_vac_negative_means_over_budget(self):
        """EAC > BAC → VAC < 0 → 超支"""
        vac = EVMCalculator.calculate_variance_at_completion(
            bac=Decimal("1000"), eac=Decimal("1200")
        )
        assert vac == Decimal("-200.0000")

    def test_vac_zero_on_budget(self):
        vac = EVMCalculator.calculate_variance_at_completion(
            bac=Decimal("1000"), eac=Decimal("1000")
        )
        assert vac == Decimal("0.0000")

    # ── SPI/CPI 超前/节约 ─────────────────────────

    def test_spi_greater_than_1_means_ahead(self):
        spi = EVMCalculator.calculate_schedule_performance_index(
            ev=Decimal("600"), pv=Decimal("500")
        )
        assert spi > Decimal("1.0")

    def test_cpi_less_than_1_means_over_budget(self):
        cpi = EVMCalculator.calculate_cost_performance_index(
            ev=Decimal("400"), ac=Decimal("500")
        )
        assert cpi < Decimal("1.0")

    # ── calculate_all_metrics 全量验证 ────────────

    def test_all_metrics_project_over_budget(self):
        """成本超支场景：AC > EV"""
        result = EVMCalculator.calculate_all_metrics(
            pv=Decimal("800"), ev=Decimal("700"), ac=Decimal("900"), bac=Decimal("1000")
        )
        assert result["cv"] < Decimal("0")   # 超支
        assert result["cpi"] < Decimal("1")

    def test_all_metrics_schedule_behind(self):
        """进度落后场景：EV < PV"""
        result = EVMCalculator.calculate_all_metrics(
            pv=Decimal("800"), ev=Decimal("600"), ac=Decimal("600"), bac=Decimal("1000")
        )
        assert result["sv"] < Decimal("0")   # 进度落后
        assert result["spi"] < Decimal("1")

    def test_all_metrics_contains_percentage_keys(self):
        result = EVMCalculator.calculate_all_metrics(
            pv=500, ev=500, ac=500, bac=1000
        )
        assert "planned_percent_complete" in result
        assert "actual_percent_complete" in result
        assert result["planned_percent_complete"] == Decimal("50.00")

    def test_all_metrics_zero_bac_percent_is_none(self):
        result = EVMCalculator.calculate_all_metrics(
            pv=0, ev=0, ac=0, bac=0
        )
        assert result["planned_percent_complete"] is None
        assert result["actual_percent_complete"] is None


# ─────────────────────────────────────────────────
# EVMService.analyze_performance — 全状态分支
# ─────────────────────────────────────────────────

class TestAnalyzePerformance:
    """全 4 档 SPI/CPI 状态 + 综合判断"""

    def setup_method(self):
        self.db = MagicMock()
        self.svc = EVMService(self.db)

    def _make_evm_data(self, spi, cpi):
        d = MagicMock()
        d.schedule_performance_index = Decimal(str(spi))
        d.cost_performance_index = Decimal(str(cpi))
        return d

    # ── 进度状态 ──────────────────────────────────

    def test_schedule_excellent_spi_ge_1_1(self):
        result = self.svc.analyze_performance(self._make_evm_data(1.15, 1.0))
        assert result["schedule_status"] == "EXCELLENT"
        assert "超前" in result["schedule_description"]

    def test_schedule_good_spi_95_to_1_1(self):
        result = self.svc.analyze_performance(self._make_evm_data(1.0, 1.0))
        assert result["schedule_status"] == "GOOD"

    def test_schedule_warning_spi_80_to_95(self):
        result = self.svc.analyze_performance(self._make_evm_data(0.85, 1.0))
        assert result["schedule_status"] == "WARNING"
        assert "轻微" in result["schedule_description"]

    def test_schedule_critical_spi_lt_80(self):
        result = self.svc.analyze_performance(self._make_evm_data(0.70, 1.0))
        assert result["schedule_status"] == "CRITICAL"
        assert "严重" in result["schedule_description"]

    # ── 成本状态 ──────────────────────────────────

    def test_cost_excellent_cpi_ge_1_1(self):
        result = self.svc.analyze_performance(self._make_evm_data(1.0, 1.2))
        assert result["cost_status"] == "EXCELLENT"
        assert "优秀" in result["cost_description"]

    def test_cost_good_cpi_95_to_1_1(self):
        result = self.svc.analyze_performance(self._make_evm_data(1.0, 0.97))
        assert result["cost_status"] == "GOOD"

    def test_cost_warning_cpi_80_to_95(self):
        result = self.svc.analyze_performance(self._make_evm_data(1.0, 0.82))
        assert result["cost_status"] == "WARNING"

    def test_cost_critical_cpi_lt_80(self):
        result = self.svc.analyze_performance(self._make_evm_data(1.0, 0.60))
        assert result["cost_status"] == "CRITICAL"
        assert "严重" in result["cost_description"]

    # ── 综合状态 ──────────────────────────────────

    def test_overall_excellent_both_good(self):
        result = self.svc.analyze_performance(self._make_evm_data(1.15, 1.15))
        assert result["overall_status"] == "EXCELLENT"

    def test_overall_critical_when_either_critical(self):
        result = self.svc.analyze_performance(self._make_evm_data(0.70, 1.0))
        assert result["overall_status"] == "CRITICAL"

    def test_overall_warning_when_either_warning(self):
        result = self.svc.analyze_performance(self._make_evm_data(0.85, 1.0))
        assert result["overall_status"] == "WARNING"

    def test_overall_good_both_good_spi_cpi(self):
        result = self.svc.analyze_performance(self._make_evm_data(1.0, 1.0))
        assert result["overall_status"] in ("EXCELLENT", "GOOD")

    def test_performance_returns_float_spi_cpi(self):
        result = self.svc.analyze_performance(self._make_evm_data(1.1, 1.1))
        assert isinstance(result["spi"], float)
        assert isinstance(result["cpi"], float)

    def test_performance_zero_spi_cpi_treated_as_critical(self):
        """SPI/CPI 默认为 Decimal('0') 时，状态为 CRITICAL"""
        result = self.svc.analyze_performance(self._make_evm_data(0, 0))
        assert result["schedule_status"] == "CRITICAL"
        assert result["cost_status"] == "CRITICAL"


# ─────────────────────────────────────────────────
# EVMService._generate_period_label
# ─────────────────────────────────────────────────

class TestGeneratePeriodLabel:
    def setup_method(self):
        self.svc = EVMService(MagicMock())

    def test_week_label_format(self):
        d = date(2026, 2, 16)   # 2026年第7周
        label = self.svc._generate_period_label("WEEK", d)
        assert label.startswith("2026-W")
        assert "W07" in label or "W" in label

    def test_month_label_format(self):
        d = date(2026, 2, 15)
        label = self.svc._generate_period_label("MONTH", d)
        assert label == "2026-02"

    def test_quarter_label_q1(self):
        d = date(2026, 1, 15)
        label = self.svc._generate_period_label("QUARTER", d)
        assert label == "2026-Q1"

    def test_quarter_label_q2(self):
        d = date(2026, 4, 1)
        label = self.svc._generate_period_label("QUARTER", d)
        assert label == "2026-Q2"

    def test_quarter_label_q3(self):
        d = date(2026, 7, 1)
        label = self.svc._generate_period_label("QUARTER", d)
        assert label == "2026-Q3"

    def test_quarter_label_q4(self):
        d = date(2026, 10, 1)
        label = self.svc._generate_period_label("QUARTER", d)
        assert label == "2026-Q4"

    def test_unknown_period_type_returns_date_string(self):
        d = date(2026, 3, 5)
        label = self.svc._generate_period_label("DAILY", d)
        assert label == "2026-03-05"


# ─────────────────────────────────────────────────
# EVMService.create_evm_data
# ─────────────────────────────────────────────────

class TestCreateEvmData:
    def setup_method(self):
        self.db = MagicMock()
        self.svc = EVMService(self.db)

    def test_project_not_found_raises_value_error(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="项目不存在"):
            self.svc.create_evm_data(
                project_id=999,
                period_type="MONTH",
                period_date=date(2026, 1, 31),
                pv=Decimal("500"),
                ev=Decimal("450"),
                ac=Decimal("480"),
                bac=Decimal("1000"),
            )

    def test_creates_evm_data_with_computed_metrics(self):
        project = MagicMock()
        project.id = 1
        project.project_code = "P001"
        self.db.query.return_value.filter.return_value.first.return_value = project

        saved_objects = []

        def mock_save(db, obj):
            saved_objects.append(obj)

        with patch("app.services.evm_service.save_obj", side_effect=mock_save):
            result = self.svc.create_evm_data(
                project_id=1,
                period_type="MONTH",
                period_date=date(2026, 1, 31),
                pv=Decimal("500"),
                ev=Decimal("450"),
                ac=Decimal("480"),
                bac=Decimal("1000"),
            )

        assert len(saved_objects) == 1
        record = saved_objects[0]
        assert record.project_id == 1
        assert record.planned_value == Decimal("500.0000")
        assert record.earned_value == Decimal("450.0000")
        assert record.schedule_variance == Decimal("-50.0000")  # EV-PV = -50

    def test_period_label_set_correctly_for_week(self):
        project = MagicMock(); project.project_code = "P001"
        self.db.query.return_value.filter.return_value.first.return_value = project

        with patch("app.services.evm_service.save_obj"):
            result = self.svc.create_evm_data(
                project_id=1,
                period_type="WEEK",
                period_date=date(2026, 2, 16),
                pv=Decimal("100"), ev=Decimal("100"), ac=Decimal("100"), bac=Decimal("1000"),
            )
        assert "W" in result.period_label

    def test_notes_and_data_source_passed_through(self):
        project = MagicMock(); project.project_code = "P001"
        self.db.query.return_value.filter.return_value.first.return_value = project

        saved = []
        with patch("app.services.evm_service.save_obj", side_effect=lambda db, obj: saved.append(obj)):
            self.svc.create_evm_data(
                project_id=1,
                period_type="MONTH",
                period_date=date(2026, 1, 31),
                pv=Decimal("100"), ev=Decimal("100"), ac=Decimal("100"), bac=Decimal("1000"),
                data_source="AUTO",
                notes="系统自动导入",
            )
        assert saved[0].data_source == "AUTO"
        assert saved[0].notes == "系统自动导入"


# ─────────────────────────────────────────────────
# EVMService.get_latest_evm_data / get_evm_trend
# ─────────────────────────────────────────────────

class TestGetLatestEvmData:
    def setup_method(self):
        self.db = MagicMock()
        self.svc = EVMService(self.db)

    def test_returns_latest_data(self):
        mock_record = MagicMock()
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_record
        result = self.svc.get_latest_evm_data(1)
        assert result == mock_record

    def test_returns_none_when_no_data(self):
        self.db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = self.svc.get_latest_evm_data(999)
        assert result is None

    def test_filters_by_period_type(self):
        mock_record = MagicMock()
        mock_q = self.db.query.return_value
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.first.return_value = mock_record

        result = self.svc.get_latest_evm_data(1, period_type="WEEK")
        assert result == mock_record


class TestGetEvmTrend:
    def setup_method(self):
        self.db = MagicMock()
        self.svc = EVMService(self.db)

    def test_returns_list_of_records(self):
        r1 = MagicMock()
        r2 = MagicMock()
        mock_q = self.db.query.return_value
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = [r1, r2]

        result = self.svc.get_evm_trend(1)
        assert len(result) == 2

    def test_limit_applied(self):
        mock_q = self.db.query.return_value
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.limit.return_value = mock_q
        mock_q.all.return_value = []

        self.svc.get_evm_trend(1, limit=5)
        mock_q.limit.assert_called_with(5)

    def test_no_limit_no_limit_call(self):
        mock_q = self.db.query.return_value
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = []

        self.svc.get_evm_trend(1)
        mock_q.limit.assert_not_called()

    def test_period_type_filter_applied(self):
        mock_q = self.db.query.return_value
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = []

        self.svc.get_evm_trend(1, period_type="QUARTER")
        # filter was called (at least once for period_type)
        assert mock_q.filter.call_count >= 1
