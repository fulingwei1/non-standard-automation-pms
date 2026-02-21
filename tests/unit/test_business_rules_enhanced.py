# -*- coding: utf-8 -*-
"""
business_rules.py 增强单元测试

测试覆盖：
1. 毛利率计算规则（calc_gross_margin, is_warning_required, requires_gm_approval）
2. 套件率计算规则（calc_kit_rate, should_trigger_shortage_alert）
3. 项目延期预警规则（calc_spi, get_delay_alert_level）
4. 付款节点验证（create_standard_payment_milestones, calc_payment_overdue_days, is_overdue_escalation_required）
5. 工时异常检测（is_daily_overtime, should_hr_review）
6. FAT/SAT 验收判定规则（evaluate_fat_result）
7. 项目最终毛利核算（calc_final_margin, requires_margin_review）
8. 工期偏差分析（analyze_delay_root_causes, recalculate_delivery_date）
9. BOM 套件率计算 & 缺料预警（calc_bom_kit_rate, generate_shortage_alert）
"""

import unittest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.business_rules import (
    KPI_BENCHMARKS,
    # 1. 毛利率
    calc_gross_margin,
    is_warning_required,
    requires_gm_approval,
    # 2. 套件率
    calc_kit_rate,
    should_trigger_shortage_alert,
    # 3. 项目延期预警
    calc_spi,
    get_delay_alert_level,
    # 4. 付款节点
    PaymentMilestone,
    create_standard_payment_milestones,
    calc_payment_overdue_days,
    is_overdue_escalation_required,
    # 5. 工时
    is_daily_overtime,
    should_hr_review,
    # 6. FAT
    FATResult,
    evaluate_fat_result,
    # 7. 最终毛利
    calc_final_margin,
    requires_margin_review,
    # 8. 工期偏差
    analyze_delay_root_causes,
    recalculate_delivery_date,
    # 9. BOM 套件率 & 缺料预警
    ShortageAlert,
    calc_bom_kit_rate,
    generate_shortage_alert,
)


# ===========================================================================
# 1. 毛利率计算规则测试
# ===========================================================================

class TestGrossMarginRules(unittest.TestCase):
    """毛利率计算规则测试类"""

    def test_calc_gross_margin_normal(self):
        """测试正常毛利率计算"""
        # 合同金额 100万，各项成本共 70万，毛利率 30%
        margin = calc_gross_margin(
            contract=1_000_000,
            hardware=300_000,
            labor=200_000,
            outsource=100_000,
            travel=100_000,
        )
        self.assertEqual(margin, Decimal("0.30"))

    def test_calc_gross_margin_zero_profit(self):
        """测试零毛利（成本等于合同金额）"""
        margin = calc_gross_margin(
            contract=1_000_000,
            hardware=400_000,
            labor=300_000,
            outsource=200_000,
            travel=100_000,
        )
        self.assertEqual(margin, Decimal("0.0"))

    def test_calc_gross_margin_negative_profit(self):
        """测试负毛利（成本超过合同金额）"""
        margin = calc_gross_margin(
            contract=1_000_000,
            hardware=500_000,
            labor=400_000,
            outsource=200_000,
            travel=100_000,
        )
        self.assertEqual(margin, Decimal("-0.2"))

    def test_calc_gross_margin_invalid_contract_zero(self):
        """测试合同金额为0时抛出异常"""
        with self.assertRaises(ValueError) as ctx:
            calc_gross_margin(
                contract=0,
                hardware=100,
                labor=100,
                outsource=50,
                travel=50,
            )
        self.assertIn("合同金额必须大于 0", str(ctx.exception))

    def test_calc_gross_margin_invalid_contract_negative(self):
        """测试合同金额为负数时抛出异常"""
        with self.assertRaises(ValueError):
            calc_gross_margin(
                contract=-1000,
                hardware=100,
                labor=100,
                outsource=50,
                travel=50,
            )

    def test_is_warning_required_below_threshold(self):
        """测试毛利率低于20%触发预警"""
        self.assertTrue(is_warning_required(0.15))
        self.assertTrue(is_warning_required(0.19))

    def test_is_warning_required_above_threshold(self):
        """测试毛利率高于20%不触发预警"""
        self.assertFalse(is_warning_required(0.20))
        self.assertFalse(is_warning_required(0.25))

    def test_requires_gm_approval_below_10_percent(self):
        """测试毛利率低于10%需要总经理审批"""
        self.assertTrue(requires_gm_approval(0.05))
        self.assertTrue(requires_gm_approval(0.09))

    def test_requires_gm_approval_above_10_percent(self):
        """测试毛利率高于10%不需要总经理审批"""
        self.assertFalse(requires_gm_approval(0.10))
        self.assertFalse(requires_gm_approval(0.15))


