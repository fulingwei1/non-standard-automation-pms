# -*- coding: utf-8 -*-
"""线索描述生成模块单元测试"""
import pytest
from unittest.mock import MagicMock
from app.services.lead_priority_scoring.descriptions import DescriptionsMixin


class TestDescriptionsMixin:
    def setup_method(self):
        self.mixin = DescriptionsMixin()

    def test_get_requirement_maturity_high(self):
        lead = MagicMock()
        lead.completeness = 85
        assert "非常明确" in self.mixin._get_requirement_maturity_description(lead)

    def test_get_requirement_maturity_medium(self):
        lead = MagicMock()
        lead.completeness = 65
        assert "基本明确" in self.mixin._get_requirement_maturity_description(lead)

    def test_get_requirement_maturity_partial(self):
        lead = MagicMock()
        lead.completeness = 45
        assert "部分明确" in self.mixin._get_requirement_maturity_description(lead)

    def test_get_requirement_maturity_low(self):
        lead = MagicMock()
        lead.completeness = 20
        assert "不明确" in self.mixin._get_requirement_maturity_description(lead)

    def test_get_requirement_maturity_none(self):
        lead = MagicMock()
        lead.completeness = None
        assert "不明确" in self.mixin._get_requirement_maturity_description(lead)

    def test_get_customer_level_description(self):
        self.mixin._calculate_customer_importance = MagicMock(return_value=20)
        lead = MagicMock()
        result = self.mixin._get_customer_level_description(lead)
        assert "A级" in result

    def test_get_contract_amount_description(self):
        self.mixin._calculate_contract_amount_score = MagicMock(return_value=25)
        lead = MagicMock()
        result = self.mixin._get_contract_amount_description(lead)
        assert "100万" in result

    def test_get_win_rate_description(self):
        self.mixin._calculate_win_rate_score = MagicMock(return_value=20)
        lead = MagicMock()
        result = self.mixin._get_win_rate_description(lead)
        assert "80%" in result

    def test_get_urgency_description(self):
        self.mixin._calculate_urgency_score = MagicMock(return_value=10)
        lead = MagicMock()
        result = self.mixin._get_urgency_description(lead)
        assert "紧急" in result

    def test_get_relationship_description(self):
        self.mixin._calculate_relationship_score = MagicMock(return_value=10)
        lead = MagicMock()
        result = self.mixin._get_relationship_description(lead)
        assert "老客户" in result

    def test_get_relationship_description_for_opp(self):
        self.mixin._calculate_opportunity_relationship = MagicMock(return_value=5)
        opp = MagicMock()
        customer = MagicMock()
        result = self.mixin._get_relationship_description_for_opp(opp, customer)
        assert "新客户" in result
