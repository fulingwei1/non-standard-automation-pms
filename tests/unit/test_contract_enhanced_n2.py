# -*- coding: utf-8 -*-
"""
合同增强服务 N2 深度覆盖测试
覆盖: approve_contract, reject_contract, 状态流转, void_contract,
      get_pending_approvals, 条款/附件管理, get_contract_stats,
      金额重新计算
"""
import pytest
from decimal import Decimal
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.services.sales.contract_enhanced import ContractEnhancedService


# ======================= approve_contract =======================

class TestApproveContract:
    """测试审批通过逻辑"""

    def test_raises_when_approval_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="审批记录不存在"):
            ContractEnhancedService.approve_contract(db, 1, 99, user_id=1)

    def test_raises_when_already_processed(self):
        db = MagicMock()
        approval = MagicMock()
        approval.approval_status = "approved"
        db.query.return_value.filter.return_value.first.return_value = approval
        with pytest.raises(ValueError, match="该审批已处理"):
            ContractEnhancedService.approve_contract(db, 1, 1, user_id=1)

    def test_sets_approval_to_approved(self):
        db = MagicMock()
        approval = MagicMock()
        approval.approval_status = "pending"
        contract = MagicMock()
        contract.status = "approving"

        # Simulate query chain: first returns approval, second returns contract, third returns pending count
        call_count = [0]
        def query_side(model):
            call_count[0] += 1
            q = MagicMock()
            if call_count[0] == 1:
                q.filter.return_value.first.return_value = approval
            elif call_count[0] == 2:
                q.filter.return_value.first.return_value = contract
            else:
                q.filter.return_value.count.return_value = 1  # still pending
            return q
        db.query.side_effect = query_side

        result = ContractEnhancedService.approve_contract(db, 1, 1, user_id=5, opinion="OK")
        assert approval.approval_status == "approved"
        assert approval.approver_id == 5
        assert approval.approval_opinion == "OK"
        db.commit.assert_called_once()

    def test_sets_contract_to_approved_when_all_done(self):
        db = MagicMock()
        approval = MagicMock()
        approval.approval_status = "pending"
        contract = MagicMock()
        contract.status = "approving"

        call_count = [0]
        def query_side(model):
            call_count[0] += 1
            q = MagicMock()
            if call_count[0] == 1:
                q.filter.return_value.first.return_value = approval
            elif call_count[0] == 2:
                q.filter.return_value.first.return_value = contract
            else:
                q.filter.return_value.count.return_value = 0  # all approved
            return q
        db.query.side_effect = query_side

        ContractEnhancedService.approve_contract(db, 1, 1, user_id=1)
        assert contract.status == "approved"


# ======================= reject_contract =======================

class TestRejectContract:
    """测试审批驳回逻辑"""

    def test_raises_when_approval_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="审批记录不存在"):
            ContractEnhancedService.reject_contract(db, 1, 99, user_id=1, opinion="reject")

    def test_raises_when_already_processed(self):
        db = MagicMock()
        approval = MagicMock()
        approval.approval_status = "rejected"
        db.query.return_value.filter.return_value.first.return_value = approval
        with pytest.raises(ValueError, match="该审批已处理"):
            ContractEnhancedService.reject_contract(db, 1, 1, user_id=1, opinion="no")

    def test_sets_contract_back_to_draft(self):
        db = MagicMock()
        approval = MagicMock()
        approval.approval_status = "pending"
        contract = MagicMock()

        call_count = [0]
        def query_side(model):
            call_count[0] += 1
            q = MagicMock()
            if call_count[0] == 1:
                q.filter.return_value.first.return_value = approval
            else:
                q.filter.return_value.first.return_value = contract
            return q
        db.query.side_effect = query_side

        ContractEnhancedService.reject_contract(db, 1, 1, user_id=2, opinion="不合规")
        assert approval.approval_status == "rejected"
        assert approval.approver_id == 2
        assert contract.status == "draft"
        db.commit.assert_called_once()


# ======================= mark_as_signed =======================

