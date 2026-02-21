# -*- coding: utf-8 -*-
"""
项目报表生成器测试

测试覆盖：
- 周报数据生成
- 月报数据生成
- 里程碑数据统计
- 工时数据汇总
- 机台数据查询
- 风险评估逻辑
"""

import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.services.report_framework.generators.project import ProjectReportGenerator
from app.models.project import Machine, Project, ProjectMilestone
from app.models.timesheet import Timesheet


class TestProjectReportGenerator:
    """项目报表生成器测试类"""

    def test_generate_weekly_success(self, mock_db_session):
        """测试生成周报成功"""
        # 准备测试数据
        start = date(2026, 2, 10)
        end = date(2026, 2, 16)
        
        mock_project = MagicMock(spec=Project)
        mock_project.id = 1
        mock_project.project_name = "测试项目"
        mock_project.project_code = "PJ-001"
        mock_project.progress = 45.5
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        result = ProjectReportGenerator.generate_weekly(mock_db_session, 1, start, end)
        
        assert "summary" in result
        assert "milestones" in result
        assert "timesheet" in result
        assert "machines" in result
        assert "risks" in result
        assert result["summary"]["project_name"] == "测试项目"
        assert result["summary"]["project_id"] == 1

    def test_generate_weekly_project_not_found(self, mock_db_session):
        """测试项目不存在时返回错误"""
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        result = ProjectReportGenerator.generate_weekly(
            mock_db_session, 999, date.today(), date.today()
        )
        
        assert "error" in result
        assert result["error"] == "项目不存在"
        assert result["project_id"] == 999

    def test_generate_monthly_success(self, mock_db_session):
        """测试生成月报成功"""
        start = date(2026, 2, 1)
        end = date(2026, 2, 28)
        
        mock_project = MagicMock(spec=Project)
        mock_project.id = 2
        mock_project.project_name = "月报测试项目"
        mock_project.budget_amount = 100000
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_project
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        result = ProjectReportGenerator.generate_monthly(mock_db_session, 2, start, end)
        
        assert "summary" in result
        assert result["summary"]["report_type"] == "月报"
        assert "milestones" in result
        assert "progress_trend" in result
        assert "cost" in result
        assert result["cost"]["planned_cost"] == 100000

    def test_build_project_summary(self):
        """测试构建项目基础信息"""
        mock_project = MagicMock()
        mock_project.id = 5
        mock_project.project_name = "测试项目"
        mock_project.project_code = "PJ-005"
        mock_project.customer_name = "测试客户"
        mock_project.current_stage = "S2"
        mock_project.health_status = "H2"
        mock_project.progress = 66.6
        
        start = date(2026, 2, 1)
        end = date(2026, 2, 28)
        
        summary = ProjectReportGenerator._build_project_summary(mock_project, start, end)
        
        assert summary["project_id"] == 5
        assert summary["project_name"] == "测试项目"
        assert summary["project_code"] == "PJ-005"
        assert summary["customer_name"] == "测试客户"
        assert summary["current_stage"] == "S2"
        assert summary["health_status"] == "H2"
        assert summary["progress"] == 66.6
        assert summary["period_start"] == "2026-02-01"
        assert summary["period_end"] == "2026-02-28"

    def test_get_milestone_data_empty(self, mock_db_session):
        """测试无里程碑数据情况"""
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        result = ProjectReportGenerator._get_milestone_data(
            mock_db_session, 1, date(2026, 2, 1), date(2026, 2, 28)
        )
        
        assert result["summary"]["total"] == 0
        assert result["summary"]["completed"] == 0
        assert result["summary"]["delayed"] == 0
        assert result["summary"]["in_progress"] == 0
        assert result["details"] == []

    def test_get_milestone_data_with_milestones(self, mock_db_session):
        """测试有里程碑数据的情况"""
        mock_m1 = MagicMock()
        mock_m1.id = 1
        mock_m1.milestone_name = "需求评审"
        mock_m1.milestone_date = date(2026, 2, 10)
        mock_m1.actual_date = date(2026, 2, 11)
        mock_m1.status = "COMPLETED"
        
        mock_m2 = MagicMock()
        mock_m2.id = 2
        mock_m2.milestone_name = "设计完成"
        mock_m2.milestone_date = date(2026, 2, 20)
        mock_m2.actual_date = None
        mock_m2.status = "IN_PROGRESS"
        
        mock_m3 = MagicMock()
        mock_m3.id = 3
        mock_m3.milestone_name = "测试完成"
        mock_m3.milestone_date = date(2026, 2, 25)
        mock_m3.actual_date = None
        mock_m3.status = "DELAYED"
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_m1, mock_m2, mock_m3
        ]
        
        result = ProjectReportGenerator._get_milestone_data(
            mock_db_session, 1, date(2026, 2, 1), date(2026, 2, 28)
        )
        
        assert result["summary"]["total"] == 3
        assert result["summary"]["completed"] == 1
        assert result["summary"]["delayed"] == 1
        assert result["summary"]["in_progress"] == 1
        assert len(result["details"]) == 3
        assert result["details"][0]["name"] == "需求评审"

    def test_get_timesheet_data_empty(self, mock_db_session):
        """测试无工时数据情况"""
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        result = ProjectReportGenerator._get_timesheet_data(
            mock_db_session, 1, date(2026, 2, 1), date(2026, 2, 28)
        )
        
        assert result["total_hours"] == 0
        assert result["unique_workers"] == 0
        assert result["avg_hours_per_worker"] == 0
        assert result["timesheet_count"] == 0

    def test_get_timesheet_data_with_data(self, mock_db_session):
        """测试有工时数据的情况"""
        mock_ts1 = MagicMock()
        mock_ts1.user_id = 1
        mock_ts1.hours = 8.0
        
        mock_ts2 = MagicMock()
        mock_ts2.user_id = 2
        mock_ts2.hours = 6.5
        
        mock_ts3 = MagicMock()
        mock_ts3.user_id = 1
        mock_ts3.hours = 7.5
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_ts1, mock_ts2, mock_ts3
        ]
        
        result = ProjectReportGenerator._get_timesheet_data(
            mock_db_session, 1, date(2026, 2, 1), date(2026, 2, 28)
        )
        
        assert result["total_hours"] == 22.0
        assert result["unique_workers"] == 2
        assert result["avg_hours_per_worker"] == 11.0
        assert result["timesheet_count"] == 3

    def test_get_machine_data_empty(self, mock_db_session):
        """测试无机台数据情况"""
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        result = ProjectReportGenerator._get_machine_data(mock_db_session, 1)
        
        assert result == []

    def test_get_machine_data_with_machines(self, mock_db_session):
        """测试有机台数据的情况"""
        mock_m1 = MagicMock()
        mock_m1.id = 1
        mock_m1.machine_code = "M-001"
        mock_m1.machine_name = "测试机台1"
        mock_m1.status = "PRODUCTION"
        mock_m1.progress = 75.0
        
        mock_m2 = MagicMock()
        mock_m2.id = 2
        mock_m2.machine_code = "M-002"
        mock_m2.machine_name = "测试机台2"
        mock_m2.status = "TESTING"
        mock_m2.progress = 50.0
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            mock_m1, mock_m2
        ]
        
        result = ProjectReportGenerator._get_machine_data(mock_db_session, 1)
        
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[0]["machine_code"] == "M-001"
        assert result[0]["progress"] == 75.0
        assert result[1]["status"] == "TESTING"

    def test_get_weekly_trend(self, mock_db_session):
        """测试获取周度趋势数据"""
        mock_ts1 = MagicMock()
        mock_ts1.hours = 40.0
        
        mock_ts2 = MagicMock()
        mock_ts2.hours = 35.0
        
        mock_db_session.query.return_value.filter.return_value.all.side_effect = [
            [mock_ts1],  # 第一周
            [mock_ts2],  # 第二周
            [],          # 第三周
            [],          # 第四周
        ]
        
        start = date(2026, 2, 1)
        end = date(2026, 2, 28)
        
        result = ProjectReportGenerator._get_weekly_trend(
            mock_db_session, 1, start, end
        )
        
        assert len(result) == 4
        assert result[0]["week"] == 1
        assert result[0]["hours"] == 40.0
        assert result[1]["hours"] == 35.0
        assert result[2]["hours"] == 0

    def test_get_cost_summary_with_budget(self):
        """测试获取成本概况（有预算）"""
        mock_project = MagicMock()
        mock_project.budget_amount = 200000
        
        result = ProjectReportGenerator._get_cost_summary(mock_project)
        
        assert result["planned_cost"] == 200000
        assert result["actual_cost"] == 0
        assert result["cost_variance"] == 0

    def test_get_cost_summary_no_budget(self):
        """测试获取成本概况（无预算）"""
        mock_project = MagicMock(spec=Project)
        del mock_project.budget_amount
        
        result = ProjectReportGenerator._get_cost_summary(mock_project)
        
        assert result["planned_cost"] == 0

    def test_assess_risks_healthy_project(self):
        """测试健康项目的风险评估"""
        summary = {"health_status": "H1"}
        milestones = {"summary": {"delayed": 0}}
        
        risks = ProjectReportGenerator._assess_risks(summary, milestones)
        
        assert len(risks) == 0

    def test_assess_risks_medium_health(self):
        """测试中等健康度风险"""
        summary = {"health_status": "H2"}
        milestones = {"summary": {"delayed": 0}}
        
        risks = ProjectReportGenerator._assess_risks(summary, milestones)
        
        assert len(risks) == 1
        assert risks[0]["type"] == "健康度"
        assert risks[0]["level"] == "MEDIUM"

    def test_assess_risks_high_health(self):
        """测试高风险健康度"""
        summary = {"health_status": "H3"}
        milestones = {"summary": {"delayed": 0}}
        
        risks = ProjectReportGenerator._assess_risks(summary, milestones)
        
        assert len(risks) == 1
        assert risks[0]["level"] == "HIGH"

    def test_assess_risks_delayed_milestones(self):
        """测试里程碑延期风险"""
        summary = {"health_status": "H1"}
        milestones = {"summary": {"delayed": 2}}
        
        risks = ProjectReportGenerator._assess_risks(summary, milestones)
        
        assert len(risks) == 1
        assert risks[0]["type"] == "里程碑延期"
        assert risks[0]["level"] == "HIGH"
        assert "2 个里程碑延期" in risks[0]["description"]

    def test_assess_risks_multiple_risks(self):
        """测试多重风险"""
        summary = {"health_status": "H3"}
        milestones = {"summary": {"delayed": 1}}
        
        risks = ProjectReportGenerator._assess_risks(summary, milestones)
        
        assert len(risks) == 2
