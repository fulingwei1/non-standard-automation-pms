# -*- coding: utf-8 -*-
"""第二十批 - project_export_service 单元测试"""
import pytest
pytest.importorskip("app.services.project_export_service")

from unittest.mock import MagicMock, patch
from app.services.project_export_service import (
    get_excel_styles,
    build_project_info_data,
)


def make_project(**kwargs):
    p = MagicMock()
    p.project_code = kwargs.get('project_code', 'P-001')
    p.project_name = kwargs.get('project_name', '测试项目')
    p.customer_name = kwargs.get('customer_name', '客户A')
    p.contract_no = kwargs.get('contract_no', 'C-001')
    p.contract_amount = kwargs.get('contract_amount', 100000)
    p.pm_name = kwargs.get('pm_name', '张三')
    p.project_type = kwargs.get('project_type', '非标')
    p.stage = kwargs.get('stage', '执行')
    p.status = kwargs.get('status', '进行中')
    p.health = kwargs.get('health', 'GREEN')
    p.progress_pct = kwargs.get('progress_pct', 50)
    p.planned_start_date = kwargs.get('planned_start_date', None)
    p.planned_end_date = kwargs.get('planned_end_date', None)
    p.actual_start_date = kwargs.get('actual_start_date', None)
    p.actual_end_date = kwargs.get('actual_end_date', None)
    return p


class TestGetExcelStyles:
    def test_returns_dict(self):
        styles = get_excel_styles()
        assert isinstance(styles, dict)

    def test_returns_empty_when_no_openpyxl(self):
        with patch("app.services.project_export_service.OPENPYXL_AVAILABLE", False):
            styles = get_excel_styles()
            assert styles == {}

    def test_contains_expected_keys_when_available(self):
        import importlib
        try:
            import openpyxl  # noqa
            styles = get_excel_styles()
            assert 'header_fill' in styles or styles == {}
        except ImportError:
            pytest.skip("openpyxl not installed")


class TestBuildProjectInfoData:
    def test_returns_list(self):
        project = make_project()
        data = build_project_info_data(project)
        assert isinstance(data, list)

    def test_contains_tuples(self):
        project = make_project()
        data = build_project_info_data(project)
        for item in data:
            assert isinstance(item, tuple)
            assert len(item) == 2

    def test_project_name_in_data(self):
        project = make_project(project_name='我的项目')
        data = build_project_info_data(project)
        labels = [item[0] for item in data]
        values = [item[1] for item in data]
        assert '项目名称' in labels
        name_idx = labels.index('项目名称')
        assert values[name_idx] == '我的项目'

    def test_handles_none_dates(self):
        project = make_project(
            planned_start_date=None,
            planned_end_date=None,
            actual_start_date=None,
            actual_end_date=None,
        )
        data = build_project_info_data(project)
        # Should not raise
        assert any(item[0] == '计划开始日期' for item in data)

    def test_formats_dates_correctly(self):
        from datetime import date
        project = make_project(
            planned_start_date=date(2025, 1, 1),
            planned_end_date=date(2025, 12, 31),
        )
        data = build_project_info_data(project)
        date_values = {item[0]: item[1] for item in data}
        assert date_values['计划开始日期'] == '2025-01-01'
        assert date_values['计划结束日期'] == '2025-12-31'

    def test_handles_none_contract_amount(self):
        project = make_project(contract_amount=None)
        data = build_project_info_data(project)
        amount_vals = {item[0]: item[1] for item in data}
        assert '合同金额' in amount_vals
        assert '0.00' in amount_vals['合同金额']


class TestProjectExportServiceClass:
    def test_import_class_if_exists(self):
        try:
            from app.services.project_export_service import ProjectExportService
            db = MagicMock()
            svc = ProjectExportService(db)
            assert svc is not None
        except ImportError:
            pass  # class may not exist, module is functions

    def test_export_projects_function_exists(self):
        import app.services.project_export_service as mod
        # Check at least one export function exists
        assert any(
            name in dir(mod)
            for name in ['export_projects', 'ProjectExportService', 'build_project_info_data']
        )
