# -*- coding: utf-8 -*-
"""Unit tests for app/services/approval_engine/adapters/contract.py - batch 41"""
import pytest

pytest.importorskip("app.services.approval_engine.adapters.contract")

from unittest.mock import MagicMock, patch


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def adapter(db):
    from app.services.approval_engine.adapters.contract import ContractApprovalAdapter
    return ContractApprovalAdapter(db)


def test_entity_type(adapter):
    assert adapter.entity_type == "CONTRACT"


def test_get_entity_not_found(adapter, db):
    db.query.return_value.filter.return_value.first.return_value = None
    result = adapter.get_entity(999)
    assert result is None


def test_get_entity_data_empty_when_missing(adapter, db):
    db.query.return_value.filter.return_value.first.return_value = None
    result = adapter.get_entity_data(999)
    assert result == {}


def test_on_submit_sets_pending(adapter, db):
    contract = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = contract
    adapter.on_submit(1, MagicMock())
    assert contract.status == "PENDING_APPROVAL"
    db.flush.assert_called()


def test_on_approved_sets_approved(adapter, db):
    contract = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = contract
    adapter.on_approved(1, MagicMock())
    assert contract.status == "APPROVED"


def test_on_rejected_sets_rejected(adapter, db):
    contract = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = contract
    adapter.on_rejected(1, MagicMock())
    assert contract.status == "REJECTED"


def test_on_withdrawn_sets_draft(adapter, db):
    contract = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = contract
    adapter.on_withdrawn(1, MagicMock())
    assert contract.status == "DRAFT"


def test_validate_submit_contract_not_found(adapter, db):
    db.query.return_value.filter.return_value.first.return_value = None
    ok, msg = adapter.validate_submit(999)
    assert ok is False
    assert "不存在" in msg


def test_validate_submit_wrong_status(adapter, db):
    contract = MagicMock()
    contract.status = "APPROVED"
    contract.contract_amount = 10000
    db.query.return_value.filter.return_value.first.return_value = contract
    ok, msg = adapter.validate_submit(1)
    assert ok is False


def test_validate_submit_success(adapter, db):
    contract = MagicMock()
    contract.status = "DRAFT"
    contract.contract_amount = 10000
    db.query.return_value.filter.return_value.first.return_value = contract
    ok, msg = adapter.validate_submit(1)
    assert ok is True
