# -*- coding: utf-8 -*-
"""
权限模块单元测试

测试 app/core/permissions/ 中的权限检查功能
"""

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
    ):
        self.is_superuser = is_superuser
        self.id = user_id
        self.department = department
        self.department_id = department_id
        self.roles = roles or []


class MockUserRole:
    """模拟用户角色关联对象"""

    def __init__(self, role_code: str, role_name: str = None):
        self.role = MagicMock()
        self.role.role_code = role_code
        self.role.role_name = role_name or role_code
        self.role.is_active = True


class TestFinancePermissions:
    """财务权限测试"""

    def test_has_finance_access_superuser(self):
        """测试超级用户有财务权限"""
        from app.core.permissions.finance import has_finance_access

        user = MockUser(is_superuser=True)
        assert has_finance_access(user) is True

    def test_has_finance_access_finance_manager(self):
        """测试财务经理有财务权限"""
        from app.core.permissions.finance import has_finance_access

        user = MockUser(roles=[MockUserRole("finance_manager", "财务经理")])
        assert has_finance_access(user) is True

    def test_has_finance_access_accountant(self):
        """测试会计有财务权限"""
        from app.core.permissions.finance import has_finance_access

        user = MockUser(roles=[MockUserRole("accountant", "会计")])
        assert has_finance_access(user) is True

    def test_has_finance_access_sales_director(self):
        """测试销售总监有财务权限（查看回款）"""
        from app.core.permissions.finance import has_finance_access

        user = MockUser(roles=[MockUserRole("sales_director", "销售总监")])
        assert has_finance_access(user) is True

    def test_has_finance_access_pm(self):
        """测试项目经理有财务权限"""
        from app.core.permissions.finance import has_finance_access

        user = MockUser(roles=[MockUserRole("pm", "项目经理")])
        assert has_finance_access(user) is True

    def test_has_finance_access_no_permission(self):
        """测试普通用户无财务权限"""
        from app.core.permissions.finance import has_finance_access

        user = MockUser(roles=[MockUserRole("engineer", "工程师")])
        assert has_finance_access(user) is False

    def test_has_finance_access_chinese_role_name(self):
        """测试中文角色名称"""
        from app.core.permissions.finance import has_finance_access

        user = MockUser(roles=[MockUserRole("unknown_code", "财务人员")])
        assert has_finance_access(user) is True

    def test_require_finance_access_returns_callable(self):
        """测试require_finance_access返回可调用对象"""
        from app.core.permissions.finance import require_finance_access

        checker = require_finance_access()
        assert callable(checker)


class TestHrPermissions:
    """人力资源权限测试"""

    def test_has_hr_access_superuser(self):
        """测试超级用户有HR权限"""
        from app.core.permissions.hr import has_hr_access

        user = MockUser(is_superuser=True)
        assert has_hr_access(user) is True

    def test_has_hr_access_hr_manager(self):
        """测试人事经理有HR权限"""
        from app.core.permissions.hr import has_hr_access

        user = MockUser(roles=[MockUserRole("hr_manager", "人事经理")])
        assert has_hr_access(user) is True

    def test_has_hr_access_gm(self):
        """测试总经理有HR权限"""
        from app.core.permissions.hr import has_hr_access

        user = MockUser(roles=[MockUserRole("gm", "总经理")])
        assert has_hr_access(user) is True

    def test_has_hr_access_admin(self):
        """测试管理员有HR权限"""
        from app.core.permissions.hr import has_hr_access

        user = MockUser(roles=[MockUserRole("admin", "管理员")])
        assert has_hr_access(user) is True

    def test_has_hr_access_no_permission(self):
        """测试普通用户无HR权限"""
        from app.core.permissions.hr import has_hr_access

        user = MockUser(roles=[MockUserRole("engineer", "工程师")])
        assert has_hr_access(user) is False

    def test_require_hr_access_returns_callable(self):
        """测试require_hr_access返回可调用对象"""
        from app.core.permissions.hr import require_hr_access

        checker = require_hr_access()
        assert callable(checker)


