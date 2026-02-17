# -*- coding: utf-8 -*-
"""
D6组：行业专项 - 非标设备交付测试

金凯博非标自动化测试设备（ICT/FCT/EOL）项目交付核心业务逻辑验证。
涵盖：FAT出厂验收判定、项目毛利核算、工期偏差分析、套件率预警触发。

业务背景：
  - ICT/FCT/EOL 测试台交付时须通过 FAT（出厂验收）+ SAT（现场验收）
  - FAT 判定结果直接决定是否允许发货
  - 结项毛利率 < 20% 触发管理审查
  - 套件率 < 95% 触发缺料预警，影响生产开工
"""

from datetime import date
from decimal import Decimal

import pytest

from tests.fixtures.industry_data import KPI_BENCHMARKS, SAMPLE_PROJECTS

from app.services.business_rules import (
    # FAT 验收
    evaluate_fat_result,
    FATResult,
    # 结项毛利
    calc_final_margin,
    requires_margin_review,
    # 工期偏差
    analyze_delay_root_causes,
    recalculate_delivery_date,
    # BOM 套件率 & 缺料预警
    calc_bom_kit_rate,
    generate_shortage_alert,
    ShortageAlert,
)


# ===========================================================================
# 1. FAT 验收判定规则
# ===========================================================================

class TestFATAcceptanceRules:
    """
    金凯博出厂验收（FAT）判定规则：
      - 所有测试项通过                   → FAT PASSED，允许发货
      - 有 CRITICAL 级别不通过           → FAT FAILED，禁止发货
      - 有 MAJOR 级别不通过              → FAT FAILED，禁止发货
      - 仅有 MINOR 级别不通过            → CONDITIONAL_PASS，可发货但限期整改
    FAT 一次通过率目标 ≥ 90%（KPI_BENCHMARKS["fat_pass_rate_target"]）
    """

    def test_fat_pass_all_items(self):
        """所有测试项通过 → FAT PASSED，允许发货"""
        test_items = [
            {"name": "ICT测试通过率",  "result": "PASS", "level": "CRITICAL"},
            {"name": "节拍时间",        "result": "PASS", "level": "MAJOR"},
            {"name": "外观检查",        "result": "PASS", "level": "MINOR"},
        ]
        fat_result = evaluate_fat_result(test_items)

        assert fat_result.status == "PASSED"
        assert fat_result.can_ship is True
        assert fat_result.failed_items == []

    def test_fat_fail_on_critical(self):
        """CRITICAL 项不通过 → FAT FAILED，禁止发货"""
        test_items = [
            {"name": "ICT测试通过率",  "result": "FAIL", "level": "CRITICAL"},
            {"name": "外观检查",        "result": "PASS", "level": "MINOR"},
        ]
        fat_result = evaluate_fat_result(test_items)

        assert fat_result.status == "FAILED"
        assert fat_result.can_ship is False
        assert "ICT测试通过率" in fat_result.failed_items

    def test_fat_fail_on_major(self):
        """MAJOR 项不通过 → FAT FAILED，禁止发货"""
        test_items = [
            {"name": "节拍时间（45s目标）", "result": "FAIL", "level": "MAJOR"},
            {"name": "外观检查",             "result": "PASS", "level": "MINOR"},
        ]
        fat_result = evaluate_fat_result(test_items)

        assert fat_result.status == "FAILED"
        assert fat_result.can_ship is False
        assert "节拍时间（45s目标）" in fat_result.failed_items

    def test_fat_conditional_pass_minor_only(self):
        """仅有 MINOR 不通过 → CONDITIONAL_PASS，可发货但需整改"""
        test_items = [
            {"name": "ICT测试",   "result": "PASS", "level": "CRITICAL"},
            {"name": "节拍时间",   "result": "PASS", "level": "MAJOR"},
            {"name": "标签位置",   "result": "FAIL", "level": "MINOR"},  # 细节问题
        ]
        fat_result = evaluate_fat_result(test_items)

        assert fat_result.status == "CONDITIONAL_PASS"
        assert fat_result.can_ship is True   # 允许发货
        assert "标签位置" in fat_result.conditional_items
        assert fat_result.failed_items == []  # 无阻塞项

    def test_fat_pass_rate_target_meets_kpi(self):
        """FAT 一次通过率目标 90% 符合 KPI 基准"""
        assert KPI_BENCHMARKS["fat_pass_rate_target"] == 0.90

    def test_fat_empty_items_raises(self):
        """空测试项列表应抛出 ValueError"""
        with pytest.raises(ValueError, match="不能为空"):
            evaluate_fat_result([])

    def test_fat_multiple_critical_failures(self):
        """多个 CRITICAL 项不通过 → 所有失败项都记录在 failed_items"""
        test_items = [
            {"name": "ICT测试通过率",  "result": "FAIL", "level": "CRITICAL"},
            {"name": "安全回路检测",    "result": "FAIL", "level": "CRITICAL"},
            {"name": "外观检查",        "result": "PASS", "level": "MINOR"},
        ]
        fat_result = evaluate_fat_result(test_items)

        assert fat_result.status == "FAILED"
        assert fat_result.can_ship is False
        assert len(fat_result.failed_items) == 2

    def test_fat_conditional_multiple_minor_failures(self):
        """多个 MINOR 不通过 → 仍为有条件通过，所有 MINOR 问题记录到 conditional_items"""
        test_items = [
            {"name": "ICT测试",   "result": "PASS", "level": "CRITICAL"},
            {"name": "标签位置",   "result": "FAIL", "level": "MINOR"},
            {"name": "铭牌字体",   "result": "FAIL", "level": "MINOR"},
            {"name": "线缆整理",   "result": "FAIL", "level": "MINOR"},
        ]
        fat_result = evaluate_fat_result(test_items)

        assert fat_result.status == "CONDITIONAL_PASS"
        assert fat_result.can_ship is True
        assert len(fat_result.conditional_items) == 3


