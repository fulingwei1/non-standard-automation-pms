#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速验证角色继承功能

不依赖完整的测试框架，直接验证核心功能
"""

import os
import sys

# 设置环境变量
os.environ["ENVIRONMENT"] = "development"
os.environ["SECRET_KEY"] = "test_secret_key_12345678"
os.environ["SQLITE_DB_PATH"] = ":memory:"

from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

# 创建独立的Base，避免加载所有模型
Base = declarative_base()


# 简化的模型定义（仅用于测试）
class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    code = Column(String(50))
    is_active = Column(Boolean, default=True)


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    role_code = Column(String(50))
    role_name = Column(String(100))
    parent_id = Column(Integer, ForeignKey("roles.id"))
    inherit_permissions = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    
    parent = relationship("Role", remote_side=[id], backref="children")


class ApiPermission(Base):
    __tablename__ = "api_permissions"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"))
    perm_code = Column(String(100))
    perm_name = Column(String(200))
    module = Column(String(50))
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)


class RoleApiPermission(Base):
    __tablename__ = "role_api_permissions"
    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    permission_id = Column(Integer, ForeignKey("api_permissions.id"))
    created_at = Column(DateTime, default=datetime.now)


# 导入工具类（使用简化的模型）
from app.utils.role_inheritance_utils import RoleInheritanceUtils


def create_test_db():
    """创建内存测试数据库"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def test_basic_inheritance():
    """测试1：基础单级继承"""
    print("\n📋 测试1: 单级继承")
    print("-" * 60)

    RoleInheritanceUtils.clear_cache()
    db = create_test_db()

    # 创建测试权限
    perm1 = ApiPermission(
        id=1,
        perm_code="parent:perm1",
        perm_name="父权限1",
        module="test",
        is_active=True,
    )
    perm2 = ApiPermission(
        id=2,
        perm_code="child:perm2",
        perm_name="子权限2",
        module="test",
        is_active=True,
    )
    db.add_all([perm1, perm2])
    db.commit()

    # 创建父角色
    parent = Role(
        id=1,
        role_code="parent",
        role_name="父角色",
        parent_id=None,
        inherit_permissions=False,
        is_active=True,
    )
    db.add(parent)
    db.add(RoleApiPermission(role_id=1, permission_id=1))
    db.commit()

    # 创建子角色（继承）
    child = Role(
        id=2,
        role_code="child",
        role_name="子角色",
        parent_id=1,
        inherit_permissions=True,
        is_active=True,
    )
    db.add(child)
    db.add(RoleApiPermission(role_id=2, permission_id=2))
    db.commit()

    # 验证继承
    child_perms = RoleInheritanceUtils.get_inherited_permissions(db, 2)

    print(f"父角色权限: parent:perm1")
    print(f"子角色自有权限: child:perm2")
    print(f"子角色继承权限: {child_perms}")

    assert "parent:perm1" in child_perms, "❌ 子角色应该继承父角色权限"
    assert "child:perm2" in child_perms, "❌ 子角色应该保留自己的权限"
    assert len(child_perms) == 2, f"❌ 子角色应该有2个权限，实际有{len(child_perms)}个"

    print("✅ 测试通过：子角色正确继承父角色权限")

    db.close()


def test_multi_level_inheritance():
    """测试2：多级继承"""
    print("\n📋 测试2: 三级继承")
    print("-" * 60)

    RoleInheritanceUtils.clear_cache()
    db = create_test_db()

    # 创建权限
    for i in range(1, 4):
        perm = ApiPermission(
            id=i,
            perm_code=f"level{i-1}:perm",
            perm_name=f"Level{i-1}权限",
            module="test",
            is_active=True,
        )
        db.add(perm)
    db.commit()

    # 创建3级角色
    for i in range(1, 4):
        role = Role(
            id=i,
            role_code=f"level{i-1}",
            role_name=f"Level {i-1}",
            parent_id=i - 1 if i > 1 else None,
            inherit_permissions=True,
            is_active=True,
        )
        db.add(role)
        db.add(RoleApiPermission(role_id=i, permission_id=i))
    db.commit()

    # 验证 Level 2 角色的权限
    level2_perms = RoleInheritanceUtils.get_inherited_permissions(db, 3)

    print(f"Level 0 权限: level0:perm")
    print(f"Level 1 权限: level1:perm")
    print(f"Level 2 权限: level2:perm")
    print(f"Level 2 继承权限: {level2_perms}")

    assert "level0:perm" in level2_perms, "❌ 应该继承祖父角色权限"
    assert "level1:perm" in level2_perms, "❌ 应该继承父角色权限"
    assert "level2:perm" in level2_perms, "❌ 应该保留自己的权限"
    assert len(level2_perms) == 3, f"❌ 应该有3个权限，实际有{len(level2_perms)}个"

    print("✅ 测试通过：多级继承正常工作")

    db.close()


