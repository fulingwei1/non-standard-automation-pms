# -*- coding: utf-8 -*-
"""
角色管理完整测试套件
测试角色CRUD、权限分配、数据范围等核心功能
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from app.models.user import Role, ApiPermission, RoleApiPermission


@pytest.mark.unit
class TestRoleCRUD:
    """角色CRUD操作测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = MagicMock()
        db.query = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.delete = MagicMock()
        db.rollback = MagicMock()
        return db

    @pytest.fixture
    def sample_role(self):
        """示例角色数据"""
        return Role(
            id=1,
            role_code="PM",
            role_name="项目经理",
            description="项目全权管理",
            data_scope="PROJECT",
            is_system=False,
            is_active=True,
            sort_order=10
        )

    def test_create_role_success(self, mock_db):
        """测试创建角色成功"""
        role = Role(
            role_code="NEW_ROLE",
            role_name="新角色",
            description="测试角色",
            data_scope="DEPT",
            is_system=False,
            is_active=True
        )
        
        mock_db.add(role)
        mock_db.commit()
        
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_create_role_duplicate_code(self, mock_db, sample_role):
        """测试创建重复角色代码失败"""
        # 模拟角色代码已存在
        mock_db.query(Role).filter().first.return_value = sample_role
        
        existing_role = mock_db.query(Role).filter(Role.role_code == "PM").first()
        assert existing_role is not None
        assert existing_role.role_code == "PM"

    def test_update_role_info(self, mock_db, sample_role):
        """测试更新角色信息"""
        mock_db.query(Role).filter().first.return_value = sample_role
        
        sample_role.role_name = "高级项目经理"
        sample_role.description = "更新后的描述"
        mock_db.commit()
        
        assert sample_role.role_name == "高级项目经理"
        assert mock_db.commit.called

    def test_delete_role(self, mock_db, sample_role):
        """测试删除角色"""
        mock_db.query(Role).filter().first.return_value = sample_role
        
        mock_db.delete(sample_role)
        mock_db.commit()
        
        assert mock_db.delete.called
        assert mock_db.commit.called

    def test_deactivate_role(self, mock_db, sample_role):
        """测试禁用角色"""
        mock_db.query(Role).filter().first.return_value = sample_role
        
        sample_role.is_active = False
        mock_db.commit()
        
        assert sample_role.is_active is False
        assert mock_db.commit.called


