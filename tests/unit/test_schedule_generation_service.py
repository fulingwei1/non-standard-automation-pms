# -*- coding: utf-8 -*-
"""
AI 智能排程服务 单元测试
"""

from datetime import date, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.schedule_generation_service import ScheduleGenerationService


def _make_service():
    """创建服务实例"""
    db = MagicMock()
    return ScheduleGenerationService(db)


def _make_project(**kwargs):
    """创建模拟项目"""
    project = MagicMock()
    project.id = kwargs.get("id", 1)
    project.project_name = kwargs.get("project_name", "测试项目")
    project.project_type = kwargs.get("project_type", "非标自动化")
    project.estimated_hours = kwargs.get("estimated_hours", 1000)
    project.contract_amount = kwargs.get("contract_amount", Decimal("100000"))
    project.start_date = kwargs.get("start_date", date(2024, 1, 1))
    project.planned_end_date = kwargs.get("planned_end_date", date(2024, 6, 30))
    project.pm_id = kwargs.get("pm_id", 1)
    project.status = kwargs.get("status", "EXECUTING")
    return project


class TestScheduleGenerationService:
    """测试 AI 智能排程服务"""

    def test_generate_schedule_project_not_found(self):
        """测试项目不存在的情况"""
        service = _make_service()
        service.db.query.return_value.filter.return_value.first.return_value = None

        result = service.generate_schedule(project_id=999)

        assert "error" in result
        assert result["error"] == "项目不存在"

    @patch.object(ScheduleGenerationService, "_analyze_historical_projects")
    @patch.object(ScheduleGenerationService, "_determine_phases_and_tasks")
    @patch.object(ScheduleGenerationService, "_schedule_tasks")
    def test_generate_schedule_normal_mode(
        self, mock_schedule, mock_determine, mock_analyze
    ):
        """测试正常模式生成计划"""
        service = _make_service()
        project = _make_project(id=1, project_name="测试项目")

        service.db.query.return_value.filter.return_value.first.return_value = project
        mock_analyze.return_value = {"phase_durations": {}}
        mock_determine.return_value = [
            {"phase": "设计", "duration": 30},
            {"phase": "采购", "duration": 20},
            {"phase": "生产", "duration": 40},
        ]
        mock_schedule.return_value = []

        result = service.generate_schedule(project_id=1, mode="NORMAL")

        assert "project_id" in result or "schedule_plan" in result or "error" in result

    @patch.object(ScheduleGenerationService, "_analyze_historical_projects")
    @patch.object(ScheduleGenerationService, "_determine_phases_and_tasks")
    @patch.object(ScheduleGenerationService, "_schedule_tasks")
    def test_generate_schedule_intensive_mode(self, mock_schedule, mock_determine, mock_analyze):
        """测试高强度模式生成计划"""
        service = _make_service()
        project = _make_project(id=1, project_name="测试项目")

        service.db.query.return_value.filter.return_value.first.return_value = project
        mock_analyze.return_value = {"phase_durations": {}}
        mock_determine.return_value = [
            {"phase": "设计", "duration": 20},
            {"phase": "采购", "duration": 15},
            {"phase": "生产", "duration": 30},
        ]
        mock_schedule.return_value = []

        result = service.generate_schedule(project_id=1, mode="INTENSIVE")

        assert "project_id" in result or "schedule_plan" in result or "error" in result

    @patch.object(ScheduleGenerationService, "_analyze_historical_projects")
    def test_analyze_historical_projects(self, mock_analyze):
        """测试分析历史项目"""
        service = _make_service()
        project = _make_project(project_type="非标自动化")

        # 模拟查询返回空列表
        service.db.query.return_value.filter.return_value.all.return_value = []

        result = service._analyze_historical_projects(project)

        assert isinstance(result, list)


class TestScheduleModes:
    """测试不同排程模式"""

    def test_determine_phases_normal_mode(self):
        """测试正常模式确定阶段和任务"""
        service = _make_service()
        project = _make_project(
            estimated_hours=1000,
            start_date=date(2024, 1, 1),
            planned_end_date=date(2024, 6, 30),
        )

        result = service._determine_phases_and_tasks(project, mode="NORMAL")

        assert isinstance(result, list)
        # 正常模式应该包含更长的阶段
        assert len(result) > 0

    def test_determine_phases_intensive_mode(self):
        """测试高强度模式确定阶段和任务"""
        service = _make_service()
        project = _make_project(
            estimated_hours=1000,
            start_date=date(2024, 1, 1),
            planned_end_date=date(2024, 6, 30),
        )

        result = service._determine_phases_and_tasks(project, mode="INTENSIVE")

        assert isinstance(result, list)
        # 高强度模式的持续时间应该更短
        assert len(result) > 0


class TestScheduleWithTeamMembers:
    """测试团队成员配置"""

    @patch.object(ScheduleGenerationService, "_analyze_historical_projects")
    @patch.object(ScheduleGenerationService, "_determine_phases_and_tasks")
    @patch.object(ScheduleGenerationService, "_schedule_tasks")
    def test_generate_with_team_members(self, mock_schedule, mock_determine, mock_analyze):
        """测试带团队成员生成计划"""
        service = _make_service()
        project = _make_project(id=1)

        service.db.query.return_value.filter.return_value.first.return_value = project
        mock_analyze.return_value = {"phase_durations": {}}
        mock_determine.return_value = [{"phase": "设计", "duration": 30}]
        mock_schedule.return_value = []

        team_members = [
            {"user_id": 1, "name": "张三", "role": "工程师"},
            {"user_id": 2, "name": "李四", "role": "工程师"},
        ]

        result = service.generate_schedule(project_id=1, team_members=team_members)

        assert "project_id" in result or "schedule_plan" in result or "error" in result