# -*- coding: utf-8 -*-
"""
Tests for acceptance_report_service
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from sqlalchemy.orm import Session

from app.models.acceptance import AcceptanceIssue, AcceptanceOrder, AcceptanceReport
from app.models.user import User


class TestGenerateReportNo:
    """Test suite for generate_report_no function."""

    def test_generate_fat_report_no(self):
        """Test generating FAT report number."""
        from app.services.acceptance_report_service import generate_report_no, REPORTLAB_AVAILABLE

        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab not available")

        db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.scalar = Mock(return_value=3)

        db.query = Mock(return_value=mock_query)

        result = generate_report_no(db, "FAT")

        assert result.startswith("FAT-")

    def test_generate_sat_report_no(self):
        """Test generating SAT report number."""
        from app.services.acceptance_report_service import generate_report_no, REPORTLAB_AVAILABLE

        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab not available")

        db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.scalar = Mock(return_value=0)

        db.query = Mock(return_value=mock_query)

        result = generate_report_no(db, "SAT")

        assert result.startswith("SAT-")
        assert result.endswith("-001")


class TestGetReportVersion:
    """Test suite for get_report_version function."""

    def test_get_report_version_new_report(self):
        """Test getting version for new report."""
        from app.services.acceptance_report_service import get_report_version, REPORTLAB_AVAILABLE

        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab not available")

        db = Mock(spec=Session)
        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=None)

        db.query = Mock(return_value=mock_query)

        result = get_report_version(db, 1, "FAT")

        assert result == 1

    def test_get_report_version_existing_report(self):
        """Test getting version for existing report."""
        from app.services.acceptance_report_service import get_report_version, REPORTLAB_AVAILABLE

        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab not available")

        db = Mock(spec=Session)
        mock_report = Mock()
        mock_report.version = 3

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.order_by = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=mock_report)

        db.query = Mock(return_value=mock_query)

        result = get_report_version(db, 1, "FAT")

        assert result == 4


class TestBuildReportContent:
    """Test suite for build_report_content function."""

    @pytest.fixture
    def mock_order(self):
        """Create mock order."""
        order = Mock(spec=AcceptanceOrder)
        order.id = 1
        order.project_name = "测试项目"
        order.machine_name = "测试设备"

        mock_project = Mock()
        mock_project.project_name = "测试项目"
        order.project = mock_project

        return order

    @pytest.fixture
    def mock_user(self):
        """Create mock user."""
        user = Mock(spec=User)
        user.id = 1
        user.real_name = "张三"
        user.username = "zhangsan"
        return user

    def test_build_report_content_basic(self, mock_order):
        """Test building report content with basic info."""
        from app.services.acceptance_report_service import build_report_content, REPORTLAB_AVAILABLE

        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab not available")

        db = Mock(spec=Session)

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.scalar = Mock(return_value=5)

        db.query = Mock(return_value=mock_query)

        result = build_report_content(db, mock_order, "FAT-001", 1, None)

        assert isinstance(result, str)
        assert "5" in result

    def test_build_report_content_with_qa_signer(self, mock_order, mock_user):
        """Test building report content with QA signer."""
        from app.services.acceptance_report_service import build_report_content, REPORTLAB_AVAILABLE

        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab not available")

        db = Mock(spec=Session)
        mock_order.qa_signer_id = 1

        mock_query = Mock()
        mock_query.filter = Mock(return_value=mock_query)
        mock_query.first = Mock(return_value=mock_user)

        db.query = Mock(return_value=mock_query)

        result = build_report_content(db, mock_order, "FAT-001", 1, mock_user)

        assert isinstance(result, str)
        assert "张三" in result or "zhangsan" in result

    def test_build_report_content_without_project(self, mock_order):
        """Test building report content without project."""
        from app.services.acceptance_report_service import build_report_content, REPORTLAB_AVAILABLE

        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab not available")

        db = Mock(spec=Session)
        mock_order.project = None

        result = build_report_content(db, mock_order, "FAT-001", 1, None)

        assert isinstance(result, str)

    def test_build_report_content_without_machine(self, mock_order):
        """Test building report content without machine."""
        from app.services.acceptance_report_service import build_report_content, REPORTLAB_AVAILABLE

        if not REPORTLAB_AVAILABLE:
            pytest.skip("reportlab not available")

        db = Mock(spec=Session)
        mock_order.machine = None

        result = build_report_content(db, mock_order, "FAT-001", 1, None)

        assert isinstance(result, str)