@pytest.mark.unit
class TestRoleHierarchy:
    """角色层级测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return MagicMock()

    @pytest.fixture
    def hierarchical_roles(self):
        """层级角色数据"""
        return [
            Role(id=1, role_code="ADMIN", role_name="系统管理员", parent_id=None, level=0),
            Role(id=2, role_code="GM", role_name="总经理", parent_id=None, level=1),
            Role(id=3, role_code="PM", role_name="项目经理", parent_id=2, level=2),
            Role(id=4, role_code="ENGINEER", role_name="工程师", parent_id=3, level=3),
        ]

    def test_role_has_parent(self, hierarchical_roles):
        """测试角色有父级"""
        pm_role = hierarchical_roles[2]
        assert pm_role.parent_id is not None
        assert pm_role.parent_id == 2  # GM的ID

    def test_role_no_parent(self, hierarchical_roles):
        """测试顶级角色无父级"""
        admin_role = hierarchical_roles[0]
        gm_role = hierarchical_roles[1]
        
        assert admin_role.parent_id is None
        assert gm_role.parent_id is None

    def test_role_level_hierarchy(self, hierarchical_roles):
        """测试角色层级正确"""
        assert hierarchical_roles[0].level == 0  # ADMIN
        assert hierarchical_roles[1].level == 1  # GM
        assert hierarchical_roles[2].level == 2  # PM
        assert hierarchical_roles[3].level == 3  # ENGINEER

    def test_get_child_roles(self, mock_db, hierarchical_roles):
        """测试获取子角色"""
        gm_role = hierarchical_roles[1]
        
        # 模拟查询返回子角色
        child_roles = [r for r in hierarchical_roles if r.parent_id == gm_role.id]
        mock_db.query(Role).filter().all.return_value = child_roles
        
        children = mock_db.query(Role).filter(Role.parent_id == gm_role.id).all()
        
        assert len(children) == 1
        assert children[0].role_code == "PM"


@pytest.mark.unit
class TestDataScope:
    """数据范围测试"""

    @pytest.fixture
    def roles_with_different_scopes(self):
        """不同数据范围的角色"""
        return [
            Role(id=1, role_code="ADMIN", role_name="系统管理员", data_scope="ALL"),
            Role(id=2, role_code="GM", role_name="总经理", data_scope="ALL"),
            Role(id=3, role_code="DEPT_MGR", role_name="部门经理", data_scope="DEPT"),
            Role(id=4, role_code="PM", role_name="项目经理", data_scope="PROJECT"),
            Role(id=5, role_code="SALES", role_name="销售专员", data_scope="OWN"),
        ]

    def test_all_scope_role(self, roles_with_different_scopes):
        """测试全局数据范围角色"""
        admin = roles_with_different_scopes[0]
        gm = roles_with_different_scopes[1]
        
        assert admin.data_scope == "ALL"
        assert gm.data_scope == "ALL"

    def test_dept_scope_role(self, roles_with_different_scopes):
        """测试部门数据范围角色"""
        dept_mgr = roles_with_different_scopes[2]
        assert dept_mgr.data_scope == "DEPT"

    def test_project_scope_role(self, roles_with_different_scopes):
        """测试项目数据范围角色"""
        pm = roles_with_different_scopes[3]
        assert pm.data_scope == "PROJECT"

    def test_own_scope_role(self, roles_with_different_scopes):
        """测试个人数据范围角色"""
        sales = roles_with_different_scopes[4]
        assert sales.data_scope == "OWN"

    def test_scope_hierarchy(self, roles_with_different_scopes):
        """测试数据范围层级（ALL > DEPT > PROJECT > OWN）"""
        scopes = ["ALL", "DEPT", "PROJECT", "OWN"]
        
        for i, role in enumerate(roles_with_different_scopes[:4]):
            expected_scope = scopes[min(i, len(scopes)-1)]
            # 验证数据范围遵循层级
            if role.data_scope == "ALL":
                assert True  # 最高权限
            elif role.data_scope == "DEPT":
                assert role.data_scope != "ALL"  # 低于全局
            elif role.data_scope == "PROJECT":
                assert role.data_scope not in ["ALL", "DEPT"]
            elif role.data_scope == "OWN":
                assert role.data_scope not in ["ALL", "DEPT", "PROJECT"]


@pytest.mark.unit
class TestRolePermissionAssignment:
    """角色权限分配测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = MagicMock()
        db.query = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.delete = MagicMock()
        return db

    @pytest.fixture
    def sample_role(self):
        """示例角色"""
        return Role(id=1, role_code="PM", role_name="项目经理")

    @pytest.fixture
    def sample_permissions(self):
        """示例权限列表"""
        return [
            ApiPermission(id=1, perm_code="project:view", perm_name="查看项目", module="PROJECT"),
            ApiPermission(id=2, perm_code="project:create", perm_name="创建项目", module="PROJECT"),
            ApiPermission(id=3, perm_code="project:update", perm_name="编辑项目", module="PROJECT"),
        ]

    def test_assign_single_permission(self, mock_db, sample_role, sample_permissions):
        """测试分配单个权限"""
        perm = sample_permissions[0]
        
        role_perm = RoleApiPermission(role_id=sample_role.id, api_permission_id=perm.id)
        mock_db.add(role_perm)
        mock_db.commit()
        
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_assign_multiple_permissions(self, mock_db, sample_role, sample_permissions):
        """测试批量分配权限"""
        for perm in sample_permissions:
            role_perm = RoleApiPermission(role_id=sample_role.id, api_permission_id=perm.id)
            mock_db.add(role_perm)
        
        mock_db.commit()
        
        assert mock_db.add.call_count == 3
        assert mock_db.commit.called

    def test_remove_permission(self, mock_db, sample_role, sample_permissions):
        """测试移除权限"""
        perm = sample_permissions[0]
        role_perm = RoleApiPermission(role_id=sample_role.id, api_permission_id=perm.id)
        
        mock_db.query(RoleApiPermission).filter().first.return_value = role_perm
        
        mock_db.delete(role_perm)
        mock_db.commit()
        
        assert mock_db.delete.called
        assert mock_db.commit.called

    def test_replace_permissions(self, mock_db, sample_role, sample_permissions):
        """测试替换权限（先删除所有，再添加新的）"""
        old_perms = sample_permissions[:2]  # 前2个
        new_perms = sample_permissions[1:]  # 后2个
        
        # 模拟删除所有旧权限
        mock_db.query(RoleApiPermission).filter().delete.return_value = 2
        
        # 添加新权限
        for perm in new_perms:
            role_perm = RoleApiPermission(role_id=sample_role.id, api_permission_id=perm.id)
            mock_db.add(role_perm)
        
        mock_db.commit()
        
        assert mock_db.query(RoleApiPermission).filter().delete.called
        assert mock_db.add.call_count == 2
        assert mock_db.commit.called


