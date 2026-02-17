# -*- coding: utf-8 -*-
"""
D1组：核心业务规则深度测试

目标：验证每条业务规则的正确性、边界值和异常路径。
不追求覆盖率数字，而是确保每个断言都有实际业务意义。

业务规则覆盖：
1. 毛利率计算规则（Gross Margin）
2. 套件率计算规则（Kit Rate）
3. 项目延期预警规则（SPI / Schedule Performance）
4. 付款节点验证（Payment Milestone）
5. 工时异常检测（Overtime Detection）
"""

from datetime import date
from decimal import Decimal

import pytest

from app.services.business_rules import (
    # 毛利率
    KPI_BENCHMARKS,
    calc_gross_margin,
    is_warning_required,
    requires_gm_approval,
    # 套件率
    calc_kit_rate,
    should_trigger_shortage_alert,
    # 进度绩效
    calc_spi,
    get_delay_alert_level,
    # 付款节点
    PaymentMilestone,
    create_standard_payment_milestones,
    calc_payment_overdue_days,
    is_overdue_escalation_required,
    # 工时
    is_daily_overtime,
    should_hr_review,
)


# ===========================================================================
# 1. 毛利率计算规则
# ===========================================================================


class TestGrossMarginCalculation:
    """
    业务规则：
      毛利率 = (合同金额 - 硬件成本 - 人工成本 - 外协费 - 差旅费) / 合同金额
      毛利率 < 20%  → 预警
      毛利率 < 10%  → 需总经理审批
    """

    def test_gross_margin_normal_above_20_percent(self):
        """
        正常路径：毛利率 25%，不触发任何预警。
        典型的标准项目成本结构。
        """
        # (200000 - 100000 - 20000 - 10000 - 20000) / 200000 = 50000/200000 = 25%
        margin = calc_gross_margin(
            contract=200000,
            hardware=100000,
            labor=20000,
            outsource=10000,
            travel=20000,
        )
        assert margin == pytest.approx(Decimal("0.25"), abs=Decimal("0.001"))
        assert is_warning_required(margin) is False
        assert requires_gm_approval(margin) is False

    def test_gross_margin_warning_threshold_below_20(self):
        """
        边界值（低于20%警戒线）：毛利率17%，必须触发预警，但不需总经理审批。
        实际非标项目常见：硬件成本高、外协比例大。
        """
        # (100000 - 65000 - 15000 - 2000 - 1000) / 100000 = 17000/100000 = 17%
        margin = calc_gross_margin(
            contract=100000,
            hardware=65000,
            labor=15000,
            outsource=2000,
            travel=1000,
        )
        assert margin == pytest.approx(Decimal("0.17"), abs=Decimal("0.001"))
        assert is_warning_required(margin) is True, "毛利率17% < 20%，必须触发预警"
        assert requires_gm_approval(margin) is False, "17% > 10%，不需总经理审批"

    def test_gross_margin_exactly_at_20_percent_boundary(self):
        """
        精确边界：毛利率恰好等于20%时，不触发预警（规则为严格小于）。
        边界值测试，确认 < 而非 <= 的语义。
        """
        # (100000 - 60000 - 15000 - 3000 - 2000) / 100000 = 20000/100000 = 20%
        margin = calc_gross_margin(
            contract=100000,
            hardware=60000,
            labor=15000,
            outsource=3000,
            travel=2000,
        )
        assert margin == pytest.approx(Decimal("0.20"), abs=Decimal("0.001"))
        # 业务规则：< 20% 才预警，等于20%不预警
        assert is_warning_required(margin) is False, "毛利率恰好20%不应触发预警"

    def test_gross_margin_gm_approval_required_below_10(self):
        """
        高风险路径：毛利率低于10%，必须触发预警且需总经理审批。
        此场景意味着项目大幅亏损风险，需高级管理层把关。
        """
        # (100000 - 78000 - 15000 - 5000 - 2000) / 100000 = 0/100000 = 0%
        # 调整：(100000 - 78000 - 12000 - 4000 - 1000) / 100000 = 5000/100000 = 5%
        margin = calc_gross_margin(
            contract=100000,
            hardware=78000,
            labor=12000,
            outsource=4000,
            travel=1000,
        )
        assert margin < Decimal("0.10"), f"期望毛利率<10%，实际={margin}"
        assert is_warning_required(margin) is True, "毛利率<10%也应触发预警（<20%的子集）"
        assert requires_gm_approval(margin) is True, "毛利率<10%必须总经理审批"

    def test_gross_margin_negative_raises_no_error(self):
        """
        极端情况：严重亏损（毛利率为负）。
        系统不应抛异常，应正确返回负值，并触发两级预警。
        """
        # 成本远超合同，倒贴场景
        margin = calc_gross_margin(
            contract=100000,
            hardware=90000,
            labor=20000,
            outsource=5000,
            travel=3000,
        )
        assert margin < Decimal("0"), "成本超过合同应返回负毛利率"
        assert is_warning_required(margin) is True
        assert requires_gm_approval(margin) is True

    def test_gross_margin_zero_contract_raises_value_error(self):
        """
        异常输入：合同金额为0时应抛出 ValueError，防止除零错误。
        """
        with pytest.raises(ValueError, match="合同金额"):
            calc_gross_margin(contract=0, hardware=0, labor=0, outsource=0, travel=0)


