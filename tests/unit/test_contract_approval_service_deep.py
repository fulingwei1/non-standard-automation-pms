# -*- coding: utf-8 -*-
"""contract.approval_service 深度测试"""

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from app.services.sales.contract.approval_service import ContractApprovalService


class FakeQuery:
    def __init__(self, first_value=None, count_value=0, all_value=None):
        self._first_value = first_value
        self._count_value = count_value
        self._all_value = all_value or []

    def filter(self, *args, **kwargs):
        return self

    def first(self):
        return self._first_value

    def count(self):
        return self._count_value

    def options(self, *args, **kwargs):
        return self

    def all(self):
        return self._all_value


class FakeApproval:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestContractApprovalServiceDeep:
    def test_create_approval_flow_by_amount(self):
        db = Mock()
        added = []
        db.add.side_effect = lambda obj: added.append(obj)
        service = ContractApprovalService(db)

        with patch("app.services.sales.contract.approval_service.ContractApproval", FakeApproval):
            low = service._create_approval_flow(1, Decimal("99999"))
            mid = service._create_approval_flow(2, Decimal("100000"))
            high = service._create_approval_flow(3, Decimal("500000"))

        assert [a.approval_role for a in low] == ["sales_manager"]
        assert [a.approval_role for a in mid] == ["sales_director"]
        assert [a.approval_role for a in high] == ["sales_director", "finance_director", "general_manager"]
        assert [a.approval_level for a in high] == [1, 2, 3]
        assert len(added) == 5
        db.flush.assert_called()

    def test_submit_for_approval_missing_and_status_transition(self):
        db = Mock()
        service = ContractApprovalService(db)
        draft_contract = SimpleNamespace(id=1, status="draft", total_amount=Decimal("10"))
        no_flow_contract = SimpleNamespace(id=2, status="draft", total_amount=Decimal("20"))
        db.query.side_effect = [FakeQuery(first_value=None), FakeQuery(first_value=draft_contract), FakeQuery(first_value=no_flow_contract)]
        service._create_approval_flow = Mock(side_effect=[[SimpleNamespace()], []])

        with pytest.raises(ValueError, match="合同不存在"):
            service.submit_for_approval(99, 1)

        with patch("app.services.sales.contract.approval_service.assert_status_allows") as allow:
            result1 = service.submit_for_approval(1, 1)
            result2 = service.submit_for_approval(2, 1)

        assert result1.status == "approving"
        assert result2.status == "approved"
        assert service._create_approval_flow.call_args_list[0].args == (1, Decimal("10"))
        allow.assert_any_call(draft_contract, "draft", "只能提交草稿状态的合同")
        allow.assert_any_call(no_flow_contract, "draft", "只能提交草稿状态的合同")
        assert db.commit.call_count == 2
        assert db.refresh.call_count == 2

    def test_approve_validates_record_and_updates_contract_status(self):
        db = Mock()
        service = ContractApprovalService(db)
        pending = SimpleNamespace(approval_status="pending", approver_id=None, approval_opinion=None, approved_at=None)
        contract = SimpleNamespace(id=1, status="approving")
        db.query.side_effect = [
            FakeQuery(first_value=None),
            FakeQuery(first_value=SimpleNamespace(approval_status="approved")),
            FakeQuery(first_value=pending),
            FakeQuery(first_value=contract),
            FakeQuery(count_value=0),
        ]

        with pytest.raises(ValueError, match="审批记录不存在"):
            service.approve(1, 1, 9)
        with pytest.raises(ValueError, match="该审批已处理"):
            service.approve(1, 1, 9)

        result = service.approve(1, 1, 9, opinion="同意")

        assert result is contract
        assert pending.approver_id == 9
        assert pending.approval_status == "approved"
        assert pending.approval_opinion == "同意"
        assert contract.status == "approved"
        db.flush.assert_called_once()
        db.commit.assert_called_once()
        db.refresh.assert_called_once_with(contract)

    def test_approve_keeps_contract_approving_when_pending_remains(self):
        db = Mock()
        service = ContractApprovalService(db)
        pending = SimpleNamespace(approval_status="pending")
        contract = SimpleNamespace(id=2, status="approving")
        db.query.side_effect = [
            FakeQuery(first_value=pending),
            FakeQuery(first_value=contract),
            FakeQuery(count_value=2),
        ]

        result = service.approve(2, 5, 10)

        assert result.status == "approving"

    def test_reject_and_get_pending_approvals(self):
        db = Mock()
        service = ContractApprovalService(db)
        approval = SimpleNamespace(approval_status="pending", approver_id=None, approval_opinion=None, approved_at=None)
        contract = SimpleNamespace(id=1, status="approving")
        approvals = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
        db.query.side_effect = [
            FakeQuery(first_value=None),
            FakeQuery(first_value=SimpleNamespace(approval_status="approved")),
            FakeQuery(first_value=approval),
            FakeQuery(first_value=contract),
            FakeQuery(all_value=approvals),
        ]

        with pytest.raises(ValueError, match="审批记录不存在"):
            service.reject(1, 1, 3, "退回")
        with pytest.raises(ValueError, match="该审批已处理"):
            service.reject(1, 1, 3, "退回")

        result = service.reject(1, 1, 3, "退回修改")
        pending_rows = service.get_pending_approvals(3)

        assert result.status == "draft"
        assert approval.approver_id == 3
        assert approval.approval_status == "rejected"
        assert approval.approval_opinion == "退回修改"
        assert pending_rows == approvals
        assert db.commit.call_count == 1
        assert db.refresh.call_count == 1