def test_no_inheritance_flag():
    """测试3：不继承标志"""
    print("\n📋 测试3: inherit_permissions=False")
    print("-" * 60)

    # 清除之前的缓存
    RoleInheritanceUtils.clear_cache()
    
    db = create_test_db()

    # 创建权限
    perm1 = ApiPermission(
        id=1, perm_code="parent:perm", perm_name="父权限", module="test", is_active=True
    )
    perm2 = ApiPermission(
        id=2, perm_code="child:perm", perm_name="子权限", module="test", is_active=True
    )
    db.add_all([perm1, perm2])
    db.commit()

    # 父角色
    parent = Role(
        id=1,
        role_code="parent",
        role_name="父角色",
        parent_id=None,
        inherit_permissions=False,
        is_active=True,
    )
    db.add(parent)
    db.add(RoleApiPermission(role_id=1, permission_id=1))
    db.commit()

    # 子角色（不继承）
    child = Role(
        id=2,
        role_code="child",
        role_name="子角色",
        parent_id=1,
        inherit_permissions=False,  # 不继承
        is_active=True,
    )
    db.add(child)
    db.add(RoleApiPermission(role_id=2, permission_id=2))
    db.commit()

    # 验证
    child_perms = RoleInheritanceUtils.get_inherited_permissions(db, 2)

    print(f"父角色权限: parent:perm")
    print(f"子角色自有权限: child:perm")
    print(f"子角色权限 (inherit=False): {child_perms}")

    assert "parent:perm" not in child_perms, "❌ 不应该继承父权限"
    assert "child:perm" in child_perms, "❌ 应该保留自己的权限"
    assert len(child_perms) == 1, f"❌ 应该只有1个权限，实际有{len(child_perms)}个"

    print("✅ 测试通过：不继承标志正常工作")

    db.close()


def test_circular_detection():
    """测试4：循环继承检测"""
    print("\n📋 测试4: 循环继承检测")
    print("-" * 60)

    RoleInheritanceUtils.clear_cache()
    db = create_test_db()

    # 创建2个角色
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
    db.add_all([role1, role2])
    db.commit()

    # 检测循环
    is_circular = RoleInheritanceUtils.detect_circular_inheritance(db, 1, 2)

    print(f"角色1 -> 角色2: {is_circular}")
    assert is_circular is True, "❌ 应该检测到循环继承"

    # 检测自引用
    is_self_circular = RoleInheritanceUtils.detect_circular_inheritance(db, 1, 1)

    print(f"角色1 -> 角色1: {is_self_circular}")
    assert is_self_circular is True, "❌ 应该检测到自引用"

    print("✅ 测试通过：循环继承检测正常")

    db.close()


def test_role_level_calculation():
    """测试5：层级计算"""
    print("\n📋 测试5: 角色层级计算")
    print("-" * 60)

    RoleInheritanceUtils.clear_cache()
    db = create_test_db()

    # 创建4级角色
    for i in range(1, 5):
        role = Role(
            id=i,
            role_code=f"level{i-1}",
            role_name=f"Level {i-1}",
            parent_id=i - 1 if i > 1 else None,
            inherit_permissions=True,
            is_active=True,
        )
        db.add(role)
    db.commit()

    # 验证层级
    for i in range(1, 5):
        level = RoleInheritanceUtils.calculate_role_level(db, i)
        expected_level = i - 1
        print(f"角色{i} 层级: {level} (期望: {expected_level})")
        assert (
            level == expected_level
        ), f"❌ 角色{i}应该是Level {expected_level}，实际是Level {level}"

    print("✅ 测试通过：层级计算正确")

    db.close()


def test_statistics():
    """测试6：统计信息"""
    print("\n📋 测试6: 继承统计")
    print("-" * 60)

    RoleInheritanceUtils.clear_cache()
    db = create_test_db()

    # 创建混合角色
    root = Role(
        id=1,
        role_code="root",
        role_name="根角色",
        parent_id=None,
        inherit_permissions=False,
        is_active=True,
    )
    child1 = Role(
        id=2,
        role_code="child1",
        role_name="子角色1",
        parent_id=1,
        inherit_permissions=True,
        is_active=True,
    )
    child2 = Role(
        id=3,
        role_code="child2",
        role_name="子角色2",
        parent_id=1,
        inherit_permissions=False,
        is_active=True,
    )
    db.add_all([root, child1, child2])
    db.commit()

    # 获取统计
    stats = RoleInheritanceUtils.get_inheritance_statistics(db)

    print(f"总角色数: {stats['total_roles']}")
    print(f"根角色数: {stats['root_roles']}")
    print(f"继承角色数: {stats['inherited_roles']}")
    print(f"非继承角色数: {stats['non_inherited_roles']}")
    print(f"最大层级: {stats['max_depth']}")

    assert stats["total_roles"] == 3, "❌ 总角色数应该是3"
    assert stats["root_roles"] == 1, "❌ 根角色数应该是1"
    assert stats["inherited_roles"] == 1, "❌ 继承角色数应该是1"

    print("✅ 测试通过：统计信息正确")

    db.close()


def main():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 角色继承功能验证")
    print("=" * 60)

    try:
        test_basic_inheritance()
        test_multi_level_inheritance()
        test_no_inheritance_flag()
        test_circular_detection()
        test_role_level_calculation()
        test_statistics()

        print("\n" + "=" * 60)
        print("🎉 所有测试通过！角色继承功能正常！")
        print("=" * 60)

        return 0

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
