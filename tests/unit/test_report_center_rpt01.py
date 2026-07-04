# -*- coding: utf-8 -*-
"""RPT-01: report center must not expose placeholder report types."""

from unittest.mock import Mock

from app.api.v1.endpoints.report_center.configs import get_report_types
from app.services.report_data_generation.core import ReportDataGenerationCore
from app.services.report_data_generation.router import ReportRouterMixin


def test_role_matrix_only_exposes_implemented_report_types():
    allowed = {
        report_type
        for reports in ReportDataGenerationCore.ROLE_REPORT_MATRIX.values()
        for report_type in reports
    }

    assert allowed <= set(ReportDataGenerationCore.IMPLEMENTED_REPORT_TYPES)
    assert "RISK_REPORT" not in allowed
    assert "COMPANY_MONTHLY" not in allowed
    assert "SALES_FUNNEL" not in allowed
    assert "PROCUREMENT_ANALYSIS" not in allowed


def test_report_type_config_only_lists_implemented_report_types():
    response = get_report_types(db=Mock(), current_user=Mock())
    exposed_types = {item["type"] for item in response.types}

    assert exposed_types == set(ReportDataGenerationCore.IMPLEMENTED_REPORT_TYPES)
    assert "RISK_REPORT" not in exposed_types
    assert "COMPANY_MONTHLY" not in exposed_types
    assert "CUSTOM" not in exposed_types


def test_unimplemented_report_type_fails_closed_instead_of_placeholder_success():
    result = ReportRouterMixin.generate_report_by_type(Mock(), report_type="RISK_REPORT")

    assert result == {"error": "报表类型 RISK_REPORT 尚未实现或未开放"}
