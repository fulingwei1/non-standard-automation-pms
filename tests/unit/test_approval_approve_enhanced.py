# -*- coding: utf-8 -*-
"""
审批处理功能增强测试
补充覆盖核心业务逻辑和异常场景,提升覆盖率到60%+
"""
import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime

# 由于approve.py是一个Mixin,需要配合core使用
# 这里测试approve的各个方法


@pytest.fixture
def db_mock():
    """数据库mock"""
    return MagicMock()


@pytest.fixture
def mock_engine():
    """Mock的审批引擎"""
    from app.services.approval_engine.engine.core import ApprovalEngineCore
    
    engine = ApprovalEngineCore.__new__(ApprovalEngineCore)
    engine.db = MagicMock()
    engine.executor = MagicMock()
    engine.notify = MagicMock()
    
    # Mock辅助方法
    engine._get_and_validate_task = MagicMock()
    engine._log_action = MagicMock()
    engine._advance_to_next_node = MagicMock()
    engine._get_previous_node = MagicMock()
    engine._return_to_node = MagicMock()
    engine._call_adapter_callback = MagicMock()
    
    return engine


@pytest.fixture
def sample_task():
    """示例任务"""
    task = MagicMock()
    task.id = 100
    task.instance_id = 50
    task.node_id = 10
    task.status = "PENDING"
    task.assignee_id = 200
    
    task.instance = MagicMock()
    task.instance.id = 50
    task.instance.status = "PENDING"
    task.instance.template_id = 5
    task.instance.title = "测试审批"
    
    task.node = MagicMock()
    task.node.id = 10
    task.node.can_transfer = True
    task.node.can_add_approver = True
    
    return task


@pytest.fixture
def sample_user():
    """示例用户"""
    user = MagicMock()
    user.id = 200
    user.real_name = "张三"
    user.username = "zhangsan"
    return user


class TestApprove:
    """测试审批通过"""
    
    def test_approve_success(self, mock_engine, sample_task, sample_user):
        """测试成功审批通过"""
        from app.services.approval_engine.engine.approve import ApprovalProcessMixin
        
        # 绑定方法
        mock_engine._get_and_validate_task.return_value = sample_task
        mock_engine.db.query.return_value.filter.return_value.first.return_value = sample_user
        mock_engine.executor.process_approval.return_value = (True, None)
        
        result = ApprovalProcessMixin.approve(
            mock_engine,
            task_id=100,
            approver_id=200,
            comment="同意"
        )
        
        assert result == sample_task
        mock_engine.executor.process_approval.assert_called_once()
        mock_engine._log_action.assert_called_once()
        mock_engine._advance_to_next_node.assert_called_once()
        mock_engine.db.commit.assert_called_once()
    
    def test_approve_cannot_proceed(self, mock_engine, sample_task, sample_user):
        """测试审批后不能流转"""
        from app.services.approval_engine.engine.approve import ApprovalProcessMixin
        
        mock_engine._get_and_validate_task.return_value = sample_task
        mock_engine.db.query.return_value.filter.return_value.first.return_value = sample_user
        mock_engine.executor.process_approval.return_value = (False, None)  # 不能流转
        
        result = ApprovalProcessMixin.approve(
            mock_engine,
            task_id=100,
            approver_id=200,
            comment="同意"
        )
        
        assert result == sample_task
        mock_engine._advance_to_next_node.assert_not_called()  # 不应该流转
        mock_engine.db.commit.assert_called_once()
    
    def test_approve_with_attachments_and_eval_data(self, mock_engine, sample_task, sample_user):
        """测试带附件和评估数据的审批"""
        from app.services.approval_engine.engine.approve import ApprovalProcessMixin
        
        mock_engine._get_and_validate_task.return_value = sample_task
        mock_engine.db.query.return_value.filter.return_value.first.return_value = sample_user
        mock_engine.executor.process_approval.return_value = (True, None)
        
        attachments = [{"name": "file1.pdf", "url": "http://example.com/file1.pdf"}]
        eval_data = {"cost_estimate": 5000.0, "risk_assessment": "低"}
        
        result = ApprovalProcessMixin.approve(
            mock_engine,
            task_id=100,
            approver_id=200,
            comment="同意",
            attachments=attachments,
            eval_data=eval_data
        )
        
        # 验证传递了所有参数
        call_args = mock_engine.executor.process_approval.call_args
        assert call_args[1]["attachments"] == attachments
        assert call_args[1]["eval_data"] == eval_data


