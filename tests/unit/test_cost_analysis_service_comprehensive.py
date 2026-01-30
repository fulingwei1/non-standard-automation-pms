# -*- coding: utf-8 -*-
"""
CostAnalysisService 综合单元测试

测试覆盖:
- predict_project_cost: 预测项目成本
- check_cost_overrun_alerts: 检查成本超支预警
- compare_project_costs: 对比项目成本
- analyze_cost_trend: 分析成本趋势
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestCostAnalysisServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()
        service = CostAnalysisService(mock_db)

        assert service.db == mock_db

    def test_threshold_constants(self):
        """测试阈值常量"""
        from app.services.cost_analysis_service import CostAnalysisService

        assert CostAnalysisService.WARNING_THRESHOLD == 80
        assert CostAnalysisService.CRITICAL_THRESHOLD == 100


class TestPredictProjectCost:
    """测试 predict_project_cost 方法"""

    def test_returns_error_when_project_not_found(self):
        """测试项目不存在时返回错误"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = CostAnalysisService(mock_db)
        result = service.predict_project_cost(project_id=999)

        assert "error" in result
        assert result["error"] == "项目不存在"

    def test_predicts_cost_with_history(self):
        """测试基于历史数据预测成本"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()

        # Mock project
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = Decimal("100000")
        mock_project.actual_cost = Decimal("30000")

        # Mock timesheets
        mock_timesheet = MagicMock()
        mock_timesheet.hours = 100
        mock_timesheet.user_id = 1
        mock_timesheet.work_date = date.today()

        # Mock tasks
        mock_task = MagicMock()
        mock_task.estimated_hours = 50

        # Setup query returns
        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_timesheet],  # timesheets
        ]

        with patch(
            "app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate",
            return_value=Decimal("100"),
        ):
            # Mock tasks query separately
            mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [mock_task]

            service = CostAnalysisService(mock_db)
            result = service.predict_project_cost(project_id=1)

        assert result["project_id"] == 1
        assert "predicted_total_cost" in result
        assert "cost_variance" in result

    def test_uses_default_hourly_rate_when_no_history(self):
        """测试无历史数据时使用默认时薪"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = Decimal("100000")
        mock_project.actual_cost = Decimal("0")

        mock_task = MagicMock()
        mock_task.estimated_hours = 100

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [mock_task]

        service = CostAnalysisService(mock_db)
        result = service.predict_project_cost(project_id=1)

        # 默认时薪100，剩余100小时，预测剩余成本10000
        assert result["predicted_remaining_cost"] == 10000.0

    def test_calculates_variance_correctly(self):
        """测试正确计算成本偏差"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = Decimal("50000")
        mock_project.actual_cost = Decimal("40000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        service = CostAnalysisService(mock_db)
        result = service.predict_project_cost(project_id=1)

        # 实际成本40000，预算50000
        assert result["cost_variance"] == -10000.0  # 40000 - 50000
        assert result["is_over_budget"] is False

    def test_handles_zero_budget(self):
        """测试处理零预算"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = 0
        mock_project.actual_cost = Decimal("10000")

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        service = CostAnalysisService(mock_db)
        result = service.predict_project_cost(project_id=1)

        assert result["cost_variance"] == 0
        assert result["cost_variance_rate"] == 0
        assert result["is_over_budget"] is False


