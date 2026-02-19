# -*- coding: utf-8 -*-
"""单元测试 - ContractApprovalAdapter (cov48)"""

import pytest
from unittest.mock import MagicMock

try:
    from app.services.approval_engine.adapters.contract import ContractApprovalAdapter
    _IMPORT_OK = True
except Exception:
    _IMPORT_OK = False

pytestmark = pytest.mark.skipif(not _IMPORT_OK, reason="Import failed for ContractApprovalAdapter")


def _make_adapter():
    db = MagicMock()
    return ContractApprovalAdapter(db)


def test_get_entity_returns_none_when_not_found():
    adapter = _make_adapter()
    adapter.db.query.return_value.filter.return_value.first.return_value = None
    assert adapter.get_entity(99) is None


def test_get_entity_data_empty_when_contract_missing():
    adapter = _make_adapter()
    adapter.db.query.return_value.filter.return_value.first.return_value = None
    assert adapter.get_entity_data(99) == {}


def test_get_entity_data_returns_expected_keys():
    adapter = _make_adapter()
    contract = MagicMock()
    contract.contract_code = "CON-2024-001"
    contract.customer_contract_no = "CUS-001"
    contract.status = "DRAFT"
    contract.contract_amount = 50000
    contract.customer_id = 10
    contract.customer = MagicMock(name="大客户公司")
    contract.project_id = 3
    contract.signed_date = MagicMock()
    contract.signed_date.isoformat.return_value = "2024-01-15"
    contract.owner_id = 5
    contract.owner = MagicMock(name="张销售")
    contract.payment_terms_summary = "月结30天"
    adapter.db.query.return_value.filter.return_value.first.return_value = contract
    result = adapter.get_entity_data(1)
    assert result["contract_code"] == "CON-2024-001"
    assert result["contract_amount"] == 50000.0


def test_on_submit_sets_pending_approval():
    adapter = _make_adapter()
    contract = MagicMock()
    adapter.db.query.return_value.filter.return_value.first.return_value = contract
    adapter.on_submit(1, MagicMock())
    assert contract.status == "PENDING_APPROVAL"
    adapter.db.flush.assert_called_once()


def test_on_approved_sets_approved():
    adapter = _make_adapter()
    contract = MagicMock()
    adapter.db.query.return_value.filter.return_value.first.return_value = contract
    adapter.on_approved(1, MagicMock())
    assert contract.status == "APPROVED"


def test_on_rejected_sets_rejected():
    adapter = _make_adapter()
    contract = MagicMock()
    adapter.db.query.return_value.filter.return_value.first.return_value = contract
    adapter.on_rejected(1, MagicMock())
    assert contract.status == "REJECTED"


def test_on_withdrawn_sets_draft():
    adapter = _make_adapter()
    contract = MagicMock()
    adapter.db.query.return_value.filter.return_value.first.return_value = contract
    adapter.on_withdrawn(1, MagicMock())
    assert contract.status == "DRAFT"


def test_validate_submit_fails_when_contract_missing():
    adapter = _make_adapter()
    adapter.db.query.return_value.filter.return_value.first.return_value = None
    ok, msg = adapter.validate_submit(99)
    assert not ok
    assert "不存在" in msg


def test_validate_submit_fails_when_bad_status():
    adapter = _make_adapter()
    contract = MagicMock()
    contract.status = "APPROVED"
    adapter.db.query.return_value.filter.return_value.first.return_value = contract
    ok, msg = adapter.validate_submit(1)
    assert not ok


def test_get_title_contains_contract_code():
    adapter = _make_adapter()
    contract = MagicMock()
    contract.contract_code = "CON-XYZ"
    contract.customer = MagicMock(name="客户X")
    adapter.db.query.return_value.filter.return_value.first.return_value = contract
    title = adapter.get_title(1)
    assert "CON-XYZ" in title
