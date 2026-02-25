# -*- coding: utf-8 -*-
"""Tests for crud types, exceptions, and query_filters"""

import pytest
from fastapi import HTTPException

from app.common.crud.types import QueryParams, PaginatedResult, SortOrder
from app.common.crud.exceptions import (
    CRUDException, NotFoundError, AlreadyExistsError, ValidationError,
    raise_not_found, raise_already_exists,
)


# ---------------------------------------------------------------------------
# SortOrder
# ---------------------------------------------------------------------------
class TestSortOrder:
    def test_values(self):
        assert SortOrder.ASC == "asc"
        assert SortOrder.DESC == "desc"


# ---------------------------------------------------------------------------
# QueryParams
# ---------------------------------------------------------------------------
class TestQueryParams:
    def test_defaults(self):
        p = QueryParams()
        assert p.page == 1
        assert p.page_size == 20
        assert p.skip == 0
        assert p.limit == 20
        assert p.sort_order == SortOrder.DESC

    def test_skip_calculation(self):
        p = QueryParams(page=3, page_size=10)
        assert p.skip == 20
        assert p.limit == 10

    def test_merged_filters(self):
        p = QueryParams(filters={"a": 1})
        merged = p.merged_filters({"b": 2})
        assert merged == {"a": 1, "b": 2}

    def test_merged_filters_empty(self):
        p = QueryParams()
        assert p.merged_filters() == {}

    def test_sort_order_normalize(self):
        p = QueryParams(sort_order="ASC")
        assert p.sort_order == SortOrder.ASC

    def test_sort_order_invalid(self):
        with pytest.raises(Exception):
            QueryParams(sort_order="invalid")

    def test_search_fields(self):
        p = QueryParams(search="test", search_fields=["name", "code"])
        assert p.search == "test"
        assert p.search_fields == ["name", "code"]


# ---------------------------------------------------------------------------
# PaginatedResult
# ---------------------------------------------------------------------------
class TestPaginatedResult:
    def test_defaults(self):
        r = PaginatedResult()
        assert r.items == []
        assert r.total == 0
        assert r.pages == 0

    def test_pages_calculation(self):
        r = PaginatedResult(items=[], total=55, page=1, page_size=20)
        assert r.pages == 3

    def test_to_dict(self):
        r = PaginatedResult(items=["a", "b"], total=2, page=1, page_size=20)
        d = r.to_dict()
        assert d["items"] == ["a", "b"]
        assert d["total"] == 2
        assert d["pages"] == 1

    def test_single_page(self):
        r = PaginatedResult(total=5, page_size=10)
        assert r.pages == 1


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class TestExceptions:
    def test_not_found_error(self):
        e = NotFoundError("Project", 1)
        assert "Project" in str(e)
        assert e.resource_name == "Project"
        assert e.resource_id == 1

    def test_already_exists_error(self):
        e = AlreadyExistsError("Project", "code", "P001")
        assert "P001" in str(e)

    def test_validation_error(self):
        e = ValidationError("bad", {"field": "err"})
        assert e.message == "bad"
        assert e.errors == {"field": "err"}

    def test_raise_not_found(self):
        with pytest.raises(HTTPException) as exc:
            raise_not_found("Item", 42)
        assert exc.value.status_code == 404

    def test_raise_already_exists(self):
        with pytest.raises(HTTPException) as exc:
            raise_already_exists("Item", "code", "X")
        assert exc.value.status_code == 409

    def test_crud_exception_hierarchy(self):
        assert issubclass(NotFoundError, CRUDException)
        assert issubclass(AlreadyExistsError, CRUDException)


# ---------------------------------------------------------------------------
# query_filters
# ---------------------------------------------------------------------------
class TestQueryFilters:
    def test_build_keyword_conditions_empty(self):
        from app.common.query_filters import build_keyword_conditions
        assert build_keyword_conditions(object, None, "name") == []
        assert build_keyword_conditions(object, "", "name") == []

    def test_apply_pagination(self):
        from app.common.query_filters import apply_pagination
        from unittest.mock import MagicMock
        q = MagicMock()
        q.offset.return_value = q
        q.limit.return_value = q
        result = apply_pagination(q, 10, 20)
        q.offset.assert_called_with(10)
        q.limit.assert_called_with(20)

    def test_apply_pagination_zero_offset(self):
        from app.common.query_filters import apply_pagination
        from unittest.mock import MagicMock
        q = MagicMock()
        q.limit.return_value = q
        apply_pagination(q, 0, 10)
        q.offset.assert_not_called()

    def test_normalize_keywords(self):
        from app.common.query_filters import _normalize_keywords
        assert _normalize_keywords(None) == []
        assert _normalize_keywords("") == []
        assert _normalize_keywords("test") == ["test"]
        assert _normalize_keywords(["a", "b"]) == ["a", "b"]
        assert _normalize_keywords(["a", None, ""]) == ["a"]
        assert _normalize_keywords(42) == ["42"]
