# -*- coding: utf-8 -*-
"""
Tests for project_export_service service
Covers: app/services/project_export_service.py
Coverage Target: 0% → 80%+
Current Coverage: 0%
Updated: 2025-01-22
"""

import pytest
from datetime import date
from io import BytesIO
from unittest.mock import MagicMock, patch, Mock


from app.models.project import Project


class TestGetExcelStyles:
    """Test suite for get_excel_styles function."""

    def test_get_excel_styles_with_openpyxl(self):
        """Test getting styles when openpyxl is available."""
        from app.services.project_export_service import (
            get_excel_styles,
            OPENPYXL_AVAILABLE,
        )

        if OPENPYXL_AVAILABLE:
            styles = get_excel_styles()

            assert isinstance(styles, dict)
            assert "header_fill" in styles
            assert "header_font" in styles
            assert "title_font" in styles
            assert "border" in styles

            assert styles["header_fill"] is not None
            assert styles["header_font"] is not None
            assert styles["title_font"] is not None
            assert styles["border"] is not None

    def test_get_excel_styles_without_openpyxl(self):
        """Test getting styles when openpyxl is not available."""
        with patch("app.services.project_export_service.OPENPYXL_AVAILABLE", False):
            from app.services.project_export_service import get_excel_styles

            styles = get_excel_styles()

            assert isinstance(styles, dict)
            assert len(styles) == 0


class TestBuildProjectInfoData:
    """Test suite for build_project_info_data function."""

    def test_build_project_info_data_complete(self):
        """Test building project info with complete data."""
        from app.services.project_export_service import build_project_info_data

        project = MagicMock(spec=Project)
        project.project_code = "PJ250101001"
        project.project_name = "测试项目"
        project.customer_name = "客户A"
        project.contract_no = "CT2025001"
        project.contract_amount = 100000.00
        project.pm_name = "张三"
        project.project_type = "NEW"
        project.stage = "S4"
        project.status = "ST10"
        project.health = "H1"
        project.progress_pct = 50.5
        project.planned_start_date = date(2025, 1, 1)
        project.planned_end_date = date(2025, 3, 31)
        project.actual_start_date = date(2025, 1, 10)
        project.actual_end_date = None

        result = build_project_info_data(project)

        assert len(result) == 15
        assert result[0] == ("项目编码", "PJ250101001")
        assert result[1] == ("项目名称", "测试项目")
        assert result[2] == ("客户名称", "客户A")
        assert result[3] == ("合同编号", "CT2025001")
        assert result[4] == ("合同金额", "100,000.00")
        assert result[5] == ("项目经理", "张三")
        assert result[6] == ("项目类型", "NEW")
        assert result[7] == ("阶段", "S4")
        assert result[8] == ("状态", "ST10")
        assert result[9] == ("健康度", "H1")
        assert result[10] == ("进度(%)", "50.50")
        assert result[11] == ("计划开始日期", "2025-01-01")
        assert result[12] == ("计划结束日期", "2025-03-31")
        assert result[13] == ("实际开始日期", "2025-01-10")
        assert result[14] == ("实际结束日期", "")

    def test_build_project_info_data_with_nulls(self):
        """Test building project info with null values."""
        from app.services.project_export_service import build_project_info_data

        project = MagicMock(spec=Project)
        project.project_code = None
        project.project_name = None
        project.customer_name = None
        project.contract_no = None
        project.contract_amount = None
        project.pm_name = None
        project.project_type = None
        project.stage = None
        project.status = None
        project.health = None
        project.progress_pct = None
        project.planned_start_date = None
        project.planned_end_date = None
        project.actual_start_date = None
        project.actual_end_date = None

        result = build_project_info_data(project)

        assert len(result) == 15
        for label, value in result:
            assert value == "" or value == "0.00"

    def test_build_project_info_data_with_zero_amount(self):
        """Test building project info data with zero contract amount."""
        from app.services.project_export_service import build_project_info_data

        project = MagicMock(spec=Project)
        project.project_code = "PJ001"
        project.project_name = "Test"
        project.customer_name = "Customer"
        project.contract_no = "CN001"
        project.contract_amount = 0
        project.pm_name = "PM"
        project.project_type = "Type"
        project.stage = "S1"
        project.status = "Active"
        project.health = "H1"
        project.progress_pct = 0
        project.planned_start_date = date(2025, 1, 1)
        project.planned_end_date = date(2025, 12, 31)
        project.actual_start_date = date(2025, 1, 2)
        project.actual_end_date = date(2025, 12, 30)

        result = build_project_info_data(project)

        amount_tuple = [t for t in result if t[0] == "合同金额"][0]
        assert amount_tuple[1] == "0.00"


