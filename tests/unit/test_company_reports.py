# -*- coding: utf-8 -*-
import pytest
from unittest.mock import MagicMock
from datetime import date
from app.services.template_report.company_reports import CompanyReportMixin


class TestCompanyReportMixin:
    def test_generate_empty(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = CompanyReportMixin._generate_company_monthly(
            db, date(2024, 1, 1), date(2024, 1, 31), {}, {}
        )
        assert result["summary"]["total_projects"] == 0
        assert result["sections"]["project_status"]["data"] == {}

    def test_generate_with_projects(self):
        db = MagicMock()
        p1 = MagicMock(); p1.status = "IN_PROGRESS"; p1.health_status = "H1"
        p2 = MagicMock(); p2.status = "COMPLETED"; p2.health_status = "H2"
        db.query.return_value.filter.return_value.all.side_effect = [
            [p1, p2],  # projects
            [],  # departments
        ]
        result = CompanyReportMixin._generate_company_monthly(
            db, date(2024, 1, 1), date(2024, 1, 31), {}, {}
        )
        assert result["summary"]["total_projects"] == 2
        assert result["metrics"]["total_projects"] == 2
