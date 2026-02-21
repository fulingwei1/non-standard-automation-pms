# -*- coding: utf-8 -*-
"""
审批引擎 actions.py 单元测试

目标:
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 测试核心业务逻辑
3. 覆盖主要方法和边界情况
4. 目标覆盖率: 70%+
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch, call

from app.models.approval import (
    ApprovalCarbonCopy,
    ApprovalComment,
    ApprovalInstance,
    ApprovalTask,
)
from app.models.user import User
from app.services.approval_engine.engine import ApprovalEngineService


class TestApprovalActionsMixin(unittest.TestCase):
    """测试 ApprovalActionsMixin 的所有方法"""

    def setUp(self):
        """每个测试前的准备"""
        # Mock database session
        self.mock_db = MagicMock()
        
        # 创建引擎实例（包含所有 mixin）
        self.engine = ApprovalEngineService(db=self.mock_db)
        
        # Mock 外部依赖
        self.engine.executor = MagicMock()
        self.engine.notify = MagicMock()
        
        # Mock _log_action 方法
        self.engine._log_action = MagicMock()
        self.engine._call_adapter_callback = MagicMock()
        self.engine._get_affected_user_ids = MagicMock(return_value=[2, 3, 4])

    # ========== add_cc() 测试 ==========

    def test_add_cc_success(self):
        """测试成功添加抄送"""
        # 准备数据
        instance_id = 1
        operator_id = 10
        cc_user_ids = [20, 21, 22]
        
        # Mock 审批实例
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.id = instance_id
        mock_instance.current_node_id = 100
        
        # Mock 操作人
        mock_operator = MagicMock(spec=User)
        mock_operator.id = operator_id
        mock_operator.real_name = "操作人"
        mock_operator.username = "operator"
        
        # Mock 抄送记录
        mock_cc_records = [
            MagicMock(spec=ApprovalCarbonCopy, id=1, user_id=20),
            MagicMock(spec=ApprovalCarbonCopy, id=2, user_id=21),
            MagicMock(spec=ApprovalCarbonCopy, id=3, user_id=22),
        ]
        
        # 配置 query mock
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,  # 第一次查询: instance
            mock_operator,  # 第二次查询: operator
        ]
        
        # 配置 executor.create_cc_records
        self.engine.executor.create_cc_records.return_value = mock_cc_records
        
        # 执行测试
        result = self.engine.add_cc(instance_id, operator_id, cc_user_ids)
        
        # 验证结果
        self.assertEqual(result, mock_cc_records)
        self.assertEqual(len(result), 3)
        
        # 验证 executor.create_cc_records 被调用
        self.engine.executor.create_cc_records.assert_called_once_with(
            instance=mock_instance,
            node_id=100,
            cc_user_ids=cc_user_ids,
            cc_source="APPROVER",
            added_by=operator_id,
        )
        
        # 验证记录日志
        self.engine._log_action.assert_called_once_with(
            instance_id=instance_id,
            operator_id=operator_id,
            operator_name="操作人",
            action="ADD_CC",
            action_detail={"cc_user_ids": cc_user_ids},
        )
        
        # 验证通知
        self.assertEqual(self.engine.notify.notify_cc.call_count, 3)
        
        # 验证 commit
        self.mock_db.commit.assert_called_once()

    def test_add_cc_instance_not_found(self):
        """测试实例不存在"""
        # Mock 查询返回 None
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 执行并验证异常
        with self.assertRaises(ValueError) as context:
            self.engine.add_cc(999, 10, [20, 21])
        
        self.assertIn("审批实例不存在", str(context.exception))

    def test_add_cc_operator_is_none(self):
        """测试操作人不存在时仍能正常执行"""
        # Mock 实例存在，操作人不存在
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.id = 1
        mock_instance.current_node_id = 100
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,
            None,  # operator 不存在
        ]
        
        self.engine.executor.create_cc_records.return_value = [MagicMock()]
        
        # 应该正常执行，不抛出异常
        result = self.engine.add_cc(1, 10, [20])
        
        self.assertIsNotNone(result)
        # operator_name 应该是 None
        self.engine._log_action.assert_called_once()
        call_kwargs = self.engine._log_action.call_args[1]
        self.assertIsNone(call_kwargs['operator_name'])

    # ========== withdraw() 测试 ==========

    def test_withdraw_success(self):
        """测试成功撤回"""
        instance_id = 1
        initiator_id = 10
        comment = "我要撤回"
        
        # Mock 审批实例
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.id = instance_id
        mock_instance.initiator_id = initiator_id
        mock_instance.status = "PENDING"
        
        # Mock 发起人
        mock_initiator = MagicMock(spec=User)
        mock_initiator.id = initiator_id
        mock_initiator.real_name = "发起人"
        mock_initiator.username = "initiator"
        
        # 创建独立的 mock 对象
        mock_instance_query = MagicMock()
        mock_instance_query.filter.return_value.first.return_value = mock_instance
        
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = mock_initiator
        
        mock_task_update_query = MagicMock()
        mock_task_filter_chain = MagicMock()
        mock_task_filter_chain.update.return_value = None
        mock_task_update_query.filter.return_value.filter.return_value = mock_task_filter_chain
        
        # 配置 db.query 返回不同的 mock
        self.mock_db.query.side_effect = [
            mock_instance_query,  # query(ApprovalInstance)
            mock_user_query,       # query(User)
            mock_task_update_query,  # query(ApprovalTask) for update
        ]
        
        # 执行测试
        result = self.engine.withdraw(instance_id, initiator_id, comment)
        
        # 验证结果
        self.assertEqual(result, mock_instance)
        self.assertEqual(mock_instance.status, "CANCELLED")
        self.assertIsNotNone(mock_instance.completed_at)
        
        # 验证日志
        self.engine._log_action.assert_called_once()
        call_kwargs = self.engine._log_action.call_args[1]
        self.assertEqual(call_kwargs['action'], 'WITHDRAW')
        self.assertEqual(call_kwargs['comment'], comment)
        self.assertEqual(call_kwargs['before_status'], 'PENDING')
        self.assertEqual(call_kwargs['after_status'], 'CANCELLED')
        
        # 验证回调
        self.engine._call_adapter_callback.assert_called_once_with(mock_instance, "on_withdrawn")
        
        # 验证通知
        self.engine.notify.notify_withdrawn.assert_called_once()
        
        # 验证 commit
        self.mock_db.commit.assert_called_once()

    def test_withdraw_instance_not_found(self):
        """测试实例不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.engine.withdraw(999, 10, "comment")
        
        self.assertIn("审批实例不存在", str(context.exception))

    def test_withdraw_not_initiator(self):
        """测试非发起人撤回"""
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.initiator_id = 10
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_instance
        
        with self.assertRaises(ValueError) as context:
            self.engine.withdraw(1, 999, "comment")  # 999 不是发起人
        
        self.assertIn("只有发起人可以撤回", str(context.exception))

    def test_withdraw_invalid_status(self):
        """测试无效状态"""
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.initiator_id = 10
        mock_instance.status = "APPROVED"  # 已通过，不能撤回
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_instance
        
        with self.assertRaises(ValueError) as context:
            self.engine.withdraw(1, 10, "comment")
        
        self.assertIn("当前状态不允许撤回", str(context.exception))

    def test_withdraw_draft_status(self):
        """测试草稿状态也可以撤回"""
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.id = 1
        mock_instance.initiator_id = 10
        mock_instance.status = "DRAFT"
        
        mock_initiator = MagicMock(spec=User)
        mock_initiator.real_name = "发起人"
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,
            mock_initiator,
        ]
        
        # 应该成功
        result = self.engine.withdraw(1, 10)
        self.assertEqual(result.status, "CANCELLED")

    # ========== terminate() 测试 ==========

    def test_terminate_success(self):
        """测试成功终止"""
        instance_id = 1
        operator_id = 99
        comment = "系统管理员强制终止"
        
        # Mock 实例
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.id = instance_id
        mock_instance.status = "PENDING"
        
        # Mock 操作人
        mock_operator = MagicMock(spec=User)
        mock_operator.id = operator_id
        mock_operator.real_name = "管理员"
        mock_operator.username = "admin"
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,
            mock_operator,
        ]
        
        # 执行测试
        result = self.engine.terminate(instance_id, operator_id, comment)
        
        # 验证结果
        self.assertEqual(result, mock_instance)
        self.assertEqual(mock_instance.status, "TERMINATED")
        self.assertIsNotNone(mock_instance.completed_at)
        
        # 验证日志
        self.engine._log_action.assert_called_once()
        call_kwargs = self.engine._log_action.call_args[1]
        self.assertEqual(call_kwargs['action'], 'TERMINATE')
        self.assertEqual(call_kwargs['comment'], comment)
        self.assertEqual(call_kwargs['before_status'], 'PENDING')
        self.assertEqual(call_kwargs['after_status'], 'TERMINATED')
        
        # 验证回调
        self.engine._call_adapter_callback.assert_called_once_with(mock_instance, "on_terminated")
        
        # 验证 commit
        self.mock_db.commit.assert_called_once()

    def test_terminate_instance_not_found(self):
        """测试实例不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.engine.terminate(999, 99, "comment")
        
        self.assertIn("审批实例不存在", str(context.exception))

    def test_terminate_invalid_status(self):
        """测试非PENDING状态不能终止"""
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.status = "APPROVED"  # 已通过，不能终止
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_instance
        
        with self.assertRaises(ValueError) as context:
            self.engine.terminate(1, 99, "comment")
        
        self.assertIn("当前状态不允许终止", str(context.exception))

    def test_terminate_operator_is_none(self):
        """测试操作人不存在时仍能终止"""
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.id = 1
        mock_instance.status = "PENDING"
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,
            None,  # operator 不存在
        ]
        
        # 应该正常执行
        result = self.engine.terminate(1, 99, "comment")
        
        self.assertEqual(result.status, "TERMINATED")
        # operator_name 应该是 None
        call_kwargs = self.engine._log_action.call_args[1]
        self.assertIsNone(call_kwargs['operator_name'])

    # ========== remind() 测试 ==========

    def test_remind_success(self):
        """测试成功催办"""
        task_id = 1
        reminder_id = 20
        
        # Mock 任务
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.id = task_id
        mock_task.instance_id = 100
        mock_task.status = "PENDING"
        mock_task.remind_count = 2
        
        # Mock 催办人
        mock_reminder = MagicMock(spec=User)
        mock_reminder.id = reminder_id
        mock_reminder.real_name = "催办人"
        mock_reminder.username = "reminder"
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_task,
            mock_reminder,
        ]
        
        # 执行测试
        result = self.engine.remind(task_id, reminder_id)
        
        # 验证结果
        self.assertTrue(result)
        self.assertEqual(mock_task.remind_count, 3)
        self.assertIsNotNone(mock_task.reminded_at)
        
        # 验证日志
        self.engine._log_action.assert_called_once()
        call_kwargs = self.engine._log_action.call_args[1]
        self.assertEqual(call_kwargs['action'], 'REMIND')
        self.assertEqual(call_kwargs['task_id'], task_id)
        
        # 验证通知
        self.engine.notify.notify_remind.assert_called_once_with(
            mock_task,
            reminder_id=reminder_id,
            reminder_name="催办人",
        )
        
        # 验证 commit
        self.mock_db.commit.assert_called_once()

    def test_remind_task_not_found(self):
        """测试任务不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with self.assertRaises(ValueError) as context:
            self.engine.remind(999, 20)
        
        self.assertIn("任务不存在", str(context.exception))

    def test_remind_invalid_status(self):
        """测试非PENDING状态不能催办"""
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.status = "APPROVED"  # 已处理
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_task
        
        with self.assertRaises(ValueError) as context:
            self.engine.remind(1, 20)
        
        self.assertIn("只能催办待处理的任务", str(context.exception))

    def test_remind_count_initial_none(self):
        """测试初始催办次数为None"""
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.id = 1
        mock_task.instance_id = 100
        mock_task.status = "PENDING"
        mock_task.remind_count = None  # 初始为None
        
        mock_reminder = MagicMock(spec=User)
        mock_reminder.real_name = "催办人"
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_task,
            mock_reminder,
        ]
        
        result = self.engine.remind(1, 20)
        
        # 应该从0变成1
        self.assertTrue(result)
        self.assertEqual(mock_task.remind_count, 1)

    def test_remind_reminder_is_none(self):
        """测试催办人不存在时仍能催办"""
        mock_task = MagicMock(spec=ApprovalTask)
        mock_task.id = 1
        mock_task.instance_id = 100
        mock_task.status = "PENDING"
        mock_task.remind_count = 0
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_task,
            None,  # reminder 不存在
        ]
        
        result = self.engine.remind(1, 20)
        
        self.assertTrue(result)
        # reminder_name 应该是 None
        call_kwargs = self.engine.notify.notify_remind.call_args[1]
        self.assertIsNone(call_kwargs['reminder_name'])

    # ========== add_comment() 测试 ==========

    def test_add_comment_success(self):
        """测试成功添加评论"""
        instance_id = 1
        user_id = 10
        content = "这是一条评论"
        
        # Mock 用户
        mock_user = MagicMock(spec=User)
        mock_user.id = user_id
        mock_user.real_name = "评论者"
        mock_user.username = "commenter"
        
        # Mock 实例
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.id = instance_id
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,    # 第一次: 查询用户
            mock_instance,  # 第二次: 查询实例（用于通知）
        ]
        
        # 执行测试
        result = self.engine.add_comment(
            instance_id=instance_id,
            user_id=user_id,
            content=content,
        )
        
        # 验证 db.add 被调用
        self.mock_db.add.assert_called_once()
        added_comment = self.mock_db.add.call_args[0][0]
        self.assertIsInstance(added_comment, ApprovalComment)
        self.assertEqual(added_comment.instance_id, instance_id)
        self.assertEqual(added_comment.user_id, user_id)
        self.assertEqual(added_comment.content, content)
        self.assertEqual(added_comment.user_name, "评论者")
        
        # 验证日志
        self.engine._log_action.assert_called_once()
        call_kwargs = self.engine._log_action.call_args[1]
        self.assertEqual(call_kwargs['action'], 'COMMENT')
        self.assertEqual(call_kwargs['comment'], content)
        
        # 验证 flush 和 commit
        self.mock_db.flush.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_add_comment_with_reply(self):
        """测试添加回复评论"""
        instance_id = 1
        user_id = 10
        content = "回复评论"
        parent_id = 100
        reply_to_user_id = 20
        
        mock_user = MagicMock(spec=User)
        mock_user.real_name = "回复者"
        
        mock_instance = MagicMock(spec=ApprovalInstance)
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            mock_instance,
        ]
        
        result = self.engine.add_comment(
            instance_id=instance_id,
            user_id=user_id,
            content=content,
            parent_id=parent_id,
            reply_to_user_id=reply_to_user_id,
        )
        
        added_comment = self.mock_db.add.call_args[0][0]
        self.assertEqual(added_comment.parent_id, parent_id)
        self.assertEqual(added_comment.reply_to_user_id, reply_to_user_id)

    def test_add_comment_with_mentions(self):
        """测试添加带@提及的评论"""
        instance_id = 1
        user_id = 10
        content = "@张三 @李四 请看一下"
        mentioned_user_ids = [30, 40]
        
        mock_user = MagicMock(spec=User)
        mock_user.real_name = "评论者"
        
        mock_instance = MagicMock(spec=ApprovalInstance)
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            mock_instance,
        ]
        
        result = self.engine.add_comment(
            instance_id=instance_id,
            user_id=user_id,
            content=content,
            mentioned_user_ids=mentioned_user_ids,
        )
        
        added_comment = self.mock_db.add.call_args[0][0]
        self.assertEqual(added_comment.mentioned_user_ids, mentioned_user_ids)
        
        # 验证通知被调用
        self.engine.notify.notify_comment.assert_called_once()
        call_kwargs = self.engine.notify.notify_comment.call_args[1]
        self.assertEqual(call_kwargs['mentioned_user_ids'], mentioned_user_ids)
        self.assertEqual(call_kwargs['comment_content'], content)

    def test_add_comment_with_attachments(self):
        """测试添加带附件的评论"""
        instance_id = 1
        user_id = 10
        content = "请看附件"
        attachments = [
            {"url": "http://example.com/file1.pdf", "name": "文件1.pdf"},
            {"url": "http://example.com/file2.jpg", "name": "图片.jpg"},
        ]
        
        mock_user = MagicMock(spec=User)
        mock_user.real_name = "评论者"
        
        mock_instance = MagicMock(spec=ApprovalInstance)
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            mock_instance,
        ]
        
        result = self.engine.add_comment(
            instance_id=instance_id,
            user_id=user_id,
            content=content,
            attachments=attachments,
        )
        
        added_comment = self.mock_db.add.call_args[0][0]
        self.assertEqual(added_comment.attachments, attachments)

    def test_add_comment_user_not_found(self):
        """测试用户不存在时仍能添加评论（username会是None）"""
        instance_id = 1
        user_id = 999
        content = "匿名评论"
        
        mock_instance = MagicMock(spec=ApprovalInstance)
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            None,  # 用户不存在
            mock_instance,
        ]
        
        result = self.engine.add_comment(instance_id, user_id, content)
        
        added_comment = self.mock_db.add.call_args[0][0]
        self.assertIsNone(added_comment.user_name)

    def test_add_comment_no_mentions_no_notify(self):
        """测试没有@时不发送通知"""
        instance_id = 1
        user_id = 10
        content = "普通评论"
        
        mock_user = MagicMock(spec=User)
        mock_user.real_name = "评论者"
        
        mock_instance = MagicMock(spec=ApprovalInstance)
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            mock_instance,
        ]
        
        result = self.engine.add_comment(
            instance_id=instance_id,
            user_id=user_id,
            content=content,
            mentioned_user_ids=None,  # 没有@
        )
        
        # 不应该调用 notify_comment
        self.engine.notify.notify_comment.assert_not_called()

    def test_add_comment_instance_not_found_no_notify(self):
        """测试实例不存在时不发送通知"""
        mock_user = MagicMock(spec=User)
        mock_user.real_name = "评论者"
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            None,  # 实例不存在
        ]
        
        result = self.engine.add_comment(
            instance_id=999,
            user_id=10,
            content="评论",
            mentioned_user_ids=[20],
        )
        
        # 实例不存在，不发送通知
        self.engine.notify.notify_comment.assert_not_called()


