# -*- coding: utf-8 -*-
"""
成本分析服务单元测试

测试 CostAnalysisService 类的所有公共和私有方法
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest
from unittest.mock import Mock, MagicMock, patch

from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User
from app.services.cost_analysis_service import CostAnalysisService


class TestCostAnalysisService:
    """成本分析服务测试类"""

    @pytest.fixture
    def db_session(self):
        """模拟数据库会话"""
        return MagicMock()

    @pytest.fixture
    def service(self, db_session):
        """创建服务实例"""
        return CostAnalysisService(db_session)

    @pytest.fixture
    def mock_project(self):
        """创建模拟项目对象"""
        project = Mock(spec=Project)
        project.id = 1
        project.project_code = "PJ-TEST-001"
        project.project_name = "测试项目"
        project.budget_amount = Decimal("1000000")
        project.actual_cost = Decimal("80000")
        project.total_hours = Decimal("1000")
        project.is_active = True
        return project

    @pytest.fixture
    def mock_timesheet(self, mock_project):
        """创建模拟工时记录"""
        ts = Mock(spec=Timesheet)
        ts.id = 1
        ts.project_id = mock_project.id
        ts.user_id = 1
        ts.work_date = date.today()
        ts.hours = 40
        ts.status = "APPROVED"
        ts.user = Mock(spec=User)
        ts.user.id = 1
        ts.user.hourly_rate = Decimal("100")
        return ts

    @pytest.fixture
    def mock_task(self, mock_project):
        """创建模拟任务"""
        task = Mock()
        task.project_id = mock_project.id
        task.status = "IN_PROGRESS"
        task.estimated_hours = Decimal("60")
        return task


class TestPredictProjectCost(TestCostAnalysisService):
    """测试 predict_project_cost 方法"""

    def test_predict_project_cost_with_history(
        self, service, db_session, mock_project, mock_timesheet
    ):
        """基于历史工时数据预测成本"""
        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_project
        )
        db_session.query.return_value.filter.return_value.all.return_value = [
            mock_timesheet
        ]
        db_session.query.return_value.filter.return_value.all.return_value = [mock_task]

        with patch(
            "app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate",
            return_value=Decimal("100"),
        ):
            result = service.predict_project_cost(1, based_on_history=True)

        assert result["project_id"] == 1
        assert result["budget"] == 1000000
        assert result["actual_cost"] == 80000
        assert result["cost_variance"] == pytest.approx(0, abs=1e-3)
        assert result["predicted_total_cost"] == pytest.approx(100000, rel=1e-2)

    def test_predict_project_cost_no_history(
        self, service, db_session, mock_project, mock_task
    ):
        """没有历史数据时使用默认时薪"""
        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_project
        )
        db_session.query.return_value.filter.return_value.all.return_value = []
        db_session.query.return_value.filter.return_value.all.return_value = [mock_task]

        with patch(
            "app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate",
            return_value=Decimal("100"),
        ):
            result = service.predict_project_cost(1, based_on_history=True)

        assert result["cost_variance"] == pytest.approx(0.2, abs=1e-3)
        assert result["is_over_budget"] is False

    def test_predict_project_cost_zero_budget(self, service, db_session, mock_project):
        """预算为零"""
        mock_project.budget_amount = Decimal("0")

        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_project
        )
        db_session.query.return_value.filter.return_value.all.return_value = [
            mock_timesheet
        ]
        db_session.query.return_value.filter.return_value.all.return_value = [mock_task]

        with patch(
            "app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate",
            return_value=Decimal("100"),
        ):
            result = service.predict_project_cost(1, based_on_history=True)

        assert result["is_over_budget"] is False

    def test_predict_project_cost_project_not_exists(self, service, db_session):
        """项目不存在"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = service.predict_project_cost(999, based_on_history=True)

        assert result["error"] == "项目不存在"


class TestCheckCostOverrunAlerts(TestCostAnalysisService):
    """测试 check_cost_overrun_alerts 方法"""

    def test_check_cost_overrun_alerts_critical(
        self, service, db_session, mock_project
    ):
        """严重预警（成本超支100%）"""
        mock_project.budget_amount = Decimal("1000000")
        mock_project.actual_cost = Decimal("2000000")

        db_session.query.return_value.filter.return_value.all.return_value = [
            mock_project
        ]

        alerts = service.check_cost_overrun_alerts()

        assert len(alerts) == 1
        assert alerts[0]["alert_level"] == "CRITICAL"
        assert "成本超支预警" in alerts[0]["message"]

    def test_check_cost_overrun_alerts_warning(self, service, db_session, mock_project):
        """警告预警（成本超支80%）"""
        mock_project.budget_amount = Decimal("1000000")
        mock_project.actual_cost = Decimal("1800000")

        db_session.query.return_value.filter.return_value.all.return_value = [
            mock_project
        ]

        with patch(
            "app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate",
            return_value=Decimal("100"),
        ) as mock_rate:
            alerts = service.check_cost_overrun_alerts()

        assert len(alerts) == 1
        assert alerts[0]["alert_level"] == "WARNING"

    def test_check_cost_overrun_alerts_no_overrun(
        self, service, db_session, mock_project
    ):
        """没有超支"""
        mock_project.budget_amount = Decimal("1000000")
        mock_project.actual_cost = Decimal("900000")

        db_session.query.return_value.filter.return_value.all.return_value = [
            mock_project
        ]

        alerts = service.check_cost_overrun_alerts()

        assert len(alerts) == 0

    def test_check_cost_overrun_alerts_no_budget(
        self, service, db_session, mock_project
    ):
        """没有预算的项目"""
        mock_project.budget_amount = None
        mock_project.actual_cost = Decimal("900000")

        db_session.query.return_value.filter.return_value.all.return_value = [
            mock_project
        ]

        alerts = service.check_cost_overrun_alerts()

        assert len(alerts) == 0

    def test_check_cost_overrun_alerts_specific_project(
        self, service, db_session, mock_project
    ):
        """检查指定项目"""
        db_session.query.return_value.filter.return_value.all.return_value = [
            mock_project
        ]

        alerts = service.check_cost_overrun_alerts(project_id=1)

        assert len(alerts) == 1
        assert alerts[0]["project_id"] == 1


