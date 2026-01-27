# -*- coding: utf-8 -*-
"""
报价单状态机

状态转换规则：
- DRAFT → PENDING_APPROVAL: 提交审批
- DRAFT → CANCELLED: 取消报价
- PENDING_APPROVAL → IN_REVIEW: 进入评审
- PENDING_APPROVAL → APPROVED: 直接批准
- PENDING_APPROVAL → REJECTED: 审批拒绝
- PENDING_APPROVAL → DRAFT: 撤回审批
- IN_REVIEW → APPROVED: 评审通过
- IN_REVIEW → REJECTED: 评审拒绝
- IN_REVIEW → REVISION_REQUIRED: 需要修改
- APPROVED → SENT: 发送给客户
- APPROVED → EXPIRED: 报价过期
- APPROVED → CANCELLED: 取消报价
- REJECTED → DRAFT: 重新起草
- REJECTED → CANCELLED: 取消报价
- REVISION_REQUIRED → DRAFT: 返回草稿
- REVISION_REQUIRED → PENDING_APPROVAL: 修改后重新提交
- SENT → ACCEPTED: 客户接受
- SENT → REJECTED: 客户拒绝
- SENT → EXPIRED: 报价过期
- ACCEPTED → CONVERTED: 转换为合同
- EXPIRED → DRAFT: 重新起草
"""

from datetime import datetime
from sqlalchemy.orm import Session

from app.core.state_machine.base import StateMachine
from app.core.state_machine.decorators import transition
from app.models.sales.quotes import Quote


