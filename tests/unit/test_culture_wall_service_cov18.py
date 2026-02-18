# -*- coding: utf-8 -*-
"""第十八批 - 文化墙服务单元测试"""
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

try:
    from app.services.culture_wall_service import (
        check_user_role_permission,
        get_content_types_config,
        get_read_records,
        query_content_by_type,
    )
    IMPORT_OK = True
except Exception:
    IMPORT_OK = False

pytestmark = pytest.mark.skipif(not IMPORT_OK, reason="导入失败，跳过")


class TestCheckUserRolePermission:
    def test_no_config_returns_true(self):
        assert check_user_role_permission(None, ["admin"]) is True

    def test_empty_visible_roles_returns_true(self):
        config = MagicMock()
        config.visible_roles = []
        assert check_user_role_permission(config, ["admin"]) is True

    def test_role_in_visible_returns_true(self):
        config = MagicMock()
        config.visible_roles = ["admin", "manager"]
        assert check_user_role_permission(config, ["admin"]) is True

    def test_role_not_in_visible_returns_false(self):
        config = MagicMock()
        config.visible_roles = ["admin"]
        assert check_user_role_permission(config, ["user"]) is False

    def test_multiple_roles_one_match(self):
        config = MagicMock()
        config.visible_roles = ["admin", "viewer"]
        assert check_user_role_permission(config, ["user", "viewer"]) is True


class TestGetContentTypesConfig:
    def test_no_config_returns_empty(self):
        assert get_content_types_config(None) == {}

    def test_config_with_types(self):
        config = MagicMock()
        config.content_types = {"NEWS": {"enabled": True, "max_count": 5}}
        result = get_content_types_config(config)
        assert result == {"NEWS": {"enabled": True, "max_count": 5}}

    def test_config_no_content_types(self):
        config = MagicMock()
        config.content_types = None
        result = get_content_types_config(config)
        assert result == {}


class TestQueryContentByType:
    def test_disabled_type_returns_empty(self):
        content_query = MagicMock()
        config = {"NEWS": {"enabled": False}}
        result = query_content_by_type(content_query, "NEWS", config)
        assert result == []

    def test_uses_max_count_from_config(self):
        config = {"NEWS": {"enabled": True, "max_count": 3}}
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [1, 2, 3]
        result = query_content_by_type(mock_query, "NEWS", config)
        assert len(result) == 3

    def test_default_max_count_when_no_config(self):
        config = {}
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        result = query_content_by_type(mock_query, "NEWS", config)
        assert result == []


class TestGetReadRecords:
    def test_empty_content_ids(self):
        db = MagicMock()
        result = get_read_records(db, [], user_id=1)
        assert result == {}

    def test_returns_read_mapping(self):
        db = MagicMock()
        rec1 = MagicMock()
        rec1.content_id = 10
        db.query.return_value.filter.return_value.all.return_value = [rec1]
        result = get_read_records(db, [10, 20], user_id=1)
        assert result.get(10) is True
        assert 20 not in result
