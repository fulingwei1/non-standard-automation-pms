# -*- coding: utf-8 -*-
"""第四十二批：ecn_knowledge_service/solution_extraction.py 单元测试"""
import pytest

pytest.importorskip("app.services.ecn_knowledge_service.solution_extraction")

from unittest.mock import MagicMock, patch
from app.services.ecn_knowledge_service.solution_extraction import (
    extract_solution,
    _auto_extract_solution,
    _extract_keywords,
    _build_solution_description,
    _extract_solution_steps,
)


def make_service():
    svc = MagicMock()
    return svc


def make_ecn(**kw):
    ecn = MagicMock()
    ecn.id = 1
    ecn.ecn_type = "DESIGN"
    ecn.root_cause_category = "QUALITY"
    ecn.solution = kw.get("solution", "")
    ecn.execution_note = kw.get("execution_note", "")
    ecn.change_description = kw.get("change_description", "")
    ecn.root_cause_analysis = kw.get("root_cause_analysis", "")
    ecn.cost_impact = kw.get("cost_impact", 0)
    ecn.schedule_impact_days = kw.get("schedule_impact_days", 0)
    return ecn


# ------------------------------------------------------------------ tests ---

def test_extract_solution_ecn_not_found():
    svc = make_service()
    svc.db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError, match="不存在"):
        extract_solution(svc, ecn_id=999)


def test_extract_solution_auto_returns_dict():
    svc = make_service()
    ecn = make_ecn(solution="use bolt A instead of B")
    svc.db.query.return_value.filter.return_value.first.return_value = ecn
    svc.db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
    result = extract_solution(svc, ecn_id=1)
    assert "ecn_id" in result
    assert "solution" in result
    assert "keywords" in result


def test_auto_extract_prefers_solution_field():
    ecn = make_ecn(solution="解决方案A")
    result = _auto_extract_solution(ecn)
    assert result == "解决方案A"


def test_auto_extract_falls_back_to_execution_note():
    ecn = make_ecn(solution="", execution_note="执行说明B")
    result = _auto_extract_solution(ecn)
    assert result == "执行说明B"


def test_auto_extract_from_change_description():
    ecn = make_ecn(solution="", execution_note="",
                   change_description="问题描述。解决方案：更换零件C")
    result = _auto_extract_solution(ecn)
    assert "更换零件C" in result


def test_extract_keywords_includes_ecn_type():
    svc = make_service()
    ecn = make_ecn()
    svc.db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
    keywords = _extract_keywords(svc, ecn)
    assert "DESIGN" in keywords


def test_build_solution_description_from_ecn_fields():
    ecn = make_ecn(solution="", change_description="变更说明", root_cause_analysis="根因")
    desc = _build_solution_description(ecn, "")
    assert "变更说明" in desc or "根因" in desc


def test_extract_solution_steps_from_numbered_text():
    svc = make_service()
    ecn = make_ecn()
    solution = "1. 第一步\n2. 第二步\n- 辅助说明"
    steps = _extract_solution_steps(svc, ecn, solution)
    assert any("第一步" in s for s in steps)
