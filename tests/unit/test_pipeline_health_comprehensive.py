# -*- coding: utf-8 -*-
"""PipelineHealthService 综合测试"""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.pipeline_health_service import PipelineHealthService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def svc(mock_db):
    return PipelineHealthService(mock_db)


def _make_lead(**kwargs):
    lead = MagicMock()
    lead.id = kwargs.get("id", 1)
    lead.lead_code = kwargs.get("lead_code", "L001")
    lead.status = kwargs.get("status", "NEW")
    lead.next_action_at = kwargs.get("next_action_at")
    lead.created_at = kwargs.get("created_at", datetime.now())
    lead.follow_ups = kwargs.get("follow_ups", [])
    return lead


def _make_opportunity(**kwargs):
    opp = MagicMock()
    opp.id = kwargs.get("id", 1)
    opp.opp_code = kwargs.get("opp_code", "O001")
    opp.stage = kwargs.get("stage", "DISCOVERY")
    opp.updated_at = kwargs.get("updated_at", datetime.now())
    opp.created_at = kwargs.get("created_at", datetime.now())
    opp.gate_status = kwargs.get("gate_status", "PENDING")
    return opp


def _make_quote(**kwargs):
    q = MagicMock()
    q.id = kwargs.get("id", 1)
    q.quote_code = kwargs.get("quote_code", "Q001")
    q.status = kwargs.get("status", "DRAFT")
    q.created_at = kwargs.get("created_at", datetime.now())
    q.valid_until = kwargs.get("valid_until")
    return q


def _make_contract(**kwargs):
    c = MagicMock()
    c.id = kwargs.get("id", 1)
    c.contract_code = kwargs.get("contract_code", "C001")
    c.status = kwargs.get("status", "ACTIVE")
    c.project_id = kwargs.get("project_id")
    return c


def _make_invoice(**kwargs):
    inv = MagicMock()
    inv.id = kwargs.get("id", 1)
    inv.invoice_code = kwargs.get("invoice_code", "INV001")
    inv.total_amount = kwargs.get("total_amount", 10000)
    inv.amount = kwargs.get("amount", 10000)
    inv.paid_amount = kwargs.get("paid_amount", 0)
    inv.due_date = kwargs.get("due_date", date.today())
    inv.issue_date = kwargs.get("issue_date", date.today())
    return inv