# ===========================================================================
# 2. 套件率计算规则测试
# ===========================================================================

class TestKitRateRules(unittest.TestCase):
    """套件率计算规则测试类"""

    def test_calc_kit_rate_normal(self):
        """测试正常套件率计算"""
        kit_rate = calc_kit_rate(actual_qty=95, bom_qty=100)
        self.assertEqual(kit_rate, Decimal("0.95"))

    def test_calc_kit_rate_full(self):
        """测试满足率100%"""
        kit_rate = calc_kit_rate(actual_qty=100, bom_qty=100)
        self.assertEqual(kit_rate, Decimal("1.0"))

    def test_calc_kit_rate_excess(self):
        """测试超配（实际数量大于BOM需求）"""
        kit_rate = calc_kit_rate(actual_qty=120, bom_qty=100)
        self.assertEqual(kit_rate, Decimal("1.2"))

    def test_calc_kit_rate_zero_actual(self):
        """测试实际数量为0"""
        kit_rate = calc_kit_rate(actual_qty=0, bom_qty=100)
        self.assertEqual(kit_rate, Decimal("0.0"))

    def test_calc_kit_rate_invalid_bom_zero(self):
        """测试BOM需求数量为0时抛出异常"""
        with self.assertRaises(ValueError) as ctx:
            calc_kit_rate(actual_qty=100, bom_qty=0)
        self.assertIn("BOM 需求数量必须大于 0", str(ctx.exception))

    def test_calc_kit_rate_invalid_bom_negative(self):
        """测试BOM需求数量为负数时抛出异常"""
        with self.assertRaises(ValueError):
            calc_kit_rate(actual_qty=100, bom_qty=-10)

    def test_should_trigger_shortage_alert_below_95(self):
        """测试套件率低于95%触发缺料预警"""
        self.assertTrue(should_trigger_shortage_alert(0.90))
        self.assertTrue(should_trigger_shortage_alert(0.94))

    def test_should_trigger_shortage_alert_above_95(self):
        """测试套件率高于95%不触发缺料预警"""
        self.assertFalse(should_trigger_shortage_alert(0.95))
        self.assertFalse(should_trigger_shortage_alert(1.0))


# ===========================================================================
# 3. 项目延期预警规则测试
# ===========================================================================