class TestProcurementPermissions:
    """采购权限测试"""

    def test_has_procurement_access_superuser(self):
        """测试超级用户有采购权限"""
        from app.core.permissions.procurement import has_procurement_access

        user = MockUser(is_superuser=True)
        assert has_procurement_access(user) is True

    def test_has_procurement_access_procurement_engineer(self):
        """测试采购工程师有采购权限"""
        from app.core.permissions.procurement import has_procurement_access

        user = MockUser(roles=[MockUserRole("procurement_engineer")])
        assert has_procurement_access(user) is True

    def test_has_procurement_access_pmc(self):
        """测试PMC有采购权限"""
        from app.core.permissions.procurement import has_procurement_access

        user = MockUser(roles=[MockUserRole("pmc")])
        assert has_procurement_access(user) is True

    def test_has_procurement_access_pm(self):
        """测试项目经理有采购权限"""
        from app.core.permissions.procurement import has_procurement_access

        user = MockUser(roles=[MockUserRole("pm")])
        assert has_procurement_access(user) is True

    def test_has_procurement_access_no_permission(self):
        """测试普通用户无采购权限"""
        from app.core.permissions.procurement import has_procurement_access

        user = MockUser(roles=[MockUserRole("sales")])
        assert has_procurement_access(user) is False

    def test_has_shortage_report_access_superuser(self):
        """测试超级用户有缺料上报权限"""
        from app.core.permissions.procurement import has_shortage_report_access

        user = MockUser(is_superuser=True)
        assert has_shortage_report_access(user) is True

    def test_has_shortage_report_access_assembler(self):
        """测试装配技工有缺料上报权限"""
        from app.core.permissions.procurement import has_shortage_report_access

        user = MockUser(roles=[MockUserRole("assembler")])
        assert has_shortage_report_access(user) is True

    def test_has_shortage_report_access_warehouse(self):
        """测试仓库管理员有缺料上报权限"""
        from app.core.permissions.procurement import has_shortage_report_access

        user = MockUser(roles=[MockUserRole("warehouse")])
        assert has_shortage_report_access(user) is True

    def test_has_shortage_report_access_no_permission(self):
        """测试普通用户无缺料上报权限"""
        from app.core.permissions.procurement import has_shortage_report_access

        user = MockUser(roles=[MockUserRole("engineer")])
        assert has_shortage_report_access(user) is False


class TestProductionPermissions:
    """生产权限测试"""

    def test_has_production_access_superuser(self):
        """测试超级用户有生产权限"""
        from app.core.permissions.production import has_production_access

        user = MockUser(is_superuser=True)
        assert has_production_access(user) is True

    def test_has_production_access_production_manager(self):
        """测试生产部经理有生产权限"""
        from app.core.permissions.production import has_production_access

        user = MockUser(roles=[MockUserRole("production_manager")])
        assert has_production_access(user) is True

    def test_has_production_access_assembler(self):
        """测试装配技工有生产权限"""
        from app.core.permissions.production import has_production_access

        user = MockUser(roles=[MockUserRole("assembler")])
        assert has_production_access(user) is True

    def test_has_production_access_pmc(self):
        """测试PMC有生产权限"""
        from app.core.permissions.production import has_production_access

        user = MockUser(roles=[MockUserRole("pmc")])
        assert has_production_access(user) is True

    def test_has_production_access_no_permission(self):
        """测试普通用户无生产权限"""
        from app.core.permissions.production import has_production_access

        user = MockUser(roles=[MockUserRole("sales")])
        assert has_production_access(user) is False


class TestRdProjectPermissions:
    """研发项目权限测试"""

    def test_has_rd_project_access_superuser(self):
        """测试超级用户有研发项目权限"""
        from app.core.permissions.rd_project import has_rd_project_access

        user = MockUser(is_superuser=True)
        assert has_rd_project_access(user) is True

    def test_has_rd_project_access_rd_engineer(self):
        """测试研发工程师有研发项目权限"""
        from app.core.permissions.rd_project import has_rd_project_access

        user = MockUser(roles=[MockUserRole("rd_engineer", "研发工程师")])
        assert has_rd_project_access(user) is True

    def test_has_rd_project_access_me_engineer(self):
        """测试机械工程师有研发项目权限"""
        from app.core.permissions.rd_project import has_rd_project_access

        user = MockUser(roles=[MockUserRole("me_engineer", "机械工程师")])
        assert has_rd_project_access(user) is True

    def test_has_rd_project_access_ee_engineer(self):
        """测试电气工程师有研发项目权限"""
        from app.core.permissions.rd_project import has_rd_project_access

        user = MockUser(roles=[MockUserRole("ee_engineer", "电气工程师")])
        assert has_rd_project_access(user) is True

    def test_has_rd_project_access_pm(self):
        """测试项目经理有研发项目权限"""
        from app.core.permissions.rd_project import has_rd_project_access

        user = MockUser(roles=[MockUserRole("pm", "项目经理")])
        assert has_rd_project_access(user) is True

    def test_has_rd_project_access_no_permission(self):
        """测试销售无研发项目权限"""
        from app.core.permissions.rd_project import has_rd_project_access

        user = MockUser(roles=[MockUserRole("sales", "销售")])
        assert has_rd_project_access(user) is False

    def test_rd_project_roles_constant(self):
        """测试RD_PROJECT_ROLES常量"""
        from app.core.permissions.rd_project import RD_PROJECT_ROLES

        assert "admin" in RD_PROJECT_ROLES
        assert "rd_engineer" in RD_PROJECT_ROLES
        assert "pm" in RD_PROJECT_ROLES


