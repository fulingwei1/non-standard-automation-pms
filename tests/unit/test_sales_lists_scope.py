# -*- coding: utf-8 -*-
"""
Sales lists/analytics scope tests — Sprint 6

Verifies that list, statistics, analytics, and export endpoints
correctly enforce data-scope checks.
"""

import inspect
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# 1. Pipeline analysis — all 4 endpoints must pass current_user to service
# ---------------------------------------------------------------------------

class TestPipelineAnalysisScope:
    """Pipeline analysis endpoints must instantiate service with current_user."""

    def test_pipeline_breaks_passes_user(self):
        source = inspect.getsource(
            __import__(
                "app.api.v1.endpoints.sales.pipeline_analysis",
                fromlist=["get_pipeline_breaks"],
            ).get_pipeline_breaks
        )
        assert "current_user=current_user" in source

    def test_break_reasons_passes_user(self):
        source = inspect.getsource(
            __import__(
                "app.api.v1.endpoints.sales.pipeline_analysis",
                fromlist=["get_break_reasons"],
            ).get_break_reasons
        )
        assert "current_user=current_user" in source

    def test_break_patterns_passes_user(self):
        source = inspect.getsource(
            __import__(
                "app.api.v1.endpoints.sales.pipeline_analysis",
                fromlist=["get_break_patterns"],
            ).get_break_patterns
        )
        assert "current_user=current_user" in source

    def test_break_warnings_passes_user(self):
        source = inspect.getsource(
            __import__(
                "app.api.v1.endpoints.sales.pipeline_analysis",
                fromlist=["get_pipeline_break_warnings"],
            ).get_pipeline_break_warnings
        )
        assert "current_user=current_user" in source


class TestPipelineBreakServiceScope:
    """PipelineBreakAnalysisService must apply scope filtering internally."""

    def test_service_accepts_current_user(self):
        from app.services.pipeline_break_analysis_service import PipelineBreakAnalysisService

        db = MagicMock()
        user = MagicMock()
        service = PipelineBreakAnalysisService(db, current_user=user)
        assert service._current_user is user

    def test_apply_scope_calls_filter(self):
        from app.services.pipeline_break_analysis_service import PipelineBreakAnalysisService

        db = MagicMock()
        user = MagicMock()
        service = PipelineBreakAnalysisService(db, current_user=user)

        with patch(
            "app.core.sales_permissions.filter_sales_data_by_scope"
        ) as mock_filter:
            mock_filter.return_value = MagicMock()
            service._apply_scope(MagicMock(), MagicMock(), "owner_id")
            mock_filter.assert_called_once()

    def test_apply_scope_noop_without_user(self):
        from app.services.pipeline_break_analysis_service import PipelineBreakAnalysisService

        db = MagicMock()
        service = PipelineBreakAnalysisService(db)  # no user
        query = MagicMock()
        result = service._apply_scope(query, MagicMock(), "owner_id")
        assert result is query  # unchanged


# ---------------------------------------------------------------------------
# 2. Quote stats — must apply filter_sales_data_by_scope
# ---------------------------------------------------------------------------

class TestQuoteStatsScope:
    """GET /statistics/quote-stats must filter by scope."""

    def test_quote_stats_has_scope_filter(self):
        source = inspect.getsource(
            __import__(
                "app.api.v1.endpoints.sales.statistics_quotes",
                fromlist=["get_quote_stats"],
            ).get_quote_stats
        )
        assert "filter_sales_data_by_scope" in source


# ---------------------------------------------------------------------------
# 3. Revenue forecast — must apply filter_sales_data_by_scope
# ---------------------------------------------------------------------------

class TestRevenueForecastScope:
    """GET /statistics/revenue-forecast must filter by scope."""

    def test_revenue_forecast_has_scope_filter(self):
        source = inspect.getsource(
            __import__(
                "app.api.v1.endpoints.sales.statistics_prediction",
                fromlist=["get_revenue_forecast"],
            ).get_revenue_forecast
        )
        assert "filter_sales_data_by_scope" in source


# ---------------------------------------------------------------------------
# 4. Quote exports — must check_sales_data_permission
# ---------------------------------------------------------------------------

class TestQuoteExportScope:
    """Quote export endpoints must check entity-level scope."""

    def test_excel_export_has_scope_check(self):
        source = inspect.getsource(
            __import__(
                "app.api.v1.endpoints.sales.quote_exports",
                fromlist=["export_quote_to_excel"],
            ).export_quote_to_excel
        )
        assert "check_sales_data_permission" in source

    def test_pdf_export_has_scope_check(self):
        source = inspect.getsource(
            __import__(
                "app.api.v1.endpoints.sales.quote_exports",
                fromlist=["export_quote_to_pdf"],
            ).export_quote_to_pdf
        )
        assert "check_sales_data_permission" in source

    def test_batch_export_has_scope_check(self):
        source = inspect.getsource(
            __import__(
                "app.api.v1.endpoints.sales.quote_exports",
                fromlist=["batch_export_quotes"],
            ).batch_export_quotes
        )
        assert "check_sales_data_permission" in source


# ---------------------------------------------------------------------------
# 5. Global contacts list — must use proper scope, not is_admin
# ---------------------------------------------------------------------------

class TestGlobalContactsScope:
    """GET /contacts must use scope-based filtering, not is_admin."""

    def test_contacts_list_uses_scope_not_is_admin(self):
        source = inspect.getsource(
            __import__(
                "app.api.v1.endpoints.sales.contacts",
                fromlist=["read_contacts"],
            ).read_contacts
        )
        # Should use get_sales_data_scope, not is_admin
        assert "get_sales_data_scope" in source
        # Should NOT still use the is_admin hack
        assert "is_admin" not in source
