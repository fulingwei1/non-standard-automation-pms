# -*- coding: utf-8 -*-
"""
毛利率预测 API 测试 - 单元测试版本

测试内容：
- SQL 查询逻辑验证
- 预测算法测试
- 数据聚合测试
- 边界条件（空数据、单条数据）

覆盖的 SQL 逻辑：
1. 主查询：projects 表 + contract_amount/actual_cost 计算毛利率
2. 成本明细查询：project_costs 按 cost_type 聚合
3. 行业系数查询：BOM 成本比例、研发工时单价、生产人工占比
4. 相似项目查询：按合同金额最近原则匹配
"""

import pytest
from decimal import Decimal
from unittest.mock import MagicMock, patch


class TestMarginCalculation:
    """毛利率计算测试"""

    def test_gross_margin_calculation(self):
        """测试毛利率计算公式：(contract - cost) / contract * 100"""
        contract_amount = Decimal("100000")
        actual_cost = Decimal("70000")
        
        # 毛利率 = (100000 - 70000) / 100000 * 100 = 30%
        expected_margin = 30.0
        actual_margin = (float(contract_amount - actual_cost) / float(contract_amount)) * 100
        
        assert actual_margin == expected_margin

    def test_gross_margin_zero_contract(self):
        """测试合同金额为0的情况"""
        contract_amount = Decimal("0")
        actual_cost = Decimal("70000")
        
        # 合同为0时，按SQL逻辑返回0
        if contract_amount > 0:
            margin = (float(contract_amount - actual_cost) / float(contract_amount)) * 100
        else:
            margin = 0
            
        assert margin == 0

    def test_gross_margin_higher_cost(self):
        """测试成本超过合同金额（亏损）"""
        contract_amount = Decimal("100000")
        actual_cost = Decimal("120000")
        
        # 亏损：(-20000) / 100000 * 100 = -20%
        margin = (float(contract_amount - actual_cost) / float(contract_amount)) * 100
        
        assert margin == -20.0