class TestSchedulerPermissions:
    """调度器权限测试"""

    def test_has_scheduler_admin_access_superuser(self):
        """测试超级用户有调度器权限"""
        from app.core.permissions.scheduler import has_scheduler_admin_access

        user = MockUser(is_superuser=True)
        assert has_scheduler_admin_access(user) is True

    def test_has_scheduler_admin_access_admin(self):
        """测试管理员有调度器权限"""
        from app.core.permissions.scheduler import has_scheduler_admin_access

        user = MockUser(roles=[MockUserRole("admin", "管理员")])
        assert has_scheduler_admin_access(user) is True

    def test_has_scheduler_admin_access_gm(self):
        """测试总经理有调度器权限"""
        from app.core.permissions.scheduler import has_scheduler_admin_access

        user = MockUser(roles=[MockUserRole("gm", "总经理")])
        assert has_scheduler_admin_access(user) is True

    def test_has_scheduler_admin_access_no_permission(self):
        """测试普通用户无调度器权限"""
        from app.core.permissions.scheduler import has_scheduler_admin_access

        user = MockUser(roles=[MockUserRole("engineer", "工程师")])
        assert has_scheduler_admin_access(user) is False


class TestTimesheetPermissions:
    """工时审批权限测试"""

    def test_has_timesheet_approval_access_superuser(self):
        """测试超级用户有工时审批权限"""
        from app.core.permissions.timesheet import has_timesheet_approval_access

        user = MockUser(is_superuser=True)
        db = MagicMock()
        assert has_timesheet_approval_access(user, db) is True

    def test_has_timesheet_approval_access_pm(self):
        """测试项目经理有工时审批权限"""
        from app.core.permissions.timesheet import has_timesheet_approval_access

        user = MockUser(roles=[MockUserRole("pm", "项目经理")])
        db = MagicMock()
        assert has_timesheet_approval_access(user, db) is True

    def test_has_timesheet_approval_access_dept_manager(self):
        """测试部门经理有工时审批权限"""
        from app.core.permissions.timesheet import has_timesheet_approval_access

        user = MockUser(roles=[MockUserRole("dept_manager", "部门经理")])
        db = MagicMock()
        assert has_timesheet_approval_access(user, db) is True

    def test_has_timesheet_approval_access_hr_manager(self):
        """测试人事经理有工时审批权限"""
        from app.core.permissions.timesheet import has_timesheet_approval_access

        user = MockUser(roles=[MockUserRole("hr_manager", "人事经理")])
        db = MagicMock()
        assert has_timesheet_approval_access(user, db) is True

    def test_has_timesheet_approval_access_no_permission(self):
        """测试普通用户无工时审批权限"""
        from app.core.permissions.timesheet import has_timesheet_approval_access

        user = MockUser(roles=[MockUserRole("engineer", "工程师")])
        db = MagicMock()
        assert has_timesheet_approval_access(user, db) is False

    def test_check_timesheet_approval_permission_superuser(self):
        """测试超级用户批量审批权限"""
        from app.core.permissions.timesheet import check_timesheet_approval_permission

        user = MockUser(is_superuser=True)
        db = MagicMock()
        timesheets = []
        assert check_timesheet_approval_permission(user, db, timesheets) is True