class TestCheckCostOverrunAlerts:
    """测试 check_cost_overrun_alerts 方法"""

    def test_returns_empty_when_no_projects_exceed_threshold(self):
        """测试无项目超阈值时返回空列表"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = Decimal("100000")
        mock_project.actual_cost = Decimal("50000")  # 50%

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [mock_project]

        service = CostAnalysisService(mock_db)
        result = service.check_cost_overrun_alerts()

        assert result == []

    def test_returns_warning_alert_at_80_percent(self):
        """测试80%时返回警告预警"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = Decimal("100000")
        mock_project.actual_cost = Decimal("85000")  # 85%

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [mock_project]

        with patch.object(CostAnalysisService, "predict_project_cost") as mock_predict:
            mock_predict.return_value = {"predicted_total_cost": 90000}

            service = CostAnalysisService(mock_db)
            result = service.check_cost_overrun_alerts()

        assert len(result) == 1
        assert result[0]["alert_level"] == "WARNING"
        assert result[0]["cost_rate"] == 85.0

    def test_returns_critical_alert_at_100_percent(self):
        """测试100%时返回严重预警"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = Decimal("100000")
        mock_project.actual_cost = Decimal("110000")  # 110%

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [mock_project]

        with patch.object(CostAnalysisService, "predict_project_cost") as mock_predict:
            mock_predict.return_value = {"predicted_total_cost": 120000}

            service = CostAnalysisService(mock_db)
            result = service.check_cost_overrun_alerts()

        assert len(result) == 1
        assert result[0]["alert_level"] == "CRITICAL"

    def test_skips_projects_without_budget(self):
        """测试跳过无预算的项目"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.budget_amount = None
        mock_project.actual_cost = Decimal("50000")

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [mock_project]

        service = CostAnalysisService(mock_db)
        result = service.check_cost_overrun_alerts()

        assert result == []

    def test_filters_by_project_id(self):
        """测试按项目ID筛选"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = Decimal("100000")
        mock_project.actual_cost = Decimal("90000")

        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [mock_project]

        with patch.object(CostAnalysisService, "predict_project_cost") as mock_predict:
            mock_predict.return_value = {"predicted_total_cost": 95000}

            service = CostAnalysisService(mock_db)
            result = service.check_cost_overrun_alerts(project_id=1)

        assert len(result) == 1


class TestCompareProjectCosts:
    """测试 compare_project_costs 方法"""

    def test_returns_error_when_no_projects_found(self):
        """测试项目不存在时返回错误"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = CostAnalysisService(mock_db)
        result = service.compare_project_costs([1, 2, 3])

        assert "error" in result

    def test_compares_multiple_projects(self):
        """测试对比多个项目"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()

        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.project_code = "PJ001"
        mock_project1.project_name = "项目1"
        mock_project1.budget_amount = Decimal("100000")
        mock_project1.actual_cost = Decimal("80000")

        mock_project2 = MagicMock()
        mock_project2.id = 2
        mock_project2.project_code = "PJ002"
        mock_project2.project_name = "项目2"
        mock_project2.budget_amount = Decimal("150000")
        mock_project2.actual_cost = Decimal("120000")

        mock_timesheet1 = MagicMock()
        mock_timesheet1.hours = 100
        mock_timesheet1.user_id = 1
        mock_timesheet1.work_date = date.today()

        mock_timesheet2 = MagicMock()
        mock_timesheet2.hours = 150
        mock_timesheet2.user_id = 2
        mock_timesheet2.work_date = date.today()

        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_project1, mock_project2],  # projects
            [mock_timesheet1],  # project1 timesheets
            [mock_timesheet2],  # project2 timesheets
        ]

        with patch(
            "app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate",
            return_value=Decimal("100"),
        ):
            service = CostAnalysisService(mock_db)
            result = service.compare_project_costs([1, 2])

        assert "projects" in result
        assert "summary" in result
        assert result["summary"]["project_count"] == 2

    def test_calculates_averages_correctly(self):
        """测试正确计算平均值"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()

        mock_project1 = MagicMock()
        mock_project1.id = 1
        mock_project1.project_code = "PJ001"
        mock_project1.project_name = "项目1"
        mock_project1.budget_amount = Decimal("100000")
        mock_project1.actual_cost = Decimal("80000")

        mock_project2 = MagicMock()
        mock_project2.id = 2
        mock_project2.project_code = "PJ002"
        mock_project2.project_name = "项目2"
        mock_project2.budget_amount = Decimal("100000")
        mock_project2.actual_cost = Decimal("60000")

        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_project1, mock_project2],
            [],  # no timesheets for project1
            [],  # no timesheets for project2
        ]

        service = CostAnalysisService(mock_db)
        result = service.compare_project_costs([1, 2])

        assert result["summary"]["avg_total_cost"] == 0  # 没有工时记录
        assert result["summary"]["avg_total_hours"] == 0

    def test_calculates_per_person_stats(self):
        """测试计算人均统计"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "项目1"
        mock_project.budget_amount = Decimal("100000")
        mock_project.actual_cost = Decimal("80000")

        mock_ts1 = MagicMock()
        mock_ts1.hours = 50
        mock_ts1.user_id = 1
        mock_ts1.work_date = date.today()

        mock_ts2 = MagicMock()
        mock_ts2.hours = 100
        mock_ts2.user_id = 2
        mock_ts2.work_date = date.today()

        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [mock_project],
            [mock_ts1, mock_ts2],
        ]

        with patch(
            "app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate",
            return_value=Decimal("100"),
        ):
            service = CostAnalysisService(mock_db)
            result = service.compare_project_costs([1])

        project_data = result["projects"][0]
        assert project_data["personnel_count"] == 2
        assert project_data["total_hours"] == 150


class TestAnalyzeCostTrend:
    """测试 analyze_cost_trend 方法"""

    def test_returns_error_when_project_not_found(self):
        """测试项目不存在时返回错误"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        service = CostAnalysisService(mock_db)
        result = service.analyze_cost_trend(project_id=999)

        assert "error" in result

    def test_analyzes_monthly_trend(self):
        """测试分析月度趋势"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"

        mock_timesheet = MagicMock()
        mock_timesheet.hours = 40
        mock_timesheet.user_id = 1
        mock_timesheet.work_date = date.today()

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [
            mock_timesheet
        ]

        with patch(
            "app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate",
            return_value=Decimal("100"),
        ):
            service = CostAnalysisService(mock_db)
            result = service.analyze_cost_trend(project_id=1, months=3)

        assert "monthly_trend" in result
        assert "total_cost" in result
        assert "total_hours" in result

    def test_uses_default_months(self):
        """测试使用默认月数"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        service = CostAnalysisService(mock_db)
        result = service.analyze_cost_trend(project_id=1)

        # 默认6个月
        assert len(result["monthly_trend"]) >= 6

    def test_handles_empty_timesheets(self):
        """测试处理空工时记录"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        service = CostAnalysisService(mock_db)
        result = service.analyze_cost_trend(project_id=1)

        assert result["total_cost"] == 0
        assert result["total_hours"] == 0

    def test_groups_by_month_correctly(self):
        """测试正确按月分组"""
        from app.services.cost_analysis_service import CostAnalysisService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"

        # 创建两个月的工时记录
        today = date.today()
        last_month = today.replace(day=1) - timedelta(days=1)

        mock_ts1 = MagicMock()
        mock_ts1.hours = 40
        mock_ts1.user_id = 1
        mock_ts1.work_date = today

        mock_ts2 = MagicMock()
        mock_ts2.hours = 60
        mock_ts2.user_id = 1
        mock_ts2.work_date = last_month

        mock_db.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = [
            mock_ts1,
            mock_ts2,
        ]

        with patch(
            "app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate",
            return_value=Decimal("100"),
        ):
            service = CostAnalysisService(mock_db)
            result = service.analyze_cost_trend(project_id=1, months=2)

        assert result["total_hours"] == 100  # 40 + 60
