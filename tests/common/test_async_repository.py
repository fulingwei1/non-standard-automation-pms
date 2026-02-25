# -*- coding: utf-8 -*-
"""Tests for async BaseRepository - mock at method level to avoid select() issues"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import BaseModel


class FakeModel:
    __name__ = "FakeModel"
    id = MagicMock()
    name = MagicMock()
    deleted_at = MagicMock()

    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)


class FCreate(BaseModel):
    name: str


class FUpdate(BaseModel):
    name: str | None = None


def _make_repo():
    from app.common.crud.repository import BaseRepository
    db = AsyncMock()
    repo = BaseRepository(FakeModel, db, "Fake")
    return repo, db


class TestAsyncRepoInit:
    def test_defaults(self):
        repo, _ = _make_repo()
        assert repo.resource_name == "Fake"
        assert repo.model == FakeModel

    def test_default_resource_name(self):
        from app.common.crud.repository import BaseRepository
        db = AsyncMock()
        repo = BaseRepository(FakeModel, db)
        assert repo.resource_name == "FakeModel"


class TestAsyncRepoCreate:
    @pytest.mark.asyncio
    async def test_create(self):
        repo, db = _make_repo()
        db.add = MagicMock()  # add is sync
        result = await repo.create(FCreate(name="new"))
        db.add.assert_called_once()
        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_no_commit(self):
        repo, db = _make_repo()
        db.add = MagicMock()
        await repo.create(FCreate(name="new"), commit=False)
        db.commit.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_many(self):
        repo, db = _make_repo()
        db.add = MagicMock()
        results = await repo.create_many([FCreate(name="a"), FCreate(name="b")])
        assert db.add.call_count == 2
        assert len(results) == 2


class TestAsyncRepoGetByField:
    @pytest.mark.asyncio
    async def test_invalid_field(self):
        repo, db = _make_repo()
        with pytest.raises(ValueError):
            await repo.get_by_field("nonexistent", "x")


class TestAsyncRepoDelete:
    @pytest.mark.asyncio
    async def test_soft_delete_no_field(self):
        repo, db = _make_repo()
        fake_obj = MagicMock(spec=[])  # no deleted_at
        with patch.object(repo, "get", new_callable=AsyncMock, return_value=fake_obj):
            with pytest.raises(ValueError, match="不支持软删除"):
                await repo.delete(1, soft_delete=True)

    @pytest.mark.asyncio
    async def test_delete_not_found(self):
        repo, db = _make_repo()
        with patch.object(repo, "get", new_callable=AsyncMock, return_value=None):
            assert await repo.delete(999) is False

    @pytest.mark.asyncio
    async def test_hard_delete(self):
        repo, db = _make_repo()
        fake_obj = FakeModel(id=1, name="x")
        with patch.object(repo, "get", new_callable=AsyncMock, return_value=fake_obj):
            result = await repo.delete(1)
            assert result is True
            db.delete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_soft_delete(self):
        repo, db = _make_repo()
        fake_obj = FakeModel(id=1, name="x")
        fake_obj.deleted_at = None
        with patch.object(repo, "get", new_callable=AsyncMock, return_value=fake_obj):
            result = await repo.delete(1, soft_delete=True)
            assert result is True
            assert fake_obj.deleted_at is not None


class TestAsyncRepoUpdate:
    @pytest.mark.asyncio
    async def test_update_found(self):
        repo, db = _make_repo()
        fake_obj = FakeModel(id=1, name="old")
        with patch.object(repo, "get", new_callable=AsyncMock, return_value=fake_obj):
            result = await repo.update(1, FUpdate(name="new"))
            assert result.name == "new"

    @pytest.mark.asyncio
    async def test_update_not_found(self):
        repo, db = _make_repo()
        with patch.object(repo, "get", new_callable=AsyncMock, return_value=None):
            assert await repo.update(999, FUpdate(name="x")) is None

    @pytest.mark.asyncio
    async def test_update_by_field(self):
        repo, db = _make_repo()
        fake_obj = FakeModel(id=1, name="old")
        with patch.object(repo, "get_by_field", new_callable=AsyncMock, return_value=fake_obj):
            result = await repo.update_by_field("name", "old", FUpdate(name="new"))
            assert result.name == "new"

    @pytest.mark.asyncio
    async def test_update_by_field_not_found(self):
        repo, db = _make_repo()
        with patch.object(repo, "get_by_field", new_callable=AsyncMock, return_value=None):
            assert await repo.update_by_field("name", "nope", FUpdate(name="x")) is None


class TestAsyncRepoExists:
    @pytest.mark.asyncio
    async def test_exists_true(self):
        repo, db = _make_repo()
        with patch.object(repo, "get", new_callable=AsyncMock, return_value=FakeModel(id=1, name="x")):
            assert await repo.exists(1) is True

    @pytest.mark.asyncio
    async def test_exists_false(self):
        repo, db = _make_repo()
        with patch.object(repo, "get", new_callable=AsyncMock, return_value=None):
            assert await repo.exists(999) is False

    @pytest.mark.asyncio
    async def test_exists_by_field(self):
        repo, db = _make_repo()
        with patch.object(repo, "get_by_field", new_callable=AsyncMock, return_value=FakeModel(id=1, name="x")):
            assert await repo.exists_by_field("name", "x") is True
