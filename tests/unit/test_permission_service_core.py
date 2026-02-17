# -*- coding: utf-8 -*-
"""
app/services/permission_service.py 核心方法覆盖率测试（当前 12%）
专注于不需要 DB 的方法和可 mock DB 的方法
"""
import pytest
from unittest.mock import MagicMock, patch


class TestPermissionServiceCheckPermission:
    """测试 check_permission 系列（超级管理员快速路径）"""

    @pytest.fixture
    def mock_db(self):
        return MagicMock()

    def test_superuser_has_all_permissions(self, mock_db):
        from app.services.permission_service import PermissionService

        user = MagicMock()
        user.is_superuser = True

        result = PermissionService.check_permission(
            db=mock_db,
            user_id=1,
            permission_code="project:delete",
            user=user
        )
        assert result is True

    def test_superuser_check_any_permission(self, mock_db):
        from app.services.permission_service import PermissionService

        user = MagicMock()
        user.is_superuser = True

        result = PermissionService.check_any_permission(
            db=mock_db,
            user_id=1,
            permission_codes=["a", "b", "c"],
            user=user
        )
        assert result is True

    def test_superuser_check_all_permissions(self, mock_db):
        from app.services.permission_service import PermissionService

        user = MagicMock()
        user.is_superuser = True

        result = PermissionService.check_all_permissions(
            db=mock_db,
            user_id=1,
            permission_codes=["a", "b", "c"],
            user=user
        )
        assert result is True

    def test_regular_user_check_permission_denied(self, mock_db):
        from app.services.permission_service import PermissionService

        user = MagicMock()
        user.is_superuser = False
        user.tenant_id = 1

        with patch.object(
            PermissionService, "get_user_permissions", return_value=set()
        ):
            result = PermissionService.check_permission(
                db=mock_db,
                user_id=10,
                permission_code="project:delete",
                user=user
            )
            assert result is False

    def test_regular_user_check_permission_granted(self, mock_db):
        from app.services.permission_service import PermissionService

        user = MagicMock()
        user.is_superuser = False
        user.tenant_id = 1

        with patch.object(
            PermissionService,
            "get_user_permissions",
            return_value={"project:read", "project:edit"}
        ):
            result = PermissionService.check_permission(
                db=mock_db,
                user_id=10,
                permission_code="project:read",
                user=user
            )
            assert result is True

    def test_check_any_permission_has_one(self, mock_db):
        from app.services.permission_service import PermissionService

        user = MagicMock()
        user.is_superuser = False
        user.tenant_id = 1

        with patch.object(
            PermissionService,
            "get_user_permissions",
            return_value={"project:read"}
        ):
            result = PermissionService.check_any_permission(
                db=mock_db,
                user_id=10,
                permission_codes=["project:read", "project:delete"],
                user=user
            )
            assert result is True

    def test_check_any_permission_has_none(self, mock_db):
        from app.services.permission_service import PermissionService

        user = MagicMock()
        user.is_superuser = False
        user.tenant_id = 1

        with patch.object(
            PermissionService,
            "get_user_permissions",
            return_value=set()
        ):
            result = PermissionService.check_any_permission(
                db=mock_db,
                user_id=10,
                permission_codes=["project:read", "project:delete"],
                user=user
            )
            assert result is False

    def test_check_all_permissions_has_all(self, mock_db):
        from app.services.permission_service import PermissionService

        user = MagicMock()
        user.is_superuser = False
        user.tenant_id = 1

        with patch.object(
            PermissionService,
            "get_user_permissions",
            return_value={"project:read", "project:edit", "project:delete"}
        ):
            result = PermissionService.check_all_permissions(
                db=mock_db,
                user_id=10,
                permission_codes=["project:read", "project:edit"],
                user=user
            )
            assert result is True

    def test_check_all_permissions_missing_some(self, mock_db):
        from app.services.permission_service import PermissionService

        user = MagicMock()
        user.is_superuser = False
        user.tenant_id = 1

        with patch.object(
            PermissionService,
            "get_user_permissions",
            return_value={"project:read"}
        ):
            result = PermissionService.check_all_permissions(
                db=mock_db,
                user_id=10,
                permission_codes=["project:read", "project:delete"],
                user=user
            )
            assert result is False


class TestCheckPermissionCompat:
    """测试兼容性函数"""

    def test_compat_superuser(self):
        from app.services.permission_service import check_permission_compat

        user = MagicMock()
        user.is_superuser = True
        db = MagicMock()

        result = check_permission_compat(user, "any:permission", db)
        assert result is True

    def test_compat_regular_user_denied(self):
        from app.services.permission_service import check_permission_compat
        from app.services.permission_service import PermissionService

        user = MagicMock()
        user.is_superuser = False
        user.id = 10
        user.tenant_id = 1
        db = MagicMock()

        with patch.object(PermissionService, "check_permission", return_value=False):
            result = check_permission_compat(user, "project:delete", db)
            assert result is False


class TestHasModulePermission:
    """测试模块权限检查"""

    def test_superuser_has_module(self):
        from app.services.permission_service import has_module_permission

        user = MagicMock()
        user.is_superuser = True
        db = MagicMock()

        result = has_module_permission(user, "sales", db)
        assert result is True

    def test_regular_user_no_module_permissions(self):
        from app.services.permission_service import has_module_permission
        from app.services.permission_service import PermissionService

        user = MagicMock()
        user.is_superuser = False
        user.id = 10
        user.tenant_id = 1
        db = MagicMock()

        with patch.object(PermissionService, "get_user_permissions", return_value=set()):
            result = has_module_permission(user, "sales", db)
            assert result is False