# ===========================================================================
# 2. 套件率（Kit Rate）计算规则
# ===========================================================================


class TestKitRateCalculation:
    """
    业务规则：
      套件率 = 实际领料数量 / BOM 需求数量
      套件率 < 95%  → 触发缺料预警，影响排程
    """

    def test_kit_rate_shortage_alert_below_95(self):
        """
        缺料场景：套件率 93%，低于95%基准，必须触发缺料预警。
        生产计划无法完整启动，需紧急补料。
        """
        kit_rate = calc_kit_rate(actual_qty=93, bom_qty=100)
        assert kit_rate == pytest.approx(Decimal("0.93"), abs=Decimal("0.001"))
        assert kit_rate < KPI_BENCHMARKS["kit_rate_target"], "93% < 95% KPI目标"
        assert should_trigger_shortage_alert(kit_rate) is True

    def test_kit_rate_normal_above_95(self):
        """
        正常路径：套件率 97%，高于95%基准，不触发缺料预警。
        物料备料充足，生产可正常排程。
        """
        kit_rate = calc_kit_rate(actual_qty=97, bom_qty=100)
        assert kit_rate == pytest.approx(Decimal("0.97"), abs=Decimal("0.001"))
        assert should_trigger_shortage_alert(kit_rate) is False

    def test_kit_rate_exactly_at_95_boundary(self):
        """
        精确边界：套件率恰好等于95%，不触发预警（规则为严格小于）。
        确认边界语义正确，避免误报。
        """
        kit_rate = calc_kit_rate(actual_qty=95, bom_qty=100)
        assert kit_rate == pytest.approx(Decimal("0.95"), abs=Decimal("0.001"))
        # 恰好等于目标值，不触发预警
        assert should_trigger_shortage_alert(kit_rate) is False, \
            "套件率恰好95%不应触发预警"

    def test_kit_rate_severe_shortage_zero_actual(self):
        """
        极端缺料：实际领料为0，套件率=0，必须触发预警。
        代表物料完全未到货的情况。
        """
        kit_rate = calc_kit_rate(actual_qty=0, bom_qty=100)
        assert kit_rate == Decimal("0")
        assert should_trigger_shortage_alert(kit_rate) is True

    def test_kit_rate_zero_bom_qty_raises_value_error(self):
        """
        异常输入：BOM 需求数量为0时应抛出 ValueError。
        """
        with pytest.raises(ValueError, match="BOM"):
            calc_kit_rate(actual_qty=10, bom_qty=0)


# ===========================================================================
# 3. 项目延期预警规则
# ===========================================================================


