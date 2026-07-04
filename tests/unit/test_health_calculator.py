# -*- coding: utf-8 -*-
"""
项目健康度计算器单元测试
覆盖 H1/H2/H3/H4 全路径及各风险检测子方法
"""
from datetime import date, timedelta
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from app.models.enums import ProjectHealthEnum
from app.services.health_calculator import HealthCalculator


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def calculator(mock_db):
    return HealthCalculator(db=mock_db)


def make_project(**kwargs):
    """辅助：创建轻量项目 mock"""
    p = MagicMock()
    p.id = 1
    p.status = "ST10"
    p.planned_end_date = None
    p.progress_pct = 50.0
    p.pm_id = 1
    p.customer_id = 1
    p.customer_name = "TestCo"
    p.pm_name = "PM1"
    p.planned_start_date = None
    for k, v in kwargs.items():
        setattr(p, k, v)
    return p


class TestIsClosed:
    def test_st30_is_closed(self, calculator):
        p = make_project(status="ST30")
        assert calculator._is_closed(p) is True

    def test_st99_is_closed(self, calculator):
        p = make_project(status="ST99")
        assert calculator._is_closed(p) is True

    def test_st10_not_closed(self, calculator):
        p = make_project(status="ST10")
        assert calculator._is_closed(p) is False


class TestIsBlocked:
    def test_st14_is_blocked(self, calculator):
        p = make_project(status="ST14")
        assert calculator._is_blocked(p) is True

    def test_st19_is_blocked(self, calculator):
        p = make_project(status="ST19")
        assert calculator._is_blocked(p) is True

    def test_no_blocked_tasks_or_issues(self, mock_db, calculator):
        p = make_project(status="ST10")
        # db 返回 0 条阻塞记录
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        assert calculator._is_blocked(p) is False


class TestHasRisks:
    def test_st22_has_risk(self, calculator):
        p = make_project(status="ST22")
        assert calculator._has_risks(p) is True

    def test_st26_has_risk(self, calculator):
        p = make_project(status="ST26")
        assert calculator._has_risks(p) is True

    def test_deadline_approaching_triggers_risk(self, calculator):
        p = make_project(status="ST10", planned_end_date=date.today() + timedelta(days=3))
        # _is_deadline_approaching checks without db queries
        # Mock all db sub-checks to return 0
        calculator.db.query.return_value.filter.return_value.count.return_value = 0
        calculator.db.query.return_value.join.return_value.filter.return_value.count.return_value = (
            0
        )
        result = calculator._is_deadline_approaching(p, days=7)
        assert result is True

    def test_far_deadline_no_risk(self, calculator):
        p = make_project(planned_end_date=date.today() + timedelta(days=30))
        result = calculator._is_deadline_approaching(p, days=7)
        assert result is False

    def test_no_planned_end_date_no_risk(self, calculator):
        p = make_project(planned_end_date=None)
        result = calculator._is_deadline_approaching(p, days=7)
        assert result is False


class TestCalculateHealth:
    def test_closed_project_returns_h4(self, calculator):
        p = make_project(status="ST30")
        assert calculator.calculate_health(p) == ProjectHealthEnum.H4.value

    def test_blocked_project_returns_h3(self, mock_db, calculator):
        p = make_project(status="ST14")
        result = calculator.calculate_health(p)
        assert result == ProjectHealthEnum.H3.value

    def test_normal_project_returns_h1(self, mock_db, calculator):
        p = make_project(status="ST10", planned_end_date=date.today() + timedelta(days=30))
        # All db risk checks return 0
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = calculator.calculate_health(p)
        assert result == ProjectHealthEnum.H1.value

    def test_rectification_returns_h2(self, mock_db, calculator):
        p = make_project(status="ST22")
        # 确保阻塞判断中的db查询返回0
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        result = calculator.calculate_health(p)
        assert result == ProjectHealthEnum.H2.value

    def test_h4_takes_priority_over_blocked_status(self, calculator):
        """已完结状态优先级高于阻塞判断"""
        p = make_project(status="ST30")
        assert calculator.calculate_health(p) == ProjectHealthEnum.H4.value

    def test_over_budget_project_returns_h2(self, mock_db, calculator):
        """实际成本超过预算时，主健康度不能继续判 H1。"""
        p = make_project(
            status="ST10",
            planned_start_date=date.today(),
            planned_end_date=date.today() + timedelta(days=30),
            progress_pct=50,
            budget_amount=100,
            actual_cost=125,
        )
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 0

        result = calculator.calculate_health(p)

        assert result == ProjectHealthEnum.H2.value

    def test_project_with_no_health_baseline_is_not_h1(self, mock_db, calculator):
        """完全缺少计划、进度和成本基线时，不能默认绿灯。"""
        p = make_project(
            status="ST10",
            planned_start_date=None,
            planned_end_date=None,
            progress_pct=0,
            budget_amount=0,
            actual_cost=0,
        )
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 0

        result = calculator.calculate_health(p)

        assert result == ProjectHealthEnum.H2.value


class TestHealthSnapshotData:
    def test_snapshot_data_uses_dimension_scores_and_cost_metrics(self, mock_db, calculator):
        p = make_project(
            status="ST10",
            planned_start_date=date.today() - timedelta(days=10),
            planned_end_date=date.today() + timedelta(days=10),
            progress_pct=25,
            budget_amount=100,
            actual_cost=125,
        )
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.join.return_value.filter.return_value.count.return_value = 0

        with patch("app.services.health_calculator.HealthTrendService") as trend_cls:
            trend_cls.return_value.calculate_dimension_scores.return_value = {
                "schedule": 90,
                "cost": 45,
                "resource": 85,
                "quality": 75,
            }

            snapshot_data = calculator.build_health_snapshot_data(p)

        assert snapshot_data["overall_health"] == ProjectHealthEnum.H2.value
        assert snapshot_data["schedule_health"] == ProjectHealthEnum.H1.value
        assert snapshot_data["cost_health"] == ProjectHealthEnum.H3.value
        assert snapshot_data["resource_health"] == ProjectHealthEnum.H1.value
        assert snapshot_data["quality_health"] == ProjectHealthEnum.H2.value
        assert snapshot_data["budget_used_pct"] == 125.0
        assert snapshot_data["cost_variance"] == 25.0
        assert snapshot_data["schedule_variance"] == 25.0


class TestScheduleVarianceCheck:
    def test_below_threshold_returns_false(self, mock_db, calculator):
        p = make_project()
        p.progress_pct = 55.0
        # 构造 milestone 数据
        mock_db.query.return_value.filter.return_value.all.return_value = []
        result = calculator._has_schedule_variance(p, threshold=10.0)
        assert result is False

    def test_no_progress_pct_returns_false(self, calculator):
        p = make_project()
        p.progress_pct = None
        result = calculator._has_schedule_variance(p, threshold=10.0)
        assert result is False
