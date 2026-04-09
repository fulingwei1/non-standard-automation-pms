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
    project.product_category = kwargs.get("product_category", "自动化设备")
    project.industry = kwargs.get("industry", "制造业")
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

    def test_generate_schedule_success(self):
        """测试成功生成计划"""
        service = _make_service()
        project = _make_project(id=1, project_name="测试项目")

        service.db.query.return_value.filter.return_value.first.return_value = project

        result = service.generate_schedule(project_id=1, mode="NORMAL")

        # 验证返回了计划
        assert result is not None
        assert isinstance(result, dict)

    def test_generate_schedule_intensive_mode(self):
        """测试高强度模式生成计划"""
        service = _make_service()
        project = _make_project(id=1, project_name="测试项目")

        service.db.query.return_value.filter.return_value.first.return_value = project

        result = service.generate_schedule(project_id=1, mode="INTENSIVE")

        assert result is not None
        assert isinstance(result, dict)


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

        assert isinstance(result, dict)
        assert len(result) > 0
        # 验证包含主要阶段
        assert "engineering" in result or "design" in result

    def test_determine_phases_intensive_mode(self):
        """测试高强度模式确定阶段和任务"""
        service = _make_service()
        project = _make_project(
            estimated_hours=1000,
            start_date=date(2024, 1, 1),
            planned_end_date=date(2024, 6, 30),
        )

        result = service._determine_phases_and_tasks(project, mode="INTENSIVE")

        assert isinstance(result, dict)
        assert len(result) > 0


class TestScheduleWithTeamMembers:
    """测试团队成员配置"""

    def test_generate_with_team_members(self):
        """测试带团队成员生成计划"""
        service = _make_service()
        project = _make_project(id=1)

        service.db.query.return_value.filter.return_value.first.return_value = project

        team_members = [
            {"user_id": 1, "name": "张三", "role": "工程师"},
            {"user_id": 2, "name": "李四", "role": "工程师"},
        ]

        result = service.generate_schedule(project_id=1, team_members=team_members)

        assert result is not None
        assert isinstance(result, dict)


class TestEfficiencyFactors:
    """测试效率系数计算"""

    def test_calculate_efficiency_factors_with_members(self):
        """测试有团队成员时的效率系数"""
        service = _make_service()

        team_members = [
            {"user_id": 1, "name": "张三", "role": "工程师"},
            {"user_id": 2, "name": "李四", "role": "工程师"},
        ]

        result = service._calculate_efficiency_factors(team_members)

        assert isinstance(result, dict)

    def test_calculate_efficiency_factors_without_members(self):
        """测试无团队成员时的效率系数"""
        service = _make_service()

        result = service._calculate_efficiency_factors(None)

        assert isinstance(result, dict)


class TestHistoricalAnalysis:
    """测试历史项目分析"""

    def test_analyze_historical_projects(self):
        """测试分析历史项目"""
        service = _make_service()
        project = _make_project(project_type="非标自动化")

        # 模拟查询返回空列表
        service.db.query.return_value.filter.return_value.all.return_value = []

        result = service._analyze_historical_projects(project)

        assert isinstance(result, dict)
        assert "phase_durations" in result or "sample_count" in result or "confidence" in result

    def test_get_default_historical_data(self):
        """测试获取默认历史数据"""
        service = _make_service()

        result = service._get_default_historical_data()

        assert isinstance(result, dict)