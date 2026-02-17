# -*- coding: utf-8 -*-
"""
金凯博自动化测试（深圳）— ATE行业KPI计算逻辑单元测试

验证非标自动化测试设备项目管理中的核心KPI计算：
- 项目准时交付率（On-time Delivery Rate）
- 毛利率计算（合同额 - 硬件 - 人工 - 外协 - 差旅）
- FAT一次通过率
- 客户满意度加权平均
- 工程师人效（产出工时/总工时）
- 返工率统计

测试数据来自 tests/fixtures/industry_data.py
"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock

from tests.fixtures.industry_data import (
    SAMPLE_PROJECTS,
    CUSTOMERS,
    SAMPLE_TIMESHEETS,
    SAMPLE_COSTS,
    KPI_BENCHMARKS,
    PROJECT_TYPES,
    make_mock_project,
)

# ─────────────────────────────────────────────────────────────────────────────
# KPI 计算函数（内嵌实现）
# ─────────────────────────────────────────────────────────────────────────────


def calculate_on_time_delivery_rate(projects: list) -> dict:
    """
    计算项目准时交付率（ODR）
    :param projects: 项目列表，每项含 planned_end_date / actual_end_date / status
    :return: {"odr": float, "on_time": int, "delayed": int, "total": int}
    """
    completed = [p for p in projects if p.get("status") in ("COMPLETED", "CLOSED")]
    if not completed:
        return {"odr": 0.0, "on_time": 0, "delayed": 0, "total": 0}

    on_time = 0
    delayed = 0
    for p in completed:
        planned = p.get("planned_end_date")
        actual = p.get("actual_end_date")
        if actual is None:
            # 未记录实际结束日期，按延期处理
            delayed += 1
        elif actual <= planned:
            on_time += 1
        else:
            delayed += 1

    total = on_time + delayed
    return {
        "odr": on_time / total if total > 0 else 0.0,
        "on_time": on_time,
        "delayed": delayed,
        "total": total,
    }


def calculate_gross_margin(
    contract_amount: float,
    hardware_cost: float,
    labor_cost: float,
    outsourcing_cost: float,
    travel_cost: float,
    other_cost: float = 0.0,
) -> dict:
    """
    毛利率计算：（合同金额 - 成本合计）/ 合同金额
    成本 = 硬件 + 人工 + 外协 + 差旅 + 其他
    """
    total_cost = hardware_cost + labor_cost + outsourcing_cost + travel_cost + other_cost
    gross_profit = contract_amount - total_cost
    gross_margin = gross_profit / contract_amount if contract_amount > 0 else 0.0
    return {
        "contract_amount": contract_amount,
        "total_cost": total_cost,
        "gross_profit": gross_profit,
        "gross_margin": round(gross_margin, 4),
        "cost_breakdown": {
            "hardware": hardware_cost,
            "labor": labor_cost,
            "outsourcing": outsourcing_cost,
            "travel": travel_cost,
            "other": other_cost,
        },
    }


def calculate_fat_first_pass_rate(fat_records: list) -> dict:
    """
    FAT（工厂验收测试）一次通过率
    :param fat_records: [{"project_id": int, "passed_first_attempt": bool}, ...]
    :return: {"fpr": float, "passed": int, "failed": int, "total": int}
    """
    if not fat_records:
        return {"fpr": 0.0, "passed": 0, "failed": 0, "total": 0}
    passed = sum(1 for r in fat_records if r.get("passed_first_attempt", False))
    total = len(fat_records)
    return {
        "fpr": round(passed / total, 4),
        "passed": passed,
        "failed": total - passed,
        "total": total,
    }


def calculate_weighted_customer_satisfaction(ratings: list) -> dict:
    """
    客户满意度加权平均（大客户权重更高）
    :param ratings: [{"customer_level": str, "score": float}, ...]
                    customer_level: "A" → weight=2, "B" → weight=1
    :return: {"weighted_avg": float, "count": int, "min": float, "max": float}
    """
    WEIGHT_MAP = {"A": 2, "B": 1, "C": 0.5}
    if not ratings:
        return {"weighted_avg": 0.0, "count": 0, "min": 0.0, "max": 0.0}

    total_weight = 0.0
    weighted_sum = 0.0
    scores = []

    for r in ratings:
        weight = WEIGHT_MAP.get(r.get("customer_level", "B"), 1)
        score = r.get("score", 0.0)
        weighted_sum += score * weight
        total_weight += weight
        scores.append(score)

    return {
        "weighted_avg": round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0,
        "count": len(ratings),
        "min": min(scores),
        "max": max(scores),
        "total_weight": total_weight,
    }


def calculate_engineer_efficiency(timesheet_records: list) -> dict:
    """
    工程师人效 = 产出工时（APPROVED状态）/ 总工时
    :param timesheet_records: 工时记录列表
    :return: {"efficiency": float, "productive_hours": float, "total_hours": float}
    """
    total_hours = sum(r.get("hours", 0.0) for r in timesheet_records)
    productive_hours = sum(
        r.get("hours", 0.0)
        for r in timesheet_records
        if r.get("status") == "APPROVED"
    )
    efficiency = productive_hours / total_hours if total_hours > 0 else 0.0
    return {
        "efficiency": round(efficiency, 4),
        "productive_hours": productive_hours,
        "total_hours": total_hours,
        "pending_hours": total_hours - productive_hours,
    }


def calculate_rework_rate(work_records: list) -> dict:
    """
    返工率 = 标记为返工的工时 / 总工时
    工单类型含 REWORK / DEBUGGING 的视为返工
    :return: {"rework_rate": float, "rework_hours": float, "total_hours": float}
    """
    REWORK_TYPES = {"REWORK", "DEBUGGING"}
    total_hours = sum(r.get("hours", 0.0) for r in work_records)
    rework_hours = sum(
        r.get("hours", 0.0)
        for r in work_records
        if r.get("type", "") in REWORK_TYPES
    )
    return {
        "rework_rate": round(rework_hours / total_hours, 4) if total_hours > 0 else 0.0,
        "rework_hours": rework_hours,
        "total_hours": total_hours,
        "normal_hours": total_hours - rework_hours,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 测试类 1：准时交付率
# ─────────────────────────────────────────────────────────────────────────────

class TestOnTimeDeliveryRate:
    """项目准时交付率 KPI 测试"""

    def test_all_projects_on_time_odr_100_percent(self):
        """所有项目准时交付：ODR=100%"""
        projects = [
            {"status": "COMPLETED", "planned_end_date": date(2025, 10, 15),
             "actual_end_date": date(2025, 10, 12)},
            {"status": "COMPLETED", "planned_end_date": date(2025, 11, 30),
             "actual_end_date": date(2025, 11, 30)},  # 恰好准时
        ]
        result = calculate_on_time_delivery_rate(projects)
        assert result["odr"] == pytest.approx(1.0)
        assert result["on_time"] == 2
        assert result["delayed"] == 0

    def test_mixed_on_time_and_delayed(self):
        """3个完成项目，2个准时1个延期：ODR≈67%"""
        projects = [
            {"status": "COMPLETED", "planned_end_date": date(2025, 10, 15),
             "actual_end_date": date(2025, 10, 14)},
            {"status": "COMPLETED", "planned_end_date": date(2025, 11, 30),
             "actual_end_date": date(2025, 11, 28)},
            {"status": "COMPLETED", "planned_end_date": date(2025, 9, 30),
             "actual_end_date": date(2025, 10, 12)},  # 延期12天
        ]
        result = calculate_on_time_delivery_rate(projects)
        assert result["odr"] == pytest.approx(2 / 3, abs=0.001)
        assert result["delayed"] == 1

    def test_odr_with_lixun_completed_project(self):
        """立讯精密AirPods FCT项目（样例数据）：已完成，检查ODR统计"""
        # SAMPLE_PROJECTS[1]: planned_end_date=2025-10-15, 状态COMPLETED
        p = SAMPLE_PROJECTS[1]
        projects_data = [
            {
                "status": p["status"],
                "planned_end_date": p["planned_end_date"],
                "actual_end_date": date(2025, 10, 10),  # 提前5天完成
            }
        ]
        result = calculate_on_time_delivery_rate(projects_data)
        assert result["odr"] == 1.0
        assert result["on_time"] == 1

    def test_odr_excludes_in_progress_projects(self):
        """进行中的项目不计入ODR统计"""
        projects = [
            {"status": "IN_PROGRESS", "planned_end_date": date(2026, 5, 31),
             "actual_end_date": None},
            {"status": "COMPLETED", "planned_end_date": date(2025, 10, 15),
             "actual_end_date": date(2025, 10, 10)},
        ]
        result = calculate_on_time_delivery_rate(projects)
        assert result["total"] == 1
        assert result["odr"] == 1.0  # 只统计已完成的1个

    def test_odr_below_kpi_target_85_percent(self):
        """ODR低于85%目标时需要关注"""
        projects = [
            {"status": "COMPLETED", "planned_end_date": date(2025, i, 28),
             "actual_end_date": date(2025, i + 1, 5)}   # 每个均延期
            for i in range(1, 8)
        ]
        result = calculate_on_time_delivery_rate(projects)
        assert result["odr"] == 0.0  # 全部延期
        assert result["odr"] < KPI_BENCHMARKS["project_on_time_rate"]  # < 85%


# ─────────────────────────────────────────────────────────────────────────────
# 测试类 2：毛利率计算
# ─────────────────────────────────────────────────────────────────────────────

class TestGrossMarginCalculation:
    """项目毛利率计算测试"""

    def test_ict_project_gross_margin_calculation(self):
        """比亚迪ICT项目毛利率：合同32万，成本28.35万→毛利率约11.4%"""
        # SAMPLE_PROJECTS[0]: contract_amount=320000
        # SAMPLE_COSTS：硬件175000+人工72000+外协28000+差旅8500=283500
        result = calculate_gross_margin(
            contract_amount=320000,
            hardware_cost=175000,
            labor_cost=72000,
            outsourcing_cost=28000,
            travel_cost=8500,
        )
        expected_margin = (320000 - 283500) / 320000
        assert result["gross_margin"] == pytest.approx(expected_margin, abs=0.001)
        assert result["gross_profit"] == pytest.approx(36500)
        assert result["total_cost"] == pytest.approx(283500)

    def test_gross_margin_above_35_percent_target(self):
        """毛利率达到35%KPI目标"""
        # EOL项目：合同52万，成本33.8万
        result = calculate_gross_margin(
            contract_amount=520000,
            hardware_cost=210000,
            labor_cost=90000,
            outsourcing_cost=30000,
            travel_cost=8000,
        )
        assert result["gross_margin"] >= KPI_BENCHMARKS["gross_margin_target"]

    def test_gross_margin_negative_means_loss(self):
        """毛利率为负时代表亏损项目"""
        result = calculate_gross_margin(
            contract_amount=100000,
            hardware_cost=80000,
            labor_cost=40000,
            outsourcing_cost=10000,
            travel_cost=5000,
        )
        assert result["gross_margin"] < 0
        assert result["gross_profit"] < 0

    def test_gross_margin_cost_breakdown_sums_correctly(self):
        """成本分项加总应等于总成本"""
        result = calculate_gross_margin(
            contract_amount=280000,
            hardware_cost=130000,
            labor_cost=60000,
            outsourcing_cost=22000,
            travel_cost=6000,
            other_cost=3000,
        )
        breakdown = result["cost_breakdown"]
        sum_breakdown = sum(breakdown.values())
        assert sum_breakdown == pytest.approx(result["total_cost"])

    def test_burn_system_small_project_margin(self):
        """烧录系统小项目（9.5万合同）毛利率测试"""
        # PROJECT_TYPES["BURN"]: avg_budget=95000
        result = calculate_gross_margin(
            contract_amount=95000,
            hardware_cost=40000,
            labor_cost=20000,
            outsourcing_cost=5000,
            travel_cost=2000,
        )
        expected = (95000 - 67000) / 95000
        assert result["gross_margin"] == pytest.approx(expected, abs=0.001)

    def test_gross_margin_all_cost_types_included(self):
        """验证所有五类成本都被纳入计算"""
        result = calculate_gross_margin(
            contract_amount=200000,
            hardware_cost=10000,
            labor_cost=20000,
            outsourcing_cost=30000,
            travel_cost=40000,
            other_cost=50000,
        )
        assert result["total_cost"] == 150000
        assert result["gross_profit"] == 50000


# ─────────────────────────────────────────────────────────────────────────────
# 测试类 3：FAT一次通过率
# ─────────────────────────────────────────────────────────────────────────────

class TestFATFirstPassRate:
    """工厂验收测试（FAT）一次通过率 KPI 测试"""

    def test_fat_all_pass_first_attempt(self):
        """所有项目FAT一次通过：FPR=100%"""
        records = [
            {"project_id": 1, "passed_first_attempt": True},
            {"project_id": 2, "passed_first_attempt": True},
            {"project_id": 3, "passed_first_attempt": True},
        ]
        result = calculate_fat_first_pass_rate(records)
        assert result["fpr"] == 1.0
        assert result["passed"] == 3
        assert result["failed"] == 0

    def test_fat_mixed_results_correct_rate(self):
        """10个项目中9个一次通过：FPR=90%，恰好达到目标"""
        records = [
            {"project_id": i, "passed_first_attempt": True}
            for i in range(1, 10)
        ] + [{"project_id": 10, "passed_first_attempt": False}]

        result = calculate_fat_first_pass_rate(records)
        assert result["fpr"] == pytest.approx(0.90)
        assert result["fpr"] == KPI_BENCHMARKS["fat_pass_rate_target"]

    def test_fat_pass_rate_below_target_triggers_review(self):
        """FAT通过率低于90%：需要质量审查"""
        records = [
            {"project_id": 1, "passed_first_attempt": True},
            {"project_id": 2, "passed_first_attempt": False},  # 需要返修
            {"project_id": 3, "passed_first_attempt": False},  # 需要返修
        ]
        result = calculate_fat_first_pass_rate(records)
        assert result["fpr"] == pytest.approx(1 / 3, abs=0.001)
        assert result["fpr"] < KPI_BENCHMARKS["fat_pass_rate_target"]
        assert result["failed"] == 2

    def test_fat_single_project_pass(self):
        """单个项目FAT通过"""
        result = calculate_fat_first_pass_rate([
            {"project_id": 3, "passed_first_attempt": True}
        ])
        assert result["fpr"] == 1.0
        assert result["total"] == 1

    def test_fat_empty_records_returns_zero(self):
        """无FAT记录时返回0"""
        result = calculate_fat_first_pass_rate([])
        assert result["fpr"] == 0.0
        assert result["total"] == 0


# ─────────────────────────────────────────────────────────────────────────────
# 测试类 4：客户满意度加权平均
# ─────────────────────────────────────────────────────────────────────────────

class TestCustomerSatisfactionWeightedAverage:
    """客户满意度加权平均计算（A级客户权重2倍）"""

    def test_single_a_level_customer_satisfaction(self):
        """单个A级客户（比亚迪）评分4.5"""
        ratings = [{"customer_level": "A", "score": 4.5}]
        result = calculate_weighted_customer_satisfaction(ratings)
        assert result["weighted_avg"] == pytest.approx(4.5)
        assert result["count"] == 1

    def test_mixed_level_customers_weighted_correctly(self):
        """A级客户权重2，B级权重1：加权平均应偏向A级"""
        ratings = [
            {"customer_level": "A", "score": 5.0},  # 比亚迪
            {"customer_level": "B", "score": 3.0},  # 伯恩光学
        ]
        # 加权平均 = (5.0*2 + 3.0*1) / (2+1) = 13/3 ≈ 4.33
        result = calculate_weighted_customer_satisfaction(ratings)
        assert result["weighted_avg"] == pytest.approx(13 / 3, abs=0.01)

    def test_all_major_customers_above_target(self):
        """主要客户（比亚迪、立讯、德赛西威）满意度均高于4.2目标"""
        ratings = [
            {"customer_level": "A", "score": 4.8},  # 比亚迪
            {"customer_level": "A", "score": 4.5},  # 立讯精密
            {"customer_level": "A", "score": 4.3},  # 德赛西威
        ]
        result = calculate_weighted_customer_satisfaction(ratings)
        assert result["weighted_avg"] >= KPI_BENCHMARKS["customer_satisfaction"]
        assert result["min"] >= KPI_BENCHMARKS["customer_satisfaction"]

    def test_poor_rating_from_b_level_customer_doesnt_drag_kpi(self):
        """B级客户低评分对加权平均的影响小于A级"""
        # A级客户4.5，B级客户2.0
        ratings_with_b_low = [
            {"customer_level": "A", "score": 4.5},
            {"customer_level": "B", "score": 2.0},
        ]
        # A级客户4.5，A级客户2.0（对比）
        ratings_with_a_low = [
            {"customer_level": "A", "score": 4.5},
            {"customer_level": "A", "score": 2.0},
        ]
        result_b = calculate_weighted_customer_satisfaction(ratings_with_b_low)
        result_a = calculate_weighted_customer_satisfaction(ratings_with_a_low)
        assert result_b["weighted_avg"] > result_a["weighted_avg"]

    def test_satisfaction_score_range_min_max(self):
        """验证最高分和最低分记录正确"""
        ratings = [
            {"customer_level": "A", "score": 4.9},
            {"customer_level": "B", "score": 3.2},
            {"customer_level": "B", "score": 4.1},
        ]
        result = calculate_weighted_customer_satisfaction(ratings)
        assert result["max"] == pytest.approx(4.9)
        assert result["min"] == pytest.approx(3.2)


# ─────────────────────────────────────────────────────────────────────────────
# 测试类 5：工程师人效
# ─────────────────────────────────────────────────────────────────────────────

class TestEngineerEfficiency:
    """工程师人效（产出工时/总工时）KPI 测试"""

    def test_engineer_efficiency_all_approved(self):
        """所有工时已审批：人效=100%"""
        timesheets = [
            {"hours": 8.0, "status": "APPROVED"},
            {"hours": 8.0, "status": "APPROVED"},
        ]
        result = calculate_engineer_efficiency(timesheets)
        assert result["efficiency"] == pytest.approx(1.0)
        assert result["productive_hours"] == 16.0

    def test_engineer_efficiency_with_pending_hours(self):
        """部分工时待审批：人效小于100%"""
        # SAMPLE_TIMESHEETS 包含 APPROVED 和 PENDING 状态
        timesheets = list(SAMPLE_TIMESHEETS)
        result = calculate_engineer_efficiency(timesheets)
        approved_hours = sum(t["hours"] for t in timesheets if t["status"] == "APPROVED")
        total_hours = sum(t["hours"] for t in timesheets)
        expected_eff = approved_hours / total_hours
        assert result["efficiency"] == pytest.approx(expected_eff, abs=0.001)
        assert result["productive_hours"] == pytest.approx(approved_hours)

    def test_engineer_efficiency_from_sample_data_accuracy(self):
        """验证样例工时数据计算准确性"""
        # SAMPLE_TIMESHEETS: ids 1,2,4 = APPROVED; id 3 = PENDING
        # hours: 8.0 + 8.0 + 4.0(PENDING) + 6.5 = 26.5 total
        # APPROVED: 8.0 + 8.0 + 6.5 = 22.5
        result = calculate_engineer_efficiency(SAMPLE_TIMESHEETS)
        assert result["total_hours"] == pytest.approx(26.5)
        assert result["productive_hours"] == pytest.approx(22.5)
        assert result["pending_hours"] == pytest.approx(4.0)

    def test_empty_timesheets_zero_efficiency(self):
        """无工时记录：人效返回0"""
        result = calculate_engineer_efficiency([])
        assert result["efficiency"] == 0.0
        assert result["total_hours"] == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 测试类 6：返工率统计
# ─────────────────────────────────────────────────────────────────────────────

class TestReworkRateStatistics:
    """项目返工率统计 KPI 测试"""

    def test_rework_rate_with_no_rework_hours(self):
        """无返工工时：返工率=0%"""
        records = [
            {"hours": 8.0, "type": "HARDWARE", "status": "APPROVED"},
            {"hours": 6.0, "type": "SOFTWARE", "status": "APPROVED"},
        ]
        result = calculate_rework_rate(records)
        assert result["rework_rate"] == 0.0
        assert result["rework_hours"] == 0.0

    def test_rework_rate_with_debugging_hours(self):
        """DEBUGGING工时记为返工：返工率计算"""
        records = [
            {"hours": 8.0, "type": "HARDWARE", "status": "APPROVED"},
            {"hours": 4.0, "type": "SOFTWARE", "status": "APPROVED"},
            {"hours": 6.5, "type": "DEBUGGING", "status": "APPROVED"},  # 返工
        ]
        result = calculate_rework_rate(records)
        expected_rate = 6.5 / (8.0 + 4.0 + 6.5)
        assert result["rework_rate"] == pytest.approx(expected_rate, abs=0.001)
        assert result["rework_hours"] == pytest.approx(6.5)

    def test_rework_rate_from_sample_timesheets(self):
        """使用SAMPLE_TIMESHEETS真实数据：FCT联调工时应计为返工"""
        # id=4: DEBUGGING type, 6.5h (立讯FCT蓝牙误判问题修复)
        result = calculate_rework_rate(SAMPLE_TIMESHEETS)
        assert result["rework_hours"] == pytest.approx(6.5)
        assert result["total_hours"] == pytest.approx(26.5)
        expected_rate = 6.5 / 26.5
        assert result["rework_rate"] == pytest.approx(expected_rate, abs=0.001)

    def test_rework_rate_below_5_percent_target(self):
        """正常项目返工率应低于5%上限"""
        records = [
            {"hours": 8.0, "type": "HARDWARE", "status": "APPROVED"},
            {"hours": 8.0, "type": "SOFTWARE", "status": "APPROVED"},
            {"hours": 8.0, "type": "DESIGN", "status": "APPROVED"},
            {"hours": 0.3, "type": "REWORK", "status": "APPROVED"},  # 少量返工
        ]
        result = calculate_rework_rate(records)
        assert result["rework_rate"] < KPI_BENCHMARKS["rework_rate_limit"]  # < 5%

    def test_high_rework_rate_indicates_quality_issue(self):
        """返工率超过5%警示质量问题（视觉检测算法调优场景）"""
        records = [
            {"hours": 8.0, "type": "DESIGN", "status": "APPROVED"},
            {"hours": 3.0, "type": "DEBUGGING", "status": "APPROVED"},  # 视觉算法调试
            {"hours": 2.0, "type": "REWORK", "status": "APPROVED"},     # 返工
        ]
        result = calculate_rework_rate(records)
        assert result["rework_rate"] > KPI_BENCHMARKS["rework_rate_limit"]  # > 5%
        assert result["rework_hours"] == pytest.approx(5.0)

    def test_rework_rate_normal_hours_accuracy(self):
        """normal_hours（非返工工时）计算准确"""
        records = [
            {"hours": 10.0, "type": "HARDWARE"},
            {"hours": 4.0, "type": "REWORK"},
        ]
        result = calculate_rework_rate(records)
        assert result["normal_hours"] == pytest.approx(10.0)
        assert result["rework_rate"] == pytest.approx(4.0 / 14.0, abs=0.001)
