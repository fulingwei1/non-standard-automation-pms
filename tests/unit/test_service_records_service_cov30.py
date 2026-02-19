# -*- coding: utf-8 -*-
"""
Unit tests for ServiceRecordsService (第三十批)
"""
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.services.service.service_records_service import ServiceRecordsService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def service(mock_db):
    return ServiceRecordsService(db=mock_db)


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.username = "tech01"
    return user


# ---------------------------------------------------------------------------
# get_record_statistics
# ---------------------------------------------------------------------------

class TestGetRecordStatistics:
    def test_returns_statistics_no_filters(self, service, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.count.return_value = 10
        mock_query.filter.return_value = mock_query

        # type_stats
        type_stat = MagicMock()
        type_stat.service_type = "repair"
        type_stat.count = 10
        mock_query.with_entities.return_value.group_by.return_value.all.return_value = [type_stat]

        # status_stats (second call via chaining)
        status_stat = MagicMock()
        status_stat.status = "completed"
        status_stat.count = 6

        # Make with_entities chain return different things on consecutive calls
        call_count = [0]
        def with_entities_side_effect(*args):
            call_count[0] += 1
            mock_chain = MagicMock()
            if call_count[0] == 1:
                mock_chain.group_by.return_value.all.return_value = [type_stat]
            else:
                mock_chain.group_by.return_value.all.return_value = [status_stat]
            return mock_chain

        mock_query.with_entities.side_effect = with_entities_side_effect

        # completed records for duration
        completed_record = MagicMock()
        completed_record.start_time = datetime(2024, 1, 1, 8, 0, 0)
        completed_record.end_time = datetime(2024, 1, 1, 10, 0, 0)
        mock_query.filter.return_value.all.return_value = [completed_record]

        result = service.get_record_statistics()

        assert "total_records" in result
        assert "type_distribution" in result
        assert "status_distribution" in result
        assert "average_service_duration_hours" in result

    def test_returns_zero_avg_duration_when_no_completed(self, service, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.all.return_value = []

        call_count = [0]
        def with_entities_side_effect(*args):
            call_count[0] += 1
            mock_chain = MagicMock()
            mock_chain.group_by.return_value.all.return_value = []
            return mock_chain

        mock_query.with_entities.side_effect = with_entities_side_effect

        result = service.get_record_statistics()
        assert result["average_service_duration_hours"] == 0
        assert result["total_records"] == 0

    def test_completion_rate_zero_when_no_records(self, service, mock_db):
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.count.return_value = 0
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value.all.return_value = []

        mock_query.with_entities.return_value.group_by.return_value.all.return_value = []

        result = service.get_record_statistics()
        assert result["completion_rate"] == 0


# ---------------------------------------------------------------------------
# get_service_records
# ---------------------------------------------------------------------------

class TestGetServiceRecords:
    @patch("app.services.service.service_records_service.ServiceRecord")
    @patch("app.services.service.service_records_service.joinedload")
    @patch("app.services.service.service_records_service.apply_keyword_filter")
    @patch("app.services.service.service_records_service.apply_pagination")
    @patch("app.services.service.service_records_service.get_pagination_params")
    def test_returns_paginated_list(self, mock_params, mock_apag, mock_kw, mock_jl, mock_sr, service, mock_db):
        mock_params.return_value = MagicMock(
            page=1, page_size=20, offset=0, limit=20,
            pages_for_total=lambda t: 1
        )
        mock_jl.return_value = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_kw.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 1
        mock_apag.return_value = mock_query

        record = MagicMock()
        mock_query.all.return_value = [record]

        with patch("app.services.service.service_records_service.ServiceRecordResponse.model_validate") as mv:
            mv.return_value = MagicMock()
            result = service.get_service_records(page=1, page_size=20)

        assert result.total == 1

    @patch("app.services.service.service_records_service.ServiceRecord")
    @patch("app.services.service.service_records_service.joinedload")
    @patch("app.services.service.service_records_service.apply_keyword_filter")
    @patch("app.services.service.service_records_service.apply_pagination")
    @patch("app.services.service.service_records_service.get_pagination_params")
    def test_filters_by_status(self, mock_params, mock_apag, mock_kw, mock_jl, mock_sr, service, mock_db):
        mock_params.return_value = MagicMock(
            page=1, page_size=20, offset=0, limit=20,
            pages_for_total=lambda t: 0
        )
        mock_jl.return_value = MagicMock()
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.options.return_value = mock_query
        mock_kw.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.count.return_value = 0
        mock_apag.return_value = mock_query
        mock_query.all.return_value = []

        result = service.get_service_records(status="completed")
        assert result.total == 0


# ---------------------------------------------------------------------------
# create_service_record
# ---------------------------------------------------------------------------

class TestCreateServiceRecord:
    @patch("app.services.service.service_records_service.save_obj")
    @patch("app.services.service.service_records_service.ServiceRecord")
    def test_creates_record_with_defaults(self, mock_sr_cls, mock_save, service, mock_user, mock_db):
        mock_record = MagicMock()
        mock_sr_cls.return_value = mock_record

        record_data = MagicMock()
        record_data.ticket_id = 10
        record_data.title = "Test Record"
        record_data.description = "desc"
        record_data.service_type = "repair"
        record_data.service_date = None
        record_data.start_time = None
        record_data.end_time = None
        record_data.location = "site A"
        record_data.technician_id = None
        record_data.work_summary = "done"
        record_data.parts_used = []
        record_data.next_actions = None
        record_data.customer_feedback = None
        record_data.status = None

        result = service.create_service_record(record_data, mock_user)
        mock_save.assert_called_once()
        assert result is not None


# ---------------------------------------------------------------------------
# upload_record_photos
# ---------------------------------------------------------------------------

class TestUploadRecordPhotos:
    def test_raises_404_when_record_not_found(self, service, mock_db, mock_user):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            service.upload_record_photos(999, [], mock_user)
        assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# delete_record_photo
# ---------------------------------------------------------------------------

class TestDeleteRecordPhoto:
    def test_raises_404_when_record_not_found(self, service, mock_db, mock_user):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            service.delete_record_photo(999, 0, mock_user)

    def test_raises_400_when_photo_index_out_of_range(self, service, mock_db, mock_user):
        record = MagicMock()
        record.photos = []
        mock_db.query.return_value.filter.return_value.first.return_value = record

        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            service.delete_record_photo(1, 5, mock_user)
        assert exc.value.status_code == 400
