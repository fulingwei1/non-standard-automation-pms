# -*- coding: utf-8 -*-
"""Unit tests for app/services/approval_engine/engine/submit.py - batch 41"""
import pytest

pytest.importorskip("app.services.approval_engine.engine.submit")

from unittest.mock import MagicMock, patch


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def submit_mixin(mock_db):
    """Create an ApprovalSubmitMixin with all needed attributes mocked."""
    with patch("app.services.approval_engine.engine.core.ApprovalRouterService"), \
         patch("app.services.approval_engine.engine.core.ApprovalNodeExecutor"), \
         patch("app.services.approval_engine.engine.core.ApprovalNotifyService"), \
         patch("app.services.approval_engine.engine.core.ApprovalDelegateService"):
        from app.services.approval_engine.engine.submit import ApprovalSubmitMixin
        mixin = ApprovalSubmitMixin.__new__(ApprovalSubmitMixin)
        mixin.db = mock_db
        mixin.router = MagicMock()
        mixin.executor = MagicMock()
        mixin._generate_instance_no = MagicMock(return_value="AP2601010001")
        mixin._get_first_node = MagicMock(return_value=None)
        mixin._create_node_tasks = MagicMock()
        mixin._log_action = MagicMock()
        return mixin


def test_submit_raises_if_template_not_found(submit_mixin, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError, match="审批模板不存在"):
        submit_mixin.submit(
            template_code="NONEXIST",
            entity_type="TEST",
            entity_id=1,
            form_data={},
            initiator_id=1
        )


def test_submit_raises_if_initiator_not_found(submit_mixin, mock_db):
    template = MagicMock()
    template.id = 1
    template.is_active = True

    call_count = [0]
    def side_effect(*args, **kwargs):
        call_count[0] += 1
        q = MagicMock()
        if call_count[0] == 1:
            q.filter.return_value.first.return_value = template
        else:
            q.filter.return_value.first.return_value = None
        return q

    mock_db.query.side_effect = side_effect

    with patch("app.services.approval_engine.engine.submit.get_adapter") as mock_ga:
        mock_ga.side_effect = ValueError("不支持的业务类型")
        with pytest.raises(ValueError, match="发起人不存在"):
            submit_mixin.submit(
                template_code="TEST_TMPL",
                entity_type="UNSUPPORTED",
                entity_id=1,
                form_data={},
                initiator_id=999
            )


def test_save_draft_raises_if_template_not_found(submit_mixin, mock_db):
    mock_db.query.return_value.filter.return_value.first.return_value = None
    with pytest.raises(ValueError, match="审批模板不存在"):
        submit_mixin.save_draft(
            template_code="NONEXIST",
            entity_type="TEST",
            entity_id=1,
            form_data={},
            initiator_id=1
        )


def test_submit_mixin_instantiation():
    from app.services.approval_engine.engine.submit import ApprovalSubmitMixin
    mixin = ApprovalSubmitMixin(db=None)
    assert mixin is not None


def test_save_draft_success(submit_mixin, mock_db):
    template = MagicMock()
    template.id = 1
    initiator = MagicMock()
    initiator.real_name = "Test User"

    call_count = [0]
    def side_effect(*args, **kwargs):
        call_count[0] += 1
        q = MagicMock()
        if call_count[0] == 1:
            q.filter.return_value.first.return_value = template
        else:
            q.filter.return_value.first.return_value = initiator
        return q

    mock_db.query.side_effect = side_effect

    with patch("app.services.approval_engine.engine.submit.ApprovalInstance") as MockInst:
        MockInst.return_value = MagicMock()
        result = submit_mixin.save_draft(
            template_code="TMPL",
            entity_type="TEST",
            entity_id=1,
            form_data={},
            initiator_id=1
        )
        mock_db.add.assert_called()
        mock_db.commit.assert_called()
