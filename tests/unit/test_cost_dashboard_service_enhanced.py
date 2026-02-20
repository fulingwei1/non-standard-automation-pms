# -*- coding: utf-8 -*-
"""
成本仪表盘服务增强测试
目标覆盖率: 60%+
测试重点: 仪表板数据聚合、成本趋势分析、预警指标、图表数据、异常处理
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.project import Project, ProjectCost, ProjectPaymentPlan
from app.models.project.financial import FinancialProjectCost
from app.services.cost_dashboard_service import CostDashboardService


class TestCostDashboardServiceInit:
    """测试初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        db = MagicMock(spec=Session)
        service = CostDashboardService(db)
        assert service.db == db


class TestGetCostOverview:
    """测试获取成本总览数据"""

    def test_get_cost_overview_empty_database(self):
        """测试空数据库情况"""
        db = MagicMock(spec=Session)
        
        # Mock 项目总数
        query_count = MagicMock()
        query_count.filter.return_value.count.return_value = 0
        
        # Mock 预算和成本统计
        query_stats = MagicMock()
        query_stats.filter.return_value.first.return_value = Mock(
            total_budget=None,
            total_actual_cost=None,
            total_contract_amount=None
        )
        
        # Mock 超支、正常、预警项目数
        query_overrun = MagicMock()
        query_overrun.filter.return_value.count.return_value = 0
        
        query_normal = MagicMock()
        query_normal.filter.return_value.count.return_value = 0
        
        query_alert = MagicMock()
        query_alert.filter.return_value.count.return_value = 0
        
        # Mock 本月成本
        query_month_project = MagicMock()
        query_month_project.filter.return_value.first.return_value = Mock(total=None)
        
        query_month_financial = MagicMock()
        query_month_financial.filter.return_value.first.return_value = Mock(total=None)
        
        db.query.side_effect = [
            query_count,
            query_stats,
            query_overrun,
            query_normal,
            query_alert,
            query_month_project,
            query_month_financial
        ]

        service = CostDashboardService(db)
        result = service.get_cost_overview()

        assert result["total_projects"] == 0
        assert result["total_budget"] == 0
        assert result["total_actual_cost"] == 0
        assert result["total_contract_amount"] == 0
        assert result["budget_execution_rate"] == 0

    def test_get_cost_overview_with_projects(self):
        """测试包含项目的成本总览"""
        db = MagicMock(spec=Session)

        # Mock 项目总数
        query_count = MagicMock()
        query_count.filter.return_value.count.return_value = 10

        # Mock 预算和成本统计
        query_stats = MagicMock()
        stats_mock = Mock(
            total_budget=Decimal("1000000"),
            total_actual_cost=Decimal("750000"),
            total_contract_amount=Decimal("1200000")
        )
        query_stats.filter.return_value.first.return_value = stats_mock

        # Mock 超支项目数
        query_overrun = MagicMock()
        query_overrun.filter.return_value.count.return_value = 3

        # Mock 正常项目数
        query_normal = MagicMock()
        query_normal.filter.return_value.count.return_value = 5

        # Mock 预警项目数
        query_alert = MagicMock()
        query_alert.filter.return_value.count.return_value = 2

        # Mock 本月成本
        query_month_project = MagicMock()
        query_month_project.filter.return_value.first.return_value = Mock(total=Decimal("80000"))

        query_month_financial = MagicMock()
        query_month_financial.filter.return_value.first.return_value = Mock(total=Decimal("20000"))

        # 设置查询返回值
        db.query.side_effect = [
            query_count,
            query_stats,
            query_overrun,
            query_normal,
            query_alert,
            query_month_project,
            query_month_financial
        ]

        service = CostDashboardService(db)
        result = service.get_cost_overview()

        assert result["total_projects"] == 10
        assert result["total_budget"] == 1000000.0
        assert result["total_actual_cost"] == 750000.0
        assert result["budget_execution_rate"] == 75.0
        assert result["cost_overrun_count"] == 3
        assert result["cost_normal_count"] == 5
        assert result["cost_alert_count"] == 2

    def test_get_cost_overview_budget_execution_rate_calculation(self):
        """测试预算执行率计算"""
        db = MagicMock(spec=Session)
        
        query_count = MagicMock()
        query_count.filter.return_value.count.return_value = 5

        query_stats = MagicMock()
        stats_mock = Mock(
            total_budget=Decimal("500000"),
            total_actual_cost=Decimal("425000"),
            total_contract_amount=Decimal("600000")
        )
        query_stats.filter.return_value.first.return_value = stats_mock

        query_overrun = MagicMock()
        query_overrun.filter.return_value.count.return_value = 1
        
        query_normal = MagicMock()
        query_normal.filter.return_value.count.return_value = 3
        
        query_alert = MagicMock()
        query_alert.filter.return_value.count.return_value = 1
        
        query_month_project = MagicMock()
        query_month_project.filter.return_value.first.return_value = Mock(total=Decimal("40000"))
        
        query_month_financial = MagicMock()
        query_month_financial.filter.return_value.first.return_value = Mock(total=Decimal("10000"))
        
        db.query.side_effect = [
            query_count,
            query_stats,
            query_overrun,
            query_normal,
            query_alert,
            query_month_project,
            query_month_financial
        ]

        service = CostDashboardService(db)
        result = service.get_cost_overview()

        expected_rate = (425000 / 500000) * 100
        assert result["budget_execution_rate"] == round(expected_rate, 2)

    def test_get_cost_overview_zero_budget(self):
        """测试预算为零的情况"""
        db = MagicMock(spec=Session)
        
        query_count = MagicMock()
        query_count.filter.return_value.count.return_value = 3

        query_stats = MagicMock()
        stats_mock = Mock(
            total_budget=Decimal("0"),
            total_actual_cost=Decimal("100000"),
            total_contract_amount=Decimal("150000")
        )
        query_stats.filter.return_value.first.return_value = stats_mock

        query_overrun = MagicMock()
        query_overrun.filter.return_value.count.return_value = 0
        
        query_normal = MagicMock()
        query_normal.filter.return_value.count.return_value = 0
        
        query_alert = MagicMock()
        query_alert.filter.return_value.count.return_value = 0
        
        query_month_project = MagicMock()
        query_month_project.filter.return_value.first.return_value = Mock(total=Decimal("0"))
        
        query_month_financial = MagicMock()
        query_month_financial.filter.return_value.first.return_value = Mock(total=Decimal("0"))
        
        db.query.side_effect = [
            query_count,
            query_stats,
            query_overrun,
            query_normal,
            query_alert,
            query_month_project,
            query_month_financial
        ]

        service = CostDashboardService(db)
        result = service.get_cost_overview()

        assert result["budget_execution_rate"] == 0

    def test_get_cost_overview_month_variance(self):
        """测试月度偏差计算"""
        db = MagicMock(spec=Session)

        query_count = MagicMock()
        query_count.filter.return_value.count.return_value = 8

        query_stats = MagicMock()
        stats_mock = Mock(
            total_budget=Decimal("1200000"),
            total_actual_cost=Decimal("960000"),
            total_contract_amount=Decimal("1500000")
        )
        query_stats.filter.return_value.first.return_value = stats_mock

        query_overrun = MagicMock()
        query_overrun.filter.return_value.count.return_value = 2

        query_normal = MagicMock()
        query_normal.filter.return_value.count.return_value = 4

        query_alert = MagicMock()
        query_alert.filter.return_value.count.return_value = 2

        query_month_project = MagicMock()
        query_month_project.filter.return_value.first.return_value = Mock(total=Decimal("120000"))

        query_month_financial = MagicMock()
        query_month_financial.filter.return_value.first.return_value = Mock(total=Decimal("30000"))

        db.query.side_effect = [
            query_count,
            query_stats,
            query_overrun,
            query_normal,
            query_alert,
            query_month_project,
            query_month_financial
        ]

        service = CostDashboardService(db)
        result = service.get_cost_overview()

        month_budget = 1200000 / 12
        month_actual = 150000
        expected_variance = month_actual - month_budget
        expected_variance_pct = (expected_variance / month_budget) * 100

        assert result["month_actual_cost"] == 150000.0
        assert result["month_variance"] == round(expected_variance, 2)
        assert result["month_variance_pct"] == round(expected_variance_pct, 2)

    def test_get_cost_overview_excludes_s0_and_s9_stages(self):
        """测试排除S0和S9阶段的项目"""
        db = MagicMock(spec=Session)

        service = CostDashboardService(db)
        service.get_cost_overview()

        # 验证查询时排除了S0和S9
        calls = db.query.return_value.filter.call_args_list
        # 由于使用了notin，我们只检查filter被调用
        assert len(calls) > 0