class TestSchedulePerformanceAlert:
    """
    业务规则（基于 PMBOK EVM）：
      SPI = EV / PV
      SPI >= 0.9  → NONE（正常）
      0.8 <= SPI < 0.9 → WARNING（延期预警）
      SPI < 0.8   → URGENT（紧急预警，通知 PM）
    """

    def test_schedule_performance_urgent_at_0_8(self):
        """
        边界精确性：SPI 恰好等于 0.8 时，规则为"严格小于 0.8 才 URGENT"，
        所以 SPI=0.8 应为 WARNING（落在 0.8 <= SPI < 0.9 区间）。
        此测试验证边界不被误分类为 URGENT，避免错误触发紧急流程。
        """
        spi = calc_spi(ev=48000, pv=60000)  # EV/PV = 0.8 精确边界
        assert spi == pytest.approx(Decimal("0.8"), abs=Decimal("0.001"))
        # SPI=0.8 不严格小于 0.8，故应为 WARNING 而非 URGENT
        assert get_delay_alert_level(spi) == "WARNING", \
            "SPI=0.8 处于延期预警区间 [0.8, 0.9)，应为 WARNING 而非 URGENT"

    def test_schedule_performance_urgent_below_0_8(self):
        """
        严重延期：SPI=0.75，进度大幅落后，紧急预警。
        项目存在无法按期交付的高风险。
        """
        spi = calc_spi(ev=45000, pv=60000)  # EV/PV = 0.75
        assert spi == pytest.approx(Decimal("0.75"), abs=Decimal("0.001"))
        assert get_delay_alert_level(spi) == "URGENT"

    def test_schedule_performance_warning_between_0_8_and_0_9(self):
        """
        轻度延期：SPI=0.85（0.8 < SPI < 0.9），触发延期预警但非紧急。
        项目进度落后需关注，PM 应制定赶工计划。
        """
        spi = calc_spi(ev=51000, pv=60000)  # EV/PV = 0.85
        assert spi == pytest.approx(Decimal("0.85"), abs=Decimal("0.001"))
        assert get_delay_alert_level(spi) == "WARNING"

    def test_schedule_performance_normal_above_0_9(self):
        """
        正常路径：SPI=0.967，进度接近计划，无预警。
        正常推进中的项目，无需额外干预。
        """
        spi = calc_spi(ev=58000, pv=60000)  # SPI ≈ 0.9667
        assert spi == pytest.approx(Decimal("0.9667"), abs=Decimal("0.001"))
        assert get_delay_alert_level(spi) == "NONE"

    def test_schedule_performance_spi_above_1_excellent(self):
        """
        超前完成：SPI > 1.0，进度超前，无预警。
        """
        spi = calc_spi(ev=65000, pv=60000)  # SPI ≈ 1.083
        assert spi > Decimal("1.0")
        assert get_delay_alert_level(spi) == "NONE"

    def test_calc_spi_zero_pv_raises_value_error(self):
        """
        异常输入：计划价值为0时应抛出 ValueError。
        """
        with pytest.raises(ValueError, match="PV"):
            calc_spi(ev=1000, pv=0)


# ===========================================================================
# 4. 付款节点验证
# ===========================================================================


