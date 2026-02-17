# -*- coding: utf-8 -*-
"""
TimesheetAnalyticsService 单元测试

覆盖：
- analyze_trend (工时趋势分析)
- _calculate_trend (趋势计算)
- _generate_trend_chart (图表生成)
- analyze_workload (负荷热力图)
- analyze_efficiency (效率对比)
- analyze_overtime (加班统计)
- analyze_department_comparison (部门对比)
- analyze_project_distribution (项目分布)
"""

import pytest
from datetime import date, timedelta, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.services.timesheet_analytics_service import TimesheetAnalyticsService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return TimesheetAnalyticsService(db)


def _make_query_row(**kwargs):
    """构建一个通用查询结果行 mock"""
    row = MagicMock()
    for k, v in kwargs.items():
        setattr(row, k, v)
    return row


# ---------------------------------------------------------------------------
# Tests: _calculate_trend
# ---------------------------------------------------------------------------

class TestCalculateTrend:
    def test_less_than_two_results_returns_stable(self, service):
        trend, rate = service._calculate_trend([])
        assert trend == "STABLE"
        assert rate == 0.0

    def test_increasing_trend(self, service):
        results = [
            _make_query_row(total_hours=100),
            _make_query_row(total_hours=100),
            _make_query_row(total_hours=100),
            _make_query_row(total_hours=200),
            _make_query_row(total_hours=200),
            _make_query_row(total_hours=200),
        ]
        trend, rate = service._calculate_trend(results)
        assert trend == "INCREASING"
        assert rate > 5

    def test_decreasing_trend(self, service):
        results = [
            _make_query_row(total_hours=200),
            _make_query_row(total_hours=200),
            _make_query_row(total_hours=200),
            _make_query_row(total_hours=100),
            _make_query_row(total_hours=100),
            _make_query_row(total_hours=100),
        ]
        trend, rate = service._calculate_trend(results)
        assert trend == "DECREASING"
        assert rate < -5

    def test_stable_trend(self, service):
        results = [_make_query_row(total_hours=100) for _ in range(6)]
        trend, rate = service._calculate_trend(results)
        assert trend == "STABLE"
        assert abs(rate) <= 5


# ---------------------------------------------------------------------------
# Tests: _generate_trend_chart
# ---------------------------------------------------------------------------

class TestGenerateTrendChart:
    def test_daily_chart_format(self, service):
        results = [
            _make_query_row(work_date=date(2024, 1, i), total_hours=8*i, normal_hours=8*i, overtime_hours=0)
            for i in range(1, 4)
        ]
        chart = service._generate_trend_chart(results, "DAILY")
        assert len(chart.labels) == 3
        assert chart.labels[0] == "2024-01-01"
        assert len(chart.datasets) == 3

    def test_monthly_chart_format(self, service):
        results = [
            _make_query_row(work_date=date(2024, m, 1), total_hours=100, normal_hours=80, overtime_hours=20)
            for m in range(1, 4)
        ]
        chart = service._generate_trend_chart(results, "MONTHLY")
        assert chart.labels[0] == "2024-01"

    def test_empty_results_chart(self, service):
        chart = service._generate_trend_chart([], "DAILY")
        assert chart.labels == []
        assert len(chart.datasets) == 3


# ---------------------------------------------------------------------------
# Tests: analyze_trend
# ---------------------------------------------------------------------------

class TestAnalyzeTrend:
    def test_returns_trend_response_with_correct_fields(self, service, db):
        start = date(2024, 1, 1)
        end = date(2024, 3, 31)

        row = _make_query_row(
            work_date=date(2024, 1, 1),
            total_hours=160,
            normal_hours=128,
            overtime_hours=32,
        )
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = [row]

        result = service.analyze_trend("MONTHLY", start, end)
        assert result.period_type == "MONTHLY"
        assert float(result.total_hours) == 160.0
        assert result.trend in ("INCREASING", "DECREASING", "STABLE")

    def test_empty_data_returns_zeros(self, service, db):
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []
        start = date(2024, 1, 1)
        end = date(2024, 3, 31)
        result = service.analyze_trend("MONTHLY", start, end)
        assert float(result.total_hours) == 0
        assert float(result.average_hours) == 0

    def test_filter_by_user_ids(self, service, db):
        """传入 user_ids 时查询链中包含 filter"""
        db.query.return_value.filter.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []
        start = date(2024, 1, 1)
        end = date(2024, 3, 31)
        result = service.analyze_trend("DAILY", start, end, user_ids=[1, 2])
        assert result is not None  # 不抛异常即可


