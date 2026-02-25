# -*- coding: utf-8 -*-
"""business_rules.py 综合测试 - 覆盖所有函数和分支"""

from datetime import date
from decimal import Decimal

import pytest

from app.services.business_rules import (
    KPI_BENCHMARKS,
    calc_gross_margin,
    is_warning_required,
    requires_gm_approval,
    calc_kit_rate,
    should_trigger_shortage_alert,
    calc_spi,
    get_delay_alert_level,
    PaymentMilestone,
    STANDARD_PAYMENT_RATIOS,
    create_standard_payment_milestones,
    calc_payment_overdue_days,
    is_overdue_escalation_required,
    is_daily_overtime,
    should_hr_review,
    evaluate_fat_result,
    FATResult,
    calc_final_margin,
    requires_margin_review,
    analyze_delay_root_causes,
    recalculate_delivery_date,
    calc_bom_kit_rate,
    generate_shortage_alert,
    ShortageAlert,
)


# ---- 1. 毛利率 ----

class TestCalcGrossMargin:
    def test_normal_case(self):
        m = calc_gross_margin(1000, 200, 100, 50, 50)
        assert m == Decimal("0.600000")

    def test_zero_costs(self):
        m = calc_gross_margin(1000, 0, 0, 0, 0)
        assert m == Decimal("1.000000")

    def test_negative_margin(self):
        m = calc_gross_margin(100, 50, 50, 50, 50)
        assert m < 0

    def test_contract_zero_raises(self):
        with pytest.raises(ValueError):
            calc_gross_margin(0, 10, 10, 10, 10)

    def test_contract_negative_raises(self):
        with pytest.raises(ValueError):
            calc_gross_margin(-100, 10, 10, 10, 10)

    def test_decimal_input(self):
        m = calc_gross_margin(Decimal("1000"), Decimal("200"), Decimal("100"), Decimal("50"), Decimal("50"))
        assert m == Decimal("0.600000")

    def test_float_input(self):
        m = calc_gross_margin(1000.0, 200.0, 100.0, 50.0, 50.0)
        assert m == Decimal("0.600000")

    def test_break_even(self):
        m = calc_gross_margin(100, 25, 25, 25, 25)
        assert m == Decimal("0.000000")

    def test_tiny_margin(self):
        m = calc_gross_margin(1000, 300, 300, 300, 99)
        assert m > 0

    def test_large_amounts(self):
        m = calc_gross_margin(10_000_000, 2_000_000, 1_000_000, 500_000, 500_000)
        assert m == Decimal("0.600000")


class TestIsWarningRequired:
    def test_below_threshold(self):
        assert is_warning_required(0.19) is True

    def test_at_threshold(self):
        assert is_warning_required(0.20) is False

    def test_above_threshold(self):
        assert is_warning_required(0.21) is False

    def test_zero(self):
        assert is_warning_required(0) is True

    def test_negative(self):
        assert is_warning_required(-0.1) is True

    def test_decimal_input(self):
        assert is_warning_required(Decimal("0.199")) is True


class TestRequiresGmApproval:
    def test_below_threshold(self):
        assert requires_gm_approval(0.09) is True

    def test_at_threshold(self):
        assert requires_gm_approval(0.10) is False

    def test_above_threshold(self):
        assert requires_gm_approval(0.15) is False

    def test_negative(self):
        assert requires_gm_approval(-0.05) is True


# ---- 2. 套件率 ----

class TestCalcKitRate:
    def test_normal(self):
        r = calc_kit_rate(95, 100)
        assert r == Decimal("0.950000")

    def test_full(self):
        r = calc_kit_rate(100, 100)
        assert r == Decimal("1.000000")

    def test_over(self):
        r = calc_kit_rate(110, 100)
        assert r > 1

    def test_zero_bom_raises(self):
        with pytest.raises(ValueError):
            calc_kit_rate(10, 0)

    def test_negative_bom_raises(self):
        with pytest.raises(ValueError):
            calc_kit_rate(10, -5)

    def test_zero_actual(self):
        r = calc_kit_rate(0, 100)
        assert r == Decimal("0.000000")

    def test_decimal_input(self):
        r = calc_kit_rate(Decimal("95"), Decimal("100"))
        assert r == Decimal("0.950000")


