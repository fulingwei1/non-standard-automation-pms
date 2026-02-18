# -*- coding: utf-8 -*-
"""第二十七批 - information_gap_analysis_service 单元测试"""

import pytest
from datetime import date
from unittest.mock import MagicMock

pytest.importorskip("app.services.information_gap_analysis_service")

from app.services.information_gap_analysis_service import InformationGapAnalysisService


def make_db():
    return MagicMock()


def make_lead(**kwargs):
    lead = MagicMock()
    lead.id = kwargs.get("id", 1)
    lead.customer_name = kwargs.get("customer_name", "测试客户")
    lead.contact_name = kwargs.get("contact_name", "联系人")
    lead.contact_phone = kwargs.get("contact_phone", "13800000000")
    lead.demand_summary = kwargs.get("demand_summary", "需求摘要内容")
    lead.source = kwargs.get("source", "官网")
    lead.industry = kwargs.get("industry", "制造业")
    lead.status = kwargs.get("status", "OPEN")
    return lead


def make_opportunity(**kwargs):
    opp = MagicMock()
    opp.id = kwargs.get("id", 1)
    opp.opp_name = kwargs.get("opp_name", "测试商机")
    opp.est_amount = kwargs.get("est_amount", 500000)
    opp.budget_range = kwargs.get("budget_range", "50-100万")
    opp.delivery_window = kwargs.get("delivery_window", "2024Q3")
    opp.decision_chain = kwargs.get("decision_chain", "总经理决策")
    opp.acceptance_basis = kwargs.get("acceptance_basis", "验收标准说明")
    return opp


def make_quote(**kwargs):
    quote = MagicMock()
    quote.id = kwargs.get("id", 1)
    quote.total_amount = kwargs.get("total_amount", 100000)
    quote.valid_until = kwargs.get("valid_until", date(2024, 12, 31))
    quote.items = kwargs.get("items", [MagicMock(), MagicMock()])
    return quote


class TestGetQualityLevel:
    def setup_method(self):
        db = make_db()
        self.svc = InformationGapAnalysisService(db)

    def test_high_score(self):
        assert self.svc._get_quality_level(90) == "HIGH"

    def test_medium_score(self):
        assert self.svc._get_quality_level(70) == "MEDIUM"

    def test_low_score(self):
        assert self.svc._get_quality_level(50) == "LOW"

    def test_boundary_80_is_high(self):
        assert self.svc._get_quality_level(80) == "HIGH"

    def test_boundary_60_is_medium(self):
        assert self.svc._get_quality_level(60) == "MEDIUM"

    def test_boundary_59_is_low(self):
        assert self.svc._get_quality_level(59) == "LOW"


class TestAnalyzeLeadMissing:
    def setup_method(self):
        db = make_db()
        self.svc = InformationGapAnalysisService(db)

    def test_complete_lead_has_100_score(self):
        lead = make_lead()
        missing, score = self.svc._analyze_lead_missing(lead)
        assert score == 100
        assert missing == []

    def test_missing_customer_name_deducts_10(self):
        lead = make_lead(customer_name=None)
        missing, score = self.svc._analyze_lead_missing(lead)
        assert "customer_name" in missing
        assert score == 90

    def test_missing_contact_phone_deducts_10(self):
        lead = make_lead(contact_phone=None)
        missing, score = self.svc._analyze_lead_missing(lead)
        assert "contact_phone" in missing
        assert score == 90

    def test_missing_demand_summary_deducts_15(self):
        lead = make_lead(demand_summary=None)
        missing, score = self.svc._analyze_lead_missing(lead)
        assert "demand_summary" in missing
        assert score == 85

    def test_empty_string_counts_as_missing(self):
        lead = make_lead(customer_name="   ")
        missing, score = self.svc._analyze_lead_missing(lead)
        assert "customer_name" in missing

    def test_all_missing_score_not_below_zero(self):
        lead = make_lead(
            customer_name=None,
            contact_name=None,
            contact_phone=None,
            demand_summary=None,
            source=None,
            industry=None
        )
        missing, score = self.svc._analyze_lead_missing(lead)
        assert score >= 0


class TestAnalyzeOpportunityMissing:
    def setup_method(self):
        db = make_db()
        self.svc = InformationGapAnalysisService(db)

    def test_complete_opportunity_100_score(self):
        opp = make_opportunity()
        missing, score = self.svc._analyze_opportunity_missing(opp)
        assert score == 100
        assert missing == []

    def test_missing_est_amount_deducts_15(self):
        opp = make_opportunity(est_amount=None)
        missing, score = self.svc._analyze_opportunity_missing(opp)
        assert "est_amount" in missing
        assert score == 85

    def test_missing_opp_name_deducts_10(self):
        opp = make_opportunity(opp_name=None)
        missing, score = self.svc._analyze_opportunity_missing(opp)
        assert "opp_name" in missing
        assert score == 90

    def test_empty_opp_name_counts_missing(self):
        opp = make_opportunity(opp_name="")
        missing, score = self.svc._analyze_opportunity_missing(opp)
        assert "opp_name" in missing


