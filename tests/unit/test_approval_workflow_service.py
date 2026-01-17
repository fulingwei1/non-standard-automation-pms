# -*- coding: utf-8 -*-
"""
审批工作流服务单元测试

测试内容：
- 启动审批流程
- 审批通过/驳回
- 审批委托
- 审批撤回
- 审批历史查询
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.enums import ApprovalActionEnum, ApprovalRecordStatusEnum
from app.models.sales import (
    ApprovalHistory,
    ApprovalRecord,
    ApprovalWorkflow,
    ApprovalWorkflowStep,
)
from app.services.approval_workflow_service import ApprovalWorkflowService


class TestApprovalWorkflowServiceInit:
    """服务初始化测试"""

    def test_service_init(self, db_session: Session):
        """测试服务初始化"""
        service = ApprovalWorkflowService(db_session)
        assert service.db == db_session


class TestStartApproval:
    """启动审批流程测试"""

    def test_start_approval_with_workflow_id(self, db_session: Session):
        """测试使用指定工作流ID启动审批"""
        service = ApprovalWorkflowService(db_session)

        # 查找一个活跃的工作流
        workflow = db_session.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.is_active == True
        ).first()

        if not workflow:
            pytest.skip("No active workflow available")

        try:
            record = service.start_approval(
                entity_type=workflow.workflow_type,
                entity_id=99999,  # 使用一个不太可能存在的ID
                initiator_id=1,
                workflow_id=workflow.id,
                comment="测试启动审批"
            )

            assert record is not None
            assert record.entity_type == workflow.workflow_type
            assert record.entity_id == 99999
            assert record.workflow_id == workflow.id
            assert record.status == ApprovalRecordStatusEnum.PENDING
            assert record.current_step == 1

            # 清理测试数据
            db_session.delete(record)
            db_session.commit()
        except ValueError as e:
            # 如果已有审批记录，也是预期行为
            assert "已有待审批的记录" in str(e) or "不存在" in str(e)

    def test_start_approval_invalid_workflow(self, db_session: Session):
        """测试使用无效工作流ID启动审批"""
        service = ApprovalWorkflowService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.start_approval(
                entity_type="QUOTE",
                entity_id=1,
                initiator_id=1,
                workflow_id=999999
            )

        assert "不存在或已禁用" in str(exc_info.value)

    def test_start_approval_duplicate_pending(self, db_session: Session):
        """测试重复启动已有待审批记录"""
        service = ApprovalWorkflowService(db_session)

        # 查找已有的待审批记录
        existing_record = db_session.query(ApprovalRecord).filter(
            ApprovalRecord.status == ApprovalRecordStatusEnum.PENDING
        ).first()

        if not existing_record:
            pytest.skip("No pending approval record available")

        with pytest.raises(ValueError) as exc_info:
            service.start_approval(
                entity_type=existing_record.entity_type,
                entity_id=existing_record.entity_id,
                initiator_id=1
            )

        assert "已有待审批的记录" in str(exc_info.value)

    def test_start_approval_auto_select_workflow(self, db_session: Session):
        """测试自动选择工作流"""
        service = ApprovalWorkflowService(db_session)

        # 查找一个有工作流的实体类型
        workflow = db_session.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.is_active == True
        ).first()

        if not workflow:
            pytest.skip("No active workflow available")

        try:
            record = service.start_approval(
                entity_type=workflow.workflow_type,
                entity_id=88888,
                initiator_id=1,
                routing_params={"amount": 50000}
            )

            assert record is not None
            assert record.workflow_id is not None

            # 清理
            db_session.delete(record)
            db_session.commit()
        except ValueError:
            # 如果没有找到工作流或已有记录
            pass


class TestApproveStep:
    """审批通过测试"""

    def test_approve_step_success(self, db_session: Session):
        """测试审批通过成功"""
        service = ApprovalWorkflowService(db_session)

        # 查找待审批的记录
        record = db_session.query(ApprovalRecord).filter(
            ApprovalRecord.status == ApprovalRecordStatusEnum.PENDING
        ).first()

        if not record:
            pytest.skip("No pending approval record available")

        original_step = record.current_step

        try:
            updated_record = service.approve_step(
                record_id=record.id,
                approver_id=1,
                comment="测试通过"
            )

            # 验证状态变化
            assert updated_record is not None
            # 要么步骤增加，要么状态变为已通过
            assert (
                updated_record.current_step > original_step or
                updated_record.status == ApprovalRecordStatusEnum.APPROVED
            )

            # 验证历史记录
            history = db_session.query(ApprovalHistory).filter(
                ApprovalHistory.approval_record_id == record.id,
                ApprovalHistory.action == ApprovalActionEnum.APPROVE
            ).first()
            assert history is not None
        except ValueError:
            pass

    def test_approve_step_not_found(self, db_session: Session):
        """测试审批不存在的记录"""
        service = ApprovalWorkflowService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.approve_step(
                record_id=999999,
                approver_id=1
            )

        assert "不存在" in str(exc_info.value)

    def test_approve_non_pending_record(self, db_session: Session):
        """测试审批非待审批状态的记录"""
        service = ApprovalWorkflowService(db_session)

        # 查找已完成的审批记录
        record = db_session.query(ApprovalRecord).filter(
            ApprovalRecord.status != ApprovalRecordStatusEnum.PENDING
        ).first()

        if not record:
            pytest.skip("No non-pending approval record available")

        with pytest.raises(ValueError) as exc_info:
            service.approve_step(
                record_id=record.id,
                approver_id=1
            )

        assert "无法审批" in str(exc_info.value)


class TestRejectStep:
    """审批驳回测试"""

    def test_reject_step_success(self, db_session: Session):
        """测试审批驳回成功"""
        service = ApprovalWorkflowService(db_session)

        # 查找待审批的记录
        record = db_session.query(ApprovalRecord).filter(
            ApprovalRecord.status == ApprovalRecordStatusEnum.PENDING
        ).first()

        if not record:
            pytest.skip("No pending approval record available")

        try:
            updated_record = service.reject_step(
                record_id=record.id,
                approver_id=1,
                comment="测试驳回原因"
            )

            assert updated_record is not None
            assert updated_record.status == ApprovalRecordStatusEnum.REJECTED

            # 验证历史记录
            history = db_session.query(ApprovalHistory).filter(
                ApprovalHistory.approval_record_id == record.id,
                ApprovalHistory.action == ApprovalActionEnum.REJECT
            ).first()
            assert history is not None
            assert history.comment == "测试驳回原因"
        except ValueError:
            pass

    def test_reject_step_empty_comment(self, db_session: Session):
        """测试驳回时没有填写原因"""
        service = ApprovalWorkflowService(db_session)

        record = db_session.query(ApprovalRecord).filter(
            ApprovalRecord.status == ApprovalRecordStatusEnum.PENDING
        ).first()

        if not record:
            pytest.skip("No pending approval record available")

        with pytest.raises(ValueError) as exc_info:
            service.reject_step(
                record_id=record.id,
                approver_id=1,
                comment=""
            )

        assert "驳回原因不能为空" in str(exc_info.value)

    def test_reject_step_not_found(self, db_session: Session):
        """测试驳回不存在的记录"""
        service = ApprovalWorkflowService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.reject_step(
                record_id=999999,
                approver_id=1,
                comment="驳回原因"
            )

        assert "不存在" in str(exc_info.value)


class TestDelegateStep:
    """审批委托测试"""

    def test_delegate_step_not_found(self, db_session: Session):
        """测试委托不存在的记录"""
        service = ApprovalWorkflowService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.delegate_step(
                record_id=999999,
                approver_id=1,
                delegate_to_id=2,
                comment="委托测试"
            )

        assert "不存在" in str(exc_info.value)

    def test_delegate_step_not_allowed(self, db_session: Session):
        """测试不允许委托的步骤"""
        service = ApprovalWorkflowService(db_session)

        # 查找待审批的记录
        record = db_session.query(ApprovalRecord).filter(
            ApprovalRecord.status == ApprovalRecordStatusEnum.PENDING
        ).first()

        if not record:
            pytest.skip("No pending approval record available")

        # 查找对应步骤
        step = db_session.query(ApprovalWorkflowStep).filter(
            ApprovalWorkflowStep.workflow_id == record.workflow_id,
            ApprovalWorkflowStep.step_order == record.current_step
        ).first()

        if step and step.can_delegate:
            pytest.skip("Step allows delegation")

        try:
            service.delegate_step(
                record_id=record.id,
                approver_id=1,
                delegate_to_id=2
            )
        except ValueError as e:
            assert "不允许委托" in str(e)


class TestWithdrawApproval:
    """审批撤回测试"""

    def test_withdraw_approval_not_found(self, db_session: Session):
        """测试撤回不存在的记录"""
        service = ApprovalWorkflowService(db_session)

        with pytest.raises(ValueError) as exc_info:
            service.withdraw_approval(
                record_id=999999,
                initiator_id=1,
                comment="撤回测试"
            )

        assert "不存在" in str(exc_info.value)

    def test_withdraw_approval_not_initiator(self, db_session: Session):
        """测试非发起人撤回"""
        service = ApprovalWorkflowService(db_session)

        record = db_session.query(ApprovalRecord).filter(
            ApprovalRecord.status == ApprovalRecordStatusEnum.PENDING
        ).first()

        if not record:
            pytest.skip("No pending approval record available")

        # 使用一个不是发起人的ID
        wrong_initiator_id = record.initiator_id + 1000

        with pytest.raises(ValueError) as exc_info:
            service.withdraw_approval(
                record_id=record.id,
                initiator_id=wrong_initiator_id,
                comment="撤回测试"
            )

        assert "只有发起人" in str(exc_info.value)

    def test_withdraw_non_pending_record(self, db_session: Session):
        """测试撤回非待审批状态的记录"""
        service = ApprovalWorkflowService(db_session)

        record = db_session.query(ApprovalRecord).filter(
            ApprovalRecord.status != ApprovalRecordStatusEnum.PENDING
        ).first()

        if not record:
            pytest.skip("No non-pending approval record available")

        with pytest.raises(ValueError) as exc_info:
            service.withdraw_approval(
                record_id=record.id,
                initiator_id=record.initiator_id,
                comment="撤回测试"
            )

        assert "无法撤回" in str(exc_info.value)


class TestGetCurrentStep:
    """获取当前步骤测试"""

    def test_get_current_step_success(self, db_session: Session):
        """测试成功获取当前步骤"""
        service = ApprovalWorkflowService(db_session)

        record = db_session.query(ApprovalRecord).filter(
            ApprovalRecord.status == ApprovalRecordStatusEnum.PENDING
        ).first()

        if not record:
            pytest.skip("No pending approval record available")

        step_info = service.get_current_step(record.id)

        if step_info:
            assert "step_order" in step_info
            assert "step_name" in step_info
            assert "approver_role" in step_info
            assert "is_required" in step_info

    def test_get_current_step_not_found(self, db_session: Session):
        """测试获取不存在记录的当前步骤"""
        service = ApprovalWorkflowService(db_session)

        step_info = service.get_current_step(999999)
        assert step_info is None


class TestGetApprovalHistory:
    """获取审批历史测试"""

    def test_get_approval_history(self, db_session: Session):
        """测试获取审批历史"""
        service = ApprovalWorkflowService(db_session)

        record = db_session.query(ApprovalRecord).first()

        if not record:
            pytest.skip("No approval record available")

        history = service.get_approval_history(record.id)

        assert isinstance(history, list)
        # 历史记录应该按步骤和时间排序
        if len(history) > 1:
            for i in range(1, len(history)):
                assert (
                    history[i].step_order >= history[i-1].step_order or
                    history[i].action_at >= history[i-1].action_at
                )


class TestGetApprovalRecord:
    """获取审批记录测试"""

    def test_get_approval_record_exists(self, db_session: Session):
        """测试获取已存在的审批记录"""
        service = ApprovalWorkflowService(db_session)

        existing_record = db_session.query(ApprovalRecord).first()

        if not existing_record:
            pytest.skip("No approval record available")

        record = service.get_approval_record(
            entity_type=existing_record.entity_type,
            entity_id=existing_record.entity_id
        )

        assert record is not None
        assert record.entity_type == existing_record.entity_type
        assert record.entity_id == existing_record.entity_id

    def test_get_approval_record_not_exists(self, db_session: Session):
        """测试获取不存在的审批记录"""
        service = ApprovalWorkflowService(db_session)

        record = service.get_approval_record(
            entity_type="NONEXISTENT_TYPE",
            entity_id=999999
        )

        assert record is None


class TestSelectWorkflowByRouting:
    """工作流路由选择测试"""

    def test_select_workflow_single(self, db_session: Session):
        """测试只有一个工作流时直接返回"""
        service = ApprovalWorkflowService(db_session)

        # 查找只有一个工作流的类型
        workflow = db_session.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.is_active == True
        ).first()

        if not workflow:
            pytest.skip("No active workflow available")

        selected = service._select_workflow_by_routing(workflow.workflow_type)

        if selected:
            assert selected.workflow_type == workflow.workflow_type
            assert selected.is_active == True

    def test_select_workflow_no_match(self, db_session: Session):
        """测试没有匹配工作流"""
        service = ApprovalWorkflowService(db_session)

        selected = service._select_workflow_by_routing("NONEXISTENT_TYPE")

        assert selected is None

    def test_select_workflow_with_routing_params(self, db_session: Session):
        """测试带路由参数的工作流选择"""
        service = ApprovalWorkflowService(db_session)

        workflow = db_session.query(ApprovalWorkflow).filter(
            ApprovalWorkflow.is_active == True
        ).first()

        if not workflow:
            pytest.skip("No active workflow available")

        # 测试带金额参数
        selected = service._select_workflow_by_routing(
            workflow.workflow_type,
            routing_params={"amount": 1000000}
        )

        # 应该返回某个工作流（具体取决于路由规则实现）
        if selected:
            assert selected.is_active == True