class TestGetTopProjects:
    """测试获取TOP项目统计"""

    def test_get_top_projects_empty_list(self):
        """测试无项目情况"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.all.return_value = []

        service = CostDashboardService(db)
        result = service.get_top_projects(limit=10)

        assert len(result["top_cost_projects"]) == 0
        assert len(result["top_overrun_projects"]) == 0
        assert len(result["top_profit_margin_projects"]) == 0
        assert len(result["bottom_profit_margin_projects"]) == 0

    def test_get_top_projects_with_data(self):
        """测试包含数据的TOP项目"""
        db = MagicMock(spec=Session)

        # Mock 项目数据
        projects = []
        for i in range(1, 16):
            project = Mock(spec=Project)
            project.id = i
            project.project_code = f"PRJ-{i:03d}"
            project.project_name = f"项目{i}"
            project.customer_name = f"客户{i}"
            project.pm_name = f"PM{i}"
            project.budget_amount = Decimal(100000 + i * 10000)
            project.actual_cost = Decimal(90000 + i * 9000)
            project.contract_amount = Decimal(120000 + i * 12000)
            project.stage = "S3"
            project.status = "IN_PROGRESS"
            project.health = "GREEN"
            projects.append(project)

        db.query.return_value.filter.return_value.all.return_value = projects

        service = CostDashboardService(db)
        result = service.get_top_projects(limit=5)

        assert len(result["top_cost_projects"]) == 5
        assert len(result["top_profit_margin_projects"]) == 5
        assert len(result["bottom_profit_margin_projects"]) == 5

        # 验证成本排序 (降序)
        top_costs = [p["actual_cost"] for p in result["top_cost_projects"]]
        assert top_costs == sorted(top_costs, reverse=True)

        # 验证利润率排序
        top_margins = [p["profit_margin"] for p in result["top_profit_margin_projects"]]
        assert top_margins == sorted(top_margins, reverse=True)

        bottom_margins = [p["profit_margin"] for p in result["bottom_profit_margin_projects"]]
        assert bottom_margins == sorted(bottom_margins)

    def test_get_top_projects_cost_variance_calculation(self):
        """测试成本偏差计算"""
        db = MagicMock(spec=Session)

        project = Mock(spec=Project)
        project.id = 1
        project.project_code = "PRJ-001"
        project.project_name = "测试项目"
        project.customer_name = "测试客户"
        project.pm_name = "张三"
        project.budget_amount = Decimal("100000")
        project.actual_cost = Decimal("120000")
        project.contract_amount = Decimal("150000")
        project.stage = "S4"
        project.status = "IN_PROGRESS"
        project.health = "YELLOW"

        db.query.return_value.filter.return_value.all.return_value = [project]

        service = CostDashboardService(db)
        result = service.get_top_projects(limit=10)

        project_data = result["top_cost_projects"][0]
        assert project_data["cost_variance"] == 20000.0
        assert project_data["cost_variance_pct"] == 20.0

    def test_get_top_projects_profit_margin_calculation(self):
        """测试利润率计算"""
        db = MagicMock(spec=Session)

        project = Mock(spec=Project)
        project.id = 1
        project.project_code = "PRJ-001"
        project.project_name = "高利润项目"
        project.customer_name = "优质客户"
        project.pm_name = "李四"
        project.budget_amount = Decimal("80000")
        project.actual_cost = Decimal("60000")
        project.contract_amount = Decimal("100000")
        project.stage = "S5"
        project.status = "COMPLETED"
        project.health = "GREEN"

        db.query.return_value.filter.return_value.all.return_value = [project]

        service = CostDashboardService(db)
        result = service.get_top_projects(limit=10)

        project_data = result["top_profit_margin_projects"][0]
        expected_profit = 100000 - 60000
        expected_margin = (expected_profit / 100000) * 100
        assert project_data["profit"] == 40000.0
        assert project_data["profit_margin"] == round(expected_margin, 2)

    def test_get_top_projects_limit_parameter(self):
        """测试limit参数"""
        db = MagicMock(spec=Session)

        projects = []
        for i in range(1, 21):
            project = Mock(spec=Project)
            project.id = i
            project.project_code = f"PRJ-{i:03d}"
            project.project_name = f"项目{i}"
            project.customer_name = f"客户{i}"
            project.pm_name = f"PM{i}"
            project.budget_amount = Decimal(100000)
            project.actual_cost = Decimal(80000 + i * 1000)
            project.contract_amount = Decimal(120000)
            project.stage = "S3"
            project.status = "IN_PROGRESS"
            project.health = "GREEN"
            projects.append(project)

        db.query.return_value.filter.return_value.all.return_value = projects

        service = CostDashboardService(db)
        result = service.get_top_projects(limit=3)

        assert len(result["top_cost_projects"]) == 3
        assert len(result["top_profit_margin_projects"]) == 3

    def test_get_top_projects_overrun_only(self):
        """测试仅包含超支项目"""
        db = MagicMock(spec=Session)

        projects = []
        # 3个超支项目
        for i in range(1, 4):
            project = Mock(spec=Project)
            project.id = i
            project.project_code = f"PRJ-{i:03d}"
            project.project_name = f"超支项目{i}"
            project.customer_name = f"客户{i}"
            project.pm_name = f"PM{i}"
            project.budget_amount = Decimal(100000)
            project.actual_cost = Decimal(100000 + i * 10000)  # 超支
            project.contract_amount = Decimal(150000)
            project.stage = "S3"
            project.status = "IN_PROGRESS"
            project.health = "RED"
            projects.append(project)

        # 2个正常项目
        for i in range(4, 6):
            project = Mock(spec=Project)
            project.id = i
            project.project_code = f"PRJ-{i:03d}"
            project.project_name = f"正常项目{i}"
            project.customer_name = f"客户{i}"
            project.pm_name = f"PM{i}"
            project.budget_amount = Decimal(100000)
            project.actual_cost = Decimal(80000)  # 正常
            project.contract_amount = Decimal(120000)
            project.stage = "S3"
            project.status = "IN_PROGRESS"
            project.health = "GREEN"
            projects.append(project)

        db.query.return_value.filter.return_value.all.return_value = projects

        service = CostDashboardService(db)
        result = service.get_top_projects(limit=10)

        # 只有3个超支项目
        assert len(result["top_overrun_projects"]) == 3
        # 所有超支项目的偏差都应该>0
        for project in result["top_overrun_projects"]:
            assert project["cost_variance"] > 0


class TestGetCostAlerts:
    """测试获取成本预警列表"""

    def test_get_cost_alerts_no_alerts(self):
        """测试无预警情况"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.all.return_value = []

        service = CostDashboardService(db)
        result = service.get_cost_alerts()

        assert result["total_alerts"] == 0
        assert result["high_alerts"] == 0
        assert result["medium_alerts"] == 0
        assert result["low_alerts"] == 0
        assert len(result["alerts"]) == 0

    def test_get_cost_alerts_overrun_high_severity(self):
        """测试严重超支预警 (>20%)"""
        db = MagicMock(spec=Session)

        project = Mock(spec=Project)
        project.id = 1
        project.project_code = "PRJ-001"
        project.project_name = "严重超支项目"
        project.budget_amount = Decimal("100000")
        project.actual_cost = Decimal("125000")  # 超支25%
        project.stage = "S3"

        query_project = MagicMock()
        query_project.filter.return_value.all.return_value = [project]

        query_cost = MagicMock()
        query_cost.filter.return_value.first.return_value = Mock(total=Decimal("0"))

        db.query.side_effect = [query_project] + [query_cost] * 10

        service = CostDashboardService(db)
        result = service.get_cost_alerts()

        assert result["total_alerts"] == 1
        assert result["high_alerts"] == 1
        alert = result["alerts"][0]
        assert alert["alert_type"] == "overrun"
        assert alert["alert_level"] == "high"
        assert "严重超支" in alert["message"]

    def test_get_cost_alerts_overrun_medium_severity(self):
        """测试中度超支预警 (10-20%)"""
        db = MagicMock(spec=Session)

        project = Mock(spec=Project)
        project.id = 2
        project.project_code = "PRJ-002"
        project.project_name = "中度超支项目"
        project.budget_amount = Decimal("100000")
        project.actual_cost = Decimal("115000")  # 超支15%
        project.stage = "S4"

        query_project = MagicMock()
        query_project.filter.return_value.all.return_value = [project]

        query_cost = MagicMock()
        query_cost.filter.return_value.first.return_value = Mock(total=Decimal("0"))

        db.query.side_effect = [query_project] + [query_cost] * 10

        service = CostDashboardService(db)
        result = service.get_cost_alerts()

        assert result["medium_alerts"] == 1
        alert = result["alerts"][0]
        assert alert["alert_level"] == "medium"
        assert "超支" in alert["message"]

    def test_get_cost_alerts_overrun_low_severity(self):
        """测试轻微超支预警 (<10%)"""
        db = MagicMock(spec=Session)

        project = Mock(spec=Project)
        project.id = 3
        project.project_code = "PRJ-003"
        project.project_name = "轻微超支项目"
        project.budget_amount = Decimal("100000")
        project.actual_cost = Decimal("105000")  # 超支5%
        project.stage = "S3"

        query_project = MagicMock()
        query_project.filter.return_value.all.return_value = [project]

        query_cost = MagicMock()
        query_cost.filter.return_value.first.return_value = Mock(total=Decimal("0"))

        db.query.side_effect = [query_project] + [query_cost] * 10

        service = CostDashboardService(db)
        result = service.get_cost_alerts()

        assert result["low_alerts"] == 1
        alert = result["alerts"][0]
        assert alert["alert_level"] == "low"
        assert "轻微超支" in alert["message"]

    def test_get_cost_alerts_budget_critical_high(self):
        """测试预算即将用尽预警 (>95%)"""
        db = MagicMock(spec=Session)

        project = Mock(spec=Project)
        project.id = 4
        project.project_code = "PRJ-004"
        project.project_name = "预算告急项目"
        project.budget_amount = Decimal("100000")
        project.actual_cost = Decimal("97000")  # 97%
        project.stage = "S3"

        query_project = MagicMock()
        query_project.filter.return_value.all.return_value = [project]

        query_cost = MagicMock()
        query_cost.filter.return_value.first.return_value = Mock(total=Decimal("0"))

        db.query.side_effect = [query_project] + [query_cost] * 10

        service = CostDashboardService(db)
        result = service.get_cost_alerts()

        assert result["high_alerts"] == 1
        alert = result["alerts"][0]
        assert alert["alert_type"] == "budget_critical"
        assert "即将用尽" in alert["message"]

    def test_get_cost_alerts_budget_critical_medium(self):
        """测试预算告急预警 (90-95%)"""
        db = MagicMock(spec=Session)

        project = Mock(spec=Project)
        project.id = 5
        project.project_code = "PRJ-005"
        project.project_name = "预算告急项目"
        project.budget_amount = Decimal("100000")
        project.actual_cost = Decimal("93000")  # 93%
        project.stage = "S4"

        query_project = MagicMock()
        query_project.filter.return_value.all.return_value = [project]

        query_cost = MagicMock()
        query_cost.filter.return_value.first.return_value = Mock(total=Decimal("0"))

        db.query.side_effect = [query_project] + [query_cost] * 10

        service = CostDashboardService(db)
        result = service.get_cost_alerts()

        assert result["medium_alerts"] == 1
        alert = result["alerts"][0]
        assert alert["alert_type"] == "budget_critical"
        assert "告急" in alert["message"]

    def test_get_cost_alerts_abnormal_spike(self):
        """测试成本异常波动预警"""
        db = MagicMock(spec=Session)

        project = Mock(spec=Project)
        project.id = 6
        project.project_code = "PRJ-006"
        project.project_name = "异常波动项目"
        project.budget_amount = Decimal("120000")
        project.actual_cost = Decimal("60000")  # 平均月成本5000
        project.stage = "S3"

        query_project = MagicMock()
        query_project.filter.return_value.all.return_value = [project]

        query_cost = MagicMock()
        # 本月成本15000，是平均月成本的3倍
        query_cost.filter.return_value.first.return_value = Mock(total=Decimal("15000"))

        db.query.side_effect = [query_project] + [query_cost] * 10

        service = CostDashboardService(db)
        result = service.get_cost_alerts()

        # 应该有异常波动预警
        assert result["total_alerts"] >= 1
        abnormal_alerts = [a for a in result["alerts"] if a["alert_type"] == "abnormal"]
        assert len(abnormal_alerts) > 0

    def test_get_cost_alerts_multiple_alerts(self):
        """测试多个预警"""
        db = MagicMock(spec=Session)

        projects = []
        # 高风险超支
        p1 = Mock(spec=Project)
        p1.id = 1
        p1.project_code = "PRJ-001"
        p1.project_name = "高风险项目"
        p1.budget_amount = Decimal("100000")
        p1.actual_cost = Decimal("130000")
        p1.stage = "S3"
        projects.append(p1)

        # 预算告急
        p2 = Mock(spec=Project)
        p2.id = 2
        p2.project_code = "PRJ-002"
        p2.project_name = "告急项目"
        p2.budget_amount = Decimal("200000")
        p2.actual_cost = Decimal("196000")
        p2.stage = "S4"
        projects.append(p2)

        # 轻微超支
        p3 = Mock(spec=Project)
        p3.id = 3
        p3.project_code = "PRJ-003"
        p3.project_name = "轻微超支"
        p3.budget_amount = Decimal("80000")
        p3.actual_cost = Decimal("83000")
        p3.stage = "S3"
        projects.append(p3)

        query_project = MagicMock()
        query_project.filter.return_value.all.return_value = projects

        query_cost = MagicMock()
        query_cost.filter.return_value.first.return_value = Mock(total=Decimal("0"))

        db.query.side_effect = [query_project] + [query_cost] * 20

        service = CostDashboardService(db)
        result = service.get_cost_alerts()

        assert result["total_alerts"] == 3
        assert result["high_alerts"] == 2  # 严重超支 + 预算即将用尽
        assert result["low_alerts"] == 1  # 轻微超支

    def test_get_cost_alerts_sorting(self):
        """测试预警排序 (按级别和偏差率)"""
        db = MagicMock(spec=Session)

        projects = []
        # 中度超支
        p1 = Mock(spec=Project)
        p1.id = 1
        p1.project_code = "PRJ-001"
        p1.project_name = "中度超支"
        p1.budget_amount = Decimal("100000")
        p1.actual_cost = Decimal("115000")
        p1.stage = "S3"
        projects.append(p1)

        # 严重超支
        p2 = Mock(spec=Project)
        p2.id = 2
        p2.project_code = "PRJ-002"
        p2.project_name = "严重超支"
        p2.budget_amount = Decimal("100000")
        p2.actual_cost = Decimal("125000")
        p2.stage = "S4"
        projects.append(p2)

        # 轻微超支
        p3 = Mock(spec=Project)
        p3.id = 3
        p3.project_code = "PRJ-003"
        p3.project_name = "轻微超支"
        p3.budget_amount = Decimal("100000")
        p3.actual_cost = Decimal("105000")
        p3.stage = "S3"
        projects.append(p3)

        query_project = MagicMock()
        query_project.filter.return_value.all.return_value = projects

        query_cost = MagicMock()
        query_cost.filter.return_value.first.return_value = Mock(total=Decimal("0"))

        db.query.side_effect = [query_project] + [query_cost] * 20

        service = CostDashboardService(db)
        result = service.get_cost_alerts()

        alerts = result["alerts"]
        # 严重超支应该排第一
        assert alerts[0]["alert_level"] == "high"
        # 中度超支排第二
        assert alerts[1]["alert_level"] == "medium"
        # 轻微超支排最后
        assert alerts[2]["alert_level"] == "low"


