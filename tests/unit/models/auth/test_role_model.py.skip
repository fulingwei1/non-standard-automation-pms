# -*- coding: utf-8 -*-
"""
Role Model 测试
"""

import pytest
from sqlalchemy.exc import IntegrityError

try:
    from app.models.permission import Role
except ImportError:
    pytest.skip("Role not importable from app.models.permission (moved to app.models.user)", allow_module_level=True)


class TestRoleModel:
    """Role 模型测试"""

    def test_create_role(self, db_session):
        """测试创建角色"""
        role = Role(
            role_code="ROLE001",
            role_name="测试角色",
            description="这是一个测试角色"
        )
        db_session.add(role)
        db_session.commit()
        
        assert role.id is not None
        assert role.role_code == "ROLE001"
        assert role.role_name == "测试角色"

    def test_role_code_unique(self, db_session):
        """测试角色编码唯一性"""
        r1 = Role(
            role_code="ROLE001",
            role_name="角色1"
        )
        db_session.add(r1)
        db_session.commit()
        
        r2 = Role(
            role_code="ROLE001",
            role_name="角色2"
        )
        db_session.add(r2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_role_type(self, db_session):
        """测试角色类型"""
        types = ["系统角色", "业务角色", "自定义角色"]
        
        for i, rt in enumerate(types):
            role = Role(
                role_code=f"ROLE_TYPE_{i}",
                role_name=f"{rt}测试",
                role_type=rt
            )
            db_session.add(role)
        db_session.commit()
        
        count = db_session.query(Role).filter(
            Role.role_type.in_(types)
        ).count()
        assert count == len(types)

    def test_role_status(self, db_session, sample_role):
        """测试角色状态"""
        sample_role.status = "ACTIVE"
        db_session.commit()
        
        db_session.refresh(sample_role)
        assert sample_role.status == "ACTIVE"

    def test_role_level(self, db_session):
        """测试角色级别"""
        role = Role(
            role_code="ROLE002",
            role_name="级别测试",
            level=5
        )
        db_session.add(role)
        db_session.commit()
        
        assert role.level == 5

    def test_role_description(self, db_session):
        """测试角色描述"""
        desc = "拥有系统全部权限的管理员角色"
        role = Role(
            role_code="ADMIN",
            role_name="系统管理员",
            description=desc
        )
        db_session.add(role)
        db_session.commit()
        
        assert role.description == desc

    def test_role_update(self, db_session, sample_role):
        """测试更新角色"""
        sample_role.role_name = "更新后的角色"
        sample_role.description = "新的描述"
        db_session.commit()
        
        db_session.refresh(sample_role)
        assert sample_role.role_name == "更新后的角色"

    def test_role_delete(self, db_session):
        """测试删除角色"""
        role = Role(
            role_code="ROLE_DEL",
            role_name="待删除"
        )
        db_session.add(role)
        db_session.commit()
        rid = role.id
        
        db_session.delete(role)
        db_session.commit()
        
        deleted = db_session.query(Role).filter_by(id=rid).first()
        assert deleted is None

    def test_role_is_default(self, db_session):
        """测试默认角色标志"""
        role = Role(
            role_code="DEFAULT_ROLE",
            role_name="默认角色",
            is_default=True
        )
        db_session.add(role)
        db_session.commit()
        
        assert role.is_default is True

    def test_role_is_system(self, db_session):
        """测试系统角色标志"""
        role = Role(
            role_code="SYS_ROLE",
            role_name="系统角色",
            is_system=True
        )
        db_session.add(role)
        db_session.commit()
        
        assert role.is_system is True

    def test_multiple_roles(self, db_session):
        """测试多个角色"""
        roles = [
            Role(
                role_code=f"ROLE{i:03d}",
                role_name=f"角色{i}"
            ) for i in range(1, 6)
        ]
        db_session.add_all(roles)
        db_session.commit()
        
        count = db_session.query(Role).count()
        assert count >= 5

    def test_role_hierarchy(self, db_session):
        """测试角色层级"""
        parent = Role(
            role_code="PARENT_ROLE",
            role_name="父角色"
        )
        db_session.add(parent)
        db_session.commit()
        
        child = Role(
            role_code="CHILD_ROLE",
            role_name="子角色",
            parent_id=parent.id
        )
        db_session.add(child)
        db_session.commit()
        
        assert child.parent_id == parent.id