class TestMachineDocumentPermissions:
    """机台文档权限测试"""

    def test_has_machine_document_permission_superuser(self):
        """测试超级用户有文档权限"""
        from app.core.permissions.machine import has_machine_document_permission

        user = MockUser(is_superuser=True)
        assert has_machine_document_permission(user, "CIRCUIT_DIAGRAM") is True

    def test_has_machine_document_permission_engineer_circuit(self):
        """测试工程师有电路图权限"""
        from app.core.permissions.machine import has_machine_document_permission

        user = MockUser(roles=[MockUserRole("ENGINEER", "工程师")])
        assert has_machine_document_permission(user, "CIRCUIT_DIAGRAM") is True

    def test_has_machine_document_permission_pm_plc(self):
        """测试项目经理有PLC程序权限"""
        from app.core.permissions.machine import has_machine_document_permission

        user = MockUser(roles=[MockUserRole("PM", "项目经理")])
        assert has_machine_document_permission(user, "PLC_PROGRAM") is True

    def test_has_machine_document_permission_pmc_bom(self):
        """测试PMC有BOM文档权限"""
        from app.core.permissions.machine import has_machine_document_permission

        user = MockUser(roles=[MockUserRole("PMC", "物料计划员")])
        assert has_machine_document_permission(user, "BOM_DOCUMENT") is True

    def test_has_machine_document_permission_qa_fat(self):
        """测试质量工程师有FAT文档权限"""
        from app.core.permissions.machine import has_machine_document_permission

        user = MockUser(roles=[MockUserRole("QA", "质量工程师")])
        assert has_machine_document_permission(user, "FAT_DOCUMENT") is True

    def test_has_machine_document_permission_qa_sat(self):
        """测试质量工程师有SAT文档权限"""
        from app.core.permissions.machine import has_machine_document_permission

        user = MockUser(roles=[MockUserRole("QA", "质量工程师")])
        assert has_machine_document_permission(user, "SAT_DOCUMENT") is True

    def test_has_machine_document_permission_engineer_other(self):
        """测试工程师有其他文档权限"""
        from app.core.permissions.machine import has_machine_document_permission

        user = MockUser(roles=[MockUserRole("ENGINEER", "工程师")])
        assert has_machine_document_permission(user, "OTHER") is True

    def test_has_machine_document_permission_no_permission(self):
        """测试无权限用户"""
        from app.core.permissions.machine import has_machine_document_permission

        user = MockUser(roles=[MockUserRole("SALES", "销售")])
        assert has_machine_document_permission(user, "CIRCUIT_DIAGRAM") is False

    def test_has_machine_document_upload_permission(self):
        """测试上传权限函数"""
        from app.core.permissions.machine import has_machine_document_upload_permission

        user = MockUser(is_superuser=True)
        assert has_machine_document_upload_permission(user, "CIRCUIT_DIAGRAM") is True

    def test_has_machine_document_permission_case_insensitive(self):
        """测试文档类型大小写不敏感"""
        from app.core.permissions.machine import has_machine_document_permission

        user = MockUser(is_superuser=True)
        assert has_machine_document_permission(user, "circuit_diagram") is True
        assert has_machine_document_permission(user, "CIRCUIT_DIAGRAM") is True


class TestProjectPermissions:
    """项目权限测试"""

    @patch("app.services.data_scope_service.DataScopeService.check_project_access")
    def test_check_project_access_delegates_to_service(self, mock_check):
        """测试check_project_access委托给DataScopeService"""
        from app.core.permissions.project import check_project_access

        mock_check.return_value = True

        user = MockUser()
        db = MagicMock()

        result = check_project_access(1, user, db)

        mock_check.assert_called_once_with(db, user, 1)
        assert result is True

    def test_require_project_access_returns_callable(self):
        """测试require_project_access返回可调用对象"""
        from app.core.permissions.project import require_project_access

        checker = require_project_access()
        assert callable(checker)


class TestPermissionsInit:
    """权限模块导出测试"""

    def test_all_permissions_exported(self):
        """测试所有权限函数都已导出"""
        from app.core.permissions import (
        RD_PROJECT_ROLES,
        check_project_access,
        check_timesheet_approval_permission,
        has_finance_access,
        has_hr_access,
        has_machine_document_permission,
        has_machine_document_upload_permission,
        has_procurement_access,
        has_production_access,
        has_rd_project_access,
        has_scheduler_admin_access,
        has_shortage_report_access,
        has_timesheet_approval_access,
        require_finance_access,
        require_hr_access,
        require_procurement_access,
        require_production_access,
        require_project_access,
        require_rd_project_access,
        require_scheduler_admin_access,
        require_shortage_report_access,
        require_timesheet_approval_access,
        )

        # 验证所有函数可调用
        assert callable(has_finance_access)
        assert callable(require_finance_access)
        assert callable(has_hr_access)
        assert callable(require_hr_access)
        assert callable(has_procurement_access)
        assert callable(require_procurement_access)
        assert callable(has_shortage_report_access)
        assert callable(require_shortage_report_access)
        assert callable(has_production_access)
        assert callable(require_production_access)
        assert callable(check_project_access)
        assert callable(require_project_access)
        assert callable(has_rd_project_access)
        assert callable(require_rd_project_access)
        assert callable(has_scheduler_admin_access)
        assert callable(require_scheduler_admin_access)
        assert callable(has_timesheet_approval_access)
        assert callable(require_timesheet_approval_access)
        assert callable(check_timesheet_approval_permission)
        assert callable(has_machine_document_permission)
        assert callable(has_machine_document_upload_permission)

        # 验证常量
        assert isinstance(RD_PROJECT_ROLES, list)


# ============================================================================
# Auth 模块测试
# ============================================================================


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