class TestDelayAlertRules(unittest.TestCase):
    """项目延期预警规则测试类"""

    def test_calc_spi_normal(self):
        """测试正常SPI计算"""
        spi = calc_spi(ev=90, pv=100)
        self.assertEqual(spi, Decimal("0.9"))

    def test_calc_spi_ahead_of_schedule(self):
        """测试进度超前（SPI > 1）"""
        spi = calc_spi(ev=110, pv=100)
        self.assertEqual(spi, Decimal("1.1"))

    def test_calc_spi_on_schedule(self):
        """测试进度符合计划（SPI = 1）"""
        spi = calc_spi(ev=100, pv=100)
        self.assertEqual(spi, Decimal("1.0"))

    def test_calc_spi_invalid_pv_zero(self):
        """测试计划价值为0时抛出异常"""
        with self.assertRaises(ValueError) as ctx:
            calc_spi(ev=100, pv=0)
        self.assertIn("计划价值 (PV) 必须大于 0", str(ctx.exception))

    def test_calc_spi_invalid_pv_negative(self):
        """测试计划价值为负数时抛出异常"""
        with self.assertRaises(ValueError):
            calc_spi(ev=100, pv=-50)

    def test_get_delay_alert_level_none(self):
        """测试SPI >= 0.9时返回NONE"""
        self.assertEqual(get_delay_alert_level(0.9), "NONE")
        self.assertEqual(get_delay_alert_level(1.0), "NONE")
        self.assertEqual(get_delay_alert_level(1.1), "NONE")

    def test_get_delay_alert_level_warning(self):
        """测试0.8 <= SPI < 0.9时返回WARNING"""
        self.assertEqual(get_delay_alert_level(0.8), "WARNING")
        self.assertEqual(get_delay_alert_level(0.85), "WARNING")
        self.assertEqual(get_delay_alert_level(0.89), "WARNING")

    def test_get_delay_alert_level_urgent(self):
        """测试SPI < 0.8时返回URGENT"""
        self.assertEqual(get_delay_alert_level(0.79), "URGENT")
        self.assertEqual(get_delay_alert_level(0.5), "URGENT")
        self.assertEqual(get_delay_alert_level(0.1), "URGENT")


# ===========================================================================
# 4. 付款节点验证测试
# ===========================================================================

class TestPaymentMilestoneRules(unittest.TestCase):
    """付款节点验证测试类"""

    def test_create_standard_payment_milestones_normal(self):
        """测试标准付款里程碑生成"""
        milestones = create_standard_payment_milestones(1_000_000)
        self.assertEqual(len(milestones), 4)
        self.assertEqual(milestones[0].stage, "签约款")
        self.assertEqual(milestones[0].amount, Decimal("300000.00"))
        self.assertEqual(milestones[1].stage, "到货款")
        self.assertEqual(milestones[1].amount, Decimal("300000.00"))
        self.assertEqual(milestones[2].stage, "验收款")
        self.assertEqual(milestones[2].amount, Decimal("300000.00"))
        self.assertEqual(milestones[3].stage, "质保款")
        self.assertEqual(milestones[3].amount, Decimal("100000.00"))

    def test_create_standard_payment_milestones_sum_equals_contract(self):
        """测试付款里程碑总额等于合同金额"""
        milestones = create_standard_payment_milestones(1_234_567.89)
        total = sum(m.amount for m in milestones)
        self.assertEqual(total, Decimal("1234567.89"))

    def test_create_standard_payment_milestones_invalid_amount_zero(self):
        """测试合同金额为0时抛出异常"""
        with self.assertRaises(ValueError) as ctx:
            create_standard_payment_milestones(0)
        self.assertIn("合同金额必须大于 0", str(ctx.exception))

    def test_create_standard_payment_milestones_invalid_amount_negative(self):
        """测试合同金额为负数时抛出异常"""
        with self.assertRaises(ValueError):
            create_standard_payment_milestones(-100000)

    def test_calc_payment_overdue_days_overdue(self):
        """测试逾期天数计算"""
        due_date = date(2024, 1, 1)
        today = date(2024, 1, 31)
        overdue = calc_payment_overdue_days(due_date, today)
        self.assertEqual(overdue, 30)

    def test_calc_payment_overdue_days_not_overdue(self):
        """测试未逾期情况"""
        due_date = date(2024, 1, 31)
        today = date(2024, 1, 1)
        overdue = calc_payment_overdue_days(due_date, today)
        self.assertEqual(overdue, 0)

    def test_calc_payment_overdue_days_on_due_date(self):
        """测试到期当天（未逾期）"""
        due_date = date(2024, 1, 15)
        today = date(2024, 1, 15)
        overdue = calc_payment_overdue_days(due_date, today)
        self.assertEqual(overdue, 0)

    def test_is_overdue_escalation_required_below_threshold(self):
        """测试逾期天数低于30天不需要升级"""
        self.assertFalse(is_overdue_escalation_required(15))
        self.assertFalse(is_overdue_escalation_required(30))

    def test_is_overdue_escalation_required_above_threshold(self):
        """测试逾期天数超过30天需要升级"""
        self.assertTrue(is_overdue_escalation_required(31))
        self.assertTrue(is_overdue_escalation_required(60))


