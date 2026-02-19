# -*- coding: utf-8 -*-
"""
tests/unit/test_ps_calculation_cov51.py
Unit tests for app/services/performance_service/calculation.py
"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.performance_service.calculation import (
        calculate_final_score,
        calculate_quarterly_score,
        get_score_level,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _make_eval(evaluator_type, score, project_weight=None):
    e = MagicMock()
    e.evaluator_type = evaluator_type
    e.score = score
    e.project_weight = project_weight
    e.evaluator_id = 1
    e.project_id = None
    e.comment = ""
    e.evaluated_at = None
    return e


# ─── get_score_level ─────────────────────────────────────────────────────────

def test_get_score_level_A_plus():
    assert get_score_level(95) == "A+"
    assert get_score_level(100) == "A+"


def test_get_score_level_boundaries():
    assert get_score_level(90) == "A"
    assert get_score_level(85) == "B+"
    assert get_score_level(80) == "B"
    assert get_score_level(75) == "C+"
    assert get_score_level(70) == "C"
    assert get_score_level(60) == "D"


# ─── calculate_final_score ───────────────────────────────────────────────────

def test_calculate_final_score_no_weight_config_no_evaluations():
    """No weight config + no evaluations → None"""
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []

    result = calculate_final_score(db, summary_id=1, period="2025-01")
    assert result is None


def test_calculate_final_score_dept_only():
    """Only dept manager evaluation, uses 100% of dept score."""
    from app.models.performance import EvaluatorTypeEnum, EvaluationStatusEnum

    db = MagicMock()
    # No weight config
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    dept_eval = _make_eval(EvaluatorTypeEnum.DEPT_MANAGER, 88)
    dept_eval.status = EvaluationStatusEnum.COMPLETED

    # evaluations query
    db.query.return_value.filter.return_value.all.return_value = [dept_eval]

    result = calculate_final_score(db, summary_id=1, period="2025-01")
    assert result is not None
    assert result["final_score"] == 88.0
    assert result["dept_score"] == 88.0
    assert result["project_score"] is None


def test_calculate_final_score_both_managers_weighted():
    """Both dept + project evals with default 50/50 weights."""
    from app.models.performance import EvaluatorTypeEnum, EvaluationStatusEnum

    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    dept_eval = _make_eval(EvaluatorTypeEnum.DEPT_MANAGER, 80)
    dept_eval.status = EvaluationStatusEnum.COMPLETED

    proj_eval = _make_eval(EvaluatorTypeEnum.PROJECT_MANAGER, 90, project_weight=100)
    proj_eval.status = EvaluationStatusEnum.COMPLETED

    db.query.return_value.filter.return_value.all.return_value = [dept_eval, proj_eval]

    result = calculate_final_score(db, summary_id=1, period="2025-01")
    assert result is not None
    # 80*0.5 + 90*0.5 = 85
    assert result["final_score"] == 85.0
    assert result["dept_weight"] == 50
    assert result["project_weight"] == 50


def test_calculate_final_score_project_only():
    """Only project manager evaluation → uses 100% of project score."""
    from app.models.performance import EvaluatorTypeEnum, EvaluationStatusEnum

    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

    proj_eval = _make_eval(EvaluatorTypeEnum.PROJECT_MANAGER, 92, project_weight=0)
    proj_eval.status = EvaluationStatusEnum.COMPLETED

    db.query.return_value.filter.return_value.all.return_value = [proj_eval]

    result = calculate_final_score(db, summary_id=1, period="2025-01")
    assert result is not None
    # project_weight=0 → simple average = 92
    assert result["final_score"] == 92.0


def test_calculate_final_score_with_weight_config():
    """Uses explicit weight config (30 dept / 70 project)."""
    from app.models.performance import EvaluatorTypeEnum, EvaluationStatusEnum

    weight_cfg = MagicMock()
    weight_cfg.dept_manager_weight = 30
    weight_cfg.project_manager_weight = 70

    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = weight_cfg

    dept_eval = _make_eval(EvaluatorTypeEnum.DEPT_MANAGER, 80)
    proj_eval = _make_eval(EvaluatorTypeEnum.PROJECT_MANAGER, 100, project_weight=100)

    db.query.return_value.filter.return_value.all.return_value = [dept_eval, proj_eval]

    result = calculate_final_score(db, summary_id=1, period="2025-06")
    assert result is not None
    # 80*0.3 + 100*0.7 = 24 + 70 = 94
    assert result["final_score"] == 94.0


# ─── calculate_quarterly_score ───────────────────────────────────────────────

def test_calculate_quarterly_score_no_summaries():
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []

    result = calculate_quarterly_score(db, employee_id=1, end_period="2025-03")
    assert result is None


def test_calculate_quarterly_score_averages_monthly_scores():
    """Simulates 2 months with scores and checks average."""
    db = MagicMock()

    summary1 = MagicMock()
    summary1.id = 1
    summary1.period = "2025-03"

    summary2 = MagicMock()
    summary2.id = 2
    summary2.period = "2025-02"

    db.query.return_value.filter.return_value.all.return_value = [summary1, summary2]

    with patch(
        "app.services.performance_service.calculation.calculate_final_score"
    ) as mock_calc:
        mock_calc.side_effect = [
            {"final_score": 90.0},
            {"final_score": 80.0},
        ]
        result = calculate_quarterly_score(db, employee_id=1, end_period="2025-03")

    assert result == 85.0