class TestMarkAsSigned:
    def test_raises_when_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="合同不存在"):
            ContractEnhancedService.mark_as_signed(db, 999)

    def test_raises_when_not_approved(self):
        db = MagicMock()
        c = MagicMock()
        c.status = "draft"
        db.query.return_value.filter.return_value.first.return_value = c
        with pytest.raises(ValueError, match="只能标记已审批的合同为已签署"):
            ContractEnhancedService.mark_as_signed(db, 1)

    def test_sets_status_to_signed(self):
        db = MagicMock()
        c = MagicMock()
        c.status = "approved"
        db.query.return_value.filter.return_value.first.return_value = c
        ContractEnhancedService.mark_as_signed(db, 1)
        assert c.status == "signed"
        db.commit.assert_called_once()


# ======================= mark_as_executing =======================

class TestMarkAsExecuting:
    def test_raises_when_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="合同不存在"):
            ContractEnhancedService.mark_as_executing(db, 999)

    def test_raises_when_not_signed(self):
        db = MagicMock()
        c = MagicMock()
        c.status = "approved"
        db.query.return_value.filter.return_value.first.return_value = c
        with pytest.raises(ValueError, match="只能标记已签署的合同为执行中"):
            ContractEnhancedService.mark_as_executing(db, 1)

    def test_sets_status_to_executing(self):
        db = MagicMock()
        c = MagicMock()
        c.status = "signed"
        db.query.return_value.filter.return_value.first.return_value = c
        ContractEnhancedService.mark_as_executing(db, 1)
        assert c.status == "executing"


# ======================= mark_as_completed =======================

class TestMarkAsCompleted:
    def test_raises_when_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="合同不存在"):
            ContractEnhancedService.mark_as_completed(db, 999)

    def test_raises_when_not_executing(self):
        db = MagicMock()
        c = MagicMock()
        c.status = "signed"
        db.query.return_value.filter.return_value.first.return_value = c
        with pytest.raises(ValueError, match="只能标记执行中的合同为已完成"):
            ContractEnhancedService.mark_as_completed(db, 1)

    def test_sets_status_to_completed(self):
        db = MagicMock()
        c = MagicMock()
        c.status = "executing"
        db.query.return_value.filter.return_value.first.return_value = c
        ContractEnhancedService.mark_as_completed(db, 1)
        assert c.status == "completed"


# ======================= void_contract =======================

class TestVoidContract:
    def test_raises_when_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="合同不存在"):
            ContractEnhancedService.void_contract(db, 999)

    def test_raises_when_already_completed(self):
        db = MagicMock()
        c = MagicMock()
        c.status = "completed"
        db.query.return_value.filter.return_value.first.return_value = c
        with pytest.raises(ValueError, match="已完成的合同不能作废"):
            ContractEnhancedService.void_contract(db, 1)

    def test_voids_draft_contract(self):
        db = MagicMock()
        c = MagicMock()
        c.status = "draft"
        db.query.return_value.filter.return_value.first.return_value = c
        ContractEnhancedService.void_contract(db, 1)
        assert c.status == "voided"
        db.commit.assert_called_once()

    def test_voids_executing_contract(self):
        db = MagicMock()
        c = MagicMock()
        c.status = "executing"
        db.query.return_value.filter.return_value.first.return_value = c
        ContractEnhancedService.void_contract(db, 1)
        assert c.status == "voided"


# ======================= get_pending_approvals =======================

class TestGetPendingApprovals:
    def test_returns_pending_approvals(self):
        db = MagicMock()
        approvals = [MagicMock(), MagicMock()]
        (db.query.return_value
         .filter.return_value
         .options.return_value
         .all.return_value) = approvals
        result = ContractEnhancedService.get_pending_approvals(db, user_id=1)
        assert len(result) == 2

    def test_returns_empty_list_when_none(self):
        db = MagicMock()
        (db.query.return_value
         .filter.return_value
         .options.return_value
         .all.return_value) = []
        result = ContractEnhancedService.get_pending_approvals(db, user_id=1)
        assert result == []


# ======================= 条款管理 =======================

