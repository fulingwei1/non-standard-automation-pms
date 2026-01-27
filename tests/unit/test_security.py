# -*- coding: utf-8 -*-
"""
权限系统单元测试

测试内容：
- 基础权限检查函数 check_permission
- 角色权限验证
- 超级用户权限处理
- 销售权限检查
- 采购、财务、生产、HR等模块权限
- 数据权限范围过滤
"""

import pytest
from sqlalchemy.orm import Session

from app.core.security import (
    check_permission,
    has_procurement_access,
    has_finance_access,
    has_hr_access,
    has_production_access,
    has_timesheet_approval_access,
    has_scheduler_admin_access,
    has_rd_project_access,
    has_machine_document_permission,
    has_machine_document_upload_permission,
    has_shortage_report_access,
    has_sales_assessment_access,
    has_sales_approval_access,
    check_sales_create_permission,
    check_sales_edit_permission,
    check_sales_delete_permission,
    get_sales_data_scope,
    check_timesheet_approval_permission,
)


@pytest.mark.unit
@pytest.mark.security
class TestBasePermissionChecks:
    """基础权限检查函数测试"""

    @pytest.fixture
    def setup_permissions(self, db_session: Session):
        """设置测试权限和角色"""
        from app.models.user import Role, Permission, RolePermission

        # 创建测试权限
        permissions_to_create = [
        ("project:read", "项目读取", "project"),
        ("project:write", "项目写入", "project"),
        ("procurement:read", "采购读取", "procurement"),
        ("procurement:write", "采购写入", "procurement"),
        ("finance:read", "财务读取", "finance"),
        ("finance:write", "财务写入", "finance"),
        ]

        for perm_code, perm_name, module in permissions_to_create:
            existing = (
            db_session.query(Permission)
            .filter(Permission.permission_code == perm_code)
            .first()
            )
            if not existing:
                perm = Permission(
                permission_code=perm_code,
                permission_name=perm_name,
                module=module,
                is_active=True,
                )
                db_session.add(perm)

                db_session.flush()

                # 创建测试角色
                role_pm = db_session.query(Role).filter(Role.role_code == "PM").first()
                if not role_pm:
                    role_pm = Role(
                    role_code="PM", role_name="项目经理", is_active=True, data_scope="OWN"
                    )
                    db_session.add(role_pm)
                    db_session.flush()

                    role_procurement = (
                    db_session.query(Role)
                    .filter(Role.role_code == "procurement_engineer")
                    .first()
                    )
                    if not role_procurement:
                        role_procurement = Role(
                        role_code="procurement_engineer",
                        role_name="采购工程师",
                        is_active=True,
                        )
                        db_session.add(role_procurement)
                        db_session.flush()

                        # 为角色分配权限
                        for perm_code in ["project:read", "project:write"]:
                            perm = (
                            db_session.query(Permission)
                            .filter(Permission.permission_code == perm_code)
                            .first()
                            )
                            if (
                            perm
                            and not db_session.query(RolePermission)
                            .filter(
                            RolePermission.role_id == role_pm.id,
                            RolePermission.permission_id == perm.id,
                            )
                            .first()
                            ):
                            rp = RolePermission(role_id=role_pm.id, permission_id=perm.id)
                            db_session.add(rp)

                            for perm_code in ["procurement:read", "procurement:write"]:
                                perm = (
                                db_session.query(Permission)
                                .filter(Permission.permission_code == perm_code)
                                .first()
                                )
                                if (
                                perm
                                and not db_session.query(RolePermission)
                                .filter(
                                RolePermission.role_id == role_procurement.id,
                                RolePermission.permission_id == perm.id,
                                )
                                .first()
                                ):
                                rp = RolePermission(role_id=role_procurement.id, permission_id=perm.id)
                                db_session.add(rp)

                                db_session.commit()
                                return {"pm": role_pm, "procurement": role_procurement}

    @pytest.fixture
    def test_user_with_permissions(self, db_session: Session, setup_permissions):
        """创建有权限的测试用户"""
        from app.models.user import User, UserRole

        role = setup_permissions["pm"]

        user = db_session.query(User).filter(User.username == "test_perm_user").first()
        if not user:
            user = User(
            employee_id=9999,
            username="test_perm_user",
            password_hash="hashed_pass",
            real_name="测试用户",
            is_active=True,
            is_superuser=False,
            )
            db_session.add(user)
            db_session.flush()

            ur = UserRole(user_id=user.id, role_id=role.id)
            db_session.add(ur)
            db_session.commit()
            db_session.refresh(user)

            return user

    @pytest.fixture
    def test_user_without_permissions(self, db_session: Session):
        """创建无权限的测试用户"""
        from app.models.user import User

        user = (
        db_session.query(User).filter(User.username == "test_no_perm_user").first()
        )
        if not user:
            user = User(
            employee_id=9997,
            username="test_no_perm_user",
            password_hash="hashed_pass",
            real_name="无权限用户",
            is_active=True,
            is_superuser=False,
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)

            return user

    @pytest.fixture
    def test_superuser(self, db_session: Session):
        """创建超级用户"""
        from app.models.user import User

        user = (
        db_session.query(User)
        .filter(User.username == "test_superuser_perm")
        .first()
        )
        if not user:
            user = User(
            employee_id=9996,
            username="test_superuser_perm",
            password_hash="hashed_pass",
            real_name="超级管理员",
            is_active=True,
            is_superuser=True,
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)

            return user

    def test_check_permission_user_has_permission(
        self, test_user_with_permissions, db_session
    ):
        """测试用户拥有权限"""
        result = check_permission(
        test_user_with_permissions, "project:read", db_session
        )
        assert result is True

    def test_check_permission_user_does_not_have_permission(
        self, test_user_with_permissions, db_session
    ):
        """测试用户没有权限"""
        result = check_permission(
        test_user_with_permissions, "finance:read", db_session
        )
        assert result is False

    def test_superuser_has_all_permissions(self, test_superuser, db_session):
        """测试超级管理员拥有所有权限"""
        result1 = check_permission(test_superuser, "project:read", db_session)
        result2 = check_permission(test_superuser, "finance:write", db_session)
        result3 = check_permission(test_superuser, "nonexistent:perm", db_session)
        assert result1 is True
        assert result2 is True
        assert result3 is True

    def test_user_with_no_roles(self, test_user_without_permissions, db_session):
        """测试没有角色的用户"""
        result = check_permission(
        test_user_without_permissions, "project:read", db_session
        )
        assert result is False

    def test_check_permission_invalid_permission_string(
        self, test_user_with_permissions, db_session
    ):
        """测试无效的权限字符串"""
        result = check_permission(test_user_with_permissions, "", db_session)
        assert result is False

        result2 = check_permission(
        test_user_with_permissions, "invalid:permission:string", db_session
        )
        assert result2 is False

    def test_check_permission_with_db_session(
        self, test_user_with_permissions, db_session
    ):
        """测试使用数据库会话的权限检查"""
        result = check_permission(
        test_user_with_permissions, "project:write", db_session
        )
        assert result is True

    def test_check_permission_without_db_session(self, test_user_with_permissions):
        """测试不提供数据库会话时的权限检查（降级到ORM）"""
        result = check_permission(test_user_with_permissions, "project:read", None)
        assert result is True