class TestEdgeCases(unittest.TestCase):
    """边界情况测试"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.engine = ApprovalEngineService(db=self.mock_db)
        self.engine.executor = MagicMock()
        self.engine.notify = MagicMock()
        self.engine._log_action = MagicMock()
        self.engine._call_adapter_callback = MagicMock()
        self.engine._get_affected_user_ids = MagicMock(return_value=[])

    def test_add_cc_empty_cc_list(self):
        """测试空抄送列表"""
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.id = 1
        mock_instance.current_node_id = 100
        
        mock_operator = MagicMock(spec=User)
        mock_operator.real_name = "操作人"
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,
            mock_operator,
        ]
        
        self.engine.executor.create_cc_records.return_value = []
        
        result = self.engine.add_cc(1, 10, [])
        
        # 应该返回空列表
        self.assertEqual(result, [])
        # 不应该调用 notify_cc
        self.engine.notify.notify_cc.assert_not_called()

    def test_withdraw_with_none_comment(self):
        """测试撤回时comment为None"""
        mock_instance = MagicMock(spec=ApprovalInstance)
        mock_instance.id = 1
        mock_instance.initiator_id = 10
        mock_instance.status = "PENDING"
        
        mock_initiator = MagicMock(spec=User)
        mock_initiator.real_name = "发起人"
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_instance,
            mock_initiator,
        ]
        
        # comment 为 None
        result = self.engine.withdraw(1, 10, comment=None)
        
        self.assertEqual(result.status, "CANCELLED")
        # 验证日志中comment为None
        call_kwargs = self.engine._log_action.call_args[1]
        self.assertIsNone(call_kwargs['comment'])

    def test_add_comment_all_parameters(self):
        """测试添加评论时所有参数都传入"""
        mock_user = MagicMock(spec=User)
        mock_user.real_name = "评论者"
        
        mock_instance = MagicMock(spec=ApprovalInstance)
        
        self.mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_user,
            mock_instance,
        ]
        
        result = self.engine.add_comment(
            instance_id=1,
            user_id=10,
            content="完整评论",
            parent_id=100,
            reply_to_user_id=20,
            mentioned_user_ids=[30, 40],
            attachments=[{"url": "http://test.com/file.pdf"}],
        )
        
        added_comment = self.mock_db.add.call_args[0][0]
        self.assertEqual(added_comment.parent_id, 100)
        self.assertEqual(added_comment.reply_to_user_id, 20)
        self.assertEqual(added_comment.mentioned_user_ids, [30, 40])
        self.assertIsNotNone(added_comment.attachments)


if __name__ == "__main__":
    unittest.main()
