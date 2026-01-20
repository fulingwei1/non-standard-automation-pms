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
