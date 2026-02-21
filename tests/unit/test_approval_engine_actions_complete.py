# -*- coding: utf-8 -*-
"""
审批引擎操作混入类完整单元测试

测试 ApprovalActionsMixin 的所有方法:
- add_cc (加抄送)
- withdraw (撤回审批)
- terminate (终止审批)
- remind (催办)
- add_comment (添加评论)

覆盖率目标: 60%+
测试用例数: 20-30个
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, call

from app.models.approval import (
    ApprovalCarbonCopy,
    ApprovalComment,
    ApprovalInstance,
    ApprovalTask,
)
from app.models.user import User
from app.services.approval_engine.engine.actions import ApprovalActionsMixin


class MockApprovalEngine(ApprovalActionsMixin):
    """用于测试的 Mock 引擎类"""
    
    def __init__(self, db):
        self.db = db
        self.executor = MagicMock()
        self.notify = MagicMock()
        
    def _log_action(self, **kwargs):
        """Mock 日志记录"""
        pass
    
    def _get_affected_user_ids(self, instance):
        """Mock 获取受影响用户"""
        return [1, 2, 3]
    
    def _call_adapter_callback(self, instance, callback_name):
        """Mock 适配器回调"""
        pass


@pytest.fixture
def mock_db():
    """创建 mock 数据库会话"""
    return MagicMock()


@pytest.fixture
def engine(mock_db):
    """创建测试引擎实例"""
    return MockApprovalEngine(mock_db)


@pytest.fixture
def mock_instance():
    """创建 mock 审批实例"""
    instance = MagicMock(spec=ApprovalInstance)
    instance.id = 100
    instance.current_node_id = 10
    instance.initiator_id = 999
    instance.status = "PENDING"
    instance.completed_at = None
    return instance


@pytest.fixture
def mock_user():
    """创建 mock 用户"""
    user = MagicMock(spec=User)
    user.id = 999
    user.username = "testuser"
    user.real_name = "测试用户"
    return user


@pytest.fixture
def mock_task():
    """创建 mock 任务"""
    task = MagicMock(spec=ApprovalTask)
    task.id = 50
    task.instance_id = 100
    task.status = "PENDING"
    task.remind_count = 0
    task.reminded_at = None
    return task


# ============================================================================
# add_cc 测试
# ============================================================================

@pytest.mark.unit
class TestAddCC:
    """测试加抄送功能"""
    
    def test_add_cc_success(self, engine, mock_db, mock_instance, mock_user):
        """测试成功添加抄送"""
        # 准备数据
        cc_user_ids = [1, 2, 3]
        mock_cc_records = [MagicMock(spec=ApprovalCarbonCopy) for _ in range(3)]
        
        # 设置 mock 行为
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,  # 查询实例
            mock_user,      # 查询操作人
        ]
        engine.executor.create_cc_records.return_value = mock_cc_records
        
        # 执行
        result = engine.add_cc(
            instance_id=100,
            operator_id=999,
            cc_user_ids=cc_user_ids,
        )
        
        # 验证
        assert len(result) == 3
        engine.executor.create_cc_records.assert_called_once_with(
            instance=mock_instance,
            node_id=mock_instance.current_node_id,
            cc_user_ids=cc_user_ids,
            cc_source="APPROVER",
            added_by=999,
        )
        assert engine.notify.notify_cc.call_count == 3
        mock_db.commit.assert_called_once()
    
    def test_add_cc_instance_not_found(self, engine, mock_db):
        """测试实例不存在时抛出异常"""
        # 设置 mock 行为 - 实例不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行并验证异常
        with pytest.raises(ValueError, match="审批实例不存在"):
            engine.add_cc(instance_id=999, operator_id=1, cc_user_ids=[2])
    
    def test_add_cc_empty_list(self, engine, mock_db, mock_instance, mock_user):
        """测试空抄送列表"""
        # 设置 mock 行为
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,
            mock_user,
        ]
        engine.executor.create_cc_records.return_value = []
        
        # 执行
        result = engine.add_cc(
            instance_id=100,
            operator_id=999,
            cc_user_ids=[],
        )
        
        # 验证
        assert len(result) == 0
        engine.notify.notify_cc.assert_not_called()
    
    def test_add_cc_multiple_times(self, engine, mock_db, mock_instance, mock_user):
        """测试多次添加抄送"""
        # 第一次添加
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,
            mock_user,
        ]
        engine.executor.create_cc_records.return_value = [MagicMock()]
        
        result1 = engine.add_cc(100, 999, [1])
        
        # 第二次添加
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,
            mock_user,
        ]
        engine.executor.create_cc_records.return_value = [MagicMock()]
        
        result2 = engine.add_cc(100, 999, [2])
        
        # 验证都成功
        assert len(result1) == 1
        assert len(result2) == 1


# ============================================================================
# withdraw 测试
# ============================================================================

@pytest.mark.unit
class TestWithdraw:
    """测试撤回审批功能"""
    
    def test_withdraw_success(self, engine, mock_db, mock_instance, mock_user):
        """测试成功撤回审批"""
        # 设置 mock 行为
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,  # 查询实例
            mock_user,      # 查询发起人
        ]
        mock_update = MagicMock()
        mock_db.query.return_value.filter.return_value.update = mock_update
        
        # 执行
        result = engine.withdraw(
            instance_id=100,
            initiator_id=999,
            comment="不想审批了",
        )
        
        # 验证
        assert result == mock_instance
        assert result.status == "CANCELLED"
        assert result.completed_at is not None
        mock_update.assert_called_once()
        engine.notify.notify_withdrawn.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_withdraw_instance_not_found(self, engine, mock_db):
        """测试实例不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="审批实例不存在"):
            engine.withdraw(instance_id=999, initiator_id=1)
    
    def test_withdraw_not_initiator(self, engine, mock_db, mock_instance):
        """测试非发起人撤回"""
        mock_instance.initiator_id = 100  # 发起人是100
        mock_db.query.return_value.filter.return_value.first.return_value = mock_instance
        
        with pytest.raises(ValueError, match="只有发起人可以撤回审批"):
            engine.withdraw(instance_id=100, initiator_id=999)  # 999不是发起人
    
    def test_withdraw_invalid_status(self, engine, mock_db, mock_instance):
        """测试无效状态下撤回"""
        mock_instance.status = "APPROVED"  # 已批准的不能撤回
        mock_db.query.return_value.filter.return_value.first.return_value = mock_instance
        
        with pytest.raises(ValueError, match="当前状态不允许撤回"):
            engine.withdraw(instance_id=100, initiator_id=999)
    
    def test_withdraw_from_draft_status(self, engine, mock_db, mock_instance, mock_user):
        """测试从草稿状态撤回"""
        mock_instance.status = "DRAFT"
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,
            mock_user,
        ]
        mock_update = MagicMock()
        mock_db.query.return_value.filter.return_value.update = mock_update
        
        result = engine.withdraw(100, 999)
        
        assert result.status == "CANCELLED"
    
    def test_withdraw_cancels_pending_tasks(self, engine, mock_db, mock_instance, mock_user):
        """测试撤回时取消待处理任务"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,
            mock_user,
        ]
        mock_update = MagicMock()
        mock_db.query.return_value.filter.return_value.update = mock_update
        
        engine.withdraw(100, 999)
        
        # 验证调用了更新任务状态
        assert mock_update.call_count >= 1


# ============================================================================
# terminate 测试
# ============================================================================

@pytest.mark.unit
class TestTerminate:
    """测试终止审批功能"""
    
    def test_terminate_success(self, engine, mock_db, mock_instance, mock_user):
        """测试成功终止审批"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,
            mock_user,
        ]
        mock_update = MagicMock()
        mock_db.query.return_value.filter.return_value.update = mock_update
        
        result = engine.terminate(
            instance_id=100,
            operator_id=999,
            comment="紧急终止",
        )
        
        assert result == mock_instance
        assert result.status == "TERMINATED"
        assert result.completed_at is not None
        mock_db.commit.assert_called_once()
    
    def test_terminate_instance_not_found(self, engine, mock_db):
        """测试实例不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="审批实例不存在"):
            engine.terminate(999, 1, "原因")
    
    def test_terminate_invalid_status(self, engine, mock_db, mock_instance):
        """测试无效状态下终止"""
        mock_instance.status = "APPROVED"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_instance
        
        with pytest.raises(ValueError, match="当前状态不允许终止"):
            engine.terminate(100, 999, "原因")
    
    def test_terminate_cancels_tasks(self, engine, mock_db, mock_instance, mock_user):
        """测试终止时取消任务"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,
            mock_user,
        ]
        mock_update = MagicMock()
        mock_db.query.return_value.filter.return_value.update = mock_update
        
        engine.terminate(100, 999, "终止原因")
        
        assert mock_update.call_count >= 1
    
    def test_terminate_with_long_comment(self, engine, mock_db, mock_instance, mock_user):
        """测试带长评论终止"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,
            mock_user,
        ]
        mock_update = MagicMock()
        mock_db.query.return_value.filter.return_value.update = mock_update
        
        long_comment = "很长的终止原因" * 100
        result = engine.terminate(100, 999, long_comment)
        
        assert result.status == "TERMINATED"


# ============================================================================
# remind 测试
# ============================================================================

@pytest.mark.unit
class TestRemind:
    """测试催办功能"""
    
    def test_remind_success(self, engine, mock_db, mock_task, mock_user):
        """测试成功催办"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_task,
            mock_user,
        ]
        
        result = engine.remind(task_id=50, reminder_id=999)
        
        assert result is True
        assert mock_task.remind_count == 1
        assert mock_task.reminded_at is not None
        engine.notify.notify_remind.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_remind_task_not_found(self, engine, mock_db):
        """测试任务不存在"""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(ValueError, match="任务不存在"):
            engine.remind(999, 1)
    
    def test_remind_invalid_task_status(self, engine, mock_db, mock_task):
        """测试无效任务状态"""
        mock_task.status = "APPROVED"
        mock_db.query.return_value.filter.return_value.first.return_value = mock_task
        
        with pytest.raises(ValueError, match="只能催办待处理的任务"):
            engine.remind(50, 999)
    
    def test_remind_multiple_times(self, engine, mock_db, mock_task, mock_user):
        """测试多次催办"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_task,
            mock_user,
        ]
        
        # 第一次催办
        engine.remind(50, 999)
        assert mock_task.remind_count == 1
        
        # 第二次催办
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_task,
            mock_user,
        ]
        engine.remind(50, 999)
        assert mock_task.remind_count == 2
    
    def test_remind_updates_timestamp(self, engine, mock_db, mock_task, mock_user):
        """测试催办更新时间戳"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_task,
            mock_user,
        ]
        
        before = datetime.now()
        engine.remind(50, 999)
        after = datetime.now()
        
        assert mock_task.reminded_at is not None
        assert before <= mock_task.reminded_at <= after