class TestPaymentMilestoneValidation:
    """
    业务规则（标准合同付款结构）：
      签约款 30% + 到货款 30% + 验收款 30% + 质保款 10% = 100%
      逾期超过 30 天需升级至管理层跟进
    """

    def test_payment_milestone_sum_equals_contract_amount(self):
        """
        合规验证：四个付款节点金额之和必须精确等于合同总金额。
        任何分摊误差都会造成财务核算问题。
        """
        contract_amount = 300000
        milestones = create_standard_payment_milestones(contract_amount)

        total = sum(m.amount for m in milestones)
        assert total == Decimal(str(contract_amount)), \
            f"付款节点总和 {total} 应等于合同金额 {contract_amount}"

    def test_payment_milestone_first_is_30_percent(self):
        """
        首款验证：签约款应为合同金额的30%。
        首款比例决定项目启动资金，错误会影响供应商付款计划。
        """
        milestones = create_standard_payment_milestones(300000)
        assert milestones[0].stage == "签约款"
        assert milestones[0].amount == Decimal("90000"), \
            "签约款 = 300000 × 30% = 90000"

    def test_payment_milestone_last_is_10_percent(self):
        """
        尾款验证：质保款应为合同金额的10%。
        质保款是项目最终结算的关键节点，比例错误影响项目结案。
        """
        milestones = create_standard_payment_milestones(300000)
        assert milestones[-1].stage == "质保款"
        assert milestones[-1].amount == Decimal("30000"), \
            "质保款 = 300000 × 10% = 30000"

    def test_payment_milestone_four_stages(self):
        """
        结构验证：标准合同必须包含4个付款阶段。
        """
        milestones = create_standard_payment_milestones(300000)
        assert len(milestones) == 4
        stages = [m.stage for m in milestones]
        assert stages == ["签约款", "到货款", "验收款", "质保款"]

    def test_payment_milestone_non_round_number_contract(self):
        """
        精度验证：合同金额非整数时，所有节点之和仍应精确等于合同金额。
        防止浮点拆分导致最后一笔多收或少收。
        """
        contract_amount = Decimal("123456.78")
        milestones = create_standard_payment_milestones(contract_amount)
        total = sum(m.amount for m in milestones)
        assert total == contract_amount, \
            f"非整数合同金额拆分后总和 {total} 应等于 {contract_amount}"

    def test_payment_overdue_days_calculation(self):
        """
        逾期天数计算：质保款逾期60天。
        准确的逾期天数是计算罚息和升级判断的基础。
        """
        overdue_days = calc_payment_overdue_days(
            due_date=date(2026, 1, 1),
            today=date(2026, 3, 2),
        )
        assert overdue_days == 60, f"期望60天逾期，实际={overdue_days}"

    def test_payment_overdue_escalation_required_above_30_days(self):
        """
        升级阈值：逾期超过30天需升级至管理层。
        60天逾期远超30天门槛，应触发升级流程。
        """
        overdue_days = calc_payment_overdue_days(
            due_date=date(2026, 1, 1),
            today=date(2026, 3, 2),
        )
        assert overdue_days == 60
        assert is_overdue_escalation_required(overdue_days) is True, \
            "逾期60天 > 30天阈值，必须升级"

    def test_payment_overdue_no_escalation_within_30_days(self):
        """
        正常催款期：逾期15天，尚未达到升级阈值，不升级。
        """
        overdue_days = calc_payment_overdue_days(
            due_date=date(2026, 1, 1),
            today=date(2026, 1, 16),
        )
        assert overdue_days == 15
        assert is_overdue_escalation_required(overdue_days) is False

    def test_payment_not_yet_due_returns_zero(self):
        """
        未到期：付款日期在未来，逾期天数应为0，不触发任何预警。
        """
        overdue_days = calc_payment_overdue_days(
            due_date=date(2026, 12, 31),
            today=date(2026, 2, 17),
        )
        assert overdue_days == 0
        assert is_overdue_escalation_required(overdue_days) is False

    def test_payment_exactly_30_days_overdue_no_escalation(self):
        """
        精确边界：逾期恰好30天，不触发升级（规则为严格大于30天）。
        """
        overdue_days = 30
        assert is_overdue_escalation_required(overdue_days) is False, \
            "逾期恰好30天不应升级（需 > 30天才升级）"

    def test_payment_zero_contract_raises_value_error(self):
        """
        异常输入：合同金额为0时应抛出 ValueError。
        """
        with pytest.raises(ValueError, match="合同金额"):
            create_standard_payment_milestones(0)


# ===========================================================================
# 5. 工时异常检测
# ===========================================================================


