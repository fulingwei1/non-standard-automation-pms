# -*- coding: utf-8 -*-
"""第二十五批 - project_workspace_service 单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import date

pytest.importorskip("app.services.project_workspace_service")

from app.services.project_workspace_service import (
    build_project_basic_info,
    build_team_info,
    build_task_info,
    build_bonus_info,
    build_meeting_info,
    build_issue_info,
    build_solution_info,
    build_document_info,
)


def _make_project():
    proj = MagicMock()
    proj.id = 1
    proj.project_code = "PRJ001"
    proj.project_name = "测试项目"
    proj.stage = "S2"
    proj.status = "ST01"
    proj.health = "H1"
    proj.progress_pct = 45
    proj.contract_amount = 200000
    proj.pm_name = "张三"
    return proj


# ── build_project_basic_info ──────────────────────────────────────────────────

class TestBuildProjectBasicInfo:
    def test_returns_dict_with_correct_keys(self):
        result = build_project_basic_info(_make_project())
        expected = {"id", "project_code", "project_name", "stage", "status",
                    "health", "progress_pct", "contract_amount", "pm_name"}
        assert expected.issubset(result.keys())

    def test_progress_pct_is_float(self):
        result = build_project_basic_info(_make_project())
        assert isinstance(result["progress_pct"], float)

    def test_contract_amount_is_float(self):
        result = build_project_basic_info(_make_project())
        assert isinstance(result["contract_amount"], float)

    def test_values_mapped_correctly(self):
        proj = _make_project()
        result = build_project_basic_info(proj)
        assert result["project_code"] == "PRJ001"
        assert result["pm_name"] == "张三"
        assert result["stage"] == "S2"

    def test_none_progress_defaults_to_zero(self):
        proj = _make_project()
        proj.progress_pct = None
        result = build_project_basic_info(proj)
        assert result["progress_pct"] == 0.0

    def test_none_contract_amount_defaults_to_zero(self):
        proj = _make_project()
        proj.contract_amount = None
        result = build_project_basic_info(proj)
        assert result["contract_amount"] == 0.0


# ── build_team_info ───────────────────────────────────────────────────────────

class TestBuildTeamInfo:
    def test_returns_list_of_member_dicts(self):
        db = MagicMock()
        member = MagicMock()
        member.user_id = 1
        member.role_code = "PM"
        member.allocation_pct = 100
        member.start_date = date(2025, 1, 1)
        member.end_date = None
        member.user = MagicMock(real_name="张三", username="zhangsan")
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [member]
        result = build_team_info(db, project_id=1)
        assert len(result) == 1
        assert result[0]["user_id"] == 1
        assert result[0]["role_code"] == "PM"

    def test_returns_empty_list_when_no_members(self):
        db = MagicMock()
        db.query.return_value.options.return_value.filter.return_value.all.return_value = []
        result = build_team_info(db, project_id=1)
        assert result == []

    def test_allocation_pct_is_float(self):
        db = MagicMock()
        member = MagicMock()
        member.user_id = 2
        member.role_code = "DEV"
        member.allocation_pct = 80
        member.start_date = None
        member.end_date = None
        member.user = MagicMock(real_name="李四", username="lisi")
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [member]
        result = build_team_info(db, project_id=1)
        assert isinstance(result[0]["allocation_pct"], float)

    def test_start_date_formatted_as_isoformat(self):
        db = MagicMock()
        member = MagicMock()
        member.user_id = 3
        member.role_code = "QA"
        member.allocation_pct = 50
        member.start_date = date(2025, 3, 15)
        member.end_date = None
        member.user = MagicMock(real_name="王五", username="wangwu")
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [member]
        result = build_team_info(db, project_id=1)
        assert result[0]["start_date"] == "2025-03-15"

    def test_none_start_date_is_none(self):
        db = MagicMock()
        member = MagicMock()
        member.user_id = 4
        member.role_code = "DEV"
        member.allocation_pct = 100
        member.start_date = None
        member.end_date = None
        member.user = MagicMock(real_name="赵六", username="zhaoliu")
        db.query.return_value.options.return_value.filter.return_value.all.return_value = [member]
        result = build_team_info(db, project_id=1)
        assert result[0]["start_date"] is None


# ── build_task_info ───────────────────────────────────────────────────────────

class TestBuildTaskInfo:
    def test_returns_list_of_task_dicts(self):
        db = MagicMock()
        task = MagicMock()
        task.id = 1
        task.title = "任务1"
        task.status = "IN_PROGRESS"
        task.assignee_name = "张三"
        task.plan_end_date = date(2025, 5, 31)
        task.progress = 60
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = [task]
        result = build_task_info(db, project_id=1)
        assert len(result) == 1
        assert result[0]["title"] == "任务1"

    def test_returns_empty_when_no_tasks(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        result = build_task_info(db, project_id=1)
        assert result == []

    def test_progress_is_float(self):
        db = MagicMock()
        task = MagicMock()
        task.id = 2
        task.title = "任务2"
        task.status = "DONE"
        task.assignee_name = None
        task.plan_end_date = None
        task.progress = 100
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = [task]
        result = build_task_info(db, project_id=1)
        assert isinstance(result[0]["progress"], float)

    def test_none_plan_end_date_is_none(self):
        db = MagicMock()
        task = MagicMock()
        task.id = 3
        task.title = "任务3"
        task.status = "TODO"
        task.assignee_name = "李四"
        task.plan_end_date = None
        task.progress = 0
        db.query.return_value.filter.return_value.limit.return_value.all.return_value = [task]
        result = build_task_info(db, project_id=1)
        assert result[0]["plan_end_date"] is None


# ── build_bonus_info ──────────────────────────────────────────────────────────

class TestBuildBonusInfo:
    def test_returns_dict_with_expected_keys(self):
        db = MagicMock()
        with patch("app.services.project_workspace_service.ProjectBonusService") as MockBonus:
            mock_svc = MockBonus.return_value
            mock_svc.get_project_bonus_rules.return_value = []
            mock_svc.get_project_bonus_calculations.return_value = []
            mock_svc.get_project_bonus_distributions.return_value = []
            mock_svc.get_project_bonus_statistics.return_value = {}
            mock_svc.get_project_member_bonus_summary.return_value = []
            result = build_bonus_info(db, project_id=1)
        assert set(result.keys()) == {"rules", "calculations", "distributions", "statistics", "member_summary"}

    def test_returns_empty_on_exception(self):
        db = MagicMock()
        with patch("app.services.project_workspace_service.ProjectBonusService") as MockBonus:
            MockBonus.side_effect = Exception("数据库错误")
            result = build_bonus_info(db, project_id=1)
        assert result["rules"] == []
        assert result["calculations"] == []
        assert result["statistics"] == {}


# ── build_meeting_info ────────────────────────────────────────────────────────

class TestBuildMeetingInfo:
    def test_returns_dict_with_meetings_and_statistics(self):
        db = MagicMock()
        with patch("app.services.project_workspace_service.ProjectMeetingService") as MockMeeting:
            mock_svc = MockMeeting.return_value
            mock_svc.get_project_meetings.return_value = []
            mock_svc.get_project_meeting_statistics.return_value = {}
            result = build_meeting_info(db, project_id=1)
        assert "meetings" in result
        assert "statistics" in result

    def test_returns_empty_on_exception(self):
        db = MagicMock()
        with patch("app.services.project_workspace_service.ProjectMeetingService") as MockMeeting:
            MockMeeting.side_effect = Exception("失败")
            result = build_meeting_info(db, project_id=1)
        assert result["meetings"] == []
        assert result["statistics"] == {}


# ── build_issue_info ──────────────────────────────────────────────────────────

class TestBuildIssueInfo:
    def test_returns_dict_with_issues_key(self):
        db = MagicMock()
        issue = MagicMock()
        issue.id = 1
        issue.issue_no = "ISS001"
        issue.title = "问题标题"
        issue.status = "OPEN"
        issue.severity = "HIGH"
        issue.priority = "P1"
        issue.solution = "方案"
        issue.assignee_name = "张三"
        issue.report_date = date(2025, 4, 1)
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [issue]
        result = build_issue_info(db, project_id=1)
        assert "issues" in result
        assert len(result["issues"]) == 1

    def test_has_solution_flag(self):
        db = MagicMock()
        issue = MagicMock()
        issue.id = 2
        issue.issue_no = "ISS002"
        issue.title = "有方案的问题"
        issue.status = "CLOSED"
        issue.severity = "LOW"
        issue.priority = "P3"
        issue.solution = "解决方案内容"
        issue.assignee_name = None
        issue.report_date = None
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [issue]
        result = build_issue_info(db, project_id=1)
        assert result["issues"][0]["has_solution"] is True

    def test_empty_solution_has_solution_false(self):
        db = MagicMock()
        issue = MagicMock()
        issue.id = 3
        issue.issue_no = "ISS003"
        issue.title = "无方案问题"
        issue.status = "OPEN"
        issue.severity = "MEDIUM"
        issue.priority = "P2"
        issue.solution = ""
        issue.assignee_name = "李四"
        issue.report_date = None
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [issue]
        result = build_issue_info(db, project_id=1)
        assert result["issues"][0]["has_solution"] is False


# ── build_solution_info ───────────────────────────────────────────────────────

class TestBuildSolutionInfo:
    def test_returns_dict_with_solutions_and_statistics(self):
        db = MagicMock()
        with patch("app.services.project_workspace_service.ProjectSolutionService") as MockSolution:
            mock_svc = MockSolution.return_value
            mock_svc.get_project_solutions.return_value = []
            mock_svc.get_project_solution_statistics.return_value = {}
            result = build_solution_info(db, project_id=1)
        assert "solutions" in result
        assert "statistics" in result

    def test_limits_solutions_to_20(self):
        db = MagicMock()
        with patch("app.services.project_workspace_service.ProjectSolutionService") as MockSolution:
            mock_svc = MockSolution.return_value
            mock_svc.get_project_solutions.return_value = list(range(30))
            mock_svc.get_project_solution_statistics.return_value = {}
            result = build_solution_info(db, project_id=1)
        assert len(result["solutions"]) == 20

    def test_returns_empty_on_exception(self):
        db = MagicMock()
        with patch("app.services.project_workspace_service.ProjectSolutionService") as MockSolution:
            MockSolution.side_effect = Exception("错误")
            result = build_solution_info(db, project_id=1)
        assert result["solutions"] == []
        assert result["statistics"] == {}


# ── build_document_info ───────────────────────────────────────────────────────

class TestBuildDocumentInfo:
    def test_returns_list_of_document_dicts(self):
        db = MagicMock()
        doc = MagicMock()
        doc.id = 1
        doc.doc_name = "需求文档"
        doc.doc_type = "REQUIREMENT"
        doc.version = "v1.0"
        doc.status = "APPROVED"
        doc.created_at = MagicMock()
        doc.created_at.isoformat.return_value = "2025-01-01T00:00:00"
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [doc]
        result = build_document_info(db, project_id=1)
        assert len(result) == 1
        assert result[0]["doc_name"] == "需求文档"

    def test_returns_empty_when_no_documents(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        result = build_document_info(db, project_id=1)
        assert result == []
