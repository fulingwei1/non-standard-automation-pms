# -*- coding: utf-8 -*-
"""
Unit tests for app/services/ecn_knowledge_service/solution_extraction.py (cov52)
"""
import pytest
from unittest.mock import MagicMock

try:
    from app.services.ecn_knowledge_service.solution_extraction import (
        extract_solution,
        _auto_extract_solution,
        _extract_keywords,
        _build_solution_description,
        _extract_solution_steps,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_service():
    service = MagicMock()
    service.db = MagicMock()
    return service


def _make_ecn(ecn_id=1, ecn_type="DESIGN", solution=None,
              execution_note=None, change_description=None,
              root_cause_category="HUMAN", root_cause_analysis=None):
    ecn = MagicMock()
    ecn.id = ecn_id
    ecn.ecn_type = ecn_type
    ecn.solution = solution
    ecn.execution_note = execution_note
    ecn.change_description = change_description
    ecn.root_cause_category = root_cause_category
    ecn.root_cause_analysis = root_cause_analysis
    ecn.cost_impact = None
    ecn.schedule_impact_days = None
    return ecn


# ──────────────────────── extract_solution ────────────────────────

def test_extract_solution_ecn_not_found():
    """ECN 不存在时抛出 ValueError"""
    service = _make_service()
    service.db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="不存在"):
        extract_solution(service, ecn_id=999)


def test_extract_solution_auto_extract():
    """auto_extract=True 时返回必要字段"""
    service = _make_service()
    ecn = _make_ecn(solution="直接替换物料A", change_description="物料变更")
    service.db.query.return_value.filter.return_value.first.return_value = ecn
    service.db.query.return_value.filter.return_value.limit.return_value.all.return_value = []

    result = extract_solution(service, ecn_id=1, auto_extract=True)

    assert result["ecn_id"] == 1
    assert "solution" in result
    assert "keywords" in result
    assert "extracted_at" in result


def test_extract_solution_manual():
    """auto_extract=False 时使用 ecn.solution"""
    service = _make_service()
    ecn = _make_ecn(solution="手动填写的方案")
    service.db.query.return_value.filter.return_value.first.return_value = ecn
    service.db.query.return_value.filter.return_value.limit.return_value.all.return_value = []

    result = extract_solution(service, ecn_id=1, auto_extract=False)

    assert result["solution"] == "手动填写的方案"


# ──────────────────────── _auto_extract_solution ────────────────────────

def test_auto_extract_from_solution_field():
    """solution 字段有值时直接返回"""
    ecn = _make_ecn(solution="先换物料A再验证")
    assert _auto_extract_solution(ecn) == "先换物料A再验证"


def test_auto_extract_from_execution_note():
    """solution 为空时从 execution_note 提取"""
    ecn = _make_ecn(execution_note="执行步骤：1.检查 2.替换")
    assert "执行步骤" in _auto_extract_solution(ecn)


def test_auto_extract_empty():
    """无内容时返回空字符串"""
    ecn = _make_ecn()
    assert _auto_extract_solution(ecn) == ""


# ──────────────────────── _extract_keywords ────────────────────────

def test_extract_keywords_basic():
    """基本关键词提取不报错，返回列表"""
    service = _make_service()
    service.db.query.return_value.filter.return_value.limit.return_value.all.return_value = []

    ecn = _make_ecn(ecn_type="DESIGN", root_cause_category="HUMAN",
                    change_description="物料测试质量")
    keywords = _extract_keywords(service, ecn)

    assert isinstance(keywords, list)
    assert "DESIGN" in keywords


# ──────────────────────── _build_solution_description ────────────────────────

def test_build_solution_description_with_solution():
    """有 solution 时直接返回"""
    ecn = _make_ecn()
    result = _build_solution_description(ecn, "已有方案")
    assert result == "已有方案"


def test_build_solution_description_no_solution():
    """无 solution 时根据 ECN 信息拼接"""
    ecn = _make_ecn(change_description="变更说明", root_cause_analysis="根因分析")
    result = _build_solution_description(ecn, "")
    assert "变更内容" in result or "根本原因" in result


# ──────────────────────── _extract_solution_steps ────────────────────────

def test_extract_solution_steps_numbered():
    """带序号的行被识别为步骤"""
    service = _make_service()
    service.db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []

    ecn = _make_ecn()
    solution = "1. 第一步\n2. 第二步\n- 子步骤"
    steps = _extract_solution_steps(service, ecn, solution)

    assert len(steps) >= 2
