# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock
from app.services.lead_priority_scoring.lead_scoring import LeadScoringMixin


class FakeService(LeadScoringMixin):
    def __init__(self, db):
        self.db = db

    def _calculate_customer_importance(self, lead): return 15
    def _calculate_contract_amount_score(self, lead): return 20
    def _calculate_win_rate_score(self, lead): return 15
    def _calculate_requirement_maturity_score(self, lead): return 10
    def _calculate_urgency_score(self, lead): return 7
    def _calculate_relationship_score(self, lead): return 8
    def _get_customer_level_description(self, lead): return "A级"
    def _get_contract_amount_description(self, lead): return "100万"
    def _get_win_rate_description(self, lead): return "75%"
    def _get_requirement_maturity_description(self, lead): return "成熟"
    def _get_urgency_description(self, lead): return "紧急"
    def _get_relationship_description(self, lead): return "良好"
    def _determine_priority_level(self, total, urgency): return "HIGH"
    def _determine_importance_level(self, total): return "HIGH"
    def _determine_urgency_level(self, urgency): return "MEDIUM"


class TestLeadScoringMixin:
    def setup_method(self):
        self.db = MagicMock()
        self.service = FakeService(self.db)

    def test_lead_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            self.service.calculate_lead_priority(999)

    def test_calculate_success(self):
        lead = MagicMock()
        lead.id = 1
        lead.lead_code = "L001"
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.service.calculate_lead_priority(1)
        assert result["total_score"] == 75
        assert result["is_key_lead"] is True
        assert result["lead_code"] == "L001"
        assert len(result["scores"]) == 6
