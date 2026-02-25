# -*- coding: utf-8 -*-
"""Tests for async BaseService (app.common.crud.service)"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel
from fastapi import HTTPException


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------
class FakeModel:
    __name__ = "FakeModel"
    id = MagicMock()
    name = MagicMock()

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


class FCreate(BaseModel):
    name: str


class FUpdate(BaseModel):
    name: str | None = None


class FResponse(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


def _make_service():
    from app.common.crud.service import BaseService

    db = AsyncMock()

    class TestService(BaseService):
        def _to_response(self, obj):
            return FResponse.model_validate(obj)

    svc = TestService(FakeModel, db, "Fake")
    svc.repository = AsyncMock()
    return svc


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestAsyncServiceGet:
    @pytest.mark.asyncio
    async def test_get_found(self):
        svc = _make_service()
        svc.repository.get.return_value = FakeModel(id=1, name="a")
        result = await svc.get(1)
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_get_not_found(self):
        svc = _make_service()
        svc.repository.get.return_value = None
        with pytest.raises(HTTPException) as exc:
            await svc.get(999)
        assert exc.value.status_code == 404


class TestAsyncServiceGetByField:
    @pytest.mark.asyncio
    async def test_found(self):
        svc = _make_service()
        svc.repository.get_by_field.return_value = FakeModel(id=1, name="a")
        result = await svc.get_by_field("name", "a")
        assert result.name == "a"

    @pytest.mark.asyncio
    async def test_not_found(self):
        svc = _make_service()
        svc.repository.get_by_field.return_value = None
        result = await svc.get_by_field("name", "nope")
        assert result is None


class TestAsyncServiceList:
    @pytest.mark.asyncio
    async def test_list(self):
        svc = _make_service()
        svc.repository.list.return_value = ([FakeModel(id=1, name="a")], 1)
        result = await svc.list(skip=0, limit=10)
        assert result["total"] == 1
        assert len(result["items"]) == 1


class TestAsyncServiceCreate:
    @pytest.mark.asyncio
    async def test_create(self):
        svc = _make_service()
        svc.repository.exists_by_field.return_value = False
        svc.repository.create.return_value = FakeModel(id=1, name="new")

        with patch.object(svc, "_log_audit", new_callable=AsyncMock):
            result = await svc.create(FCreate(name="new"))
        assert result.name == "new"

    @pytest.mark.asyncio
    async def test_create_unique_conflict(self):
        svc = _make_service()
        svc.repository.exists_by_field.return_value = True

        with pytest.raises(HTTPException) as exc:
            await svc.create(FCreate(name="dup"), check_unique={"name": "dup"})
        assert exc.value.status_code == 409


class TestAsyncServiceUpdate:
    @pytest.mark.asyncio
    async def test_update(self):
        svc = _make_service()
        svc.repository.get.return_value = FakeModel(id=1, name="old")
        svc.repository.update.return_value = FakeModel(id=1, name="new")
        svc.repository.get_by_field.return_value = None

        with patch.object(svc, "_log_audit", new_callable=AsyncMock):
            result = await svc.update(1, FUpdate(name="new"))
        assert result.name == "new"

    @pytest.mark.asyncio
    async def test_update_not_found(self):
        svc = _make_service()
        svc.repository.get.return_value = None
        with pytest.raises(HTTPException):
            await svc.update(999, FUpdate(name="x"))

    @pytest.mark.asyncio
    async def test_update_unique_conflict(self):
        svc = _make_service()
        svc.repository.get.return_value = FakeModel(id=1, name="old")
        existing = FakeModel(id=2, name="taken")
        svc.repository.get_by_field.return_value = existing

        with pytest.raises(HTTPException) as exc:
            await svc.update(1, FUpdate(name="taken"), check_unique={"name": "taken"})
        assert exc.value.status_code == 409


class TestAsyncServiceDelete:
    @pytest.mark.asyncio
    async def test_delete(self):
        svc = _make_service()
        svc.repository.exists.return_value = True
        svc.repository.delete.return_value = True

        with patch.object(svc, "_log_audit", new_callable=AsyncMock):
            result = await svc.delete(1)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        svc = _make_service()
        svc.repository.exists.return_value = False
        with pytest.raises(HTTPException):
            await svc.delete(999)


class TestAsyncServiceCount:
    @pytest.mark.asyncio
    async def test_count(self):
        svc = _make_service()
        svc.repository.count.return_value = 10
        assert await svc.count() == 10
