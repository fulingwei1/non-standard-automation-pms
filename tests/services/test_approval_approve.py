# -*- coding: utf-8 -*-
"""ApprovalProcessMixin (engine/approve.py) 单元测试"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock


class TestApprovalProcessMixin:
    """测试审批处理功能"""

    def _make_engine(self):
        """创建一个带有 ApprovalProcessMixin 方法的模拟引擎"""
        from app.services.approval_engine.engine.approve import ApprovalProcessMixin

        # Create a class that combines core + mixin
        class MockEngine(ApprovalProcessMixin):
            def __init__(self):
                self.db = MagicMock()
                self.executor = MagicMock()
                self.notify = MagicMock()
                self.delegate_service = MagicMock()

            def _get_and_validate_task(self, task_id, user_id):
                return self._mock_task

            def _log_action(self, **kwargs):
                pass

            def _advance_to_next_node(self, instance, task):
                pass

            def _call_adapter_callback(self, instance, callback):
                pass

            def _get_previous_node(self, node):
                return None

            def _return_to_node(self, instance, node):
                pass

        engine = MockEngine()
        return engine

    # -- approve --

    def test_approve_success(self):
        engine = self._make_engine()
        task = MagicMock(id=1, node_id=1, instance=MagicMock(id=1, status="IN_PROGRESS"))
        engine._mock_task = task
        engine.executor.process_approval.return_value = (True, None)
        approver = MagicMock(real_name="张三", username="zs")
        engine.db.query.return_value.filter.return_value.first.return_value = approver

        result = engine.approve(1, 1, comment="同意")
        assert result == task
        engine.executor.process_approval.assert_called_once()
        engine.db.commit.assert_called_once()

    def test_approve_no_proceed(self):
        engine = self._make_engine()
        task = MagicMock(id=1, node_id=1, instance=MagicMock(id=1, status="IN_PROGRESS"))
        engine._mock_task = task
        engine.executor.process_approval.return_value = (False, None)
        engine.db.query.return_value.filter.return_value.first.return_value = MagicMock()

        result = engine.approve(1, 1)
        assert result == task

    # -- reject --

    def test_reject_no_comment_raises(self):
        engine = self._make_engine()
        with pytest.raises(ValueError, match="不能为空"):
            engine.reject(1, 1, comment="")

    def test_reject_to_start(self):
        engine = self._make_engine()
        instance = MagicMock(id=1, status="IN_PROGRESS")
        task = MagicMock(id=1, node_id=1, instance=instance, node=MagicMock())
        engine._mock_task = task
        engine.executor.process_approval.return_value = (True, None)
        engine.db.query.return_value.filter.return_value.first.return_value = MagicMock(real_name="R", username="r")

        result = engine.reject(1, 1, comment="不行", reject_to="START")
        assert instance.status == "REJECTED"
        engine.db.commit.assert_called()

    def test_reject_to_prev(self):
        engine = self._make_engine()
        instance = MagicMock(id=1, status="IN_PROGRESS")
        task = MagicMock(id=1, node_id=1, instance=instance, node=MagicMock())
        engine._mock_task = task
        engine.executor.process_approval.return_value = (True, None)
        engine.db.query.return_value.filter.return_value.first.return_value = MagicMock(real_name="R", username="r")

        # _get_previous_node returns None -> rejected
        result = engine.reject(1, 1, comment="退回", reject_to="PREV")
        assert instance.status == "REJECTED"

    def test_reject_to_specific_node(self):
        engine = self._make_engine()
        instance = MagicMock(id=1, status="IN_PROGRESS")
        task = MagicMock(id=1, node_id=1, instance=instance, node=MagicMock())
        engine._mock_task = task
        engine.executor.process_approval.return_value = (True, None)
        approver = MagicMock(real_name="R", username="r")
        target_node = MagicMock(id=5)

        def query_side(*a, **kw):
            m = MagicMock()
            m.filter.return_value.first.return_value = approver
            return m
        engine.db.query.side_effect = query_side

        # Override to test specific node path
        engine.db.query.return_value.filter.return_value.first.return_value = target_node

        result = engine.reject(1, 1, comment="退到节点5", reject_to="5")
        engine.db.commit.assert_called()

    def test_reject_to_invalid_node_id(self):
        engine = self._make_engine()
        instance = MagicMock(id=1, status="IN_PROGRESS")
        task = MagicMock(id=1, node_id=1, instance=instance, node=MagicMock())
        engine._mock_task = task
        engine.executor.process_approval.return_value = (True, None)
        engine.db.query.return_value.filter.return_value.first.return_value = MagicMock(real_name="R", username="r")

        result = engine.reject(1, 1, comment="bad", reject_to="not_a_number")
        assert instance.status == "REJECTED"

    # -- return_to --

    def test_return_to_success(self):
        engine = self._make_engine()
        instance = MagicMock(id=1, status="IN_PROGRESS")
        task = MagicMock(id=1, node_id=1, instance=instance)
        engine._mock_task = task
        target_node = MagicMock(id=3)
        engine.db.query.return_value.filter.return_value.first.return_value = target_node

        result = engine.return_to(1, 1, target_node_id=3, comment="退回")
        assert task.action == "RETURN"
        assert task.status == "COMPLETED"
        engine.db.commit.assert_called()

    # -- transfer --

    def test_transfer_not_allowed(self):
        engine = self._make_engine()
        node = MagicMock(can_transfer=False)
        task = MagicMock(id=1, node=node, instance=MagicMock())
        engine._mock_task = task

        with pytest.raises(ValueError, match="不允许转审"):
            engine.transfer(1, 1, 2)

    def test_transfer_target_not_found(self):
        engine = self._make_engine()
        node = MagicMock(can_transfer=True)
        task = MagicMock(id=1, node=node, instance=MagicMock())
        engine._mock_task = task
        engine.db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="不存在"):
            engine.transfer(1, 1, 999)

    def test_transfer_success(self):
        engine = self._make_engine()
        node = MagicMock(can_transfer=True)
        instance = MagicMock(id=1)
        task = MagicMock(id=1, node=node, node_id=1, instance=instance,
                         task_type="APPROVAL", task_order=1, due_at=None, is_countersign=False)
        engine._mock_task = task
        from_user = MagicMock(real_name="A", username="a")
        to_user = MagicMock(real_name="B", username="b")

        call_count = [0]
        def query_side(model):
            m = MagicMock()
            call_count[0] += 1
            if call_count[0] == 1:
                m.filter.return_value.first.return_value = from_user
            elif call_count[0] == 2:
                m.filter.return_value.first.return_value = to_user
            else:
                m.filter.return_value.first.return_value = MagicMock()
            return m
        engine.db.query.side_effect = query_side

        result = engine.transfer(1, 1, 2)
        assert task.status == "TRANSFERRED"
        engine.db.commit.assert_called()

    # -- add_approver --

    def test_add_approver_not_allowed(self):
        engine = self._make_engine()
        node = MagicMock(can_add_approver=False)
        task = MagicMock(id=1, node=node, instance=MagicMock())
        engine._mock_task = task

        with pytest.raises(ValueError, match="不允许加签"):
            engine.add_approver(1, 1, [2, 3])

    def test_add_approver_before(self):
        engine = self._make_engine()
        node = MagicMock(can_add_approver=True)
        instance = MagicMock(id=1)
        task = MagicMock(id=1, node=node, node_id=1, instance=instance,
                         task_order=1, due_at=None, status="PENDING")
        engine._mock_task = task
        operator = MagicMock(real_name="Op", username="op")
        approver = MagicMock(real_name="New", username="new")

        engine.db.query.return_value.filter.return_value.first.return_value = operator

        result = engine.add_approver(1, 1, [2], position="BEFORE")
        assert task.status == "SKIPPED"
        engine.db.commit.assert_called()
