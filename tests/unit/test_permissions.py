# -*- coding: utf-8 -*-
"""
权限模块单元测试

测试新的权限系统：
- PermissionService（数据库驱动的权限检查）
- app/core/auth.py 中的认证和权限函数
- app/core/permissions/timesheet.py 中的工时权限函数
- app/core/sales_permissions.py 中的销售权限函数
"""

import pytest
from unittest.mock import MagicMock, patch


class MockUser:
    """模拟用户对象"""

    def __init__(
        self,
        is_superuser: bool = False,
        roles: list = None,
        department: str = None,
        department_id: int = None,
        user_id: int = 1,
        username: str = "test_user",
        tenant_id: int = None,
    ):
        self.is_superuser = is_superuser
        self.id = user_id
        self.username = username
        self.department = department
        self.department_id = department_id
        self.roles = roles or []
        self.tenant_id = tenant_id


class MockUserRole:
    """模拟用户角色关联对象"""

    def __init__(self, role_code: str, role_name: str = None):
        self.role = MagicMock()
        self.role.role_code = role_code
        self.role.role_name = role_name or role_code
        self.role.is_active = True


# ============================================================================
# PermissionService 测试
# ============================================================================

@pytest.mark.unit
class TestPermissionService:
    """权限服务测试"""

    def test_check_permission_superuser(self):
        """测试超级用户始终有权限"""
        from app.services.permission_service import PermissionService

        db = MagicMock()
        user = MockUser(is_superuser=True,
        password_hash="test_hash_123"
    )

        result = PermissionService.check_permission(
            db, user.id, "any:permission", user=user
        )
        assert result is True

    def test_check_permission_normal_user(self):
        """测试普通用户权限检查"""
        from app.services.permission_service import PermissionService

        db = MagicMock()
        user = MockUser(is_superuser=False,
        password_hash="test_hash_123"
    )

        with patch.object(
            PermissionService, 'get_user_permissions', return_value=["project:read"]
        ):
            result = PermissionService.check_permission(
                db, user.id, "project:read", user=user
            )
            assert result is True

            result = PermissionService.check_permission(
                db, user.id, "project:write", user=user
            )
            assert result is False

    def test_check_any_permission_superuser(self):
        """测试超级用户检查任一权限"""
        from app.services.permission_service import PermissionService

        db = MagicMock()
        user = MockUser(is_superuser=True,
        password_hash="test_hash_123"
    )

        result = PermissionService.check_any_permission(
            db, user.id, ["perm1", "perm2"], user=user
        )
        assert result is True

    def test_check_any_permission_normal_user(self):
        """测试普通用户检查任一权限"""
        from app.services.permission_service import PermissionService

        db = MagicMock()
        user = MockUser(is_superuser=False,
        password_hash="test_hash_123"
    )

        with patch.object(
            PermissionService, 'get_user_permissions', return_value=["perm2", "perm3"]
        ):
            result = PermissionService.check_any_permission(
                db, user.id, ["perm1", "perm2"], user=user
            )
            assert result is True

            result = PermissionService.check_any_permission(
                db, user.id, ["perm4", "perm5"], user=user
            )
            assert result is False

    def test_check_all_permissions_superuser(self):
        """测试超级用户检查所有权限"""
        from app.services.permission_service import PermissionService

        db = MagicMock()
        user = MockUser(is_superuser=True,
        password_hash="test_hash_123"
    )

        result = PermissionService.check_all_permissions(
            db, user.id, ["perm1", "perm2"], user=user
        )
        assert result is True

    def test_check_all_permissions_normal_user(self):
        """测试普通用户检查所有权限"""
        from app.services.permission_service import PermissionService

        db = MagicMock()
        user = MockUser(is_superuser=False,
        password_hash="test_hash_123"
    )

        with patch.object(
            PermissionService, 'get_user_permissions', return_value=["perm1", "perm2", "perm3"]
        ):
            result = PermissionService.check_all_permissions(
                db, user.id, ["perm1", "perm2"], user=user
            )
            assert result is True

            result = PermissionService.check_all_permissions(
                db, user.id, ["perm1", "perm4"], user=user
            )
            assert result is False

    def test_has_module_permission(self):
        """测试模块权限检查兼容函数"""
        from app.services.permission_service import has_module_permission

        db = MagicMock()
        user = MockUser(is_superuser=True,
        password_hash="test_hash_123"
    )

        result = has_module_permission(user, "finance", db)
        assert result is True


