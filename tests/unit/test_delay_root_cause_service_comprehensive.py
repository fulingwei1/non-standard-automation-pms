# -*- coding: utf-8 -*-
"""
DelayRootCauseService 综合单元测试

测试覆盖:
- analyze_root_cause: 延期根因分析
- analyze_impact: 延期影响分析
- analyze_trends: 延期趋势分析
- _calculate_delay_days: 计算延期天数
- _is_project_delayed: 判断项目是否延期
- _calculate_project_delay_days: 计算项目延期天数
- _calculate_trend_direction: 计算趋势方向
"""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest


class TestDelayRootCauseServiceInit:
    """测试服务初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()
        service = DelayRootCauseService(mock_db)

        assert service.db == mock_db


class TestAnalyzeRootCause:
    """测试 analyze_root_cause 方法"""

    def test_returns_empty_when_no_delayed_tasks(self):
        """测试无延期任务时返回空结果"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = DelayRootCauseService(mock_db)
        result = service.analyze_root_cause()

        assert result["total_delayed_tasks"] == 0
        assert result["root_causes"] == []

    def test_groups_by_delay_reason(self):
        """测试按延期原因分组"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()

        # Mock delayed tasks
        mock_task1 = MagicMock()
        mock_task1.delay_reason = "MATERIAL"
        mock_task1.is_delayed = True
        mock_task1.id = 1
        mock_task1.task_name = "任务1"
        mock_task1.project_id = 1
        mock_task1.plan_end_date = date.today() - timedelta(days=5)
        mock_task1.actual_end_date = date.today()

        mock_task2 = MagicMock()
        mock_task2.delay_reason = "MATERIAL"
        mock_task2.is_delayed = True
        mock_task2.id = 2
        mock_task2.task_name = "任务2"
        mock_task2.project_id = 1
        mock_task2.plan_end_date = date.today() - timedelta(days=3)
        mock_task2.actual_end_date = date.today()

        mock_task3 = MagicMock()
        mock_task3.delay_reason = "DESIGN"
        mock_task3.is_delayed = True
        mock_task3.id = 3
        mock_task3.task_name = "任务3"
        mock_task3.project_id = 2
        mock_task3.plan_end_date = date.today() - timedelta(days=10)
        mock_task3.actual_end_date = date.today()

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_task1,
            mock_task2,
            mock_task3,
        ]

        service = DelayRootCauseService(mock_db)
        result = service.analyze_root_cause()

        assert result["total_delayed_tasks"] == 3
        assert len(result["root_causes"]) == 2

        # 验证按延期天数排序（DESIGN 应该在前面）
        assert result["root_causes"][0]["reason"] == "DESIGN"
        assert result["root_causes"][0]["total_delay_days"] == 10

    def test_filters_by_project_id(self):
        """测试按项目ID筛选"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

        service = DelayRootCauseService(mock_db)
        result = service.analyze_root_cause(project_id=1)

        assert result["total_delayed_tasks"] == 0

    def test_filters_by_date_range(self):
        """测试按日期范围筛选"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.filter.return_value.filter.return_value.all.return_value = []

        service = DelayRootCauseService(mock_db)
        result = service.analyze_root_cause(
            start_date=date.today() - timedelta(days=30), end_date=date.today()
        )

        assert result["analysis_period"]["start_date"] is not None
        assert result["analysis_period"]["end_date"] is not None

    def test_handles_unknown_reason(self):
        """测试处理未知原因"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()

        mock_task = MagicMock()
        mock_task.delay_reason = None  # 无原因
        mock_task.is_delayed = True
        mock_task.id = 1
        mock_task.task_name = "任务"
        mock_task.project_id = 1
        mock_task.plan_end_date = date.today() - timedelta(days=5)
        mock_task.actual_end_date = date.today()

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_task]

        service = DelayRootCauseService(mock_db)
        result = service.analyze_root_cause()

        assert result["root_causes"][0]["reason"] == "UNKNOWN"


