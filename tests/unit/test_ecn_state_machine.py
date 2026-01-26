# -*- coding: utf-8 -*-
"""
ECN状态机单元测试

测试ECN状态机的状态转换逻辑，包括新增的COMPLETED状态
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from app.core.state_machine.exceptions import InvalidStateTransitionError
from app.core.state_machine.ecn import EcnStateMachine
from app.models.enums.workflow import EcnStatusEnum


class MockEcnModel:
    """模拟ECN模型"""

    def __init__(self):
        self.status = EcnStatusEnum.DRAFT
        self.ecn_no = "ECN-TEST-001"
        self.change_reason = "测试变更原因"
        self.change_description = "测试变更描述"
        self.ecn_type = "DESIGN_CHANGE"
        self.approval_note = None
        self.approved_at = None
        self.execution_start = None
        self.execution_end = None
        self.execution_note = None


class TestEcnStateMachineInitialization:
    """ECN状态机初始化测试"""

    def test_initialization(self):
        """测试状态机初始化"""
        model = MockEcnModel()
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        assert sm.model == model
        assert sm.db == db
        assert sm.state_field == "status"
        assert sm.current_state == EcnStatusEnum.DRAFT

    def test_initialization_with_custom_state(self):
        """测试自定义初始状态初始化"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.APPROVED
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        assert sm.current_state == EcnStatusEnum.APPROVED


class TestEcnStateMachineDraftTransitions:
    """DRAFT状态转换测试"""

    def test_submit_for_review_valid(self):
        """测试从DRAFT提交审核"""
        model = MockEcnModel()
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        result = sm.transition_to(str(EcnStatusEnum.PENDING_REVIEW))
        assert result is True
        assert model.status == EcnStatusEnum.PENDING_REVIEW

    def test_cancel_draft_valid(self):
        """测试取消草稿"""
        model = MockEcnModel()
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        result = sm.transition_to(str(EcnStatusEnum.CANCELLED))
        assert result is True
        assert model.status == EcnStatusEnum.CANCELLED


class TestEcnStateMachinePendingReviewTransitions:
    """PENDING_REVIEW状态转换测试"""

    def test_approve_valid(self):
        """测试审批通过"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.PENDING_REVIEW
        model.approval_note = "同意此变更"
        model.approved_at = datetime.now()
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        result = sm.approve()
        assert result is True
        assert model.status == EcnStatusEnum.APPROVED

    def test_approve_without_note(self):
        """测试未填写审批意见时批准"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.PENDING_REVIEW
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        with pytest.raises(ValueError, match="审批意见不能为空"):
            sm.approve()

    def test_approve_without_approval_time(self):
        """测试未设置审批时间时批准"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.PENDING_REVIEW
        model.approval_note = "同意此变更"
        model.approved_at = None
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        with pytest.raises(ValueError, match="审批时间必须设置"):
            sm.approve()

    def test_reject_valid(self):
        """测试审批拒绝"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.PENDING_REVIEW
        model.approval_note = "需要更多说明"
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        result = sm.reject()
        assert result is True
        assert model.status == EcnStatusEnum.REJECTED

    def test_reject_without_note(self):
        """测试未填写拒绝原因时拒绝"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.PENDING_REVIEW
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        with pytest.raises(ValueError, match="拒绝原因不能为空"):
            sm.reject()


class TestEcnStateMachineApprovedTransitions:
    """APPROVED状态转换测试"""

    def test_implement_valid(self):
        """测试执行变更"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.APPROVED
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        result = sm.implement()
        assert result is True
        assert model.status == EcnStatusEnum.IMPLEMENTED
        assert model.execution_start is not None