class TestCheckPermission:
    """测试权限检查函数"""

    def test_superuser_always_has_permission(self):
        """测试超级管理员始终有权限"""
        from app.core.auth import check_permission

        user = MockUser(is_superuser=True)
        result = check_permission(user, "any:permission")
        assert result is True

    def test_user_without_roles(self):
        """测试没有角色的用户无权限"""
        from app.core.auth import check_permission

        user = MockUser(is_superuser=False, roles=[])
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


class TestSalesDataScope:
    """测试销售数据范围"""

    def test_superuser_gets_all_scope(self):
        """测试超级管理员获取ALL范围"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(is_superuser=True)
        db = MagicMock()

        scope = get_sales_data_scope(user, db)
        assert scope == "ALL"

    def test_sales_director_gets_all_scope(self):
        """测试销售总监获取ALL范围"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(roles=[MockUserRole("SALES_DIRECTOR", "销售总监")])
        db = MagicMock()

        scope = get_sales_data_scope(user, db)
        assert scope == "ALL"

    def test_sales_manager_gets_team_scope(self):
        """测试销售经理获取TEAM范围"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(roles=[MockUserRole("SALES_MANAGER", "销售经理")])
        db = MagicMock()

        scope = get_sales_data_scope(user, db)
        assert scope == "TEAM"

    def test_finance_gets_finance_only_scope(self):
        """测试财务获取FINANCE_ONLY范围"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(roles=[MockUserRole("FINANCE", "财务")])
        db = MagicMock()

        scope = get_sales_data_scope(user, db)
        assert scope == "FINANCE_ONLY"

    def test_sales_gets_own_scope(self):
        """测试销售获取OWN范围"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(roles=[MockUserRole("SALES", "销售")])
        db = MagicMock()

        scope = get_sales_data_scope(user, db)
        assert scope == "OWN"

    def test_presales_gets_own_scope(self):
        """测试售前获取OWN范围"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(roles=[MockUserRole("PRESALES", "售前")])
        db = MagicMock()

        scope = get_sales_data_scope(user, db)
        assert scope == "OWN"

    def test_unknown_role_gets_none_scope(self):
        """测试未知角色获取NONE范围"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(roles=[MockUserRole("UNKNOWN_ROLE", "未知角色")])
        db = MagicMock()

        scope = get_sales_data_scope(user, db)
        assert scope == "NONE"

    def test_inactive_role_not_counted(self):
        """测试非活跃角色不计入"""
        from app.core.sales_permissions import get_sales_data_scope

        role = MockUserRole("SALES_DIRECTOR", "销售总监")
        role.role.is_active = False  # 设置为非活跃
        user = MockUser(roles=[role])
        db = MagicMock()

        scope = get_sales_data_scope(user, db)
        assert scope == "NONE"


class TestSalesCreatePermission:
    """测试销售数据创建权限"""

    def test_superuser_can_create(self):
        """测试超级管理员可以创建"""
        from app.core.sales_permissions import check_sales_create_permission

        user = MockUser(is_superuser=True)
        db = MagicMock()

        assert check_sales_create_permission(user, db) is True

    def test_sales_can_create(self):
        """测试销售可以创建"""
        from app.core.sales_permissions import check_sales_create_permission

        user = MockUser(roles=[MockUserRole("SALES", "销售")])
        db = MagicMock()

        assert check_sales_create_permission(user, db) is True

    def test_sales_manager_can_create(self):
        """测试销售经理可以创建"""
        from app.core.sales_permissions import check_sales_create_permission

        user = MockUser(roles=[MockUserRole("SALES_MANAGER", "销售经理")])
        db = MagicMock()

        assert check_sales_create_permission(user, db) is True

    def test_sales_director_can_create(self):
        """测试销售总监可以创建"""
        from app.core.sales_permissions import check_sales_create_permission

        user = MockUser(roles=[MockUserRole("SALES_DIRECTOR", "销售总监")])
        db = MagicMock()

        assert check_sales_create_permission(user, db) is True

    def test_finance_cannot_create(self):
        """测试财务不能创建销售数据"""
        from app.core.sales_permissions import check_sales_create_permission

        user = MockUser(roles=[MockUserRole("FINANCE", "财务")])
        db = MagicMock()

        assert check_sales_create_permission(user, db) is False

    def test_unknown_role_cannot_create(self):
        """测试未知角色不能创建"""
        from app.core.sales_permissions import check_sales_create_permission

        user = MockUser(roles=[MockUserRole("UNKNOWN", "未知")])
        db = MagicMock()

        assert check_sales_create_permission(user, db) is False


class TestSalesEditPermission:
    """测试销售数据编辑权限"""

    def test_superuser_can_edit_all(self):
        """测试超级管理员可以编辑所有"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(is_superuser=True)
        db = MagicMock()

        assert check_sales_edit_permission(user, db, 999, 888) is True

    def test_sales_director_can_edit_all(self):
        """测试销售总监可以编辑所有"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(
        user_id=1,
        roles=[MockUserRole("SALES_DIRECTOR", "销售总监")]
        )
        db = MagicMock()

        assert check_sales_edit_permission(user, db, 999, 888) is True

    def test_sales_manager_can_edit_all(self):
        """测试销售经理可以编辑所有"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(
        user_id=1,
        roles=[MockUserRole("SALES_MANAGER", "销售经理")]
        )
        db = MagicMock()

        assert check_sales_edit_permission(user, db, 999, 888) is True

    def test_sales_can_edit_own_created(self):
        """测试销售可以编辑自己创建的"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(
        user_id=100,
        roles=[MockUserRole("SALES", "销售")]
        )
        db = MagicMock()

        # 自己创建的
        assert check_sales_edit_permission(user, db, 100, None) is True

    def test_sales_can_edit_own_responsible(self):
        """测试销售可以编辑自己负责的"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(
        user_id=100,
        roles=[MockUserRole("SALES", "销售")]
        )
        db = MagicMock()

        # 自己负责的
        assert check_sales_edit_permission(user, db, None, 100) is True

    def test_sales_cannot_edit_others(self):
        """测试销售不能编辑别人的"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(
        user_id=100,
        roles=[MockUserRole("SALES", "销售")]
        )
        db = MagicMock()

        # 别人的
        assert check_sales_edit_permission(user, db, 999, 888) is False

    def test_finance_cannot_edit(self):
        """测试财务不能编辑"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(
        user_id=1,
        roles=[MockUserRole("FINANCE", "财务")]
        )
        db = MagicMock()

        assert check_sales_edit_permission(user, db, 1, 1) is False


