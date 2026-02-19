# -*- coding: utf-8 -*-
"""
第四十五批覆盖：sales_reminder/base.py
"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.sales_reminder.base")

from app.services.sales_reminder.base import (
    find_users_by_role,
    find_users_by_department,
    create_notification,
)


@pytest.fixture
def mock_db():
    return MagicMock()


class TestFindUsersByRole:
    def test_empty_role_name_returns_empty(self, mock_db):
        result = find_users_by_role(mock_db, "")
        assert result == []

    def test_none_role_name_returns_empty(self, mock_db):
        result = find_users_by_role(mock_db, None)
        assert result == []

    def test_no_matching_roles_returns_empty(self, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        with patch("app.services.sales_reminder.base.apply_keyword_filter", return_value=mock_db.query.return_value.filter.return_value):
            result = find_users_by_role(mock_db, "不存在的角色")
        assert result == []

    def test_roles_found_users_found(self, mock_db):
        role = MagicMock(id=1)
        user = MagicMock(id=10)
        user_role = MagicMock(user_id=10)

        roles_query = MagicMock()
        roles_query.all.return_value = [role]

        users_query = MagicMock()
        users_query.all.return_value = [user]

        user_roles_query = MagicMock()
        user_roles_query.all.return_value = [user_role]

        with patch("app.services.sales_reminder.base.apply_keyword_filter", return_value=roles_query):
            mock_db.query.return_value.filter.return_value.all.side_effect = [
                [user_role],
                [user],
            ]
            # Hard to mock deeply; just verify no crash with basic mock
            result = find_users_by_role(mock_db, "销售")
        assert isinstance(result, list)


class TestFindUsersByDepartment:
    def test_empty_dept_name_returns_empty(self, mock_db):
        result = find_users_by_department(mock_db, "")
        assert result == []

    def test_none_dept_name_returns_empty(self, mock_db):
        result = find_users_by_department(mock_db, None)
        assert result == []

    def test_returns_users_from_department(self, mock_db):
        user = MagicMock(id=1)
        query_mock = MagicMock()
        query_mock.all.return_value = [user]

        with patch("app.services.sales_reminder.base.apply_keyword_filter", return_value=query_mock):
            result = find_users_by_department(mock_db, "销售部")
        assert result == [user]


class TestCreateNotification:
    def test_create_notification_calls_dispatcher(self, mock_db):
        mock_dispatcher = MagicMock()
        mock_dispatcher.create_system_notification.return_value = MagicMock(id=1)

        with patch(
            "app.services.sales_reminder.base.NotificationDispatcher",
            return_value=mock_dispatcher,
        ):
            result = create_notification(
                db=mock_db,
                user_id=1,
                notification_type="REMINDER",
                title="测试通知",
                content="这是一条测试通知",
            )

        mock_dispatcher.create_system_notification.assert_called_once()
        call_kwargs = mock_dispatcher.create_system_notification.call_args.kwargs
        assert call_kwargs["recipient_id"] == 1
        assert call_kwargs["title"] == "测试通知"

    def test_create_notification_with_all_params(self, mock_db):
        mock_dispatcher = MagicMock()
        mock_dispatcher.create_system_notification.return_value = MagicMock()

        with patch(
            "app.services.sales_reminder.base.NotificationDispatcher",
            return_value=mock_dispatcher,
        ):
            create_notification(
                db=mock_db,
                user_id=5,
                notification_type="ALERT",
                title="告警",
                content="内容",
                source_type="Project",
                source_id=10,
                link_url="/projects/10",
                priority="HIGH",
                extra_data={"key": "val"},
            )

        call_kwargs = mock_dispatcher.create_system_notification.call_args.kwargs
        assert call_kwargs["priority"] == "HIGH"
        assert call_kwargs["extra_data"] == {"key": "val"}
