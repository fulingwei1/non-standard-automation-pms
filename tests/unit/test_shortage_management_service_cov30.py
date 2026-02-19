# -*- coding: utf-8 -*-
"""
Unit tests for ShortageManagementService (第三十批)
"""
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.shortage.shortage_management_service import ShortageManagementService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return ShortageManagementService(db=mock_db)


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 5
    user.username = "reporter01"
    return user


# ---------------------------------------------------------------------------
# get_shortage_list
# ---------------------------------------------------------------------------

class TestGetShortageList:
    @patch("app.services.shortage.shortage_management_service.apply_keyword_filter")
    @patch("app.services.shortage.shortage_management_service.apply_pagination")
    @patch("app.services.shortage.shortage_management_service.get_pagination_params")
    def test_returns_paginated_list(self, mock_params, mock_apag, mock_kw, service, mock_db):
        mock_params.return_value = MagicMock(
            page=1, page_size=20, offset=0, limit=20,
            pages_for_total=lambda t: 1
        )
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_kw.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_apag.return_value = mock_query

        record = MagicMock()
        record.id = 1
        record.report_no = "SR20240101001"
        record.project_id = None
        record.material_id = None
        record.material_code = "MAT001"
        record.material_name = "零件A"
        record.required_qty = Decimal("10")
        record.shortage_qty = Decimal("5")
        record.urgent_level = "HIGH"
        record.status = "REPORTED"
        record.reporter_id = None
        record.report_time = None
        record.solution_type = None
        record.created_at = None
        mock_query.all.return_value = [record]

        result = service.get_shortage_list(page=1, page_size=20)
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0]["material_code"] == "MAT001"

    @patch("app.services.shortage.shortage_management_service.apply_keyword_filter")
    @patch("app.services.shortage.shortage_management_service.apply_pagination")
    @patch("app.services.shortage.shortage_management_service.get_pagination_params")
    def test_filter_by_status(self, mock_params, mock_apag, mock_kw, service, mock_db):
        mock_params.return_value = MagicMock(
            page=1, page_size=20, offset=0, limit=20,
            pages_for_total=lambda t: 0
        )
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_kw.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.order_by.return_value = mock_query
        mock_apag.return_value = mock_query
        mock_query.all.return_value = []

        result = service.get_shortage_list(status="RESOLVED")
        assert result.total == 0
        assert result.items == []

    @patch("app.services.shortage.shortage_management_service.apply_keyword_filter")
    @patch("app.services.shortage.shortage_management_service.apply_pagination")
    @patch("app.services.shortage.shortage_management_service.get_pagination_params")
    def test_with_project_name_lookup(self, mock_params, mock_apag, mock_kw, service, mock_db):
        mock_params.return_value = MagicMock(
            page=1, page_size=20, offset=0, limit=20,
            pages_for_total=lambda t: 1
        )
        mock_query = MagicMock()
        mock_kw.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 1
        mock_query.order_by.return_value = mock_query
        mock_apag.return_value = mock_query

        record = MagicMock()
        record.id = 2
        record.report_no = "SR20240102001"
        record.project_id = 10
        record.material_id = None
        record.material_code = "MAT002"
        record.material_name = "零件B"
        record.required_qty = Decimal("20")
        record.shortage_qty = Decimal("10")
        record.urgent_level = "NORMAL"
        record.status = "REPORTED"
        record.reporter_id = None
        record.report_time = None
        record.solution_type = None
        record.created_at = None
        mock_query.all.return_value = [record]

        project = MagicMock()
        project.project_name = "示例项目"

        def db_query_side_effect(model):
            from app.models.shortage import ShortageReport
            if model is ShortageReport:
                return mock_query
            inner = MagicMock()
            inner.filter.return_value.first.return_value = project
            return inner

        mock_db.query.side_effect = db_query_side_effect

        result = service.get_shortage_list(project_id=10)
        assert result.total == 1


# ---------------------------------------------------------------------------
# create_shortage_record
# ---------------------------------------------------------------------------

class TestCreateShortageRecord:
    @patch("app.services.shortage.shortage_management_service.save_obj")
    def test_returns_error_when_material_not_found(self, mock_save, service, mock_db, mock_user):
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        mock_db.query.return_value.filter.return_value.first.return_value = None

        data = {"material_id": 999, "required_qty": 10, "shortage_qty": 5}
        result = service.create_shortage_record(data, mock_user)
        assert result["success"] is False
        assert "物料不存在" in result["message"]
        mock_save.assert_not_called()

    @patch("app.services.shortage.shortage_management_service.save_obj")
    def test_creates_record_successfully(self, mock_save, service, mock_db, mock_user):
        material = MagicMock()
        material.id = 1
        material.material_code = "MAT001"
        material.material_name = "零件A"

        call_count = [0]
        def query_side_effect(model):
            call_count[0] += 1
            inner = MagicMock()
            if call_count[0] == 1:
                # count query for report_no generation
                inner.filter.return_value.count.return_value = 0
            else:
                inner.filter.return_value.first.return_value = material
            return inner

        mock_db.query.side_effect = query_side_effect

        data = {
            "material_id": 1,
            "required_qty": 10,
            "shortage_qty": 5,
            "urgent_level": "HIGH",
            "project_id": 2,
        }
        result = service.create_shortage_record(data, mock_user)
        assert result["success"] is True
        mock_save.assert_called_once()


# ---------------------------------------------------------------------------
# get_shortage_statistics
# ---------------------------------------------------------------------------

class TestGetShortageStatistics:
    def test_returns_statistics_dict(self, service, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.group_by.return_value.all.return_value = [("REPORTED", 3), ("RESOLVED", 2)]
        mock_query.order_by.return_value.all.return_value = []

        result = service.get_shortage_statistics()
        assert "total_count" in result
        assert "pending_count" in result
        assert "resolved_count" in result
        assert "by_status" in result
        assert "by_urgent_level" in result
        assert "daily_trend" in result

    def test_returns_statistics_with_project_filter(self, service, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 2

        def group_by_side(*args):
            inner = MagicMock()
            inner.all.return_value = []
            return inner

        mock_query.group_by.side_effect = group_by_side
        mock_query.order_by.return_value.all.return_value = []

        result = service.get_shortage_statistics(project_id=10)
        assert result["total_count"] == 2
