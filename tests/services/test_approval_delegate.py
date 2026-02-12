# -*- coding: utf-8 -*-
"""ApprovalDelegateService 单元测试"""

import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch


class TestApprovalDelegateService:

    def _make_service(self):
        from app.services.approval_engine.delegate import ApprovalDelegateService
        db = MagicMock()
        return ApprovalDelegateService(db), db

    # -- get_active_delegate --

    def test_get_active_delegate_all_scope(self):
        svc, db = self._make_service()
        delegate = MagicMock(scope="ALL")
        db.query.return_value.filter.return_value.all.return_value = [delegate]
        result = svc.get_active_delegate(1)
        assert result == delegate

    def test_get_active_delegate_template_scope_match(self):
        svc, db = self._make_service()
        delegate = MagicMock(scope="TEMPLATE", template_ids=[10, 20])
        db.query.return_value.filter.return_value.all.return_value = [delegate]
        result = svc.get_active_delegate(1, template_id=10)
        assert result == delegate

    def test_get_active_delegate_template_scope_no_match(self):
        svc, db = self._make_service()
        delegate = MagicMock(scope="TEMPLATE", template_ids=[10, 20])
        db.query.return_value.filter.return_value.all.return_value = [delegate]
        result = svc.get_active_delegate(1, template_id=99)
        assert result is None

    def test_get_active_delegate_none(self):
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.all.return_value = []
        assert svc.get_active_delegate(1) is None

    def test_get_active_delegate_category_scope(self):
        svc, db = self._make_service()
        delegate = MagicMock(scope="CATEGORY", categories=["SALES"])
        db.query.return_value.filter.return_value.all.return_value = [delegate]
        template = MagicMock(category="SALES")
        # Second query for template
        db.query.return_value.filter.return_value.first.return_value = template
        result = svc.get_active_delegate(1, template_id=5)
        assert result == delegate

    # -- apply_delegation --

    def test_apply_delegation_no_config(self):
        svc, db = self._make_service()
        task = MagicMock()
        task.instance = MagicMock(template_id=1)
        with patch.object(svc, 'get_active_delegate', return_value=None):
            result = svc.apply_delegation(task, 1)
        assert result is None

    def test_apply_delegation_success(self):
        svc, db = self._make_service()
        delegate_config = MagicMock(id=1, delegate_id=5)
        task = MagicMock()
        task.instance = MagicMock(template_id=1, id=10)
        user = MagicMock(real_name="李四", username="lisi")
        db.query.return_value.filter.return_value.first.return_value = user

        with patch.object(svc, 'get_active_delegate', return_value=delegate_config):
            result = svc.apply_delegation(task, 1)
        assert result == task
        assert task.assignee_id == 5
        assert task.assignee_type == "DELEGATED"

    # -- create_delegate --

    def test_create_delegate_success(self):
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.first.return_value = None  # no overlap
        result = svc.create_delegate(
            user_id=1, delegate_id=2,
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 31),
        )
        db.add.assert_called_once()
        db.flush.assert_called_once()

    def test_create_delegate_overlap_raises(self):
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.first.return_value = MagicMock()
        with pytest.raises(ValueError, match="重叠"):
            svc.create_delegate(1, 2, date(2026, 1, 1), date(2026, 1, 31))

    # -- update_delegate --

    def test_update_delegate_found(self):
        svc, db = self._make_service()
        delegate = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = delegate
        result = svc.update_delegate(1, scope="ALL", reason="test")
        assert result == delegate

    def test_update_delegate_not_found(self):
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        assert svc.update_delegate(999) is None

    def test_update_delegate_only_allowed_fields(self):
        svc, db = self._make_service()
        delegate = MagicMock(spec=["id", "scope", "reason"])
        db.query.return_value.filter.return_value.first.return_value = delegate
        result = svc.update_delegate(1, scope="TEMPLATE")
        assert result == delegate

    # -- cancel_delegate --

    def test_cancel_delegate_success(self):
        svc, db = self._make_service()
        delegate = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = delegate
        assert svc.cancel_delegate(1) is True
        assert delegate.is_active is False

    def test_cancel_delegate_not_found(self):
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        assert svc.cancel_delegate(999) is False

    # -- get_user_delegates --

    def test_get_user_delegates(self):
        svc, db = self._make_service()
        delegates = [MagicMock(), MagicMock()]
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = delegates
        result = svc.get_user_delegates(1)
        assert len(result) == 2

    def test_get_user_delegates_include_inactive(self):
        svc, db = self._make_service()
        delegates = [MagicMock()]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = delegates
        result = svc.get_user_delegates(1, include_inactive=True)
        assert len(result) == 1

    # -- get_delegated_to_user --

    def test_get_delegated_to_user(self):
        svc, db = self._make_service()
        delegates = [MagicMock()]
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = delegates
        result = svc.get_delegated_to_user(2)
        assert len(result) == 1

    # -- record_delegate_action --

    def test_record_delegate_action(self):
        svc, db = self._make_service()
        log = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = log
        svc.record_delegate_action(1, "APPROVED")
        assert log.action == "APPROVED"

    def test_record_delegate_action_not_found(self):
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        svc.record_delegate_action(999, "APPROVED")  # no error

    # -- notify_original_user --

    def test_notify_original_user_no_log(self):
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        svc.notify_original_user(999)  # no error

    def test_notify_original_user_success(self):
        svc, db = self._make_service()
        log = MagicMock(delegate_config_id=1)
        config = MagicMock(notify_original=True)
        db.query.return_value.filter.return_value.first.side_effect = [log, config]
        with patch.object(svc, '_send_delegate_notification'):
            svc.notify_original_user(1)
        assert log.original_notified is True

    # -- cleanup_expired_delegates --

    def test_cleanup_expired_delegates(self):
        svc, db = self._make_service()
        svc.cleanup_expired_delegates()
        db.query.return_value.filter.return_value.update.assert_called_once()
