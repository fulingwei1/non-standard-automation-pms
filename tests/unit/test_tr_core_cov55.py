# -*- coding: utf-8 -*-
"""
Tests for app/services/template_report/core.py
"""
import sys
import pytest
from datetime import date
from unittest.mock import MagicMock, patch, Mock

try:
    from app.services.template_report.core import TemplateReportCore
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


def _make_template(report_type, template_id=1):
    t = MagicMock()
    t.id = template_id
    t.template_code = f"TPL_{template_id}"
    t.template_name = f"Template {template_id}"
    t.report_type = report_type
    t.sections = {}
    t.metrics_config = {}
    return t


def _inject_mock_mixins():
    """Inject mock submodules into sys.modules so inner imports resolve"""
    mocks = {}
    for name in ["project_reports", "dept_reports", "analysis_reports",
                 "company_reports", "generic_report"]:
        mod = MagicMock()
        full = f"app.services.template_report.{name}"
        sys.modules[full] = mod
        mocks[name] = mod
    return mocks


def _cleanup_mock_mixins(mocks):
    for name in mocks:
        sys.modules.pop(f"app.services.template_report.{name}", None)


def test_generate_sets_default_dates():
    """未提供日期时应自动设置默认日期范围"""
    mocks = _inject_mock_mixins()
    try:
        db = MagicMock()
        template = _make_template("UNKNOWN_TYPE")
        mocks["generic_report"].GenericReportMixin._generate_generic_report.return_value = {}
        result = TemplateReportCore.generate_from_template(db, template)
        assert "period" in result
        assert result["period"]["end_date"] is not None
        assert result["period"]["start_date"] is not None
    finally:
        _cleanup_mock_mixins(mocks)


def test_generate_returns_template_info():
    """结果包含模板基本信息"""
    mocks = _inject_mock_mixins()
    try:
        db = MagicMock()
        template = _make_template("OTHER", template_id=5)
        mocks["generic_report"].GenericReportMixin._generate_generic_report.return_value = {}
        result = TemplateReportCore.generate_from_template(db, template)
        assert result["template_id"] == 5
        assert result["report_type"] == "OTHER"
    finally:
        _cleanup_mock_mixins(mocks)


def test_generate_project_weekly():
    """PROJECT_WEEKLY 类型路由到 ProjectReportMixin"""
    mocks = _inject_mock_mixins()
    try:
        db = MagicMock()
        template = _make_template("PROJECT_WEEKLY")
        mocks["project_reports"].ProjectReportMixin._generate_project_weekly.return_value = {}
        TemplateReportCore.generate_from_template(db, template, project_id=1)
        mocks["project_reports"].ProjectReportMixin._generate_project_weekly.assert_called_once()
    finally:
        _cleanup_mock_mixins(mocks)


def test_generate_dept_monthly():
    """DEPT_MONTHLY 类型路由到 DeptReportMixin"""
    mocks = _inject_mock_mixins()
    try:
        db = MagicMock()
        template = _make_template("DEPT_MONTHLY")
        mocks["dept_reports"].DeptReportMixin._generate_dept_monthly.return_value = {}
        TemplateReportCore.generate_from_template(db, template, department_id=2)
        mocks["dept_reports"].DeptReportMixin._generate_dept_monthly.assert_called_once()
    finally:
        _cleanup_mock_mixins(mocks)


def test_generate_company_monthly():
    """COMPANY_MONTHLY 类型路由到 CompanyReportMixin"""
    mocks = _inject_mock_mixins()
    try:
        db = MagicMock()
        template = _make_template("COMPANY_MONTHLY")
        mocks["company_reports"].CompanyReportMixin._generate_company_monthly.return_value = {}
        TemplateReportCore.generate_from_template(db, template)
        mocks["company_reports"].CompanyReportMixin._generate_company_monthly.assert_called_once()
    finally:
        _cleanup_mock_mixins(mocks)


def test_generate_with_explicit_dates():
    """提供明确日期时不使用默认值"""
    mocks = _inject_mock_mixins()
    try:
        db = MagicMock()
        template = _make_template("GENERIC")
        start = date(2024, 1, 1)
        end = date(2024, 1, 31)
        mocks["generic_report"].GenericReportMixin._generate_generic_report.return_value = {}
        result = TemplateReportCore.generate_from_template(
            db, template, start_date=start, end_date=end
        )
        assert result["period"]["start_date"] == "2024-01-01"
        assert result["period"]["end_date"] == "2024-01-31"
    finally:
        _cleanup_mock_mixins(mocks)


def test_generate_cost_analysis():
    """COST_ANALYSIS 类型路由到 AnalysisReportMixin"""
    mocks = _inject_mock_mixins()
    try:
        db = MagicMock()
        template = _make_template("COST_ANALYSIS")
        mocks["analysis_reports"].AnalysisReportMixin._generate_cost_analysis.return_value = {}
        TemplateReportCore.generate_from_template(db, template, project_id=1)
        mocks["analysis_reports"].AnalysisReportMixin._generate_cost_analysis.assert_called_once()
    finally:
        _cleanup_mock_mixins(mocks)
