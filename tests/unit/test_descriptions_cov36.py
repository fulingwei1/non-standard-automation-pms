# -*- coding: utf-8 -*-
"""描述生成模块单元测试 - 第三十六批"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.lead_priority_scoring.descriptions")

try:
    from app.services.lead_priority_scoring.descriptions import DescriptionsMixin
except ImportError:
    pytestmark = pytest.mark.skip(reason="导入失败")
    DescriptionsMixin = None


def make_lead(completeness=80, **kwargs):
    lead = MagicMock()
    lead.completeness = completeness
    return lead


def make_service_with_scores(**score_map):
    """创建一个拥有 DescriptionsMixin 和 mock 评分方法的服务"""
    class FakeService(DescriptionsMixin):
        def _calculate_customer_importance(self, lead): return score_map.get("customer_importance", 20)
        def _calculate_contract_amount_score(self, lead): return score_map.get("contract_amount_score", 25)
        def _calculate_win_rate_score(self, lead): return score_map.get("win_rate_score", 20)
        def _calculate_urgency_score(self, lead): return score_map.get("urgency_score", 10)
        def _calculate_relationship_score(self, lead): return score_map.get("relationship_score", 10)
        def _calculate_opportunity_relationship(self, opp, cust): return score_map.get("opp_relationship", 10)
    return FakeService()


class TestCustomerLevelDescription:
    def test_a_level(self):
        svc = make_service_with_scores(customer_importance=20)
        desc = svc._get_customer_level_description(make_lead())
        assert "A级" in desc

    def test_b_level(self):
        svc = make_service_with_scores(customer_importance=15)
        desc = svc._get_customer_level_description(make_lead())
        assert "B级" in desc

    def test_unknown_level(self):
        svc = make_service_with_scores(customer_importance=99)
        desc = svc._get_customer_level_description(make_lead())
        assert "未知" in desc


class TestContractAmountDescription:
    def test_large_amount(self):
        svc = make_service_with_scores(contract_amount_score=25)
        desc = svc._get_contract_amount_description(make_lead())
        assert "≥100万" in desc

    def test_small_amount(self):
        svc = make_service_with_scores(contract_amount_score=5)
        desc = svc._get_contract_amount_description(make_lead())
        assert "<10万" in desc


class TestWinRateDescription:
    def test_high_win_rate(self):
        svc = make_service_with_scores(win_rate_score=20)
        desc = svc._get_win_rate_description(make_lead())
        assert "≥80%" in desc


class TestRequirementMaturityDescription:
    def test_high_completeness(self):
        svc = make_service_with_scores()
        desc = svc._get_requirement_maturity_description(make_lead(completeness=90))
        assert "非常明确" in desc

    def test_low_completeness(self):
        svc = make_service_with_scores()
        desc = svc._get_requirement_maturity_description(make_lead(completeness=20))
        assert "不明确" in desc


class TestRelationshipDescription:
    def test_good_relationship(self):
        svc = make_service_with_scores(relationship_score=10)
        desc = svc._get_relationship_description(make_lead())
        assert "老客户" in desc

    def test_new_customer(self):
        svc = make_service_with_scores(relationship_score=2)
        desc = svc._get_relationship_description(make_lead())
        assert "新客户" in desc
