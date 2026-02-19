# -*- coding: utf-8 -*-
"""Unit tests for app/services/approval_engine/engine/core.py - batch 41"""
import pytest

pytest.importorskip("app.services.approval_engine.engine.core")

from unittest.mock import MagicMock, patch, call
from datetime import datetime


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def core(mock_db):
    with patch("app.services.approval_engine.engine.core.ApprovalRouterService"), \
         patch("app.services.approval_engine.engine.core.ApprovalNodeExecutor"), \
         patch("app.services.approval_engine.engine.core.ApprovalNotifyService"), \
         patch("app.services.approval_engine.engine.core.ApprovalDelegateService"):
        from app.services.approval_engine.engine.core import ApprovalEngineCore
        return ApprovalEngineCore(mock_db)


def test_generate_instance_no_format(core, mock_db):
    mock_db.query.return_value.filter.return_value.with_for_update.return_value.scalar.return_value = None
    with patch("app.services.approval_engine.engine.core.apply_like_filter") as mock_filter:
        mock_filter.return_value = mock_db.query.return_value.filter.return_value
        result = core._generate_instance_no("TEST")
    assert result.startswith("AP")
    assert len(result) > 8


def test_get_first_node_queries_correctly(core, mock_db):
    mock_node = MagicMock()
    mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_node
    result = core._get_first_node(1)
    assert result is mock_node


def test_get_previous_node_none_when_no_prev(core, mock_db):
    mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
    current = MagicMock()
    current.flow_id = 1
    current.node_order = 1
    result = core._get_previous_node(current)
    assert result is None


def test_get_and_validate_task_not_found(core, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError, match="任务不存在"):
        core._get_and_validate_task(999, 1)


def test_get_and_validate_task_wrong_assignee(core, mock_db):
    task = MagicMock()
    task.assignee_id = 2
    task.status = "PENDING"
    mock_db.query.return_value.filter.return_value.first.return_value = task
    with pytest.raises(ValueError, match="无权操作"):
        core._get_and_validate_task(1, 1)


def test_get_and_validate_task_wrong_status(core, mock_db):
    task = MagicMock()
    task.assignee_id = 1
    task.status = "DONE"
    mock_db.query.return_value.filter.return_value.first.return_value = task
    with pytest.raises(ValueError, match="任务状态"):
        core._get_and_validate_task(1, 1)


def test_log_action_creates_log(core, mock_db):
    with patch("app.services.approval_engine.engine.core.ApprovalActionLog") as MockLog:
        MockLog.return_value = MagicMock()
        core._log_action(
            instance_id=1,
            operator_id=2,
            action="SUBMIT"
        )
        mock_db.add.assert_called()


def test_get_affected_user_ids_returns_assignees(core, mock_db):
    task1 = MagicMock()
    task1.assignee_id = 10
    task2 = MagicMock()
    task2.assignee_id = 20
    mock_db.query.return_value.filter.return_value.all.return_value = [task1, task2]
    instance = MagicMock()
    instance.id = 1
    result = core._get_affected_user_ids(instance)
    assert set(result) == {10, 20}