class TestShouldTriggerShortageAlert:
    def test_below_target(self):
        assert should_trigger_shortage_alert(0.94) is True

    def test_at_target(self):
        assert should_trigger_shortage_alert(0.95) is False

    def test_above_target(self):
        assert should_trigger_shortage_alert(0.96) is False

    def test_zero(self):
        assert should_trigger_shortage_alert(0) is True


# ---- 3. SPI ----

class TestCalcSpi:
    def test_normal(self):
        spi = calc_spi(90, 100)
        assert spi == Decimal("0.900000")

    def test_ahead(self):
        spi = calc_spi(110, 100)
        assert spi > 1

    def test_zero_pv_raises(self):
        with pytest.raises(ValueError):
            calc_spi(50, 0)

    def test_negative_pv_raises(self):
        with pytest.raises(ValueError):
            calc_spi(50, -10)

    def test_zero_ev(self):
        spi = calc_spi(0, 100)
        assert spi == Decimal("0.000000")


class TestGetDelayAlertLevel:
    def test_none(self):
        assert get_delay_alert_level(0.95) == "NONE"

    def test_at_warning_boundary(self):
        assert get_delay_alert_level(0.90) == "NONE"

    def test_warning(self):
        assert get_delay_alert_level(0.89) == "WARNING"

    def test_at_urgent_boundary(self):
        assert get_delay_alert_level(0.80) == "WARNING"

    def test_urgent(self):
        assert get_delay_alert_level(0.79) == "URGENT"

    def test_zero(self):
        assert get_delay_alert_level(0) == "URGENT"

    def test_above_one(self):
        assert get_delay_alert_level(1.5) == "NONE"


# ---- 4. 付款 ----

