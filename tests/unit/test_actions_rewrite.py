# -*- coding: utf-8 -*-
"""
审批操作功能单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库、通知）
2. 测试核心审批操作逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime
from app.services.approval_engine.engine.actions import ApprovalActionsMixin
from app.models.approval import (
    ApprovalCarbonCopy,
    ApprovalComment,
    ApprovalInstance,
    ApprovalTask,
)
from app.models.user import User


class MockEngine(ApprovalActionsMixin):
    """测试用的Mock引擎类"""
    def __init__(self):
        self.db = MagicMock()
        self.executor = MagicMock()
        self.notify = MagicMock()
    
    def _log_action(self, **kwargs):
        """Mock日志记录"""
        pass
    
    def _get_affected_user_ids(self, instance):
        """Mock获取受影响用户"""
        return [2, 3]
    
    def _call_adapter_callback(self, instance, callback_name):
        """Mock适配器回调"""
        pass


class TestAddCC(unittest.TestCase):
    """测试加抄送功能"""

    def setUp(self):
        self.engine = MockEngine()

    def test_add_cc_success(self):
        """测试成功加抄送"""
        # 准备mock数据
        instance = ApprovalInstance(
            id=1,
            current_node_id=10,
            status="PENDING"
        )
        operator = User(id=1, username="admin", real_name="管理员",
        password_hash="test_hash_123"
    )
        cc_records = [
            ApprovalCarbonCopy(id=1, instance_id=1, cc_user_id=2),
            ApprovalCarbonCopy(id=2, instance_id=1, cc_user_id=3),
        ]

        # Mock数据库查询
        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            instance,  # 第一次查询instance
            operator,  # 第二次查询operator
        ]

        # Mock executor创建抄送记录
        self.engine.executor.create_cc_records.return_value = cc_records

        # 执行
        result = self.engine.add_cc(
            instance_id=1,
            operator_id=1,
            cc_user_ids=[2, 3]
        )

        # 验证
        self.assertEqual(len(result), 2)
        self.engine.executor.create_cc_records.assert_called_once_with(
            instance=instance,
            node_id=10,
            cc_user_ids=[2, 3],
            cc_source="APPROVER",
            added_by=1,
        )
        self.assertEqual(self.engine.notify.notify_cc.call_count, 2)
        self.engine.db.commit.assert_called_once()

    def test_add_cc_instance_not_found(self):
        """测试审批实例不存在"""
        self.engine.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.engine.add_cc(instance_id=999, operator_id=1, cc_user_ids=[2])
        
        self.assertIn("审批实例不存在", str(context.exception))

    def test_add_cc_operator_not_found(self):
        """测试操作人不存在（应仍能成功）"""
        instance = ApprovalInstance(id=1, current_node_id=10)
        
        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            instance,  # instance存在
            None,      # operator不存在
        ]
        
        cc_records = [ApprovalCarbonCopy(id=1, instance_id=1, cc_user_id=2)]
        self.engine.executor.create_cc_records.return_value = cc_records

        # 即使operator为None，也应能执行（只是记录的operator_name为None）
        result = self.engine.add_cc(instance_id=1, operator_id=999, cc_user_ids=[2])
        
        self.assertEqual(len(result), 1)


class TestWithdraw(unittest.TestCase):
    """测试撤回审批功能"""

    def setUp(self):
        self.engine = MockEngine()

    def test_withdraw_success(self):
        """测试成功撤回"""
        instance = ApprovalInstance(
            id=1,
            initiator_id=10,
            status="PENDING",
            completed_at=None
        )
        initiator = User(id=10, username="user1", real_name="用户1",
        password_hash="test_hash_123"
    )

        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            instance,
            initiator,
        ]

        # Mock task查询和更新
        task_query_mock = MagicMock()
        self.engine.db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=instance)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=initiator)))),
            task_query_mock,  # ApprovalTask查询
        ]

        result = self.engine.withdraw(
            instance_id=1,
            initiator_id=10,
            comment="撤回测试"
        )

        # 验证实例状态更新
        self.assertEqual(result.status, "CANCELLED")
        self.assertIsNotNone(result.completed_at)
        
        # 验证任务被取消
        task_query_mock.filter.assert_called()
        
        # 验证通知
        self.engine.notify.notify_withdrawn.assert_called_once()
        self.engine.db.commit.assert_called_once()

    def test_withdraw_not_initiator(self):
        """测试非发起人撤回"""
        instance = ApprovalInstance(id=1, initiator_id=10, status="PENDING")
        
        self.engine.db.query.return_value.filter.return_value.first.return_value = instance

        with self.assertRaises(ValueError) as context:
            self.engine.withdraw(instance_id=1, initiator_id=99, comment="撤回")
        
        self.assertIn("只有发起人可以撤回", str(context.exception))

    def test_withdraw_invalid_status(self):
        """测试无效状态撤回"""
        instance = ApprovalInstance(
            id=1,
            initiator_id=10,
            status="APPROVED"  # 已通过不能撤回
        )
        
        self.engine.db.query.return_value.filter.return_value.first.return_value = instance

        with self.assertRaises(ValueError) as context:
            self.engine.withdraw(instance_id=1, initiator_id=10)
        
        self.assertIn("当前状态不允许撤回", str(context.exception))

    def test_withdraw_from_draft(self):
        """测试从草稿状态撤回"""
        instance = ApprovalInstance(
            id=1,
            initiator_id=10,
            status="DRAFT",
            completed_at=None
        )
        initiator = User(id=10, username="user1", real_name="用户1",
        password_hash="test_hash_123"
    )

        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            instance,
            initiator,
        ]

        task_query_mock = MagicMock()
        self.engine.db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=instance)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=initiator)))),
            task_query_mock,
        ]

        result = self.engine.withdraw(instance_id=1, initiator_id=10)
        
        # DRAFT状态也允许撤回
        self.assertEqual(result.status, "CANCELLED")

    def test_withdraw_instance_not_found(self):
        """测试审批实例不存在"""
        self.engine.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.engine.withdraw(instance_id=999, initiator_id=10)
        
        self.assertIn("审批实例不存在", str(context.exception))


class TestTerminate(unittest.TestCase):
    """测试终止审批功能"""

    def setUp(self):
        self.engine = MockEngine()

    def test_terminate_success(self):
        """测试成功终止"""
        instance = ApprovalInstance(
            id=1,
            status="PENDING",
            completed_at=None
        )
        operator = User(id=1, username="admin", real_name="管理员",
        password_hash="test_hash_123"
    )

        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            instance,
            operator,
        ]

        task_query_mock = MagicMock()
        self.engine.db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=instance)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=operator)))),
            task_query_mock,
        ]

        result = self.engine.terminate(
            instance_id=1,
            operator_id=1,
            comment="违规终止"
        )

        # 验证实例状态
        self.assertEqual(result.status, "TERMINATED")
        self.assertIsNotNone(result.completed_at)
        
        # 验证任务被取消
        task_query_mock.filter.assert_called()
        
        self.engine.db.commit.assert_called_once()

    def test_terminate_invalid_status(self):
        """测试无效状态终止"""
        instance = ApprovalInstance(id=1, status="APPROVED")
        
        self.engine.db.query.return_value.filter.return_value.first.return_value = instance

        with self.assertRaises(ValueError) as context:
            self.engine.terminate(instance_id=1, operator_id=1, comment="终止")
        
        self.assertIn("当前状态不允许终止", str(context.exception))

    def test_terminate_instance_not_found(self):
        """测试审批实例不存在"""
        self.engine.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.engine.terminate(instance_id=999, operator_id=1, comment="终止")
        
        self.assertIn("审批实例不存在", str(context.exception))

    def test_terminate_operator_not_found(self):
        """测试操作人不存在（应仍能成功）"""
        instance = ApprovalInstance(id=1, status="PENDING", completed_at=None)
        
        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            instance,
            None,  # operator不存在
        ]

        task_query_mock = MagicMock()
        self.engine.db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=instance)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=None)))),
            task_query_mock,
        ]

        result = self.engine.terminate(instance_id=1, operator_id=999, comment="终止")
        
        self.assertEqual(result.status, "TERMINATED")


class TestRemind(unittest.TestCase):
    """测试催办功能"""

    def setUp(self):
        self.engine = MockEngine()

    def test_remind_success(self):
        """测试成功催办"""
        task = ApprovalTask(
            id=1,
            instance_id=10,
            status="PENDING",
            remind_count=0,
            reminded_at=None
        )
        reminder = User(id=5, username="user5", real_name="催办人",
        password_hash="test_hash_123"
    )

        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            task,
            reminder,
        ]

        result = self.engine.remind(task_id=1, reminder_id=5)

        # 验证
        self.assertTrue(result)
        self.assertEqual(task.remind_count, 1)
        self.assertIsNotNone(task.reminded_at)
        
        self.engine.notify.notify_remind.assert_called_once()
        self.engine.db.commit.assert_called_once()

    def test_remind_increase_count(self):
        """测试多次催办计数增加"""
        task = ApprovalTask(
            id=1,
            instance_id=10,
            status="PENDING",
            remind_count=2,  # 已催办2次
            reminded_at=datetime(2024, 1, 1)
        )
        reminder = User(id=5, username="user5", real_name="催办人",
        password_hash="test_hash_123"
    )

        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            task,
            reminder,
        ]

        result = self.engine.remind(task_id=1, reminder_id=5)

        self.assertTrue(result)
        self.assertEqual(task.remind_count, 3)  # 应增加到3

    def test_remind_task_not_found(self):
        """测试任务不存在"""
        self.engine.db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as context:
            self.engine.remind(task_id=999, reminder_id=5)
        
        self.assertIn("任务不存在", str(context.exception))

    def test_remind_invalid_status(self):
        """测试无效状态催办"""
        task = ApprovalTask(id=1, status="APPROVED")
        
        self.engine.db.query.return_value.filter.return_value.first.return_value = task

        with self.assertRaises(ValueError) as context:
            self.engine.remind(task_id=1, reminder_id=5)
        
        self.assertIn("只能催办待处理的任务", str(context.exception))

    def test_remind_reminder_not_found(self):
        """测试催办人不存在（应仍能成功）"""
        task = ApprovalTask(
            id=1,
            instance_id=10,
            status="PENDING",
            remind_count=0
        )
        
        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            task,
            None,  # reminder不存在
        ]

        result = self.engine.remind(task_id=1, reminder_id=999)
        
        self.assertTrue(result)
        self.assertEqual(task.remind_count, 1)


class TestAddComment(unittest.TestCase):
    """测试添加评论功能"""

    def setUp(self):
        self.engine = MockEngine()

    def test_add_comment_simple(self):
        """测试简单评论"""
        user = User(id=1, username="user1", real_name="用户1",
        password_hash="test_hash_123"
    )
        instance = ApprovalInstance(id=10, status="PENDING")

        # Mock查询
        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            user,
            instance,
        ]

        # Mock db.add和flush
        comment_captured = None
        def capture_comment(obj):
            nonlocal comment_captured
            comment_captured = obj
        
        self.engine.db.add.side_effect = capture_comment
        self.engine.db.flush.return_value = None

        result = self.engine.add_comment(
            instance_id=10,
            user_id=1,
            content="这是一条评论"
        )

        # 验证评论对象创建
        self.engine.db.add.assert_called_once()
        self.engine.db.flush.assert_called_once()
        self.engine.db.commit.assert_called_once()
        
        # 验证评论内容
        self.assertIsNotNone(comment_captured)
        self.assertEqual(comment_captured.instance_id, 10)
        self.assertEqual(comment_captured.user_id, 1)
        self.assertEqual(comment_captured.content, "这是一条评论")

    def test_add_comment_with_reply(self):
        """测试回复评论"""
        user = User(id=2, username="user2", real_name="用户2",
        password_hash="test_hash_123"
    )
        instance = ApprovalInstance(id=10, status="PENDING")

        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            user,
            instance,
        ]

        comment_captured = None
        def capture_comment(obj):
            nonlocal comment_captured
            comment_captured = obj
        
        self.engine.db.add.side_effect = capture_comment

        result = self.engine.add_comment(
            instance_id=10,
            user_id=2,
            content="回复内容",
            parent_id=5,
            reply_to_user_id=1
        )

        self.assertIsNotNone(comment_captured)
        self.assertEqual(comment_captured.parent_id, 5)
        self.assertEqual(comment_captured.reply_to_user_id, 1)

    def test_add_comment_with_mentions(self):
        """测试@提及评论"""
        user = User(id=1, username="user1", real_name="用户1",
        password_hash="test_hash_123"
    )
        instance = ApprovalInstance(id=10, status="PENDING")

        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            user,
            instance,
        ]

        comment_captured = None
        def capture_comment(obj):
            nonlocal comment_captured
            comment_captured = obj
        
        self.engine.db.add.side_effect = capture_comment

        result = self.engine.add_comment(
            instance_id=10,
            user_id=1,
            content="@用户2 @用户3 请查看",
            mentioned_user_ids=[2, 3]
        )

        # 验证提及
        self.assertIsNotNone(comment_captured)
        self.assertEqual(comment_captured.mentioned_user_ids, [2, 3])
        
        # 验证通知
        self.engine.notify.notify_comment.assert_called_once_with(
            instance,
            commenter_name="用户1",
            comment_content="@用户2 @用户3 请查看",
            mentioned_user_ids=[2, 3]
        )

    def test_add_comment_with_attachments(self):
        """测试带附件评论"""
        user = User(id=1, username="user1", real_name="用户1",
        password_hash="test_hash_123"
    )
        instance = ApprovalInstance(id=10, status="PENDING")

        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            user,
            instance,
        ]

        comment_captured = None
        def capture_comment(obj):
            nonlocal comment_captured
            comment_captured = obj
        
        self.engine.db.add.side_effect = capture_comment

        attachments = [
            {"name": "file1.pdf", "url": "http://example.com/file1.pdf"},
            {"name": "file2.png", "url": "http://example.com/file2.png"},
        ]

        result = self.engine.add_comment(
            instance_id=10,
            user_id=1,
            content="带附件的评论",
            attachments=attachments
        )

        self.assertIsNotNone(comment_captured)
        self.assertEqual(comment_captured.attachments, attachments)

    def test_add_comment_user_not_found(self):
        """测试用户不存在（应仍能成功，user_name为None）"""
        instance = ApprovalInstance(id=10, status="PENDING")
        
        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            None,  # user不存在
            instance,
        ]

        comment_captured = None
        def capture_comment(obj):
            nonlocal comment_captured
            comment_captured = obj
        
        self.engine.db.add.side_effect = capture_comment

        result = self.engine.add_comment(
            instance_id=10,
            user_id=999,
            content="匿名评论"
        )

        self.assertIsNotNone(comment_captured)
        self.assertIsNone(comment_captured.user_name)

    def test_add_comment_no_mentions(self):
        """测试无@提及时不发通知"""
        user = User(id=1, username="user1", real_name="用户1",
        password_hash="test_hash_123"
    )
        instance = ApprovalInstance(id=10, status="PENDING")

        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            user,
            instance,
        ]

        self.engine.db.add.return_value = None

        result = self.engine.add_comment(
            instance_id=10,
            user_id=1,
            content="普通评论"
        )

        # 没有提及时不应发送通知
        self.engine.notify.notify_comment.assert_not_called()

    def test_add_comment_instance_not_found_no_notify(self):
        """测试实例不存在时不发通知"""
        user = User(id=1, username="user1", real_name="用户1",
        password_hash="test_hash_123"
    )
        
        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            user,
            None,  # instance不存在
        ]

        self.engine.db.add.return_value = None

        result = self.engine.add_comment(
            instance_id=999,
            user_id=1,
            content="评论",
            mentioned_user_ids=[2, 3]
        )

        # instance不存在时不发通知
        self.engine.notify.notify_comment.assert_not_called()


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""

    def setUp(self):
        self.engine = MockEngine()

    def test_add_cc_empty_list(self):
        """测试空抄送列表"""
        instance = ApprovalInstance(id=1, current_node_id=10)
        operator = User(id=1, username="admin",
        password_hash="test_hash_123"
    )

        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            instance,
            operator,
        ]

        self.engine.executor.create_cc_records.return_value = []

        result = self.engine.add_cc(instance_id=1, operator_id=1, cc_user_ids=[])

        self.assertEqual(len(result), 0)
        # 即使列表为空也应正常执行
        self.engine.db.commit.assert_called_once()

    def test_withdraw_without_comment(self):
        """测试无说明撤回"""
        instance = ApprovalInstance(id=1, initiator_id=10, status="PENDING", completed_at=None)
        initiator = User(id=10, username="user1",
        password_hash="test_hash_123"
    )

        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            instance,
            initiator,
        ]

        task_query_mock = MagicMock()
        self.engine.db.query.side_effect = [
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=instance)))),
            MagicMock(filter=MagicMock(return_value=MagicMock(first=MagicMock(return_value=initiator)))),
            task_query_mock,
        ]

        # 不传comment参数
        result = self.engine.withdraw(instance_id=1, initiator_id=10)

        self.assertEqual(result.status, "CANCELLED")

    def test_remind_count_none_to_one(self):
        """测试remind_count从None变为1"""
        task = ApprovalTask(
            id=1,
            instance_id=10,
            status="PENDING",
            remind_count=None,  # 初始为None
        )
        reminder = User(id=5, username="user5",
        password_hash="test_hash_123"
    )

        self.engine.db.query.return_value.filter.return_value.first.side_effect = [
            task,
            reminder,
        ]

        result = self.engine.remind(task_id=1, reminder_id=5)

        # None + 1 = 1
        self.assertEqual(task.remind_count, 1)


if __name__ == "__main__":
    unittest.main()