class TestOvertimeDetection:
    """
    业务规则：
      日工时 > 10 小时  → 标记异常（可能漏报/健康风险）
      月工时 > 220 小时 → 触发 HR 关注
    """

    def test_daily_overtime_above_10_hours(self):
        """
        日加班：10.5小时，超过10小时阈值，触发异常标记。
        长时间工作可能掩盖项目风险，也涉及员工健康合规。
        """
        assert is_daily_overtime(hours=10.5) is True

    def test_daily_normal_hours_no_flag(self):
        """
        正常工时：8小时，不触发任何异常标记。
        """
        assert is_daily_overtime(hours=8.0) is False

    def test_daily_overtime_exactly_at_10_hours_no_flag(self):
        """
        精确边界：日工时恰好等于10小时，不触发异常（规则为严格大于）。
        """
        assert is_daily_overtime(hours=10.0) is False, \
            "日工时恰好10小时不应标记异常（需 > 10h）"

    def test_daily_overtime_just_above_threshold(self):
        """
        微超边界：10.1小时，刚超过阈值，触发异常。
        """
        assert is_daily_overtime(hours=10.1) is True

    def test_monthly_overtime_hr_alert_above_220(self):
        """
        月度过劳：225小时，超过220小时HR关注线。
        月均每天工作约10.2小时，存在劳动合规和员工健康风险。
        """
        assert should_hr_review(monthly_hours=225) is True

    def test_monthly_normal_hours_no_hr_review(self):
        """
        月度正常：180小时，约每天8小时，无需HR关注。
        """
        assert should_hr_review(monthly_hours=180) is False

    def test_monthly_overtime_exactly_at_220_no_review(self):
        """
        精确边界：月工时恰好220小时，不触发HR关注（规则为严格大于）。
        """
        assert should_hr_review(monthly_hours=220) is False, \
            "月工时恰好220小时不应触发HR关注（需 > 220h）"

    def test_monthly_extreme_overtime_hr_review(self):
        """
        极端情况：300小时/月（相当于每天超14小时），严重过劳，必须HR关注。
        """
        assert should_hr_review(monthly_hours=300) is True


# ===========================================================================
# 6. 跨规则集成验证（现实业务场景）
# ===========================================================================


class TestCrossRuleBusinessScenarios:
    """
    模拟真实项目场景，验证多个业务规则联合运作时的一致性。
    """

    def test_high_risk_project_scenario(self):
        """
        高风险项目场景：
        - 毛利率仅8%（需总经理审批）
        - 套件率90%（缺料预警）
        - SPI=0.75（紧急进度预警）
        - 付款逾期45天（需升级）
        所有规则应联合触发，确保系统综合风险识别。
        """
        # 毛利率 8%
        margin = calc_gross_margin(
            contract=500000, hardware=400000, labor=52000, outsource=6000, travel=2000
        )
        assert requires_gm_approval(margin) is True, "8%毛利率需总经理审批"

        # 套件率 90%
        kit_rate = calc_kit_rate(actual_qty=90, bom_qty=100)
        assert should_trigger_shortage_alert(kit_rate) is True, "90%套件率触发缺料预警"

        # 进度 SPI=0.75
        spi = calc_spi(ev=45000, pv=60000)
        assert get_delay_alert_level(spi) == "URGENT", "SPI=0.75 触发紧急延期预警"

        # 付款逾期45天
        overdue = calc_payment_overdue_days(date(2026, 1, 1), date(2026, 2, 15))
        assert is_overdue_escalation_required(overdue) is True, "45天逾期需升级"

    def test_healthy_project_scenario(self):
        """
        健康项目场景：所有指标均在正常范围内，不触发任何预警。
        """
        # 毛利率 30%
        margin = calc_gross_margin(
            contract=300000, hardware=150000, labor=30000, outsource=10000, travel=20000
        )
        assert is_warning_required(margin) is False
        assert requires_gm_approval(margin) is False

        # 套件率 98%
        kit_rate = calc_kit_rate(actual_qty=98, bom_qty=100)
        assert should_trigger_shortage_alert(kit_rate) is False

        # 进度正常 SPI=1.0
        spi = calc_spi(ev=60000, pv=60000)
        assert get_delay_alert_level(spi) == "NONE"

        # 付款准时
        overdue = calc_payment_overdue_days(date(2026, 3, 1), date(2026, 2, 17))
        assert overdue == 0
        assert is_overdue_escalation_required(overdue) is False

        # 工时正常
        assert is_daily_overtime(hours=8.5) is False
        assert should_hr_review(monthly_hours=190) is False