# ============================================================================
# Timesheet 权限测试（保留的业务逻辑函数）
# ============================================================================

@pytest.mark.unit
class TestTimesheetPermissions:
    """工时审批权限测试"""

    def test_has_timesheet_approval_access_superuser(self):
        """测试超级用户有工时审批权限"""
        from app.core.permissions.timesheet import has_timesheet_approval_access

        user = MockUser(is_superuser=True,
        password_hash="test_hash_123"
    )
        db = MagicMock()
        assert has_timesheet_approval_access(user, db) is True

    def test_has_timesheet_approval_access_with_managed_projects(self):
        """测试管理项目的用户有工时审批权限"""
        from app.core.permissions.timesheet import has_timesheet_approval_access

        user = MockUser(user_id=100,
        password_hash="test_hash_123"
    )
        db = MagicMock()

        # Mock: 用户管理一个项目
        mock_project = MagicMock()
        mock_project.id = 1
        db.query.return_value.filter.return_value.all.return_value = [mock_project]

        with patch(
            "app.core.permissions.timesheet.get_user_manageable_dimensions",
            return_value={
                "is_admin": False,
                "project_ids": {1},
                "rd_project_ids": set(),
                "department_ids": set(),
                "subordinate_user_ids": set(),
            }
        ):
            assert has_timesheet_approval_access(user, db) is True

    def test_has_timesheet_approval_access_with_subordinates(self):
        """测试有下属的用户有工时审批权限"""
        from app.core.permissions.timesheet import has_timesheet_approval_access

        user = MockUser(user_id=100,
        password_hash="test_hash_123"
    )
        db = MagicMock()

        with patch(
            "app.core.permissions.timesheet.get_user_manageable_dimensions",
            return_value={
                "is_admin": False,
                "project_ids": set(),
                "rd_project_ids": set(),
                "department_ids": set(),
                "subordinate_user_ids": {200, 201},
            }
        ):
            assert has_timesheet_approval_access(user, db) is True

    def test_has_timesheet_approval_access_hr_admin(self):
        """测试人事管理员有工时审批权限"""
        from app.core.permissions.timesheet import has_timesheet_approval_access

        user = MockUser(roles=[MockUserRole("hr_admin", "人事管理员")],
        password_hash="test_hash_123"
    )
        db = MagicMock()
        assert has_timesheet_approval_access(user, db) is True

    def test_has_timesheet_approval_access_no_permission(self):
        """测试普通用户无工时审批权限"""
        from app.core.permissions.timesheet import has_timesheet_approval_access

        user = MockUser(roles=[MockUserRole("engineer", "工程师")],
        password_hash="test_hash_123"
    )
        db = MagicMock()

        with patch(
            "app.core.permissions.timesheet.get_user_manageable_dimensions",
            return_value={
                "is_admin": False,
                "project_ids": set(),
                "rd_project_ids": set(),
                "department_ids": set(),
                "subordinate_user_ids": set(),
            }
        ):
            assert has_timesheet_approval_access(user, db) is False

    def test_check_timesheet_approval_permission_superuser(self):
        """测试超级用户审批权限"""
        from app.core.permissions.timesheet import check_timesheet_approval_permission

        user = MockUser(is_superuser=True,
        password_hash="test_hash_123"
    )
        db = MagicMock()
        timesheet = MagicMock()
        timesheet.user_id = 2
        timesheet.project_id = 1
        timesheet.rd_project_id = None
        timesheet.department_id = None
        # 正确的参数顺序: db, timesheet, current_user
        assert check_timesheet_approval_permission(db, timesheet, user) is True

    def test_require_timesheet_approval_access_returns_callable(self):
        """测试 require_timesheet_approval_access 返回可调用对象"""
        from app.core.permissions.timesheet import require_timesheet_approval_access

        checker = require_timesheet_approval_access()
        assert callable(checker)


# ============================================================================
# Auth 模块测试
# ============================================================================

