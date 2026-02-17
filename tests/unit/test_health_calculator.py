# -*- coding: utf-8 -*-
"""
项目健康度计算器单元测试
覆盖 H1/H2/H3/H4 全路径及各风险检测子方法
"""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, PropertyMock, patch

from app.services.health_calculator import HealthCalculator
from app.models.enums import ProjectHealthEnum


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
        calculator.db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
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