class TestReject:
    """测试审批驳回"""
    
    def test_reject_to_start(self, mock_engine, sample_task, sample_user):
        """测试驳回到发起人"""
        from app.services.approval_engine.engine.approve import ApprovalProcessMixin
        
        mock_engine._get_and_validate_task.return_value = sample_task
        mock_engine.db.query.return_value.filter.return_value.first.return_value = sample_user
        mock_engine.executor.process_approval.return_value = (False, None)
        
        result = ApprovalProcessMixin.reject(
            mock_engine,
            task_id=100,
            approver_id=200,
            comment="不符合要求",
            reject_to="START"
        )
        
        assert result == sample_task
        assert sample_task.instance.status == "REJECTED"
        assert sample_task.instance.completed_at is not None
        mock_engine._call_adapter_callback.assert_called_once_with(sample_task.instance, "on_rejected")
        mock_engine.notify.notify_rejected.assert_called_once()
        mock_engine.db.commit.assert_called_once()
    
    def test_reject_to_previous_node(self, mock_engine, sample_task, sample_user):
        """测试驳回到上一节点"""
        from app.services.approval_engine.engine.approve import ApprovalProcessMixin
        
        prev_node = MagicMock()
        prev_node.id = 5
        
        mock_engine._get_and_validate_task.return_value = sample_task
        mock_engine.db.query.return_value.filter.return_value.first.return_value = sample_user
        mock_engine.executor.process_approval.return_value = (False, None)
        mock_engine._get_previous_node.return_value = prev_node
        
        result = ApprovalProcessMixin.reject(
            mock_engine,
            task_id=100,
            approver_id=200,
            comment="请修改",
            reject_to="PREV"
        )
        
        mock_engine._return_to_node.assert_called_once_with(sample_task.instance, prev_node)
        mock_engine.db.commit.assert_called_once()
    
    def test_reject_to_specific_node(self, mock_engine, sample_task, sample_user):
        """测试驳回到指定节点"""
        from app.services.approval_engine.engine.approve import ApprovalProcessMixin
        
        target_node = MagicMock()
        target_node.id = 8
        
        mock_engine._get_and_validate_task.return_value = sample_task
        mock_engine.db.query.return_value.filter.return_value.first.side_effect = [sample_user, target_node]
        mock_engine.executor.process_approval.return_value = (False, None)
        
        result = ApprovalProcessMixin.reject(
            mock_engine,
            task_id=100,
            approver_id=200,
            comment="请重新审核",
            reject_to="8"
        )
        
        mock_engine._return_to_node.assert_called_once_with(sample_task.instance, target_node)
    
    def test_reject_without_comment_raises_error(self, mock_engine, sample_task):
        """测试没有驳回原因抛出异常"""
        from app.services.approval_engine.engine.approve import ApprovalProcessMixin
        
        mock_engine._get_and_validate_task.return_value = sample_task
        
        with pytest.raises(ValueError, match="驳回原因不能为空"):
            ApprovalProcessMixin.reject(
                mock_engine,
                task_id=100,
                approver_id=200,
                comment=""
            )


class TestReturnTo:
    """测试退回到指定节点"""
    
    def test_return_to_success(self, mock_engine, sample_task, sample_user):
        """测试成功退回"""
        from app.services.approval_engine.engine.approve import ApprovalProcessMixin
        
        target_node = MagicMock()
        target_node.id = 5
        
        mock_engine._get_and_validate_task.return_value = sample_task
        mock_engine.db.query.return_value.filter.side_effect = [
            MagicMock(first=lambda: sample_user),
            MagicMock(first=lambda: target_node)
        ]
        
        result = ApprovalProcessMixin.return_to(
            mock_engine,
            task_id=100,
            approver_id=200,
            target_node_id=5,
            comment="退回修改"
        )
        
        assert result == sample_task
        assert sample_task.action == "RETURN"
        assert sample_task.comment == "退回修改"
        assert sample_task.status == "COMPLETED"
        assert sample_task.return_to_node_id == 5
        mock_engine._return_to_node.assert_called_once_with(sample_task.instance, target_node)
        mock_engine.db.commit.assert_called_once()


class TestTransfer:
    """测试转审"""
    
    def test_transfer_success(self, mock_engine, sample_task, sample_user):
        """测试成功转审"""
        from app.services.approval_engine.engine.approve import ApprovalProcessMixin
        
        to_user = MagicMock()
        to_user.id = 300
        to_user.real_name = "李四"
        to_user.username = "lisi"
        
        mock_engine._get_and_validate_task.return_value = sample_task
        mock_engine.db.query.return_value.filter.return_value.first.side_effect = [sample_user, to_user]
        
        result = ApprovalProcessMixin.transfer(
            mock_engine,
            task_id=100,
            from_user_id=200,
            to_user_id=300,
            comment="转给你处理"
        )
        
        assert result is not None
        assert result.assignee_id == 300
        assert result.assignee_type == "TRANSFERRED"
        assert result.original_assignee_id == 200
        assert sample_task.status == "TRANSFERRED"
        mock_engine.notify.notify_transferred.assert_called_once()
        mock_engine.db.commit.assert_called_once()
    
    def test_transfer_node_not_allow(self, mock_engine, sample_task, sample_user):
        """测试节点不允许转审"""
        from app.services.approval_engine.engine.approve import ApprovalProcessMixin
        
        sample_task.node.can_transfer = False
        mock_engine._get_and_validate_task.return_value = sample_task
        mock_engine.db.query.return_value.filter.return_value.first.return_value = sample_user
        
        with pytest.raises(ValueError, match="当前节点不允许转审"):
            ApprovalProcessMixin.transfer(
                mock_engine,
                task_id=100,
                from_user_id=200,
                to_user_id=300
            )
    
    def test_transfer_to_user_not_found(self, mock_engine, sample_task, sample_user):
        """测试转审目标用户不存在"""
        from app.services.approval_engine.engine.approve import ApprovalProcessMixin
        
        mock_engine._get_and_validate_task.return_value = sample_task
        mock_engine.db.query.return_value.filter.return_value.first.side_effect = [sample_user, None]
        
        with pytest.raises(ValueError, match="转审目标用户不存在"):
            ApprovalProcessMixin.transfer(
                mock_engine,
                task_id=100,
                from_user_id=200,
                to_user_id=999
            )


