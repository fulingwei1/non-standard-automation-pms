# -*- coding: utf-8 -*-
"""
部门报表生成器测试

测试覆盖：
- 部门周报生成
- 部门月报生成
- 人员工时统计
- 项目分布分析
- 人员负荷计算
- 项目统计逻辑
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.services.report_framework.generators.department import DeptReportGenerator
from app.models.organization import Department
from app.models.project import Project, ProjectMember
from app.models.timesheet import Timesheet
from app.models.user import User


class TestDeptReportGenerator:
    """部门报表生成器测试类"""

    def test_generate_weekly_success(self, mock_db_session):
        """测试生成部门周报成功"""
        start = date(2026, 2, 10)
        end = date(2026, 2, 16)
        
        mock_dept = MagicMock(spec=Department)
        mock_dept.id = 1
        mock_dept.dept_name = "研发部"
        mock_dept.dept_code = "DEV"
        
        mock_user = MagicMock(spec=User)
        mock_user.id = 1
        mock_user.real_name = "张三"
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_dept
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_user],  # department members
            [],           # timesheets
            [],           # project breakdown timesheets
            [],           # workload timesheets
        ]
        
        result = DeptReportGenerator.generate_weekly(mock_db_session, 1, start, end)
        
        assert "summary" in result
        assert result["summary"]["department_name"] == "研发部"
        assert result["summary"]["department_code"] == "DEV"
        assert "members" in result
        assert "timesheet" in result
        assert "workload" in result

    def test_generate_weekly_department_not_found(self, mock_db_session):
        """测试部门不存在时返回错误"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = DeptReportGenerator.generate_weekly(
            mock_db_session, 999, date.today(), date.today()
        )
        
        assert "error" in result
        assert result["error"] == "部门不存在"
        assert result["department_id"] == 999

    def test_generate_monthly_success(self, mock_db_session):
        """测试生成部门月报成功"""
        start = date(2026, 2, 1)
        end = date(2026, 2, 28)
        
        mock_dept = MagicMock()
        mock_dept.id = 2
        mock_dept.dept_name = "生产部"
        mock_dept.dept_code = "PROD"
        
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "李四"
        
        # 模拟多次查询调用
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_dept
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_user],  # department members (first call)
            [mock_user],  # department members (second call for stats)
            [],           # project memberships
            [],           # projects
            [],           # timesheets for summary
            [],           # timesheets for breakdown
            [],           # timesheets for workload
        ]
        
        result = DeptReportGenerator.generate_monthly(mock_db_session, 2, start, end)
        
        assert "summary" in result
        assert result["summary"]["report_type"] == "月报"
        assert "key_metrics" in result
        assert "project_stats" in result
        assert "member_workload" in result

    def test_get_department_members_by_id(self, mock_db_session):
        """测试通过department_id获取成员"""
        mock_dept = MagicMock()
        mock_dept.id = 1
        
        mock_user1 = MagicMock()
        mock_user1.id = 1
        mock_user1.real_name = "用户1"
        
        mock_user2 = MagicMock()
        mock_user2.id = 2
        mock_user2.real_name = "用户2"
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_user1, mock_user2
        ]
        
        members = DeptReportGenerator._get_department_members(mock_db_session, mock_dept)
        
        assert len(members) == 2
        assert members[0].id == 1

    def test_get_department_members_by_name_fallback(self, mock_db_session):
        """测试通过部门名称查询成员（ID查询失败时的后备）"""
        mock_dept = MagicMock()
        mock_dept.id = 1
        mock_dept.dept_name = "研发部"
        
        mock_user = MagicMock()
        mock_user.id = 10
        mock_user.department = "研发部"
        
        # 第一次查询返回空（按ID），第二次返回用户（按名称）
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            [],           # by department_id
            [mock_user],  # by department name
        ]
        
        members = DeptReportGenerator._get_department_members(mock_db_session, mock_dept)
        
        assert len(members) == 1
        assert members[0].id == 10

    def test_get_timesheet_summary_empty(self, mock_db_session):
        """测试无工时数据情况"""
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        result = DeptReportGenerator._get_timesheet_summary(
            mock_db_session, [1, 2, 3], date(2026, 2, 1), date(2026, 2, 28)
        )
        
        assert result["total_hours"] == 0
        assert result["timesheet_count"] == 0

    def test_get_timesheet_summary_with_data(self, mock_db_session):
        """测试有工时数据的情况"""
        mock_ts1 = MagicMock()
        mock_ts1.hours = 40.0
        
        mock_ts2 = MagicMock()
        mock_ts2.hours = 35.5
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_ts1, mock_ts2
        ]
        
        result = DeptReportGenerator._get_timesheet_summary(
            mock_db_session, [1, 2], date(2026, 2, 1), date(2026, 2, 28)
        )
        
        assert result["total_hours"] == 75.5
        assert result["timesheet_count"] == 2

    def test_get_timesheet_summary_no_users(self, mock_db_session):
        """测试用户列表为空的情况"""
        result = DeptReportGenerator._get_timesheet_summary(
            mock_db_session, [], date(2026, 2, 1), date(2026, 2, 28)
        )
        
        assert result["total_hours"] == 0
        assert result["timesheet_count"] == 0

    def test_get_project_breakdown_empty(self, mock_db_session):
        """测试无项目分布数据"""
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        result = DeptReportGenerator._get_project_breakdown(
            mock_db_session, [1], date(2026, 2, 1), date(2026, 2, 28)
        )
        
        assert result == []

    def test_get_project_breakdown_with_projects(self, mock_db_session):
        """测试有项目分布数据"""
        mock_ts1 = MagicMock()
        mock_ts1.project_id = 1
        mock_ts1.hours = 40.0
        
        mock_ts2 = MagicMock()
        mock_ts2.project_id = 1
        mock_ts2.hours = 20.0
        
        mock_ts3 = MagicMock()
        mock_ts3.project_id = 2
        mock_ts3.hours = 30.0
        
        mock_project = MagicMock()
        mock_project.project_name = "项目A"
        
        # 第一次返回工时数据，第二次返回项目信息
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_ts1, mock_ts2, mock_ts3
        ]
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_project
        
        result = DeptReportGenerator._get_project_breakdown(
            mock_db_session, [1], date(2026, 2, 1), date(2026, 2, 28)
        )
        
        assert len(result) == 2
        assert result[0]["hours"] == 60.0  # 项目1合计
        assert result[1]["hours"] == 30.0  # 项目2
        assert result[0]["percentage"] == 66.7  # 60/90 * 100

    def test_get_project_breakdown_non_project_work(self, mock_db_session):
        """测试非项目工作的工时"""
        mock_ts = MagicMock()
        mock_ts.project_id = None
        mock_ts.hours = 8.0
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [mock_ts]
        
        result = DeptReportGenerator._get_project_breakdown(
            mock_db_session, [1], date(2026, 2, 1), date(2026, 2, 28)
        )
        
        assert len(result) == 1
        assert result[0]["project_name"] == "非项目工作"

    def test_get_project_breakdown_with_limit(self, mock_db_session):
        """测试限制返回数量"""
        timesheets = []
        for i in range(15):
            mock_ts = MagicMock()
            mock_ts.project_id = i + 1
            mock_ts.hours = 10.0
            timesheets.append(mock_ts)
        
        mock_project = MagicMock()
        mock_project.project_name = "测试项目"
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = timesheets
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_project
        
        result = DeptReportGenerator._get_project_breakdown(
            mock_db_session, [1], date(2026, 2, 1), date(2026, 2, 28), limit=5
        )
        
        assert len(result) <= 5

    def test_get_member_workload(self, mock_db_session):
        """测试获取成员工作负荷"""
        mock_user1 = MagicMock()
        mock_user1.id = 1
        mock_user1.real_name = "张三"
        mock_user1.username = "zhangsan"
        mock_user1.position = "高级工程师"
        
        mock_user2 = MagicMock()
        mock_user2.id = 2
        mock_user2.real_name = "李四"
        mock_user2.username = "lisi"
        mock_user2.position = "工程师"
        
        mock_ts1 = MagicMock()
        mock_ts1.user_id = 1
        mock_ts1.hours = 40.0
        
        mock_ts2 = MagicMock()
        mock_ts2.user_id = 2
        mock_ts2.hours = 30.0
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_ts1, mock_ts2
        ]
        
        result = DeptReportGenerator._get_member_workload(
            mock_db_session, [mock_user1, mock_user2], date(2026, 2, 1), date(2026, 2, 7)
        )
        
        assert len(result) == 2
        assert result[0]["user_id"] == 1
        assert result[0]["total_hours"] == 40.0
        assert result[0]["avg_daily_hours"] == 8.0

    def test_get_member_workload_detailed(self, mock_db_session):
        """测试获取成员工作负荷详情"""
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.real_name = "王五"
        mock_user.username = "wangwu"
        mock_user.position = "项目经理"
        
        mock_ts1 = MagicMock()
        mock_ts1.user_id = 1
        mock_ts1.hours = 8.0
        mock_ts1.work_date = date(2026, 2, 1)
        
        mock_ts2 = MagicMock()
        mock_ts2.user_id = 1
        mock_ts2.hours = 8.0
        mock_ts2.work_date = date(2026, 2, 2)
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_ts1, mock_ts2
        ]
        
        working_days = 5
        
        result = DeptReportGenerator._get_member_workload_detailed(
            mock_db_session, [mock_user], date(2026, 2, 1), date(2026, 2, 5), working_days
        )
        
        assert len(result) == 1
        assert result[0]["total_hours"] == 16.0
        assert result[0]["expected_hours"] == 40
        assert result[0]["utilization_rate"] == 40.0
        assert result[0]["timesheet_days"] == 2

    def test_get_project_stats_empty(self, mock_db_session):
        """测试无项目统计数据"""
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            [],  # project memberships
            [],  # projects
        ]
        
        result = DeptReportGenerator._get_project_stats(
            mock_db_session, [1], date(2026, 2, 1), date(2026, 2, 28)
        )
        
        assert result["total"] == 0
        assert result["by_stage"] == {}
        assert result["by_health"] == {}

    def test_get_project_stats_with_projects(self, mock_db_session):
        """测试有项目统计数据"""
        mock_pm1 = MagicMock()
        mock_pm1.project_id = 1
        
        mock_pm2 = MagicMock()
        mock_pm2.project_id = 2
        
        mock_p1 = MagicMock()
        mock_p1.id = 1
        mock_p1.stage = "S2"
        mock_p1.health = "H1"
        mock_p1.is_active = True
        mock_p1.created_at = None
        mock_p1.updated_at = None
        
        mock_p2 = MagicMock()
        mock_p2.id = 2
        mock_p2.stage = "S3"
        mock_p2.health = "H2"
        mock_p2.is_active = True
        mock_p2.created_at = None
        mock_p2.updated_at = None
        
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_pm1, mock_pm2],  # project memberships
            [mock_p1, mock_p2],    # projects
        ]
        
        result = DeptReportGenerator._get_project_stats(
            mock_db_session, [1], date(2026, 2, 1), date(2026, 2, 28)
        )
        
        assert result["total"] == 2
        assert result["by_stage"]["S2"] == 1
        assert result["by_stage"]["S3"] == 1
        assert result["by_health"]["H1"] == 1
        assert result["by_health"]["H2"] == 1