# ---------------------------------------------------------------------------
# Tests: analyze_efficiency
# ---------------------------------------------------------------------------

class TestAnalyzeEfficiency:
    def test_efficiency_rate_formula(self, service, db):
        """efficiency = planned/actual*100; planned=actual*0.9"""
        result_mock = _make_query_row(actual_hours=200)
        db.query.return_value.filter.return_value.first.return_value = result_mock

        start = date(2024, 1, 1)
        end = date(2024, 1, 31)
        result = service.analyze_efficiency("MONTHLY", start, end)

        actual = 200.0
        planned = actual * 0.9
        expected_efficiency = (planned / actual) * 100
        assert abs(float(result.efficiency_rate) - round(expected_efficiency, 2)) < 0.01

    def test_no_actual_hours_efficiency_100(self, service, db):
        """实际工时为0 → efficiency=100"""
        result_mock = _make_query_row(actual_hours=0)
        db.query.return_value.filter.return_value.first.return_value = result_mock

        result = service.analyze_efficiency("MONTHLY", date(2024, 1, 1), date(2024, 1, 31))
        assert float(result.efficiency_rate) == 100.0

    def test_variance_rate_is_positive(self, service, db):
        """actual > planned → variance_rate > 0"""
        result_mock = _make_query_row(actual_hours=100)
        db.query.return_value.filter.return_value.first.return_value = result_mock

        result = service.analyze_efficiency("MONTHLY", date(2024, 1, 1), date(2024, 1, 31))
        # variance = actual - planned = 100 - 90 = 10
        assert float(result.variance_hours) > 0


# ---------------------------------------------------------------------------
# Tests: analyze_overtime
# ---------------------------------------------------------------------------

class TestAnalyzeOvertime:
    def _make_overtime_result(self, total_overtime=20, weekend=10, holiday=5, total_hours=160):
        r = MagicMock()
        r.total_overtime = total_overtime
        r.weekend_hours = weekend
        r.holiday_hours = holiday
        r.total_hours = total_hours
        return r

    def test_overtime_rate_calculation(self, service, db):
        r = self._make_overtime_result(total_overtime=32, total_hours=160)
        db.query.return_value.filter.return_value.first.return_value = r
        db.query.return_value.filter.return_value.scalar.return_value = 4  # 4 users
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []

        result = service.analyze_overtime("MONTHLY", date(2024, 1, 1), date(2024, 1, 31))
        # rate = 32/160*100 = 20%
        assert abs(float(result.overtime_rate) - 20.0) < 0.01

    def test_avg_overtime_per_person(self, service, db):
        r = self._make_overtime_result(total_overtime=40, total_hours=160)
        db.query.return_value.filter.return_value.first.return_value = r
        db.query.return_value.filter.return_value.scalar.return_value = 5  # 5 users
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = []
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []

        result = service.analyze_overtime("MONTHLY", date(2024, 1, 1), date(2024, 1, 31))
        # avg = 40/5 = 8
        assert abs(float(result.avg_overtime_per_person) - 8.0) < 0.01

    def test_top_overtime_users_included(self, service, db):
        r = self._make_overtime_result()
        db.query.return_value.filter.return_value.first.return_value = r
        db.query.return_value.filter.return_value.scalar.return_value = 2

        user_row = _make_query_row(user_id=1, user_name="张三", department_name="研发部", overtime_hours=20)
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = [user_row]
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []

        result = service.analyze_overtime("MONTHLY", date(2024, 1, 1), date(2024, 1, 31))
        assert len(result.top_overtime_users) == 1
        assert result.top_overtime_users[0]["user_name"] == "张三"


# ---------------------------------------------------------------------------
# Tests: analyze_department_comparison
# ---------------------------------------------------------------------------

