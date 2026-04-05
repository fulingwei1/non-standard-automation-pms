# -*- coding: utf-8 -*-
"""
审批工作流服务测试

测试 ApprovalWorkflowService 的核心功能
"""

from unittest.mock import Mock, MagicMock

import pytest
from sqlalchemy.orm import Session

from app.models.enums import ApprovalRecordStatusEnum


class TestApprovalWorkflowService:
    """审批工作流服务测试类"""

    @pytest.fixture
    def mock_db_session(self):
        """创建模拟的数据库会话"""
        db = Mock(spec=Session)
        db.query = Mock(return_value=Mock())
        return db

    @pytest.fixture
    def service(self, mock_db_session):
        """创建审批工作流服务实例"""
        from app.services.approval_workflow_service import ApprovalWorkflowService
        return ApprovalWorkflowService(mock_db_session)

    def test_approve_step_success(self, service, mock_db_session):
        """测试审批通过"""
        # Mock 查询返回审批记录
        record = Mock()
        record.id = 1
        record.status = ApprovalRecordStatusEnum.PENDING

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = record
        mock_db_session.query.return_value = mock_query

        # 执行测试
        result = service.approve_step(
            record_id=1,
            approver_id=200,
            comment="同意",
        )

        # 验证结果
        assert result.status == ApprovalRecordStatusEnum.APPROVED
        mock_db_session.commit.assert_called_once()

    def test_approve_step_not_found(self, service, mock_db_session):
        """测试审批记录不存在时抛出异常"""
        # Mock 查询返回空
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        # 执行测试并验证异常
        with pytest.raises(ValueError, match="审批记录不存在"):
            service.approve_step(
                record_id=999,
                approver_id=200,
            )

    def test_reject_step_success(self, service, mock_db_session):
        """测试审批驳回"""
        # Mock 查询返回审批记录
        record = Mock()
        record.id = 1
        record.status = ApprovalRecordStatusEnum.PENDING

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = record
        mock_db_session.query.return_value = mock_query

        # 执行测试
        result = service.reject_step(
            record_id=1,
            approver_id=200,
            comment="需要修改",
        )

        # 验证结果
        assert result.status == ApprovalRecordStatusEnum.REJECTED
        mock_db_session.commit.assert_called_once()

    def test_reject_step_not_found(self, service, mock_db_session):
        """测试驳回不存在的记录"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        with pytest.raises(ValueError, match="审批记录不存在"):
            service.reject_step(
                record_id=999,
                approver_id=200,
            )

    def test_withdraw_approval_success(self, service, mock_db_session):
        """测试撤回审批"""
        record = Mock()
        record.id = 1
        record.status = ApprovalRecordStatusEnum.PENDING

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = record
        mock_db_session.query.return_value = mock_query

        # 执行测试
        result = service.withdraw_approval(
            record_id=1,
            user_id=100,
            reason="不需要审批了",
        )

        # 验证结果
        assert result.status == ApprovalRecordStatusEnum.CANCELLED
        mock_db_session.commit.assert_called_once()

    def test_withdraw_approval_not_found(self, service, mock_db_session):
        """测试撤回不存在的审批"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query

        with pytest.raises(ValueError, match="审批记录不存在"):
            service.withdraw_approval(
                record_id=999,
                user_id=100,
            )

    def test_validate_approver(self, service):
        """测试审批人验证"""
        # 默认实现返回True
        result = service._validate_approver(record_id=1, approver_id=200)
        assert result is True