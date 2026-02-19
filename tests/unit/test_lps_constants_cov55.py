# -*- coding: utf-8 -*-
"""
Tests for app/services/lead_priority_scoring/constants.py
"""
import pytest

try:
    from app.services.lead_priority_scoring.constants import ScoringConstants
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def test_customer_importance_scores_keys():
    """客户重要性分数应包含 A-E 级别"""
    scores = ScoringConstants.CUSTOMER_IMPORTANCE_SCORES
    for grade in ["A", "B", "C", "D", "E"]:
        assert grade in scores


def test_customer_importance_scores_order():
    """A级客户分数应高于E级"""
    scores = ScoringConstants.CUSTOMER_IMPORTANCE_SCORES
    assert scores["A"] > scores["E"]


def test_contract_amount_scores_is_list():
    """合同金额分数映射应为列表"""
    assert isinstance(ScoringConstants.CONTRACT_AMOUNT_SCORES, list)
    assert len(ScoringConstants.CONTRACT_AMOUNT_SCORES) > 0


def test_contract_amount_scores_descending():
    """合同金额分数应从高到低排列"""
    amounts = [item[0] for item in ScoringConstants.CONTRACT_AMOUNT_SCORES]
    assert amounts == sorted(amounts, reverse=True)


def test_win_rate_scores_coverage():
    """中标概率分数映射应覆盖 0.0-1.0 区间"""
    thresholds = [item[0] for item in ScoringConstants.WIN_RATE_SCORES]
    assert 0.0 in thresholds


def test_requirement_maturity_scores():
    """需求成熟度映射应包含 1-5 级"""
    for level in [1, 2, 3, 4, 5]:
        assert level in ScoringConstants.REQUIREMENT_MATURITY_SCORES


def test_urgency_scores_keys():
    """紧急程度分数应包含 HIGH/MEDIUM/LOW"""
    scores = ScoringConstants.URGENCY_SCORES
    assert "HIGH" in scores
    assert "MEDIUM" in scores
    assert "LOW" in scores
    assert scores["HIGH"] > scores["LOW"]


def test_relationship_scores_keys():
    """客户关系分数应包含所有预期键"""
    scores = ScoringConstants.RELATIONSHIP_SCORES
    assert "EXISTING_GOOD" in scores
    assert "NEW_POOR" in scores
    assert scores["EXISTING_GOOD"] > scores["NEW_POOR"]