class TestAnalyzeDepartmentComparison:
    def _make_dept_row(self, dept_id, dept_name, total, normal, overtime, user_count, entry_count):
        r = MagicMock()
        r.department_id = dept_id
        r.department_name = dept_name
        r.total_hours = total
        r.normal_hours = normal
        r.overtime_hours = overtime
        r.user_count = user_count
        r.entry_count = entry_count
        return r

    def test_departments_sorted_by_total_hours(self, service, db):
        rows = [
            self._make_dept_row(1, "研发部", 500, 400, 100, 5, 50),
            self._make_dept_row(2, "测试部", 300, 250, 50,  3, 30),
        ]
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = rows

        result = service.analyze_department_comparison("MONTHLY", date(2024, 1, 1), date(2024, 1, 31))
        assert len(result.departments) == 2
        # 第一个部门 total_hours 应 >= 第二个
        assert result.departments[0]["total_hours"] >= result.departments[1]["total_hours"]

    def test_avg_hours_per_person(self, service, db):
        rows = [self._make_dept_row(1, "研发部", 400, 320, 80, 4, 40)]
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = rows

        result = service.analyze_department_comparison("MONTHLY", date(2024, 1, 1), date(2024, 1, 31))
        dept = result.departments[0]
        assert dept["avg_hours_per_person"] == 100.0  # 400/4

    def test_overtime_rate_in_department(self, service, db):
        rows = [self._make_dept_row(1, "研发部", 200, 160, 40, 2, 20)]
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = rows

        result = service.analyze_department_comparison("MONTHLY", date(2024, 1, 1), date(2024, 1, 31))
        dept = result.departments[0]
        assert dept["overtime_rate"] == 20.0  # 40/200*100

    def test_rankings_assigned(self, service, db):
        rows = [
            self._make_dept_row(1, "研发部", 500, 400, 100, 5, 50),
            self._make_dept_row(2, "测试部", 300, 250, 50, 3, 30),
        ]
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = rows

        result = service.analyze_department_comparison("MONTHLY", date(2024, 1, 1), date(2024, 1, 31))
        ranks = [d["rank"] for d in result.rankings]
        assert 1 in ranks
        assert 2 in ranks


# ---------------------------------------------------------------------------
# Tests: analyze_project_distribution
# ---------------------------------------------------------------------------

class TestAnalyzeProjectDistribution:
    def _make_proj_row(self, project_id, project_name, total_hours, user_count, entry_count):
        r = MagicMock()
        r.project_id = project_id
        r.project_name = project_name
        r.total_hours = total_hours
        r.user_count = user_count
        r.entry_count = entry_count
        return r

    def test_percentage_sums_to_100(self, service, db):
        rows = [
            self._make_proj_row(1, "项目A", 600, 3, 30),
            self._make_proj_row(2, "项目B", 300, 2, 20),
            self._make_proj_row(3, "项目C", 100, 1, 10),
        ]
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = rows

        result = service.analyze_project_distribution("MONTHLY", date(2024, 1, 1), date(2024, 1, 31))
        total_pct = sum(p["percentage"] for p in result.project_details)
        assert abs(total_pct - 100.0) < 0.1

    def test_concentration_index_range(self, service, db):
        rows = [self._make_proj_row(i, f"Proj{i}", 100, 1, 10) for i in range(5)]
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = rows

        result = service.analyze_project_distribution("MONTHLY", date(2024, 1, 1), date(2024, 1, 31))
        assert 0.0 <= float(result.concentration_index) <= 1.0

    def test_empty_results(self, service, db):
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []

        result = service.analyze_project_distribution("MONTHLY", date(2024, 1, 1), date(2024, 1, 31))
        assert float(result.total_hours) == 0
        assert result.total_projects == 0

    def test_pie_chart_labels_match_projects(self, service, db):
        rows = [
            self._make_proj_row(1, "项目A", 400, 2, 20),
            self._make_proj_row(2, "项目B", 200, 1, 10),
        ]
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = rows

        result = service.analyze_project_distribution("MONTHLY", date(2024, 1, 1), date(2024, 1, 31))
        assert "项目A" in result.pie_chart.labels
        assert "项目B" in result.pie_chart.labels


# ---------------------------------------------------------------------------
# Tests: analyze_workload
# ---------------------------------------------------------------------------

class TestAnalyzeWorkload:
    def test_empty_data_returns_no_overload(self, service, db):
        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = []

        start = date(2024, 1, 1)
        end = date(2024, 1, 7)
        result = service.analyze_workload("WEEKLY", start, end)

        assert result.statistics["total_users"] == 0
        assert result.statistics["overload_count"] == 0
        assert result.overload_users == []

    def test_overload_user_detected(self, service, db):
        """用户日均工时 > 8h → 超负荷"""
        start = date(2024, 1, 1)
        end = date(2024, 1, 5)  # 5天

        rows = []
        for d in range(1, 6):
            row = MagicMock()
            row.user_id = 1
            row.user_name = "张三"
            row.department_name = "研发部"
            row.work_date = date(2024, 1, d)
            row.daily_hours = 12  # 超时
            rows.append(row)

        db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.all.return_value = rows

        result = service.analyze_workload("WEEKLY", start, end)
        assert len(result.overload_users) >= 1