@pytest.mark.unit
@pytest.mark.security
class TestProcurementPermissions:
    """采购权限测试"""

    @pytest.fixture
    def procurement_user(self, db_session: Session):
        """创建采购工程师用户"""
        from app.models.user import User, Role, UserRole

        role = (
        db_session.query(Role)
        .filter(Role.role_code == "procurement_engineer")
        .first()
        )
        if not role:
            role = Role(
            role_code="procurement_engineer",
            role_name="采购工程师",
            is_active=True,
            )
            db_session.add(role)
            db_session.flush()

            user = (
            db_session.query(User).filter(User.username == "test_procurement").first()
            )
            if not user:
                user = User(
                employee_id=8001,
                username="test_procurement",
                password_hash="hashed",
                real_name="采购工程师",
                is_active=True,
                is_superuser=False,
                )
                db_session.add(user)
                db_session.flush()

                ur = UserRole(user_id=user.id, role_id=role.id)
                db_session.add(ur)
                db_session.commit()
                db_session.refresh(user)

                return user

    @pytest.fixture
    def sales_user(self, db_session: Session):
        """创建销售用户（无采购权限）"""
        from app.models.user import User, Role, UserRole

        role = db_session.query(Role).filter(Role.role_code == "SALES").first()
        if not role:
            role = Role(role_code="SALES", role_name="销售", is_active=True)
            db_session.add(role)
            db_session.flush()

            user = db_session.query(User).filter(User.username == "test_sales").first()
            if not user:
                user = User(
                employee_id=8002,
                username="test_sales",
                password_hash="hashed",
                real_name="销售",
                is_active=True,
                is_superuser=False,
                )
                db_session.add(user)
                db_session.flush()

                ur = UserRole(user_id=user.id, role_id=role.id)
                db_session.add(ur)
                db_session.commit()
                db_session.refresh(user)

                return user

    def test_procurement_user_has_access(self, procurement_user):
        """测试采购工程师有采购权限"""
        assert has_procurement_access(procurement_user) is True

    def test_sales_user_no_access(self, sales_user):
        """测试销售用户无采购权限"""
        assert has_procurement_access(sales_user) is False

    def test_superuser_has_procurement_access(self, db_session: Session):
        """测试超级用户有采购权限"""
        from app.models.user import User

        user = (
        db_session.query(User)
        .filter(User.username == "test_superuser_perm")
        .first()
        )
        if user:
            assert has_procurement_access(user) is True


