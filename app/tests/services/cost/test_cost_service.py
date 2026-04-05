# -*- coding: utf-8 -*-
"""
成本服务测试

测试 CostService 的核心功能：
- 成本汇总与分布
- 预算偏差计算
- 成本对比分析
- 利润分析
"""

import pytest
from decimal import Decimal

from app.services.cost.cost_service import CostService


class TestCostService:
    """成本服务测试类"""

    def test_get_project_success(self, db_session, test_project):
        """测试获取项目基本信息"""
        service = CostService(db_session)
        project = service.get_project(test_project.id)
        
        assert project is not None
        assert project.id == test_project.id
        assert project.project_name == "测试项目"

    def test_get_project_not_found(self, db_session):
        """测试获取不存在的项目"""
        service = CostService(db_session)
        project = service.get_project(99999)
        
        assert project is None

    def test_get_cost_breakdown_with_costs(self, db_session, test_project_with_costs):
        """测试获取项目成本汇总（含成本记录）"""
        service = CostService(db_session)
        breakdown = service.get_cost_breakdown(test_project_with_costs.id)
        
        # 总成本 = 20000 + 15000 + 10000 + 5000 = 50000
        assert breakdown["total_cost"] == Decimal("50000")
        
        # 按类型检查
        assert "材料费" in breakdown["cost_by_type"]
        assert breakdown["cost_by_type"]["材料费"] == Decimal("20000")
        assert breakdown["cost_by_type"]["人工费"] == Decimal("15000")
        
        # 按分类检查
        assert "BOM" in breakdown["cost_by_category"]
        assert breakdown["cost_by_category"]["BOM"] == Decimal("20000")

    def test_get_cost_breakdown_no_costs(self, db_session, test_project_no_costs):
        """测试获取项目成本汇总（无成本记录）"""
        service = CostService(db_session)
        breakdown = service.get_cost_breakdown(test_project_no_costs.id)
        
        assert breakdown["total_cost"] == Decimal("0")
        assert breakdown["cost_by_type"] == {}
        assert breakdown["cost_by_category"] == {}

    def test_calculate_variance_under_budget(self):
        """测试预算偏差计算（未超预算）"""
        variance = CostService.calculate_variance(
            budget_amount=100000,
            actual_cost=80000
        )
        
        assert variance["budget_variance"] == -20000  # 节省了
        assert variance["budget_variance_pct"] == -20.0

    def test_calculate_variance_over_budget(self):
        """测试预算偏差计算（超预算）"""
        variance = CostService.calculate_variance(
            budget_amount=100000,
            actual_cost=120000
        )
        
        assert variance["budget_variance"] == 20000  # 超支了
        assert variance["budget_variance_pct"] == 20.0

    def test_calculate_variance_zero_budget(self):
        """测试预算偏差计算（预算为0）"""
        variance = CostService.calculate_variance(
            budget_amount=0,
            actual_cost=50000
        )
        
        assert variance["budget_variance"] == 0
        assert variance["budget_variance_pct"] == 0

    def test_get_project_cost_analysis(self, db_session, test_project_with_costs):
        """测试项目成本分析"""
        service = CostService(db_session)
        analysis = service.get_project_cost_analysis(test_project_with_costs.id)
        
        assert analysis["project_id"] == test_project_with_costs.id
        assert analysis["budget_amount"] == Decimal("80000")
        assert analysis["contract_amount"] == Decimal("100000")
        assert analysis["actual_cost"] == Decimal("50000")
        assert analysis["total_cost"] == Decimal("50000")
        
        # 预算偏差检查 (50000 - 80000 = -30000, -37.5%)
        assert analysis["budget_variance"] == -30000
        assert analysis["budget_variance_pct"] == -37.5
        
        # 合同偏差 (100000 - 50000 = 50000, 50%)
        assert analysis["contract_variance"] == 50000
        assert analysis["contract_variance_pct"] == 50.0

    def test_get_project_cost_analysis_not_found(self, db_session):
        """测试获取不存在的项目成本分析"""
        service = CostService(db_session)
        analysis = service.get_project_cost_analysis(99999)
        
        assert "error" in analysis
        assert analysis["error"] == "项目不存在"

    def test_get_project_cost_analysis_with_comparison(self, db_session, test_project_with_costs, test_project_no_costs):
        """测试带对比项目的成本分析"""
        service = CostService(db_session)
        analysis = service.get_project_cost_analysis(
            test_project_with_costs.id,
            compare_project_id=test_project_no_costs.id
        )
        
        assert "comparison" in analysis
        comparison = analysis["comparison"]
        assert comparison["compare_project_id"] == test_project_no_costs.id
        assert comparison["compare_budget_amount"] == Decimal("40000")
        assert comparison["budget_diff"] == Decimal("40000")  # 80000 - 40000
        assert comparison["actual_diff"] == Decimal("50000")  # 50000 - 0

    def test_calculate_cost_stats(self, db_session, test_project_with_costs):
        """测试项目成本统计"""
        service = CostService(db_session)
        # 传入 float 类型的 budget_amount
        stats = service.calculate_cost_stats(test_project_with_costs.id, budget_amount=60000.0)
        
        # total_cost 是 float
        assert float(stats["total_cost"]) == 50000.0
        assert stats["budget_amount"] == 60000.0
        assert stats["cost_variance"] == -10000.0
        assert stats["cost_variance_rate"] == pytest.approx(-16.67, rel=0.01)
        assert stats["is_over_budget"] is False

    def test_calculate_cost_stats_over_budget(self, db_session, test_project_with_costs):
        """测试项目成本统计（超预算）"""
        service = CostService(db_session)
        # 传入 float 类型的 budget_amount
        stats = service.calculate_cost_stats(test_project_with_costs.id, budget_amount=40000.0)
        
        assert stats["is_over_budget"] is True
        assert stats["cost_variance"] == 10000.0
        assert stats["cost_variance_rate"] == 25.0

    def test_get_project_profit_analysis(self, db_session, test_project_with_costs, test_invoice):
        """测试项目利润分析"""
        service = CostService(db_session)
        profit = service.get_project_profit_analysis(test_project_with_costs.id)
        
        assert profit["project_id"] == test_project_with_costs.id
        assert profit["contract_amount"] == Decimal("100000")
        assert profit["actual_cost"] == Decimal("50000")
        assert profit["gross_profit"] == Decimal("50000")
        assert profit["profit_margin"] == 50.0
        
        # 成本明细检查
        assert len(profit["cost_breakdown"]) > 0
        # 检查各成本类型的占比
        for item in profit["cost_breakdown"]:
            assert "cost_type" in item
            assert "amount" in item
            assert "percentage" in item

    def test_get_project_profit_analysis_not_found(self, db_session):
        """测试获取不存在的项目利润分析"""
        service = CostService(db_session)
        profit = service.get_project_profit_analysis(99999)
        
        assert "error" in profit
        assert profit["error"] == "项目不存在"