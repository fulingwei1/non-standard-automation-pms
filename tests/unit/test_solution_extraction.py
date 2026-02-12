# -*- coding: utf-8 -*-
"""ECN知识库 - 解决方案提取 单元测试"""
import re
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.ecn_knowledge_service.solution_extraction import (
    _auto_extract_solution,
    _build_solution_description,
    _extract_keywords,
    _extract_solution_steps,
    extract_solution,
)


def _make_ecn(**kw):
    ecn = MagicMock()
    ecn.id = kw.get("id", 1)
    ecn.solution = kw.get("solution", None)
    ecn.execution_note = kw.get("execution_note", None)
    ecn.change_description = kw.get("change_description", None)
    ecn.root_cause_analysis = kw.get("root_cause_analysis", None)
    ecn.root_cause_category = kw.get("root_cause_category", None)
    ecn.ecn_type = kw.get("ecn_type", "DESIGN")
    ecn.cost_impact = kw.get("cost_impact", 0)
    ecn.schedule_impact_days = kw.get("schedule_impact_days", 0)
    return ecn


class TestAutoExtractSolution:
    def test_from_solution_field(self):
        ecn = _make_ecn(solution="直接修改BOM")
        assert _auto_extract_solution(ecn) == "直接修改BOM"

    def test_from_execution_note(self):
        ecn = _make_ecn(execution_note="执行更换物料")
        assert _auto_extract_solution(ecn) == "执行更换物料"

    def test_from_change_description_keyword(self):
        ecn = _make_ecn(change_description="问题分析 解决方案 更换电阻")
        result = _auto_extract_solution(ecn)
        assert "更换电阻" in result

    def test_empty_when_nothing(self):
        ecn = _make_ecn()
        assert _auto_extract_solution(ecn) == ""


class TestExtractKeywords:
    def test_includes_ecn_type(self):
        service = MagicMock()
        service.db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        ecn = _make_ecn(ecn_type="DESIGN", root_cause_category="材料")
        kws = _extract_keywords(service, ecn)
        assert "DESIGN" in kws
        assert "材料" in kws

    def test_common_keywords_from_description(self):
        service = MagicMock()
        service.db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
        ecn = _make_ecn(change_description="修改设计图纸和物料")
        kws = _extract_keywords(service, ecn)
        assert "设计" in kws
        assert "物料" in kws


class TestBuildSolutionDescription:
    def test_returns_solution_if_present(self):
        ecn = _make_ecn()
        assert _build_solution_description(ecn, "修复方案") == "修复方案"

    def test_builds_from_ecn_fields(self):
        ecn = _make_ecn(change_description="变更A", root_cause_analysis="原因B")
        result = _build_solution_description(ecn, "")
        assert "变更A" in result
        assert "原因B" in result

    def test_default_message(self):
        ecn = _make_ecn()
        result = _build_solution_description(ecn, "")
        assert "暂无" in result


class TestExtractSolutionSteps:
    def test_numbered_steps(self):
        service = MagicMock()
        solution = "1. 第一步\n2. 第二步"
        ecn = _make_ecn()
        steps = _extract_solution_steps(service, ecn, solution)
        assert len(steps) == 2

    def test_bullet_steps(self):
        service = MagicMock()
        solution = "- 步骤A\n- 步骤B"
        ecn = _make_ecn()
        steps = _extract_solution_steps(service, ecn, solution)
        assert len(steps) == 2

    def test_fallback_to_tasks(self):
        service = MagicMock()
        task = MagicMock()
        task.task_name = "任务1"
        task.task_description = "描述1"
        service.db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [task]
        ecn = _make_ecn()
        steps = _extract_solution_steps(service, ecn, "")
        assert len(steps) == 1


class TestExtractSolution:
    def test_basic_flow(self):
        service = MagicMock()
        ecn = _make_ecn(solution="方案X", cost_impact=100, schedule_impact_days=5)
        service.db.query.return_value.filter.return_value.first.return_value = ecn
        # mock _extract_keywords via service.db
        service.db.query.return_value.filter.return_value.limit.return_value.all.return_value = []

        with patch("app.services.ecn_knowledge_service.solution_extraction._extract_solution_steps", return_value=[]):
            result = extract_solution(service, 1)

        assert result["ecn_id"] == 1
        assert result["estimated_cost"] == 100.0
        assert result["estimated_days"] == 5

    def test_ecn_not_found(self):
        service = MagicMock()
        service.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            extract_solution(service, 999)
