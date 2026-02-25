# -*- coding: utf-8 -*-
"""Culture Wall Service 测试 - Batch 2"""
from datetime import date, datetime
from unittest.mock import MagicMock, patch
import pytest

from app.services.culture_wall_service import (
    get_culture_wall_config, check_user_role_permission,
    get_content_types_config, build_content_query,
    query_content_by_type, get_read_records, format_content,
    get_personal_goals, format_goal, get_notifications
)


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_config():
    c = MagicMock()
    c.is_default = True
    c.is_enabled = True
    c.visible_roles = ["ADMIN", "PM"]
    c.content_types = {
        "NEWS": {"enabled": True, "max_count": 5},
        "PERSONAL_GOAL": {"enabled": True, "max_count": 3},
        "NOTIFICATION": {"enabled": True, "max_count": 10},
        "DISABLED_TYPE": {"enabled": False}
    }
    return c


class TestGetCultureWallConfig:
    def test_default_config(self, mock_db, mock_config):
        mock_db.query.return_value.filter.return_value.first.return_value = mock_config
        result = get_culture_wall_config(mock_db)
        assert result == mock_config

    def test_fallback_to_latest(self, mock_db, mock_config):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_config
        result = get_culture_wall_config(mock_db)
        assert result == mock_config

    def test_no_config(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        result = get_culture_wall_config(mock_db)
        assert result is None


class TestCheckUserRolePermission:
    def test_no_config(self):
        assert check_user_role_permission(None, ["ADMIN"]) is True

    def test_no_visible_roles(self):
        config = MagicMock()
        config.visible_roles = []
        assert check_user_role_permission(config, ["ADMIN"]) is True

    def test_none_visible_roles(self):
        config = MagicMock()
        config.visible_roles = None
        assert check_user_role_permission(config, ["PM"]) is True

    def test_user_has_permission(self, mock_config):
        assert check_user_role_permission(mock_config, ["PM"]) is True

    def test_user_no_permission(self, mock_config):
        assert check_user_role_permission(mock_config, ["VIEWER"]) is False

    def test_multiple_roles_one_matches(self, mock_config):
        assert check_user_role_permission(mock_config, ["VIEWER", "ADMIN"]) is True


class TestGetContentTypesConfig:
    def test_with_config(self, mock_config):
        result = get_content_types_config(mock_config)
        assert "NEWS" in result

    def test_none_config(self):
        assert get_content_types_config(None) == {}

    def test_no_content_types(self):
        config = MagicMock()
        config.content_types = None
        assert get_content_types_config(config) == {}


class TestQueryContentByType:
    def test_enabled_type(self):
        content_query = MagicMock()
        items = [MagicMock()]
        content_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = items
        config = {"NEWS": {"enabled": True, "max_count": 5}}
        result = query_content_by_type(content_query, "NEWS", config)
        assert len(result) == 1

    def test_disabled_type(self):
        content_query = MagicMock()
        config = {"DISABLED": {"enabled": False}}
        result = query_content_by_type(content_query, "DISABLED", config)
        assert result == []

    def test_unknown_type_uses_default(self):
        content_query = MagicMock()
        content_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        result = query_content_by_type(content_query, "UNKNOWN", {}, default_max_count=20)
        content_query.filter.return_value.order_by.return_value.limit.assert_called_with(20)


class TestGetReadRecords:
    def test_empty_content_ids(self, mock_db):
        assert get_read_records(mock_db, [], 1) == {}

    def test_with_records(self, mock_db):
        r1 = MagicMock()
        r1.content_id = 10
        r2 = MagicMock()
        r2.content_id = 20
        mock_db.query.return_value.filter.return_value.all.return_value = [r1, r2]
        result = get_read_records(mock_db, [10, 20, 30], 1)
        assert result == {10: True, 20: True}


class TestFormatContent:
    def test_format(self):
        content = MagicMock()
        content.id = 1
        content.content_type = "NEWS"
        content.title = "Test"
        content.content = "Body"
        content.summary = "Sum"
        content.images = [{"url": "img.jpg", "name": "test"}]
        content.videos = None
        content.attachments = None
        content.is_published = True
        content.publish_date = date(2024, 1, 1)
        content.expire_date = None
        content.priority = 1
        content.display_order = 1
        content.view_count = 10
        content.related_project_id = None
        content.related_department_id = None
        content.published_by = 1
        content.published_by_name = "Admin"
        content.created_by = 1
        content.created_at = datetime(2024, 1, 1)
        content.updated_at = datetime(2024, 1, 1)

        result = format_content(content, {1: True})
        assert result.title == "Test"
        assert result.is_read is True


class TestGetPersonalGoals:
    def test_disabled(self, mock_db):
        config = {"PERSONAL_GOAL": {"enabled": False}}
        result = get_personal_goals(mock_db, 1, date(2024, 6, 15), config)
        assert result == []

    def test_returns_goals(self, mock_db):
        goal = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.side_effect = [[goal], []]
        config = {"PERSONAL_GOAL": {"enabled": True, "max_count": 5}}
        result = get_personal_goals(mock_db, 1, date(2024, 6, 15), config)
        assert len(result) == 1

    def test_no_config_uses_default(self, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = get_personal_goals(mock_db, 1, date(2024, 1, 15), {})
        assert result == []


class TestFormatGoal:
    def test_format(self):
        goal = MagicMock()
        goal.id = 1
        goal.user_id = 1
        goal.goal_type = "MONTHLY"
        goal.period = "2024-01"
        goal.title = "Goal"
        goal.description = "Desc"
        goal.target_value = "100"
        goal.current_value = "50"
        goal.unit = "%"
        goal.progress = 50
        goal.status = "IN_PROGRESS"
        goal.start_date = date(2024, 1, 1)
        goal.end_date = date(2024, 1, 31)
        goal.completed_date = None
        goal.notes = None
        goal.created_by = 1
        goal.created_at = datetime(2024, 1, 1)
        goal.updated_at = datetime(2024, 1, 1)
        result = format_goal(goal)
        assert result.title == "Goal"


class TestGetNotifications:
    def test_disabled(self, mock_db):
        config = {"NOTIFICATION": {"enabled": False}}
        result = get_notifications(mock_db, 1, config)
        assert result == []

    def test_returns_notifications(self, mock_db):
        notif = MagicMock()
        notif.id = 1
        notif.title = "Alert"
        notif.content = "Body"
        notif.notification_type = "SYSTEM"
        notif.priority = "HIGH"
        notif.created_at = datetime(2024, 1, 1)
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [notif]
        result = get_notifications(mock_db, 1, {"NOTIFICATION": {"enabled": True, "max_count": 10}})
        assert len(result) == 1
        assert result[0]["title"] == "Alert"

    def test_empty_config(self, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        result = get_notifications(mock_db, 1, {})
        assert result == []
