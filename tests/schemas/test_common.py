# -*- coding: utf-8 -*-
"""Tests for app/schemas/common.py"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.common import (
    ResponseModel,
    PaginatedResponse,
    PageParams,
    IdResponse,
    MessageResponse,
    BatchOperationResponse,
    StatusUpdate,
    BaseSchema,
    TimestampSchema,
    AuditSchema,
    PageResponse,
)


class TestResponseModel:
    def test_defaults(self):
        r = ResponseModel()
        assert r.code == 200
        assert r.message == "success"
        assert r.data is None

    def test_with_data(self):
        r = ResponseModel(data={"key": "val"})
        assert r.data == {"key": "val"}

    def test_custom_code(self):
        r = ResponseModel(code=404, message="not found")
        assert r.code == 404

    def test_generic_int(self):
        r = ResponseModel[int](data=42)
        assert r.data == 42

    def test_generic_list(self):
        r = ResponseModel[list](data=[1, 2])
        assert r.data == [1, 2]


class TestPaginatedResponse:
    def test_defaults(self):
        p = PaginatedResponse()
        assert p.items == []
        assert p.total == 0
        assert p.page == 1
        assert p.page_size == 20
        assert p.pages == 0

    def test_with_items(self):
        p = PaginatedResponse(items=[1, 2, 3], total=3, page=1, page_size=10, pages=1)
        assert len(p.items) == 3

    def test_generic(self):
        p = PaginatedResponse[str](items=["a", "b"], total=2)
        assert p.items == ["a", "b"]


class TestPageParams:
    def test_defaults(self):
        p = PageParams()
        assert p.page == 1
        assert p.page_size == 20
        assert p.sort_order == "desc"

    def test_page_ge_1(self):
        with pytest.raises(ValidationError):
            PageParams(page=0)

    def test_page_size_ge_1(self):
        with pytest.raises(ValidationError):
            PageParams(page_size=0)

    def test_page_size_le_100(self):
        with pytest.raises(ValidationError):
            PageParams(page_size=101)

    def test_valid_page_size(self):
        p = PageParams(page_size=100)
        assert p.page_size == 100

    def test_sort_by(self):
        p = PageParams(sort_by="name", sort_order="asc")
        assert p.sort_by == "name"


class TestIdResponse:
    def test_valid(self):
        r = IdResponse(id=1)
        assert r.id == 1

    def test_missing_id(self):
        with pytest.raises(ValidationError):
            IdResponse()


class TestMessageResponse:
    def test_valid(self):
        r = MessageResponse(message="ok")
        assert r.message == "ok"

    def test_missing(self):
        with pytest.raises(ValidationError):
            MessageResponse()


class TestBatchOperationResponse:
    def test_valid(self):
        r = BatchOperationResponse(success_count=5, failed_count=1)
        assert r.success_count == 5
        assert r.failed_items == []

    def test_with_alias(self):
        r = BatchOperationResponse(success_count=3, failed_count=0, failed_tasks=[])
        assert r.failed_items == []

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            BatchOperationResponse()


class TestStatusUpdate:
    def test_valid(self):
        s = StatusUpdate(status="ACTIVE")
        assert s.status == "ACTIVE"
        assert s.remark is None

    def test_with_remark(self):
        s = StatusUpdate(status="CLOSED", remark="done")
        assert s.remark == "done"

    def test_missing(self):
        with pytest.raises(ValidationError):
            StatusUpdate()


class TestTimestampSchema:
    def test_defaults(self):
        t = TimestampSchema()
        assert t.created_at is None
        assert t.updated_at is None

    def test_with_dates(self):
        now = datetime.now()
        t = TimestampSchema(created_at=now, updated_at=now)
        assert t.created_at == now


class TestAuditSchema:
    def test_defaults(self):
        a = AuditSchema()
        assert a.created_by is None
        assert a.created_by_name is None

    def test_with_audit(self):
        a = AuditSchema(created_by=1, created_by_name="admin")
        assert a.created_by == 1


class TestPageResponse:
    def test_defaults(self):
        p = PageResponse()
        assert p.items == []
        assert p.skip == 0
        assert p.limit == 20

    def test_with_data(self):
        p = PageResponse(items=[1], total=1, skip=0, limit=10)
        assert p.total == 1
