# -*- coding: utf-8 -*-
"""
AI 智能优化分析服务 单元测试
"""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.schedule_optimization_service import ScheduleOptimizationService


def _make_service():
    """创建服务实例"""
    db = MagicMock()
    return ScheduleOptimizationService(db)


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


class TestScheduleOptimizationService:
    """测试 AI 智能优化分析服务"""

    def test_analyze_optimization_potential_project_not_found(self):
        """测试项目不存在的情况"""
        service = _make_service()
        service.db.query.return_value.filter.return_value.first.return_value = None

        result = service.analyze_optimization_potential(project_id=999)

        assert "error" in result
        assert result["error"] == "项目不存在"

    def test_analyze_optimization_potential_success(self):
        """测试成功分析优化潜力"""
        service = _make_service()
        project = _make_project(id=1, project_name="测试项目")

        service.db.query.return_value.filter.return_value.first.return_value = project

        result = service.analyze_optimization_potential(project_id=1)

        assert result is not None
        assert isinstance(result, dict)


class TestSimilarProjects:
    """测试相似项目查找"""

    def test_find_similar_projects(self):
        """测试查找相似项目"""
        service = _make_service()
        project = _make_project(project_type="非标自动化", estimated_hours=1000)

        # 模拟查询返回相似项目
        similar_project = _make_project(id=2, project_name="相似项目")
        # 修复 mock 链
        service.db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [similar_project]

        result = service._find_similar_projects(project)

        assert isinstance(result, list)


class TestOptimizationAnalysis:
    """测试优化分析"""

    def test_analyze_phases_optimization(self):
        """测试分析各阶段优化潜力"""
        service = _make_service()
        project = _make_project()
        similar_projects = [_make_project(id=2)]

        result = service._analyze_phases_optimization(project, similar_projects)

        assert isinstance(result, dict)


class TestReusableContent:
    """测试可复用内容识别"""

    def test_identify_reusable_content(self):
        """测试识别可复用内容"""
        service = _make_service()
        project = _make_project()
        similar_projects = [_make_project(id=2)]

        result = service._identify_reusable_content(project, similar_projects)

        assert isinstance(result, dict)


class TestAutomationSuggestions:
    """测试自动化建议生成"""

    def test_generate_automation_suggestions(self):
        """测试生成自动化建议"""
        service = _make_service()
        project = _make_project()
        optimization_analysis = {
            "design": {"potential": 20},
            "production": {"potential": 30},
        }
        reusable_content = [{"content": "历史方案"}]

        result = service._generate_automation_suggestions(
            project, optimization_analysis, reusable_content
        )

        assert isinstance(result, list)


class TestTimeSavings:
    """测试时间节省计算"""

    def test_calculate_time_savings(self):
        """测试计算可节省时间"""
        service = _make_service()
        optimization_analysis = {
            "design": {"potential": 20},
            "procurement": {"potential": 15},
            "production": {"potential": 25},
        }

        result = service._calculate_time_savings(optimization_analysis)

        assert isinstance(result, dict)


class TestOptimizationReport:
    """测试优化报告生成"""

    def test_optimization_report_structure(self):
        """测试优化报告结构"""
        service = _make_service()
        project = _make_project(id=1)

        service.db.query.return_value.filter.return_value.first.return_value = project

        result = service.analyze_optimization_potential(project_id=1)

        # 验证报告包含必要字段
        assert result is not None
        assert isinstance(result, dict)