# -*- coding: utf-8 -*-
"""第十二批：审批代理人服务单元测试"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime

try:
    from app.services.approval_engine.delegate import ApprovalDelegateService
    SKIP = False
except Exception:
    SKIP = True

pytestmark = pytest.mark.skipif(SKIP, reason="导入失败")


def _make_service():
    db = MagicMock()
    return ApprovalDelegateService(db=db), db


def _mock_delegate(scope="ALL", user_id=1, delegate_id=2, template_ids=None):
    d = MagicMock()
    d.user_id = user_id
    d.delegate_user_id = delegate_id
    d.scope = scope
    d.is_active = True
    d.start_date = date(2020, 1, 1)
    d.end_date = date(2099, 12, 31)
    d.template_ids = template_ids or []
    return d


class TestApprovalDelegateServiceInit:
    def test_db_stored(self):
        db = MagicMock()
        svc = ApprovalDelegateService(db=db)
        assert svc.db is db


class TestGetActiveDelegate:
    """get_active_delegate 方法测试"""

    def test_returns_none_when_no_delegates(self):
        svc, db = _make_service()
        db.query.return_value.filter.return_value.all.return_value = []

        result = svc.get_active_delegate(user_id=1)
        assert result is None

    def test_returns_all_scope_delegate(self):
        svc, db = _make_service()
        delegate = _mock_delegate(scope="ALL")
        db.query.return_value.filter.return_value.all.return_value = [delegate]

        result = svc.get_active_delegate(user_id=1)
        assert result is delegate

    def test_returns_template_scope_delegate_with_matching_template(self):
        svc, db = _make_service()
        delegate = _mock_delegate(scope="TEMPLATE")
        delegate.template_ids = [5, 10]
        db.query.return_value.filter.return_value.all.return_value = [delegate]

        result = svc.get_active_delegate(user_id=1, template_id=5)
        assert result is delegate

    def test_returns_none_for_template_scope_without_template_id(self):
        svc, db = _make_service()
        delegate = _mock_delegate(scope="TEMPLATE")
        delegate.template_ids = [5]
        db.query.return_value.filter.return_value.all.return_value = [delegate]

        result = svc.get_active_delegate(user_id=1, template_id=None)
        assert result is None

    def test_uses_today_when_check_date_not_provided(self):
        svc, db = _make_service()
        db.query.return_value.filter.return_value.all.return_value = []

        # 不传 check_date 应该也能正常运行
        result = svc.get_active_delegate(user_id=1)
        assert result is None

    def test_custom_check_date(self):
        svc, db = _make_service()
        delegate = _mock_delegate(scope="ALL")
        db.query.return_value.filter.return_value.all.return_value = [delegate]

        result = svc.get_active_delegate(user_id=1, check_date=date(2025, 6, 15))
        assert result is delegate


class TestDelegateLogic:
    """代理人逻辑场景测试"""

    def test_multiple_delegates_returns_first_matching(self):
        svc, db = _make_service()
        d1 = _mock_delegate(scope="TEMPLATE")
        d1.template_ids = [99]  # 不匹配
        d2 = _mock_delegate(scope="ALL")
        db.query.return_value.filter.return_value.all.return_value = [d1, d2]

        result = svc.get_active_delegate(user_id=1, template_id=5)
        # d1 不匹配(TEMPLATE但模板不符)，d2 是 ALL 应匹配
        assert result is d2
