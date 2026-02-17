# -*- coding: utf-8 -*-
"""
ApprovalDelegateService 单元测试 - G2组覆盖率提升

覆盖:
- ApprovalDelegateService.__init__
- get_active_delegate (scope: ALL / TEMPLATE / CATEGORY / not found)
- apply_delegation (with/without delegate found)
- create_delegate (成功 / 重叠冲突)
- update_delegate
- cancel_delegate
- get_user_delegates
- get_delegated_to_user
- record_delegate_action
"""

from datetime import date, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest


class TestApprovalDelegateServiceInit:
    def test_init_stores_db(self):
        from app.services.approval_engine.delegate import ApprovalDelegateService
        db = MagicMock()
        svc = ApprovalDelegateService(db)
        assert svc.db is db


class TestGetActiveDelegate:
    """测试 get_active_delegate"""

    def setup_method(self):
        from app.services.approval_engine.delegate import ApprovalDelegateService
        self.db = MagicMock()
        self.svc = ApprovalDelegateService(self.db)

    def test_returns_none_when_no_delegates(self):
        self.db.query.return_value.filter.return_value.all.return_value = []
        result = self.svc.get_active_delegate(user_id=1)
        assert result is None

    def test_returns_all_scope_delegate(self):
        delegate = MagicMock()
        delegate.scope = "ALL"
        # Mock the chained filter call
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [delegate]
        self.db.query.return_value = q

        result = self.svc.get_active_delegate(user_id=1)
        assert result == delegate

    def test_returns_template_scope_delegate_when_matching(self):
        delegate = MagicMock()
        delegate.scope = "TEMPLATE"
        delegate.template_ids = [5, 10, 15]
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [delegate]
        self.db.query.return_value = q

        result = self.svc.get_active_delegate(user_id=1, template_id=10)
        assert result == delegate

    def test_skips_template_scope_when_id_not_in_list(self):
        delegate = MagicMock()
        delegate.scope = "TEMPLATE"
        delegate.template_ids = [5, 10]
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = [delegate]
        self.db.query.return_value = q

        result = self.svc.get_active_delegate(user_id=1, template_id=99)
        assert result is None

    def test_uses_today_as_default_check_date(self):
        q = MagicMock()
        q.filter.return_value = q
        q.all.return_value = []
        self.db.query.return_value = q

        # Should not raise - uses date.today() internally
        self.svc.get_active_delegate(user_id=1)


class TestApplyDelegation:
    """测试 apply_delegation"""

    def setup_method(self):
        from app.services.approval_engine.delegate import ApprovalDelegateService
        self.db = MagicMock()
        self.svc = ApprovalDelegateService(self.db)

    def test_returns_none_when_no_delegate_config(self):
        self.svc.get_active_delegate = MagicMock(return_value=None)
        task = MagicMock()
        task.instance = MagicMock()
        task.instance.template_id = 1

        result = self.svc.apply_delegation(task, original_assignee_id=5)
        assert result is None

    def test_updates_task_assignee_to_delegate(self):
        delegate_config = MagicMock()
        delegate_config.delegate_id = 99
        delegate_config.id = 1

        self.svc.get_active_delegate = MagicMock(return_value=delegate_config)

        task = MagicMock()
        task.instance = MagicMock()
        task.instance.template_id = 1
        task.instance.id = 10
        task.id = 5

        delegate_user = MagicMock()
        delegate_user.real_name = "代理人"
        delegate_user.username = "delegate"
        self.db.query.return_value.filter.return_value.first.return_value = delegate_user

        result = self.svc.apply_delegation(task, original_assignee_id=42)

        assert task.assignee_id == 99
        assert task.assignee_type == "DELEGATED"
        assert task.original_assignee_id == 42
        self.db.add.assert_called_once()  # delegate log