class TestContractTerms:
    @patch("app.services.sales.contract_enhanced.save_obj")
    def test_add_term_creates_term(self, mock_save):
        db = MagicMock()
        term_data = MagicMock()
        term_data.model_dump.return_value = {"term_content": "付款条款"}
        result = ContractEnhancedService.add_term(db, contract_id=1, term_data=term_data)
        mock_save.assert_called_once()
        assert result.contract_id == 1

    def test_get_terms_returns_list(self):
        db = MagicMock()
        terms = [MagicMock(), MagicMock()]
        db.query.return_value.filter.return_value.all.return_value = terms
        result = ContractEnhancedService.get_terms(db, 1)
        assert result == terms

    def test_update_term_sets_content(self):
        db = MagicMock()
        term = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = term
        result = ContractEnhancedService.update_term(db, 1, "新条款内容")
        assert term.term_content == "新条款内容"
        db.commit.assert_called_once()

    def test_update_term_returns_none_when_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = ContractEnhancedService.update_term(db, 99, "...")
        assert result is None

    @patch("app.services.sales.contract_enhanced.delete_obj")
    def test_delete_term_success(self, mock_delete):
        db = MagicMock()
        term = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = term
        result = ContractEnhancedService.delete_term(db, 1)
        assert result is True
        mock_delete.assert_called_once_with(db, term)

    def test_delete_term_not_found_returns_false(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = ContractEnhancedService.delete_term(db, 99)
        assert result is False


# ======================= 附件管理 =======================

class TestContractAttachments:
    @patch("app.services.sales.contract_enhanced.save_obj")
    def test_add_attachment_creates_attachment(self, mock_save):
        db = MagicMock()
        att_data = MagicMock()
        att_data.model_dump.return_value = {"file_name": "合同.pdf"}
        result = ContractEnhancedService.add_attachment(db, 1, att_data, user_id=5)
        mock_save.assert_called_once()
        assert result.uploaded_by == 5

    def test_get_attachments_returns_list(self):
        db = MagicMock()
        atts = [MagicMock()]
        db.query.return_value.filter.return_value.all.return_value = atts
        result = ContractEnhancedService.get_attachments(db, 1)
        assert result == atts

    @patch("app.services.sales.contract_enhanced.delete_obj")
    def test_delete_attachment_success(self, mock_delete):
        db = MagicMock()
        att = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = att
        result = ContractEnhancedService.delete_attachment(db, 1)
        assert result is True

    def test_delete_attachment_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        result = ContractEnhancedService.delete_attachment(db, 99)
        assert result is False


# ======================= get_contract_stats =======================

class TestGetContractStats:
    def test_returns_stats_structure(self):
        db = MagicMock()
        # All count queries return 0 or specific values
        q = MagicMock()
        q.filter.return_value.scalar.return_value = 5
        q.scalar.return_value = 10
        db.query.return_value = q

        result = ContractEnhancedService.get_contract_stats(db)
        assert result is not None
        assert hasattr(result, "total_count")
        assert hasattr(result, "total_amount")

    def test_handles_none_amounts_gracefully(self):
        """DB返回 None 时使用默认值"""
        db = MagicMock()
        q = MagicMock()
        q.scalar.return_value = None
        q.filter.return_value.scalar.return_value = None
        db.query.return_value = q

        result = ContractEnhancedService.get_contract_stats(db)
        assert result.total_amount == Decimal(0)
        assert result.total_count == 0


# ======================= 金额计算 (update_contract) =======================

class TestContractAmountCalculation:
    def test_unreceived_amount_recalculated_on_amount_update(self):
        """更新 total_amount 后 unreceived_amount 重算"""
        db = MagicMock()
        c = MagicMock()
        c.status = "draft"
        c.total_amount = Decimal("100000")
        c.received_amount = Decimal("20000")
        db.query.return_value.filter.return_value.first.return_value = c

        contract_data = MagicMock()
        contract_data.model_dump.return_value = {"total_amount": Decimal("200000")}
        contract_data.total_amount = Decimal("200000")
        contract_data.received_amount = None

        # Execute update – this will set c.total_amount = 200000
        # Then recalc: unreceived = 200000 - 20000 = 180000
        for field, value in {"total_amount": Decimal("200000")}.items():
            setattr(c, field, value)

        ContractEnhancedService.update_contract(db, 1, contract_data)
        assert c.unreceived_amount == c.total_amount - c.received_amount
