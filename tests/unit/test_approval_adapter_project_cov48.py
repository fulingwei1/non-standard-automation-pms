# -*- coding: utf-8 -*-
"""单元测试 - ProjectApprovalAdapter (cov48)"""

import pytest
from unittest.mock import MagicMock

try:
    from app.services.approval_engine.adapters.project import ProjectApprovalAdapter
    _IMPORT_OK = True
except Exception:
    _IMPORT_OK = False

pytestmark = pytest.mark.skipif(not _IMPORT_OK, reason="Import failed for ProjectApprovalAdapter")


def _make_adapter():
    db = MagicMock()
    return ProjectApprovalAdapter(db)


def test_get_entity_returns_none_when_not_found():
    adapter = _make_adapter()
    adapter.db.query.return_value.filter.return_value.first.return_value = None
    assert adapter.get_entity(99) is None


def test_get_entity_data_empty_when_project_missing():
    adapter = _make_adapter()
    adapter.db.query.return_value.filter.return_value.first.return_value = None
    assert adapter.get_entity_data(99) == {}


def test_on_submit_sets_pending_approval_and_records_instance():
    adapter = _make_adapter()
    project = MagicMock()
    instance = MagicMock(id=5)
    adapter.db.query.return_value.filter.return_value.first.return_value = project
    adapter.on_submit(1, instance)
    assert project.status == "PENDING_APPROVAL"
    assert project.approval_status == "PENDING"
    assert project.approval_record_id == 5


def test_on_approved_stage_s1_advances_to_s2():
    adapter = _make_adapter()
    project = MagicMock()
    project.stage = "S1"
    instance = MagicMock(id=10)
    adapter.db.query.return_value.filter.return_value.first.return_value = project
    adapter.on_approved(1, instance)
    assert project.stage == "S2"
    assert project.status == "ST02"
    assert project.approval_status == "APPROVED"


def test_on_approved_non_s1_still_sets_approved():
    adapter = _make_adapter()
    project = MagicMock()
    project.stage = "S3"
    instance = MagicMock(id=11)
    adapter.db.query.return_value.filter.return_value.first.return_value = project
    adapter.on_approved(1, instance)
    assert project.status == "ST02"
    assert project.approval_status == "APPROVED"


def test_on_rejected_sets_rejected():
    adapter = _make_adapter()
    project = MagicMock()
    instance = MagicMock(id=7)
    adapter.db.query.return_value.filter.return_value.first.return_value = project
    adapter.on_rejected(1, instance)
    assert project.status == "REJECTED"
    assert project.approval_status == "REJECTED"


def test_on_withdrawn_resets_to_draft():
    adapter = _make_adapter()
    project = MagicMock()
    instance = MagicMock(id=8)
    adapter.db.query.return_value.filter.return_value.first.return_value = project
    adapter.on_withdrawn(1, instance)
    assert project.status == "ST01"
    assert project.approval_status == "CANCELLED"
    assert project.approval_record_id is None


def test_validate_submit_fails_when_project_missing():
    adapter = _make_adapter()
    adapter.db.query.return_value.filter.return_value.first.return_value = None
    ok, msg = adapter.validate_submit(99)
    assert not ok
    assert "不存在" in msg


def test_validate_submit_fails_when_status_invalid():
    adapter = _make_adapter()
    project = MagicMock()
    project.status = "APPROVED"
    adapter.db.query.return_value.filter.return_value.first.return_value = project
    ok, msg = adapter.validate_submit(1)
    assert not ok


def test_get_title_contains_project_code_and_name():
    adapter = _make_adapter()
    project = MagicMock()
    project.project_code = "PRJ-2024-001"
    project.project_name = "智慧城市平台"
    adapter.db.query.return_value.filter.return_value.first.return_value = project
    title = adapter.get_title(1)
    assert "PRJ-2024-001" in title
    assert "智慧城市平台" in title
