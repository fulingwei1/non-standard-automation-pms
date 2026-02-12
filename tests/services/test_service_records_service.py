# -*- coding: utf-8 -*-
"""服务记录服务单元测试"""
import pytest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from app.models.service import ServiceRecord

# Patch relationship attributes used in joinedload()
for _attr in ('ticket', 'technician', 'created_by_user'):
    if not hasattr(ServiceRecord, _attr):
        setattr(ServiceRecord, _attr, MagicMock())

from app.services.service.service_records_service import ServiceRecordsService


def _make_db():
    return MagicMock()


def _make_user(uid=1):
    u = MagicMock()
    u.id = uid
    return u


class TestGetRecordStatistics:
    def test_basic(self):
        db = _make_db()
        q = db.query.return_value
        q.count.return_value = 5
        q.with_entities.return_value.group_by.return_value.all.return_value = []
        q.filter.return_value.all.return_value = []
        q.filter.return_value.count.return_value = 5
        q.filter.return_value.with_entities.return_value.group_by.return_value.all.return_value = []
        svc = ServiceRecordsService(db)
        result = svc.get_record_statistics()
        assert "total_records" in result
        assert "completion_rate" in result

    def test_with_filters(self):
        db = _make_db()
        q = db.query.return_value
        q.filter.return_value = q
        q.count.return_value = 0
        q.with_entities.return_value.group_by.return_value.all.return_value = []
        q.filter.return_value.all.return_value = []
        svc = ServiceRecordsService(db)
        # ServiceRecord model lacks technician_id; patch it as a mock column
        from app.models.service.record import ServiceRecord
        with patch.object(ServiceRecord, "technician_id", create=True, new=MagicMock()):
            result = svc.get_record_statistics(
                start_date=date(2025, 1, 1), end_date=date(2025, 12, 31), technician_id=1
            )
        assert result["total_records"] == 0


class TestGetServiceRecords:
    def test_list(self):
        db = _make_db()
        q = db.query.return_value.options.return_value
        for attr in ('filter', 'order_by'):
            setattr(q, attr, MagicMock(return_value=q))
        q.count.return_value = 0
        q.all.return_value = []

        with patch("app.services.service.service_records_service.joinedload", lambda *a, **k: MagicMock()), \
             patch("app.services.service.service_records_service.apply_keyword_filter", return_value=q), \
             patch("app.services.service.service_records_service.get_pagination_params") as gpp, \
             patch("app.services.service.service_records_service.apply_pagination", return_value=q):
            pag = MagicMock(page=1, page_size=20, offset=0, limit=20)
            pag.pages_for_total.return_value = 0
            gpp.return_value = pag
            svc = ServiceRecordsService(db)
            result = svc.get_service_records()
            assert result.total == 0


class TestCreateServiceRecord:
    def test_create(self):
        db = _make_db()
        record_data = MagicMock(
            ticket_id=1, title="维修记录", description="desc",
            service_type="repair", service_date=date(2025, 5, 1),
            start_time=datetime(2025, 5, 1, 9), end_time=datetime(2025, 5, 1, 17),
            location="现场", technician_id=1, work_summary="完成",
            parts_used="螺栓x10", next_actions="无", customer_feedback="好",
            status="in_progress"
        )
        svc = ServiceRecordsService(db)
        with patch("app.services.service.service_records_service.ServiceRecord") as MockRecord:
            instance = MagicMock()
            instance.ticket = None
            MockRecord.return_value = instance
            result = svc.create_service_record(record_data, _make_user())
        db.add.assert_called_once()
        db.commit.assert_called()


class TestUploadRecordPhotos:
    def test_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = ServiceRecordsService(db)
        with pytest.raises(HTTPException) as exc_info:
            svc.upload_record_photos(999, [], _make_user())
        assert exc_info.value.status_code == 404


class TestDeleteRecordPhoto:
    def test_not_found(self):
        db = _make_db()
        db.query.return_value.filter.return_value.first.return_value = None
        svc = ServiceRecordsService(db)
        with pytest.raises(HTTPException):
            svc.delete_record_photo(999, 0, _make_user())

    def test_invalid_index(self):
        db = _make_db()
        record = MagicMock(photos=[])
        db.query.return_value.filter.return_value.first.return_value = record
        svc = ServiceRecordsService(db)
        with pytest.raises(HTTPException):
            svc.delete_record_photo(1, 5, _make_user())
