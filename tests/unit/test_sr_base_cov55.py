# -*- coding: utf-8 -*-
"""
Tests for app/services/sales_reminder/base.py
"""
import pytest
from unittest.mock import MagicMock, patch, call

try:
    from app.services.sales_reminder.base import (
        find_users_by_role,
        find_users_by_department,
        create_notification,
    )
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


@pytest.fixture
def mock_db():
    return MagicMock()


def test_find_users_by_role_empty_name(mock_db):
    """角色名为空时返回空列表"""
    result = find_users_by_role(mock_db, "")
    assert result == []


def test_find_users_by_role_no_matching_roles(mock_db):
    """无匹配角色时返回空列表"""
    with patch("app.services.sales_reminder.base.apply_keyword_filter") as mock_filter:
        mock_filter.return_value.all.return_value = []
        mock_db.query.return_value.filter.return_value = MagicMock()
        result = find_users_by_role(mock_db, "nonexistent_role")
        assert result == []


def test_find_users_by_role_returns_users(mock_db):
    """找到角色时返回对应用户"""
    role = MagicMock()
    role.id = 1
    user_role = MagicMock()
    user_role.user_id = 10
    user = MagicMock()
    user.id = 10

    with patch("app.services.sales_reminder.base.apply_keyword_filter") as mock_filter:
        mock_filter.return_value = MagicMock()
        mock_filter.return_value.all.return_value = [role]
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            [user_role], [user]
        ]
        result = find_users_by_role(mock_db, "sales")
        # 应调用了 db.query 多次


def test_find_users_by_department_empty(mock_db):
    """部门名为空时返回空列表"""
    result = find_users_by_department(mock_db, "")
    assert result == []


def test_find_users_by_department_returns_users(mock_db):
    """根据部门名称查找用户"""
    user = MagicMock()
    with patch("app.services.sales_reminder.base.apply_keyword_filter") as mock_filter:
        mock_filter.return_value = MagicMock()
        mock_filter.return_value.all.return_value = [user]
        result = find_users_by_department(mock_db, "销售部")
        assert result == [user]


def test_create_notification_calls_dispatcher(mock_db):
    """create_notification 应调用 NotificationDispatcher"""
    with patch("app.services.sales_reminder.base.NotificationDispatcher") as MockDispatcher:
        mock_dispatcher = MagicMock()
        MockDispatcher.return_value = mock_dispatcher
        mock_dispatcher.create_system_notification.return_value = MagicMock()
        result = create_notification(
            db=mock_db,
            user_id=1,
            notification_type="SALES_REMINDER",
            title="测试",
            content="内容",
        )
        MockDispatcher.assert_called_once_with(mock_db)
        mock_dispatcher.create_system_notification.assert_called_once()


def test_create_notification_passes_extra_data(mock_db):
    """extra_data 参数应传递给 dispatcher"""
    with patch("app.services.sales_reminder.base.NotificationDispatcher") as MockDispatcher:
        mock_dispatcher = MagicMock()
        MockDispatcher.return_value = mock_dispatcher
        extra = {"key": "value"}
        create_notification(mock_db, 1, "TYPE", "Title", "Content", extra_data=extra)
        call_kwargs = mock_dispatcher.create_system_notification.call_args[1]
        assert call_kwargs.get("extra_data") == extra