class TestEcnStateMachineImplementedTransitions:
    """IMPLEMENTED状态转换测试"""

    def test_complete_valid(self):
        """测试完成验证"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.IMPLEMENTED
        model.execution_note = "已验证通过"
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        result = sm.complete()
        assert result is True
        assert model.status == EcnStatusEnum.COMPLETED
        assert model.execution_end is not None

    def test_complete_without_execution_note(self):
        """测试未填写执行说明时完成"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.IMPLEMENTED
        model.execution_note = None
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        with pytest.raises(ValueError, match="执行说明不能为空"):
            sm.complete()

    def test_cancel_implemented_valid(self):
        """测试取消已实施的变更"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.IMPLEMENTED
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        result = sm.cancel_implemented()
        assert result is True
        assert model.status == EcnStatusEnum.CANCELLED


class TestEcnStateMachineRejectedTransitions:
    """REJECTED状态转换测试"""

    def test_revise_valid(self):
        """测试重新编辑"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.REJECTED
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        result = sm.revise()
        assert result is True
        assert model.status == EcnStatusEnum.DRAFT

    def test_cancel_rejected_valid(self):
        """测试放弃变更"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.REJECTED
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        result = sm.cancel_rejected()
        assert result is True
        assert model.status == EcnStatusEnum.CANCELLED


class TestEcnStateMachineCompletedTransitions:
    """COMPLETED状态转换测试（新增）"""

    def test_cancel_completed_valid(self):
        """测试取消已完成的变更"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.COMPLETED
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        result = sm.cancel_completed()
        assert result is True
        assert model.status == EcnStatusEnum.CANCELLED


class TestEcnStateMachineHelperMethods:
    """ECN状态机辅助方法测试"""

    def test_get_next_states_from_draft(self):
        """测试从DRAFT获取下一状态"""
        model = MockEcnModel()
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        next_states = sm.get_next_states()
        assert EcnStatusEnum.PENDING_REVIEW in next_states
        assert EcnStatusEnum.CANCELLED in next_states

    def test_get_next_states_from_implemented(self):
        """测试从IMPLEMENTED获取下一状态（包含COMPLETED）"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.IMPLEMENTED
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        next_states = sm.get_next_states()
        assert EcnStatusEnum.COMPLETED in next_states
        assert EcnStatusEnum.CANCELLED in next_states

    def test_is_editable_true(self):
        """测试可编辑状态"""
        model = MockEcnModel()
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        assert sm.is_editable() is True

        model.status = EcnStatusEnum.REJECTED
        sm = EcnStateMachine(model, db)
        assert sm.is_editable() is True

    def test_is_editable_false(self):
        """测试不可编辑状态"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.APPROVED
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        assert sm.is_editable() is False

        model.status = EcnStatusEnum.COMPLETED
        sm = EcnStateMachine(model, db)
        assert sm.is_editable() is False

    def test_is_cancellable_all_states(self):
        """测试所有状态的可取消性"""
        model = MockEcnModel()
        db = MagicMock()

        cancellable_states = [
            EcnStatusEnum.DRAFT,
            EcnStatusEnum.PENDING_REVIEW,
            EcnStatusEnum.REJECTED,
            EcnStatusEnum.IMPLEMENTED,
            EcnStatusEnum.COMPLETED,
        ]

        for status in cancellable_states:
            model.status = status
            sm = EcnStateMachine(model, db)
            assert sm.is_cancellable() is True, f"Status {status} should be cancellable"

    def test_get_status_label(self):
        """测试获取状态中文标签"""
        model = MockEcnModel()
        db = MagicMock()

        test_cases = [
            (EcnStatusEnum.DRAFT, "草稿"),
            (EcnStatusEnum.PENDING_REVIEW, "待审核"),
            (EcnStatusEnum.APPROVED, "已批准"),
            (EcnStatusEnum.REJECTED, "已拒绝"),
            (EcnStatusEnum.IMPLEMENTED, "已实施"),
            (EcnStatusEnum.COMPLETED, "已完成"),
            (EcnStatusEnum.CANCELLED, "已取消"),
        ]

        for status, expected_label in test_cases:
            model.status = status
            sm = EcnStateMachine(model, db)
            label = sm.get_status_label()
            assert label == expected_label, (
                f"Status {status} should have label {expected_label}"
            )

    def test_get_status_label_unknown(self):
        """测试未知状态返回"""
        model = MockEcnModel()
        model.status = "UNKNOWN_STATUS"
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        label = sm.get_status_label()
        assert label == "未知状态"