class TestSalesDeletePermission:
    """测试销售数据删除权限"""

    def test_superuser_can_delete(self):
        """测试超级管理员可以删除"""
        from app.core.sales_permissions import check_sales_delete_permission

        user = MockUser(is_superuser=True)
        db = MagicMock()

        assert check_sales_delete_permission(user, db, 999) is True

    def test_sales_director_can_delete_all(self):
        """测试销售总监可以删除所有"""
        from app.core.sales_permissions import check_sales_delete_permission

        user = MockUser(
        user_id=1,
        roles=[MockUserRole("SALES_DIRECTOR", "销售总监")]
        )
        db = MagicMock()

        assert check_sales_delete_permission(user, db, 999) is True

    def test_sales_manager_can_only_delete_own(self):
        """测试销售经理只能删除自己创建的"""
        from app.core.sales_permissions import check_sales_delete_permission

        user = MockUser(
        user_id=100,
        roles=[MockUserRole("SALES_MANAGER", "销售经理")]
        )
        db = MagicMock()

        # 自己创建的可以删除
        assert check_sales_delete_permission(user, db, 100) is True
        # 别人创建的不能删除
        assert check_sales_delete_permission(user, db, 999) is False

    def test_sales_can_delete_own(self):
        """测试销售只能删除自己创建的"""
        from app.core.sales_permissions import check_sales_delete_permission

        user = MockUser(
        user_id=100,
        roles=[MockUserRole("SALES", "销售")]
        )
        db = MagicMock()

        # 自己创建的可以删除
        assert check_sales_delete_permission(user, db, 100) is True

        # 别人创建的不能删除
        assert check_sales_delete_permission(user, db, 999) is False

    def test_finance_cannot_delete_others(self):
        """测试财务不能删除别人创建的数据"""
        from app.core.sales_permissions import check_sales_delete_permission

        user = MockUser(
        user_id=1,
        roles=[MockUserRole("FINANCE", "财务")]
        )
        db = MagicMock()

        # 财务不能删除别人创建的数据
        assert check_sales_delete_permission(user, db, 999) is False

    def test_user_can_delete_own_created(self):
        """测试用户可以删除自己创建的数据（即使是财务）"""
        from app.core.sales_permissions import check_sales_delete_permission

        user = MockUser(
        user_id=1,
        roles=[MockUserRole("FINANCE", "财务")]
        )
        db = MagicMock()

        # 可以删除自己创建的
        assert check_sales_delete_permission(user, db, 1) is True