class TestCreateStandardPaymentMilestones:
    def test_normal(self):
        ms = create_standard_payment_milestones(100000)
        assert len(ms) == 4
        total = sum(m.amount for m in ms)
        assert total == Decimal("100000")

    def test_stages(self):
        ms = create_standard_payment_milestones(100000)
        stages = [m.stage for m in ms]
        assert "签约款" in stages
        assert "质保款" in stages

    def test_ratios(self):
        ms = create_standard_payment_milestones(100000)
        assert ms[0].ratio == Decimal("0.30")
        assert ms[3].ratio == Decimal("0.10")

    def test_zero_raises(self):
        with pytest.raises(ValueError):
            create_standard_payment_milestones(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            create_standard_payment_milestones(-100)

    def test_small_amount(self):
        ms = create_standard_payment_milestones(1)
        total = sum(m.amount for m in ms)
        assert total == Decimal("1")

    def test_decimal_input(self):
        ms = create_standard_payment_milestones(Decimal("100000.50"))
        total = sum(m.amount for m in ms)
        assert total == Decimal("100000.50")

    def test_trigger_fields(self):
        ms = create_standard_payment_milestones(10000)
        assert all(m.trigger for m in ms)


class TestCalcPaymentOverdueDays:
    def test_overdue(self):
        assert calc_payment_overdue_days(date(2024, 1, 1), date(2024, 1, 11)) == 10

    def test_not_overdue(self):
        assert calc_payment_overdue_days(date(2024, 1, 11), date(2024, 1, 1)) == 0

    def test_same_day(self):
        assert calc_payment_overdue_days(date(2024, 1, 1), date(2024, 1, 1)) == 0


class TestIsOverdueEscalationRequired:
    def test_below(self):
        assert is_overdue_escalation_required(30) is False

    def test_above(self):
        assert is_overdue_escalation_required(31) is True

    def test_zero(self):
        assert is_overdue_escalation_required(0) is False


# ---- 5. 工时 ----

class TestIsDailyOvertime:
    def test_normal(self):
        assert is_daily_overtime(8) is False

    def test_at_threshold(self):
        assert is_daily_overtime(10) is False

    def test_above_threshold(self):
        assert is_daily_overtime(10.1) is True

    def test_zero(self):
        assert is_daily_overtime(0) is False


class TestShouldHrReview:
    def test_normal(self):
        assert should_hr_review(200) is False

    def test_at_threshold(self):
        assert should_hr_review(220) is False

    def test_above(self):
        assert should_hr_review(221) is True


# ---- 6. FAT 验收 ----

class TestEvaluateFatResult:
    def test_all_pass(self):
        items = [
            {"name": "A", "result": "PASS", "level": "CRITICAL"},
            {"name": "B", "result": "PASS", "level": "MAJOR"},
        ]
        r = evaluate_fat_result(items)
        assert r.status == "PASSED"
        assert r.can_ship is True
        assert len(r.failed_items) == 0

    def test_critical_fail(self):
        items = [
            {"name": "A", "result": "FAIL", "level": "CRITICAL"},
            {"name": "B", "result": "PASS", "level": "MINOR"},
        ]
        r = evaluate_fat_result(items)
        assert r.status == "FAILED"
        assert r.can_ship is False
        assert "A" in r.failed_items

    def test_major_fail(self):
        items = [
            {"name": "X", "result": "FAIL", "level": "MAJOR"},
        ]
        r = evaluate_fat_result(items)
        assert r.status == "FAILED"
        assert r.can_ship is False

    def test_minor_only_fail(self):
        items = [
            {"name": "M1", "result": "FAIL", "level": "MINOR"},
            {"name": "M2", "result": "PASS", "level": "CRITICAL"},
        ]
        r = evaluate_fat_result(items)
        assert r.status == "CONDITIONAL_PASS"
        assert r.can_ship is True
        assert "M1" in r.conditional_items

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            evaluate_fat_result([])

    def test_no_level_defaults_minor(self):
        items = [{"name": "X", "result": "FAIL"}]
        r = evaluate_fat_result(items)
        assert r.status == "CONDITIONAL_PASS"

    def test_no_name_defaults(self):
        items = [{"result": "FAIL", "level": "CRITICAL"}]
        r = evaluate_fat_result(items)
        assert r.status == "FAILED"
        assert "未知测试项" in r.failed_items

    def test_mixed_failures(self):
        items = [
            {"name": "C1", "result": "FAIL", "level": "CRITICAL"},
            {"name": "M1", "result": "FAIL", "level": "MINOR"},
            {"name": "P1", "result": "PASS", "level": "MAJOR"},
        ]
        r = evaluate_fat_result(items)
        assert r.status == "FAILED"
        assert r.can_ship is False
        assert len(r.failed_items) == 2


# ---- 7. 最终毛利 ----

class TestCalcFinalMargin:
    def test_normal(self):
        data = {"contract_amount": 1000, "costs": {"hardware": 200, "labor": 100}}
        assert calc_final_margin(data) == pytest.approx(0.7)

    def test_no_costs(self):
        data = {"contract_amount": 1000, "costs": {}}
        assert calc_final_margin(data) == 1.0

    def test_zero_contract_raises(self):
        with pytest.raises(ValueError):
            calc_final_margin({"contract_amount": 0, "costs": {}})

    def test_negative_margin(self):
        data = {"contract_amount": 100, "costs": {"total": 200}}
        assert calc_final_margin(data) < 0

    def test_no_costs_key(self):
        data = {"contract_amount": 100}
        assert calc_final_margin(data) == 1.0


class TestRequiresMarginReview:
    def test_below(self):
        assert requires_margin_review(0.19) is True

    def test_at(self):
        assert requires_margin_review(0.20) is False

    def test_above(self):
        assert requires_margin_review(0.30) is False


# ---- 8. 延期分析 ----

class TestAnalyzeDelayRootCauses:
    def test_empty(self):
        assert analyze_delay_root_causes([]) == []

    def test_single(self):
        delays = [{"reason": "缺料", "days": 5, "project_id": 1}]
        r = analyze_delay_root_causes(delays)
        assert len(r) == 1
        assert r[0]["reason"] == "缺料"
        assert r[0]["frequency"] == 1
        assert r[0]["total_days"] == 5
        assert r[0]["avg_days"] == 5.0

    def test_multiple_same_reason(self):
        delays = [
            {"reason": "缺料", "days": 5},
            {"reason": "缺料", "days": 10},
        ]
        r = analyze_delay_root_causes(delays)
        assert r[0]["frequency"] == 2
        assert r[0]["total_days"] == 15
        assert r[0]["avg_days"] == 7.5

    def test_sorted_by_frequency(self):
        delays = [
            {"reason": "A", "days": 1},
            {"reason": "B", "days": 1},
            {"reason": "B", "days": 2},
        ]
        r = analyze_delay_root_causes(delays)
        assert r[0]["reason"] == "B"
        assert r[1]["reason"] == "A"

    def test_no_reason_key(self):
        delays = [{"days": 5}]
        r = analyze_delay_root_causes(delays)
        assert r[0]["reason"] == "未知原因"

    def test_no_days_key(self):
        delays = [{"reason": "X"}]
        r = analyze_delay_root_causes(delays)
        assert r[0]["total_days"] == 0


class TestRecalculateDeliveryDate:
    def test_normal(self):
        d = recalculate_delivery_date(date(2024, 1, 1), 10)
        assert d == date(2024, 1, 11)

    def test_zero_delay(self):
        d = recalculate_delivery_date(date(2024, 1, 1), 0)
        assert d == date(2024, 1, 1)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            recalculate_delivery_date(date(2024, 1, 1), -1)

    def test_cross_month(self):
        d = recalculate_delivery_date(date(2024, 1, 25), 10)
        assert d == date(2024, 2, 4)


# ---- 9. BOM 套件率 & 缺料预警 ----

class TestCalcBomKitRate:
    def test_full(self):
        items = [{"material": "A", "required": 10, "available": 10}]
        assert calc_bom_kit_rate(items) == 1.0

    def test_partial(self):
        items = [
            {"material": "A", "required": 10, "available": 10},
            {"material": "B", "required": 10, "available": 5},
        ]
        assert calc_bom_kit_rate(items) == 0.5

    def test_over_available_capped(self):
        items = [{"material": "A", "required": 10, "available": 20}]
        assert calc_bom_kit_rate(items) == 1.0

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            calc_bom_kit_rate([])

    def test_zero_required_raises(self):
        with pytest.raises(ValueError):
            calc_bom_kit_rate([{"material": "A", "required": 0, "available": 5}])

    def test_zero_available(self):
        items = [{"material": "A", "required": 10, "available": 0}]
        assert calc_bom_kit_rate(items) == 0.0


class TestGenerateShortageAlert:
    def test_no_alert_when_full(self):
        items = [{"material": "A", "required": 10, "available": 10}]
        assert generate_shortage_alert(items, 1) is None

    def test_no_alert_at_95(self):
        items = [{"material": "A", "required": 100, "available": 95}]
        assert generate_shortage_alert(items, 1) is None

    def test_warning_alert(self):
        items = [{"material": "A", "required": 100, "available": 90}]
        alert = generate_shortage_alert(items, 1)
        assert alert is not None
        assert alert.severity == "WARNING"
        assert alert.project_id == 1
        assert "A" in alert.missing_materials

    def test_critical_alert_zero_stock(self):
        items = [
            {"material": "A", "required": 10, "available": 0},
            {"material": "B", "required": 10, "available": 10},
        ]
        alert = generate_shortage_alert(items, 42)
        assert alert is not None
        assert alert.severity == "CRITICAL"
        assert alert.project_id == 42

    def test_details_populated(self):
        items = [{"material": "X", "required": 10, "available": 5}]
        alert = generate_shortage_alert(items, 1)
        assert len(alert.details) == 1
        assert alert.details[0]["shortage"] == 5

    def test_multiple_missing(self):
        items = [
            {"material": "A", "required": 10, "available": 5},
            {"material": "B", "required": 10, "available": 3},
        ]
        alert = generate_shortage_alert(items, 1)
        assert len(alert.missing_materials) == 2


# ---- KPI Benchmarks ----

class TestKPIBenchmarks:
    def test_all_keys_exist(self):
        keys = [
            "gross_margin_warning", "gross_margin_gm_approval",
            "kit_rate_target", "spi_warning", "spi_urgent",
            "payment_overdue_escalation_days",
            "daily_overtime_threshold", "monthly_hr_review_threshold",
        ]
        for k in keys:
            assert k in KPI_BENCHMARKS

    def test_payment_milestone_dataclass(self):
        pm = PaymentMilestone(stage="test", ratio=Decimal("0.3"), amount=Decimal("300"))
        assert pm.stage == "test"
        assert pm.trigger == ""

    def test_standard_ratios_sum_to_one(self):
        total = sum(r["ratio"] for r in STANDARD_PAYMENT_RATIOS)
        assert total == Decimal("1.00")
