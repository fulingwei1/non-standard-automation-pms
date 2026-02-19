# -*- coding: utf-8 -*-
"""
第三十三批覆盖率测试 - 审批操作混入 (ApprovalActionsMixin)
"""
import pytest
from unittest.mock import MagicMock, call
from datetime import datetime

try:
    from app.services.approval_engine.engine.actions import ApprovalActionsMixin
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="actions 导入失败")


def _make_engine(instance=None, task=None, user=None):
    """构造最小化引擎 mock"""
    engine = MagicMock(spec=ApprovalActionsMixin)
    engine.db = MagicMock()

    # query chain
    def query_side(model):
        q = MagicMock()
        q.filter.return_value.first.return_value = {
            "instance": instance,
            "task": task,
            "user": user,
        }.get(model.__name__.lower().replace("approval", "").replace("record", "instance"), None)
        q.filter.return_value.update.return_value = None
        return q

    engine.db.query.side_effect = query_side
    engine._log_action = MagicMock()
    engine._get_affected_user_ids = MagicMock(return_value=[2, 3])
    engine._call_adapter_callback = MagicMock()
    engine.executor = MagicMock()
    engine.notify = MagicMock()
    return engine


class TestAddCc:
    def test_instance_not_found_raises(self):
        """审批实例不存在时抛出 ValueError"""
        engine = MagicMock(spec=ApprovalActionsMixin)
        engine.db = MagicMock()
        mock_q = MagicMock()
        mock_q.filter.return_value.first.return_value = None
        engine.db.query.return_value = mock_q

        with pytest.raises(ValueError, match="审批实例不存在"):
            ApprovalActionsMixin.add_cc(engine, instance_id=999, operator_id=1, cc_user_ids=[2])

    def test_add_cc_creates_records(self):
        """加抄送成功时创建抄送记录并通知"""
        engine = MagicMock(spec=ApprovalActionsMixin)
        engine.db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.current_node_id = 10

        mock_operator = MagicMock()
        mock_operator.real_name = "张三"
        mock_operator.username = "zhangsan"

        mock_cc1 = MagicMock()
        mock_cc2 = MagicMock()

        def query_dispatch(model):
            q = MagicMock()
            name = model.__name__
            if "Instance" in name:
                q.filter.return_value.first.return_value = mock_instance
            elif "User" in name:
                q.filter.return_value.first.return_value = mock_operator
            else:
                q.filter.return_value.first.return_value = None
            return q

        engine.db.query.side_effect = query_dispatch
        engine.executor = MagicMock()
        engine.executor.create_cc_records.return_value = [mock_cc1, mock_cc2]
        engine._log_action = MagicMock()
        engine.notify = MagicMock()

        result = ApprovalActionsMixin.add_cc(engine, instance_id=1, operator_id=1, cc_user_ids=[2, 3])

        assert len(result) == 2
        engine.notify.notify_cc.assert_called()
        engine.db.commit.assert_called_once()


class TestWithdraw:
    def test_instance_not_found_raises(self):
        """实例不存在时抛出 ValueError"""
        engine = MagicMock(spec=ApprovalActionsMixin)
        engine.db = MagicMock()
        engine.db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="审批实例不存在"):
            ApprovalActionsMixin.withdraw(engine, instance_id=999, initiator_id=1)

    def test_not_initiator_raises(self):
        """非发起人撤回时抛出 ValueError"""
        engine = MagicMock(spec=ApprovalActionsMixin)
        engine.db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.initiator_id = 5  # 发起人是5
        mock_instance.status = "PENDING"
        engine.db.query.return_value.filter.return_value.first.return_value = mock_instance

        with pytest.raises(ValueError, match="只有发起人"):
            ApprovalActionsMixin.withdraw(engine, instance_id=1, initiator_id=1)  # 操作人是1

    def test_wrong_status_raises(self):
        """状态不是PENDING/DRAFT时抛出 ValueError"""
        engine = MagicMock(spec=ApprovalActionsMixin)
        engine.db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.initiator_id = 1
        mock_instance.status = "APPROVED"
        engine.db.query.return_value.filter.return_value.first.return_value = mock_instance

        with pytest.raises(ValueError, match="当前状态不允许撤回"):
            ApprovalActionsMixin.withdraw(engine, instance_id=1, initiator_id=1)

    def test_withdraw_success(self):
        """正常撤回更新状态为CANCELLED"""
        engine = MagicMock(spec=ApprovalActionsMixin)
        engine.db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.initiator_id = 1
        mock_instance.status = "PENDING"

        mock_user = MagicMock()
        mock_user.real_name = "李四"
        mock_user.username = "lisi"

        def query_dispatch(model):
            q = MagicMock()
            name = model.__name__
            if "Instance" in name:
                q.filter.return_value.first.return_value = mock_instance
            elif "User" in name:
                q.filter.return_value.first.return_value = mock_user
            else:
                q.filter.return_value.update.return_value = None
            return q

        engine.db.query.side_effect = query_dispatch
        engine._get_affected_user_ids = MagicMock(return_value=[2])
        engine._call_adapter_callback = MagicMock()
        engine._log_action = MagicMock()
        engine.notify = MagicMock()

        result = ApprovalActionsMixin.withdraw(engine, instance_id=1, initiator_id=1, comment="不需要了")

        assert mock_instance.status == "CANCELLED"
        engine.db.commit.assert_called_once()