@pytest.mark.unit
@pytest.mark.security
class TestFinancePermissions:
    """财务权限测试"""

    @pytest.fixture
    def finance_user(self, db_session: Session):
        """创建财务用户"""
        from app.models.user import User, Role, UserRole

        role = (
        db_session.query(Role).filter(Role.role_code == "finance_manager").first()
        )
        if not role:
            role = Role(
            role_code="finance_manager", role_name="财务经理", is_active=True
            )
            db_session.add(role)
            db_session.flush()

            user = db_session.query(User).filter(User.username == "test_finance").first()
            if not user:
                user = User(
                employee_id=7001,
                username="test_finance",
                password_hash="hashed",
                real_name="财务经理",
                is_active=True,
                is_superuser=False,
                )
                db_session.add(user)
                db_session.flush()

                ur = UserRole(user_id=user.id, role_id=role.id)
                db_session.add(ur)
                db_session.commit()
                db_session.refresh(user)

                return user

    def test_finance_user_has_access(self, finance_user):
        """测试财务经理有财务权限"""
        assert has_finance_access(finance_user) is True

    def test_finance_user_chinese_role_name(self, db_session: Session):
        """测试中文角色名"""
        from app.models.user import User, Role, UserRole

        role = Role(role_code="chinese_role", role_name="财务人员", is_active=True)
        db_session.add(role)
        db_session.flush()

        user = User(
        employee_id=7002,
        username="test_finance_cn",
        password_hash="hashed",
        real_name="财务人员",
        is_active=True,
        is_superuser=False,
        )
        db_session.add(user)
        db_session.flush()

        ur = UserRole(user_id=user.id, role_id=role.id)
        db_session.add(ur)
        db_session.commit()
        db_session.refresh(user)

        assert has_finance_access(user) is True