class TestAnalyzeQuoteMissing:
    def setup_method(self):
        db = make_db()
        self.svc = InformationGapAnalysisService(db)

    def test_complete_quote_100_score(self):
        quote = make_quote()
        missing, score = self.svc._analyze_quote_missing(quote)
        assert score == 100

    def test_no_items_deducts_20(self):
        quote = make_quote(items=[])
        missing, score = self.svc._analyze_quote_missing(quote)
        assert "quote_items" in missing
        assert score == 80

    def test_no_total_amount_deducts_15(self):
        quote = make_quote(total_amount=0)
        missing, score = self.svc._analyze_quote_missing(quote)
        assert "total_amount" in missing
        assert score == 85

    def test_no_valid_until_deducts_10(self):
        quote = make_quote(valid_until=None)
        missing, score = self.svc._analyze_quote_missing(quote)
        assert "valid_until" in missing
        assert score == 90


class TestAnalyzeMissingSingle:
    def setup_method(self):
        self.db = make_db()
        self.svc = InformationGapAnalysisService(self.db)

    def test_lead_single_entity(self):
        lead = make_lead()
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.svc.analyze_missing("LEAD", 1)
        assert result["entity_type"] == "LEAD"
        assert result["entity_id"] == 1
        assert "missing_fields" in result
        assert "completeness_score" in result
        assert "quality_level" in result

    def test_opportunity_single_entity(self):
        opp = make_opportunity()
        self.db.query.return_value.filter.return_value.first.return_value = opp
        result = self.svc.analyze_missing("OPPORTUNITY", 1)
        assert result["entity_type"] == "OPPORTUNITY"

    def test_quote_single_entity(self):
        quote = make_quote()
        self.db.query.return_value.filter.return_value.first.return_value = quote
        result = self.svc.analyze_missing("QUOTE", 1)
        assert result["entity_type"] == "QUOTE"

    def test_entity_not_found_returns_default(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.svc.analyze_missing("LEAD", 999)
        assert result["completeness_score"] == 100  # default value returned when entity not found


class TestGetQualityScore:
    def setup_method(self):
        self.db = make_db()
        self.svc = InformationGapAnalysisService(self.db)

    def test_quality_score_structure(self):
        lead = make_lead()
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.svc.get_quality_score("LEAD", 1)
        assert "entity_type" in result
        assert "entity_id" in result
        assert "quality_score" in result
        assert "quality_level" in result
        assert "missing_fields" in result
        assert "recommendations" in result

    def test_recommendations_for_missing_fields(self):
        lead = make_lead(customer_name=None)
        self.db.query.return_value.filter.return_value.first.return_value = lead
        result = self.svc.get_quality_score("LEAD", 1)
        assert len(result["recommendations"]) > 0


class TestGetRecommendations:
    def setup_method(self):
        db = make_db()
        self.svc = InformationGapAnalysisService(db)

    def test_known_field_recommendation(self):
        recs = self.svc._get_recommendations(["customer_name"])
        assert len(recs) > 0
        assert "客户名称" in recs[0]

    def test_unknown_field_no_recommendation(self):
        recs = self.svc._get_recommendations(["unknown_field"])
        assert len(recs) == 0

    def test_multiple_fields_multiple_recs(self):
        recs = self.svc._get_recommendations(["customer_name", "contact_name", "est_amount"])
        assert len(recs) == 3

    def test_empty_fields_empty_recs(self):
        recs = self.svc._get_recommendations([])
        assert recs == []


class TestAnalyzeBatchMissing:
    def setup_method(self):
        db = make_db()
        self.svc = InformationGapAnalysisService(db)

    def test_batch_lead_analysis(self):
        leads = [
            make_lead(),
            make_lead(customer_name=None),
            make_lead(customer_name=None, contact_phone=None, demand_summary=None)
        ]
        result = self.svc._analyze_batch_missing("LEAD", leads)
        assert result["entity_type"] == "LEAD"
        assert result["total"] == 3
        assert "quality_distribution" in result
        assert "common_missing_fields" in result

    def test_quality_distribution_sums_to_total(self):
        leads = [make_lead() for _ in range(5)]
        result = self.svc._analyze_batch_missing("LEAD", leads)
        dist = result["quality_distribution"]
        assert dist["high"] + dist["medium"] + dist["low"] == 5

    def test_common_missing_fields_has_percentages(self):
        leads = [make_lead(customer_name=None) for _ in range(3)]
        result = self.svc._analyze_batch_missing("LEAD", leads)
        if result["common_missing_fields"]:
            for item in result["common_missing_fields"]:
                assert "field" in item
                assert "count" in item
                assert "percentage" in item


class TestAnalyzeImpact:
    def setup_method(self):
        self.db = make_db()
        self.svc = InformationGapAnalysisService(self.db)

    def test_impact_analysis_structure(self):
        leads = [make_lead(), make_lead(demand_summary=None)]
        quotes = [make_quote(), make_quote(items=[])]
        self.db.query.return_value.all.side_effect = [leads, quotes]

        result = self.svc.analyze_impact()
        assert "analysis_period" in result
        assert "lead_quality_impact" in result
        assert "quote_quality_impact" in result

    def test_impact_lead_quality_fields(self):
        leads = [make_lead()]
        quotes = []
        self.db.query.return_value.all.side_effect = [leads, quotes]

        result = self.svc.analyze_impact()
        lqi = result["lead_quality_impact"]
        assert "high_quality_count" in lqi
        assert "low_quality_count" in lqi
        assert "high_quality_conversion_rate" in lqi
        assert "low_quality_conversion_rate" in lqi

    def test_impact_with_date_range(self):
        leads = []
        quotes = []
        self.db.query.return_value.all.side_effect = [leads, quotes]

        result = self.svc.analyze_impact(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 30)
        )
        assert result["analysis_period"]["start_date"] == "2024-01-01"
        assert result["analysis_period"]["end_date"] == "2024-06-30"
