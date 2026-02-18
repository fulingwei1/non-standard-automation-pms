# -*- coding: utf-8 -*-
"""第十二批：审批处理功能单元测试"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.approval_engine.engine.approve import ApprovalProcessMixin
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败")


def _make_mixin():
    """创建一个混入了 ApprovalProcessMixin 的测试对象"""
    mixin = ApprovalProcessMixin()
    # 注入必要属性
    mixin.db = MagicMock()
    mixin.executor = MagicMock()
    return mixin


def _make_task(task_id=1, assignee_id=10, instance_id=100):
    task = MagicMock()
    task.id = task_id
    task.assignee_id = assignee_id
    task.instance_id = instance_id
    task.node_id = 5
    inst = MagicMock()
    inst.id = instance_id
    inst.status = "IN_PROGRESS"
    task.instance = inst
    task.node = MagicMock()
    return task


def _make_approver(user_id=10):
    user = MagicMock()
    user.id = user_id
    user.real_name = "张三"
    user.username = "zhangsan"
    return user


class TestApprovalProcessMixinApprove:
    """approve 方法测试"""

    def _setup_approve(self, mixin, task, can_proceed=True):
        mixin._get_and_validate_task = MagicMock(return_value=task)
        approver = _make_approver()
        mixin.db.query.return_value.filter.return_value.first.return_value = approver
        mixin.executor.process_approval.return_value = (can_proceed, None)
        mixin._log_action = MagicMock()
        mixin._advance_to_next_node = MagicMock()
        return approver

    def test_approve_returns_task(self):
        mixin = _make_mixin()
        task = _make_task()
        self._setup_approve(mixin, task)

        result = mixin.approve(task_id=1, approver_id=10)
        assert result is task

    def test_approve_calls_executor_process_approval(self):
        mixin = _make_mixin()
        task = _make_task()
        self._setup_approve(mixin, task)

        mixin.approve(task_id=1, approver_id=10, comment="同意")
        mixin.executor.process_approval.assert_called_once()

    def test_approve_advances_when_can_proceed(self):
        mixin = _make_mixin()
        task = _make_task()
        self._setup_approve(mixin, task, can_proceed=True)

        mixin.approve(task_id=1, approver_id=10)
        mixin._advance_to_next_node.assert_called_once()

    def test_approve_does_not_advance_when_cannot_proceed(self):
        mixin = _make_mixin()
        task = _make_task()
        self._setup_approve(mixin, task, can_proceed=False)

        mixin.approve(task_id=1, approver_id=10)
        mixin._advance_to_next_node.assert_not_called()

    def test_approve_commits_db(self):
        mixin = _make_mixin()
        task = _make_task()
        self._setup_approve(mixin, task)

        mixin.approve(task_id=1, approver_id=10)
        mixin.db.commit.assert_called_once()


class TestApprovalProcessMixinReject:
    """reject 方法测试"""

    def _setup_reject(self, mixin, task):
        mixin._get_and_validate_task = MagicMock(return_value=task)
        approver = _make_approver()
        mixin.db.query.return_value.filter.return_value.first.return_value = approver
        mixin.executor.process_approval.return_value = (False, None)
        mixin._log_action = MagicMock()
        mixin._call_adapter_callback = MagicMock()
        mixin.notify = MagicMock()
        mixin._get_previous_node = MagicMock(return_value=None)
        return approver

    def test_reject_raises_without_comment(self):
        mixin = _make_mixin()
        with pytest.raises(ValueError):
            mixin.reject(task_id=1, approver_id=10, comment="")

    def test_reject_returns_task(self):
        mixin = _make_mixin()
        task = _make_task()
        self._setup_reject(mixin, task)

        result = mixin.reject(task_id=1, approver_id=10, comment="不同意")
        assert result is task

    def test_reject_to_start_sets_status_rejected(self):
        mixin = _make_mixin()
        task = _make_task()
        self._setup_reject(mixin, task)

        mixin.reject(task_id=1, approver_id=10, comment="驳回", reject_to="START")
        assert task.instance.status == "REJECTED"
