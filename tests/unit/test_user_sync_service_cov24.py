# -*- coding: utf-8 -*-
"""第二十四批 - user_sync_service 单元测试"""

import pytest
from unittest.mock import MagicMock, patch

pytest.importorskip("app.services.user_sync_service")

from app.services.user_sync_service import UserSyncService


class TestUserSyncServiceClass:
    def test_default_position_role_mapping_exists(self):
        mapping = UserSyncService.DEFAULT_POSITION_ROLE_MAPPING
        assert isinstance(mapping, dict)
        assert len(mapping) > 0

    def test_project_manager_in_mapping(self):
        assert UserSyncService.DEFAULT_POSITION_ROLE_MAPPING.get("项目经理") == "pm"

    def test_pmc_in_mapping(self):
        assert "PMC" in UserSyncService.DEFAULT_POSITION_ROLE_MAPPING

    def test_engineering_roles_in_mapping(self):
        mapping = UserSyncService.DEFAULT_POSITION_ROLE_MAPPING
        assert "机械工程师" in mapping
        assert "电气工程师" in mapping
        assert "软件工程师" in mapping

    def test_sales_roles_in_mapping(self):
        mapping = UserSyncService.DEFAULT_POSITION_ROLE_MAPPING
        assert "销售工程师" in mapping
        assert "销售经理" in mapping

    def test_management_roles_in_mapping(self):
        mapping = UserSyncService.DEFAULT_POSITION_ROLE_MAPPING
        assert "总经理" in mapping
        assert mapping["总经理"] == "gm"

    def test_assembler_roles_exist(self):
        mapping = UserSyncService.DEFAULT_POSITION_ROLE_MAPPING
        assembler_keys = [k for k, v in mapping.items() if v == "assembler"]
        assert len(assembler_keys) >= 2

    def test_get_role_by_position_is_static(self):
        assert callable(getattr(UserSyncService, "get_role_by_position", None))
