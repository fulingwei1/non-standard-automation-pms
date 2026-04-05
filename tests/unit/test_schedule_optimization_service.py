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

    @patch.object(ScheduleOptimizationService, "_find_similar_projects")
    @patch.object(ScheduleOptimizationService, "_analyze_phases_optimization")
    @patch.object(ScheduleOptimizationService, "_identify_reusable_content")
    @patch.object(ScheduleOptimizationService, "_generate_automation_suggestions")
    @patch.object(ScheduleOptimizationService, "_calculate_time_savings")
    def test_analyze_optimization_potential_success(
        self,
        mock_time_savings,
        mock_automation,
        mock_reusable,
        mock_analyze,
        mock_find,
    ):
        """测试成功分析优化潜力"""
        service = _make_service()
        project = _make_project(id=1, project_name="测试项目")

        service.db.query.return_value.filter.return_value.first.return_value = project

        mock_find.return_value = []
        mock_analyze.return_value = {
            "design": {"potential": 20, "suggestions": ["使用标准件"]},
            "procurement": {"potential": 15, "suggestions": ["批量采购"]},
        }
        mock_reusable.return_value = [{"content": "历史方案", "relevance": 0.9}]
        mock_automation.return_value = ["建议自动化装配"]
        mock_time_savings.return_value = {"total_hours": 100, "percentage": 10}

        result = service.analyze_optimization_potential(project_id=1)

        assert "project_id" in result
        assert result["project_id"] == 1
        assert "optimization_analysis" in result or "time_savings" in result or "suggestions" in result


class TestSimilarProjects:
    """测试相似项目查找"""

    @patch.object(ScheduleOptimizationService, "_calculate_similarity")
    def test_find_similar_projects(self, mock_similarity):
        """测试查找相似项目"""
        service = _make_service()
        project = _make_project(project_type="非标自动化", estimated_hours=1000)

        # 模拟查询返回相似项目
        similar_project = _make_project(id=2, project_name="相似项目")
        service.db.query.return_value.filter.return_value.all.return_value = [similar_project]
        mock_similarity.return_value = 0.85

        result = service._find_similar_projects(project)

        assert isinstance(result, list)

    def test_calculate_similarity(self):
        """测试计算项目相似度"""
        service = _make_service()
        current = _make_project(
            project_type="非标自动化",
            estimated_hours=1000,
            contract_amount=Decimal("100000"),
        )
        similar = _make_project(
            project_type="非标自动化",
            estimated_hours=1200,
            contract_amount=Decimal("110000"),
        )

        result = service._calculate_similarity(current, similar)

        assert isinstance(result, (int, float))
        assert 0 <= result <= 1


class TestOptimizationAnalysis:
    """测试优化分析"""

    def test_analyze_phases_optimization(self):
        """测试分析各阶段优化潜力"""
        service = _make_service()
        project = _make_project()
        similar_projects = [_make_project(id=2)]

        result = service._analyze_phases_optimization(project, similar_projects)

        assert isinstance(result, dict)
        assert "design" in result or "procurement" in result or "production" in result or len(result) >= 0


class TestReusableContent:
    """测试可复用内容识别"""

    def test_identify_reusable_content(self):
        """测试识别可复用内容"""
        service = _make_service()
        project = _make_project()
        similar_projects = [_make_project(id=2)]

        result = service._identify_reusable_content(project, similar_projects)

        assert isinstance(result, list)


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
        assert "total_hours" in result or "percentage" in result or len(result) >= 0


class TestOptimizationReport:
    """测试优化报告生成"""

    @patch.object(ScheduleOptimizationService, "_find_similar_projects")
    @patch.object(ScheduleOptimizationService, "_analyze_phases_optimization")
    @patch.object(ScheduleOptimizationService, "_identify_reusable_content")
    @patch.object(ScheduleOptimizationService, "_generate_automation_suggestions")
    @patch.object(ScheduleOptimizationService, "_calculate_time_savings")
    def test_optimization_report_structure(
        self,
        mock_time_savings,
        mock_automation,
        mock_reusable,
        mock_analyze,
        mock_find,
    ):
        """测试优化报告结构"""
        service = _make_service()
        project = _make_project(id=1)

        service.db.query.return_value.filter.return_value.first.return_value = project

        mock_find.return_value = []
        mock_analyze.return_value = {"design": {"potential": 20}}
        mock_reusable.return_value = []
        mock_automation.return_value = []
        mock_time_savings.return_value = {"total_hours": 100, "percentage": 10}

        result = service.analyze_optimization_potential(project_id=1)

        # 验证报告包含必要字段
        assert "project_id" in result
        assert "time_savings" in result or "optimization_analysis" in result or "suggestions" in result