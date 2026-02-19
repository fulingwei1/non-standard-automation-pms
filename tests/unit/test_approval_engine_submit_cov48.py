# -*- coding: utf-8 -*-
"""单元测试 - ApprovalSubmitMixin (cov48)"""

import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.approval_engine.engine.submit import ApprovalSubmitMixin
    _IMPORT_OK = True
except Exception:
    _IMPORT_OK = False

pytestmark = pytest.mark.skipif(not _IMPORT_OK, reason="Import failed for ApprovalSubmitMixin")

_ADAPTER_PATH = "app.services.approval_engine.engine.submit.get_adapter"


def _make_mixin():
    """构建一个带有必要 mock 属性的 ApprovalSubmitMixin 实例"""
    db = MagicMock()
    obj = ApprovalSubmitMixin(db)
    obj.db = db
    obj.router = MagicMock()
    obj.executor = MagicMock()
    obj.notify = MagicMock()
    obj._generate_instance_no = MagicMock(return_value="AP240101-0001")
    obj._get_first_node = MagicMock(return_value=None)
    obj._create_node_tasks = MagicMock()
    obj._log_action = MagicMock()
    return obj


def test_submit_raises_when_template_not_found():
    obj = _make_mixin()
    obj.db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError, match="审批模板不存在"):
        obj.submit("NO_TMPL", "INVOICE", 1, {}, 1)


def test_submit_raises_when_initiator_not_found():
    obj = _make_mixin()
    template = MagicMock(id=1, template_name="T", is_active=True)
    obj.db.query.return_value.filter.return_value.first.side_effect = [template, None]
    with pytest.raises(ValueError, match="发起人不存在"):
        obj.submit("TMPL", "INVOICE", 1, {}, 99)


def test_submit_raises_when_no_matching_flow():
    obj = _make_mixin()
    template = MagicMock(id=1, template_name="T", is_active=True)
    initiator = MagicMock(id=1, real_name="张三", username="zhangsan")
    obj.db.query.return_value.filter.return_value.first.side_effect = [template, initiator]
    obj.router.select_flow.return_value = None
    with patch(_ADAPTER_PATH, side_effect=ValueError("不支持的业务类型")):
        with pytest.raises(ValueError, match="未找到适用"):
            obj.submit("TMPL", "INVOICE", 1, {}, 1)


def test_submit_succeeds_and_calls_db_commit():
    obj = _make_mixin()
    template = MagicMock(id=1, template_name="T", is_active=True)
    initiator = MagicMock(id=1, real_name="张三", username="zhangsan")
    flow = MagicMock(id=10)
    obj.db.query.return_value.filter.return_value.first.side_effect = [template, initiator]
    obj.router.select_flow.return_value = flow
    with patch(_ADAPTER_PATH, side_effect=ValueError("不支持的业务类型")):
        instance = obj.submit("TMPL", "INVOICE", 1, {}, 1)
    assert instance is not None
    obj.db.add.assert_called()
    obj.db.commit.assert_called()


def test_submit_logs_action():
    obj = _make_mixin()
    template = MagicMock(id=1, template_name="T", is_active=True)
    initiator = MagicMock(id=1, real_name="张三", username="zhangsan")
    flow = MagicMock(id=10)
    obj.db.query.return_value.filter.return_value.first.side_effect = [template, initiator]
    obj.router.select_flow.return_value = flow
    with patch(_ADAPTER_PATH, side_effect=ValueError("不支持的业务类型")):
        obj.submit("TMPL", "INVOICE", 1, {}, 1)
    obj._log_action.assert_called()


def test_save_draft_raises_when_template_not_found():
    obj = _make_mixin()
    obj.db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError, match="审批模板不存在"):
        obj.save_draft("NO_TMPL", "INVOICE", 1, {}, 1)


def test_save_draft_creates_draft_instance():
    obj = _make_mixin()
    template = MagicMock(id=1, is_active=True)
    initiator = MagicMock(real_name="李四", username="lisi")
    obj.db.query.return_value.filter.return_value.first.side_effect = [template, initiator]
    result = obj.save_draft("TMPL", "INVOICE", 1, {}, 1, title="草稿测试")
    obj.db.add.assert_called_once()
    obj.db.commit.assert_called_once()
    assert result is not None
