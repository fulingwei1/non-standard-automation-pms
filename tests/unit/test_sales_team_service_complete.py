# -*- coding: utf-8 -*-
"""
Tests for sales_team_service service
Covers: app/services/sales_team_service.py
Coverage Target: 0% → 70%+
File Size: 200 lines
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.services.sales_team_service import SalesTeamService


@pytest.fixture
def sales_team_service(db_session: Session):
    """Create sales team service instance."""
    return SalesTeamService(db_session)


@pytest.fixture
def mock_user(db_session: Session):
    """Create mock user."""
    user = MagicMock()
    user.id = 1
    user.username = "test_user"
    return user


@pytest.fixture
def mock_period_start():
    """Return period start date for this month."""
    today = date.today()
    return date(today.year, today.month, 1)


@pytest.fixture
def mock_period_end():
    """Return period end date for this month."""
    today = date.today()
    if today.month == 12:
        return date(today.year, today.month, 31)
    else:
        # Get last day of month
        import calendar

        _, last_day = calendar.monthrange(today.year, today.month)
        return date(today.year, today.month, last_day)


class TestCalculateTargetPerformance:
    """Test suite for calculate_target_performance."""

    def test_calculate_target_performance_lead_count_basic(
        self,
        sales_team_service: SalesTeamService,
        mock_user,
        mock_period_start,
        mock_period_end,
    ):
        """Test target performance calculation with basic lead count."""
        target = MagicMock()
        target.target_type = "LEAD_COUNT"
        target.target_value = Decimal("10")
        target.start_date = mock_period_start
        target.end_date = mock_period_end
        target.user_id = mock_user.id

        result = sales_team_service.calculate_target_performance(target)

        assert result == (Decimal("10"), 100.0)

    def test_calculate_target_performance_lead_count_with_period_overlap(
        self,
        sales_team_service: SalesTeamService,
        mock_user,
        mock_period_start,
        mock_period_end,
    ):
        """Test target performance when period overlaps target period."""
        target = MagicMock()
        target.target_type = "LEAD_COUNT"
        target.target_value = Decimal("10")
        target.start_date = mock_period_start - timedelta(days=5)  # Before period
        target.end_date = mock_period_end + timedelta(days=5)  # After period
        target.user_id = mock_user.id

        # Mock period queries to return leads in target period

        # Create leads in target period
        leads = []
        for i in range(int(target.target_value)):
            lead = MagicMock()
            lead.created_at = datetime.combine(
                mock_period_start, datetime.min.time()
            ) + timedelta(days=i)
            leads.append(lead)

        # Mock query to return filtered leads
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value = leads
        mock_query.filter.return_value.all.return_value = leads

        with patch.object(sales_team_service.db.query, return_value=mock_query):
            result = sales_team_service.calculate_target_performance(target)

        # Should count only leads in target period
        assert result == (Decimal("10"), 100.0)

    def test_calculate_target_performance_opportunity_count_basic(
        self,
        sales_team_service: SalesTeamService,
        mock_user,
        mock_period_start,
        mock_period_end,
    ):
        """Test target performance with basic opportunity count."""
        target = MagicMock()
        target.target_type = "OPPORTUNITY_COUNT"
        target.target_value = Decimal("5")
        target.start_date = mock_period_start
        target.end_date = mock_period_end
        target.user_id = mock_user.id

        result = sales_team_service.calculate_target_performance(target)

        assert result == (Decimal("5"), 100.0)

    def test_calculate_target_performance_contract_amount_basic(
        self,
        sales_team_service: SalesTeamService,
        mock_user,
        mock_period_start,
        mock_period_end,
    ):
        """Test target performance with basic contract amount."""
        target = MagicMock()
        target.target_type = "CONTRACT_AMOUNT"
        target.target_value = Decimal("100000")
        target.start_date = mock_period_start
        target.end_date = mock_period_end
        target.user_id = mock_user.id

        # Mock contracts in period
        contracts = []
        for i in range(1):
            contract = MagicMock()
            contract.created_at = datetime.combine(
                mock_period_start, datetime.min.time()
            )
            contract.contract_amount = Decimal("100000")
            contracts.append(contract)

        # Mock query to return filtered contracts
        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value = contracts
        mock_query.filter.return_value.all.return_value = contracts

        with patch.object(sales_team_service.db.query, return_value=mock_query):
            result = sales_team_service.calculate_target_performance(target)

        assert result == (Decimal("100000"), 100.0)

    def test_calculate_target_performance_collection_amount_basic(
        self,
        sales_team_service: SalesTeamService,
        mock_user,
        mock_period_start,
        mock_period_end,
    ):
        """Test target performance with basic collection amount."""
        target = MagicMock()
        target.target_type = "COLLECTION_AMOUNT"
        target.target_value = Decimal("50000")
        target.start_date = mock_period_start
        target.end_date = mock_period_end
        target.user_id = mock_user.id

        # Mock invoices in period
        invoices = []
        for i in range(1):
            invoice = MagicMock()
            invoice.invoice_date = datetime.combine(
                mock_period_start, datetime.min.time()
            )
            invoice.amount = Decimal("50000")
            invoices.append(invoice)

        # Mock query to return filtered invoices
        mock_query = MagicMock()
        mock_query.join.return_value.join.return_value = invoices
        mock_query.join.return_value.all.return_value = invoices

        with patch.object(sales_team_service.db.query, return_value=mock_query):
            result = sales_team_service.calculate_target_performance(target)

        assert result == (Decimal("50000"), 100.0)

    def test_calculate_target_performance_with_invoices(
        self,
        sales_team_service: SalesTeamService,
        mock_user,
        mock_period_start,
        mock_period_end,
    ):
        """Test target performance when multiple invoices."""
        target = MagicMock()
        target.target_type = "COLLECTION_AMOUNT"
        target.target_value = Decimal("100000")
        target.start_date = mock_period_start
        target.end_date = mock_period_end
        target.user_id = mock_user.id

        # Mock invoices - some in period, some outside
        invoices = []
        for i in range(1, 5):
            invoice = MagicMock()
            invoice.invoice_date = datetime.combine(
                mock_period_start + timedelta(days=i), datetime.min.time()
            )
            invoice.amount = Decimal("20000")
            invoices.append(invoice)

        # Mock query
        mock_query = MagicMock()
        mock_query.join.return_value.join.return_value = invoices
        mock_query.join.return_value.all.return_value = invoices

        with patch.object(sales_team_service.db.query, return_value=mock_query):
            result = sales_team_service.calculate_target_performance(target)

        # Should count all invoices (sum = 100000)
        assert result == (Decimal("100000"), 100.0)

    def test_calculate_target_performance_zero_target_value(
        self,
        sales_team_service: SalesTeamService,
        mock_user,
        mock_period_start,
        mock_period_end,
    ):
        """Test target performance when target value is zero."""
        target = MagicMock()
        target.target_type = "LEAD_COUNT"
        target.target_value = Decimal("0")
        target.start_date = mock_period_start
        target.end_date = mock_period_end
        target.user_id = mock_user.id

        with patch.object(sales_team_service.db.query):
            result = sales_team_service.calculate_target_performance(target)

        # Should handle zero gracefully
        assert result == (Decimal("0"), 0.0)

    def test_calculate_target_performance_no_target_type(
        self,
        sales_team_service: SalesTeamService,
        mock_user,
        mock_period_start,
        mock_period_end,
    ):
        """Test target performance when target type is None."""
        target = MagicMock()
        target.target_type = None  # No target type set
        target.target_value = Decimal("100")
        target.start_date = mock_period_start
        target.end_date = mock_period_end
        target.user_id = mock_user.id

        result = sales_team_service.calculate_target_performance(target)

        # Should handle gracefully
        assert result == (Decimal("100"), 0.0)


class TestCalculateTargetPerformanceEdgeCases:
    """Test edge cases and error handling."""

    def test_period_end_before_start(
        self,
        sales_team_service: SalesTeamService,
        mock_user,
        mock_period_start,
    ):
        """Test when period end is before period start (invalid)."""
        target = MagicMock()
        target.target_type = "LEAD_COUNT"
        target.target_value = Decimal("10")
        target.start_date = mock_period_end  # End before start!
        target.end_date = mock_period_start - timedelta(days=1)
        target.user_id = mock_user.id

        result = sales_team_service.calculate_target_performance(target)

        # Should handle gracefully
        assert result == (Decimal("0"), 0.0)

    def test_period_dates_outside_range(
        self,
        sales_team_service: SalesTeamService,
        mock_user,
        mock_period_start,
        mock_period_end,
    ):
        """Test when period dates are outside current period."""
        future_start = mock_period_start + timedelta(days=30)
        future_end = mock_period_end + timedelta(days=30)

        target = MagicMock()
        target.target_type = "LEAD_COUNT"
        target.target_value = Decimal("10")
        target.start_date = future_start
        target.end_date = future_end
        target.user_id = mock_user.id

        result = sales_team_service.calculate_target_performance(target)

        # Should handle gracefully
        assert result == (Decimal("0"), 0.0)

    def test_parse_period_value_invalid_format(
        self,
        sales_team_service: SalesTeamService,
    ):
        """Test parsing invalid period value format."""
        target = MagicMock()
        target.target_type = "LEAD_COUNT"
        target.target_value = Decimal("10")
        target.period_value = "2026Q1"  # Wrong format
        target.start_date = mock_period_start
        target.end_date = mock_period_end
        target.user_id = mock_user.id

        result = sales_team_service.calculate_target_performance(target)

        # Should parse as Q1 (first quarter)
        actual_value, completion_rate = result
        assert actual_value is not None
        assert completion_rate is not None

    def test_parse_period_value_month_format(
        self,
        sales_team_service: SalesTeamService,
    ):
        """Test parsing period value as month format."""
        target = MagicMock()
        target.target_type = "LEAD_COUNT"
        target.target_value = Decimal("10")
        target.period_value = "2026-01"  # Month format
        target.start_date = mock_period_start
        target.end_date = mock_period_end
        target.user_id = mock_user.id

        result = sales_team_service.calculate_target_performance(target)

        # Should parse correctly
        assert result == (Decimal("10"), 100.0)

    def test_parse_period_value_year_format(
        self,
        sales_team_service: SalesTeamService,
    ):
        """Test parsing period value as year format."""
        target = MagicMock()
        target.target_type = "LEAD_COUNT"
        target.target_value = Decimal("10")
        target.period_value = "2026"  # Year format
        target.start_date = mock_period_start
        target.end_date = mock_period_end
        target.user_id = mock_user.id

        result = sales_team_service.calculate_target_performance(target)

        # Should parse correctly
        assert result == (Decimal("10"), 100.0)


class TestSalesTeamServiceHelperMethods:
    """Test helper methods in SalesTeamService."""

    def test_parse_period_value_quarter(self, sales_team_service: SalesTeamService):
        """Test parsing quarterly period value."""
        # Q1
        result = sales_team_service.parse_period_value("2026Q1")
        assert result == ("2026-01-01", "2026-03-31")

        # Q2
        result = sales_team_service.parse_period_value("2026Q2")
        assert result == ("2026-04-01", "2026-06-30")

        # Q3
        result = sales_team_service.parse_period_value("2026Q3")
        assert result == ("2026-07-01", "2026-09-30")

        # Q4
        result = sales_team_service.parse_period_value("2026Q4")
        assert result == ("2026-10-01", "2026-12-31")

    def test_parse_period_value_month(self, sales_team_service: SalesTeamService):
        """Test parsing monthly period value."""
        result = sales_team_service.parse_period_value("2026-01")
        assert result == ("2026-01-01", "2026-01-31")

    def test_parse_period_value_year(self, sales_team_service: SalesTeamService):
        """Test parsing yearly period value."""
        result = sales_team_service.parse_period_value("2026")
        assert result == ("2026-01-01", "2026-12-31")

    def test_parse_period_value_invalid_format(
        self, sales_team_service: SalesTeamService
    ):
        """Test parsing invalid period value format."""
        result = sales_team_service.parse_period_value("invalid")
        assert result is None

    def test_parse_period_value_empty_string(
        self, sales_team_service: SalesTeamService
    ):
        """Test parsing empty period value."""
        result = sales_team_service.parse_period_value("")
        assert result is None