class TestEcnStateMachineWorkflow:
    """ECN状态机完整工作流测试"""

    def test_full_workflow_from_draft_to_completed(self):
        """测试从草稿到完成的完整工作流"""
        model = MockEcnModel()
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        # DRAFT -> PENDING_REVIEW
        result = sm.submit_for_review()
        assert result is True
        assert sm.current_state == EcnStatusEnum.PENDING_REVIEW

        # PENDING_REVIEW -> APPROVED
        model.approval_note = "同意"
        model.approved_at = datetime.now()
        result = sm.approve()
        assert result is True
        assert sm.current_state == EcnStatusEnum.APPROVED

        # APPROVED -> IMPLEMENTED
        result = sm.implement()
        assert result is True
        assert sm.current_state == EcnStatusEnum.IMPLEMENTED

        # IMPLEMENTED -> COMPLETED
        model.execution_note = "已验证"
        result = sm.complete()
        assert result is True
        assert sm.current_state == EcnStatusEnum.COMPLETED

    def test_rejection_and_revision_workflow(self):
        """测试拒绝和修订工作流"""
        model = MockEcnModel()
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        # DRAFT -> PENDING_REVIEW
        result = sm.submit_for_review()
        assert result is True

        # PENDING_REVIEW -> REJECTED
        model.approval_note = "需要修改"
        result = sm.reject()
        assert result is True
        assert sm.current_state == EcnStatusEnum.REJECTED

        # REJECTED -> DRAFT
        result = sm.revise()
        assert result is True
        assert sm.current_state == EcnStatusEnum.DRAFT

    def test_cancel_workflow(self):
        """测试取消工作流"""
        model = MockEcnModel()
        db = MagicMock()

        # 从 DRAFT 取消
        sm = EcnStateMachine(model, db)
        result = sm.cancel_draft()
        assert result is True
        assert sm.current_state == EcnStatusEnum.CANCELLED

        # 从 IMPLEMENTED 取消
        model.status = EcnStatusEnum.IMPLEMENTED
        sm = EcnStateMachine(model, db)
        result = sm.cancel_implemented()
        assert result is True
        assert sm.current_state == EcnStatusEnum.CANCELLED

        # 从 COMPLETED 取消
        model.status = EcnStatusEnum.COMPLETED
        sm = EcnStateMachine(model, db)
        result = sm.cancel_completed()
        assert result is True
        assert sm.current_state == EcnStatusEnum.CANCELLED


class TestEcnStateMachineInvalidTransitions:
    """ECN状态机无效转换测试"""

    def test_invalid_transition_from_approved_to_draft(self):
        """测试从APPROVED到DRAFT的无效转换"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.APPROVED
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        can, reason = sm.can_transition_to(EcnStatusEnum.DRAFT)
        assert can is False
        assert "未定义" in reason or "无法转换" in reason

    def test_invalid_transition_from_implemented_to_draft(self):
        """测试从IMPLEMENTED到DRAFT的无效转换"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.IMPLEMENTED
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        can, reason = sm.can_transition_to(EcnStatusEnum.DRAFT)
        assert can is False

    def test_invalid_transition_from_completed_to_draft(self):
        """测试从COMPLETED到DRAFT的无效转换"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.COMPLETED
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        can, reason = sm.can_transition_to(EcnStatusEnum.DRAFT)
        assert can is False

    def test_invalid_transition_raises_error(self):
        """测试无效转换抛出异常"""
        model = MockEcnModel()
        model.status = EcnStatusEnum.APPROVED
        db = MagicMock()
        sm = EcnStateMachine(model, db)

        with pytest.raises(InvalidStateTransitionError):
            sm.transition_to(EcnStatusEnum.DRAFT)
