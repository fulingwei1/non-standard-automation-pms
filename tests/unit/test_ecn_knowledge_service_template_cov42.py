# -*- coding: utf-8 -*-
"""第四十二批：ecn_knowledge_service/template.py 单元测试"""
import pytest

pytest.importorskip("app.services.ecn_knowledge_service.template")

from unittest.mock import MagicMock, patch
from app.services.ecn_knowledge_service.template import (
    recommend_solutions,
    create_solution_template,
    apply_solution_template,
    _calculate_template_score,
    _generate_template_code,
)


def make_service():
    return MagicMock()


def make_ecn(ecn_type="DESIGN", root_cause_category="QUALITY"):
    ecn = MagicMock()
    ecn.id = 1
    ecn.ecn_type = ecn_type
    ecn.root_cause_category = root_cause_category
    ecn.ecn_title = "测试ECN"
    ecn.solution = ""
    ecn.cost_impact = None
    ecn.schedule_impact_days = None
    ecn.change_description = ""
    return ecn


def make_template(ecn_type="DESIGN", root_cause="QUALITY", keywords=None,
                  success_rate=80, usage_count=5, is_active=True):
    t = MagicMock()
    t.ecn_type = ecn_type
    t.root_cause_category = root_cause
    t.keywords = keywords or []
    t.success_rate = success_rate
    t.usage_count = usage_count
    t.is_active = is_active
    t.id = 1
    t.template_code = "T001"
    t.template_name = "模板A"
    t.template_category = "DESIGN"
    t.solution_description = "解决方案"
    t.solution_steps = ["步骤1"]
    t.estimated_cost = 100
    t.estimated_days = 5
    return t


# ------------------------------------------------------------------ tests ---

def test_recommend_solutions_ecn_not_found():
    svc = make_service()
    svc.db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError, match="不存在"):
        recommend_solutions(svc, ecn_id=999)


def test_recommend_solutions_empty_templates():
    svc = make_service()
    ecn = make_ecn()
    q = MagicMock()
    q.filter.return_value.first.return_value = ecn
    q.filter.return_value.all.return_value = []
    svc.db.query.return_value = q
    result = recommend_solutions(svc, ecn_id=1)
    assert result == []


def test_calculate_template_score_type_match():
    svc = make_service()
    svc.db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
    ecn = make_ecn(ecn_type="DESIGN")
    tmpl = make_template(ecn_type="DESIGN")
    score = _calculate_template_score(svc, ecn, tmpl)
    assert score >= 30.0


def test_calculate_template_score_type_mismatch():
    svc = make_service()
    svc.db.query.return_value.filter.return_value.limit.return_value.all.return_value = []
    ecn = make_ecn(ecn_type="DESIGN", root_cause_category="QUALITY")
    # Different type AND different root cause AND no keywords AND zero success_rate AND zero usage
    tmpl = make_template(ecn_type="PROCESS", root_cause="DESIGN_ERROR",
                         keywords=[], success_rate=0, usage_count=0)
    score = _calculate_template_score(svc, ecn, tmpl)
    assert score == 0.0


def test_create_solution_template_ecn_not_found():
    svc = make_service()
    svc.db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError):
        create_solution_template(svc, ecn_id=999, template_data={}, created_by=1)


def test_apply_solution_template_success():
    svc = make_service()
    ecn = make_ecn()
    tmpl = make_template()

    call_count = [0]
    def query_router(*args):
        call_count[0] += 1
        q = MagicMock()
        if call_count[0] == 1:
            q.filter.return_value.first.return_value = ecn
        else:
            q.filter.return_value.first.return_value = tmpl
        return q

    svc.db.query.side_effect = query_router
    result = apply_solution_template(svc, ecn_id=1, template_id=1)
    assert result["ecn_id"] == 1
    assert result["template_id"] == 1


def test_generate_template_code_format():
    ecn = make_ecn()
    code = _generate_template_code(ecn)
    assert code.startswith("ECN-SOL-")
    assert "0001" in code