@pytest.mark.unit
class TestPasswordHashing:
    """测试密码加密和验证"""

    def test_verify_password_correct(self):
        """测试正确密码验证"""
        from app.core.auth import get_password_hash, verify_password

        password = "test_password_123"
        hashed = get_password_hash(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """测试错误密码验证"""
        from app.core.auth import get_password_hash, verify_password

        password = "test_password_123"
        hashed = get_password_hash(password)

        assert verify_password("wrong_password", hashed) is False

    def test_password_hash_is_different(self):
        """测试相同密码生成不同哈希（使用盐）"""
        from app.core.auth import get_password_hash

        password = "test_password_123"
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # 两次哈希应该不同（因为随机盐）
        assert hash1 != hash2

    def test_empty_password(self):
        """测试空密码可以哈希"""
        from app.core.auth import get_password_hash, verify_password

        password = ""
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_unicode_password(self):
        """测试Unicode密码"""
        from app.core.auth import get_password_hash, verify_password

        password = "密码测试123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True


@pytest.mark.unit
class TestTokenCreation:
    """测试 Token 创建"""

    def test_create_access_token_default_expiry(self):
        """测试使用默认过期时间创建 Token"""
        from app.core.auth import create_access_token

        token = create_access_token(data={"sub": "123"})

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT token 应该足够长

    def test_create_access_token_custom_expiry(self):
        """测试使用自定义过期时间创建 Token"""
        from datetime import timedelta

        from app.core.auth import create_access_token

        token = create_access_token(
            data={"sub": "456"}, expires_delta=timedelta(hours=2)
        )

        assert token is not None
        assert isinstance(token, str)

    def test_token_contains_jti(self):
        """测试 Token 包含 JTI（JWT ID）"""
        from jose import jwt

        from app.core.auth import create_access_token
        from app.core.config import settings

        token = create_access_token(data={"sub": "789"})

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )

        assert "jti" in payload
        assert len(payload["jti"]) == 32  # hex(16 bytes) = 32 chars

    def test_token_contains_exp(self):
        """测试 Token 包含过期时间"""
        from jose import jwt

        from app.core.auth import create_access_token
        from app.core.config import settings

        token = create_access_token(data={"sub": "test"})

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )

        assert "exp" in payload
        assert "iat" in payload


@pytest.mark.unit
class TestTokenRevocation:
    """测试 Token 撤销"""

    def test_revoke_token_none(self):
        """测试撤销空 Token 不抛出异常"""
        from app.core.auth import revoke_token

        # 不应该抛出异常
        revoke_token(None)

    def test_is_token_revoked_none(self):
        """测试检查空 Token 返回 False"""
        from app.core.auth import is_token_revoked

        assert is_token_revoked(None) is False

    def test_revoke_and_check_token_memory_fallback(self):
        """测试撤销并检查 Token（内存降级模式）"""
        from app.core.auth import (
            create_access_token,
            is_token_revoked,
            revoke_token,
        )

        # 创建 Token
        token = create_access_token(data={"sub": "test_user"})

        # 验证未撤销
        assert is_token_revoked(token) is False

        # 撤销 Token（使用内存模式）
        with patch("app.core.auth.get_redis_client") as mock_redis:
            mock_redis.return_value = None  # 模拟 Redis 不可用
            revoke_token(token)
            assert is_token_revoked(token) is True


@pytest.mark.unit
class TestCheckPermission:
    """测试权限检查函数"""

    def test_superuser_always_has_permission(self):
        """测试超级管理员始终有权限"""
        from app.core.auth import check_permission

        user = MockUser(is_superuser=True, username="admin",
        password_hash="test_hash_123"
    )
        result = check_permission(user, "any:permission")
        assert result is True

    def test_user_without_roles(self):
        """测试没有角色的用户无权限"""
        from app.core.auth import check_permission

        user = MockUser(is_superuser=False, roles=[], username="test_user",
        password_hash="test_hash_123"
    )

        # Mock 缓存服务返回空权限列表
        # 注意：import 在函数内部，需要 patch 源模块
        with patch("app.services.permission_cache_service.get_permission_cache_service") as mock_cache:
            mock_cache.return_value.get_user_permissions.return_value = []
            result = check_permission(user, "test:permission")
            assert result is False

    def test_require_permission_returns_callable(self):
        """测试 require_permission 返回可调用对象"""
        from app.core.auth import require_permission

        checker = require_permission("test:permission")
        assert callable(checker)


# ============================================================================
# Sales Permissions 测试
# ============================================================================