class TestAddProjectInfoSheet:
    """Test suite for add_project_info_sheet function."""

    def test_add_project_info_sheet_without_openpyxl(self):
        """Test adding sheet without openpyxl."""
        from app.services.project_export_service import add_project_info_sheet

        ws = MagicMock()
        project = MagicMock(spec=Project)
        styles = {}

        with patch("app.services.project_export_service.OPENPYXL_AVAILABLE", False):
            add_project_info_sheet(ws, project, styles)

            ws.__setitem__.assert_not_called()

    def test_add_project_info_sheet_with_openpyxl(self):
        """Test adding sheet with openpyxl available."""
        from app.services.project_export_service import (
            add_project_info_sheet,
            OPENPYXL_AVAILABLE,
        )

        if not OPENPYXL_AVAILABLE:
            pytest.skip("openpyxl not available")

        ws = MagicMock()
        ws.merge_cells = MagicMock()
        ws.__setitem__ = MagicMock()
        ws.column_dimensions = {}

        project = MagicMock(spec=Project)
        project.project_code = "PJ001"
        project.project_name = "测试项目"
        project.customer_name = "客户A"
        project.contract_no = "CT001"
        project.contract_amount = 50000.0
        project.pm_name = "张三"
        project.project_type = "NEW"
        project.stage = "S1"
        project.status = "ST01"
        project.health = "H1"
        project.progress_pct = 10.0
        project.planned_start_date = date(2025, 1, 1)
        project.planned_end_date = date(2025, 3, 31)
        project.actual_start_date = None
        project.actual_end_date = None

        styles = {
            "title_font": MagicMock(),
            "border": MagicMock(),
        }

        mock_cell = MagicMock()
        ws.cell = MagicMock(return_value=mock_cell)

        add_project_info_sheet(ws, project, styles)

        assert ws.merge_cells.called
        ws.__setitem__.assert_any_call("A1")


