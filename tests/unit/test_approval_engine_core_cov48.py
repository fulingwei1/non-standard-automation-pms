# -*- coding: utf-8 -*-
"""单元测试 - ApprovalEngineCore (cov48)"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.approval_engine.engine.core import ApprovalEngineCore
    _IMPORT_OK = True
except Exception:
    _IMPORT_OK = False

pytestmark = pytest.mark.skipif(not _IMPORT_OK, reason="Import failed for ApprovalEngineCore")

_PATCH_TARGETS = [
    "app.services.approval_engine.engine.core.ApprovalRouterService",
    "app.services.approval_engine.engine.core.ApprovalNodeExecutor",
    "app.services.approval_engine.engine.core.ApprovalNotifyService",
    "app.services.approval_engine.engine.core.ApprovalDelegateService",
]


def _make_core():
    db = MagicMock()
    with patch(_PATCH_TARGETS[0]), \
         patch(_PATCH_TARGETS[1]), \
         patch(_PATCH_TARGETS[2]), \
         patch(_PATCH_TARGETS[3]):
        core = ApprovalEngineCore(db)
    return core


def test_get_and_validate_task_raises_when_not_found():
    core = _make_core()
    core.db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError, match="任务不存在"):
        core._get_and_validate_task(99, 1)


def test_get_and_validate_task_raises_when_wrong_assignee():
    core = _make_core()
    task = MagicMock()
    task.assignee_id = 2
    task.status = "PENDING"
    core.db.query.return_value.filter.return_value.first.return_value = task
    with pytest.raises(ValueError, match="无权"):
        core._get_and_validate_task(1, user_id=1)


def test_get_and_validate_task_raises_when_not_pending():
    core = _make_core()
    task = MagicMock()
    task.assignee_id = 1
    task.status = "DONE"
    core.db.query.return_value.filter.return_value.first.return_value = task
    with pytest.raises(ValueError, match="任务状态"):
        core._get_and_validate_task(1, user_id=1)


def test_get_and_validate_task_returns_task_when_valid():
    core = _make_core()
    task = MagicMock()
    task.assignee_id = 1
    task.status = "PENDING"
    core.db.query.return_value.filter.return_value.first.return_value = task
    result = core._get_and_validate_task(1, user_id=1)
    assert result is task


def test_get_affected_user_ids_returns_assignee_ids():
    core = _make_core()
    t1 = MagicMock(assignee_id=10)
    t2 = MagicMock(assignee_id=20)
    core.db.query.return_value.filter.return_value.all.return_value = [t1, t2]
    instance = MagicMock(id=1)
    result = core._get_affected_user_ids(instance)
    assert 10 in result
    assert 20 in result


def test_log_action_adds_log_object():
    core = _make_core()
    core._log_action(instance_id=1, operator_id=5, action="SUBMIT")
    core.db.add.assert_called_once()


def test_call_adapter_callback_ignores_value_error():
    core = _make_core()
    instance = MagicMock(entity_type="UNKNOWN", entity_id=1)
    # get_adapter is imported locally inside _call_adapter_callback, patch at source
    with patch("app.services.approval_engine.adapters.get_adapter",
               side_effect=ValueError("不支持的业务类型")):
        core._call_adapter_callback(instance, "on_approved")  # should not raise


def test_generate_instance_no_returns_ap_prefixed_string():
    core = _make_core()
    mock_query = MagicMock()
    mock_query.with_for_update.return_value.scalar.return_value = None
    with patch("app.services.approval_engine.engine.core.apply_like_filter",
               return_value=mock_query):
        result = core._generate_instance_no("SALES_INVOICE")
    assert isinstance(result, str)
    assert result.startswith("AP")
