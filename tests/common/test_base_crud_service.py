# -*- coding: utf-8 -*-
"""Tests for BaseCRUDService (sync, with QueryParams/PaginatedResult)"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.common.crud.types import QueryParams, PaginatedResult, SortOrder


# ---------------------------------------------------------------------------
# Fake model & schemas
# ---------------------------------------------------------------------------
class FakeModel:
    __name__ = "FakeModel"
    id = MagicMock()
    name = MagicMock()
    status = MagicMock()
    deleted_at = MagicMock()
    created_at = MagicMock()

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class FakeCreate(BaseModel):
    name: str
    status: str = "active"


class FakeUpdate(BaseModel):
    name: str | None = None
    status: str | None = None


class FakeResponse(BaseModel):
    id: int
    name: str
    status: str = "active"

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_service(db=None):
    from app.common.crud.base_crud_service import BaseCRUDService

    db = db or MagicMock(spec=Session)
    svc = BaseCRUDService(
        model=FakeModel,
        db=db,
        response_schema=FakeResponse,
        resource_name="FakeModel",
    )
    return svc, db


# ---------------------------------------------------------------------------
# Tests: Init
# ---------------------------------------------------------------------------
class TestBaseCRUDServiceInit:
    def test_defaults(self):
        svc, _ = _make_service()
        assert svc.resource_name == "FakeModel"
        assert svc.default_sort_field == "created_at"
        assert svc.soft_delete_field == "deleted_at"

    def test_with_default_filters(self):
        from app.common.crud.base_crud_service import BaseCRUDService

        db = MagicMock(spec=Session)
        svc = BaseCRUDService(
            model=FakeModel,
            db=db,
            response_schema=FakeResponse,
            default_filters={"tenant_id": 1},
        )
        assert svc._default_filters == {"tenant_id": 1}


# ---------------------------------------------------------------------------
# Tests: Get
# ---------------------------------------------------------------------------
class TestGet:
    def test_get_found(self):
        svc, _ = _make_service()
        fake_obj = FakeModel(id=1, name="test", status="active")
        svc.repository = MagicMock()
        svc.repository.get.return_value = fake_obj

        result = svc.get(1)
        assert result.id == 1
        assert result.name == "test"

    def test_get_not_found(self):
        svc, _ = _make_service()
        svc.repository = MagicMock()
        svc.repository.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            svc.get(999)
        assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# Tests: List
# ---------------------------------------------------------------------------
class TestList:
    def test_list_default_params(self):
        svc, _ = _make_service()
        fake_items = [FakeModel(id=1, name="a", status="active")]
        svc.repository = MagicMock()
        svc.repository.list.return_value = (fake_items, 1)

        result = svc.list()
        assert isinstance(result, PaginatedResult)
        assert result.total == 1
        assert len(result.items) == 1

    def test_list_with_params(self):
        svc, _ = _make_service()
        svc.repository = MagicMock()
        svc.repository.list.return_value = ([], 0)

        params = QueryParams(page=2, page_size=10, search="test")
        result = svc.list(params)
        assert result.total == 0
        assert result.page == 2

    def test_list_include_deleted(self):
        svc, _ = _make_service()
        svc.repository = MagicMock()
        svc.repository.list.return_value = ([], 0)

        params = QueryParams(include_deleted=True)
        result = svc.list(params)
        # Should not include soft_delete_field filter
        call_kwargs = svc.repository.list.call_args[1]
        filters = call_kwargs.get("filters")
        if filters:
            assert "deleted_at" not in filters

    def test_list_extra_filters(self):
        svc, _ = _make_service()
        svc.repository = MagicMock()
        svc.repository.list.return_value = ([], 0)

        result = svc.list(extra_filters={"status": "active"})
        call_kwargs = svc.repository.list.call_args[1]
        assert call_kwargs["filters"]["status"] == "active"


# ---------------------------------------------------------------------------
# Tests: Count
# ---------------------------------------------------------------------------
class TestCount:
    def test_count(self):
        svc, _ = _make_service()
        svc.repository = MagicMock()
        svc.repository.count.return_value = 42

        assert svc.count() == 42


# ---------------------------------------------------------------------------
# Tests: Create
# ---------------------------------------------------------------------------
class TestCreate:
    @patch("app.common.crud.base_crud_service.BaseCRUDService._log_audit")
    def test_create_basic(self, mock_audit):
        svc, _ = _make_service()
        fake_obj = FakeModel(id=1, name="new", status="active")
        svc.repository = MagicMock()
        svc.repository.create.return_value = fake_obj
        svc.repository.get_by_field.return_value = None

        result = svc.create(FakeCreate(name="new"))
        assert result.id == 1
        assert result.name == "new"

    @patch("app.common.crud.base_crud_service.BaseCRUDService._log_audit")
    def test_create_with_unique_check_dict(self, mock_audit):
        svc, _ = _make_service()
        svc.repository = MagicMock()
        # Simulate existing record
        existing = FakeModel(id=2, name="dup")
        svc.repository.get_by_field.return_value = existing

        with pytest.raises(HTTPException) as exc_info:
            svc.create(FakeCreate(name="dup"), check_unique={"name": "dup"})
        assert exc_info.value.status_code == 409

    @patch("app.common.crud.base_crud_service.BaseCRUDService._log_audit")
    def test_create_status_change_hook(self, mock_audit):
        svc, _ = _make_service()
        fake_obj = FakeModel(id=1, name="new", status="pending")
        svc.repository = MagicMock()
        svc.repository.create.return_value = fake_obj
        svc.repository.get_by_field.return_value = None

        with patch.object(svc, "_on_status_change") as mock_hook:
            svc.create(FakeCreate(name="new", status="pending"))
            mock_hook.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: Bulk Create
# ---------------------------------------------------------------------------
class TestBulkCreate:
    def test_bulk_create(self):
        svc, _ = _make_service()
        objs = [
            FakeModel(id=1, name="a", status="active"),
            FakeModel(id=2, name="b", status="active"),
        ]
        svc.repository = MagicMock()
        svc.repository.create_many.return_value = objs

        results = svc.bulk_create([FakeCreate(name="a"), FakeCreate(name="b")])
        assert len(results) == 2


# ---------------------------------------------------------------------------
# Tests: Update
# ---------------------------------------------------------------------------
class TestUpdate:
    @patch("app.common.crud.base_crud_service.BaseCRUDService._log_audit")
    def test_update_basic(self, mock_audit):
        svc, _ = _make_service()
        fake_obj = FakeModel(id=1, name="old", status="active")
        updated_obj = FakeModel(id=1, name="new", status="active")
        svc.repository = MagicMock()
        svc.repository.get.return_value = fake_obj
        svc.repository.update.return_value = updated_obj
        svc.repository.get_by_field.return_value = None

        result = svc.update(1, FakeUpdate(name="new"))
        assert result.name == "new"

    @patch("app.common.crud.base_crud_service.BaseCRUDService._log_audit")
    def test_update_not_found(self, mock_audit):
        svc, _ = _make_service()
        svc.repository = MagicMock()
        svc.repository.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            svc.update(999, FakeUpdate(name="x"))
        assert exc_info.value.status_code == 404

    @patch("app.common.crud.base_crud_service.BaseCRUDService._log_audit")
    def test_update_status_change(self, mock_audit):
        svc, _ = _make_service()
        fake_obj = FakeModel(id=1, name="x", status="draft")
        updated_obj = FakeModel(id=1, name="x", status="active")
        svc.repository = MagicMock()
        svc.repository.get.return_value = fake_obj
        svc.repository.update.return_value = updated_obj
        svc.repository.get_by_field.return_value = None

        with patch.object(svc, "_on_status_change") as mock_hook:
            svc.update(1, FakeUpdate(status="active"))
            mock_hook.assert_called_once_with(updated_obj, "draft", "active")

    @patch("app.common.crud.base_crud_service.BaseCRUDService._log_audit")
    def test_update_unique_conflict(self, mock_audit):
        svc, _ = _make_service()
        svc.unique_fields = ("name",)
        fake_obj = FakeModel(id=1, name="old", status="active")
        existing = FakeModel(id=2, name="taken")
        svc.repository = MagicMock()
        svc.repository.get.return_value = fake_obj
        svc.repository.get_by_field.return_value = existing

        with pytest.raises(HTTPException) as exc_info:
            svc.update(1, FakeUpdate(name="taken"))
        assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# Tests: Delete
# ---------------------------------------------------------------------------
class TestDelete:
    def test_delete_basic(self):
        svc, _ = _make_service()
        svc.repository = MagicMock()
        svc.repository.exists.return_value = True
        svc.repository.delete.return_value = True

        result = svc.delete(1)
        assert result is True

    def test_delete_not_found(self):
        svc, _ = _make_service()
        svc.repository = MagicMock()
        svc.repository.exists.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            svc.delete(999)
        assert exc_info.value.status_code == 404

    def test_delete_soft(self):
        svc, _ = _make_service()
        svc.repository = MagicMock()
        svc.repository.exists.return_value = True
        svc.repository.delete.return_value = True

        result = svc.delete(1, soft_delete=True)
        assert result is True
        svc.repository.delete.assert_called_with(1, soft_delete=True)

    def test_delete_default_uses_soft_delete_field(self):
        svc, _ = _make_service()
        svc.soft_delete_field = "deleted_at"
        svc.repository = MagicMock()
        svc.repository.exists.return_value = True
        svc.repository.delete.return_value = True

        svc.delete(1)
        svc.repository.delete.assert_called_with(1, soft_delete=True)

    def test_delete_no_soft_delete_field(self):
        svc, _ = _make_service()
        svc.soft_delete_field = None
        svc.repository = MagicMock()
        svc.repository.exists.return_value = True
        svc.repository.delete.return_value = True

        svc.delete(1)
        svc.repository.delete.assert_called_with(1, soft_delete=False)


# ---------------------------------------------------------------------------
# Tests: Bulk Delete
# ---------------------------------------------------------------------------
class TestBulkDelete:
    def test_bulk_delete(self):
        svc, _ = _make_service()
        svc.repository = MagicMock()
        svc.repository.exists.return_value = True
        svc.repository.delete.return_value = True

        count = svc.bulk_delete([1, 2, 3])
        assert count == 3


# ---------------------------------------------------------------------------
# Tests: Internal helpers
# ---------------------------------------------------------------------------
class TestMergeFilters:
    def test_default_soft_delete_filter(self):
        svc, _ = _make_service()
        params = QueryParams()
        filters = svc._merge_filters(params, None)
        assert "deleted_at" in filters
        assert filters["deleted_at"] == {"is_null": True}

    def test_include_deleted_skips_soft_delete_filter(self):
        svc, _ = _make_service()
        params = QueryParams(include_deleted=True)
        filters = svc._merge_filters(params, None)
        # When include_deleted=True, _merge_filters skips adding deleted_at filter
        assert "deleted_at" not in filters

    def test_extra_filters_merged(self):
        svc, _ = _make_service()
        params = QueryParams(filters={"status": "active"})
        filters = svc._merge_filters(params, {"tenant_id": 1})
        assert filters["status"] == "active"
        assert filters["tenant_id"] == 1

    def test_allowed_filter_fields(self):
        svc, _ = _make_service()
        svc.allowed_filter_fields = ["status"]
        params = QueryParams(filters={"status": "active", "name": "test"})
        filters = svc._merge_filters(params, None)
        assert "status" in filters
        assert "name" not in filters


class TestResolveSorting:
    def test_default_sorting(self):
        svc, _ = _make_service()
        params = QueryParams()
        field, order = svc._resolve_sorting(params)
        assert field == "created_at"
        assert order == SortOrder.DESC

    def test_custom_sorting(self):
        svc, _ = _make_service()
        params = QueryParams(sort_by="name", sort_order=SortOrder.ASC)
        field, order = svc._resolve_sorting(params)
        assert field == "name"
        assert order == SortOrder.ASC

    def test_disallowed_sort_field_falls_back(self):
        svc, _ = _make_service()
        svc.allowed_sort_fields = ["created_at", "name"]
        params = QueryParams(sort_by="secret_field")
        field, order = svc._resolve_sorting(params)
        assert field == "created_at"


class TestEnsureUnique:
    def test_unique_with_string(self):
        svc, _ = _make_service()
        svc.repository = MagicMock()
        svc.repository.get_by_field.return_value = None

        data = FakeCreate(name="unique")
        svc._ensure_unique("name", data=data)  # should not raise

    def test_unique_with_list(self):
        svc, _ = _make_service()
        svc.repository = MagicMock()
        svc.repository.get_by_field.return_value = None

        data = FakeCreate(name="unique")
        svc._ensure_unique(["name"], data=data)

    def test_unique_conflict(self):
        svc, _ = _make_service()
        svc.repository = MagicMock()
        existing = FakeModel(id=2, name="dup")
        svc.repository.get_by_field.return_value = existing

        with pytest.raises(HTTPException) as exc_info:
            svc._ensure_unique({"name": "dup"})
        assert exc_info.value.status_code == 409

    def test_unique_same_id_ok(self):
        svc, _ = _make_service()
        svc.repository = MagicMock()
        existing = FakeModel(id=1, name="dup")
        svc.repository.get_by_field.return_value = existing

        # Same ID should not raise
        svc._ensure_unique({"name": "dup"}, current_id=1)

    def test_unique_no_data_raises(self):
        svc, _ = _make_service()
        with pytest.raises(ValueError):
            svc._ensure_unique("name", data=None)

    def test_unique_none_fields(self):
        svc, _ = _make_service()
        svc._ensure_unique(None)  # should not raise


# ---------------------------------------------------------------------------
# Tests: Hooks
# ---------------------------------------------------------------------------
class TestHooks:
    def test_to_response(self):
        svc, _ = _make_service()
        obj = FakeModel(id=1, name="test", status="active")
        result = svc._to_response(obj)
        assert isinstance(result, FakeResponse)

    def test_to_response_no_schema(self):
        svc, _ = _make_service()
        svc.response_schema = None
        with pytest.raises(NotImplementedError):
            svc._to_response(FakeModel(id=1, name="x"))

    def test_before_after_hooks_passthrough(self):
        svc, _ = _make_service()
        schema = FakeCreate(name="x")
        assert svc._before_create(schema) is schema

        obj = FakeModel(id=1, name="x")
        assert svc._after_create(obj) is obj

        update = FakeUpdate(name="y")
        assert svc._before_update(1, update, obj) is update
        assert svc._after_update(obj) is obj

        assert svc._before_delete(1) is None
        assert svc._after_delete(1) is None

    def test_before_after_list_hooks(self):
        svc, _ = _make_service()
        params = QueryParams()
        assert svc._before_list(params) is params

        result = PaginatedResult(items=[], total=0, page=1, page_size=20)
        assert svc._after_list(result, params) is result