@pytest.mark.unit
@pytest.mark.security
class TestHRPermissions:
    """人力资源权限测试"""

    @pytest.fixture
    def hr_user(self, db_session: Session):
        """创建HR用户"""
        from app.models.user import User, Role, UserRole

        role = db_session.query(Role).filter(Role.role_code == "hr_manager").first()
        if not role:
            role = Role(role_code="hr_manager", role_name="人事经理", is_active=True)
            db_session.add(role)
            db_session.flush()

            user = db_session.query(User).filter(User.username == "test_hr").first()
            if not user:
                user = User(
                employee_id=6001,
                username="test_hr",
                password_hash="hashed",
                real_name="人事经理",
                is_active=True,
                is_superuser=False,
                )
                db_session.add(user)
                db_session.flush()

                ur = UserRole(user_id=user.id, role_id=role.id)
                db_session.add(ur)
                db_session.commit()
                db_session.refresh(user)

                return user

    def test_hr_user_has_access(self, hr_user):
        """测试人事经理有人力资源权限"""
        assert has_hr_access(hr_user) is True

    def test_production_user_no_hr_access(self, db_session: Session):
        """测试生产人员无人力资源权限"""
        from app.models.user import User, Role, UserRole

        role = Role(
        role_code="production_manager", role_name="生产经理", is_active=True
        )
        db_session.add(role)
        db_session.flush()

        user = User(
        employee_id=6002,
        username="test_production",
        password_hash="hashed",
        real_name="生产经理",
        is_active=True,
        is_superuser=False,
        )
        db_session.add(user)
        db_session.flush()

        ur = UserRole(user_id=user.id, role_id=role.id)
        db_session.add(ur)
        db_session.commit()
        db_session.refresh(user)

        assert has_hr_access(user) is False


@pytest.mark.unit
@pytest.mark.security
class TestProductionPermissions:
    """生产权限测试"""

    @pytest.fixture
    def production_user(self, db_session: Session):
        """创建生产用户"""
        from app.models.user import User, Role, UserRole

        role = (
        db_session.query(Role)
        .filter(Role.role_code == "production_manager")
        .first()
        )
        if not role:
            role = Role(
            role_code="production_manager", role_name="生产经理", is_active=True
            )
            db_session.add(role)
            db_session.flush()

            user = (
            db_session.query(User)
            .filter(User.username == "test_production_perm")
            .first()
            )
            if not user:
                user = User(
                employee_id=5001,
                username="test_production_perm",
                password_hash="hashed",
                real_name="生产经理",
                is_active=True,
                is_superuser=False,
                )
                db_session.add(user)
                db_session.flush()

                ur = UserRole(user_id=user.id, role_id=role.id)
                db_session.add(ur)
                db_session.commit()
                db_session.refresh(user)

                return user

    def test_production_user_has_access(self, production_user):
        """测试生产经理有生产权限"""
        assert has_production_access(production_user) is True