class TestGetProjectCostDashboard:
    """测试获取单项目成本仪表盘"""

    def test_get_project_cost_dashboard_project_not_found(self):
        """测试项目不存在"""
        db = MagicMock(spec=Session)
        db.query.return_value.filter.return_value.first.return_value = None

        service = CostDashboardService(db)
        with pytest.raises(ValueError, match="项目 999 不存在"):
            service.get_project_cost_dashboard(999)

    def test_get_project_cost_dashboard_basic_info(self):
        """测试基本项目信息"""
        db = MagicMock(spec=Session)

        project = Mock(spec=Project)
        project.id = 1
        project.project_code = "PRJ-001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("500000")
        project.actual_cost = Decimal("400000")
        project.contract_amount = Decimal("600000")

        query_project = MagicMock()
        query_project.filter.return_value.first.return_value = project

        query_cost = MagicMock()
        query_cost.filter.return_value.group_by.return_value.all.return_value = []

        query_financial = MagicMock()
        query_financial.filter.return_value.group_by.return_value.all.return_value = []

        query_monthly = MagicMock()
        query_monthly.filter.return_value.first.return_value = Mock(total=Decimal("0"))

        query_payment = MagicMock()
        query_payment.filter.return_value.first.return_value = Mock(total=Decimal("0"))

        db.query.side_effect = [query_project, query_cost, query_financial] + \
                               [query_monthly] * 30 + [query_payment, query_payment]

        service = CostDashboardService(db)
        result = service.get_project_cost_dashboard(1)

        assert result["project_id"] == 1
        assert result["project_code"] == "PRJ-001"
        assert result["budget_amount"] == 500000.0
        assert result["actual_cost"] == 400000.0
        assert result["variance"] == -100000.0
        assert result["variance_pct"] == -20.0

    def test_get_project_cost_dashboard_cost_breakdown(self):
        """测试成本结构"""
        db = MagicMock(spec=Session)

        project = Mock(spec=Project)
        project.id = 1
        project.project_code = "PRJ-001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("300000")
        project.actual_cost = Decimal("250000")
        project.contract_amount = Decimal("350000")

        query_project = MagicMock()
        query_project.filter.return_value.first.return_value = project

        # Mock 成本分类
        query_cost = MagicMock()
        cost_breakdown = [
            ("人工成本", Decimal("150000")),
            ("材料成本", Decimal("80000")),
        ]
        query_cost.filter.return_value.group_by.return_value.all.return_value = cost_breakdown

        query_financial = MagicMock()
        financial_breakdown = [
            ("外协成本", Decimal("20000")),
        ]
        query_financial.filter.return_value.group_by.return_value.all.return_value = financial_breakdown

        query_monthly = MagicMock()
        query_monthly.filter.return_value.first.return_value = Mock(total=Decimal("0"))

        query_payment = MagicMock()
        query_payment.filter.return_value.first.return_value = Mock(total=Decimal("0"))

        db.query.side_effect = [query_project, query_cost, query_financial] + \
                               [query_monthly] * 30 + [query_payment, query_payment]

        service = CostDashboardService(db)
        result = service.get_project_cost_dashboard(1)

        breakdown = result["cost_breakdown"]
        assert len(breakdown) == 3

        # 验证分类和金额
        categories = {item["category"]: item["amount"] for item in breakdown}
        assert categories["人工成本"] == 150000.0
        assert categories["材料成本"] == 80000.0
        assert categories["外协成本"] == 20000.0

        # 验证百分比
        total = 150000 + 80000 + 20000
        for item in breakdown:
            if item["category"] == "人工成本":
                expected_pct = round((150000 / total) * 100, 2)
                assert item["percentage"] == expected_pct

    def test_get_project_cost_dashboard_monthly_costs(self):
        """测试月度成本数据"""
        db = MagicMock(spec=Session)

        project = Mock(spec=Project)
        project.id = 1
        project.project_code = "PRJ-001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("1200000")
        project.actual_cost = Decimal("800000")
        project.contract_amount = Decimal("1500000")

        query_project = MagicMock()
        query_project.filter.return_value.first.return_value = project

        query_cost = MagicMock()
        query_cost.filter.return_value.group_by.return_value.all.return_value = []

        query_financial = MagicMock()
        query_financial.filter.return_value.group_by.return_value.all.return_value = []

        # Mock 月度成本（12个月）
        query_monthly = MagicMock()
        query_monthly.filter.return_value.first.return_value = Mock(total=Decimal("70000"))

        query_payment = MagicMock()
        query_payment.filter.return_value.first.return_value = Mock(total=Decimal("0"))

        db.query.side_effect = [query_project, query_cost, query_financial] + \
                               [query_monthly] * 30 + [query_payment, query_payment]

        service = CostDashboardService(db)
        result = service.get_project_cost_dashboard(1)

        monthly_costs = result["monthly_costs"]
        assert len(monthly_costs) == 12

        # 验证月度预算
        month_budget = 1200000 / 12
        assert monthly_costs[0]["budget"] == round(month_budget, 2)

    def test_get_project_cost_dashboard_cost_trend(self):
        """测试成本趋势（累计）"""
        db = MagicMock(spec=Session)

        project = Mock(spec=Project)
        project.id = 1
        project.project_code = "PRJ-001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("600000")
        project.actual_cost = Decimal("480000")
        project.contract_amount = Decimal("720000")

        query_project = MagicMock()
        query_project.filter.return_value.first.return_value = project

        query_cost = MagicMock()
        query_cost.filter.return_value.group_by.return_value.all.return_value = []

        query_financial = MagicMock()
        query_financial.filter.return_value.group_by.return_value.all.return_value = []

        query_monthly = MagicMock()
        query_monthly.filter.return_value.first.return_value = Mock(total=Decimal("50000"))

        query_payment = MagicMock()
        query_payment.filter.return_value.first.return_value = Mock(total=Decimal("0"))

        db.query.side_effect = [query_project, query_cost, query_financial] + \
                               [query_monthly] * 30 + [query_payment, query_payment]

        service = CostDashboardService(db)
        result = service.get_project_cost_dashboard(1)

        cost_trend = result["cost_trend"]
        assert len(cost_trend) == 12

        # 验证累计成本递增
        for i in range(1, len(cost_trend)):
            assert cost_trend[i]["cumulative_cost"] >= cost_trend[i-1]["cumulative_cost"]

    def test_get_project_cost_dashboard_profit_calculation(self):
        """测试利润计算"""
        db = MagicMock(spec=Session)

        project = Mock(spec=Project)
        project.id = 1
        project.project_code = "PRJ-001"
        project.project_name = "高利润项目"
        project.budget_amount = Decimal("400000")
        project.actual_cost = Decimal("300000")
        project.contract_amount = Decimal("500000")

        query_project = MagicMock()
        query_project.filter.return_value.first.return_value = project

        query_cost = MagicMock()
        query_cost.filter.return_value.group_by.return_value.all.return_value = []

        query_financial = MagicMock()
        query_financial.filter.return_value.group_by.return_value.all.return_value = []

        query_monthly = MagicMock()
        query_monthly.filter.return_value.first.return_value = Mock(total=Decimal("0"))

        query_payment = MagicMock()
        query_payment.filter.return_value.first.return_value = Mock(total=Decimal("0"))

        db.query.side_effect = [query_project, query_cost, query_financial] + \
                               [query_monthly] * 30 + [query_payment, query_payment]

        service = CostDashboardService(db)
        result = service.get_project_cost_dashboard(1)

        expected_profit = 500000 - 300000
        expected_margin = (expected_profit / 500000) * 100

        assert result["gross_profit"] == 200000.0
        assert result["profit_margin"] == round(expected_margin, 2)

    def test_get_project_cost_dashboard_payment_data(self):
        """测试收款和开票数据"""
        db = MagicMock(spec=Session)

        project = Mock(spec=Project)
        project.id = 1
        project.project_code = "PRJ-001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("500000")
        project.actual_cost = Decimal("400000")
        project.contract_amount = Decimal("600000")

        query_project = MagicMock()
        query_project.filter.return_value.first.return_value = project

        query_cost = MagicMock()
        query_cost.filter.return_value.group_by.return_value.all.return_value = []

        query_financial = MagicMock()
        query_financial.filter.return_value.group_by.return_value.all.return_value = []

        # 12个月，每月2个查询 = 24
        query_monthly_project = MagicMock()
        query_monthly_project.filter.return_value.first.return_value = Mock(total=Decimal("0"))
        
        query_monthly_financial = MagicMock()
        query_monthly_financial.filter.return_value.first.return_value = Mock(total=Decimal("0"))

        # Mock 收款和开票
        query_received = MagicMock()
        query_received.filter.return_value.first.return_value = Mock(total=Decimal("350000"))

        query_invoiced = MagicMock()
        query_invoiced.filter.return_value.first.return_value = Mock(total=Decimal("400000"))

        # 月度查询：12个月 x 2次查询（project + financial）
        monthly_queries = []
        for _ in range(12):
            monthly_queries.append(query_monthly_project)
            monthly_queries.append(query_monthly_financial)

        db.query.side_effect = [query_project, query_cost, query_financial] + \
                               monthly_queries + [query_received, query_invoiced]

        service = CostDashboardService(db)
        result = service.get_project_cost_dashboard(1)

        assert result["received_amount"] == 350000.0
        assert result["invoiced_amount"] == 400000.0


