# -*- coding: utf-8 -*-
"""
Unit tests for app/services/ecn_knowledge_service/template.py (cov52)
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.ecn_knowledge_service.template import (
        recommend_solutions,
        create_solution_template,
        apply_solution_template,
        _calculate_template_score,
        _generate_template_code,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_service():
    service = MagicMock()
    service.db = MagicMock()
    return service


def _make_ecn(ecn_id=1, ecn_type="DESIGN", root_cause_category="HUMAN",
              ecn_title="测试ECN"):
    ecn = MagicMock()
    ecn.id = ecn_id
    ecn.ecn_type = ecn_type
    ecn.root_cause_category = root_cause_category
    ecn.ecn_title = ecn_title
    ecn.change_description = "物料变更"
    ecn.solution = None
    ecn.cost_impact = None
    ecn.schedule_impact_days = None
    return ecn


def _make_template(ecn_type="DESIGN", root_cause_category="HUMAN",
                   success_rate=90, usage_count=10):
    t = MagicMock()
    t.id = 1
    t.template_code = "ECN-SOL-001"
    t.template_name = "模板一"
    t.template_category = ecn_type
    t.ecn_type = ecn_type
    t.root_cause_category = root_cause_category
    t.solution_description = "解决步骤"
    t.solution_steps = ["步骤1", "步骤2"]
    t.keywords = ["物料", "设计"]
    t.success_rate = success_rate
    t.usage_count = usage_count
    t.estimated_cost = 1000
    t.estimated_days = 5
    t.is_active = True
    return t


# ──────────────────────── recommend_solutions ────────────────────────

def test_recommend_solutions_ecn_not_found():
    """ECN 不存在时抛出 ValueError"""
    service = _make_service()
    service.db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError, match="不存在"):
        recommend_solutions(service, ecn_id=999)


@patch("app.services.ecn_knowledge_service.template._extract_keywords", return_value=["物料"])
def test_recommend_solutions_no_templates(mock_kw):
    """无活跃模板时返回空列表"""
    service = _make_service()
    ecn = _make_ecn()
    service.db.query.return_value.filter.return_value.first.return_value = ecn
    service.db.query.return_value.filter.return_value.all.return_value = []

    result = recommend_solutions(service, ecn_id=1)
    assert result == []


@patch("app.services.ecn_knowledge_service.template._extract_keywords", return_value=["物料", "DESIGN"])
def test_recommend_solutions_returns_top_n(mock_kw):
    """返回数量不超过 top_n"""
    service = _make_service()
    ecn = _make_ecn()
    service.db.query.return_value.filter.return_value.first.return_value = ecn
    templates = [_make_template() for _ in range(10)]
    service.db.query.return_value.filter.return_value.all.return_value = templates

    result = recommend_solutions(service, ecn_id=1, top_n=3)
    assert len(result) <= 3


# ──────────────────────── create_solution_template ────────────────────────

def test_create_solution_template_ecn_not_found():
    """ECN 不存在时抛出 ValueError"""
    service = _make_service()
    service.db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(ValueError):
        create_solution_template(service, ecn_id=99, template_data={}, created_by=1)


@patch("app.services.ecn_knowledge_service.template._extract_keywords", return_value=["物料"])
@patch("app.services.ecn_knowledge_service.template.save_obj")
def test_create_solution_template_success(mock_save, mock_kw):
    """正常创建模板"""
    service = _make_service()
    ecn = _make_ecn()
    service.db.query.return_value.filter.return_value.first.return_value = ecn

    result = create_solution_template(service, ecn_id=1,
                                      template_data={"template_name": "测试模板"},
                                      created_by=1)
    mock_save.assert_called_once()
    assert result.template_code.startswith("ECN-SOL-")


# ──────────────────────── apply_solution_template ────────────────────────

def test_apply_solution_template_success():
    """正常应用模板到 ECN"""
    service = _make_service()
    ecn = _make_ecn()
    template = _make_template()

    service.db.query.return_value.filter.return_value.first.side_effect = [ecn, template]

    result = apply_solution_template(service, ecn_id=1, template_id=1)

    assert result["ecn_id"] == 1
    assert result["template_id"] == 1
    assert "applied_at" in result
    service.db.commit.assert_called_once()
    # 模板使用次数应增加
    assert template.usage_count == 11
