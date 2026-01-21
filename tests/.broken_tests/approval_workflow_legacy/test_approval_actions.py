# -*- coding: utf-8 -*-
"""
approval_workflow/approval_actions.py 单元测试

测试审批操作模块的各种方法
"""

import pytest
from unittest.mock import MagicMock

from app.models.enums import ApprovalRecordStatusEnum
from app.services.approval_workflow.approval_actions import ApprovalActionsMixin


class TestApprovalActionsService(ApprovalActionsMixin):
    """测试用的服务类，继承混入类"""

    def __init__(self, db):
        self.db = db

    def _validate_approver(self, step, approver_id):
        """Mock 验证方法"""
        return True


@pytest.mark.unit
class TestApproveStep:
    """测试 approve_step 方法"""

    def test_approve_step_success(self):
        """测试审批通过成功"""
        mock_db = MagicMock()
        service = TestApprovalActionsService(db=mock_db)

        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.status = ApprovalRecordStatusEnum.PENDING
        mock_record.current_step = 1
        mock_record.workflow_id = 100

        mock_step = MagicMock()

        mock_next_step = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [mock_record, mock_step, mock_next_step]
        mock_db.query.return_value = mock_query

        result = service.approve_step(record_id=1, approver_id=10, comment="同意")

        assert result == mock_record
        assert result.current_step == 2
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
        mock_db.refresh.assert_called_with(mock_record)

    def test_approve_step_last_step(self):
        """测试最后一步审批通过"""
        mock_db = MagicMock()
        service = TestApprovalActionsService(db=mock_db)

        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.status = ApprovalRecordStatusEnum.PENDING
        mock_record.current_step = 1
        mock_record.workflow_id = 100

        mock_step = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [mock_record, mock_step, None]
        mock_db.query.return_value = mock_query

        result = service.approve_step(record_id=1, approver_id=10, comment="同意")

        assert result.status == ApprovalRecordStatusEnum.APPROVED
        mock_db.commit.assert_called()

    def test_approve_step_record_not_found(self):
        """测试审批记录不存在"""
        mock_db = MagicMock()
        service = TestApprovalActionsService(db=mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="审批记录不存在"):
            service.approve_step(record_id=1, approver_id=10)

    def test_approve_step_invalid_status(self):
        """测试无效状态审批"""
        mock_db = MagicMock()
        service = TestApprovalActionsService(db=mock_db)

        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.status = ApprovalRecordStatusEnum.APPROVED

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_record
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="无法审批"):
            service.approve_step(record_id=1, approver_id=10)


@pytest.mark.unit
class TestRejectStep:
    """测试 reject_step 方法"""

    def test_reject_step_success(self):
        """测试审批驳回成功"""
        mock_db = MagicMock()
        service = TestApprovalActionsService(db=mock_db)

        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.status = ApprovalRecordStatusEnum.PENDING

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_record
        mock_db.query.return_value = mock_query

        result = service.reject_step(record_id=1, approver_id=10, comment="需要修改")

        assert result == mock_record
        assert result.status == ApprovalRecordStatusEnum.REJECTED
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
        mock_db.refresh.assert_called_with(mock_record)

    def test_reject_step_empty_comment(self):
        """测试驳回原因必填"""
        mock_db = MagicMock()
        service = TestApprovalActionsService(db=mock_db)

        with pytest.raises(ValueError, match="驳回原因不能为空"):
            service.reject_step(record_id=1, approver_id=10, comment="")

    def test_reject_step_record_not_found(self):
        """测试审批记录不存在"""
        mock_db = MagicMock()
        service = TestApprovalActionsService(db=mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="审批记录不存在"):
            service.reject_step(record_id=1, approver_id=10, comment="拒绝")


@pytest.mark.unit
class TestDelegateStep:
    """测试 delegate_step 方法"""

    def test_delegate_step_success(self):
        """测试委托审批成功"""
        mock_db = MagicMock()
        service = TestApprovalActionsService(db=mock_db)

        mock_record = MagicMock()
        mock_record.id = 1

        mock_step = MagicMock()
        mock_step.can_delegate = True
        mock_step.approver_id = 10

        track_step = [mock_step]

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [mock_record, mock_step, None]
        mock_db.query.return_value = mock_query

        result = service.delegate_step(
            record_id=1, approver_id=10, delegate_to_id=20, comment="委托处理"
        )

        assert result == mock_record
        assert track_step[0].approver_id == 20
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
        mock_db.refresh.assert_called_with(mock_record)

    def test_delegate_step_not_allowed(self):
        """测试不允许委托"""
        mock_db = MagicMock()
        service = TestApprovalActionsService(db=mock_db)

        mock_record = MagicMock()
        mock_record.id = 1

        mock_step = MagicMock()
        mock_step.can_delegate = False

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_step
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="不允许委托"):
            service.delegate_step(record_id=1, approver_id=10, delegate_to_id=20)


@pytest.mark.unit
class TestWithdrawApproval:
    """测试 withdraw_approval 方法"""

    def test_withdraw_approval_success(self):
        """测试撤回审批成功"""
        mock_db = MagicMock()
        service = TestApprovalActionsService(db=mock_db)

        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.initiator_id = 10
        mock_record.status = ApprovalRecordStatusEnum.PENDING
        mock_record.current_step = 1

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [mock_record, None]
        mock_db.query.return_value = mock_query

        result = service.withdraw_approval(
            record_id=1, initiator_id=10, comment="取消申请"
        )

        assert result == mock_record
        assert result.status == ApprovalRecordStatusEnum.CANCELLED
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
        mock_db.refresh.assert_called_with(mock_record)

    def test_withdraw_approval_not_initiator(self):
        """测试非发起人撤回"""
        mock_db = MagicMock()
        service = TestApprovalActionsService(db=mock_db)

        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.initiator_id = 10
        mock_record.status = ApprovalRecordStatusEnum.PENDING

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_record
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="只有发起人才能撤回"):
            service.withdraw_approval(record_id=1, initiator_id=20, comment="撤回")

    def test_withdraw_approval_already_approved(self):
        """测试已有审批人通过"""
        mock_db = MagicMock()
        service = TestApprovalActionsService(db=mock_db)

        mock_record = MagicMock()
        mock_record.id = 1
        mock_record.initiator_id = 10
        mock_record.status = ApprovalRecordStatusEnum.PENDING

        mock_history = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [mock_record, mock_history]
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="已有审批人通过"):
            service.withdraw_approval(record_id=1, initiator_id=10, comment="撤回")