class TestSalesAssessmentAccess:
    """测试销售技术评估权限"""

    def test_superuser_has_assessment_access(self):
        """测试超级管理员有技术评估权限"""
        from app.core.sales_permissions import has_sales_assessment_access

        user = MockUser(is_superuser=True)
        assert has_sales_assessment_access(user) is True

    def test_sales_engineer_has_access(self):
        """测试销售工程师有技术评估权限"""
        from app.core.sales_permissions import has_sales_assessment_access

        user = MockUser(roles=[MockUserRole("sales_engineer", "销售工程师")])
        assert has_sales_assessment_access(user) is True

    def test_presales_engineer_has_access(self):
        """测试售前工程师有技术评估权限"""
        from app.core.sales_permissions import has_sales_assessment_access

        user = MockUser(roles=[MockUserRole("presales_engineer", "售前工程师")])
        assert has_sales_assessment_access(user) is True

    def test_presales_manager_has_access(self):
        """测试售前经理有技术评估权限"""
        from app.core.sales_permissions import has_sales_assessment_access

        user = MockUser(roles=[MockUserRole("presales_manager", "售前经理")])
        assert has_sales_assessment_access(user) is True

    def test_technical_engineer_has_access(self):
        """测试技术工程师有技术评估权限"""
        from app.core.sales_permissions import has_sales_assessment_access

        user = MockUser(roles=[MockUserRole("te", "技术工程师")])
        assert has_sales_assessment_access(user) is True

    def test_finance_no_assessment_access(self):
        """测试财务无技术评估权限"""
        from app.core.sales_permissions import has_sales_assessment_access

        user = MockUser(roles=[MockUserRole("finance", "财务")])
        assert has_sales_assessment_access(user) is False


class TestSalesApprovalAccess:
    """测试销售审批权限"""

    def test_superuser_has_approval_access(self):
        """测试超级管理员有审批权限"""
        from app.core.sales_permissions import has_sales_approval_access

        user = MockUser(is_superuser=True)
        db = MagicMock()

        assert has_sales_approval_access(user, db) is True

    def test_sales_manager_has_approval_access(self):
        """测试销售经理有审批权限"""
        from app.core.sales_permissions import has_sales_approval_access

        user = MockUser(roles=[MockUserRole("sales_manager", "销售经理")])
        db = MagicMock()

        assert has_sales_approval_access(user, db) is True

    def test_finance_manager_has_approval_access(self):
        """测试财务经理有审批权限"""
        from app.core.sales_permissions import has_sales_approval_access

        user = MockUser(roles=[MockUserRole("finance_manager", "财务经理")])
        db = MagicMock()

        assert has_sales_approval_access(user, db) is True

    def test_gm_has_approval_access(self):
        """测试总经理有审批权限"""
        from app.core.sales_permissions import has_sales_approval_access

        user = MockUser(roles=[MockUserRole("gm", "总经理")])
        db = MagicMock()

        assert has_sales_approval_access(user, db) is True

    def test_chairman_has_approval_access(self):
        """测试董事长有审批权限"""
        from app.core.sales_permissions import has_sales_approval_access

        user = MockUser(roles=[MockUserRole("chairman", "董事长")])
        db = MagicMock()

        assert has_sales_approval_access(user, db) is True

    def test_sales_no_approval_access(self):
        """测试普通销售无审批权限"""
        from app.core.sales_permissions import has_sales_approval_access

        user = MockUser(roles=[MockUserRole("sales", "销售")])
        db = MagicMock()

        assert has_sales_approval_access(user, db) is False