# ===========================================================================
# 5. 工时异常检测测试
# ===========================================================================

class TestOvertimeRules(unittest.TestCase):
    """工时异常检测测试类"""

    def test_is_daily_overtime_normal(self):
        """测试正常工时不触发异常"""
        self.assertFalse(is_daily_overtime(8))
        self.assertFalse(is_daily_overtime(10))

    def test_is_daily_overtime_exceed_threshold(self):
        """测试超过10小时触发异常"""
        self.assertTrue(is_daily_overtime(10.1))
        self.assertTrue(is_daily_overtime(12))

    def test_should_hr_review_normal(self):
        """测试正常月工时不需要HR关注"""
        self.assertFalse(should_hr_review(200))
        self.assertFalse(should_hr_review(220))

    def test_should_hr_review_exceed_threshold(self):
        """测试超过220小时需要HR关注"""
        self.assertTrue(should_hr_review(220.1))
        self.assertTrue(should_hr_review(250))


# ===========================================================================
# 6. FAT/SAT 验收判定规则测试
# ===========================================================================

class TestFATRules(unittest.TestCase):
    """FAT验收判定规则测试类"""

    def test_evaluate_fat_result_all_passed(self):
        """测试所有测试项通过"""
        test_items = [
            {"name": "功能测试1", "result": "PASS", "level": "CRITICAL"},
            {"name": "功能测试2", "result": "PASS", "level": "MAJOR"},
            {"name": "功能测试3", "result": "PASS", "level": "MINOR"},
        ]
        result = evaluate_fat_result(test_items)
        self.assertEqual(result.status, "PASSED")
        self.assertTrue(result.can_ship)
        self.assertEqual(len(result.failed_items), 0)
        self.assertEqual(len(result.conditional_items), 0)

    def test_evaluate_fat_result_critical_failed(self):
        """测试CRITICAL项失败"""
        test_items = [
            {"name": "安全测试", "result": "FAIL", "level": "CRITICAL"},
            {"name": "功能测试", "result": "PASS", "level": "MAJOR"},
        ]
        result = evaluate_fat_result(test_items)
        self.assertEqual(result.status, "FAILED")
        self.assertFalse(result.can_ship)
        self.assertIn("安全测试", result.failed_items)

    def test_evaluate_fat_result_major_failed(self):
        """测试MAJOR项失败"""
        test_items = [
            {"name": "核心功能", "result": "FAIL", "level": "MAJOR"},
            {"name": "次要功能", "result": "PASS", "level": "MINOR"},
        ]
        result = evaluate_fat_result(test_items)
        self.assertEqual(result.status, "FAILED")
        self.assertFalse(result.can_ship)
        self.assertIn("核心功能", result.failed_items)

    def test_evaluate_fat_result_minor_failed_only(self):
        """测试仅MINOR项失败（有条件通过）"""
        test_items = [
            {"name": "核心功能", "result": "PASS", "level": "CRITICAL"},
            {"name": "UI显示", "result": "FAIL", "level": "MINOR"},
        ]
        result = evaluate_fat_result(test_items)
        self.assertEqual(result.status, "CONDITIONAL_PASS")
        self.assertTrue(result.can_ship)
        self.assertEqual(len(result.failed_items), 0)
        self.assertIn("UI显示", result.conditional_items)

    def test_evaluate_fat_result_multiple_failures(self):
        """测试多项失败"""
        test_items = [
            {"name": "安全测试", "result": "FAIL", "level": "CRITICAL"},
            {"name": "性能测试", "result": "FAIL", "level": "MAJOR"},
            {"name": "UI测试", "result": "FAIL", "level": "MINOR"},
        ]
        result = evaluate_fat_result(test_items)
        self.assertEqual(result.status, "FAILED")
        self.assertFalse(result.can_ship)
        self.assertEqual(len(result.failed_items), 3)

    def test_evaluate_fat_result_empty_items(self):
        """测试空测试项列表抛出异常"""
        with self.assertRaises(ValueError) as ctx:
            evaluate_fat_result([])
        self.assertIn("测试项列表不能为空", str(ctx.exception))