# ============================================================================
# add_comment 测试
# ============================================================================

@pytest.mark.unit
class TestAddComment:
    """测试添加评论功能"""
    
    def test_add_comment_simple(self, engine, mock_db, mock_user):
        """测试添加简单评论"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = engine.add_comment(
            instance_id=100,
            user_id=999,
            content="这是一条评论",
        )
        
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    def test_add_comment_with_reply(self, engine, mock_db, mock_user):
        """测试回复评论"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        result = engine.add_comment(
            instance_id=100,
            user_id=999,
            content="回复内容",
            parent_id=10,
            reply_to_user_id=888,
        )
        
        mock_db.add.assert_called_once()
    
    def test_add_comment_with_mentions(self, engine, mock_db, mock_user, mock_instance):
        """测试带@提及的评论"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,      # 查询评论人
            mock_instance,  # 查询实例
        ]
        
        mentioned_ids = [1, 2, 3]
        result = engine.add_comment(
            instance_id=100,
            user_id=999,
            content="@用户1 @用户2 @用户3",
            mentioned_user_ids=mentioned_ids,
        )
        
        engine.notify.notify_comment.assert_called_once()
    
    def test_add_comment_with_attachments(self, engine, mock_db, mock_user):
        """测试带附件的评论"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        attachments = [
            {"name": "file1.pdf", "url": "/uploads/file1.pdf"},
            {"name": "file2.png", "url": "/uploads/file2.png"},
        ]
        
        result = engine.add_comment(
            instance_id=100,
            user_id=999,
            content="请查看附件",
            attachments=attachments,
        )
        
        mock_db.add.assert_called_once()
    
    def test_add_comment_long_content(self, engine, mock_db, mock_user):
        """测试长文本评论"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        long_content = "很长的评论内容" * 200
        
        result = engine.add_comment(
            instance_id=100,
            user_id=999,
            content=long_content,
        )
        
        mock_db.add.assert_called_once()
    
    def test_add_comment_empty_content(self, engine, mock_db, mock_user):
        """测试空内容评论"""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        # 系统应该允许空评论（可能只有附件）
        result = engine.add_comment(
            instance_id=100,
            user_id=999,
            content="",
        )
        
        mock_db.add.assert_called_once()
    
    def test_add_comment_no_mentions_no_notification(self, engine, mock_db, mock_user, mock_instance):
        """测试无提及时不发送通知"""
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            mock_instance,
        ]
        
        result = engine.add_comment(
            instance_id=100,
            user_id=999,
            content="普通评论",
            mentioned_user_ids=None,
        )
        
        # 验证没有调用通知
        engine.notify.notify_comment.assert_not_called()


# ============================================================================
# 综合测试
# ============================================================================

@pytest.mark.unit
class TestIntegration:
    """集成场景测试"""
    
    def test_workflow_add_cc_then_withdraw(self, engine, mock_db, mock_instance, mock_user):
        """测试工作流：添加抄送后撤回"""
        # 1. 添加抄送
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,
            mock_user,
        ]
        engine.executor.create_cc_records.return_value = [MagicMock()]
        
        cc_result = engine.add_cc(100, 999, [1, 2])
        assert len(cc_result) > 0
        
        # 2. 撤回
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,
            mock_user,
        ]
        mock_update = MagicMock()
        mock_db.query.return_value.filter.return_value.update = mock_update
        
        withdraw_result = engine.withdraw(100, 999)
        assert withdraw_result.status == "CANCELLED"
    
    def test_workflow_comment_and_remind(self, engine, mock_db, mock_user, mock_task):
        """测试工作流：评论并催办"""
        # 1. 添加评论
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        comment = engine.add_comment(100, 999, "请尽快审批")
        
        # 2. 催办
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_task,
            mock_user,
        ]
        
        remind_result = engine.remind(50, 999)
        assert remind_result is True