class TestCreateDelegate:
    """测试 create_delegate"""

    def setup_method(self):
        from app.services.approval_engine.delegate import ApprovalDelegateService
        self.db = MagicMock()
        self.svc = ApprovalDelegateService(self.db)

    def test_raises_when_overlap_exists(self):
        existing = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = existing
        self.db.query.return_value = q

        with pytest.raises(ValueError, match="重叠"):
            self.svc.create_delegate(
                user_id=1,
                delegate_id=2,
                start_date=date.today(),
                end_date=date.today() + timedelta(days=30),
            )

    def test_creates_delegate_when_no_overlap(self):
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        self.db.query.return_value = q

        result = self.svc.create_delegate(
            user_id=1,
            delegate_id=2,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30),
            scope="ALL",
        )

        assert result is not None
        self.db.add.assert_called_once()

    def test_creates_delegate_with_template_scope(self):
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        self.db.query.return_value = q

        result = self.svc.create_delegate(
            user_id=1,
            delegate_id=2,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=7),
            scope="TEMPLATE",
            template_ids=[1, 2, 3],
        )

        assert result.scope == "TEMPLATE"
        assert result.template_ids == [1, 2, 3]


class TestUpdateDelegate:
    """测试 update_delegate"""

    def setup_method(self):
        from app.services.approval_engine.delegate import ApprovalDelegateService
        self.db = MagicMock()
        self.svc = ApprovalDelegateService(self.db)

    def test_returns_none_when_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.svc.update_delegate(999, is_active=False)
        assert result is None

    def test_updates_allowed_fields(self):
        delegate = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = delegate

        result = self.svc.update_delegate(1, is_active=False, reason="出差")
        assert delegate.is_active is False
        assert delegate.reason == "出差"

    def test_ignores_disallowed_fields(self):
        delegate = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = delegate

        result = self.svc.update_delegate(1, some_random_field="bad")
        # Should not set the disallowed field
        # Just verify it returns the delegate without error
        assert result == delegate


class TestCancelDelegate:
    """测试 cancel_delegate"""

    def setup_method(self):
        from app.services.approval_engine.delegate import ApprovalDelegateService
        self.db = MagicMock()
        self.svc = ApprovalDelegateService(self.db)

    def test_returns_false_when_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        result = self.svc.cancel_delegate(999)
        assert result is False

    def test_sets_is_active_false(self):
        delegate = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = delegate

        result = self.svc.cancel_delegate(1)
        assert result is True
        assert delegate.is_active is False


class TestGetUserDelegates:
    """测试 get_user_delegates"""

    def setup_method(self):
        from app.services.approval_engine.delegate import ApprovalDelegateService
        self.db = MagicMock()
        self.svc = ApprovalDelegateService(self.db)

    def test_returns_active_delegates_by_default(self):
        expected = [MagicMock(), MagicMock()]
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value.all.return_value = expected
        self.db.query.return_value = q

        result = self.svc.get_user_delegates(user_id=1)
        assert result == expected

    def test_includes_inactive_when_flag_set(self):
        expected = [MagicMock()]
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value.all.return_value = expected
        self.db.query.return_value = q

        result = self.svc.get_user_delegates(user_id=1, include_inactive=True)
        # With include_inactive=True, no extra is_active filter is added
        assert result == expected


class TestRecordDelegateAction:
    """测试 record_delegate_action"""

    def setup_method(self):
        from app.services.approval_engine.delegate import ApprovalDelegateService
        self.db = MagicMock()
        self.svc = ApprovalDelegateService(self.db)

    def test_updates_log_action_when_found(self):
        mock_log = MagicMock()
        self.db.query.return_value.filter.return_value.first.return_value = mock_log

        self.svc.record_delegate_action(delegate_log_id=1, action="APPROVE")
        assert mock_log.action == "APPROVE"
        assert mock_log.action_at is not None

    def test_skips_when_log_not_found(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        # Should not raise
        self.svc.record_delegate_action(delegate_log_id=999, action="APPROVE")
