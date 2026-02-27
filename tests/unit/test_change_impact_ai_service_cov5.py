# -*- coding: utf-8 -*-
"""第五批：change_impact_ai_service.py 单元测试"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

try:
    from app.services.change_impact_ai_service import ChangeImpactAIService
    HAS_MODULE = True
except ImportError:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="change_impact_ai_service not importable")


def make_service(db=None):
    if db is None:
        db = MagicMock()
    return ChangeImpactAIService()


class TestCalculateDependencyDepth:
    def test_single_node(self):
        svc = make_service()
        dep_graph = {}
        result = svc._calculate_dependency_depth(1, dep_graph)
        assert result == 1

    def test_linear_chain(self):
        svc = make_service()
        dep_graph = {1: [2], 2: [3]}
        result = svc._calculate_dependency_depth(1, dep_graph)
        assert result == 3

    def test_circular_dependency(self):
        svc = make_service()
        dep_graph = {1: [2], 2: [1]}
        # Should not infinite loop
        result = svc._calculate_dependency_depth(1, dep_graph)
        assert result >= 1

    def test_branching(self):
        svc = make_service()
        dep_graph = {1: [2, 3], 2: [4], 3: []}
        result = svc._calculate_dependency_depth(1, dep_graph)
        assert result == 3


class TestCalculateOverallRisk:
    def test_all_none_risk(self):
        svc = make_service()
        result = svc._calculate_overall_risk(
            {"level": "NONE"},
            {"level": "NONE"},
            {"level": "NONE"},
            {"level": "NONE"},
            {"detected": False},
        )
        assert result["level"] == "LOW"
        assert "level" in result

    def test_all_high_risk(self):
        svc = make_service()
        result = svc._calculate_overall_risk(
            {"level": "HIGH"},
            {"level": "HIGH"},
            {"level": "HIGH"},
            {"level": "HIGH"},
            {"detected": True, "depth": 2, "chain": []},
        )
        assert result["level"] in ("HIGH", "CRITICAL")

    def test_critical_risk(self):
        svc = make_service()
        result = svc._calculate_overall_risk(
            {"level": "CRITICAL"},
            {"level": "CRITICAL"},
            {"level": "CRITICAL"},
            {"level": "CRITICAL"},
            {"detected": True, "depth": 3, "chain": []},
        )
        assert result["level"] == "CRITICAL"
        assert result.get("recommended_action") == "ESCALATE"

    def test_medium_risk(self):
        svc = make_service()
        result = svc._calculate_overall_risk(
            {"level": "MEDIUM"},
            {"level": "MEDIUM"},
            {"level": "NONE"},
            {"level": "NONE"},
            {"detected": False},
        )
        assert result["level"] in ("LOW", "MEDIUM")


class TestParseAiResponse:
    def test_parses_json_response(self):
        import json
        svc = make_service()
        data = {"delay_days": 5, "affected_tasks": ["T1", "T2"]}
        response = json.dumps(data)
        default = {"delay_days": 0, "affected_tasks": []}
        result = svc._parse_ai_response(response, default)
        assert isinstance(result, dict)
        assert result["delay_days"] == 5

    def test_handles_non_json(self):
        svc = make_service()
        default = {"delay_days": 0}
        result = svc._parse_ai_response("plain text response", default)
        assert isinstance(result, dict)
        assert result == default


class TestAnalyzeChangeImpact:
    def test_change_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = make_service(db)
        import asyncio
        with pytest.raises(ValueError, match="不存在"):
            asyncio.get_event_loop().run_until_complete(
                svc.analyze_change_impact(999, 1)
            )