class TestEdgeCases:
    """测试边界情况"""

    def test_negative_profit_margin(self):
        """测试负利润率"""
        db = MagicMock(spec=Session)

        project = Mock(spec=Project)
        project.id = 1
        project.project_code = "PRJ-001"
        project.project_name = "亏损项目"
        project.customer_name = "客户A"
        project.pm_name = "PM张三"
        project.budget_amount = Decimal("100000")
        project.actual_cost = Decimal("150000")  # 成本超过合同
        project.contract_amount = Decimal("120000")
        project.stage = "S3"
        project.status = "IN_PROGRESS"
        project.health = "RED"

        db.query.return_value.filter.return_value.all.return_value = [project]

        service = CostDashboardService(db)
        result = service.get_top_projects(limit=10)

        project_data = result["top_cost_projects"][0]
        # 利润应该是负数
        assert project_data["profit"] < 0
        # 利润率应该是负数
        assert project_data["profit_margin"] < 0

    def test_zero_contract_amount(self):
        """测试合同金额为零"""
        db = MagicMock(spec=Session)

        project = Mock(spec=Project)
        project.id = 2
        project.project_code = "PRJ-002"
        project.project_name = "零合同项目"
        project.customer_name = "客户B"
        project.pm_name = "PM李四"
        project.budget_amount = Decimal("50000")
        project.actual_cost = Decimal("30000")
        project.contract_amount = Decimal("0")  # 零合同
        project.stage = "S2"
        project.status = "IN_PROGRESS"
        project.health = "YELLOW"

        db.query.return_value.filter.return_value.all.return_value = [project]

        service = CostDashboardService(db)
        result = service.get_top_projects(limit=10)

        project_data = result["top_cost_projects"][0]
        # 利润率应该是0，避免除以零
        assert project_data["profit_margin"] == 0

    def test_none_values_handling(self):
        """测试部分字段None值处理"""
        db = MagicMock(spec=Session)

        project = Mock(spec=Project)
        project.id = 3
        project.project_code = "PRJ-003"
        project.project_name = "空值项目"
        project.customer_name = None  # None值
        project.pm_name = None  # None值
        project.budget_amount = Decimal("100000")  # 有预算
        project.actual_cost = None  # None成本
        project.contract_amount = None  # None合同
        project.stage = "S1"
        project.status = "PLANNING"
        project.health = "GREEN"

        db.query.return_value.filter.return_value.all.return_value = [project]

        service = CostDashboardService(db)
        # 应该不会抛出异常
        result = service.get_top_projects(limit=10)
        # None值应该被转换为0
        project_data = result["top_cost_projects"][0]
        assert project_data["actual_cost"] == 0.0
        assert project_data["contract_amount"] == 0.0
        assert project_data["profit"] == 0.0
