# -*- coding: utf-8 -*-
"""
成本仪表盘服务单元测试
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.models.project import Project, ProjectCost, ProjectPaymentPlan
from app.models.project.financial import FinancialProjectCost
from app.services.cost_dashboard_service import CostDashboardService


@pytest.fixture
def mock_db():
    """模拟数据库会话"""
    return MagicMock(spec=Session)


@pytest.fixture
def service(mock_db):
    """创建服务实例"""
    return CostDashboardService(mock_db)


class TestCostOverview:
    """测试成本总览"""

    def test_get_cost_overview_basic(self, service, mock_db):
        """测试基本的成本总览获取"""
        # Mock查询结果
        mock_db.query.return_value.filter.return_value.count.return_value = 10
        
        # Mock预算和成本统计
        mock_stats = MagicMock()
        mock_stats.total_budget = Decimal("1000000")
        mock_stats.total_actual_cost = Decimal("800000")
        mock_stats.total_contract_amount = Decimal("1200000")
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_stats
        
        # 执行
        result = service.get_cost_overview()
        
        # 验证
        assert result["total_projects"] == 10
        assert result["total_budget"] == 1000000
        assert result["total_actual_cost"] == 800000
        assert result["budget_execution_rate"] == 80.0

    def test_get_cost_overview_zero_budget(self, service, mock_db):
        """测试预算为零的情况"""
        mock_db.query.return_value.filter.return_value.count.return_value = 5
        
        mock_stats = MagicMock()
        mock_stats.total_budget = 0
        mock_stats.total_actual_cost = Decimal("100000")
        mock_stats.total_contract_amount = Decimal("150000")
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_stats
        
        result = service.get_cost_overview()
        
        assert result["budget_execution_rate"] == 0

    def test_cost_overrun_count(self, service, mock_db):
        """测试超支项目统计"""
        # 设置不同的count返回值
        count_values = [10, 3, 5, 2]  # total, overrun, normal, alert
        mock_db.query.return_value.filter.return_value.count.side_effect = count_values
        
        mock_stats = MagicMock()
        mock_stats.total_budget = Decimal("1000000")
        mock_stats.total_actual_cost = Decimal("900000")
        mock_stats.total_contract_amount = Decimal("1200000")
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_stats
        
        result = service.get_cost_overview()
        
        assert result["cost_overrun_count"] == 3
        assert result["cost_normal_count"] == 5
        assert result["cost_alert_count"] == 2


class TestTopProjects:
    """测试TOP项目统计"""

    def test_get_top_projects_basic(self, service, mock_db):
        """测试基本的TOP项目获取"""
        # 创建测试项目
        projects = [
            MagicMock(
                id=i,
                project_code=f"P{i:03d}",
                project_name=f"项目{i}",
                customer_name="客户A",
                pm_name="张三",
                budget_amount=Decimal("100000") * i,
                actual_cost=Decimal("80000") * i,
                contract_amount=Decimal("120000") * i,
                stage="S3",
                status="ST03",
                health="H2",
            )
            for i in range(1, 16)
        ]
        
        mock_db.query.return_value.filter.return_value.all.return_value = projects
        
        result = service.get_top_projects(limit=10)
        
        # 验证返回的TOP项目
        assert len(result["top_cost_projects"]) == 10
        assert len(result["top_overrun_projects"]) <= 10
        assert len(result["top_profit_margin_projects"]) == 10
        assert len(result["bottom_profit_margin_projects"]) == 10
        
        # 验证成本最高项目排序（降序）
        costs = [p["actual_cost"] for p in result["top_cost_projects"]]
        assert costs == sorted(costs, reverse=True)

    def test_top_projects_profit_calculation(self, service, mock_db):
        """测试利润率计算"""
        project = MagicMock(
            id=1,
            project_code="P001",
            project_name="项目1",
            customer_name="客户A",
            pm_name="张三",
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("80000"),
            contract_amount=Decimal("120000"),
            stage="S3",
            status="ST03",
            health="H2",
        )
        
        mock_db.query.return_value.filter.return_value.all.return_value = [project]
        
        result = service.get_top_projects(limit=10)
        
        project_data = result["top_cost_projects"][0]
        
        # 利润 = 合同金额 - 实际成本 = 120000 - 80000 = 40000
        assert project_data["profit"] == 40000
        
        # 利润率 = (40000 / 120000) * 100 = 33.33%
        assert abs(project_data["profit_margin"] - 33.33) < 0.01


class TestCostAlerts:
    """测试成本预警"""

    def test_get_cost_alerts_overrun(self, service, mock_db):
        """测试超支预警"""
        # 超支项目
        project = MagicMock(
            id=1,
            project_code="P001",
            project_name="超支项目",
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("125000"),  # 超支25%
            stage="S3",
        )
        
        mock_db.query.return_value.filter.return_value.all.return_value = [project]
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(total=0)
        
        result = service.get_cost_alerts()
        
        assert result["total_alerts"] == 1
        assert result["high_alerts"] == 1
        
        alert = result["alerts"][0]
        assert alert["alert_type"] == "overrun"
        assert alert["alert_level"] == "high"
        assert alert["variance_pct"] == 25.0

    def test_get_cost_alerts_budget_critical(self, service, mock_db):
        """测试预算告急预警"""
        project = MagicMock(
            id=1,
            project_code="P001",
            project_name="预算告急项目",
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("96000"),  # 96%
            stage="S3",
        )
        
        mock_db.query.return_value.filter.return_value.all.return_value = [project]
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(total=0)
        
        result = service.get_cost_alerts()
        
        assert result["total_alerts"] == 1
        
        alert = result["alerts"][0]
        assert alert["alert_type"] == "budget_critical"
        assert alert["alert_level"] == "high"

    def test_get_cost_alerts_no_alerts(self, service, mock_db):
        """测试无预警情况"""
        project = MagicMock(
            id=1,
            project_code="P001",
            project_name="正常项目",
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("50000"),  # 50%
            stage="S3",
        )
        
        mock_db.query.return_value.filter.return_value.all.return_value = [project]
        mock_db.query.return_value.filter.return_value.first.return_value = MagicMock(total=0)
        
        result = service.get_cost_alerts()
        
        assert result["total_alerts"] == 0
        assert result["high_alerts"] == 0


class TestProjectCostDashboard:
    """测试项目成本仪表盘"""

    def test_get_project_dashboard_not_found(self, service, mock_db):
        """测试项目不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError):
            service.get_project_cost_dashboard(999)

    def test_get_project_dashboard_basic(self, service, mock_db):
        """测试基本的项目仪表盘"""
        project = MagicMock(
            id=1,
            project_code="P001",
            project_name="测试项目",
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("80000"),
            contract_amount=Decimal("120000"),
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = project
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        
        result = service.get_project_cost_dashboard(1)
        
        assert result["project_id"] == 1
        assert result["project_code"] == "P001"
        assert result["budget_amount"] == 100000
        assert result["actual_cost"] == 80000
        assert result["variance"] == -20000
        assert result["variance_pct"] == -20.0

    def test_cost_breakdown(self, service, mock_db):
        """测试成本结构分类"""
        project = MagicMock(
            id=1,
            project_code="P001",
            project_name="测试项目",
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("80000"),
            contract_amount=Decimal("120000"),
        )
        
        # Mock成本分类数据
        cost_data = [
            ("物料成本", Decimal("50000")),
            ("人工成本", Decimal("20000")),
            ("其他", Decimal("10000")),
        ]
        
        mock_db.query.return_value.filter.return_value.first.return_value = project
        
        # 配置多个查询的返回值
        mock_query_result = MagicMock()
        mock_query_result.group_by.return_value.all.side_effect = [cost_data, []]
        mock_db.query.return_value.filter.return_value = mock_query_result
        
        result = service.get_project_cost_dashboard(1)
        
        breakdown = result["cost_breakdown"]
        assert len(breakdown) == 3
        
        # 验证百分比计算
        total = 80000
        for item in breakdown:
            expected_pct = (item["amount"] / total * 100)
            assert abs(item["percentage"] - expected_pct) < 0.01

    def test_monthly_costs(self, service, mock_db):
        """测试月度成本数据"""
        project = MagicMock(
            id=1,
            project_code="P001",
            project_name="测试项目",
            budget_amount=Decimal("120000"),  # 年预算
            actual_cost=Decimal("80000"),
            contract_amount=Decimal("150000"),
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = project
        mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []
        
        result = service.get_project_cost_dashboard(1)
        
        monthly_costs = result["monthly_costs"]
        
        # 应该有12个月的数据
        assert len(monthly_costs) == 12
        
        # 月度预算应该是年预算/12
        expected_month_budget = 120000 / 12
        for month_data in monthly_costs:
            assert month_data["budget"] == round(expected_month_budget, 2)


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_database(self, service, mock_db):
        """测试空数据库"""
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        mock_stats = MagicMock()
        mock_stats.total_budget = None
        mock_stats.total_actual_cost = None
        mock_stats.total_contract_amount = None
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_stats
        
        result = service.get_cost_overview()
        
        assert result["total_projects"] == 0
        assert result["total_budget"] == 0
        assert result["total_actual_cost"] == 0

    def test_negative_cost(self, service, mock_db):
        """测试负成本（退款等特殊情况）"""
        project = MagicMock(
            id=1,
            project_code="P001",
            project_name="退款项目",
            budget_amount=Decimal("100000"),
            actual_cost=Decimal("-10000"),  # 负成本
            contract_amount=Decimal("120000"),
            stage="S3",
            status="ST03",
            health="H2",
        )
        
        mock_db.query.return_value.filter.return_value.all.return_value = [project]
        
        result = service.get_top_projects(limit=10)
        
        project_data = result["top_cost_projects"][0]
        assert project_data["actual_cost"] == -10000

    def test_very_large_numbers(self, service, mock_db):
        """测试非常大的数值"""
        project = MagicMock(
            id=1,
            project_code="P001",
            project_name="大项目",
            budget_amount=Decimal("999999999.99"),
            actual_cost=Decimal("888888888.88"),
            contract_amount=Decimal("1111111111.11"),
            stage="S3",
            status="ST03",
            health="H2",
        )
        
        mock_db.query.return_value.filter.return_value.all.return_value = [project]
        
        result = service.get_top_projects(limit=10)
        
        project_data = result["top_cost_projects"][0]
        assert project_data["budget_amount"] == 999999999.99
        assert project_data["actual_cost"] == 888888888.88