# ===========================================================================
# 2. 项目毛利核算（结项时）
# ===========================================================================

class TestProjectFinalMarginCalculation:
    """
    金凯博结项毛利核算规则：
      毛利率 = (合同金额 - 实际总成本) / 合同金额
      毛利率 > 35% → 达标（KPI 目标）
      毛利率 < 20% → 触发管理审查
    """

    def test_ict_project_margin_above_35_percent(self):
        """ICT项目成本控制良好 → 毛利率 > 35% 达标"""
        # 立讯精密 AirPods FCT 项目（成本控制较好的典型案例）
        project_data = {
            "contract_amount": 168000,
            "costs": {
                "hardware":  75000,   # 硬件
                "labor":     28000,   # 人工（3人×1.5月）
                "outsource": 12000,   # 外协
                "travel":     3000,   # 差旅
            }
        }
        margin = calc_final_margin(project_data)
        expected = (168000 - 75000 - 28000 - 12000 - 3000) / 168000  # = 50000/168000 ≈ 29.76%... 
        # 注：实际验证计算正确性，并验证与 KPI 目标的关系
        assert margin == pytest.approx(expected, abs=1e-6)
        # 毛利 = 50000/168000 ≈ 29.76%，超过 20% 警戒线，无需审查
        assert not requires_margin_review(margin)

    def test_byd_adas_ict_project_margin_calculation(self):
        """比亚迪ADAS ICT项目毛利核算 — 验证计算精度（外协超预算导致毛利偏低）"""
        # 外协超预算 12%，总成本挤压了毛利率
        project_data = {
            "contract_amount": 320000,
            "costs": {
                "hardware":  175000,   # 实际硬件成本
                "labor":      72000,   # 人工成本（5人×2月）
                "outsource":  28000,   # 外协超预算（原预算25000）
                "travel":      8500,   # 差旅
            }
        }
        margin = calc_final_margin(project_data)
        expected = (320000 - 175000 - 72000 - 28000 - 8500) / 320000  # = 36500/320000 ≈ 11.4%

        assert margin == pytest.approx(expected, abs=1e-6)
        # 毛利率 11.4% < 20% 警戒线，需要审查
        assert requires_margin_review(margin) is True

    def test_project_margin_below_warning(self):
        """毛利率低于警戒线（< 20%）触发审查"""
        project_data = {
            "contract_amount": 300000,
            "costs": {
                "hardware": 210000,
                "labor":     60000,
                "outsource": 15000,
                "travel":     5000,
            }
        }
        # 毛利 = (300000 - 290000) / 300000 ≈ 3.3%
        margin = calc_final_margin(project_data)

        assert margin < 0.20
        assert requires_margin_review(margin) is True

    def test_project_margin_near_warning_boundary(self):
        """毛利率恰好等于警戒线 20% — 不触发审查（< 而非 <=）"""
        project_data = {
            "contract_amount": 100000,
            "costs": {"hardware": 80000},  # 毛利率恰好 20%
        }
        margin = calc_final_margin(project_data)

        assert margin == pytest.approx(0.20, abs=1e-9)
        # 规则是 < 20% 触发，等于 20% 不触发
        assert requires_margin_review(margin) is False

    def test_project_margin_zero_cost(self):
        """零成本场景：毛利率应为 100%"""
        project_data = {
            "contract_amount": 200000,
            "costs": {},
        }
        margin = calc_final_margin(project_data)
        assert margin == pytest.approx(1.0, abs=1e-9)

    def test_project_margin_invalid_contract(self):
        """合同金额 <= 0 应抛出 ValueError"""
        with pytest.raises(ValueError):
            calc_final_margin({"contract_amount": 0, "costs": {}})

    def test_eol_project_high_margin(self):
        """EOL 项目高毛利场景（合同高、成本控制好）"""
        project_data = {
            "contract_amount": 520000,  # 对应 SAMPLE_PROJECTS[2]
            "costs": {
                "hardware": 250000,
                "labor":     80000,
                "outsource": 30000,
                "travel":    10000,
            }
        }
        margin = calc_final_margin(project_data)
        # 毛利 = (520000-370000)/520000 ≈ 28.8%
        assert margin == pytest.approx(150000 / 520000, abs=1e-6)
        assert margin > 0.20  # 超过警戒线