class TestTerminate:
    def test_terminate_success(self):
        """管理员终止审批，状态更新为TERMINATED"""
        engine = MagicMock(spec=ApprovalActionsMixin)
        engine.db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.status = "PENDING"

        mock_operator = MagicMock()
        mock_operator.real_name = "管理员"
        mock_operator.username = "admin"

        def query_dispatch(model):
            q = MagicMock()
            name = model.__name__
            if "Instance" in name:
                q.filter.return_value.first.return_value = mock_instance
            elif "User" in name:
                q.filter.return_value.first.return_value = mock_operator
            else:
                q.filter.return_value.update.return_value = None
            return q

        engine.db.query.side_effect = query_dispatch
        engine._call_adapter_callback = MagicMock()
        engine._log_action = MagicMock()

        result = ApprovalActionsMixin.terminate(engine, instance_id=1, operator_id=99, comment="流程有误")

        assert mock_instance.status == "TERMINATED"
        engine.db.commit.assert_called_once()


class TestRemind:
    def test_task_not_found_raises(self):
        """任务不存在时抛出 ValueError"""
        engine = MagicMock(spec=ApprovalActionsMixin)
        engine.db = MagicMock()
        engine.db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="任务不存在"):
            ApprovalActionsMixin.remind(engine, task_id=999, reminder_id=1)

    def test_remind_success(self):
        """催办成功返回 True"""
        engine = MagicMock(spec=ApprovalActionsMixin)
        engine.db = MagicMock()

        mock_task = MagicMock()
        mock_task.id = 5
        mock_task.instance_id = 1
        mock_task.status = "PENDING"
        mock_task.remind_count = 0

        mock_reminder = MagicMock()
        mock_reminder.real_name = "催办人"
        mock_reminder.username = "reminder"

        def query_dispatch(model):
            q = MagicMock()
            name = model.__name__
            if "Task" in name:
                q.filter.return_value.first.return_value = mock_task
            elif "User" in name:
                q.filter.return_value.first.return_value = mock_reminder
            return q

        engine.db.query.side_effect = query_dispatch
        engine._log_action = MagicMock()
        engine.notify = MagicMock()

        result = ApprovalActionsMixin.remind(engine, task_id=5, reminder_id=2)

        assert result is True
        assert mock_task.remind_count == 1


class TestAddComment:
    def test_add_comment_creates_record(self):
        """添加评论成功创建ApprovalComment记录"""
        engine = MagicMock(spec=ApprovalActionsMixin)
        engine.db = MagicMock()

        mock_user = MagicMock()
        mock_user.real_name = "评论者"
        mock_user.username = "commenter"

        mock_instance = MagicMock()
        mock_instance.id = 1

        def query_dispatch(model):
            q = MagicMock()
            name = model.__name__
            if "User" in name:
                q.filter.return_value.first.return_value = mock_user
            elif "Instance" in name:
                q.filter.return_value.first.return_value = mock_instance
            return q

        engine.db.query.side_effect = query_dispatch
        engine._log_action = MagicMock()
        engine.notify = MagicMock()

        result = ApprovalActionsMixin.add_comment(
            engine,
            instance_id=1,
            user_id=3,
            content="这个需要补充附件",
            mentioned_user_ids=[4, 5]
        )

        engine.db.add.assert_called_once()
        engine.db.flush.assert_called_once()
        engine.db.commit.assert_called_once()
        engine.notify.notify_comment.assert_called_once()
