# -*- coding: utf-8 -*-
"""status_service单元测试"""
from unittest.mock import Mock

import pytest

from app.services.sales.contract.status_service import (
    ContractStatusService,
    contract_status_query_values,
    normalize_contract_status,
)

class TestContractStatusServiceInit:
    def test_init(self):
        service = ContractStatusService(Mock())
        assert service is not None


def test_normalize_contract_status_accepts_legacy_uppercase_values():
    assert normalize_contract_status("signed") == "SIGNED"
    assert normalize_contract_status("ACTIVE") == "EXECUTING"
    assert normalize_contract_status("completed") == "COMPLETED"
    assert normalize_contract_status("voided") == "CANCELLED"
    assert normalize_contract_status("approving") == "PENDING_APPROVAL"


def test_contract_status_query_values_expand_legacy_and_canonical_values():
    values = set(contract_status_query_values("signed,executing,cancelled"))
    assert {"SIGNED", "signed"}.issubset(values)
    assert {"EXECUTING", "executing", "ACTIVE"}.issubset(values)
    assert {"CANCELLED", "cancelled", "voided"}.issubset(values)


def test_mark_as_executing_accepts_legacy_signed_and_writes_canonical_uppercase():
    db = Mock()
    contract = Mock(id=1, status="SIGNED", contract_code="C-1")
    db.query.return_value.filter.return_value.first.side_effect = [contract, None]

    result = ContractStatusService(db).mark_as_executing(1)

    assert result is contract
    assert contract.status == "EXECUTING"


def test_void_contract_blocks_legacy_completed_terminal_status():
    db = Mock()
    contract = Mock(id=1, status="COMPLETED", contract_code="C-1")
    db.query.return_value.filter.return_value.first.return_value = contract

    with pytest.raises(ValueError, match="已完成"):
        ContractStatusService(db).void_contract(1)