class TestAnalyzeImpact:
    """测试 analyze_impact 方法"""

    def test_returns_impact_analysis(self):
        """测试返回影响分析"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.status = "ST10"
        mock_project.contract_amount = Decimal("1000000")
        mock_project.plan_end_date = date.today() - timedelta(days=10)
        mock_project.actual_end_date = None

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]

        service = DelayRootCauseService(mock_db)
        result = service.analyze_impact()

        assert "cost_impact" in result
        assert "revenue_impact" in result
        assert "affected_projects" in result

    def test_calculates_cost_impact(self):
        """测试计算成本影响"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_code = "PJ001"
        mock_project.project_name = "测试项目"
        mock_project.status = "ST10"
        mock_project.contract_amount = Decimal("1000000")
        mock_project.plan_end_date = date.today() - timedelta(days=10)
        mock_project.actual_end_date = None

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]

        service = DelayRootCauseService(mock_db)
        result = service.analyze_impact()

        assert result["cost_impact"]["total"] > 0

    def test_returns_empty_when_no_delayed_projects(self):
        """测试无延期项目时返回空结果"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()

        mock_project = MagicMock()
        mock_project.status = "ST10"
        mock_project.plan_end_date = None  # 无计划结束日期
        mock_project.actual_end_date = None

        mock_db.query.return_value.filter.return_value.all.return_value = [mock_project]

        service = DelayRootCauseService(mock_db)
        result = service.analyze_impact()

        assert result["cost_impact"]["total"] == 0.0
        assert len(result["affected_projects"]) == 0


class TestAnalyzeTrends:
    """测试 analyze_trends 方法"""

    def test_returns_trend_analysis(self):
        """测试返回趋势分析"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        service = DelayRootCauseService(mock_db)
        result = service.analyze_trends(months=6)

        assert "period" in result
        assert "trends" in result
        assert "summary" in result
        assert result["period"]["months"] == 6

    def test_groups_by_month(self):
        """测试按月分组"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()

        mock_task1 = MagicMock()
        mock_task1.plan_start_date = date.today() - timedelta(days=30)
        mock_task1.is_delayed = True
        mock_task1.plan_end_date = date.today() - timedelta(days=35)
        mock_task1.actual_end_date = date.today() - timedelta(days=30)

        mock_task2 = MagicMock()
        mock_task2.plan_start_date = date.today() - timedelta(days=30)
        mock_task2.is_delayed = False
        mock_task2.plan_end_date = None
        mock_task2.actual_end_date = None

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_task1,
            mock_task2,
        ]

        service = DelayRootCauseService(mock_db)
        result = service.analyze_trends(months=3)

        assert len(result["trends"]) > 0

    def test_calculates_delay_rate(self):
        """测试计算延期率"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()

        month_key = date.today().strftime("%Y-%m")

        mock_task1 = MagicMock()
        mock_task1.plan_start_date = date.today()
        mock_task1.is_delayed = True
        mock_task1.plan_end_date = date.today() - timedelta(days=5)
        mock_task1.actual_end_date = date.today()

        mock_task2 = MagicMock()
        mock_task2.plan_start_date = date.today()
        mock_task2.is_delayed = False
        mock_task2.plan_end_date = None
        mock_task2.actual_end_date = None

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_task1,
            mock_task2,
        ]

        service = DelayRootCauseService(mock_db)
        result = service.analyze_trends(months=1)

        # 应该有当月的统计，1/2=50%延期率
        current_month_data = next(
            (t for t in result["trends"] if t["month"] == month_key), None
        )
        if current_month_data:
            assert current_month_data["delay_rate"] == 50.0