class TestCompareProjectCosts(TestCostAnalysisService):
    """测试 compare_project_costs 方法"""

    def test_compare_project_costs(self, service, db_session, mock_project):
        """对比两个项目成本"""
        project2 = Mock(spec=Project)
        project2.id = 2
        project2.project_code = "PJ-TEST-002"
        project2.project_name = "测试项目2"
        project2.budget_amount = Decimal("1500000")
        project2.actual_cost = Decimal("1400000")
        project2.total_hours = Decimal("1200")
        project2.is_active = True

        db_session.query.return_value.filter.return_value.all.return_value = [
            mock_project,
            project2,
        ]

        with patch(
            "app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate"
        ) as mock_rate:
            mock_rate.return_value = Decimal("100")
            result = service.compare_project_costs([1, 2])

        assert len(result["projects"]) == 2
        assert result["summary"]["avg_total_cost"] == pytest.approx(110000, rel=1e-3)
        assert result["summary"]["min_cost"] == 80000
        assert result["summary"]["max_cost"] == 140000

    def test_compare_project_costs_no_projects(self, service, db_session):
        """没有项目"""
        db_session.query.return_value.filter.return_value.all.return_value = []

        result = service.compare_project_costs([1, 2])

        assert result["error"] == "项目不存在"


class TestAnalyzeCostTrend(TestCostAnalysisService):
    """测试 analyze_cost_trend 方法"""

    def test_analyze_cost_trend(
        self, service, db_session, mock_project, mock_timesheet
    ):
        """分析6个月成本趋势"""
        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_project
        )

        ts_list = []
        for i in range(6):
            ts = Mock(spec=Timesheet)
            ts.id = i + 1
            ts.project_id = mock_project.id
            ts.user_id = 1
            ts.work_date = date.today() - timedelta(days=(5 - i) * 30)
            ts.hours = 40
            ts.status = "APPROVED"
            ts_list.append(ts)

        db_session.query.return_value.filter.return_value.all.return_value = ts_list

        with patch(
            "app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate",
            return_value=Decimal("100"),
        ):
            result = service.analyze_cost_trend(1, months=6)

        assert result["project_id"] == 1
        assert len(result["monthly_trend"]) == 6
        assert result["total_cost"] > 0
        assert result["total_hours"] == 240

    def test_analyze_cost_trend_project_not_exists(self, service, db_session):
        """项目不存在"""
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = service.analyze_cost_trend(999, months=6)

        assert result["error"] == "项目不存在"

    def test_analyze_cost_trend_no_timesheet(self, service, db_session, mock_project):
        """没有工时数据"""
        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_project
        )
        db_session.query.return_value.filter.return_value.all.return_value = []

        result = service.analyze_cost_trend(1, months=6)

        assert result["total_hours"] == 0
        assert result["total_cost"] == 0


class TestCostAnalysisServiceEdgeCases:
    """测试边缘场景"""

    def test_predict_project_cost_zero_hours(self, service, db_session, mock_project):
        """零工时数据"""
        mock_project.total_hours = Decimal("0")

        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_project
        )
        db_session.query.return_value.filter.return_value.all.return_value = []
        db_session.query.return_value.filter.return_value.all.return_value = []

        with patch(
            "app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate",
            return_value=Decimal("100"),
        ):
            result = service.predict_project_cost(1, based_on_history=True)

        assert result["predicted_remaining_cost"] == 0
        assert result["predicted_total_cost"] == float(mock_project.actual_cost or 0)

    def test_check_cost_overrun_alerts_large_overrun(
        self, service, db_session, mock_project
    ):
        """巨大超支（500%）"""
        mock_project.budget_amount = Decimal("1000000")
        mock_project.actual_cost = Decimal("6000000")

        db_session.query.return_value.filter.return_value.all.return_value = [
            mock_project
        ]

        alerts = service.check_cost_overrun_alerts()

        assert len(alerts) == 1
        assert alerts[0]["alert_level"] == "CRITICAL"
        assert "500000" in alerts[0]["message"]

    def test_compare_project_costs_one_project(self, service, db_session, mock_project):
        """只有一个项目"""
        db_session.query.return_value.filter.return_value.all.return_value = [
            mock_project
        ]

        with patch(
            "app.services.cost_analysis_service.HourlyRateService.get_user_hourly_rate",
            return_value=Decimal("100"),
        ):
            result = service.compare_project_costs([1])

        assert len(result["projects"]) == 1
        assert result["summary"]["avg_total_cost"] == float(
            mock_project.actual_cost or 0
        )
        assert result["summary"]["min_cost"] == result["summary"]["max_cost"]
