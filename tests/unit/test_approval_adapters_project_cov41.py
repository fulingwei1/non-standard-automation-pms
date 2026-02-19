# -*- coding: utf-8 -*-
"""Unit tests for app/services/approval_engine/adapters/project.py - batch 41"""
import pytest

pytest.importorskip("app.services.approval_engine.adapters.project")

from unittest.mock import MagicMock


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def adapter(db):
    from app.services.approval_engine.adapters.project import ProjectApprovalAdapter
    return ProjectApprovalAdapter(db)


def test_entity_type(adapter):
    assert adapter.entity_type == "PROJECT"


def test_get_entity_returns_none_if_missing(adapter, db):
    db.query.return_value.filter.return_value.first.return_value = None
    assert adapter.get_entity(999) is None


def test_get_entity_data_empty_when_missing(adapter, db):
    db.query.return_value.filter.return_value.first.return_value = None
    assert adapter.get_entity_data(999) == {}


def test_on_submit_sets_pending(adapter, db):
    project = MagicMock()
    instance = MagicMock()
    instance.id = 1
    db.query.return_value.filter.return_value.first.return_value = project
    adapter.on_submit(1, instance)
    assert project.status == "PENDING_APPROVAL"
    assert project.approval_status == "PENDING"


def test_on_approved_s1_advances_stage(adapter, db):
    project = MagicMock()
    project.stage = "S1"
    instance = MagicMock()
    instance.id = 2
    db.query.return_value.filter.return_value.first.return_value = project
    adapter.on_approved(1, instance)
    assert project.stage == "S2"
    assert project.approval_status == "APPROVED"


def test_on_rejected_sets_rejected(adapter, db):
    project = MagicMock()
    instance = MagicMock()
    instance.id = 3
    db.query.return_value.filter.return_value.first.return_value = project
    adapter.on_rejected(1, instance)
    assert project.status == "REJECTED"
    assert project.approval_status == "REJECTED"


def test_on_withdrawn_resets_status(adapter, db):
    project = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = project
    adapter.on_withdrawn(1, MagicMock())
    assert project.status == "ST01"
    assert project.approval_status == "CANCELLED"


def test_validate_submit_not_found(adapter, db):
    db.query.return_value.filter.return_value.first.return_value = None
    ok, msg = adapter.validate_submit(999)
    assert ok is False


def test_validate_submit_success(adapter, db):
    project = MagicMock()
    project.status = "ST01"
    project.project_name = "Test Project"
    project.pm_id = 5
    db.query.return_value.filter.return_value.first.return_value = project
    ok, msg = adapter.validate_submit(1)
    assert ok is True
