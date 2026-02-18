# -*- coding: utf-8 -*-
"""第二十七批 - lead_scoring 单元测试"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.lead_priority_scoring.lead_scoring")

from app.services.lead_priority_scoring.lead_scoring import LeadScoringMixin


class ConcreteLeadScorer(LeadScoringMixin):
    """具体化混入类用于测试"""

    def __init__(self, db):
        self.db = db

    def _calculate_customer_importance(self, lead):
        return getattr(lead, "_mock_customer_score", 15)

    def _calculate_contract_amount_score(self, lead):
        return getattr(lead, "_mock_amount_score", 20)

    def _calculate_win_rate_score(self, lead):
        return getattr(lead, "_mock_win_score", 15)

    def _calculate_requirement_maturity_score(self, lead):
        return getattr(lead, "_mock_maturity_score", 10)

    def _calculate_urgency_score(self, lead):
        return getattr(lead, "_mock_urgency_score", 8)

    def _calculate_relationship_score(self, lead):
        return getattr(lead, "_mock_relationship_score", 7)

    def _get_customer_level_description(self, lead):
        return "大客户"

    def _get_contract_amount_description(self, lead):
        return "500万以上"

    def _get_win_rate_description(self, lead):
        return "60%以上"

    def _get_requirement_maturity_description(self, lead):
        return "需求明确"

    def _get_urgency_description(self, lead):
        return "较紧急"

    def _get_relationship_description(self, lead):
        return "良好关系"

    def _determine_priority_level(self, total_score, urgency_score):
        if total_score >= 80:
            return "HIGH"
        elif total_score >= 60:
            return "MEDIUM"
        return "LOW"

    def _determine_importance_level(self, total_score):
        if total_score >= 70:
            return "KEY"
        return "NORMAL"

    def _determine_urgency_level(self, urgency_score):
        if urgency_score >= 8:
            return "URGENT"
        return "NORMAL"


def make_lead(**kwargs):
    lead = MagicMock()
    lead.id = kwargs.get("id", 1)
    lead.lead_code = kwargs.get("lead_code", "LEAD-2024-001")
    lead._mock_customer_score = kwargs.get("customer_score", 15)
    lead._mock_amount_score = kwargs.get("amount_score", 20)
    lead._mock_win_score = kwargs.get("win_score", 15)
    lead._mock_maturity_score = kwargs.get("maturity_score", 10)
    lead._mock_urgency_score = kwargs.get("urgency_score", 8)
    lead._mock_relationship_score = kwargs.get("relationship_score", 7)
    return lead


class TestCalculateLeadPriority:
    def setup_method(self):
        self.db = MagicMock()
        self.scorer = ConcreteLeadScorer(self.db)

    def test_lead_not_found_raises(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            self.scorer.calculate_lead_priority(999)

    def test_returns_correct_structure(self):
        lead = make_lead()
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.scorer.calculate_lead_priority(1)

        assert "lead_id" in result
        assert "lead_code" in result
        assert "total_score" in result
        assert "max_score" in result
        assert "scores" in result
        assert "is_key_lead" in result
        assert "priority_level" in result
        assert "importance_level" in result
        assert "urgency_level" in result

    def test_max_score_is_100(self):
        lead = make_lead()
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.scorer.calculate_lead_priority(1)
        assert result["max_score"] == 100

    def test_total_score_sums_dimensions(self):
        lead = make_lead(
            customer_score=15,
            amount_score=20,
            win_score=15,
            maturity_score=10,
            urgency_score=8,
            relationship_score=7
        )
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.scorer.calculate_lead_priority(1)
        assert result["total_score"] == 75

    def test_key_lead_flag_true_above_70(self):
        lead = make_lead(
            customer_score=15,
            amount_score=20,
            win_score=15,
            maturity_score=10,
            urgency_score=8,
            relationship_score=7
        )
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.scorer.calculate_lead_priority(1)
        assert result["is_key_lead"] is True  # total = 75 >= 70

    def test_key_lead_flag_false_below_70(self):
        lead = make_lead(
            customer_score=5,
            amount_score=10,
            win_score=10,
            maturity_score=5,
            urgency_score=5,
            relationship_score=5
        )
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.scorer.calculate_lead_priority(1)
        assert result["is_key_lead"] is False  # total = 40 < 70

    def test_scores_dict_has_six_dimensions(self):
        lead = make_lead()
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.scorer.calculate_lead_priority(1)
        assert len(result["scores"]) == 6

    def test_each_dimension_has_score_max_description(self):
        lead = make_lead()
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.scorer.calculate_lead_priority(1)

        for key, dim in result["scores"].items():
            assert "score" in dim
            assert "max" in dim
            assert "description" in dim

    def test_customer_importance_max_is_20(self):
        lead = make_lead()
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.scorer.calculate_lead_priority(1)
        assert result["scores"]["customer_importance"]["max"] == 20

    def test_contract_amount_max_is_25(self):
        lead = make_lead()
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.scorer.calculate_lead_priority(1)
        assert result["scores"]["contract_amount"]["max"] == 25

    def test_win_rate_max_is_20(self):
        lead = make_lead()
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.scorer.calculate_lead_priority(1)
        assert result["scores"]["win_rate"]["max"] == 20

    def test_urgency_max_is_10(self):
        lead = make_lead()
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.scorer.calculate_lead_priority(1)
        assert result["scores"]["urgency"]["max"] == 10

    def test_relationship_max_is_10(self):
        lead = make_lead()
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.scorer.calculate_lead_priority(1)
        assert result["scores"]["relationship"]["max"] == 10

    def test_priority_level_high(self):
        lead = make_lead(
            customer_score=20,
            amount_score=25,
            win_score=20,
            maturity_score=15,
            urgency_score=10,
            relationship_score=10
        )
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.scorer.calculate_lead_priority(1)
        assert result["priority_level"] == "HIGH"

    def test_urgency_level_urgent(self):
        lead = make_lead(urgency_score=10)
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.scorer.calculate_lead_priority(1)
        assert result["urgency_level"] == "URGENT"

    def test_lead_code_in_result(self):
        lead = make_lead(lead_code="LEAD-2024-XYZ")
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.scorer.calculate_lead_priority(1)
        assert result["lead_code"] == "LEAD-2024-XYZ"

    def test_lead_id_in_result(self):
        lead = make_lead(id=42)
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.scorer.calculate_lead_priority(42)
        assert result["lead_id"] == 42
