# -*- coding: utf-8 -*-
"""第四十六批 - 模板报表服务单元测试"""
import pytest
from datetime import date

pytest.importorskip("app.services.template_report_service",
                    reason="依赖不满足，跳过")

from unittest.mock import MagicMock, patch
from app.services.template_report_service import TemplateReportService


def _make_template(report_type="PROJECT_WEEKLY"):
    t = MagicMock()
    t.template_code = "TPL001"
    t.template_name = "测试模板"
    t.report_type = report_type
    return t


class TestGenerateFromTemplate:
    def test_project_weekly_called(self):
        db = MagicMock()
        template = _make_template("PROJECT_WEEKLY")

        with patch.object(TemplateReportService, "_generate_project_weekly",
                          return_value={"template_code": "TPL001"}) as mock_gen:
            result = TemplateReportService.generate_from_template(db, template, project_id=1)

        mock_gen.assert_called_once()

    def test_dept_weekly_called(self):
        db = MagicMock()
        template = _make_template("DEPT_WEEKLY")

        with patch.object(TemplateReportService, "_generate_dept_weekly",
                          return_value={"template_code": "TPL001"}) as mock_gen:
            result = TemplateReportService.generate_from_template(db, template, department_id=2)

        mock_gen.assert_called_once()

    def test_unknown_report_type_returns_default(self):
        db = MagicMock()
        template = _make_template("UNKNOWN_TYPE")

        result = TemplateReportService.generate_from_template(db, template)
        assert result["template_code"] == "TPL001"
        assert result["sections"] == {}

    def test_company_monthly_called(self):
        db = MagicMock()
        template = _make_template("COMPANY_MONTHLY")
        db.query.return_value.filter.return_value.all.return_value = []

        result = TemplateReportService.generate_from_template(db, template)
        assert "total_projects" in result.get("summary", {})

    def test_workload_analysis_returns_dict(self):
        db = MagicMock()
        template = _make_template("WORKLOAD_ANALYSIS")
        db.query.return_value.filter.return_value.first.return_value = None

        result = TemplateReportService.generate_from_template(db, template, department_id=5)
        assert "sections" in result

    def test_cost_analysis_with_no_project(self):
        db = MagicMock()
        template = _make_template("COST_ANALYSIS")
        db.query.return_value.filter.return_value.all.return_value = []
        db.query.return_value.all.return_value = []

        result = TemplateReportService.generate_from_template(db, template)
        assert "sections" in result