class TestCheckSalesApprovalPermission:
    """测试销售审批权限检查"""

    def test_superuser_can_approve_all(self):
        """测试超级管理员可以审批所有"""
        from app.core.sales_permissions import check_sales_approval_permission

        user = MockUser(is_superuser=True)
        db = MagicMock()

        approval = MagicMock()
        approval.approval_level = 1
        approval.approval_role = ""

        assert check_sales_approval_permission(user, approval, db) is True

    def test_no_approval_role_returns_false(self):
        """测试无审批角色返回False"""
        from app.core.sales_permissions import check_sales_approval_permission

        user = MockUser(roles=[MockUserRole("sales", "销售")])
        db = MagicMock()

        approval = MagicMock()
        approval.approval_level = 1
        approval.approval_role = ""

        assert check_sales_approval_permission(user, approval, db) is False

    def test_level1_approval_by_sales_manager(self):
        """测试销售经理可以一级审批"""
        from app.core.sales_permissions import check_sales_approval_permission

        user = MockUser(roles=[MockUserRole("sales_manager", "销售经理")])
        db = MagicMock()

        approval = MagicMock()
        approval.approval_level = 1
        approval.approval_role = ""

        assert check_sales_approval_permission(user, approval, db) is True

    def test_level1_approval_by_finance_manager(self):
        """测试财务经理可以一级审批"""
        from app.core.sales_permissions import check_sales_approval_permission

        user = MockUser(roles=[MockUserRole("finance_manager", "财务经理")])
        db = MagicMock()

        approval = MagicMock()
        approval.approval_level = 1
        approval.approval_role = ""

        assert check_sales_approval_permission(user, approval, db) is True

    def test_level2_approval_by_director(self):
        """测试销售总监可以二级审批"""
        from app.core.sales_permissions import check_sales_approval_permission

        user = MockUser(roles=[MockUserRole("sales_director", "销售总监")])
        db = MagicMock()

        approval = MagicMock()
        approval.approval_level = 2
        approval.approval_role = ""

        assert check_sales_approval_permission(user, approval, db) is True

    def test_level2_approval_by_gm(self):
        """测试总经理可以二级审批"""
        from app.core.sales_permissions import check_sales_approval_permission

        user = MockUser(roles=[MockUserRole("gm", "总经理")])
        db = MagicMock()

        approval = MagicMock()
        approval.approval_level = 2
        approval.approval_role = ""

        assert check_sales_approval_permission(user, approval, db) is True

    def test_specific_role_approval(self):
        """测试指定角色审批"""
        from app.core.sales_permissions import check_sales_approval_permission

        user = MockUser(roles=[MockUserRole("finance_manager", "财务经理")])
        db = MagicMock()

        approval = MagicMock()
        approval.approval_level = 1
        approval.approval_role = "finance_manager"

        assert check_sales_approval_permission(user, approval, db) is True


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


class TestPermissionsIntegration:
    """权限模块集成测试"""

    def test_superuser_bypasses_all_permissions(self):
        """测试超级管理员可以绕过所有权限检查"""
        from app.core.permissions.finance import has_finance_access
        from app.core.permissions.hr import has_hr_access
        from app.core.permissions.machine import has_machine_document_permission
        from app.core.permissions.procurement import (
        has_procurement_access,
        has_shortage_report_access,
        )
        from app.core.permissions.production import has_production_access
        from app.core.permissions.rd_project import has_rd_project_access
        from app.core.permissions.scheduler import has_scheduler_admin_access
        from app.core.permissions.timesheet import has_timesheet_approval_access
        from app.core.sales_permissions import (
        check_sales_create_permission,
        check_sales_delete_permission,
        check_sales_edit_permission,
        get_sales_data_scope,
        has_sales_approval_access,
        has_sales_assessment_access,
        )

        user = MockUser(is_superuser=True)
        db = MagicMock()

        # 所有权限检查都应该返回 True 或 ALL
        assert has_finance_access(user) is True
        assert has_hr_access(user) is True
        assert has_procurement_access(user) is True
        assert has_shortage_report_access(user) is True
        assert has_production_access(user) is True
        assert has_rd_project_access(user) is True
        assert has_scheduler_admin_access(user) is True
        assert has_timesheet_approval_access(user, db) is True
        assert has_machine_document_permission(user, "ANY_TYPE") is True
        assert has_sales_assessment_access(user) is True
        assert has_sales_approval_access(user, db) is True
        assert check_sales_create_permission(user, db) is True
        assert check_sales_edit_permission(user, db) is True
        assert check_sales_delete_permission(user, db) is True
        assert get_sales_data_scope(user, db) == "ALL"

    def test_empty_roles_no_permissions(self):
        """测试空角色无任何权限"""
        from app.core.permissions.finance import has_finance_access
        from app.core.permissions.hr import has_hr_access
        from app.core.permissions.procurement import (
        has_procurement_access,
        has_shortage_report_access,
        )
        from app.core.permissions.production import has_production_access
        from app.core.permissions.rd_project import has_rd_project_access
        from app.core.permissions.scheduler import has_scheduler_admin_access
        from app.core.permissions.timesheet import has_timesheet_approval_access
        from app.core.sales_permissions import (
        check_sales_create_permission,
        get_sales_data_scope,
        has_sales_assessment_access,
        )

        user = MockUser(is_superuser=False, roles=[])
        db = MagicMock()

        # 所有权限检查都应该返回 False 或 NONE
        assert has_finance_access(user) is False
        assert has_hr_access(user) is False
        assert has_procurement_access(user) is False
        assert has_shortage_report_access(user) is False
        assert has_production_access(user) is False
        assert has_rd_project_access(user) is False
        assert has_scheduler_admin_access(user) is False
        assert has_timesheet_approval_access(user, db) is False
        assert has_sales_assessment_access(user) is False
        assert check_sales_create_permission(user, db) is False
        assert get_sales_data_scope(user, db) == "NONE"