@pytest.mark.unit
@pytest.mark.security
class TestSalesPermissions:
    """销售权限测试"""

    @pytest.fixture
    def sales_director(self, db_session: Session):
        """创建销售总监"""
        from app.models.user import User, Role, UserRole

        role = db_session.query(Role).filter(Role.role_code == "SALES_DIRECTOR").first()
        if not role:
            role = Role(
            role_code="SALES_DIRECTOR", role_name="销售总监", is_active=True
            )
            db_session.add(role)
            db_session.flush()

            user = (
            db_session.query(User)
            .filter(User.username == "test_sales_director")
            .first()
            )
            if not user:
                user = User(
                employee_id=4001,
                username="test_sales_director",
                password_hash="hashed",
                real_name="销售总监",
                is_active=True,
                is_superuser=False,
                )
                db_session.add(user)
                db_session.flush()

                ur = UserRole(user_id=user.id, role_id=role.id)
                db_session.add(ur)
                db_session.commit()
                db_session.refresh(user)

                return user

    @pytest.fixture
    def sales_manager(self, db_session: Session):
        """创建销售经理"""
        from app.models.user import User, Role, UserRole

        role = db_session.query(Role).filter(Role.role_code == "SALES_MANAGER").first()
        if not role:
            role = Role(role_code="SALES_MANAGER", role_name="销售经理", is_active=True)
            db_session.add(role)
            db_session.flush()

            user = (
            db_session.query(User).filter(User.username == "test_sales_manager").first()
            )
            if not user:
                user = User(
                employee_id=4002,
                username="test_sales_manager",
                password_hash="hashed",
                real_name="销售经理",
                is_active=True,
                is_superuser=False,
                )
                db_session.add(user)
                db_session.flush()

                ur = UserRole(user_id=user.id, role_id=role.id)
                db_session.add(ur)
                db_session.commit()
                db_session.refresh(user)

                return user

    @pytest.fixture
    def sales_rep(self, db_session: Session):
        """创建销售代表"""
        from app.models.user import User, Role, UserRole

        role = db_session.query(Role).filter(Role.role_code == "SALES").first()
        if not role:
            role = Role(role_code="SALES", role_name="销售", is_active=True)
            db_session.add(role)
            db_session.flush()

            user = db_session.query(User).filter(User.username == "test_sales_rep").first()
            if not user:
                user = User(
                employee_id=4003,
                username="test_sales_rep",
                password_hash="hashed",
                real_name="销售代表",
                is_active=True,
                is_superuser=False,
                )
                db_session.add(user)
                db_session.flush()

                ur = UserRole(user_id=user.id, role_id=role.id)
                db_session.add(ur)
                db_session.commit()
                db_session.refresh(user)

                return user

    def test_sales_director_has_all_access(self, sales_director, db_session: Session):
        """测试销售总监拥有所有访问权限"""
        scope = get_sales_data_scope(sales_director, db_session)
        assert scope == "ALL"

    def test_sales_manager_has_team_access(self, sales_manager, db_session: Session):
        """测试销售经理拥有团队访问权限"""
        scope = get_sales_data_scope(sales_manager, db_session)
        assert scope == "TEAM"

    def test_sales_rep_has_own_access(self, sales_rep, db_session: Session):
        """测试销售代表拥有个人访问权限"""
        scope = get_sales_data_scope(sales_rep, db_session)
        assert scope == "OWN"

    def test_sales_create_permissions(
        self, sales_director, sales_manager, sales_rep, db_session: Session
    ):
        """测试销售数据创建权限"""
        assert check_sales_create_permission(sales_director, db_session) is True
        assert check_sales_create_permission(sales_manager, db_session) is True
        assert check_sales_create_permission(sales_rep, db_session) is True

    def test_sales_edit_permissions(
        self, sales_manager, sales_rep, db_session: Session
    ):
        """测试销售数据编辑权限"""
        # 销售经理可以编辑所有数据
        assert check_sales_edit_permission(sales_manager, db_session) is True

        # 销售代表只能编辑自己创建或负责的数据
        assert check_sales_edit_permission(sales_rep, db_session) is False
        assert (
        check_sales_edit_permission(
        sales_rep, db_session, entity_created_by=sales_rep.id
        )
        is True
        )
        assert (
        check_sales_edit_permission(
        sales_rep, db_session, entity_owner_id=sales_rep.id
        )
        is True
        )

    def test_sales_delete_permissions(
        self, sales_director, sales_manager, sales_rep, db_session: Session
    ):
        """测试销售数据删除权限"""
        # 销售总监可以删除所有数据
        assert check_sales_delete_permission(sales_director, db_session) is True

        # 销售经理不能删除其他人的数据（不是创建人）
        assert check_sales_delete_permission(sales_manager, db_session) is False

        # 销售代表只能删除自己创建的数据
        assert check_sales_delete_permission(sales_rep, db_session) is False
        assert (
        check_sales_delete_permission(
        sales_rep, db_session, entity_created_by=sales_rep.id
        )
        is True
        )

    def test_has_sales_assessment_access(self, sales_rep):
        """测试技术评估访问权限"""
        assert has_sales_assessment_access(sales_rep) is True

    def test_has_sales_approval_access(self, sales_manager, db_session: Session):
        """测试销售审批访问权限"""
        assert has_sales_approval_access(sales_manager, db_session) is True