class QuoteStateMachine(StateMachine):
    """报价单状态机"""

    def __init__(self, quote: Quote, db: Session):
        """初始化报价状态机"""
        super().__init__(quote, db, state_field='status')

    # ==================== 审批流程转换 ====================

    @transition(
        from_state="DRAFT",
        to_state="PENDING_APPROVAL",
        required_permission="quote:submit",
        action_type="SUBMIT",
        notify_users=["approvers"],
        notification_template="quote_submitted",
    )
    def submit_for_approval(self, from_state: str, to_state: str, **kwargs):
        """
        提交审批（草稿→待审批）

        Args:
            approver_ids: 审批人ID列表（可选）
        """
        # 验证报价内容完整性
        if self.model.total_amount == 0:
            raise ValueError("报价金额为0，无法提交审批")

        # 创建审批记录
        if 'approver_ids' in kwargs:
            self._create_approval_records(kwargs['approver_ids'])

    @transition(
        from_state="PENDING_APPROVAL",
        to_state="IN_REVIEW",
        required_permission="quote:review",
        action_type="START_REVIEW",
        notify_users=["owner", "reviewers"],
        notification_template="quote_in_review",
    )
    def start_review(self, from_state: str, to_state: str, **kwargs):
        """开始评审（待审批→评审中）"""
        self.model.review_started_at = datetime.now()

    @transition(
        from_state="PENDING_APPROVAL",
        to_state="APPROVED",
        required_permission="quote:approve",
        action_type="APPROVE_QUICK",
        notify_users=["owner", "created_by"],
        notification_template="quote_approved",
    )
    def approve_quick(self, from_state: str, to_state: str, **kwargs):
        """
        快速批准（待审批→已批准，无需评审）

        Args:
            approval_opinion: 审批意见（可选）
        """
        self.model.approved_at = datetime.now()
        if 'approval_opinion' in kwargs:
            self.model.approval_opinion = kwargs['approval_opinion']

    @transition(
        from_state="PENDING_APPROVAL",
        to_state="REJECTED",
        required_permission="quote:approve",
        action_type="REJECT",
        notify_users=["owner", "created_by"],
        notification_template="quote_rejected",
    )
    def reject_from_pending(self, from_state: str, to_state: str, **kwargs):
        """
        审批拒绝（待审批→已拒绝）

        Args:
            rejection_reason: 拒绝原因
        """
        self.model.rejected_at = datetime.now()
        if 'rejection_reason' in kwargs:
            self.model.rejection_reason = kwargs['rejection_reason']

    @transition(
        from_state="PENDING_APPROVAL",
        to_state="DRAFT",
        action_type="WITHDRAW",
        notify_users=["approvers"],
        notification_template="quote_withdrawn",
    )
    def withdraw(self, from_state: str, to_state: str, **kwargs):
        """撤回审批（待审批→草稿）"""
        # 取消待处理的审批记录
        self._cancel_pending_approvals()

    # ==================== 评审流程转换 ====================

    @transition(
        from_state="IN_REVIEW",
        to_state="APPROVED",
        required_permission="quote:approve",
        action_type="APPROVE",
        notify_users=["owner", "created_by"],
        notification_template="quote_approved",
    )
    def approve_after_review(self, from_state: str, to_state: str, **kwargs):
        """
        评审通过（评审中→已批准）

        Args:
            approval_opinion: 审批意见（可选）
        """
        self.model.approved_at = datetime.now()
        self.model.review_completed_at = datetime.now()
        if 'approval_opinion' in kwargs:
            self.model.approval_opinion = kwargs['approval_opinion']

    @transition(
        from_state="IN_REVIEW",
        to_state="REJECTED",
        required_permission="quote:approve",
        action_type="REJECT",
        notify_users=["owner", "created_by"],
        notification_template="quote_rejected",
    )
    def reject_after_review(self, from_state: str, to_state: str, **kwargs):
        """
        评审拒绝（评审中→已拒绝）

        Args:
            rejection_reason: 拒绝原因
        """
        self.model.rejected_at = datetime.now()
        self.model.review_completed_at = datetime.now()
        if 'rejection_reason' in kwargs:
            self.model.rejection_reason = kwargs['rejection_reason']

    @transition(
        from_state="IN_REVIEW",
        to_state="REVISION_REQUIRED",
        required_permission="quote:review",
        action_type="REQUEST_REVISION",
        notify_users=["owner", "created_by"],
        notification_template="quote_revision_required",
    )
    def request_revision(self, from_state: str, to_state: str, **kwargs):
        """
        需要修改（评审中→需修改）

        Args:
            revision_notes: 修改意见
        """
        if 'revision_notes' in kwargs:
            self.model.revision_notes = kwargs['revision_notes']

    # ==================== 客户交互转换 ====================

    @transition(
        from_state="APPROVED",
        to_state="SENT",
        required_permission="quote:send",
        action_type="SEND",
        notify_users=["owner"],
        notification_template="quote_sent",
    )
    def send_to_customer(self, from_state: str, to_state: str, **kwargs):
        """
        发送给客户（已批准→已发送）

        Args:
            sent_to: 发送对象
            sent_via: 发送方式（EMAIL/WECHAT/OTHER）
        """
        self.model.sent_at = datetime.now()
        if 'sent_to' in kwargs:
            self.model.sent_to = kwargs['sent_to']
        if 'sent_via' in kwargs:
            self.model.sent_via = kwargs['sent_via']

    @transition(
        from_state="SENT",
        to_state="ACCEPTED",
        required_permission="quote:accept",
        action_type="ACCEPT",
        notify_users=["owner", "created_by", "sales_team"],
        notification_template="quote_accepted",
    )
    def accept_by_customer(self, from_state: str, to_state: str, **kwargs):
        """
        客户接受（已发送→已接受）

        Args:
            acceptance_note: 接受说明
        """
        self.model.accepted_at = datetime.now()
        if 'acceptance_note' in kwargs:
            self.model.acceptance_note = kwargs['acceptance_note']

    @transition(
        from_state="SENT",
        to_state="REJECTED",
        action_type="REJECT_BY_CUSTOMER",
        notify_users=["owner", "created_by"],
        notification_template="quote_rejected_by_customer",
    )
    def reject_by_customer(self, from_state: str, to_state: str, **kwargs):
        """
        客户拒绝（已发送→已拒绝）

        Args:
            rejection_reason: 拒绝原因
        """
        self.model.customer_rejected_at = datetime.now()
        if 'rejection_reason' in kwargs:
            self.model.rejection_reason = kwargs['rejection_reason']

    # ==================== 转换与重启流程 ====================

    @transition(
        from_state="ACCEPTED",
        to_state="CONVERTED",
        required_permission="quote:convert",
        action_type="CONVERT",
        notify_users=["owner", "created_by"],
        notification_template="quote_converted",
    )
    def convert_to_contract(self, from_state: str, to_state: str, **kwargs):
        """
        转换为合同（已接受→已转换）

        Args:
            contract_id: 合同ID
        """
        self.model.converted_at = datetime.now()
        if 'contract_id' in kwargs:
            self.model.contract_id = kwargs['contract_id']

        # 业务逻辑：更新商机状态
        self._update_opportunity_status("WON")

    @transition(
        from_state="REJECTED",
        to_state="DRAFT",
        action_type="REDRAFT",
        notify_users=["owner"],
        notification_template="quote_redrafted",
    )
    def redraft_after_rejection(self, from_state: str, to_state: str, **kwargs):
        """重新起草（已拒绝→草稿）"""
        # 清除拒绝相关信息
        self.model.rejected_at = None
        self.model.rejection_reason = None

    @transition(
        from_state="REVISION_REQUIRED",
        to_state="DRAFT",
        action_type="REVISE",
        notify_users=["owner"],
        notification_template="quote_revised",
    )
    def revise_to_draft(self, from_state: str, to_state: str, **kwargs):
        """修改后返回草稿（需修改→草稿）"""
        pass

    @transition(
        from_state="REVISION_REQUIRED",
        to_state="PENDING_APPROVAL",
        required_permission="quote:submit",
        action_type="RESUBMIT",
        notify_users=["approvers"],
        notification_template="quote_resubmitted",
    )
    def resubmit_after_revision(self, from_state: str, to_state: str, **kwargs):
        """修改后重新提交（需修改→待审批）"""
        # 清除修改意见
        self.model.revision_notes = None

    @transition(
        from_state="EXPIRED",
        to_state="DRAFT",
        action_type="RENEW",
        notify_users=["owner"],
        notification_template="quote_renewed",
    )
    def renew_after_expiry(self, from_state: str, to_state: str, **kwargs):
        """过期后重新起草（已过期→草稿）"""
        # 清除过期标记
        self.model.expired_at = None

    # ==================== 取消与过期 ====================

    @transition(
        from_state="DRAFT",
        to_state="CANCELLED",
        action_type="CANCEL",
        notify_users=["owner"],
        notification_template="quote_cancelled",
    )
    def cancel_from_draft(self, from_state: str, to_state: str, **kwargs):
        """取消报价（草稿→已取消）"""
        self._handle_cancel(**kwargs)

    @transition(
        from_state="APPROVED",
        to_state="CANCELLED",
        required_permission="quote:cancel",
        action_type="CANCEL",
        notify_users=["owner", "approvers"],
        notification_template="quote_cancelled",
    )
    def cancel_from_approved(self, from_state: str, to_state: str, **kwargs):
        """取消报价（已批准→已取消）"""
        self._handle_cancel(**kwargs)

    @transition(
        from_state="REJECTED",
        to_state="CANCELLED",
        action_type="CANCEL",
        notify_users=["owner"],
        notification_template="quote_cancelled",
    )
    def cancel_from_rejected(self, from_state: str, to_state: str, **kwargs):
        """取消报价（已拒绝→已取消）"""
        self._handle_cancel(**kwargs)

    @transition(
        from_state="APPROVED",
        to_state="EXPIRED",
        action_type="EXPIRE",
        notify_users=["owner"],
        notification_template="quote_expired",
    )
    def expire_from_approved(self, from_state: str, to_state: str, **kwargs):
        """报价过期（已批准→已过期）"""
        self.model.expired_at = datetime.now()

    @transition(
        from_state="SENT",
        to_state="EXPIRED",
        action_type="EXPIRE",
        notify_users=["owner"],
        notification_template="quote_expired",
    )
    def expire_from_sent(self, from_state: str, to_state: str, **kwargs):
        """报价过期（已发送→已过期）"""
        self.model.expired_at = datetime.now()

    # ==================== 业务逻辑辅助方法 ====================

    def _create_approval_records(self, approver_ids):
        """创建审批记录"""
        try:
            from app.models.sales.quotes import QuoteApproval
            for idx, approver_id in enumerate(approver_ids, 1):
                approval = QuoteApproval(
                    quote_id=self.model.id,
                    approval_level=idx,
                    approver_id=approver_id,
                    status="PENDING",
                )
                self.db.add(approval)
            self.db.flush()
        except Exception as e:
            import logging
            logging.warning(f"创建审批记录失败：{str(e)}")

    def _cancel_pending_approvals(self):
        """取消待处理的审批记录"""
        try:
            from app.models.sales.quotes import QuoteApproval
            pending_approvals = (
                self.db.query(QuoteApproval)
                .filter(
                    QuoteApproval.quote_id == self.model.id,
                    QuoteApproval.status == "PENDING"
                )
                .all()
            )
            for approval in pending_approvals:
                approval.status = "CANCELLED"
            self.db.flush()
        except Exception as e:
            import logging
            logging.warning(f"取消审批记录失败：{str(e)}")

    def _update_opportunity_status(self, status: str):
        """更新商机状态"""
        try:
            if self.model.opportunity_id:
                from app.models.sales.opportunities import Opportunity
                opportunity = (
                    self.db.query(Opportunity)
                    .filter(Opportunity.id == self.model.opportunity_id)
                    .first()
                )
                if opportunity:
                    opportunity.stage = status
                    self.db.flush()
        except Exception as e:
            import logging
            logging.warning(f"更新商机状态失败：{str(e)}")

    def _handle_cancel(self, **kwargs):
        """处理取消逻辑"""
        self.model.cancelled_at = datetime.now()
        if 'cancellation_reason' in kwargs:
            self.model.cancellation_reason = kwargs['cancellation_reason']

        # 取消所有待处理的审批
        self._cancel_pending_approvals()
