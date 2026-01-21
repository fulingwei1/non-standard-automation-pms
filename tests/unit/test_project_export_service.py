# -*- coding: utf-8 -*-
"""
Tests for project_export_service service
Covers: app/services/project_export_service.py
Coverage Target: 0% → 60%+
Current Coverage: 0%
Batch: P4 - Services Layer 核心模块测试扩展
"""

from datetime import date
from io import BytesIO
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.models.project import Project


class TestGetExcelStyles:
    """Test suite for get_excel_styles function."""

    def test_get_excel_styles_with_openpyxl(self):
        """Test getting styles when openpyxl is available."""
        from app.services.project_export_service import get_excel_styles

        styles = get_excel_styles()

        assert isinstance(styles, dict)
        assert "header_fill" in styles
        assert "header_font" in styles
        assert "title_font" in styles
        assert "border" in styles

    def test_get_excel_styles_without_openpyxl(self):
        """Test getting styles when openpyxl is not available."""
        with patch("app.services.project_export_service.OPENPYXL_AVAILABLE", False):
            from app.services.project_export_service import get_excel_styles

            styles = get_excel_styles()

            assert styles == {}


class TestBuildProjectInfoData:
    """Test suite for build_project_info_data function."""

    def test_build_project_info_data_complete(self):
        """Test building project info with complete data."""
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

        from app.services.project_export_service import build_project_info_data

        result = build_project_info_data(project)

        assert len(result) == 13
        assert result[0] == ("项目编码", "PJ250101001")
        assert result[1] == ("项目名称", "测试项目")
        assert result[4] == ("合同金额", "100,000.00")
        assert result[9] == ("进度(%)", "50.50")

    def test_build_project_info_data_with_nulls(self):
        """Test building project info with null values."""
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

        from app.services.project_export_service import build_project_info_data

        result = build_project_info_data(project)

        assert len(result) == 13
        for label, value in result:
            assert value == "" or value == "0.00"


class TestAddProjectInfoSheet:
    """Test suite for add_project_info_sheet function."""

    def test_add_project_info_sheet_without_openpyxl(self):
        """Test adding sheet without openpyxl."""
        from app.services.project_export_service import add_project_info_sheet

        ws = MagicMock()
        project = MagicMock(spec=Project)
        styles = {}

        # Should return early without raising error
        add_project_info_sheet(ws, project, styles)

        ws.__getitem__.assert_not_called()

    def test_add_project_info_sheet_with_openpyxl(self):
        """Test adding sheet with openpyxl available."""
        from app.services.project_export_service import add_project_info_sheet

        ws = MagicMock()
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

        # Mock Excel operations
        ws.__getitem__ = MagicMock(side_effect=lambda x: MagicMock())

        add_project_info_sheet(ws, project, styles)

        # Verify that sheet operations were called
        assert ws.merge_cells.called or ws.__getitem__.called


class TestExportProjectToExcel:
    """Test suite for export_project_to_excel function."""

    def test_export_project_to_excel_success(self):
        """Test successful export to Excel."""
        from app.services.project_export_service import export_project_to_excel

        project = MagicMock(spec=Project)
        project.id = 1
        project.project_code = "PJ001"
        project.project_name = "测试项目"

        result = export_project_to_excel(project)

        assert result is not None
        assert isinstance(result, BytesIO)

    def test_export_project_to_excel_without_openpyxl(self):
        """Test export when openpyxl is not available."""
        with patch("app.services.project_export_service.OPENPYXL_AVAILABLE", False):
            from app.services.project_export_service import export_project_to_excel

            project = MagicMock(spec=Project)

            result = export_project_to_excel(project)

            # Should handle gracefully (return None or raise appropriate error)
            assert result is None


class TestExportProjectsToExcel:
    """Test suite for export_projects_to_excel function."""

    def test_export_projects_to_excel_single_project(self, db_session: Session):
        """Test exporting a single project."""
        from app.services.project_export_service import export_projects_to_excel

        project = Project(
            project_code="PJ001",
            project_name="测试项目",
            stage="S1",
            status="ST01",
            health="H1",
            progress_pct=20,
        )
        db_session.add(project)
        db_session.commit()

        result = export_projects_to_excel([project])

        assert result is not None
        assert isinstance(result, BytesIO)

    def test_export_projects_to_excel_multiple_projects(self, db_session: Session):
        """Test exporting multiple projects."""
        from app.services.project_export_service import export_projects_to_excel

        projects = [
            Project(
                project_code="PJ001",
                project_name="项目A",
                stage="S1",
                status="ST01",
                health="H1",
                progress_pct=20,
            ),
            Project(
                project_code="PJ002",
                project_name="项目B",
                stage="S2",
                status="ST03",
                health="H2",
                progress_pct=40,
            ),
            Project(
                project_code="PJ003",
                project_name="项目C",
                stage="S3",
                status="ST08",
                health="H1",
                progress_pct=60,
            ),
        ]
        db_session.add_all(projects)
        db_session.commit()

        result = export_projects_to_excel(projects)

        assert result is not None
        assert isinstance(result, BytesIO)

    def test_export_projects_to_excel_empty_list(self):
        """Test exporting empty project list."""
        from app.services.project_export_service import export_projects_to_excel

        result = export_projects_to_excel([])

        # Should handle empty list gracefully
        assert result is not None