@pytest.mark.unit
class TestSalesDataScope:
    """测试销售数据范围"""

    def test_superuser_gets_all_scope(self):
        """测试超级管理员获取ALL范围"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(is_superuser=True,
        password_hash="test_hash_123"
    )
        db = MagicMock()

        scope = get_sales_data_scope(user, db)
        assert scope == "ALL"

    def test_sales_gets_own_scope(self):
        """测试销售获取OWN范围"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(roles=[MockUserRole("SALES", "销售")],
        password_hash="test_hash_123"
    )
        db = MagicMock()

        scope = get_sales_data_scope(user, db)
        assert scope == "OWN"

    def test_presales_gets_own_scope(self):
        """测试售前获取OWN范围"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(roles=[MockUserRole("PRESALES", "售前")],
        password_hash="test_hash_123"
    )
        db = MagicMock()

        scope = get_sales_data_scope(user, db)
        assert scope == "OWN"


@pytest.mark.unit
class TestSalesCreatePermission:
    """测试销售数据创建权限"""

    def test_superuser_can_create(self):
        """测试超级管理员可以创建"""
        from app.core.sales_permissions import check_sales_create_permission

        user = MockUser(is_superuser=True,
        password_hash="test_hash_123"
    )
        db = MagicMock()

        assert check_sales_create_permission(user, db) is True

    def test_sales_can_create(self):
        """测试销售可以创建"""
        from app.core.sales_permissions import check_sales_create_permission

        user = MockUser(roles=[MockUserRole("SALES", "销售")],
        password_hash="test_hash_123"
    )
        db = MagicMock()

        assert check_sales_create_permission(user, db) is True


@pytest.mark.unit
class TestSalesEditPermission:
    """测试销售数据编辑权限"""

    def test_superuser_can_edit_all(self):
        """测试超级管理员可以编辑所有"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(is_superuser=True,
        password_hash="test_hash_123"
    )
        db = MagicMock()

        assert check_sales_edit_permission(user, db, 999, 888) is True

    def test_sales_can_edit_own_created(self):
        """测试销售可以编辑自己创建的"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(
            user_id=100,
            roles=[MockUserRole("SALES", "销售")],
        password_hash="test_hash_123"
    )
        db = MagicMock()

        # 自己创建的
        assert check_sales_edit_permission(user, db, 100, None) is True

    def test_sales_can_edit_own_responsible(self):
        """测试销售可以编辑自己负责的"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(
            user_id=100,
            roles=[MockUserRole("SALES", "销售")],
        password_hash="test_hash_123"
    )
        db = MagicMock()

        # 自己负责的
        assert check_sales_edit_permission(user, db, None, 100) is True

    def test_sales_cannot_edit_others(self):
        """测试销售不能编辑别人的"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(
            user_id=100,
            roles=[MockUserRole("SALES", "销售")],
        password_hash="test_hash_123"
    )
        db = MagicMock()

        # 别人的
        assert check_sales_edit_permission(user, db, 999, 888) is False


@pytest.mark.unit
class TestSalesDeletePermission:
    """测试销售数据删除权限"""

    def test_superuser_can_delete(self):
        """测试超级管理员可以删除"""
        from app.core.sales_permissions import check_sales_delete_permission

        user = MockUser(is_superuser=True,
        password_hash="test_hash_123"
    )
        db = MagicMock()

        assert check_sales_delete_permission(user, db, 999) is True

    def test_sales_can_delete_own(self):
        """测试销售只能删除自己创建的"""
        from app.core.sales_permissions import check_sales_delete_permission

        user = MockUser(
            user_id=100,
            roles=[MockUserRole("SALES", "销售")],
        password_hash="test_hash_123"
    )
        db = MagicMock()

        # 自己创建的可以删除
        assert check_sales_delete_permission(user, db, 100) is True

        # 别人创建的不能删除
        assert check_sales_delete_permission(user, db, 999) is False

    def test_user_can_delete_own_created(self):
        """测试用户可以删除自己创建的数据"""
        from app.core.sales_permissions import check_sales_delete_permission

        user = MockUser(
            user_id=1,
            roles=[MockUserRole("FINANCE", "财务")],
        password_hash="test_hash_123"
    )
        db = MagicMock()

        # 可以删除自己创建的
        assert check_sales_delete_permission(user, db, 1) is True


@pytest.mark.unit
class TestSalesAssessmentAccess:
    """测试销售技术评估权限"""

    def test_superuser_has_assessment_access(self):
        """测试超级管理员有技术评估权限"""
        from app.core.sales_permissions import has_sales_assessment_access

        user = MockUser(is_superuser=True,
        password_hash="test_hash_123"
    )
        assert has_sales_assessment_access(user) is True

    def test_sales_engineer_has_access(self):
        """测试销售工程师有技术评估权限"""
        from app.core.sales_permissions import has_sales_assessment_access

        user = MockUser(roles=[MockUserRole("sales_engineer", "销售工程师")],
        password_hash="test_hash_123"
    )
        assert has_sales_assessment_access(user) is True

    def test_presales_engineer_has_access(self):
        """测试售前工程师有技术评估权限"""
        from app.core.sales_permissions import has_sales_assessment_access

        user = MockUser(roles=[MockUserRole("presales_engineer", "售前工程师")],
        password_hash="test_hash_123"
    )
        assert has_sales_assessment_access(user) is True


@pytest.mark.unit
class TestSalesApprovalAccess:
    """测试销售审批权限"""

    def test_superuser_has_approval_access(self):
        """测试超级管理员有审批权限"""
        from app.core.sales_permissions import has_sales_approval_access

        user = MockUser(is_superuser=True,
        password_hash="test_hash_123"
    )
        db = MagicMock()

        assert has_sales_approval_access(user, db) is True

    def test_sales_no_approval_access(self):
        """测试普通销售无审批权限"""
        from app.core.sales_permissions import has_sales_approval_access

        user = MockUser(roles=[MockUserRole("sales", "销售")],
        password_hash="test_hash_123"
    )
        db = MagicMock()

        assert has_sales_approval_access(user, db) is False


@pytest.mark.unit
class TestCheckSalesApprovalPermission:
    """测试销售审批权限检查"""

    def test_superuser_can_approve_all(self):
        """测试超级管理员可以审批所有"""
        from app.core.sales_permissions import check_sales_approval_permission

        user = MockUser(is_superuser=True,
        password_hash="test_hash_123"
    )
        db = MagicMock()

        approval = MagicMock()
        approval.approval_level = 1
        approval.approval_role = ""

        assert check_sales_approval_permission(user, approval, db) is True

    def test_no_approval_role_returns_false(self):
        """测试无审批角色返回False"""
        from app.core.sales_permissions import check_sales_approval_permission

        user = MockUser(roles=[MockUserRole("sales", "销售")],
        password_hash="test_hash_123"
    )
        db = MagicMock()

        approval = MagicMock()
        approval.approval_level = 1
        approval.approval_role = ""

        assert check_sales_approval_permission(user, approval, db) is False


@pytest.mark.unit
class TestSalesPermissionDependencies:
    """测试销售权限依赖函数"""

    def test_require_sales_create_permission_returns_callable(self):
        """测试 require_sales_create_permission 返回可调用对象"""
        from app.core.sales_permissions import require_sales_create_permission

        checker = require_sales_create_permission()
        assert callable(checker)

    def test_require_sales_edit_permission_returns_callable(self):
        """测试 require_sales_edit_permission 返回可调用对象"""
        from app.core.sales_permissions import require_sales_edit_permission

        checker = require_sales_edit_permission()
        assert callable(checker)

    def test_require_sales_delete_permission_returns_callable(self):
        """测试 require_sales_delete_permission 返回可调用对象"""
        from app.core.sales_permissions import require_sales_delete_permission

        checker = require_sales_delete_permission()
        assert callable(checker)

    def test_require_sales_assessment_access_returns_callable(self):
        """测试 require_sales_assessment_access 返回可调用对象"""
        from app.core.sales_permissions import require_sales_assessment_access

        checker = require_sales_assessment_access()
        assert callable(checker)

    def test_require_sales_approval_permission_returns_callable(self):
        """测试 require_sales_approval_permission 返回可调用对象"""
        from app.core.sales_permissions import require_sales_approval_permission

        checker = require_sales_approval_permission()
        assert callable(checker)


@pytest.mark.unit
class TestSalesPermissionsExport:
    """测试销售权限模块导出"""

    def test_all_sales_permissions_exported(self):
        """测试所有销售权限函数都已导出"""
        from app.core.sales_permissions import (
            check_sales_approval_permission,
            check_sales_create_permission,
            check_sales_delete_permission,
            check_sales_edit_permission,
            filter_sales_data_by_scope,
            filter_sales_finance_data_by_scope,
            get_sales_data_scope,
            has_sales_approval_access,
            has_sales_assessment_access,
            require_sales_approval_permission,
            require_sales_assessment_access,
            require_sales_create_permission,
            require_sales_delete_permission,
            require_sales_edit_permission,
        )

        assert callable(get_sales_data_scope)
        assert callable(filter_sales_data_by_scope)
        assert callable(filter_sales_finance_data_by_scope)
        assert callable(check_sales_create_permission)
        assert callable(check_sales_edit_permission)
        assert callable(check_sales_delete_permission)
        assert callable(require_sales_create_permission)
        assert callable(require_sales_edit_permission)
        assert callable(require_sales_delete_permission)
        assert callable(has_sales_assessment_access)
        assert callable(require_sales_assessment_access)
        assert callable(has_sales_approval_access)
        assert callable(check_sales_approval_permission)
        assert callable(require_sales_approval_permission)


@pytest.mark.unit
class TestPermissionsModuleExport:
    """权限模块导出测试"""

    def test_timesheet_permissions_exported(self):
        """测试工时权限函数已导出"""
        from app.core.permissions import (
            apply_timesheet_access_filter,
            check_timesheet_approval_permission,
            get_user_manageable_dimensions,
            has_timesheet_approval_access,
            is_timesheet_admin,
            require_timesheet_approval_access,
        )

        assert callable(is_timesheet_admin)
        assert callable(get_user_manageable_dimensions)
        assert callable(apply_timesheet_access_filter)
        assert callable(check_timesheet_approval_permission)
        assert callable(has_timesheet_approval_access)
        assert callable(require_timesheet_approval_access)


@pytest.mark.unit
class TestPermissionsIntegration:
    """权限模块集成测试"""

    def test_superuser_bypasses_all_permissions(self):
        """测试超级管理员可以绕过所有权限检查"""
        from app.core.permissions.timesheet import has_timesheet_approval_access
        from app.core.sales_permissions import (
            check_sales_create_permission,
            check_sales_delete_permission,
            check_sales_edit_permission,
            get_sales_data_scope,
            has_sales_approval_access,
            has_sales_assessment_access,
        )
        from app.services.permission_service import PermissionService

        user = MockUser(is_superuser=True,
        password_hash="test_hash_123"
    )
        db = MagicMock()

        # 所有权限检查都应该返回 True 或 ALL
        assert has_timesheet_approval_access(user, db) is True
        assert has_sales_assessment_access(user) is True
        assert has_sales_approval_access(user, db) is True
        assert check_sales_create_permission(user, db) is True
        assert check_sales_edit_permission(user, db) is True
        assert check_sales_delete_permission(user, db) is True
        assert get_sales_data_scope(user, db) == "ALL"
        assert PermissionService.check_permission(db, user.id, "any:perm", user) is True

    def test_empty_roles_no_sales_permissions(self):
        """测试空角色无销售权限"""
        from app.core.permissions.timesheet import has_timesheet_approval_access
        from app.core.sales_permissions import (
            check_sales_create_permission,
            get_sales_data_scope,
            has_sales_assessment_access,
        )

        user = MockUser(is_superuser=False, roles=[],
        password_hash="test_hash_123"
    )
        db = MagicMock()

        # Mock get_user_manageable_dimensions 返回空
        with patch(
            "app.core.permissions.timesheet.get_user_manageable_dimensions",
            return_value={
                "is_admin": False,
                "project_ids": set(),
                "rd_project_ids": set(),
                "department_ids": set(),
                "subordinate_user_ids": set(),
            }
        ):
            # 无管理维度的用户没有工时审批权限
            assert has_timesheet_approval_access(user, db) is False

        # 无角色用户没有销售评估访问权限（需要特定销售角色）
        assert has_sales_assessment_access(user) is False

        # 注意：无角色用户默认有 OWN 范围，可以创建自己的数据
        # 这是符合设计的行为：OWN 范围用户可以创建自己的销售记录
        assert get_sales_data_scope(user, db) == "OWN"
        # OWN 范围允许创建数据，所以 check_sales_create_permission 返回 True
        assert check_sales_create_permission(user, db) is True
