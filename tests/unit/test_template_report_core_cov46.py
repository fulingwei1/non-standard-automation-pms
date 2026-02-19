# -*- coding: utf-8 -*-
"""第四十六批 - 模板报表核心单元测试"""
import pytest
from datetime import date

pytest.importorskip("app.services.template_report.core",
                    reason="依赖不满足，跳过")

from unittest.mock import MagicMock, patch
from app.services.template_report.core import TemplateReportCore


def _make_template(report_type="PROJECT_WEEKLY"):
    t = MagicMock()
    t.id = 1
    t.template_code = "TPL001"
    t.template_name = "测试模板"
    t.report_type = report_type
    t.sections = {}
    t.metrics_config = {}
    return t


class TestGenerateFromTemplate:
    def test_includes_period_in_result(self):
        db = MagicMock()
        template = _make_template("PROJECT_WEEKLY")

        with patch("app.services.template_report.core.ProjectReportMixin") as mock_p:
            mock_p._generate_project_weekly.return_value = {}
            result = TemplateReportCore.generate_from_template(
                db, template,
                start_date=date(2024, 1, 1),
                end_date=date(2024, 1, 7)
            )

        assert result["period"]["start_date"] == "2024-01-01"
        assert result["period"]["end_date"] == "2024-01-07"

    def test_sets_default_dates_when_not_provided(self):
        db = MagicMock()
        template = _make_template("PROJECT_WEEKLY")

        with patch("app.services.template_report.core.ProjectReportMixin") as mock_p:
            mock_p._generate_project_weekly.return_value = {}
            result = TemplateReportCore.generate_from_template(db, template)

        assert "period" in result
        assert result["period"]["end_date"] == date.today().isoformat()

    def test_project_weekly_calls_correct_generator(self):
        db = MagicMock()
        template = _make_template("PROJECT_WEEKLY")

        with patch("app.services.template_report.core.ProjectReportMixin") as mock_p:
            mock_p._generate_project_weekly.return_value = {"sections": {"foo": "bar"}}
            result = TemplateReportCore.generate_from_template(db, template, project_id=5)

        mock_p._generate_project_weekly.assert_called_once()

    def test_company_monthly_calls_correct_generator(self):
        db = MagicMock()
        template = _make_template("COMPANY_MONTHLY")

        with patch("app.services.template_report.core.CompanyReportMixin") as mock_c, \
             patch("app.services.template_report.core.ProjectReportMixin"), \
             patch("app.services.template_report.core.DeptReportMixin"), \
             patch("app.services.template_report.core.AnalysisReportMixin"), \
             patch("app.services.template_report.core.GenericReportMixin"):
            mock_c._generate_company_monthly.return_value = {}
            result = TemplateReportCore.generate_from_template(db, template)

        mock_c._generate_company_monthly.assert_called_once()

    def test_unknown_type_calls_generic_generator(self):
        db = MagicMock()
        template = _make_template("UNKNOWN_TYPE")

        with patch("app.services.template_report.core.ProjectReportMixin"), \
             patch("app.services.template_report.core.DeptReportMixin"), \
             patch("app.services.template_report.core.AnalysisReportMixin"), \
             patch("app.services.template_report.core.CompanyReportMixin"), \
             patch("app.services.template_report.core.GenericReportMixin") as mock_g:
            mock_g._generate_generic_report.return_value = {}
            result = TemplateReportCore.generate_from_template(db, template)

        mock_g._generate_generic_report.assert_called_once()

    def test_result_contains_template_info(self):
        db = MagicMock()
        template = _make_template("PROJECT_WEEKLY")

        with patch("app.services.template_report.core.ProjectReportMixin") as mock_p:
            mock_p._generate_project_weekly.return_value = {}
            result = TemplateReportCore.generate_from_template(db, template)

        assert result["template_id"] == 1
        assert result["template_code"] == "TPL001"
        assert result["template_name"] == "测试模板"
