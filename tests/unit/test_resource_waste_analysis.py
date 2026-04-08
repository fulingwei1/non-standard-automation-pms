# -*- coding: utf-8 -*-
"""资源浪费分析服务单元测试 - Core + service init"""
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.resource_waste_analysis.core import ResourceWasteAnalysisCore


class TestResourceWasteAnalysisCore:

    def test_default_hourly_rate(self):
        core = ResourceWasteAnalysisCore(MagicMock())
        assert core.hourly_rate == Decimal("300")

    def test_custom_hourly_rate(self):
        core = ResourceWasteAnalysisCore(MagicMock(), hourly_rate=Decimal("500"))
        assert core.hourly_rate == Decimal("500")

    def test_db_stored(self):
        db = MagicMock()
        core = ResourceWasteAnalysisCore(db)
        assert core.db is db

    def test_role_rates_all_present(self):
        rates = ResourceWasteAnalysisCore.ROLE_HOURLY_RATES
        assert set(rates.keys()) == {"engineer", "senior_engineer", "presales", "designer", "project_manager"}

    def test_role_rate_values(self):
        rates = ResourceWasteAnalysisCore.ROLE_HOURLY_RATES
        assert rates["engineer"] == Decimal("300")
        assert rates["senior_engineer"] == Decimal("400")
        assert rates["presales"] == Decimal("350")
        assert rates["designer"] == Decimal("320")
        assert rates["project_manager"] == Decimal("450")

    def test_default_rate_constant(self):
        assert ResourceWasteAnalysisCore.DEFAULT_HOURLY_RATE == Decimal("300")


class TestResourceWasteAnalysisServiceInit:
    """Test that the composite service initializes correctly."""

    def test_service_init(self):
        from app.services.resource_waste_analysis import ResourceWasteAnalysisService
        db = MagicMock()
        svc = ResourceWasteAnalysisService(db)
        assert svc.db is db
        assert svc.hourly_rate == Decimal("300")

    def test_service_custom_rate(self):
        from app.services.resource_waste_analysis import ResourceWasteAnalysisService
        svc = ResourceWasteAnalysisService(MagicMock(), hourly_rate=Decimal("450"))
        assert svc.hourly_rate == Decimal("450")

    def test_service_has_methods(self):
        from app.services.resource_waste_analysis import ResourceWasteAnalysisService
        svc = ResourceWasteAnalysisService(MagicMock())
        assert hasattr(svc, "calculate_waste_by_period")
        assert hasattr(svc, "get_salesperson_waste_ranking")
        assert hasattr(svc, "analyze_failure_patterns")
        assert hasattr(svc, "get_monthly_trend")
        assert hasattr(svc, "get_department_comparison")
        assert hasattr(svc, "generate_waste_report")
        assert hasattr(svc, "get_lead_resource_investment")
