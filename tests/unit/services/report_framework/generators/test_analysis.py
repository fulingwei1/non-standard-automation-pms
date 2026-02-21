# -*- coding: utf-8 -*-
"""
分析报表生成器测试

测试覆盖：
- 负荷分析报告生成
- 成本分析报告生成
- 人员负荷计算和评级
- 项目成本统计
- 负荷阈值判断
- 数据聚合和分组
"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.services.report_framework.generators.analysis import AnalysisReportGenerator
from app.models.organization import Department
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User


class TestAnalysisReportGenerator:
    """分析报表生成器测试类"""

    def test_generate_workload_analysis_success(self, mock_db_session):
        """测试生成负荷分析报告成功"""
        mock_dept = MagicMock()
        mock_dept.id = 1
        mock_dept.dept_name = "研发部"
        
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"
        mock_user.department = "研发部"
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_dept
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_user],  # users
            [],           # timesheets
        ]
        
        result = AnalysisReportGenerator.generate_workload_analysis(
            mock_db_session, department_id=1
        )
        
        assert "summary" in result
        assert "load_distribution" in result
        assert "workload_details" in result
        assert "charts" in result
        assert result["summary"]["total_users"] == 1

    def test_generate_workload_analysis_all_company(self, mock_db_session):
        """测试全公司负荷分析"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "全公司用户"
        mock_user.is_active = True
        
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_user],  # all active users
            [],           # timesheets
        ]
        
        result = AnalysisReportGenerator.generate_workload_analysis(
            mock_db_session, department_id=None
        )
        
        assert result["summary"]["scope"] == "全公司"

    def test_generate_workload_analysis_default_dates(self, mock_db_session):
        """测试使用默认日期范围"""
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            [],  # users
            [],  # timesheets
        ]
        
        result = AnalysisReportGenerator.generate_workload_analysis(mock_db_session)
        
        assert "period_start" in result["summary"]
        assert "period_end" in result["summary"]

    def test_generate_cost_analysis_success(self, mock_db_session):
        """测试生成成本分析报告成功"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = 100000
        
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_project],  # projects
            [],              # timesheets
        ]
        
        result = AnalysisReportGenerator.generate_cost_analysis(
            mock_db_session, project_id=1
        )
        
        assert "summary" in result
        assert "project_breakdown" in result
        assert "charts" in result

    def test_generate_cost_analysis_multiple_projects(self, mock_db_session):
        """测试多个项目的成本分析"""
        mock_p1 = MagicMock()
        mock_p1.id = 1
        mock_p1.project_name = "项目1"
        mock_p1.budget_amount = 50000
        
        mock_p2 = MagicMock()
        mock_p2.id = 2
        mock_p2.project_name = "项目2"
        mock_p2.budget_amount = 80000
        
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_p1, mock_p2],  # projects
            [],                   # timesheets for p1
            [],                   # timesheets for p2
        ]
        
        result = AnalysisReportGenerator.generate_cost_analysis(
            mock_db_session, project_id=None
        )
        
        assert result["summary"]["project_count"] == 2
        assert result["summary"]["total_budget"] == 130000

    def test_get_user_scope_by_department(self, mock_db_session):
        """测试按部门获取用户范围"""
        mock_dept = MagicMock()
        mock_dept.id = 5
        mock_dept.dept_name = "销售部"
        
        mock_user = MagicMock()
        mock_user.id = 10
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_dept
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_user]
        
        users, scope_name = AnalysisReportGenerator._get_user_scope(mock_db_session, 5)
        
        assert len(users) == 1
        assert scope_name == "销售部"

    def test_get_user_scope_all_company(self, mock_db_session):
        """测试获取全公司用户"""
        mock_user1 = MagicMock()
        mock_user2 = MagicMock()
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_user1, mock_user2
        ]
        
        users, scope_name = AnalysisReportGenerator._get_user_scope(mock_db_session, None)
        
        assert len(users) == 2
        assert scope_name == "全公司"

    def test_get_user_scope_department_not_found(self, mock_db_session):
        """测试部门不存在的情况"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        users, scope_name = AnalysisReportGenerator._get_user_scope(mock_db_session, 999)
        
        assert users == []
        assert scope_name == "部门"

    def test_calculate_workload_empty(self):
        """测试无工时数据的负荷计算"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "用户"
        mock_user.username = "user"
        mock_user.department = "部门"
        
        workload_list, load_summary = AnalysisReportGenerator._calculate_workload(
            MagicMock(), [mock_user], []
        )
        
        assert len(workload_list) == 1
        assert workload_list[0]["total_hours"] == 0
        assert workload_list[0]["working_days"] == 0
        assert workload_list[0]["load_level"] == "LOW"
        assert load_summary["LOW"] == 1

    def test_calculate_workload_low_load(self):
        """测试低负荷情况"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "低负荷用户"
        mock_user.username = "user"
        mock_user.department = "部门"
        
        mock_ts = MagicMock()
        mock_ts.user_id = 1
        mock_ts.hours = 80.0  # 10天工作量
        mock_ts.project_id = 1
        
        workload_list, load_summary = AnalysisReportGenerator._calculate_workload(
            MagicMock(), [mock_user], [mock_ts]
        )
        
        assert workload_list[0]["load_level"] == "LOW"
        assert load_summary["LOW"] == 1

    def test_calculate_workload_medium_load(self):
        """测试中等负荷情况"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "中负荷用户"
        mock_user.username = "user"
        mock_user.department = "部门"
        
        mock_ts = MagicMock()
        mock_ts.user_id = 1
        mock_ts.hours = 120.0  # 15天工作量
        mock_ts.project_id = 1
        
        workload_list, load_summary = AnalysisReportGenerator._calculate_workload(
            MagicMock(), [mock_user], [mock_ts]
        )
        
        assert workload_list[0]["load_level"] == "MEDIUM"
        assert load_summary["MEDIUM"] == 1

    def test_calculate_workload_high_load(self):
        """测试高负荷情况"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "高负荷用户"
        mock_user.username = "user"
        mock_user.department = "部门"
        
        mock_ts = MagicMock()
        mock_ts.user_id = 1
        mock_ts.hours = 160.0  # 20天工作量
        mock_ts.project_id = 1
        
        workload_list, load_summary = AnalysisReportGenerator._calculate_workload(
            MagicMock(), [mock_user], [mock_ts]
        )
        
        assert workload_list[0]["load_level"] == "HIGH"
        assert load_summary["HIGH"] == 1

    def test_calculate_workload_overload(self):
        """测试超负荷情况"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "超负荷用户"
        mock_user.username = "user"
        mock_user.department = "部门"
        
        mock_ts = MagicMock()
        mock_ts.user_id = 1
        mock_ts.hours = 200.0  # 25天工作量
        mock_ts.project_id = 1
        
        workload_list, load_summary = AnalysisReportGenerator._calculate_workload(
            MagicMock(), [mock_user], [mock_ts]
        )
        
        assert workload_list[0]["load_level"] == "OVERLOAD"
        assert load_summary["OVERLOAD"] == 1

    def test_calculate_workload_multiple_users(self):
        """测试多用户负荷计算"""
        mock_user1 = MagicMock()
        mock_user1.id = 1
        mock_user1.real_name = "用户1"
        mock_user1.username = "user1"
        mock_user1.department = "部门"
        
        mock_user2 = MagicMock()
        mock_user2.id = 2
        mock_user2.real_name = "用户2"
        mock_user2.username = "user2"
        mock_user2.department = "部门"
        
        mock_ts1 = MagicMock()
        mock_ts1.user_id = 1
        mock_ts1.hours = 80.0
        mock_ts1.project_id = 1
        
        mock_ts2 = MagicMock()
        mock_ts2.user_id = 2
        mock_ts2.hours = 200.0
        mock_ts2.project_id = 2
        
        workload_list, load_summary = AnalysisReportGenerator._calculate_workload(
            MagicMock(), [mock_user1, mock_user2], [mock_ts1, mock_ts2]
        )
        
        assert len(workload_list) == 2
        assert load_summary["LOW"] == 1
        assert load_summary["OVERLOAD"] == 1

    def test_calculate_workload_multiple_projects(self):
        """测试多项目工时统计"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "用户"
        mock_user.username = "user"
        mock_user.department = "部门"
        
        mock_ts1 = MagicMock()
        mock_ts1.user_id = 1
        mock_ts1.hours = 40.0
        mock_ts1.project_id = 1
        
        mock_ts2 = MagicMock()
        mock_ts2.user_id = 1
        mock_ts2.hours = 40.0
        mock_ts2.project_id = 2
        
        mock_ts3 = MagicMock()
        mock_ts3.user_id = 1
        mock_ts3.hours = 40.0
        mock_ts3.project_id = 3
        
        workload_list, load_summary = AnalysisReportGenerator._calculate_workload(
            MagicMock(), [mock_user], [mock_ts1, mock_ts2, mock_ts3]
        )
        
        assert workload_list[0]["total_hours"] == 120.0
        assert workload_list[0]["project_count"] == 3

    def test_get_projects_single(self, mock_db_session):
        """测试获取单个项目"""
        mock_project = MagicMock()
        mock_project.id = 1
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_project]
        
        projects = AnalysisReportGenerator._get_projects(mock_db_session, project_id=1)
        
        assert len(projects) == 1

    def test_get_projects_active_only(self, mock_db_session):
        """测试仅获取活跃项目"""
        mock_p1 = MagicMock()
        mock_p1.is_active = True
        mock_p1.status = "IN_PROGRESS"
        
        mock_p2 = MagicMock()
        mock_p2.is_active = True
        mock_p2.status = "ON_HOLD"
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_p1, mock_p2
        ]
        
        projects = AnalysisReportGenerator._get_projects(mock_db_session, project_id=None)
        
        assert len(projects) == 2

    def test_calculate_project_costs_empty(self, mock_db_session):
        """测试无项目成本数据"""
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        summaries, total_budget, total_actual = AnalysisReportGenerator._calculate_project_costs(
            mock_db_session, [], date(2026, 2, 1), date(2026, 2, 28)
        )
        
        assert summaries == []
        assert total_budget == 0
        assert total_actual == 0

    def test_calculate_project_costs_with_budget_no_hours(self, mock_db_session):
        """测试有预算但无工时的项目"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = 100000
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        summaries, total_budget, total_actual = AnalysisReportGenerator._calculate_project_costs(
            mock_db_session, [mock_project], date(2026, 2, 1), date(2026, 2, 28)
        )
        
        assert len(summaries) == 1
        assert summaries[0]["budget"] == 100000
        assert summaries[0]["actual_cost"] == 0
        assert summaries[0]["variance"] == 100000
        assert total_budget == 100000
        assert total_actual == 0

    def test_calculate_project_costs_with_labor_hours(self, mock_db_session):
        """测试有工时的项目成本计算"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        mock_project.budget_amount = 50000
        
        mock_ts1 = MagicMock()
        mock_ts1.hours = 100.0
        
        mock_ts2 = MagicMock()
        mock_ts2.hours = 50.0
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_ts1, mock_ts2
        ]
        
        summaries, total_budget, total_actual = AnalysisReportGenerator._calculate_project_costs(
            mock_db_session, [mock_project], date(2026, 2, 1), date(2026, 2, 28)
        )
        
        expected_cost = 150.0 * 100  # 150小时 * 默认时薪100
        assert summaries[0]["actual_cost"] == expected_cost
        assert summaries[0]["labor_hours"] == 150.0
        assert summaries[0]["variance"] == 50000 - expected_cost
        assert summaries[0]["variance_percent"] == round((50000 - expected_cost) / 50000 * 100, 2)

    def test_calculate_project_costs_over_budget(self, mock_db_session):
        """测试超预算情况"""
        mock_project = MagicMock()
        mock_project.id = 1
        mock_project.project_name = "超预算项目"
        mock_project.budget_amount = 10000
        
        mock_ts = MagicMock()
        mock_ts.hours = 200.0  # 200小时 * 100 = 20000元
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_ts]
        
        summaries, total_budget, total_actual = AnalysisReportGenerator._calculate_project_costs(
            mock_db_session, [mock_project], date(2026, 2, 1), date(2026, 2, 28)
        )
        
        assert summaries[0]["variance"] < 0
        assert summaries[0]["variance_percent"] < 0

    def test_load_thresholds_constants(self):
        """测试负荷阈值常量"""
        assert AnalysisReportGenerator.LOAD_THRESHOLDS["OVERLOAD"] == 22
        assert AnalysisReportGenerator.LOAD_THRESHOLDS["HIGH"] == 18
        assert AnalysisReportGenerator.LOAD_THRESHOLDS["MEDIUM"] == 12

    def test_default_hourly_rate_constant(self):
        """测试默认时薪常量"""
        assert AnalysisReportGenerator.DEFAULT_HOURLY_RATE == 100