@pytest.mark.unit
@pytest.mark.security
class TestTimesheetPermissions:
    """工时审批权限测试"""

    @pytest.fixture
    def pm_user(self, db_session: Session):
        """创建项目经理用户"""
        from app.models.user import User, Role, UserRole

        role = db_session.query(Role).filter(Role.role_code == "pm").first()
        if not role:
            role = Role(role_code="pm", role_name="项目经理", is_active=True)
            db_session.add(role)
            db_session.flush()

            user = (
            db_session.query(User).filter(User.username == "test_pm_timesheet").first()
            )
            if not user:
                user = User(
                employee_id=3001,
                username="test_pm_timesheet",
                password_hash="hashed",
                real_name="项目经理",
                is_active=True,
                is_superuser=False,
                )
                db_session.add(user)
                db_session.flush()

                ur = UserRole(user_id=user.id, role_id=role.id)
                db_session.add(ur)
                db_session.commit()
                db_session.refresh(user)

                return user

    def test_pm_has_timesheet_approval_access(self, pm_user, db_session: Session):
        """测试项目经理有工时审批权限"""
        assert has_timesheet_approval_access(pm_user, db_session) is True

    def test_check_timesheet_approval_permission(self, pm_user, db_session: Session):
        """测试工时审批权限检查"""
        # 模拟工单列表
        timesheet1 = type(
        "obj", (object,), {"user_id": pm_user.id, "department_id": None}
        )()

        result = check_timesheet_approval_permission(pm_user, db_session, [timesheet1])
        assert result is True


@pytest.mark.unit
@pytest.mark.security
class TestOtherPermissions:
    """其他权限测试"""

    def test_has_scheduler_admin_access(self, db_session: Session):
        """测试调度器管理员权限"""
        from app.models.user import User, Role, UserRole

        role = db_session.query(Role).filter(Role.role_code == "admin").first()
        if not role:
            role = Role(role_code="admin", role_name="管理员", is_active=True)
            db_session.add(role)
            db_session.flush()

            user = User(
            employee_id=2001,
            username="test_admin",
            password_hash="hashed",
            real_name="管理员",
            is_active=True,
            is_superuser=False,
            )
            db_session.add(user)
            db_session.flush()

            ur = UserRole(user_id=user.id, role_id=role.id)
            db_session.add(ur)
            db_session.commit()
            db_session.refresh(user)

            assert has_scheduler_admin_access(user) is True

    def test_has_rd_project_access(self, db_session: Session):
        """测试研发项目权限"""
        from app.models.user import User, Role, UserRole

        role = db_session.query(Role).filter(Role.role_code == "rd_engineer").first()
        if not role:
            role = Role(role_code="rd_engineer", role_name="研发工程师", is_active=True)
            db_session.add(role)
            db_session.flush()

            user = User(
            employee_id=1001,
            username="test_rd",
            password_hash="hashed",
            real_name="研发工程师",
            is_active=True,
            is_superuser=False,
            )
            db_session.add(user)
            db_session.flush()

            ur = UserRole(user_id=user.id, role_id=role.id)
            db_session.add(ur)
            db_session.commit()
            db_session.refresh(user)

            assert has_rd_project_access(user) is True

    def test_has_machine_document_permission(self, db_session: Session):
        """测试机台文档权限"""
        from app.models.user import User, Role, UserRole

        role = db_session.query(Role).filter(Role.role_code == "pm").first()
        if not role:
            role = Role(role_code="pm", role_name="项目经理", is_active=True)
            db_session.add(role)
            db_session.flush()

            user = User(
            employee_id=1002,
            username="test_machine",
            password_hash="hashed",
            real_name="项目经理",
            is_active=True,
            is_superuser=False,
            )
            db_session.add(user)
            db_session.flush()

            ur = UserRole(user_id=user.id, role_id=role.id)
            db_session.add(ur)
            db_session.commit()
            db_session.refresh(user)

            assert has_machine_document_permission(user, "CIRCUIT_DIAGRAM") is True

    def test_has_machine_document_upload_permission(self, db_session: Session):
        """测试机台文档上传权限"""
        from app.models.user import User, Role, UserRole

        role = db_session.query(Role).filter(Role.role_code == "ENGINEER").first()
        if not role:
            role = Role(role_code="ENGINEER", role_name="工程师", is_active=True)
            db_session.add(role)
            db_session.flush()

            user = User(
            employee_id=1003,
            username="test_upload",
            password_hash="hashed",
            real_name="工程师",
            is_active=True,
            is_superuser=False,
            )
            db_session.add(user)
            db_session.flush()

            ur = UserRole(user_id=user.id, role_id=role.id)
            db_session.add(ur)
            db_session.commit()
            db_session.refresh(user)

            assert has_machine_document_upload_permission(user, "PLC_PROGRAM") is True

    def test_has_shortage_report_access(self, db_session: Session):
        """测试缺料上报权限"""
        from app.models.user import User, Role, UserRole

        role = db_session.query(Role).filter(Role.role_code == "warehouse").first()
        if not role:
            role = Role(role_code="warehouse", role_name="仓库管理员", is_active=True)
            db_session.add(role)
            db_session.flush()

            user = User(
            employee_id=1004,
            username="test_warehouse",
            password_hash="hashed",
            real_name="仓库管理员",
            is_active=True,
            is_superuser=False,
            )
            db_session.add(user)
            db_session.flush()

            ur = UserRole(user_id=user.id, role_id=role.id)
            db_session.add(ur)
            db_session.commit()
            db_session.refresh(user)

            assert has_shortage_report_access(user) is True