class TestCalculateDelayDays:
    """测试 _calculate_delay_days 方法"""

    def test_returns_zero_when_not_delayed(self):
        """测试未延期时返回0"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()
        service = DelayRootCauseService(mock_db)

        mock_task = MagicMock()
        mock_task.is_delayed = False

        result = service._calculate_delay_days(mock_task)

        assert result == 0

    def test_calculates_from_actual_end_date(self):
        """测试从实际结束日期计算"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()
        service = DelayRootCauseService(mock_db)

        mock_task = MagicMock()
        mock_task.is_delayed = True
        mock_task.plan_end_date = date.today() - timedelta(days=10)
        mock_task.actual_end_date = date.today()

        result = service._calculate_delay_days(mock_task)

        assert result == 10

    def test_calculates_from_today_when_not_completed(self):
        """测试未完成时从今天计算"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()
        service = DelayRootCauseService(mock_db)

        mock_task = MagicMock()
        mock_task.is_delayed = True
        mock_task.plan_end_date = date.today() - timedelta(days=5)
        mock_task.actual_end_date = None

        result = service._calculate_delay_days(mock_task)

        assert result == 5

    def test_returns_zero_when_no_plan_end_date(self):
        """测试无计划结束日期时返回0"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()
        service = DelayRootCauseService(mock_db)

        mock_task = MagicMock()
        mock_task.is_delayed = True
        mock_task.plan_end_date = None
        mock_task.actual_end_date = None

        result = service._calculate_delay_days(mock_task)

        assert result == 0


class TestIsProjectDelayed:
    """测试 _is_project_delayed 方法"""

    def test_returns_false_when_no_plan_end_date(self):
        """测试无计划结束日期时返回 False"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()
        service = DelayRootCauseService(mock_db)

        mock_project = MagicMock()
        mock_project.plan_end_date = None

        result = service._is_project_delayed(mock_project)

        assert result is False

    def test_returns_true_when_actual_after_plan(self):
        """测试实际结束日期晚于计划时返回 True"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()
        service = DelayRootCauseService(mock_db)

        mock_project = MagicMock()
        mock_project.plan_end_date = date.today() - timedelta(days=10)
        mock_project.actual_end_date = date.today()

        result = service._is_project_delayed(mock_project)

        assert result is True

    def test_returns_true_when_plan_passed_not_completed(self):
        """测试计划已过但未完成时返回 True"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()
        service = DelayRootCauseService(mock_db)

        mock_project = MagicMock()
        mock_project.plan_end_date = date.today() - timedelta(days=10)
        mock_project.actual_end_date = None

        result = service._is_project_delayed(mock_project)

        assert result is True

    def test_returns_false_when_completed_on_time(self):
        """测试按时完成时返回 False"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()
        service = DelayRootCauseService(mock_db)

        mock_project = MagicMock()
        mock_project.plan_end_date = date.today()
        mock_project.actual_end_date = date.today() - timedelta(days=1)

        result = service._is_project_delayed(mock_project)

        assert result is False


class TestCalculateTrendDirection:
    """测试 _calculate_trend_direction 方法"""

    def test_returns_stable_when_single_data_point(self):
        """测试单个数据点时返回 STABLE"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()
        service = DelayRootCauseService(mock_db)

        result = service._calculate_trend_direction([{"delay_rate": 50.0}])

        assert result == "STABLE"

    def test_returns_increasing_when_rate_increased(self):
        """测试延期率增加时返回 INCREASING"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()
        service = DelayRootCauseService(mock_db)

        trend_data = [{"delay_rate": 30.0}, {"delay_rate": 50.0}]

        result = service._calculate_trend_direction(trend_data)

        assert result == "INCREASING"

    def test_returns_decreasing_when_rate_decreased(self):
        """测试延期率下降时返回 DECREASING"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()
        service = DelayRootCauseService(mock_db)

        trend_data = [{"delay_rate": 50.0}, {"delay_rate": 30.0}]

        result = service._calculate_trend_direction(trend_data)

        assert result == "DECREASING"

    def test_returns_stable_when_rate_similar(self):
        """测试延期率相近时返回 STABLE"""
        from app.services.delay_root_cause_service import DelayRootCauseService

        mock_db = MagicMock()
        service = DelayRootCauseService(mock_db)

        trend_data = [{"delay_rate": 50.0}, {"delay_rate": 52.0}]

        result = service._calculate_trend_direction(trend_data)

        assert result == "STABLE"
