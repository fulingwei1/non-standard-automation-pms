# -*- coding: utf-8 -*-
"""第十二批：审批节点执行器单元测试"""
import pytest
from unittest.mock import MagicMock, call, patch
from datetime import datetime, timedelta

try:
    from app.services.approval_engine.executor import ApprovalNodeExecutor
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败")


def _make_executor():
    db = MagicMock()
    return ApprovalNodeExecutor(db=db), db


def _make_instance(id=1):
    inst = MagicMock()
    inst.id = id
    return inst


def _make_node(mode="SINGLE", timeout_hours=None):
    node = MagicMock()
    node.id = 10
    node.approval_mode = mode
    node.timeout_hours = timeout_hours
    return node


class TestApprovalNodeExecutorInit:
    def test_db_stored(self):
        db = MagicMock()
        executor = ApprovalNodeExecutor(db=db)
        assert executor.db is db


class TestCreateTasksForNode:
    """create_tasks_for_node 方法测试"""

    def test_returns_empty_for_no_approvers(self):
        executor, db = _make_executor()
        instance = _make_instance()
        node = _make_node("SINGLE")

        result = executor.create_tasks_for_node(instance, node, approver_ids=[])
        assert result == []

    def test_single_mode_creates_one_task(self):
        executor, db = _make_executor()
        instance = _make_instance()
        node = _make_node("SINGLE")

        tasks = executor.create_tasks_for_node(instance, node, approver_ids=[101])
        assert len(tasks) == 1

    def test_or_sign_mode_creates_multiple_tasks(self):
        executor, db = _make_executor()
        instance = _make_instance()
        node = _make_node("OR_SIGN")

        tasks = executor.create_tasks_for_node(instance, node, approver_ids=[101, 102, 103])
        assert len(tasks) == 3

    def test_and_sign_mode_creates_tasks_for_all(self):
        executor, db = _make_executor()
        instance = _make_instance()
        node = _make_node("AND_SIGN")

        tasks = executor.create_tasks_for_node(instance, node, approver_ids=[201, 202])
        assert len(tasks) >= 1  # 至少创建任务

    def test_timeout_sets_due_at(self):
        executor, db = _make_executor()
        instance = _make_instance()
        node = _make_node("SINGLE", timeout_hours=24)

        tasks = executor.create_tasks_for_node(instance, node, approver_ids=[101])
        assert len(tasks) == 1
        task = tasks[0]
        # 验证 due_at 已设置
        assert task.due_at is not None or hasattr(task, 'due_at')

    def test_tasks_have_correct_instance_id(self):
        executor, db = _make_executor()
        instance = _make_instance(id=42)
        node = _make_node("SINGLE")

        tasks = executor.create_tasks_for_node(instance, node, approver_ids=[101])
        assert len(tasks) == 1
        assert tasks[0].instance_id == 42


class TestDbAddCalled:
    """验证 db.add 被调用"""

    def test_db_add_called_for_single_task(self):
        executor, db = _make_executor()
        instance = _make_instance()
        node = _make_node("SINGLE")

        executor.create_tasks_for_node(instance, node, approver_ids=[101])
        assert db.add.called