# ===========================================================================
# 7. 项目最终毛利核算测试
# ===========================================================================

class TestFinalMarginRules(unittest.TestCase):
    """项目最终毛利核算测试类"""

    def test_calc_final_margin_normal(self):
        """测试正常毛利率核算"""
        project_data = {
            "contract_amount": 1_000_000,
            "costs": {
                "hardware": 300_000,
                "labor": 200_000,
                "outsource": 100_000,
                "travel": 50_000,
            }
        }
        margin = calc_final_margin(project_data)
        self.assertAlmostEqual(margin, 0.35, places=6)

    def test_calc_final_margin_zero_profit(self):
        """测试零毛利"""
        project_data = {
            "contract_amount": 1_000_000,
            "costs": {
                "hardware": 400_000,
                "labor": 300_000,
                "outsource": 200_000,
                "travel": 100_000,
            }
        }
        margin = calc_final_margin(project_data)
        self.assertAlmostEqual(margin, 0.0, places=6)

    def test_calc_final_margin_negative_profit(self):
        """测试负毛利"""
        project_data = {
            "contract_amount": 1_000_000,
            "costs": {
                "hardware": 500_000,
                "labor": 400_000,
                "outsource": 200_000,
                "travel": 100_000,
            }
        }
        margin = calc_final_margin(project_data)
        self.assertAlmostEqual(margin, -0.2, places=6)

    def test_calc_final_margin_invalid_contract_zero(self):
        """测试合同金额为0时抛出异常"""
        project_data = {
            "contract_amount": 0,
            "costs": {"hardware": 100}
        }
        with self.assertRaises(ValueError) as ctx:
            calc_final_margin(project_data)
        self.assertIn("合同金额必须大于 0", str(ctx.exception))

    def test_requires_margin_review_below_20(self):
        """测试毛利率低于20%需要审查"""
        self.assertTrue(requires_margin_review(0.15))
        self.assertTrue(requires_margin_review(0.19))

    def test_requires_margin_review_above_20(self):
        """测试毛利率高于20%不需要审查"""
        self.assertFalse(requires_margin_review(0.20))
        self.assertFalse(requires_margin_review(0.30))


# ===========================================================================
# 8. 工期偏差分析测试
# ===========================================================================