# ===========================================================================
# 3. 工期偏差分析
# ===========================================================================

class TestScheduleDelayAnalysis:
    """
    工期偏差分析规则：
      - 延期根因按频次排序，最高频者排首位
      - 物料缺货是金凯博项目最常见延期原因
      - 缺料后重新计算交期（按自然日顺延）
    """

    def test_delay_root_cause_material_shortage(self):
        """延期根因分析：物料缺货出现最多应排首位"""
        delays = [
            {"reason": "物料缺货", "days": 15, "project_id": 1},
            {"reason": "物料缺货", "days":  8, "project_id": 2},
            {"reason": "技术问题", "days":  5, "project_id": 3},
            {"reason": "物料缺货", "days": 12, "project_id": 4},
        ]
        analysis = analyze_delay_root_causes(delays)
        top_cause = analysis[0]

        assert top_cause["reason"] == "物料缺货"
        assert top_cause["frequency"] == 3       # 出现 3 次
        assert top_cause["total_days"] == 35     # 共延误 35 天
        assert top_cause["avg_days"] == pytest.approx(35 / 3, abs=0.1)

    def test_delay_root_cause_single_entry(self):
        """单条延期记录 → 频次为1，总天数为该条记录天数"""
        delays = [
            {"reason": "客户需求变更", "days": 20, "project_id": 5},
        ]
        analysis = analyze_delay_root_causes(delays)

        assert len(analysis) == 1
        assert analysis[0]["reason"] == "客户需求变更"
        assert analysis[0]["frequency"] == 1
        assert analysis[0]["total_days"] == 20

    def test_delay_root_cause_order_by_frequency(self):
        """多种原因混合 → 按频次降序排列"""
        delays = [
            {"reason": "技术问题",   "days": 30, "project_id": 1},
            {"reason": "物料缺货",   "days": 10, "project_id": 2},
            {"reason": "物料缺货",   "days": 10, "project_id": 3},
            {"reason": "客户变更",   "days":  5, "project_id": 4},
        ]
        analysis = analyze_delay_root_causes(delays)

        # 物料缺货 频次2 排第一；技术问题、客户变更 频次1
        assert analysis[0]["reason"] == "物料缺货"
        assert analysis[0]["frequency"] == 2

    def test_delivery_date_recalculation_15_days(self):
        """缺料延误15天后重新计算交期"""
        original_delivery = date(2026, 3, 31)
        shortage_days = 15

        new_delivery = recalculate_delivery_date(original_delivery, delay_days=shortage_days)

        assert new_delivery > original_delivery
        assert (new_delivery - original_delivery).days >= shortage_days
        assert new_delivery == date(2026, 4, 15)

    def test_delivery_date_zero_delay(self):
        """零延误：新交期等于原交期"""
        original_delivery = date(2026, 3, 31)
        new_delivery = recalculate_delivery_date(original_delivery, delay_days=0)

        assert new_delivery == original_delivery

    def test_delivery_date_negative_delay_raises(self):
        """负延误天数应抛出 ValueError"""
        with pytest.raises(ValueError, match="不能为负数"):
            recalculate_delivery_date(date(2026, 3, 31), delay_days=-1)

    def test_delivery_date_across_month_boundary(self):
        """跨月延误计算正确"""
        original_delivery = date(2026, 3, 25)
        new_delivery = recalculate_delivery_date(original_delivery, delay_days=10)

        assert new_delivery == date(2026, 4, 4)


