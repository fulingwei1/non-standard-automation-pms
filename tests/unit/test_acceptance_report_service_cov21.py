# -*- coding: utf-8 -*-
"""第二十一批：验收报告服务单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

pytest.importorskip("app.services.acceptance_report_service")


@pytest.fixture
def mock_db():
    return MagicMock()


class TestGenerateReportNo:
    def test_generates_correct_format(self, mock_db):
        from app.services.acceptance_report_service import generate_report_no
        # Mock count query returning 0
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        with patch("app.services.acceptance_report_service.apply_like_filter",
                   return_value=mock_db.query.return_value.filter.return_value):
            result = generate_report_no(mock_db, "FAT")
        assert result.startswith("FAT-")
        assert result.endswith("-001")

    def test_generates_sequential_number(self, mock_db):
        from app.services.acceptance_report_service import generate_report_no
        mock_db.query.return_value.filter.return_value.scalar.return_value = 5
        with patch("app.services.acceptance_report_service.apply_like_filter",
                   return_value=mock_db.query.return_value.filter.return_value):
            result = generate_report_no(mock_db, "SAT")
        assert result.startswith("SAT-")
        assert result.endswith("-006")

    def test_different_report_types(self, mock_db):
        from app.services.acceptance_report_service import generate_report_no
        mock_db.query.return_value.filter.return_value.scalar.return_value = 0
        with patch("app.services.acceptance_report_service.apply_like_filter",
                   return_value=mock_db.query.return_value.filter.return_value):
            fat_no = generate_report_no(mock_db, "FAT")
            sat_no = generate_report_no(mock_db, "SAT")
        assert fat_no.startswith("FAT-")
        assert sat_no.startswith("SAT-")

    def test_report_no_length_format(self, mock_db):
        from app.services.acceptance_report_service import generate_report_no
        mock_db.query.return_value.filter.return_value.scalar.return_value = None
        with patch("app.services.acceptance_report_service.apply_like_filter",
                   return_value=mock_db.query.return_value.filter.return_value):
            result = generate_report_no(mock_db, "FINAL")
        # Should have format: TYPE-YYYYMMDD-NNN
        parts = result.split("-")
        assert len(parts) >= 3
        assert parts[0] == "FINAL"


class TestReportLabAvailability:
    def test_reportlab_flag(self):
        from app.services.acceptance_report_service import REPORTLAB_AVAILABLE
        # Just verify the flag exists and is boolean
        assert isinstance(REPORTLAB_AVAILABLE, bool)


class TestAcceptanceReportService:
    def test_import_service_ok(self):
        # Just ensure the module imports cleanly
        import app.services.acceptance_report_service as svc
        assert svc is not None

    def test_generate_report_no_handles_none_scalar(self, mock_db):
        from app.services.acceptance_report_service import generate_report_no
        mock_db.query.return_value.filter.return_value.scalar.return_value = None
        with patch("app.services.acceptance_report_service.apply_like_filter",
                   return_value=mock_db.query.return_value.filter.return_value):
            result = generate_report_no(mock_db, "FAT")
        assert "-001" in result