class TestCalculateLeadHealth:
    def test_not_found(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError):
            svc.calculate_lead_health(999)

    def test_converted(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = _make_lead(status="CONVERTED")
        result = svc.calculate_lead_health(1)
        assert result["health_status"] == "H4"

    def test_invalid(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = _make_lead(status="INVALID")
        result = svc.calculate_lead_health(1)
        assert result["health_status"] == "H4"

    def test_healthy_recent(self, svc, mock_db):
        lead = _make_lead(created_at=datetime.now())
        mock_db.query.return_value.filter.return_value.first.return_value = lead
        result = svc.calculate_lead_health(1)
        assert result["health_status"] == "H1"
        assert result["health_score"] == 100

    def test_warning_14_days(self, svc, mock_db):
        lead = _make_lead(created_at=datetime.now() - timedelta(days=15))
        lead.next_action_at = None
        mock_db.query.return_value.filter.return_value.first.return_value = lead
        result = svc.calculate_lead_health(1)
        assert result["health_status"] == "H2"

    def test_critical_30_days(self, svc, mock_db):
        lead = _make_lead(created_at=datetime.now() - timedelta(days=35))
        lead.next_action_at = None
        mock_db.query.return_value.filter.return_value.first.return_value = lead
        result = svc.calculate_lead_health(1)
        assert result["health_status"] == "H3"

    def test_with_follow_ups(self, svc, mock_db):
        fu = MagicMock()
        fu.created_at = datetime.now() - timedelta(days=5)
        lead = _make_lead(created_at=datetime.now() - timedelta(days=60), follow_ups=[fu])
        mock_db.query.return_value.filter.return_value.first.return_value = lead
        result = svc.calculate_lead_health(1)
        assert result["health_score"] == 100

    def test_with_next_action(self, svc, mock_db):
        lead = _make_lead(next_action_at=datetime.now() - timedelta(days=2))
        mock_db.query.return_value.filter.return_value.first.return_value = lead
        result = svc.calculate_lead_health(1)
        assert result["health_status"] == "H1"


class TestCalculateOpportunityHealth:
    def test_not_found(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError):
            svc.calculate_opportunity_health(999)

    def test_won(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = _make_opportunity(stage="WON")
        result = svc.calculate_opportunity_health(1)
        assert result["health_status"] == "H4"

    def test_lost(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = _make_opportunity(stage="LOST")
        result = svc.calculate_opportunity_health(1)
        assert result["health_status"] == "H4"

    def test_healthy(self, svc, mock_db):
        opp = _make_opportunity(updated_at=datetime.now())
        mock_db.query.return_value.filter.return_value.first.return_value = opp
        result = svc.calculate_opportunity_health(1)
        assert result["health_status"] == "H1"

    def test_warning(self, svc, mock_db):
        opp = _make_opportunity(updated_at=datetime.now() - timedelta(days=35))
        mock_db.query.return_value.filter.return_value.first.return_value = opp
        result = svc.calculate_opportunity_health(1)
        assert result["health_status"] == "H2"

    def test_critical(self, svc, mock_db):
        opp = _make_opportunity(updated_at=datetime.now() - timedelta(days=65))
        mock_db.query.return_value.filter.return_value.first.return_value = opp
        result = svc.calculate_opportunity_health(1)
        assert result["health_status"] == "H3"

    def test_gate_rejected(self, svc, mock_db):
        opp = _make_opportunity(gate_status="REJECTED", updated_at=datetime.now())
        mock_db.query.return_value.filter.return_value.first.return_value = opp
        result = svc.calculate_opportunity_health(1)
        assert result["health_status"] == "H3"


class TestCalculateQuoteHealth:
    def test_not_found(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError):
            svc.calculate_quote_health(999)

    def test_approved(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = _make_quote(status="APPROVED")
        result = svc.calculate_quote_health(1)
        assert result["health_status"] == "H4"

    def test_rejected(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = _make_quote(status="REJECTED")
        result = svc.calculate_quote_health(1)
        assert result["health_status"] == "H4"

    def test_healthy(self, svc, mock_db):
        q = _make_quote(created_at=datetime.now())
        mock_db.query.return_value.filter.return_value.first.return_value = q
        result = svc.calculate_quote_health(1)
        assert result["health_status"] == "H1"

    def test_expired(self, svc, mock_db):
        q = _make_quote(valid_until=date.today() - timedelta(days=10))
        mock_db.query.return_value.filter.return_value.first.return_value = q
        result = svc.calculate_quote_health(1)
        assert "报价已过期" in result["risk_factors"]


class TestCalculatePaymentHealth:
    def test_not_found(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError):
            svc.calculate_payment_health(999)

    def test_fully_paid(self, svc, mock_db):
        inv = _make_invoice(total_amount=10000, paid_amount=10000)
        mock_db.query.return_value.filter.return_value.first.return_value = inv
        result = svc.calculate_payment_health(1)
        assert result["health_status"] == "H4"

    def test_not_overdue(self, svc, mock_db):
        inv = _make_invoice(due_date=date.today() + timedelta(days=10), paid_amount=0)
        mock_db.query.return_value.filter.return_value.first.return_value = inv
        result = svc.calculate_payment_health(1)
        assert result["health_status"] == "H1"

    def test_slightly_overdue(self, svc, mock_db):
        inv = _make_invoice(due_date=date.today() - timedelta(days=5), paid_amount=0)
        mock_db.query.return_value.filter.return_value.first.return_value = inv
        result = svc.calculate_payment_health(1)
        assert result["health_status"] == "H2"

    def test_severely_overdue(self, svc, mock_db):
        inv = _make_invoice(due_date=date.today() - timedelta(days=35), paid_amount=0)
        mock_db.query.return_value.filter.return_value.first.return_value = inv
        result = svc.calculate_payment_health(1)
        assert result["health_status"] == "H3"


class TestCalculatePipelineHealth:
    def test_empty(self, svc):
        result = svc.calculate_pipeline_health()
        assert result == {}

    def test_with_lead(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = _make_lead()
        result = svc.calculate_pipeline_health(lead_id=1)
        assert "lead" in result
        assert "overall" in result

    def test_with_multiple(self, svc, mock_db):
        lead = _make_lead()
        opp = _make_opportunity()
        mock_db.query.return_value.filter.return_value.first.return_value = lead
        with patch.object(svc, 'calculate_lead_health', return_value={"health_score": 100}):
            with patch.object(svc, 'calculate_opportunity_health', return_value={"health_score": 50}):
                result = svc.calculate_pipeline_health(lead_id=1, opportunity_id=1)
                assert result["overall"]["health_score"] == 50

    def test_error_handling(self, svc, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        # Should not raise even if individual calculations fail
        result = svc.calculate_pipeline_health(lead_id=999, opportunity_id=999)
        # Errors are caught, so result might be empty or have partial data

    def test_overall_h3(self, svc):
        with patch.object(svc, 'calculate_lead_health', return_value={"health_score": 20}):
            result = svc.calculate_pipeline_health(lead_id=1)
            assert result["overall"]["health_status"] == "H3"

    def test_overall_h2(self, svc):
        with patch.object(svc, 'calculate_lead_health', return_value={"health_score": 50}):
            result = svc.calculate_pipeline_health(lead_id=1)
            assert result["overall"]["health_status"] == "H2"


class TestConstants:
    def test_thresholds_exist(self):
        keys = ["LEAD", "OPPORTUNITY", "QUOTE", "CONTRACT", "PAYMENT"]
        for k in keys:
            assert k in PipelineHealthService.HEALTH_THRESHOLDS
            assert "H1" in PipelineHealthService.HEALTH_THRESHOLDS[k]
            assert "H2" in PipelineHealthService.HEALTH_THRESHOLDS[k]
            assert "H3" in PipelineHealthService.HEALTH_THRESHOLDS[k]
