# -*- coding: utf-8 -*-
"""第三批覆盖率测试 - change_impact_ai_service"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from datetime import datetime
from decimal import Decimal

pytest.importorskip("app.services.change_impact_ai_service")

from app.services.change_impact_ai_service import ChangeImpactAIService


def make_db():
    return MagicMock()


def make_change_request(**kw):
    c = MagicMock()
    c.id = kw.get("id", 1)
    c.project_id = kw.get("project_id", 1)
    c.change_title = kw.get("change_title", "Test Change")
    c.change_type = kw.get("change_type", "SCOPE")
    c.description = kw.get("description", "Test description")
    return c


def make_project(**kw):
    p = MagicMock()
    p.id = kw.get("id", 1)
    p.project_name = kw.get("project_name", "TestProject")
    p.budget_amount = kw.get("budget_amount", Decimal("100000"))
    p.actual_cost = kw.get("actual_cost", Decimal("50000"))
    return p


class TestAnalyzeChangeImpact:
    @pytest.mark.asyncio
    async def test_change_not_found_raises(self):
        db = make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = ChangeImpactAIService(db_session)
        with pytest.raises(ValueError, match="变更请求.*不存在"):
            await svc.analyze_change_impact(999, 1)

    @pytest.mark.asyncio
    async def test_project_not_found_raises(self):
        db = make_db()
        change = make_change_request(project_id=999)
        # First query returns change, second returns None for project
        db.query.return_value.filter.return_value.first.side_effect = [change, None]
        svc = ChangeImpactAIService(db_session)
        with pytest.raises(ValueError, match="项目.*不存在"):
            await svc.analyze_change_impact(1, 1)


class TestCalculateOverallRisk:
    def test_low_risk(self):
        db = make_db()
        svc = ChangeImpactAIService(db_session)
        result = svc._calculate_overall_risk(
            schedule_impact={"level": "NONE", "delay_days": 0},
            cost_impact={"level": "NONE", "amount": 0},
            quality_impact={"level": "NONE", "mitigation_required": False},
            resource_impact={"level": "NONE"},
            chain_reaction={"detected": False, "depth": 0},
        )
        assert result["level"] == "LOW"
        assert result["score"] >= 0

    def test_critical_risk(self):
        db = make_db()
        svc = ChangeImpactAIService(db_session)
        result = svc._calculate_overall_risk(
            schedule_impact={"level": "CRITICAL", "delay_days": 30},
            cost_impact={"level": "CRITICAL", "amount": 500000},
            quality_impact={"level": "HIGH", "mitigation_required": True},
            resource_impact={"level": "HIGH"},
            chain_reaction={"detected": True, "depth": 3},
        )
        assert result["level"] in ("HIGH", "CRITICAL")
        assert result["score"] > 50

    def test_medium_risk(self):
        db = make_db()
        svc = ChangeImpactAIService(db_session)
        result = svc._calculate_overall_risk(
            schedule_impact={"level": "MEDIUM", "delay_days": 5},
            cost_impact={"level": "LOW", "amount": 5000},
            quality_impact={"level": "LOW", "mitigation_required": False},
            resource_impact={"level": "NONE"},
            chain_reaction={"detected": False, "depth": 0},
        )
        assert result["score"] > 0
        assert "summary" in result


class TestCalculateDependencyDepth:
    def test_no_dependencies(self):
        db = make_db()
        svc = ChangeImpactAIService(db_session)
        result = svc._calculate_dependency_depth(1, {})
        assert result == 1

    def test_chain_dependencies(self):
        db = make_db()
        svc = ChangeImpactAIService(db_session)
        dep_graph = {1: [2], 2: [3], 3: [4]}
        result = svc._calculate_dependency_depth(1, dep_graph)
        assert result == 4

    def test_circular_reference_handled(self):
        db = make_db()
        svc = ChangeImpactAIService(db_session)
        dep_graph = {1: [2], 2: [1]}  # circular
        # Should not infinite loop
        result = svc._calculate_dependency_depth(1, dep_graph)
        assert result >= 1


class TestIdentifyChainReactions:
    def test_no_dependencies(self):
        db = make_db()
        svc = ChangeImpactAIService(db_session)
        change = make_change_request()
        project = make_project()
        context = {"dependencies": [], "tasks": []}
        result = svc._identify_chain_reactions(change, project, context)
        assert result["detected"] is False
        assert result["depth"] == 0

    def test_with_dependencies(self):
        db = make_db()
        svc = ChangeImpactAIService(db_session)
        change = make_change_request()
        project = make_project()
        context = {
            "dependencies": [
                {"task_id": 1, "depends_on": 2, "type": "FS"},
                {"task_id": 2, "depends_on": 3, "type": "FS"},
            ],
            "tasks": [
                {"id": 1, "name": "Task 1", "status": "PENDING"},
                {"id": 2, "name": "Task 2", "status": "TODO"},
            ],
        }
        result = svc._identify_chain_reactions(change, project, context)
        assert "depth" in result
        assert "dependency_tree" in result


class TestGatherAnalysisContext:
    def test_gather_context(self):
        db = make_db()
        
        # change_type and change_source need .value attribute (enums in real code)
        change = MagicMock()
        change.id = 1
        change.change_code = "CHG-001"
        change.title = "Test Change"
        change.description = "Test"
        change.change_type = None  # avoid .value call on string
        change.change_source = None
        change.time_impact = 0
        change.cost_impact = None
        change.project_id = 1

        project = make_project()
        project.plan_start = None
        project.plan_end = None
        
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.all.return_value = []
        db.query.return_value = mock_q

        svc = ChangeImpactAIService(db_session)
        context = svc._gather_analysis_context(change, project)
        assert isinstance(context, dict)
        assert "tasks" in context
        assert "dependencies" in context