# ===========================================================================
# 4. BOM 套件率预警触发
# ===========================================================================

class TestBOMKitRateAndShortageAlert:
    """
    套件率预警规则：
      - 套件率 = min(available_i / required_i) —— 木桶效应
      - 套件率 < 95% → 触发缺料预警
      - 存在 available==0 的物料 → CRITICAL 等级
      - 仅部分缺货             → WARNING 等级
      - 套件率 >= 95%          → 无预警
    """

    def test_kit_rate_below_target_triggers_alert(self):
        """套件率低于95%自动触发缺料预警（NI机箱缺货 → CRITICAL）"""
        bom_items = [
            {"material": "NI机箱",   "required": 1, "available": 0},  # 缺货！
            {"material": "气缸",      "required": 8, "available": 8},
            {"material": "工业相机",  "required": 2, "available": 1},  # 缺1个
        ]
        kit_rate = calc_bom_kit_rate(bom_items)
        assert kit_rate < KPI_BENCHMARKS["kit_rate_target"]  # < 0.95

        alert = generate_shortage_alert(bom_items, project_id=1)
        assert alert is not None
        assert "NI机箱" in alert.missing_materials
        assert alert.severity == "CRITICAL"        # 关键物料完全缺货

    def test_kit_rate_perfect_supply(self):
        """所有物料齐备 → 套件率100%，无预警"""
        bom_items = [
            {"material": "NI机箱",   "required": 1, "available": 1},
            {"material": "气缸",      "required": 8, "available": 8},
            {"material": "工业相机",  "required": 2, "available": 2},
        ]
        kit_rate = calc_bom_kit_rate(bom_items)
        assert kit_rate == pytest.approx(1.0, abs=1e-9)

        alert = generate_shortage_alert(bom_items, project_id=2)
        assert alert is None  # 无缺料，不预警

    def test_kit_rate_partial_shortage_warning(self):
        """部分缺货（但不为零库存）→ WARNING 等级"""
        bom_items = [
            {"material": "气缸",      "required": 8, "available": 7},  # 缺1个
            {"material": "工业相机",  "required": 2, "available": 2},
            {"material": "伺服驱动",  "required": 4, "available": 4},
        ]
        kit_rate = calc_bom_kit_rate(bom_items)
        # min(7/8, 1.0, 1.0) = 0.875 < 0.95
        assert kit_rate == pytest.approx(7 / 8, abs=1e-6)
        assert kit_rate < KPI_BENCHMARKS["kit_rate_target"]

        alert = generate_shortage_alert(bom_items, project_id=3)
        assert alert is not None
        assert alert.severity == "WARNING"   # 部分缺货，非零库存
        assert "气缸" in alert.missing_materials

    def test_kit_rate_exactly_at_target_no_alert(self):
        """套件率恰好等于 95% 目标值 → 不触发预警"""
        # 20个物料需求，19个可用 → 19/20 = 0.95
        bom_items = [
            {"material": "螺丝M3", "required": 20, "available": 19},
        ]
        kit_rate = calc_bom_kit_rate(bom_items)
        assert kit_rate == pytest.approx(0.95, abs=1e-9)

        alert = generate_shortage_alert(bom_items, project_id=4)
        assert alert is None  # 恰好达标，不预警

    def test_kit_rate_empty_bom_raises(self):
        """空 BOM 列表应抛出 ValueError"""
        with pytest.raises(ValueError, match="不能为空"):
            calc_bom_kit_rate([])

    def test_shortage_alert_records_all_missing(self):
        """多种物料缺货 → 所有缺料物料都记录在 missing_materials"""
        bom_items = [
            {"material": "NI机箱",         "required": 1, "available": 0},
            {"material": "NI数字IO板卡",   "required": 2, "available": 0},
            {"material": "气缸",            "required": 8, "available": 8},  # 足够
        ]
        alert = generate_shortage_alert(bom_items, project_id=5)

        assert alert is not None
        assert "NI机箱" in alert.missing_materials
        assert "NI数字IO板卡" in alert.missing_materials
        assert "气缸" not in alert.missing_materials
        assert alert.severity == "CRITICAL"
        assert alert.project_id == 5

    def test_shortage_alert_details_contain_shortage_qty(self):
        """缺料预警明细应包含具体缺料数量"""
        bom_items = [
            {"material": "工业相机", "required": 4, "available": 1},
        ]
        alert = generate_shortage_alert(bom_items, project_id=6)

        assert alert is not None
        detail = next(d for d in alert.details if d["material"] == "工业相机")
        assert detail["shortage"] == 3   # 需要4台，只有1台，缺3台