class TestCreateProjectDetailExcel:
    """Test suite for create_project_detail_excel function."""

    def test_create_project_detail_excel_without_openpyxl(self):
        """Test creating Excel when openpyxl is not available."""
        from app.services.project_export_service import create_project_detail_excel

        db_session = MagicMock()
        project = MagicMock()
        project.id = 1

        with patch("app.services.project_export_service.OPENPYXL_AVAILABLE", False):
            with pytest.raises(ImportError, match="Excel处理库未安装"):
                create_project_detail_excel(
                    db_session, project, include_tasks=False, include_costs=False
                )

    def test_create_project_detail_excel_basic(self):
        """Test creating basic Excel (no tasks, no costs)."""
        from app.services.project_export_service import (
            create_project_detail_excel,
            OPENPYXL_AVAILABLE,
        )

        if not OPENPYXL_AVAILABLE:
            pytest.skip("openpyxl not available")

        db_session = MagicMock()
        project = MagicMock()
        project.id = 1
        project.project_name = "Test Project"

        def mock_query_side_effect(model):
            query_mock = MagicMock()
            query_mock.order_by = MagicMock(return_value=query_mock)
            query_mock.filter = MagicMock(return_value=query_mock)
            query_mock.all = MagicMock(return_value=[])
            return query_mock

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = create_project_detail_excel(
            db_session, project, include_tasks=False, include_costs=False
        )

        assert isinstance(result, BytesIO)
        assert result.tell() > 0

    def test_create_project_detail_excel_with_tasks(self):
        """Test creating Excel with tasks."""
        from app.services.project_export_service import (
            create_project_detail_excel,
            OPENPYXL_AVAILABLE,
        )

        if not OPENPYXL_AVAILABLE:
            pytest.skip("openpyxl not available")

        db_session = MagicMock()
        project = MagicMock()
        project.id = 1
        project.project_name = "Test Project"

        def mock_query_side_effect(model):
            query_mock = MagicMock()
            query_mock.order_by = MagicMock(return_value=query_mock)
            query_mock.filter = MagicMock(return_value=query_mock)
            query_mock.all = MagicMock(return_value=[])
            return query_mock

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = create_project_detail_excel(
            db_session, project, include_tasks=True, include_costs=False
        )

        assert isinstance(result, BytesIO)
        assert result.tell() > 0

    def test_create_project_detail_excel_with_costs(self):
        """Test creating Excel with costs."""
        from app.services.project_export_service import (
            create_project_detail_excel,
            OPENPYXL_AVAILABLE,
        )

        if not OPENPYXL_AVAILABLE:
            pytest.skip("openpyxl not available")

        db_session = MagicMock()
        project = MagicMock()
        project.id = 1
        project.project_name = "Test Project"

        def mock_query_side_effect(model):
            query_mock = MagicMock()
            query_mock.order_by = MagicMock(return_value=query_mock)
            query_mock.filter = MagicMock(return_value=query_mock)
            query_mock.all = MagicMock(return_value=[])
            return query_mock

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = create_project_detail_excel(
            db_session, project, include_tasks=False, include_costs=True
        )

        assert isinstance(result, BytesIO)
        assert result.tell() > 0

    def test_create_project_detail_excel_complete(self):
        """Test creating complete Excel with tasks and costs."""
        from app.services.project_export_service import (
            create_project_detail_excel,
            OPENPYXL_AVAILABLE,
        )

        if not OPENPYXL_AVAILABLE:
            pytest.skip("openpyxl not available")

        db_session = MagicMock()
        project = MagicMock()
        project.id = 1
        project.project_name = "Test Project"

        def mock_query_side_effect(model):
            query_mock = MagicMock()
            query_mock.order_by = MagicMock(return_value=query_mock)
            query_mock.filter = MagicMock(return_value=query_mock)
            query_mock.all = MagicMock(return_value=[])
            return query_mock

        db_session.query = Mock(side_effect=mock_query_side_effect)

        result = create_project_detail_excel(
            db_session, project, include_tasks=True, include_costs=True
        )

        assert isinstance(result, BytesIO)
        assert result.tell() > 0


class TestAddTasksSheet:
    """Test suite for add_tasks_sheet function."""

    def test_add_tasks_sheet_without_openpyxl(self):
        """Test adding tasks sheet without openpyxl."""
        from app.services.project_export_service import add_tasks_sheet

        wb = MagicMock()
        db_session = MagicMock()
        project_id = 1
        styles = {}

        with patch("app.services.project_export_service.OPENPYXL_AVAILABLE", False):
            add_tasks_sheet(wb, db_session, project_id, styles)

            assert not wb.create_sheet.called


class TestAddCostsSheet:
    """Test suite for add_costs_sheet function."""

    def test_add_costs_sheet_without_openpyxl(self):
        """Test adding costs sheet without openpyxl."""
        from app.services.project_export_service import add_costs_sheet

        wb = MagicMock()
        db_session = MagicMock()
        project_id = 1
        styles = {}

        with patch("app.services.project_export_service.OPENPYXL_AVAILABLE", False):
            add_costs_sheet(wb, db_session, project_id, styles)

            assert not wb.create_sheet.called