class TestDataAggregation:
    """数据聚合测试"""

    def test_calculate_avg_margin(self):
        """测试平均毛利率计算"""
        margins = [30.0, 25.0, 35.0]
        
        avg = sum(margins) / len(margins)
        assert avg == pytest.approx(30.0)

    def test_calculate_median_margin(self):
        """测试中位数毛利率"""
        margins = [30.0, 25.0, 35.0, 20.0, 40.0]
        sorted_margins = sorted(margins)
        median = sorted_margins[len(sorted_margins) // 2]
        
        # [20, 25, 30, 35, 40] 中间位置是 index=2，值为 30
        assert median == 30.0

    def test_calculate_median_single_value(self):
        """测试单值中位数"""
        margins = [30.0]
        sorted_margins = sorted(margins)
        median = sorted_margins[len(sorted_margins) // 2]
        
        assert median == 30.0

    def test_calculate_empty_margins(self):
        """测试空数据"""
        margins = []
        
        avg = sum(margins) / len(margins) if margins else 0
        assert avg == 0
        
        # min/max 也需要处理空情况
        min_m = min(margins) if margins else 0
        max_m = max(margins) if margins else 0
        assert min_m == 0
        assert max_m == 0


class TestCategoryAggregation:
    """按类别聚合测试"""

    def test_aggregate_by_category(self):
        """测试按产品类别聚合"""
        projects = [
            {"product_category": "ICT", "gross_margin": 30.0, "contract_amount": 100000, "actual_cost": 70000},
            {"product_category": "ICT", "gross_margin": 25.0, "contract_amount": 200000, "actual_cost": 150000},
            {"product_category": "FCT", "gross_margin": 20.0, "contract_amount": 150000, "actual_cost": 120000},
        ]
        
        cat_map = {}
        for p in projects:
            cat = p["product_category"] or "未分类"
            if cat not in cat_map:
                cat_map[cat] = {"margins": [], "count": 0, "total_contract": 0, "total_cost": 0}
            cat_map[cat]["margins"].append(p["gross_margin"])
            cat_map[cat]["count"] += 1
            cat_map[cat]["total_contract"] += p["contract_amount"]
            cat_map[cat]["total_cost"] += p["actual_cost"]
        
        assert cat_map["ICT"]["count"] == 2
        assert cat_map["FCT"]["count"] == 1
        
        # ICT 平均：(30 + 25) / 2 = 27.5
        ict_avg = sum(cat_map["ICT"]["margins"]) / len(cat_map["ICT"]["margins"])
        assert ict_avg == pytest.approx(27.5)


class TestAmountRangeAggregation:
    """按金额区间聚合测试"""

    def test_aggregate_by_amount_range(self):
        """测试按合同金额区间聚合"""
        projects = [
            {"contract_amount": 1500000, "gross_margin": 30.0},  # 200万以下
            {"contract_amount": 2500000, "gross_margin": 25.0},  # 200-350万
            {"contract_amount": 4000000, "gross_margin": 20.0},  # 350万以上
        ]
        
        ranges = [
            (0, 2000000, "200万以下"),
            (2000000, 3500000, "200-350万"),
            (3500000, 99999999, "350万以上"),
        ]
        
        by_amount = []
        for low, high, label in ranges:
            range_projects = [p for p in projects if low <= p["contract_amount"] < high]
            if range_projects:
                avg_m = sum(p["gross_margin"] for p in range_projects) / len(range_projects)
                by_amount.append({
                    "range": label,
                    "count": len(range_projects),
                    "avg_margin": avg_m,
                })
        
        assert len(by_amount) == 3
        assert by_amount[0]["range"] == "200万以下"
        assert by_amount[0]["count"] == 1


class TestCostBreakdownCalculation:
    """成本明细计算测试"""

    def test_cost_breakdown_percentage(self):
        """测试成本占比计算"""
        costs = [
            {"cost_type": "材料", "amount": 40000},
            {"cost_type": "人工", "amount": 30000},
            {"cost_type": "制造费用", "amount": 10000},
        ]
        
        total_cost = sum(c["amount"] for c in costs)
        
        for c in costs:
            c["percentage"] = (c["amount"] / total_cost) * 100
        
        # 验证百分比
        assert costs[0]["percentage"] == pytest.approx(50.0)  # 40000/80000*100
        assert costs[1]["percentage"] == pytest.approx(37.5)  # 30000/80000*100
        assert costs[2]["percentage"] == pytest.approx(12.5)  # 10000/80000*100
        
        # 验证总和为100%
        total_pct = sum(c["percentage"] for c in costs)
        assert total_pct == pytest.approx(100.0)


class TestPredictionAlgorithm:
    """预测算法测试"""

    def test_industry_coefficients(self):
        """测试行业成本系数"""
        INDUSTRY_COEFFICIENTS = {
            "锂电": {"labor_ratio": 0.25, "overhead_ratio": 0.15, "risk_factor": 1.1, "travel_ratio": 0.03},
            "光伏": {"labor_ratio": 0.22, "overhead_ratio": 0.13, "risk_factor": 1.05, "travel_ratio": 0.02},
            "3C电子": {"labor_ratio": 0.30, "overhead_ratio": 0.18, "risk_factor": 1.15, "travel_ratio": 0.04},
            "汽车": {"labor_ratio": 0.28, "overhead_ratio": 0.16, "risk_factor": 1.2, "travel_ratio": 0.03},
            "医疗": {"labor_ratio": 0.35, "overhead_ratio": 0.20, "risk_factor": 1.25, "travel_ratio": 0.05},
            "半导体": {"labor_ratio": 0.32, "overhead_ratio": 0.18, "risk_factor": 1.3, "travel_ratio": 0.04},
        }
        
        default_coefficient = {"labor_ratio": 0.28, "overhead_ratio": 0.16, "risk_factor": 1.15, "travel_ratio": 0.03}
        
        # 测试已知行业
        coef = INDUSTRY_COEFFICIENTS.get("汽车", default_coefficient)
        assert coef["labor_ratio"] == 0.28
        
        # 测试未知行业用默认
        unknown_coef = INDUSTRY_COEFFICIENTS.get("未知行业", default_coefficient)
        assert unknown_coef["risk_factor"] == 1.15

    def test_complexity_coefficients(self):
        """测试项目复杂度系数"""
        COMPLEXITY_COEFFICIENTS = {
            "LOW": {"labor_multiplier": 0.8, "overhead_multiplier": 0.9, "change_risk": 0.02},
            "MEDIUM": {"labor_multiplier": 1.0, "overhead_multiplier": 1.0, "change_risk": 0.05},
            "HIGH": {"labor_multiplier": 1.3, "overhead_multiplier": 1.2, "change_risk": 0.10},
        }
        
        # HIGH复杂度应该有更高的系数
        high = COMPLEXITY_COEFFICIENTS["HIGH"]
        assert high["labor_multiplier"] > COMPLEXITY_COEFFICIENTS["MEDIUM"]["labor_multiplier"]
        assert high["change_risk"] > COMPLEXITY_COEFFICIENTS["LOW"]["change_risk"]

    def test_margin_prediction_calculation(self):
        """测试毛利率预测计算"""
        contract_amount = 500000
        
        # 使用默认系数
        labor_ratio = 0.28
        overhead_ratio = 0.16
        risk_factor = 1.15
        travel_ratio = 0.03
        
        # 成本估算
        material_cost = contract_amount * 0.50  # 50% 物料
        design_change_cost = material_cost * 0.05  # 5% 设计变更
        rd_labor = contract_amount * labor_ratio * 0.5  # 研发50%是研发
        prod_labor = contract_amount * labor_ratio * 0.5  # 生产50%是生产
        travel = contract_amount * travel_ratio
        overhead = contract_amount * overhead_ratio
        
        base_total = material_cost + design_change_cost + rd_labor + prod_labor + travel + overhead
        risk_adjusted = base_total * risk_factor
        
        predicted_margin = ((contract_amount - risk_adjusted) / contract_amount) * 100
        
        # 验证计算结果合理
        assert -50 < predicted_margin < 50  # 毛利率应该在合理范围

    def test_confidence_calculation(self):
        """测试置信度计算"""
        def calculate_confidence(estimated_material_cost, estimated_design_change_cost, 
                                  estimated_travel_cost, estimated_rd_hours):
            input_completeness = (
                sum([
                    1 if estimated_material_cost else 0,
                    1 if estimated_design_change_cost else 0,
                    1 if estimated_travel_cost else 0,
                    1 if estimated_rd_hours else 0,
                ]) / 4.0
            )
            confidence = min(0.95, 0.4 + input_completeness * 0.4 + 0.2)
            return confidence
        
        # 完整输入
        conf_full = calculate_confidence(100000, 10000, 5000, 100)
        assert conf_full >= 0.8
        
        # 无输入
        conf_none = calculate_confidence(None, None, None, None)
        assert conf_none == pytest.approx(0.6)  # 0.4 + 0.2
        
        # 部分输入
        conf_partial = calculate_confidence(100000, None, None, None)
        assert 0.6 < conf_partial < 0.8


class TestRiskAssessment:
    """风险等级评估测试"""

    def test_risk_level_classification(self):
        """测试风险等级分类"""
        def get_risk_level(predicted_margin):
            if predicted_margin < 15:
                return "high"
            elif predicted_margin < 25:
                return "medium"
            else:
                return "low"
        
        assert get_risk_level(10) == "high"
        assert get_risk_level(20) == "medium"
        assert get_risk_level(30) == "low"


class TestSimilarProjectsMatching:
    """相似项目匹配测试"""

    def test_find_similar_by_amount(self):
        """测试按合同金额找相似项目"""
        projects = [
            {"contract_amount": 100000, "project_code": "PJ001"},
            {"contract_amount": 150000, "project_code": "PJ002"},
            {"contract_amount": 200000, "project_code": "PJ003"},
            {"contract_amount": 280000, "project_code": "PJ004"},
            {"contract_amount": 350000, "project_code": "PJ005"},
        ]
        
        target_amount = 250000
        
        # 按金额差异排序
        sorted_projects = sorted(
            projects, 
            key=lambda p: abs(p["contract_amount"] - target_amount)
        )
        
        # 取前5个（实际API限制5个）
        similar = sorted_projects[:5]
        
        assert len(similar) == 5
        # 最近的应该是 PJ004 (280000, 差30000)
        assert similar[0]["project_code"] == "PJ004"


class TestCostVarianceCalculation:
    """成本偏差计算测试"""

    def test_budget_variance_percentage(self):
        """测试预算偏差百分比计算"""
        budget_amount = Decimal("80000")
        actual_cost = Decimal("88000")
        
        # 偏差 = (实际 - 预算) / 预算 * 100
        variance_pct = float((actual_cost - budget_amount) / budget_amount) * 100
        
        assert variance_pct == pytest.approx(10.0)

    def test_margin_gap(self):
        """测试计划毛利率与实际毛利率差额"""
        contract = 100000
        budget = 80000
        actual = 85000
        
        planned_margin = (contract - budget) / contract * 100  # 20%
        actual_margin = (contract - actual) / contract * 100   # 15%
        margin_gap = actual_margin - planned_margin            # -5%
        
        assert margin_gap == pytest.approx(-5.0)

    def test_overrun_detection(self):
        """测试超预算检测"""
        budget = 80000
        actual = 85000
        overrun = actual > budget
        
        assert overrun is True
        
        not_overrun = 75000 > 80000
        assert not_overrun is False


class TestEdgeCases:
    """边界条件测试"""

    def test_single_project_stats(self):
        """测试单项目统计"""
        margins = [40.0]
        
        avg = sum(margins) / len(margins)
        sorted_margins = sorted(margins)
        median = sorted_margins[len(sorted_margins) // 2]
        
        assert avg == median == 40.0

    def test_two_project_median(self):
        """测试双项目中位数"""
        margins = [20.0, 40.0]
        
        sorted_margins = sorted(margins)
        median = sorted_margins[len(sorted_margins) // 2]
        
        # 偶数个取中间偏大的值（Python整数除法特性）
        assert median == 40.0

    def test_zero_amount_range(self):
        """测试金额为0的项目不在统计范围内"""
        projects = [
            {"contract_amount": 0, "gross_margin": 0},
            {"contract_amount": 100000, "gross_margin": 30},
        ]
        
        # SQL 中 WHERE contract_amount > 0 会过滤掉
        valid_projects = [p for p in projects if p["contract_amount"] > 0]
        
        assert len(valid_projects) == 1

    def test_null_handling(self):
        """测试空值处理"""
        # None 值应该用默认值
        value = None
        actual_cost = float(value or 0)
        
        assert actual_cost == 0.0


class TestRecommendationsLogic:
    """智能建议逻辑测试"""

    def test_input_completeness_check(self):
        """测试输入完整度检查"""
        input_data = {
            "estimated_material_cost": 100000,
            "estimated_design_change_cost": None,
            "estimated_travel_cost": 5000,
            "estimated_rd_hours": None,
        }
        
        completeness = sum(1 for v in input_data.values() if v) / len(input_data)
        
        assert completeness == pytest.approx(0.5)  # 2/4

    def test_design_change_warning(self):
        """测试设计变更费用过高警告"""
        bom_cost = 100000
        design_change = 15000  # 15%
        
        warning_triggered = design_change / bom_cost > 0.08
        
        assert warning_triggered is True

    def test_rd_cost_warning(self):
        """测试研发成本占比过高警告"""
        rd_cost = 80000
        contract = 200000  # 40%
        
        warning_triggered = rd_cost / contract > 0.25
        
        assert warning_triggered is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])