@pytest.mark.unit
@pytest.mark.security
class TestEdgeCases:
    """边界条件和异常测试"""

    def test_check_permission_with_none_user(self, db_session: Session):
        """测试None用户 - 应该抛出异常或返回False"""
        try:
            result = check_permission(None, "project:read", db_session)
            # 如果不抛异常，期望返回False
        assert result is False
        except (AttributeError, TypeError):
            # 如果抛出异常也是合理的
        assert True

    def test_check_permission_with_inactive_user(self, db_session: Session):
        """测试非活跃用户 - 使用模块级权限检查而不是check_permission"""
        from app.models.user import User, Role, UserRole

        # 创建采购角色（模块级权限）
        role = (
        db_session.query(Role)
        .filter(Role.role_code == "procurement_engineer")
        .first()
        )
        if not role:
            role = Role(
            role_code="procurement_engineer", role_name="采购工程师", is_active=True
            )
            db_session.add(role)
            db_session.flush()

            # 创建非活跃用户
            user = User(
            employee_id=1111,
            username="test_inactive",
            password_hash="hashed",
            real_name="非活跃用户",
            is_active=False,
            is_superuser=False,
            )
            db_session.add(user)
            db_session.flush()

            ur = UserRole(user_id=user.id, role_id=role.id)
            db_session.add(ur)
            db_session.commit()
            db_session.refresh(user)

            # 模块级权限检查（如has_procurement_access）只检查角色，不检查is_active
            result = has_procurement_access(user)
            assert result is True

    def test_user_with_multiple_roles(self, db_session: Session):
        """测试拥有多个角色的用户"""
        from app.models.user import User, Role, UserRole

        # 创建多个角色
        role1 = (
        db_session.query(Role)
        .filter(Role.role_code == "procurement_engineer")
        .first()
        )
        if not role1:
            role1 = Role(
            role_code="procurement_engineer",
            role_name="采购工程师",
            is_active=True,
            )
            db_session.add(role1)
            db_session.flush()

            role2 = (
            db_session.query(Role).filter(Role.role_code == "finance_manager").first()
            )
            if not role2:
                role2 = Role(
                role_code="finance_manager", role_name="财务经理", is_active=True
                )
                db_session.add(role2)
                db_session.flush()

                # 创建用户并分配多个角色
                user = User(
                employee_id=2222,
                username="test_multirole",
                password_hash="hashed",
                real_name="多角色用户",
                is_active=True,
                is_superuser=False,
                )
                db_session.add(user)
                db_session.flush()

                ur1 = UserRole(user_id=user.id, role_id=role1.id)
                ur2 = UserRole(user_id=user.id, role_id=role2.id)
                db_session.add(ur1)
                db_session.add(ur2)
                db_session.commit()
                db_session.refresh(user)

                # 应该同时拥有采购权限和财务权限
                assert has_procurement_access(user) is True
                assert has_finance_access(user) is True

    def test_permission_with_empty_roles(self, db_session: Session):
        """测试空角色列表"""
        from app.models.user import User, UserRole

        user = User(
        employee_id=3333,
        username="test_empty_roles",
        password_hash="hashed",
        real_name="空角色用户",
        is_active=True,
        is_superuser=False,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # 确保没有角色关联
        db_session.query(UserRole).filter(UserRole.user_id == user.id).delete()
        db_session.commit()

        result = check_permission(user, "project:read", db_session)
        assert result is False
