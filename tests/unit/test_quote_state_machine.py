# -*- coding: utf-8 -*-
"""
测试 Quote 状态机
"""

import pytest
from unittest.mock import Mock, patch

from app.core.state_machine.quote import QuoteStateMachine


class TestQuoteStateMachine:
    """测试 Quote 状态机"""

    @pytest.fixture
    def mock_quote(self):
        """创建模拟的 Quote 对象"""
        quote = Mock()
        quote.id = 1
        quote.status = "DRAFT"
        quote.quote_code = "QT-001"
        quote.quote_name = "测试报价"
        quote.total_amount = 100000
        quote.opportunity_id = 1
        quote.contract_id = None
        quote.sent_to = None
        quote.sent_via = None
        quote.sent_at = None
        quote.approved_at = None
        quote.rejected_at = None
        quote.accepted_at = None
        quote.converted_at = None
        quote.expired_at = None
        quote.cancelled_at = None
        quote.review_started_at = None
        quote.review_completed_at = None
        quote.rejection_reason = None
        quote.approval_opinion = None
        quote.acceptance_note = None
        quote.revision_notes = None
        quote.cancellation_reason = None
        quote.__class__.__name__ = "Quote"
        return quote

    @pytest.fixture
    def mock_db(self):
        """创建模拟的数据库会话"""
        return Mock()

    @pytest.fixture
    def mock_user(self):
        """创建模拟的用户对象"""
        user = Mock()
        user.id = 10
        user.name = "测试用户"
        user.username = "testuser"
        user.real_name = "测试用户"
        user.has_permission = Mock(return_value=True)
        return user

    def test_quote_state_machine_initialization(self, mock_quote, mock_db):
        """测试状态机初始化"""
        state_machine = QuoteStateMachine(mock_quote, mock_db)

        assert state_machine.model == mock_quote
        assert state_machine.db == mock_db
        assert state_machine.state_field == "status"
        assert state_machine.current_state == "DRAFT"

    def test_submit_for_approval(self, mock_quote, mock_db, mock_user):
        """测试提交审批转换 (DRAFT → PENDING_APPROVAL)"""
        state_machine = QuoteStateMachine(mock_quote, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'), \
             patch.object(state_machine, '_create_approval_records'):
            result = state_machine.transition_to(
                "PENDING_APPROVAL",
                current_user=mock_user,
                approver_ids=[1, 2, 3],
            )

        assert result is True
        assert mock_quote.status == "PENDING_APPROVAL"

    def test_submit_fails_without_amount(self, mock_quote, mock_db, mock_user):
        """测试金额为0时提交失败"""
        mock_quote.total_amount = 0
        state_machine = QuoteStateMachine(mock_quote, mock_db)

        with pytest.raises(ValueError, match="报价金额为0"):
            with patch.object(state_machine, '_create_audit_log'), \
                 patch.object(state_machine, '_send_notifications'):
                state_machine.transition_to("PENDING_APPROVAL", current_user=mock_user)

    def test_approve_from_pending(self, mock_quote, mock_db, mock_user):
        """测试快速批准 (PENDING_APPROVAL → APPROVED)"""
        mock_quote.status = "PENDING_APPROVAL"
        state_machine = QuoteStateMachine(mock_quote, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "APPROVED",
                current_user=mock_user,
                approval_opinion="符合要求",
            )

        assert result is True
        assert mock_quote.status == "APPROVED"
        assert mock_quote.approved_at is not None
        assert mock_quote.approval_opinion == "符合要求"

    def test_reject_from_pending(self, mock_quote, mock_db, mock_user):
        """测试审批拒绝 (PENDING_APPROVAL → REJECTED)"""
        mock_quote.status = "PENDING_APPROVAL"
        state_machine = QuoteStateMachine(mock_quote, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'), \
             patch.object(state_machine, '_cancel_pending_approvals'):
            result = state_machine.transition_to(
                "REJECTED",
                current_user=mock_user,
                rejection_reason="价格过高",
            )

        assert result is True
        assert mock_quote.status == "REJECTED"
        assert mock_quote.rejected_at is not None
        assert mock_quote.rejection_reason == "价格过高"

    def test_withdraw_approval(self, mock_quote, mock_db, mock_user):
        """测试撤回审批 (PENDING_APPROVAL → DRAFT)"""
        mock_quote.status = "PENDING_APPROVAL"
        state_machine = QuoteStateMachine(mock_quote, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'), \
             patch.object(state_machine, '_cancel_pending_approvals'):
            result = state_machine.transition_to(
                "DRAFT",
                current_user=mock_user,
            )

        assert result is True
        assert mock_quote.status == "DRAFT"

    def test_send_to_customer(self, mock_quote, mock_db, mock_user):
        """测试发送给客户 (APPROVED → SENT)"""
        mock_quote.status = "APPROVED"
        state_machine = QuoteStateMachine(mock_quote, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "SENT",
                current_user=mock_user,
                sent_to="张三",
                sent_via="EMAIL",
            )

        assert result is True
        assert mock_quote.status == "SENT"
        assert mock_quote.sent_at is not None
        assert mock_quote.sent_to == "张三"
        assert mock_quote.sent_via == "EMAIL"

    def test_customer_accept(self, mock_quote, mock_db, mock_user):
        """测试客户接受 (SENT → ACCEPTED)"""
        mock_quote.status = "SENT"
        state_machine = QuoteStateMachine(mock_quote, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "ACCEPTED",
                current_user=mock_user,
                acceptance_note="接受报价",
            )

        assert result is True
        assert mock_quote.status == "ACCEPTED"
        assert mock_quote.accepted_at is not None
        assert mock_quote.acceptance_note == "接受报价"

    def test_convert_to_contract(self, mock_quote, mock_db, mock_user):
        """测试转换为合同 (ACCEPTED → CONVERTED)"""
        mock_quote.status = "ACCEPTED"
        mock_quote.opportunity_id = 1
        state_machine = QuoteStateMachine(mock_quote, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'), \
             patch.object(state_machine, '_update_opportunity_status'):
            result = state_machine.transition_to(
                "CONVERTED",
                current_user=mock_user,
                contract_id=100,
            )

        assert result is True
        assert mock_quote.status == "CONVERTED"
        assert mock_quote.converted_at is not None
        assert mock_quote.contract_id == 100

    def test_cancel_quote(self, mock_quote, mock_db, mock_user):
        """测试取消报价 (DRAFT → CANCELLED)"""
        state_machine = QuoteStateMachine(mock_quote, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'), \
             patch.object(state_machine, '_cancel_pending_approvals'):
            result = state_machine.transition_to(
                "CANCELLED",
                current_user=mock_user,
                cancellation_reason="客户取消需求",
            )

        assert result is True
        assert mock_quote.status == "CANCELLED"
        assert mock_quote.cancelled_at is not None
        assert mock_quote.cancellation_reason == "客户取消需求"

    def test_expire_quote(self, mock_quote, mock_db, mock_user):
        """测试报价过期 (SENT → EXPIRED)"""
        mock_quote.status = "SENT"
        state_machine = QuoteStateMachine(mock_quote, mock_db)

        with patch.object(state_machine, '_create_audit_log'), \
             patch.object(state_machine, '_send_notifications'):
            result = state_machine.transition_to(
                "EXPIRED",
                current_user=mock_user,
            )

        assert result is True
        assert mock_quote.status == "EXPIRED"
        assert mock_quote.expired_at is not None

    def test_invalid_transition(self, mock_quote, mock_db, mock_user):
        """测试无效的状态转换"""
        from app.core.state_machine.exceptions import InvalidStateTransitionError

        state_machine = QuoteStateMachine(mock_quote, mock_db)

        # 尝试从 DRAFT 直接到 CONVERTED（无效）
        with pytest.raises(InvalidStateTransitionError):
            with patch.object(state_machine, '_create_audit_log'), \
                 patch.object(state_machine, '_send_notifications'):
                state_machine.transition_to("CONVERTED", current_user=mock_user)

    def test_get_allowed_transitions(self, mock_quote, mock_db):
        """测试获取允许的状态转换"""
        state_machine = QuoteStateMachine(mock_quote, mock_db)

        # DRAFT 状态允许的转换
        allowed = state_machine.get_allowed_transitions()
        assert "PENDING_APPROVAL" in allowed
        assert "CANCELLED" in allowed

        # APPROVED 状态允许的转换
        mock_quote.status = "APPROVED"
        state_machine = QuoteStateMachine(mock_quote, mock_db)
        allowed = state_machine.get_allowed_transitions()
        assert "SENT" in allowed
        assert "EXPIRED" in allowed
        assert "CANCELLED" in allowed


def test_quote_state_machine_import():
    """测试 QuoteStateMachine 可以正确导入"""
    from app.core.state_machine.quote import QuoteStateMachine

    assert QuoteStateMachine is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
