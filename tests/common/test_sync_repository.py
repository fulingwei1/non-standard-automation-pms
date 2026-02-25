# -*- coding: utf-8 -*-
"""Tests for SyncBaseRepository"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session


class FakeModel:
    __name__ = "FakeModel"
    id = MagicMock()
    name = MagicMock()
    status = MagicMock()
    deleted_at = MagicMock()
    children = MagicMock()  # fake relationship

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class CreateSchema(BaseModel):
    name: str
    status: str = "active"


class UpdateSchema(BaseModel):
    name: str | None = None
    status: str | None = None


def _make_repo(db=None):
    from app.common.crud.sync_repository import SyncBaseRepository
    db = db or MagicMock(spec=Session)
    repo = SyncBaseRepository(FakeModel, db, "FakeModel")
    return repo, db


class TestSyncBaseRepositoryInit:
    def test_default_resource_name(self):
        from app.common.crud.sync_repository import SyncBaseRepository
        db = MagicMock(spec=Session)
        repo = SyncBaseRepository(FakeModel, db)
        assert repo.resource_name == "FakeModel"


class TestSyncGet:
    def test_get_found(self):
        repo, db = _make_repo()
        fake_obj = FakeModel(id=1, name="test")
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = fake_obj
        db.query.return_value = query_mock
        assert repo.get(1) == fake_obj

    def test_get_not_found(self):
        repo, db = _make_repo()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        db.query.return_value = query_mock
        assert repo.get(999) is None

    @patch("app.common.crud.sync_repository.joinedload")
    def test_get_with_relationships(self, mock_jl):
        repo, db = _make_repo()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.options.return_value = query_mock
        query_mock.first.return_value = FakeModel(id=1, name="test")
        db.query.return_value = query_mock
        result = repo.get(1, load_relationships=["children"])
        assert result is not None
        query_mock.options.assert_called_once()


class TestSyncGetByField:
    def test_found(self):
        repo, db = _make_repo()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = FakeModel(id=1, name="test")
        db.query.return_value = query_mock
        assert repo.get_by_field("name", "test").name == "test"

    def test_invalid_field(self):
        repo, db = _make_repo()
        with pytest.raises(ValueError, match="不存在"):
            repo.get_by_field("nonexistent", "val")


class TestSyncCreate:
    def test_create_with_commit(self):
        repo, db = _make_repo()
        repo.create(CreateSchema(name="new_item"))
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_create_without_commit(self):
        repo, db = _make_repo()
        repo.create(CreateSchema(name="new_item"), commit=False)
        db.commit.assert_not_called()

    def test_create_many(self):
        repo, db = _make_repo()
        results = repo.create_many([CreateSchema(name="a"), CreateSchema(name="b")])
        assert db.add.call_count == 2
        assert len(results) == 2


class TestSyncUpdate:
    def test_update_found(self):
        repo, db = _make_repo()
        fake_obj = FakeModel(id=1, name="old")
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = fake_obj
        db.query.return_value = query_mock
        result = repo.update(1, UpdateSchema(name="new"))
        assert result.name == "new"

    def test_update_not_found(self):
        repo, db = _make_repo()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        db.query.return_value = query_mock
        assert repo.update(999, UpdateSchema(name="x")) is None

    def test_update_by_field(self):
        repo, db = _make_repo()
        fake_obj = FakeModel(id=1, name="old")
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = fake_obj
        db.query.return_value = query_mock
        result = repo.update_by_field("name", "old", UpdateSchema(name="new"))
        assert result.name == "new"

    def test_update_by_field_not_found(self):
        repo, db = _make_repo()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        db.query.return_value = query_mock
        assert repo.update_by_field("name", "nope", UpdateSchema(name="x")) is None


class TestSyncDelete:
    def test_hard_delete(self):
        repo, db = _make_repo()
        fake_obj = FakeModel(id=1, name="del")
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = fake_obj
        db.query.return_value = query_mock
        assert repo.delete(1) is True
        db.delete.assert_called_once()

    def test_soft_delete(self):
        repo, db = _make_repo()
        fake_obj = FakeModel(id=1, name="del")
        fake_obj.deleted_at = None
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = fake_obj
        db.query.return_value = query_mock
        assert repo.delete(1, soft_delete=True) is True
        assert fake_obj.deleted_at is not None

    def test_soft_delete_no_field(self):
        repo, db = _make_repo()
        fake_obj = MagicMock(spec=[])
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = fake_obj
        db.query.return_value = query_mock
        with pytest.raises(ValueError, match="不支持软删除"):
            repo.delete(1, soft_delete=True)

    def test_delete_not_found(self):
        repo, db = _make_repo()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        db.query.return_value = query_mock
        assert repo.delete(999) is False

    def test_delete_no_commit(self):
        repo, db = _make_repo()
        fake_obj = FakeModel(id=1, name="del")
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = fake_obj
        db.query.return_value = query_mock
        assert repo.delete(1, commit=False) is True
        db.commit.assert_not_called()


class TestSyncExists:
    def test_exists_true(self):
        repo, db = _make_repo()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = FakeModel(id=1, name="x")
        db.query.return_value = query_mock
        assert repo.exists(1) is True

    def test_exists_false(self):
        repo, db = _make_repo()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = None
        db.query.return_value = query_mock
        assert repo.exists(999) is False

    def test_exists_by_field(self):
        repo, db = _make_repo()
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = FakeModel(id=1, name="x")
        db.query.return_value = query_mock
        assert repo.exists_by_field("name", "x") is True


class TestSyncList:
    @patch("app.common.crud.sync_repository.SyncQueryBuilder")
    def test_list_basic(self, mock_qb):
        repo, db = _make_repo()
        mock_query = MagicMock()
        mock_count = MagicMock()
        mock_qb.build_list_query.return_value = (mock_query, mock_count)
        mock_qb.execute_list_query.return_value = ([FakeModel(id=1, name="a")], 1)
        items, total = repo.list(skip=0, limit=10)
        assert total == 1

    @patch("app.common.crud.sync_repository.joinedload")
    @patch("app.common.crud.sync_repository.SyncQueryBuilder")
    def test_list_with_relationships(self, mock_qb, mock_jl):
        repo, db = _make_repo()
        mock_query = MagicMock()
        mock_count = MagicMock()
        mock_qb.build_list_query.return_value = (mock_query, mock_count)
        mock_query.options.return_value = mock_query
        mock_qb.execute_list_query.return_value = ([], 0)
        repo.list(load_relationships=["children"])
        mock_query.options.assert_called_once()


class TestSyncCount:
    @patch("app.common.crud.sync_repository.SyncQueryBuilder")
    def test_count(self, mock_qb):
        repo, db = _make_repo()
        mock_query = MagicMock()
        mock_count = MagicMock()
        mock_count.scalar.return_value = 5
        mock_qb.build_list_query.return_value = (mock_query, mock_count)
        assert repo.count() == 5

    @patch("app.common.crud.sync_repository.SyncQueryBuilder")
    def test_count_none(self, mock_qb):
        repo, db = _make_repo()
        mock_query = MagicMock()
        mock_count = MagicMock()
        mock_count.scalar.return_value = None
        mock_qb.build_list_query.return_value = (mock_query, mock_count)
        assert repo.count() == 0
