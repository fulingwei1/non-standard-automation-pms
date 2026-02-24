# -*- coding: utf-8 -*-
"""
Permission Model 测试
"""

import pytest
from sqlalchemy.exc import IntegrityError

try:
    from app.models.permission import Permission
except ImportError:
    pytest.skip("Permission model not available (refactored to ApiPermission)", allow_module_level=True)


class TestPermissionModel:
    """Permission 模型测试"""

    def test_create_permission(self, db_session):
        """测试创建权限"""
        perm = Permission(
            permission_code="PERM001",
            permission_name="测试权限",
            resource="project",
            action="read"
        )
        db_session.add(perm)
        db_session.commit()
        
        assert perm.id is not None
        assert perm.permission_code == "PERM001"
        assert perm.permission_name == "测试权限"

    def test_permission_code_unique(self, db_session):
        """测试权限编码唯一性"""
        p1 = Permission(
            permission_code="PERM001",
            permission_name="权限1",
            resource="test"
        )
        db_session.add(p1)
        db_session.commit()
        
        p2 = Permission(
            permission_code="PERM001",
            permission_name="权限2",
            resource="test"
        )
        db_session.add(p2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_permission_resource_action(self, db_session):
        """测试权限资源和动作"""
        perm = Permission(
            permission_code="PERM002",
            permission_name="项目创建",
            resource="project",
            action="create"
        )
        db_session.add(perm)
        db_session.commit()
        
        assert perm.resource == "project"
        assert perm.action == "create"

    def test_permission_actions(self, db_session):
        """测试不同权限动作"""
        actions = ["create", "read", "update", "delete", "execute"]
        
        for i, action in enumerate(actions):
            perm = Permission(
                permission_code=f"PERM_ACT_{i}",
                permission_name=f"{action}权限",
                resource="test",
                action=action
            )
            db_session.add(perm)
        db_session.commit()
        
        count = db_session.query(Permission).filter(
            Permission.action.in_(actions)
        ).count()
        assert count == len(actions)

    def test_permission_category(self, db_session):
        """测试权限分类"""
        perm = Permission(
            permission_code="PERM003",
            permission_name="分类测试",
            resource="test",
            category="业务权限"
        )
        db_session.add(perm)
        db_session.commit()
        
        assert perm.category == "业务权限"

    def test_permission_description(self, db_session):
        """测试权限描述"""
        desc = "允许用户查看项目详情信息"
        perm = Permission(
            permission_code="PERM004",
            permission_name="项目查看",
            resource="project",
            action="read",
            description=desc
        )
        db_session.add(perm)
        db_session.commit()
        
        assert perm.description == desc

    def test_permission_update(self, db_session, sample_permission):
        """测试更新权限"""
        sample_permission.permission_name = "更新后的权限"
        sample_permission.description = "新的描述"
        db_session.commit()
        
        db_session.refresh(sample_permission)
        assert sample_permission.permission_name == "更新后的权限"

    def test_permission_delete(self, db_session):
        """测试删除权限"""
        perm = Permission(
            permission_code="PERM_DEL",
            permission_name="待删除",
            resource="test"
        )
        db_session.add(perm)
        db_session.commit()
        pid = perm.id
        
        db_session.delete(perm)
        db_session.commit()
        
        deleted = db_session.query(Permission).filter_by(id=pid).first()
        assert deleted is None

    def test_permission_is_active(self, db_session):
        """测试权限激活状态"""
        perm = Permission(
            permission_code="PERM005",
            permission_name="激活测试",
            resource="test",
            is_active=True
        )
        db_session.add(perm)
        db_session.commit()
        
        assert perm.is_active is True

    def test_multiple_permissions(self, db_session):
        """测试多个权限"""
        perms = [
            Permission(
                permission_code=f"PERM{i:03d}",
                permission_name=f"权限{i}",
                resource="test"
            ) for i in range(1, 6)
        ]
        db_session.add_all(perms)
        db_session.commit()
        
        count = db_session.query(Permission).count()
        assert count >= 5

    def test_permission_group(self, db_session):
        """测试权限分组"""
        perm = Permission(
            permission_code="PERM006",
            permission_name="分组测试",
            resource="test",
            permission_group="项目管理"
        )
        db_session.add(perm)
        db_session.commit()
        
        assert perm.permission_group == "项目管理"

    def test_permission_resource_pattern(self, db_session):
        """测试权限资源模式"""
        perm = Permission(
            permission_code="PERM007",
            permission_name="模式测试",
            resource="project:*",
            action="read"
        )
        db_session.add(perm)
        db_session.commit()
        
        assert perm.resource == "project:*"