class TestDelayAnalysisRules(unittest.TestCase):
    """工期偏差分析测试类"""

    def test_analyze_delay_root_causes_normal(self):
        """测试延期根因分析"""
        delays = [
            {"reason": "物料延期", "days": 10, "project_id": 1},
            {"reason": "物料延期", "days": 15, "project_id": 2},
            {"reason": "设计变更", "days": 5, "project_id": 3},
            {"reason": "物料延期", "days": 20, "project_id": 4},
        ]
        result = analyze_delay_root_causes(delays)
        # 物料延期出现3次，共45天，平均15天
        self.assertEqual(result[0]["reason"], "物料延期")
        self.assertEqual(result[0]["frequency"], 3)
        self.assertEqual(result[0]["total_days"], 45)
        self.assertEqual(result[0]["avg_days"], 15.0)
        # 设计变更出现1次，共5天，平均5天
        self.assertEqual(result[1]["reason"], "设计变更")
        self.assertEqual(result[1]["frequency"], 1)
        self.assertEqual(result[1]["total_days"], 5)
        self.assertEqual(result[1]["avg_days"], 5.0)

    def test_analyze_delay_root_causes_empty_list(self):
        """测试空延期列表"""
        result = analyze_delay_root_causes([])
        self.assertEqual(len(result), 0)

    def test_analyze_delay_root_causes_sorting(self):
        """测试排序逻辑（频次优先，总天数次之）"""
        delays = [
            {"reason": "A", "days": 100, "project_id": 1},  # 1次100天
            {"reason": "B", "days": 10, "project_id": 2},   # 2次共30天
            {"reason": "B", "days": 20, "project_id": 3},
        ]
        result = analyze_delay_root_causes(delays)
        # B出现2次，应排第一
        self.assertEqual(result[0]["reason"], "B")
        self.assertEqual(result[0]["frequency"], 2)

    def test_recalculate_delivery_date_normal(self):
        """测试正常交期重算"""
        original = date(2024, 1, 1)
        new_date = recalculate_delivery_date(original, delay_days=30)
        self.assertEqual(new_date, date(2024, 1, 31))

    def test_recalculate_delivery_date_zero_delay(self):
        """测试零延期"""
        original = date(2024, 1, 1)
        new_date = recalculate_delivery_date(original, delay_days=0)
        self.assertEqual(new_date, original)

    def test_recalculate_delivery_date_invalid_negative_delay(self):
        """测试负数延期天数抛出异常"""
        original = date(2024, 1, 1)
        with self.assertRaises(ValueError) as ctx:
            recalculate_delivery_date(original, delay_days=-5)
        self.assertIn("延误天数不能为负数", str(ctx.exception))


# ===========================================================================
# 9. BOM 套件率计算 & 缺料预警测试
# ===========================================================================

class TestBOMKitRateAndShortageRules(unittest.TestCase):
    """BOM 套件率计算 & 缺料预警测试类"""

    def test_calc_bom_kit_rate_normal(self):
        """测试正常BOM综合套件率计算"""
        bom_items = [
            {"material": "电机", "required": 10, "available": 9},   # 90%
            {"material": "传感器", "required": 20, "available": 19},  # 95%
            {"material": "控制器", "required": 5, "available": 5},   # 100%
        ]
        # 最小满足率为电机的90%
        kit_rate = calc_bom_kit_rate(bom_items)
        self.assertAlmostEqual(kit_rate, 0.9, places=6)

    def test_calc_bom_kit_rate_full_availability(self):
        """测试全部满足情况"""
        bom_items = [
            {"material": "电机", "required": 10, "available": 10},
            {"material": "传感器", "required": 20, "available": 20},
        ]
        kit_rate = calc_bom_kit_rate(bom_items)
        self.assertAlmostEqual(kit_rate, 1.0, places=6)

    def test_calc_bom_kit_rate_zero_availability(self):
        """测试零库存情况"""
        bom_items = [
            {"material": "电机", "required": 10, "available": 10},
            {"material": "传感器", "required": 20, "available": 0},  # 0%
        ]
        kit_rate = calc_bom_kit_rate(bom_items)
        self.assertAlmostEqual(kit_rate, 0.0, places=6)

    def test_calc_bom_kit_rate_excess_availability(self):
        """测试超配情况（按100%计算）"""
        bom_items = [
            {"material": "电机", "required": 10, "available": 15},  # 超配，按100%计
            {"material": "传感器", "required": 20, "available": 19},  # 95%
        ]
        # 最小满足率为传感器的95%
        kit_rate = calc_bom_kit_rate(bom_items)
        self.assertAlmostEqual(kit_rate, 0.95, places=6)

    def test_calc_bom_kit_rate_empty_items(self):
        """测试空BOM列表抛出异常"""
        with self.assertRaises(ValueError) as ctx:
            calc_bom_kit_rate([])
        self.assertIn("BOM 物料列表不能为空", str(ctx.exception))

    def test_calc_bom_kit_rate_invalid_required_zero(self):
        """测试需求数量为0抛出异常"""
        bom_items = [
            {"material": "电机", "required": 0, "available": 10},
        ]
        with self.assertRaises(ValueError) as ctx:
            calc_bom_kit_rate(bom_items)
        self.assertIn("需求数量必须大于 0", str(ctx.exception))

    def test_generate_shortage_alert_no_shortage(self):
        """测试无缺料情况（套件率 >= 95%）"""
        bom_items = [
            {"material": "电机", "required": 10, "available": 10},
            {"material": "传感器", "required": 20, "available": 19},  # 95%
        ]
        alert = generate_shortage_alert(bom_items, project_id=123)
        self.assertIsNone(alert)

    def test_generate_shortage_alert_warning_level(self):
        """测试WARNING级别缺料预警"""
        bom_items = [
            {"material": "电机", "required": 10, "available": 8},   # 80%
            {"material": "传感器", "required": 20, "available": 19},  # 95%
        ]
        alert = generate_shortage_alert(bom_items, project_id=123)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, "WARNING")
        self.assertEqual(alert.project_id, 123)
        self.assertIn("电机", alert.missing_materials)
        self.assertIn("传感器", alert.missing_materials)
        self.assertEqual(len(alert.details), 2)
        # 验证电机缺2个，传感器缺1个
        details_dict = {d["material"]: d for d in alert.details}
        self.assertEqual(details_dict["电机"]["shortage"], 2)
        self.assertEqual(details_dict["传感器"]["shortage"], 1)

    def test_generate_shortage_alert_critical_level(self):
        """测试CRITICAL级别缺料预警（零库存）"""
        bom_items = [
            {"material": "电机", "required": 10, "available": 0},   # 0%
            {"material": "传感器", "required": 20, "available": 19},  # 95%
        ]
        alert = generate_shortage_alert(bom_items, project_id=456)
        self.assertIsNotNone(alert)
        self.assertEqual(alert.severity, "CRITICAL")
        self.assertEqual(alert.project_id, 456)
        self.assertIn("电机", alert.missing_materials)

    def test_generate_shortage_alert_multiple_shortages(self):
        """测试多个物料缺料"""
        bom_items = [
            {"material": "电机", "required": 10, "available": 8},
            {"material": "传感器", "required": 20, "available": 15},
            {"material": "控制器", "required": 5, "available": 3},
        ]
        alert = generate_shortage_alert(bom_items, project_id=789)
        self.assertIsNotNone(alert)
        self.assertEqual(len(alert.missing_materials), 3)
        self.assertEqual(len(alert.details), 3)


