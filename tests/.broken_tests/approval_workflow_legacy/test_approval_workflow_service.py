# -*- coding: utf-8 -*-
"""
审批工作流服务单元测试

测试 ApprovalWorkflowService 类的所有公共方法
"""

from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.models.sales import (
    ApprovalHistory,
    ApprovalRecord,
    ApprovalWorkflowStep,
)
from app.models.enums import ApprovalRecordStatusEnum, ApprovalActionEnum
from app.services.approval_workflow import ApprovalWorkflowService


@pytest.mark.unit
class TestApprovalWorkflowService:
    """审批工作流服务测试类"""

    @pytest.fixture
    def db_session(self):
        """模拟数据库会话"""
        return MagicMock(spec=Session)

    @pytest.fixture
    def service(self, db_session):
        """创建服务实例"""
        return ApprovalWorkflowService(db_session)

    # ==================== 测试 approve_step() ====================

    def test_approve_step_success(self, service, db_session):
        """
        测试审批通过 - 成功

        Given: PENDING 状态的审批记录和有效的审批人
        When: 调用 approve_step
        Then: 审批通过，创建历史记录，更新步骤
        """
        mock_record = MagicMock(spec=ApprovalRecord)
        mock_record.id = 1
        mock_record.status = ApprovalRecordStatusEnum.PENDING
        mock_record.current_step = 1
        mock_record.workflow_id = 100

        mock_next_step = MagicMock(spec=ApprovalWorkflowStep)
        mock_next_step.step_order = 2

        def query_side_effect(model):
            mock_query = MagicMock()

            if model == ApprovalRecord:
                mock_query.filter.return_value.first.return_value = mock_record
            elif model == ApprovalWorkflowStep:
                mock_query.filter.return_value.first.return_value = None
                mock_query.and_.return_value.filter.return_value = MagicMock(
                    first=MagicMock(return_value=mock_next_step)
                )

            return mock_query

        db_session.query.side_effect = query_side_effect

        # 模拟 db.commit 和 db.refresh
        db_session.commit.return_value = None
        db_session.refresh.return_value = None
        db_session.add.return_value = None

        result = service.approve_step(record_id=1, approver_id=2, comment="同意")

        assert result is not None
        db_session.add.assert_called()
        db_session.commit.assert_called()

    def test_approve_step_not_pending(self, service, db_session):
        """
        测试审批通过 - 非 PENDING 状态

        Given: 非 PENDING 状态的审批记录
        When: 调用 approve_step
        Then: 抛出 ValueError
        """
        mock_record = MagicMock(spec=ApprovalRecord)
        mock_record.id = 1
        mock_record.status = ApprovalRecordStatusEnum.APPROVED

        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_record
        )

        with pytest.raises(ValueError, match="审批记录状态为.*，无法审批"):
            service.approve_step(record_id=1, approver_id=2)

    # ==================== 测试 reject_step() ====================

    def test_reject_step_success(self, service, db_session):
        """
        测试审批驳回 - 成功

        Given: PENDING 状态的审批记录
        When: 调用 reject_step
        Then: 驳回成功，创建历史记录
        """
        mock_record = MagicMock(spec=ApprovalRecord)
        mock_record.id = 1
        mock_record.status = ApprovalRecordStatusEnum.PENDING
        mock_record.current_step = 1

        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_record
        )
        db_session.commit.return_value = None
        db_session.refresh.return_value = None
        db_session.add.return_value = None

        result = service.reject_step(
            record_id=1, approver_id=2, comment="资料不全，请补充"
        )

        assert result is not None
        assert db_session.add.assert_called()

    def test_reject_step_empty_comment(self, service, db_session):
        """
        测试审批驳回 - 驳回原因为空

        Given: PENDING 状态的审批记录
        When: 调用 reject_step 且 comment 为空
        Then: 抛出 ValueError
        """
        mock_record = MagicMock(spec=ApprovalRecord)
        mock_record.id = 1
        mock_record.status = ApprovalRecordStatusEnum.PENDING

        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_record
        )

        with pytest.raises(ValueError, match="驳回原因不能为空"):
            service.reject_step(record_id=1, approver_id=2, comment="")

    # ==================== 测试 delegate_step() ====================

    def test_delegate_step_success(self, service, db_session):
        """
        测试审批委托 - 成功

        Given: PENDING 状态的审批记录和可委托的步骤
        When: 调用 delegate_step
        Then: 委托成功，创建历史记录
        """
        mock_record = MagicMock(spec=ApprovalRecord)
        mock_record.id = 1
        mock_record.status = ApprovalRecordStatusEnum.PENDING
        mock_record.current_step = 1

        mock_step = MagicMock(spec=ApprovalWorkflowStep)
        mock_step.step_order = 1
        mock_step.can_delegate = True

        def query_side_effect(model):
            mock_query = MagicMock()

            if model == ApprovalRecord:
                mock_query.filter.return_value.first.return_value = mock_record
            elif model == ApprovalWorkflowStep:
                mock_query.filter.return_value.first.return_value = mock_step

            return mock_query

        db_session.query.side_effect = query_side_effect
        db_session.commit.return_value = None
        db_session.refresh.return_value = None

        result = service.delegate_step(
            record_id=1, approver_id=2, delegate_to_id=3, comment="委托给技术总监审核"
        )

        assert result is not None
        db_session.add.assert_called()
        db_session.commit.assert_called()

    def test_delegate_step_not_delegatable(self, service, db_session):
        """
        测试审批委托 - 步骤不可委托

        Given: 不可委托的步骤
        When: 调用 delegate_step
        Then: 抛出 ValueError
        """
        mock_record = MagicMock(spec=ApprovalRecord)
        mock_record.id = 1
        mock_record.status = ApprovalRecordStatusEnum.PENDING

        mock_step = MagicMock(spec=ApprovalWorkflowStep)
        mock_step.can_delegate = False

        db_session.query.return_value.filter.return_value.first.return_value = mock_step

        with pytest.raises(ValueError, match="当前步骤不允许委托"):
            service.delegate_step(record_id=1, approver_id=2, delegate_to_id=3)

    # ==================== 测试 withdraw_approval() ====================

    def test_withdraw_approval_success(self, service, db_session):
        """
        测试撤回审批 - 成功

        Given: PENDING 状态的审批记录且为发起人
        When: 调用 withdraw_approval
        Then: 撤回成功，状态变为已取消
        """
        mock_record = MagicMock(spec=ApprovalRecord)
        mock_record.id = 1
        mock_record.status = ApprovalRecordStatusEnum.PENDING
        mock_record.current_step = 1
        mock_record.initiator_id = 2

        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_record
        )
        db_session.commit.return_value = None
        db_session.refresh.return_value = None

        result = service.withdraw_approval(
            record_id=1, initiator_id=2, comment="需要修改方案"
        )

        assert result is not None
        assert db_session.add.assert_called()
        db_session.commit.assert_called()

    def test_withdraw_approval_not_initiator(self, service, db_session):
        """
        测试撤回审批 - 非发起人

        Given: 非发起人试图撤回
        When: 调用 withdraw_approval
        Then: 抛出 ValueError
        """
        mock_record = MagicMock(spec=ApprovalRecord)
        mock_record.id = 1
        mock_record.status = ApprovalRecordStatusEnum.PENDING
        mock_record.initiator_id = 99

        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_record
        )

        with pytest.raises(ValueError, match="只有发起人才能撤回审批"):
            service.withdraw_approval(record_id=1, initiator_id=99)

    # ==================== 测试 get_current_step() ====================

    def test_get_current_step_success(self, service, db_session):
        """
        测试获取当前审批步骤 - 成功

        Given: 存在的审批记录和工作流步骤
        When: 调用 get_current_step
        Then: 返回步骤信息
        """
        mock_record = MagicMock(spec=ApprovalRecord)
        mock_record.id = 1
        mock_record.workflow_id = 100
        mock_record.current_step = 1

        mock_step = MagicMock(spec=ApprovalWorkflowStep)
        mock_step.step_order = 1
        mock_step.step_name = "技术评审"
        mock_step.approver_role = "TECHNICAL_DIRECTOR"
        mock_step.approver_id = 2
        mock_step.is_required = True
        mock_step.can_delegate = False
        mock_step.can_withdraw = True
        mock_step.due_hours = 48

        def query_side_effect(model):
            mock_query = MagicMock()

            if model == ApprovalRecord:
                mock_query.filter.return_value.first.return_value = mock_record
            elif model == ApprovalWorkflowStep:
                mock_query.filter.return_value.first.return_value = mock_step

            return mock_query

        db_session.query.side_effect = query_side_effect

        result = service.get_current_step(record_id=1)

        assert result is not None
        assert result["step_name"] == "技术评审"
        assert result["approver_role"] == "TECHNICAL_DIRECTOR"

    def test_get_current_step_not_found(self, service, db_session):
        """
        测试获取当前审批步骤 - 记录不存在

        Given: 不存在的审批记录ID
        When: 调用 get_current_step
        Then: 返回 None
        """
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = service.get_current_step(record_id=999)

        assert result is None

    # ==================== 测试 get_approval_history() ====================

    def test_get_approval_history_success(self, service, db_session):
        """
        测试获取审批历史 - 成功

        Given: 存在的审批记录和历史记录
        When: 调用 get_approval_history
        Then: 返回历史列表
        """
        mock_history1 = MagicMock(spec=ApprovalHistory)
        mock_history1.id = 1
        mock_history1.action = ApprovalActionEnum.APPROVE

        mock_history2 = MagicMock(spec=ApprovalHistory)
        mock_history2.id = 2
        mock_history2.action = ApprovalActionEnum.APPROVE

        db_session.query.return_value.order_by.return_value.all.return_value = [
            mock_history1,
            mock_history2,
        ]

        result = service.get_approval_history(record_id=1)

        assert result is not None
        assert len(result) == 2

    def test_get_approval_history_empty(self, service, db_session):
        """
        测试获取审批历史 - 无历史记录

        Given: 没有历史记录的审批
        When: 调用 get_approval_history
        Then: 返回空列表
        """
        db_session.query.return_value.order_by.return_value.all.return_value = []

        result = service.get_approval_history(record_id=1)

        assert result is not None
        assert len(result) == 0

    # ==================== 测试 get_approval_record() ====================

    def test_get_approval_record_success(self, service, db_session):
        """
        测试获取实体审批记录 - 成功

        Given: 存在的审批记录
        When: 调用 get_approval_record
        Then: 返回审批记录
        """
        mock_record = MagicMock(spec=ApprovalRecord)
        mock_record.id = 1
        mock_record.entity_type = "PROJECT"
        mock_record.entity_id = 100

        db_session.query.return_value.filter.return_value.first.return_value = (
            mock_record
        )

        result = service.get_approval_record(entity_type="PROJECT", entity_id=100)

        assert result is not None
        assert result.id == 1

    def test_get_approval_record_not_found(self, service, db_session):
        """
        测试获取实体审批记录 - 记录不存在

        Given: 不存在审批记录
        When: 调用 get_approval_record
        Then: 返回 None
        """
        db_session.query.return_value.filter.return_value.first.return_value = None

        result = service.get_approval_record(entity_type="PROJECT", entity_id=999)

        assert result is None
