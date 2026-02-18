# -*- coding: utf-8 -*-
"""第二十四批 - template_report/generic_report 单元测试"""

import pytest
from datetime import date
from unittest.mock import MagicMock

pytest.importorskip("app.services.template_report.generic_report")

from app.services.template_report.generic_report import GenericReportMixin


class TestGenerateGenericReport:
    def setup_method(self):
        self.db = MagicMock()
        self.start = date(2025, 1, 1)
        self.end = date(2025, 3, 31)

    def test_returns_dict(self):
        result = GenericReportMixin._generate_generic_report(
            db=self.db,
            report_type="SUMMARY",
            project_id=None,
            department_id=None,
            start_date=self.start,
            end_date=self.end,
        )
        assert isinstance(result, dict)

    def test_report_type_in_result(self):
        result = GenericReportMixin._generate_generic_report(
            db=self.db,
            report_type="DETAIL",
            project_id=1,
            department_id=None,
            start_date=self.start,
            end_date=self.end,
        )
        assert result["report_type"] == "DETAIL"

    def test_period_dates_in_result(self):
        result = GenericReportMixin._generate_generic_report(
            db=self.db,
            report_type="KPI",
            project_id=None,
            department_id=5,
            start_date=self.start,
            end_date=self.end,
        )
        assert result["period"]["start_date"] == "2025-01-01"
        assert result["period"]["end_date"] == "2025-03-31"

    def test_result_has_sections_and_metrics(self):
        result = GenericReportMixin._generate_generic_report(
            db=self.db,
            report_type="ANY",
            project_id=None,
            department_id=None,
            start_date=self.start,
            end_date=self.end,
        )
        assert "sections" in result
        assert "metrics" in result

    def test_different_report_types(self):
        for rtype in ["SUMMARY", "DETAIL", "KPI", "FINANCE"]:
            result = GenericReportMixin._generate_generic_report(
                db=self.db,
                report_type=rtype,
                project_id=None,
                department_id=None,
                start_date=self.start,
                end_date=self.end,
            )
            assert result["report_type"] == rtype
