# -*- coding: utf-8 -*-
"""
角色继承功能测试

测试场景：
1. 单级继承
2. 多级继承（2层、3层、4层）
3. 权限合并
4. 循环继承检测
5. inherit_permissions 标志测试
6. 缓存机制测试
7. 多租户隔离测试
8. 边界情况测试
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base
from app.models.user import ApiPermission, Role, RoleApiPermission
from app.models.tenant import Tenant
from app.utils.role_inheritance_utils import RoleInheritanceUtils


# ========== 测试固件 ==========


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()


@pytest.fixture(autouse=True)
def clear_inheritance_cache():
    """每个测试前后清除角色继承缓存，防止测试间污染"""
    RoleInheritanceUtils.clear_cache()
    yield
    RoleInheritanceUtils.clear_cache()


@pytest.fixture(scope="function")
def test_tenant(db_session):
    """创建测试租户"""
    tenant = Tenant(id=1, tenant_name="测试租户", tenant_code="test_tenant", status="active")
    db_session.add(tenant)
    db_session.commit()
    return tenant


@pytest.fixture(scope="function")
def test_permissions(db_session, test_tenant):
    """创建测试权限"""
    permissions = []

    # 系统级权限（所有租户可用）
    for i in range(1, 6):
        perm = ApiPermission(
            id=i,
            tenant_id=None,
            perm_code=f"system:perm{i}",
            perm_name=f"系统权限{i}",
            module="system",
            is_active=True,
            is_system=True,
        )
        permissions.append(perm)

    # 租户级权限
    for i in range(6, 11):
        perm = ApiPermission(
            id=i,
            tenant_id=test_tenant.id,
            perm_code=f"tenant:perm{i}",
            perm_name=f"租户权限{i}",
            module="tenant",
            is_active=True,
            is_system=False,
        )
        permissions.append(perm)

    db_session.add_all(permissions)
    db_session.commit()
    return permissions


# ========== 测试用例 ==========


class TestRoleInheritanceBasic:
    """基础继承测试"""

    def test_01_single_level_inheritance(self, db_session, test_permissions):
        """测试1：单级继承 - 子角色继承父角色权限"""
        # 创建父角色
        parent_role = Role(
            id=1,
            role_code="parent",
            role_name="父角色",
            parent_id=None,
            inherit_permissions=False,
            is_active=True,
        )
        db_session.add(parent_role)

        # 父角色拥有权限1和2
        db_session.add(
            RoleApiPermission(role_id=1, permission_id=1)
        )  # system:perm1
        db_session.add(
            RoleApiPermission(role_id=1, permission_id=2)
        )  # system:perm2

        # 创建子角色
        child_role = Role(
            id=2,
            role_code="child",
            role_name="子角色",
            parent_id=1,
            inherit_permissions=True,  # 继承父角色权限
            is_active=True,
        )
        db_session.add(child_role)

        # 子角色拥有权限3
        db_session.add(
            RoleApiPermission(role_id=2, permission_id=3)
        )  # system:perm3

        db_session.commit()

        # 测试子角色的继承权限
        child_perms = RoleInheritanceUtils.get_inherited_permissions(db_session, 2)
        assert "system:perm1" in child_perms  # 继承自父角色
        assert "system:perm2" in child_perms  # 继承自父角色
        assert "system:perm3" in child_perms  # 自有权限
        assert len(child_perms) == 3

    def test_02_no_inheritance_flag(self, db_session, test_permissions):
        """测试2：inherit_permissions=False 时不继承"""
        # 创建父角色
        parent_role = Role(
            id=1,
            role_code="parent",
            role_name="父角色",
            parent_id=None,
            inherit_permissions=False,
            is_active=True,
        )
        db_session.add(parent_role)
        db_session.add(RoleApiPermission(role_id=1, permission_id=1))

        # 创建子角色（不继承）
        child_role = Role(
            id=2,
            role_code="child",
            role_name="子角色",
            parent_id=1,
            inherit_permissions=False,  # 不继承
            is_active=True,
        )
        db_session.add(child_role)
        db_session.add(RoleApiPermission(role_id=2, permission_id=2))

        db_session.commit()

        # 测试子角色只有自己的权限
        child_perms = RoleInheritanceUtils.get_inherited_permissions(db_session, 2)
        assert "system:perm1" not in child_perms  # 不继承
        assert "system:perm2" in child_perms  # 自有权限
        assert len(child_perms) == 1

    def test_03_two_level_inheritance(self, db_session, test_permissions):
        """测试3：两层继承 (Level 0 -> 1 -> 2)"""
        # Level 0: 祖父角色
        grandparent = Role(
            id=1,
            role_code="grandparent",
            role_name="祖父角色",
            parent_id=None,
            inherit_permissions=False,
            is_active=True,
        )
        db_session.add(grandparent)
        db_session.add(RoleApiPermission(role_id=1, permission_id=1))

        # Level 1: 父角色
        parent = Role(
            id=2,
            role_code="parent",
            role_name="父角色",
            parent_id=1,
            inherit_permissions=True,
            is_active=True,
        )
        db_session.add(parent)
        db_session.add(RoleApiPermission(role_id=2, permission_id=2))

        # Level 2: 子角色
        child = Role(
            id=3,
            role_code="child",
            role_name="子角色",
            parent_id=2,
            inherit_permissions=True,
            is_active=True,
        )
        db_session.add(child)
        db_session.add(RoleApiPermission(role_id=3, permission_id=3))

        db_session.commit()

        # 子角色应该有所有权限
        child_perms = RoleInheritanceUtils.get_inherited_permissions(db_session, 3)
        assert "system:perm1" in child_perms  # 继承自祖父
        assert "system:perm2" in child_perms  # 继承自父
        assert "system:perm3" in child_perms  # 自有
        assert len(child_perms) == 3

    def test_04_three_level_inheritance(self, db_session, test_permissions):
        """测试4：三层继承 (Level 0 -> 1 -> 2 -> 3)"""
        # 创建4级角色
        roles_data = [
            (1, "level0", None, False, 1),  # Level 0
            (2, "level1", 1, True, 2),  # Level 1
            (3, "level2", 2, True, 3),  # Level 2
            (4, "level3", 3, True, 4),  # Level 3
        ]

        for role_id, code, parent_id, inherit, perm_id in roles_data:
            role = Role(
                id=role_id,
                role_code=code,
                role_name=f"角色{code}",
                parent_id=parent_id,
                inherit_permissions=inherit,
                is_active=True,
            )
            db_session.add(role)
            db_session.add(RoleApiPermission(role_id=role_id, permission_id=perm_id))

        db_session.commit()

        # Level 3 角色应该有所有权限
        level3_perms = RoleInheritanceUtils.get_inherited_permissions(db_session, 4)
        assert len(level3_perms) == 4
        assert all(f"system:perm{i}" in level3_perms for i in range(1, 5))

    def test_05_middle_level_no_inherit(self, db_session, test_permissions):
        """测试5：中间层不继承时，停止继承链"""
        # Level 0
        role0 = Role(
            id=1,
            role_code="level0",
            role_name="Level0",
            parent_id=None,
            inherit_permissions=False,
            is_active=True,
        )
        db_session.add(role0)
        db_session.add(RoleApiPermission(role_id=1, permission_id=1))

        # Level 1 (不继承)
        role1 = Role(
            id=2,
            role_code="level1",
            role_name="Level1",
            parent_id=1,
            inherit_permissions=False,  # 中断继承链
            is_active=True,
        )
        db_session.add(role1)
        db_session.add(RoleApiPermission(role_id=2, permission_id=2))

        # Level 2
        role2 = Role(
            id=3,
            role_code="level2",
            role_name="Level2",
            parent_id=2,
            inherit_permissions=True,
            is_active=True,
        )
        db_session.add(role2)
        db_session.add(RoleApiPermission(role_id=3, permission_id=3))

        db_session.commit()

        # Level 2 只能继承到 Level 1，不能继承 Level 0
        perms = RoleInheritanceUtils.get_inherited_permissions(db_session, 3)
        assert "system:perm1" not in perms  # 继承链中断
        assert "system:perm2" in perms  # 可以继承父级
        assert "system:perm3" in perms  # 自有权限
        assert len(perms) == 2


class TestRoleInheritanceAdvanced:
    """高级继承测试"""

    def test_06_circular_inheritance_detection(self, db_session):
        """测试6：循环继承检测"""
        role1 = Role(
            id=1,
            role_code="role1",
            role_name="角色1",
            parent_id=None,
            inherit_permissions=True,
            is_active=True,
        )
        role2 = Role(
            id=2,
            role_code="role2",
            role_name="角色2",
            parent_id=1,
            inherit_permissions=True,
            is_active=True,
        )
        db_session.add_all([role1, role2])
        db_session.commit()

        # 检测设置循环继承
        is_circular = RoleInheritanceUtils.detect_circular_inheritance(
            db_session, 1, 2
        )  # role1 -> role2 (但 role2 已经是 role1 的子)
        assert is_circular is True

        # 正常情况
        is_circular = RoleInheritanceUtils.detect_circular_inheritance(
            db_session, 2, 1
        )  # role2 -> role1 (正常)
        assert is_circular is False

    def test_07_self_reference_detection(self, db_session):
        """测试7：自引用检测"""
        role = Role(
            id=1,
            role_code="role1",
            role_name="角色1",
            parent_id=None,
            inherit_permissions=True,
            is_active=True,
        )
        db_session.add(role)
        db_session.commit()

        # 检测自引用
        is_circular = RoleInheritanceUtils.detect_circular_inheritance(
            db_session, 1, 1
        )
        assert is_circular is True

    def test_08_role_chain_calculation(self, db_session):
        """测试8：继承链计算"""
        # 创建3级角色
        for i in range(1, 4):
            role = Role(
                id=i,
                role_code=f"role{i}",
                role_name=f"角色{i}",
                parent_id=i - 1 if i > 1 else None,
                inherit_permissions=True,
                is_active=True,
            )
            db_session.add(role)
        db_session.commit()

        # 测试继承链
        chain = RoleInheritanceUtils.get_role_chain(db_session, 3)
        assert len(chain) == 3
        assert chain[0].id == 3  # 子
        assert chain[1].id == 2  # 父
        assert chain[2].id == 1  # 祖父

    def test_09_level_calculation(self, db_session):
        """测试9：层级计算"""
        # 创建4级角色
        for i in range(1, 5):
            role = Role(
                id=i,
                role_code=f"role{i}",
                role_name=f"角色{i}",
                parent_id=i - 1 if i > 1 else None,
                inherit_permissions=True,
                is_active=True,
            )
            db_session.add(role)
        db_session.commit()

        # 测试层级
        assert RoleInheritanceUtils.calculate_role_level(db_session, 1) == 0  # Level 0
        assert RoleInheritanceUtils.calculate_role_level(db_session, 2) == 1  # Level 1
        assert RoleInheritanceUtils.calculate_role_level(db_session, 3) == 2  # Level 2
        assert RoleInheritanceUtils.calculate_role_level(db_session, 4) == 3  # Level 3

    def test_10_multi_tenant_isolation(
        self, db_session, test_tenant, test_permissions
    ):
        """测试10：多租户权限隔离"""
        # 创建另一个租户
        tenant2 = Tenant(id=2, tenant_name="租户2", tenant_code="tenant2", status="active")
        db_session.add(tenant2)

        # 租户2的权限
        perm_t2 = ApiPermission(
            id=20,
            tenant_id=2,
            perm_code="tenant2:perm1",
            perm_name="租户2权限",
            module="tenant2",
            is_active=True,
        )
        db_session.add(perm_t2)

        # 创建角色（属于租户1）
        role = Role(
            id=1,
            tenant_id=1,
            role_code="role1",
            role_name="租户1角色",
            parent_id=None,
            inherit_permissions=True,
            is_active=True,
        )
        db_session.add(role)

        # 分配系统权限和租户1权限
        db_session.add(RoleApiPermission(role_id=1, permission_id=1))  # 系统权限
        db_session.add(RoleApiPermission(role_id=1, permission_id=6))  # 租户1权限
        db_session.add(RoleApiPermission(role_id=1, permission_id=20))  # 租户2权限

        db_session.commit()

        # 获取租户1视角的权限（应该过滤掉租户2的权限）
        perms = RoleInheritanceUtils.get_inherited_permissions(
            db_session, 1, tenant_id=1
        )
        assert "system:perm1" in perms  # 系统权限可见
        assert "tenant:perm6" in perms  # 租户1权限可见
        assert "tenant2:perm1" not in perms  # 租户2权限不可见


class TestRoleInheritancePerformance:
    """性能和缓存测试"""

    def test_11_permission_caching(self, db_session, test_permissions):
        """测试11：权限缓存机制"""
        # 创建角色
        role = Role(
            id=1,
            role_code="role1",
            role_name="角色1",
            parent_id=None,
            inherit_permissions=True,
            is_active=True,
        )
        db_session.add(role)
        db_session.add(RoleApiPermission(role_id=1, permission_id=1))
        db_session.commit()

        # 清除缓存
        RoleInheritanceUtils.clear_cache()

        # 第一次查询（应该查询数据库）
        perms1 = RoleInheritanceUtils.get_inherited_permissions(db_session, 1)

        # 第二次查询（应该从缓存读取）
        perms2 = RoleInheritanceUtils.get_inherited_permissions(db_session, 1)

        assert perms1 == perms2
        assert len(RoleInheritanceUtils._permission_cache) > 0

    def test_12_cache_invalidation(self, db_session, test_permissions):
        """测试12：缓存失效"""
        role = Role(
            id=1,
            role_code="role1",
            role_name="角色1",
            parent_id=None,
            inherit_permissions=True,
            is_active=True,
        )
        db_session.add(role)
        db_session.commit()

        # 获取权限（缓存）
        RoleInheritanceUtils.get_inherited_permissions(db_session, 1)

        # 清除特定角色缓存
        RoleInheritanceUtils.clear_cache(1)

        assert 1 not in RoleInheritanceUtils._permission_cache

    def test_13_merge_multiple_roles(self, db_session, test_permissions):
        """测试13：合并多个角色的权限"""
        # 创建3个角色，各有不同权限
        for i in range(1, 4):
            role = Role(
                id=i,
                role_code=f"role{i}",
                role_name=f"角色{i}",
                parent_id=None,
                inherit_permissions=False,
                is_active=True,
            )
            db_session.add(role)
            db_session.add(RoleApiPermission(role_id=i, permission_id=i))

        db_session.commit()

        # 合并权限
        merged = RoleInheritanceUtils.merge_role_permissions(db_session, [1, 2, 3])
        assert len(merged) == 3
        assert "system:perm1" in merged
        assert "system:perm2" in merged
        assert "system:perm3" in merged


class TestRoleInheritanceValidation:
    """验证和统计测试"""

    def test_14_validate_hierarchy_valid(self, db_session):
        """测试14：验证正常的角色层级"""
        # 创建正常的3级层级
        for i in range(1, 4):
            role = Role(
                id=i,
                role_code=f"role{i}",
                role_name=f"角色{i}",
                parent_id=i - 1 if i > 1 else None,
                inherit_permissions=True,
                is_active=True,
            )
            db_session.add(role)
        db_session.commit()

        is_valid, errors = RoleInheritanceUtils.validate_role_hierarchy(db_session)
        assert is_valid is True
        assert len(errors) == 0

    def test_15_validate_hierarchy_invalid_parent(self, db_session):
        """测试15：验证无效的父角色ID"""
        role = Role(
            id=1,
            role_code="role1",
            role_name="角色1",
            parent_id=999,  # 不存在的父角色
            inherit_permissions=True,
            is_active=True,
        )
        db_session.add(role)
        db_session.commit()

        is_valid, errors = RoleInheritanceUtils.validate_role_hierarchy(db_session)
        assert is_valid is False
        assert len(errors) > 0
        assert "不存在" in errors[0]

    def test_16_statistics(self, db_session):
        """测试16：继承统计信息"""
        # 创建混合角色结构
        role1 = Role(
            id=1,
            role_code="root",
            role_name="根角色",
            parent_id=None,
            inherit_permissions=False,
            is_active=True,
        )
        role2 = Role(
            id=2,
            role_code="child1",
            role_name="子角色1",
            parent_id=1,
            inherit_permissions=True,
            is_active=True,
        )
        role3 = Role(
            id=3,
            role_code="child2",
            role_name="子角色2",
            parent_id=1,
            inherit_permissions=False,
            is_active=True,
        )
        db_session.add_all([role1, role2, role3])
        db_session.commit()

        stats = RoleInheritanceUtils.get_inheritance_statistics(db_session)
        assert stats["total_roles"] == 3
        assert stats["root_roles"] == 1
        assert stats["inherited_roles"] == 1  # 只有 child1 继承
        assert stats["non_inherited_roles"] == 1  # child2 不继承

    def test_17_tree_data_generation(self, db_session, test_permissions):
        """测试17：角色树数据生成"""
        # 创建树状结构
        role1 = Role(
            id=1,
            role_code="root",
            role_name="根角色",
            parent_id=None,
            inherit_permissions=False,
            is_active=True,
        )
        role2 = Role(
            id=2,
            role_code="child",
            role_name="子角色",
            parent_id=1,
            inherit_permissions=True,
            is_active=True,
        )
        db_session.add_all([role1, role2])
        db_session.add(RoleApiPermission(role_id=1, permission_id=1))
        db_session.add(RoleApiPermission(role_id=2, permission_id=2))
        db_session.commit()

        tree = RoleInheritanceUtils.get_role_tree_data(db_session)
        assert len(tree) == 1  # 一个根节点
        assert tree[0]["code"] == "root"
        assert len(tree[0]["children"]) == 1
        assert tree[0]["children"][0]["code"] == "child"


class TestEdgeCases:
    """边界情况测试"""

    def test_18_empty_role(self, db_session):
        """测试18：空角色（无权限）"""
        role = Role(
            id=1,
            role_code="empty",
            role_name="空角色",
            parent_id=None,
            inherit_permissions=True,
            is_active=True,
        )
        db_session.add(role)
        db_session.commit()

        perms = RoleInheritanceUtils.get_inherited_permissions(db_session, 1)
        assert len(perms) == 0

    def test_19_inactive_role(self, db_session, test_permissions):
        """测试19：非活跃角色"""
        role = Role(
            id=1,
            role_code="inactive",
            role_name="非活跃角色",
            parent_id=None,
            inherit_permissions=True,
            is_active=False,  # 非活跃
        )
        db_session.add(role)
        db_session.add(RoleApiPermission(role_id=1, permission_id=1))
        db_session.commit()

        # 统计时应该被排除
        stats = RoleInheritanceUtils.get_inheritance_statistics(db_session)
        assert stats["total_roles"] == 0

    def test_20_duplicate_permissions(self, db_session, test_permissions):
        """测试20：重复权限（父子都有同一权限）"""
        parent = Role(
            id=1,
            role_code="parent",
            role_name="父角色",
            parent_id=None,
            inherit_permissions=False,
            is_active=True,
        )
        child = Role(
            id=2,
            role_code="child",
            role_name="子角色",
            parent_id=1,
            inherit_permissions=True,
            is_active=True,
        )
        db_session.add_all([parent, child])
        # 父子都有 perm1
        db_session.add(RoleApiPermission(role_id=1, permission_id=1))
        db_session.add(RoleApiPermission(role_id=2, permission_id=1))
        db_session.commit()

        perms = RoleInheritanceUtils.get_inherited_permissions(db_session, 2)
        # 应该去重，只有1个 perm1
        assert len(perms) == 1
        assert "system:perm1" in perms


# ========== 运行测试 ==========

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