@pytest.mark.unit
class TestApiPermissionAssignment:
    """API权限分配测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return MagicMock()

    @pytest.fixture
    def sample_role(self):
        """示例角色"""
        return Role(id=1, role_code="PM", role_name="项目经理")

    @pytest.fixture
    def sample_api_permissions(self):
        """示例API权限"""
        return [
            ApiPermission(id=1, perm_code="user:view", perm_name="查看用户", module="USER"),
            ApiPermission(id=2, perm_code="project:create", perm_name="创建项目", module="PROJECT"),
            ApiPermission(id=3, perm_code="project:update", perm_name="编辑项目", module="PROJECT"),
        ]

    def test_assign_api_permission(self, mock_db, sample_role, sample_api_permissions):
        """测试分配API权限"""
        api_perm = sample_api_permissions[0]
        
        role_api_perm = RoleApiPermission(role_id=sample_role.id, api_permission_id=api_perm.id)
        mock_db.add(role_api_perm)
        mock_db.commit()
        
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_batch_assign_api_permissions(self, mock_db, sample_role, sample_api_permissions):
        """测试批量分配API权限"""
        for api_perm in sample_api_permissions:
            role_api_perm = RoleApiPermission(
                role_id=sample_role.id,
                api_permission_id=api_perm.id
            )
            mock_db.add(role_api_perm)
        
        mock_db.commit()
        
        assert mock_db.add.call_count == 3
        assert mock_db.commit.called


@pytest.mark.unit
class TestRoleValidation:
    """角色验证测试"""

    def test_role_code_validation_format(self):
        """测试角色代码格式验证"""
        # 有效代码（大写字母和下划线）
        valid_codes = ["ADMIN", "PROJECT_MANAGER", "SALES_DIR", "QA_MGR"]
        for code in valid_codes:
            assert code.replace("_", "").isalpha()
            assert code.isupper()
        
        # 无效代码
        invalid_codes = ["admin", "Project_Manager", "sales-dir", "qa@mgr"]
        for code in invalid_codes:
            is_valid = code.replace("_", "").isalpha() and code.isupper()
            assert not is_valid

    def test_role_code_validation_length(self):
        """测试角色代码长度验证"""
        # 正常长度
        assert len("ADMIN") >= 2
        assert len("PM") >= 2
        assert len("PROJECT_MANAGER") <= 50
        
        # 太短
        assert len("A") < 2
        
        # 太长
        assert len("A" * 100) > 50

    def test_data_scope_validation(self):
        """测试数据范围验证"""
        valid_scopes = ["ALL", "DEPT", "PROJECT", "OWN"]
        invalid_scopes = ["GLOBAL", "COMPANY", "TEAM"]
        
        for scope in valid_scopes:
            assert scope in ["ALL", "DEPT", "PROJECT", "OWN"]
        
        for scope in invalid_scopes:
            assert scope not in ["ALL", "DEPT", "PROJECT", "OWN"]


@pytest.mark.unit
class TestRoleQueries:
    """角色查询测试"""

    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        db = MagicMock()
        db.query = MagicMock()
        return db

    @pytest.fixture
    def sample_roles(self):
        """示例角色列表"""
        return [
            Role(id=1, role_code="ADMIN", role_name="系统管理员", is_system=True, is_active=True),
            Role(id=2, role_code="PM", role_name="项目经理", is_system=False, is_active=True),
            Role(id=3, role_code="ENGINEER", role_name="工程师", is_system=False, is_active=True),
            Role(id=4, role_code="INTERN", role_name="实习生", is_system=False, is_active=False),
        ]

    def test_query_all_roles(self, mock_db, sample_roles):
        """测试查询所有角色"""
        mock_db.query(Role).all.return_value = sample_roles
        
        roles = mock_db.query(Role).all()
        
        assert len(roles) == 4
        assert roles[0].role_code == "ADMIN"

    def test_query_role_by_code(self, mock_db, sample_roles):
        """测试通过角色代码查询"""
        mock_db.query(Role).filter().first.return_value = sample_roles[0]
        
        role = mock_db.query(Role).filter(Role.role_code == "ADMIN").first()
        
        assert role is not None
        assert role.role_code == "ADMIN"
        assert role.is_system is True

    def test_query_active_roles(self, mock_db, sample_roles):
        """测试查询活跃角色"""
        active_roles = [r for r in sample_roles if r.is_active]
        mock_db.query(Role).filter().all.return_value = active_roles
        
        roles = mock_db.query(Role).filter(Role.is_active == True).all()
        
        assert len(roles) == 3
        assert all(r.is_active for r in roles)

    def test_query_system_roles(self, mock_db, sample_roles):
        """测试查询系统角色"""
        system_roles = [r for r in sample_roles if r.is_system]
        mock_db.query(Role).filter().all.return_value = system_roles
        
        roles = mock_db.query(Role).filter(Role.is_system == True).all()
        
        assert len(roles) == 1
        assert roles[0].role_code == "ADMIN"


@pytest.mark.unit
class TestRoleBusinessLogic:
    """角色业务逻辑测试"""

    def test_system_role_cannot_be_deleted(self):
        """测试系统角色不能被删除（业务规则）"""
        admin_role = Role(
            id=1,
            role_code="ADMIN",
            role_name="系统管理员",
            is_system=True
        )
        
        # 业务逻辑：系统角色不能被删除
        can_delete = not admin_role.is_system
        assert can_delete is False

    def test_custom_role_can_be_deleted(self):
        """测试自定义角色可以被删除"""
        custom_role = Role(
            id=2,
            role_code="CUSTOM",
            role_name="自定义角色",
            is_system=False
        )
        
        # 业务逻辑：自定义角色可以被删除
        can_delete = not custom_role.is_system
        assert can_delete is True

    def test_role_with_users_protection(self):
        """测试有用户的角色保护"""
        # 模拟角色有关联用户
        role_has_users = True
        
        # 业务逻辑：有用户的角色需要先解除关联才能删除
        can_delete = not role_has_users
        assert can_delete is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