class TestAddApprover:
    """测试加签"""
    
    def test_add_approver_after(self, mock_engine, sample_task, sample_user):
        """测试后加签"""
        from app.services.approval_engine.engine.approve import ApprovalProcessMixin
        
        approver1 = MagicMock()
        approver1.id = 300
        approver1.real_name = "李四"
        approver1.username = "lisi"
        
        approver2 = MagicMock()
        approver2.id = 400
        approver2.real_name = "王五"
        approver2.username = "wangwu"
        
        mock_engine._get_and_validate_task.return_value = sample_task
        
        def query_side_effect(model):
            mock_query = MagicMock()
            if model.__name__ == 'User':
                def filter_first_side_effect():
                    # 第一次查询operator,后续查询approvers
                    filter_first_side_effect.counter = getattr(filter_first_side_effect, 'counter', 0) + 1
                    if filter_first_side_effect.counter == 1:
                        return sample_user
                    elif filter_first_side_effect.counter == 2:
                        return approver1
                    else:
                        return approver2
                mock_query.filter.return_value.first.side_effect = filter_first_side_effect
            return mock_query
        
        mock_engine.db.query.side_effect = query_side_effect
        
        results = ApprovalProcessMixin.add_approver(
            mock_engine,
            task_id=100,
            operator_id=200,
            approver_ids=[300, 400],
            position="AFTER",
            comment="请协助审批"
        )
        
        assert len(results) == 2
        for task in results:
            assert task.assignee_type == "ADDED_AFTER"
            assert task.status == "SKIPPED"  # 后加签初始为SKIPPED
        mock_engine.db.commit.assert_called_once()
    
    def test_add_approver_before(self, mock_engine, sample_task, sample_user):
        """测试前加签"""
        from app.services.approval_engine.engine.approve import ApprovalProcessMixin
        
        approver = MagicMock()
        approver.id = 300
        approver.real_name = "李四"
        approver.username = "lisi"
        
        mock_engine._get_and_validate_task.return_value = sample_task
        mock_engine.db.query.return_value.filter.return_value.first.side_effect = [sample_user, approver]
        
        results = ApprovalProcessMixin.add_approver(
            mock_engine,
            task_id=100,
            operator_id=200,
            approver_ids=[300],
            position="BEFORE",
            comment="请先审批"
        )
        
        assert len(results) == 1
        assert results[0].assignee_type == "ADDED_BEFORE"
        assert results[0].status == "PENDING"  # 前加签立即生效
        assert sample_task.status == "SKIPPED"  # 当前任务变为等待
        mock_engine.notify.notify_add_approver.assert_called_once()
    
    def test_add_approver_node_not_allow(self, mock_engine, sample_task, sample_user):
        """测试节点不允许加签"""
        from app.services.approval_engine.engine.approve import ApprovalProcessMixin
        
        sample_task.node.can_add_approver = False
        mock_engine._get_and_validate_task.return_value = sample_task
        mock_engine.db.query.return_value.filter.return_value.first.return_value = sample_user
        
        with pytest.raises(ValueError, match="当前节点不允许加签"):
            ApprovalProcessMixin.add_approver(
                mock_engine,
                task_id=100,
                operator_id=200,
                approver_ids=[300]
            )
    
    def test_add_approver_skip_nonexistent_users(self, mock_engine, sample_task, sample_user):
        """测试跳过不存在的用户"""
        from app.services.approval_engine.engine.approve import ApprovalProcessMixin
        
        mock_engine._get_and_validate_task.return_value = sample_task
        mock_engine.db.query.return_value.filter.return_value.first.side_effect = [
            sample_user,  # operator
            None,  # approver不存在
        ]
        
        results = ApprovalProcessMixin.add_approver(
            mock_engine,
            task_id=100,
            operator_id=200,
            approver_ids=[999],
            position="AFTER"
        )
        
        assert len(results) == 0  # 跳过不存在的用户