# ===========================================================================
# 边界条件和集成测试
# ===========================================================================

class TestEdgeCasesAndIntegration(unittest.TestCase):
    """边界条件和集成测试类"""

    def test_decimal_precision_consistency(self):
        """测试Decimal精度一致性"""
        margin1 = calc_gross_margin(1000, 300, 200, 100, 100)
        margin2 = calc_gross_margin(1000.0, 300.0, 200.0, 100.0, 100.0)
        self.assertEqual(margin1, margin2)

    def test_payment_milestones_rounding(self):
        """测试付款里程碑四舍五入"""
        # 使用不易整除的金额
        milestones = create_standard_payment_milestones(1_234_567.89)
        total = sum(m.amount for m in milestones)
        # 总额应严格等于合同金额
        self.assertEqual(total, Decimal("1234567.89"))

    def test_kpi_benchmarks_immutability(self):
        """测试KPI基准常量不可变性（验证未被修改）"""
        self.assertEqual(KPI_BENCHMARKS["gross_margin_warning"], Decimal("0.20"))
        self.assertEqual(KPI_BENCHMARKS["kit_rate_target"], Decimal("0.95"))
        self.assertEqual(KPI_BENCHMARKS["spi_warning"], Decimal("0.90"))

    def test_mixed_type_inputs(self):
        """测试混合类型输入（int, float, Decimal）"""
        # calc_gross_margin 支持混合类型
        margin = calc_gross_margin(
            contract=Decimal("1000"),
            hardware=300,
            labor=200.0,
            outsource=Decimal("100"),
            travel=100,
        )
        self.assertEqual(margin, Decimal("0.3"))


if __name__ == "__main__":
    unittest.main()
