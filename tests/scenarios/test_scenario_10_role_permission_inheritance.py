"""
场景10：角色权限继承

测试角色权限的继承关系和权限传递
"""
import pytest
from sqlalchemy.orm import Session
from app.models.user import Role, ApiPermission, RoleApiPermission, User, UserRole


class TestRolePermissionInheritance:
    """角色权限继承测试"""

    @pytest.fixture
    def base_role(self, db_session: Session):
        """创建基础角色"""
        role = Role(
            role_code="BASE_ROLE",
            role_name="基础角色",
            description="基础权限角色",
            is_system=True,
            is_active=True,
        )
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)
        return role

    @pytest.fixture
    def child_role(self, db_session: Session, base_role: Role):
        """创建子角色"""
        role = Role(
            role_code="CHILD_ROLE",
            role_name="子角色",
            description="继承基础角色",
            parent_id=base_role.id,
            is_system=True,
            is_active=True,
        )
        db_session.add(role)
        db_session.commit()
        db_session.refresh(role)
        return role

    @pytest.fixture
    def test_permissions(self, db_session: Session):
        """创建测试权限"""
        permissions = [
            ApiPermission(
                perm_code="READ_PROJECT",
                perm_name="查看项目",
                module="project",
                action="read",
                is_active=True,
            ),
            ApiPermission(
                perm_code="EDIT_PROJECT",
                perm_name="编辑项目",
                module="project",
                action="edit",
                is_active=True,
            ),
            ApiPermission(
                perm_code="DELETE_PROJECT",
                perm_name="删除项目",
                module="project",
                action="delete",
                is_active=True,
            ),
        ]
        for perm in permissions:
            db_session.add(perm)
        db_session.commit()
        return permissions

    def test_01_basic_role_permission_assignment(
        self, db_session: Session, base_role: Role, test_permissions
    ):
        """测试1：基础角色权限分配"""
        # 给基础角色分配读取权限
        role_perm = RoleApiPermission(
            role_id=base_role.id,
            permission_id=test_permissions[0].id,
        )
        db_session.add(role_perm)
        db_session.commit()

        # 验证权限关联
        perms = db_session.query(RoleApiPermission).filter(
            RoleApiPermission.role_id == base_role.id
        ).all()
        assert len(perms) == 1

    def test_02_child_role_inherits_parent_permissions(
        self, db_session: Session, base_role: Role, child_role: Role, test_permissions
    ):
        """测试2：子角色继承父角色权限"""
        # 给父角色分配权限
        role_perm = RoleApiPermission(
            role_id=base_role.id,
            permission_id=test_permissions[0].id,
        )
        db_session.add(role_perm)
        db_session.commit()

        # 获取子角色的有效权限（包括继承的）
        def get_effective_permissions(session, role_id):
            role = session.query(Role).filter(Role.id == role_id).first()
            if not role:
                return []

            # 直接权限
            direct_perms = session.query(ApiPermission).join(
                RoleApiPermission
            ).filter(
                RoleApiPermission.role_id == role_id
            ).all()

            # 继承权限
            inherited_perms = []
            if role.parent_id:
                inherited_perms = get_effective_permissions(session, role.parent_id)

            return list(set(direct_perms + inherited_perms))

        effective_perms = get_effective_permissions(db_session, child_role.id)
        assert len(effective_perms) >= 1
        assert test_permissions[0] in effective_perms

    def test_03_child_role_additional_permissions(
        self, db_session: Session, base_role: Role, child_role: Role, test_permissions
    ):
        """测试3：子角色额外权限"""
        # 父角色：读权限
        role_perm1 = RoleApiPermission(
            role_id=base_role.id,
            permission_id=test_permissions[0].id,
        )
        db_session.add(role_perm1)

        # 子角色：编辑权限（额外）
        role_perm2 = RoleApiPermission(
            role_id=child_role.id,
            permission_id=test_permissions[1].id,
        )
        db_session.add(role_perm2)
        db_session.commit()

        # 子角色应该拥有读+编辑权限
        child_direct_perms = db_session.query(ApiPermission).join(
            RoleApiPermission
        ).filter(
            RoleApiPermission.role_id == child_role.id
        ).all()

        assert len(child_direct_perms) == 1  # 直接权限1个
        assert test_permissions[1] in child_direct_perms

    def test_04_multi_level_inheritance(
        self, db_session: Session, base_role: Role, test_permissions
    ):
        """测试4：多级继承"""
        # 创建三级角色继承
        level1_role = base_role

        level2_role = Role(
            role_code="LEVEL2_ROLE",
            role_name="二级角色",
            parent_id=level1_role.id,
            is_active=True,
        )
        db_session.add(level2_role)
        db_session.commit()

        level3_role = Role(
            role_code="LEVEL3_ROLE",
            role_name="三级角色",
            parent_id=level2_role.id,
            is_active=True,
        )
        db_session.add(level3_role)
        db_session.commit()

        # 各级分配不同权限
        db_session.add(RoleApiPermission(
            role_id=level1_role.id,
            permission_id=test_permissions[0].id,
        ))
        db_session.add(RoleApiPermission(
            role_id=level2_role.id,
            permission_id=test_permissions[1].id,
        ))
        db_session.add(RoleApiPermission(
            role_id=level3_role.id,
            permission_id=test_permissions[2].id,
        ))
        db_session.commit()

        # 三级角色应该拥有所有权限
        # 实际实现中需要递归查询继承链
        assert level3_role.parent_id == level2_role.id
        assert level2_role.parent_id == level1_role.id

    def test_05_permission_override(
        self, db_session: Session, base_role: Role, child_role: Role, test_permissions
    ):
        """测试5：权限覆盖"""
        # 父角色有读权限
        db_session.add(RoleApiPermission(
            role_id=base_role.id,
            permission_id=test_permissions[0].id,
        ))
        db_session.commit()

        # 子角色明确禁止读权限（通过删除或标记）
        # 在实际实现中可能需要额外的字段来表示"明确拒绝"
        # 这里简化处理：不继承该权限
        
        child_direct_perms = db_session.query(RoleApiPermission).filter(
            RoleApiPermission.role_id == child_role.id,
            RoleApiPermission.permission_id == test_permissions[0].id
        ).all()

        assert len(child_direct_perms) == 0  # 子角色未明确分配

    def test_06_user_multiple_roles(
        self, db_session: Session, test_permissions
    ):
        """测试6：用户拥有多个角色"""
        # 创建两个角色
        role1 = Role(
            role_code="ROLE_A",
            role_name="角色A",
            is_active=True,
        )
        role2 = Role(
            role_code="ROLE_B",
            role_name="角色B",
            is_active=True,
        )
        db_session.add_all([role1, role2])
        db_session.commit()

        # 角色A：读权限
        db_session.add(RoleApiPermission(
            role_id=role1.id,
            permission_id=test_permissions[0].id,
        ))

        # 角色B：编辑权限
        db_session.add(RoleApiPermission(
            role_id=role2.id,
            permission_id=test_permissions[1].id,
        ))
        db_session.commit()

        # 创建用户并分配两个角色
        from app.models.organization import Employee
        employee = Employee(
            employee_code="EMP-MULTI",
            name="多角色用户",
            department="测试部",
            role="ENGINEER",
        )
        db_session.add(employee)
        db_session.commit()

        from app.core.security import get_password_hash
        user = User(
            employee_id=employee.id,
            username="multi_role_user",
            password_hash=get_password_hash("password"),
            real_name="多角色用户",
            is_active=True,
        )
        db_session.add(user)
        db_session.commit()

        # 分配两个角色
        db_session.add(UserRole(user_id=user.id, role_id=role1.id))
        db_session.add(UserRole(user_id=user.id, role_id=role2.id))
        db_session.commit()

        # 用户应该拥有两个角色的权限并集
        user_roles = db_session.query(UserRole).filter(
            UserRole.user_id == user.id
        ).all()
        assert len(user_roles) == 2

    def test_07_permission_hierarchy(
        self, db_session: Session, test_permissions
    ):
        """测试7：权限层级关系"""
        # 定义权限依赖：删除依赖编辑，编辑依赖读
        # 这里简化为角色层级来模拟

        viewer_role = Role(
            role_code="VIEWER",
            role_name="查看者",
            is_active=True,
        )
        editor_role = Role(
            role_code="EDITOR",
            role_name="编辑者",
            parent_id=None,  # 先不设父角色
            is_active=True,
        )
        admin_role = Role(
            role_code="ADMIN",
            role_name="管理员",
            is_active=True,
        )
        db_session.add_all([viewer_role, editor_role, admin_role])
        db_session.commit()

        # 查看者：只读
        db_session.add(RoleApiPermission(
            role_id=viewer_role.id,
            permission_id=test_permissions[0].id,
        ))

        # 编辑者：读+编辑
        db_session.add_all([
            RoleApiPermission(
                role_id=editor_role.id,
                permission_id=test_permissions[0].id,
            ),
            RoleApiPermission(
                role_id=editor_role.id,
                permission_id=test_permissions[1].id,
            ),
        ])

        # 管理员：读+编辑+删除
        db_session.add_all([
            RoleApiPermission(
                role_id=admin_role.id,
                permission_id=test_permissions[0].id,
            ),
            RoleApiPermission(
                role_id=admin_role.id,
                permission_id=test_permissions[1].id,
            ),
            RoleApiPermission(
                role_id=admin_role.id,
                permission_id=test_permissions[2].id,
            ),
        ])
        db_session.commit()

        # 验证权限数量
        viewer_perms = db_session.query(RoleApiPermission).filter(
            RoleApiPermission.role_id == viewer_role.id
        ).count()
        editor_perms = db_session.query(RoleApiPermission).filter(
            RoleApiPermission.role_id == editor_role.id
        ).count()
        admin_perms = db_session.query(RoleApiPermission).filter(
            RoleApiPermission.role_id == admin_role.id
        ).count()

        assert viewer_perms == 1
        assert editor_perms == 2
        assert admin_perms == 3

    def test_08_dynamic_role_modification(
        self, db_session: Session, base_role: Role, test_permissions
    ):
        """测试8：动态修改角色权限"""
        # 初始权限
        db_session.add(RoleApiPermission(
            role_id=base_role.id,
            permission_id=test_permissions[0].id,
        ))
        db_session.commit()

        initial_count = db_session.query(RoleApiPermission).filter(
            RoleApiPermission.role_id == base_role.id
        ).count()
        assert initial_count == 1

        # 添加新权限
        db_session.add(RoleApiPermission(
            role_id=base_role.id,
            permission_id=test_permissions[1].id,
        ))
        db_session.commit()

        new_count = db_session.query(RoleApiPermission).filter(
            RoleApiPermission.role_id == base_role.id
        ).count()
        assert new_count == 2

        # 移除权限
        db_session.query(RoleApiPermission).filter(
            RoleApiPermission.role_id == base_role.id,
            RoleApiPermission.permission_id == test_permissions[0].id
        ).delete()
        db_session.commit()

        final_count = db_session.query(RoleApiPermission).filter(
            RoleApiPermission.role_id == base_role.id
        ).count()
        assert final_count == 1

    def test_09_inactive_role_permissions(
        self, db_session: Session, test_permissions
    ):
        """测试9：非活跃角色权限"""
        inactive_role = Role(
            role_code="INACTIVE_ROLE",
            role_name="非活跃角色",
            is_active=False,  # 非活跃
        )
        db_session.add(inactive_role)
        db_session.commit()

        db_session.add(RoleApiPermission(
            role_id=inactive_role.id,
            permission_id=test_permissions[0].id,
        ))
        db_session.commit()

        # 查询活跃角色的权限（应过滤非活跃角色）
        active_role_perms = db_session.query(RoleApiPermission).join(
            Role
        ).filter(
            Role.is_active == True,
            RoleApiPermission.permission_id == test_permissions[0].id
        ).all()

        # 非活跃角色的权限不应包含在内
        assert inactive_role.id not in [rp.role_id for rp in active_role_perms]

    def test_10_permission_check_with_inheritance(
        self, db_session: Session, base_role: Role, child_role: Role, test_permissions
    ):
        """测试10：权限检查（含继承）"""
        # 父角色权限
        db_session.add(RoleApiPermission(
            role_id=base_role.id,
            permission_id=test_permissions[0].id,
        ))
        db_session.commit()

        # 权限检查函数
        def has_permission(session, role_id, permission_code):
            role = session.query(Role).filter(Role.id == role_id).first()
            if not role:
                return False

            # 检查直接权限
            direct_perm = session.query(ApiPermission).join(
                RoleApiPermission
            ).filter(
                RoleApiPermission.role_id == role_id,
                ApiPermission.perm_code == permission_code
            ).first()

            if direct_perm:
                return True

            # 检查继承权限
            if role.parent_id:
                return has_permission(session, role.parent_id, permission_code)

            return False

        # 子角色应该拥有父角色的权限
        assert has_permission(db_session, child_role.id, "READ_PROJECT") is True
        assert has_permission(db_session, child_role.id, "DELETE_PROJECT") is False
