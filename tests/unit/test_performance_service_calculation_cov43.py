# -*- coding: utf-8 -*-
"""
第四十三批覆盖率测试 - app/services/performance_service/calculation.py
"""
import pytest

pytest.importorskip("app.services.performance_service.calculation")

from unittest.mock import MagicMock, patch

from app.services.performance_service.calculation import (
    calculate_final_score,
    calculate_quarterly_score,
    get_score_level,
)
from app.models.performance import EvaluatorTypeEnum


def make_db():
    return MagicMock()


# ── 1. get_score_level 各档次 ─────────────────────────────────────────────────
@pytest.mark.parametrize("score, expected_level", [
    (96, "A+"),
    (92, "A"),
    (87, "B+"),
    (82, "B"),
    (77, "C+"),
    (71, "C"),
    (65, "D"),
])
def test_get_score_level(score, expected_level):
    assert get_score_level(score) == expected_level


# ── 2. calculate_final_score: 无权重配置时使用默认 50:50 ─────────────────────
def test_calculate_final_score_default_weights():
    db = make_db()

    # no weight config
    q_weight = MagicMock()
    q_weight.filter.return_value.order_by.return_value.first.return_value = None

    dept_eval = MagicMock()
    dept_eval.evaluator_type = EvaluatorTypeEnum.DEPT_MANAGER
    dept_eval.score = 80
    dept_eval.project_weight = None
    dept_eval.evaluator_id = 1
    dept_eval.project_id = None
    dept_eval.comment = ""
    dept_eval.evaluated_at = None

    proj_eval = MagicMock()
    proj_eval.evaluator_type = EvaluatorTypeEnum.PROJECT_MANAGER
    proj_eval.score = 90
    proj_eval.project_weight = 50
    proj_eval.evaluator_id = 2
    proj_eval.project_id = 5
    proj_eval.comment = "good"
    proj_eval.evaluated_at = None

    q_evals = MagicMock()
    q_evals.filter.return_value.all.return_value = [dept_eval, proj_eval]

    db.query.side_effect = [q_weight, q_evals]

    result = calculate_final_score(db, summary_id=1, period="2026-01")
    assert result is not None
    assert "final_score" in result
    # 80 * 0.5 + 90 * 0.5 = 85
    assert result["final_score"] == 85.0


# ── 3. calculate_final_score: 无评价记录时返回 None ──────────────────────────
def test_calculate_final_score_no_evaluations():
    db = make_db()

    q_weight = MagicMock()
    q_weight.filter.return_value.order_by.return_value.first.return_value = None

    q_evals = MagicMock()
    q_evals.filter.return_value.all.return_value = []

    db.query.side_effect = [q_weight, q_evals]

    result = calculate_final_score(db, summary_id=2, period="2026-01")
    assert result is None


# ── 4. calculate_final_score: 仅有部门评价时使用其分数 ────────────────────────
def test_calculate_final_score_only_dept():
    db = make_db()

    weight_config = MagicMock()
    weight_config.dept_manager_weight = 60
    weight_config.project_manager_weight = 40

    q_weight = MagicMock()
    q_weight.filter.return_value.order_by.return_value.first.return_value = weight_config

    dept_eval = MagicMock()
    dept_eval.evaluator_type = EvaluatorTypeEnum.DEPT_MANAGER
    dept_eval.score = 88
    dept_eval.project_weight = None
    dept_eval.evaluator_id = 3
    dept_eval.project_id = None
    dept_eval.comment = ""
    dept_eval.evaluated_at = None

    q_evals = MagicMock()
    q_evals.filter.return_value.all.return_value = [dept_eval]

    db.query.side_effect = [q_weight, q_evals]

    result = calculate_final_score(db, summary_id=3, period="2026-02")
    assert result is not None
    # Only dept eval: uses its score directly (100%)
    assert result["final_score"] == 88.0


# ── 5. calculate_quarterly_score: 无总结记录时返回 None ─────────────────────
def test_calculate_quarterly_score_no_summaries():
    db = make_db()
    db.query.return_value.filter.return_value.all.return_value = []

    result = calculate_quarterly_score(db, employee_id=1, end_period="2026-01")
    assert result is None


# ── 6. calculate_quarterly_score: 有评分时计算平均 ───────────────────────────
def test_calculate_quarterly_score_with_data():
    db = make_db()

    summary1 = MagicMock()
    summary1.id = 10
    summary1.period = "2025-11"

    summary2 = MagicMock()
    summary2.id = 11
    summary2.period = "2025-12"

    db.query.return_value.filter.return_value.all.return_value = [summary1, summary2]

    with patch("app.services.performance_service.calculation.calculate_final_score") as mock_calc:
        mock_calc.side_effect = [
            {"final_score": 80.0},
            {"final_score": 90.0},
        ]
        result = calculate_quarterly_score(db, employee_id=1, end_period="2026-01")

    assert result == 85.0
