# -*- coding: utf-8 -*-
"""Tests for SyncBaseService (app.common.crud.sync_service)"""

import pytest
from unittest.mock import MagicMock
from pydantic import BaseModel
from fastapi import HTTPException
from sqlalchemy.orm import Session


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
    from app.common.crud.sync_service import SyncBaseService

    db = MagicMock(spec=Session)

    class TestSvc(SyncBaseService):
        def _to_response(self, obj):
            return FResponse.model_validate(obj)

    svc = TestSvc(FakeModel, db, "Fake")
    svc.repository = MagicMock()
    return svc


class TestSyncServiceGet:
    def test_found(self):
        svc = _make_service()
        svc.repository.get.return_value = FakeModel(id=1, name="a")
        assert svc.get(1).id == 1

    def test_not_found(self):
        svc = _make_service()
        svc.repository.get.return_value = None
        with pytest.raises(HTTPException):
            svc.get(999)


class TestSyncServiceGetByField:
    def test_found(self):
        svc = _make_service()
        svc.repository.get_by_field.return_value = FakeModel(id=1, name="a")
        assert svc.get_by_field("name", "a").name == "a"

    def test_not_found(self):
        svc = _make_service()
        svc.repository.get_by_field.return_value = None
        assert svc.get_by_field("name", "x") is None


class TestSyncServiceList:
    def test_list(self):
        svc = _make_service()
        svc.repository.list.return_value = ([FakeModel(id=1, name="a")], 1)
        result = svc.list()
        assert result["total"] == 1


class TestSyncServiceCreate:
    def test_create(self):
        svc = _make_service()
        svc.repository.exists_by_field.return_value = False
        svc.repository.create.return_value = FakeModel(id=1, name="new")
        assert svc.create(FCreate(name="new")).name == "new"

    def test_create_unique_conflict(self):
        svc = _make_service()
        svc.repository.exists_by_field.return_value = True
        with pytest.raises(HTTPException):
            svc.create(FCreate(name="dup"), check_unique={"name": "dup"})


class TestSyncServiceUpdate:
    def test_update(self):
        svc = _make_service()
        svc.repository.get.return_value = FakeModel(id=1, name="old")
        svc.repository.update.return_value = FakeModel(id=1, name="new")
        svc.repository.get_by_field.return_value = None
        assert svc.update(1, FUpdate(name="new")).name == "new"

    def test_update_not_found(self):
        svc = _make_service()
        svc.repository.get.return_value = None
        with pytest.raises(HTTPException):
            svc.update(999, FUpdate(name="x"))

    def test_update_unique_conflict(self):
        svc = _make_service()
        svc.repository.get.return_value = FakeModel(id=1, name="old")
        svc.repository.get_by_field.return_value = FakeModel(id=2, name="taken")
        with pytest.raises(HTTPException):
            svc.update(1, FUpdate(name="taken"), check_unique={"name": "taken"})


class TestSyncServiceDelete:
    def test_delete(self):
        svc = _make_service()
        svc.repository.exists.return_value = True
        svc.repository.delete.return_value = True
        assert svc.delete(1) is True

    def test_delete_not_found(self):
        svc = _make_service()
        svc.repository.exists.return_value = False
        with pytest.raises(HTTPException):
            svc.delete(999)


class TestSyncServiceCount:
    def test_count(self):
        svc = _make_service()
        svc.repository.count.return_value = 5
        assert svc.count() == 5


class TestSyncServiceHooks:
    def test_to_response_not_implemented(self):
        from app.common.crud.sync_service import SyncBaseService
        db = MagicMock(spec=Session)
        svc = SyncBaseService(FakeModel, db)
        with pytest.raises(NotImplementedError):
            svc._to_response(FakeModel(id=1, name="x"))

    def test_hooks_passthrough(self):
        svc = _make_service()
        schema = FCreate(name="x")
        assert svc._before_create(schema) is schema
        obj = FakeModel(id=1, name="x")
        assert svc._after_create(obj) is obj
