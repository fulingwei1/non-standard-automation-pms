# -*- coding: utf-8 -*-
"""
Permission Model 测试

保留原测试路径，兼容 lastfailed，但断言已对齐当前 ApiPermission 模型。
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.user import ApiPermission


class TestPermissionModel:
    """ApiPermission 模型测试"""

    def test_create_permission(self, db_session):
        """测试创建权限"""
        perm = ApiPermission(
            perm_code="PERM_CREATE",
            perm_name="测试权限",
            module="project",
            action="VIEW",
        )
        db_session.add(perm)
        db_session.commit()

        assert perm.id is not None
        assert perm.perm_code == "PERM_CREATE"
        assert perm.perm_name == "测试权限"

    def test_permission_code_unique_within_tenant(self, db_session, sample_tenant):
        """测试租户内权限编码唯一"""
        p1 = ApiPermission(
            tenant_id=sample_tenant.id,
            perm_code="PERM_DUPLICATE",
            perm_name="权限1",
            module="auth",
        )
        db_session.add(p1)
        db_session.commit()

        p2 = ApiPermission(
            tenant_id=sample_tenant.id,
            perm_code="PERM_DUPLICATE",
            perm_name="权限2",
            module="auth",
        )
        db_session.add(p2)

        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_permission_module_action(self, db_session):
        """测试权限模块和动作"""
        perm = ApiPermission(
            perm_code="PERM_MODULE",
            perm_name="项目创建",
            module="project",
            action="CREATE",
        )
        db_session.add(perm)
        db_session.commit()

        assert perm.module == "project"
        assert perm.action == "CREATE"

    def test_permission_actions(self, db_session):
        """测试不同权限动作"""
        actions = ["CREATE", "VIEW", "EDIT", "DELETE", "APPROVE"]
        codes = []

        for i, action in enumerate(actions):
            code = f"PERM_ACTION_{i}"
            codes.append(code)
            db_session.add(
                ApiPermission(
                    perm_code=code,
                    perm_name=f"{action}权限",
                    module="workflow",
                    action=action,
                )
            )
        db_session.commit()

        count = db_session.query(ApiPermission).filter(ApiPermission.perm_code.in_(codes)).count()
        assert count == len(actions)

    def test_permission_type(self, db_session):
        """测试权限类型"""
        perm = ApiPermission(
            perm_code="PERM_MENU",
            perm_name="菜单权限",
            module="menu",
            permission_type="MENU",
        )
        db_session.add(perm)
        db_session.commit()

        assert perm.permission_type == "MENU"

    def test_permission_description(self, db_session):
        """测试权限描述"""
        desc = "允许用户查看项目详情信息"
        perm = ApiPermission(
            perm_code="PERM_DESC",
            perm_name="项目查看",
            module="project",
            action="VIEW",
            description=desc,
        )
        db_session.add(perm)
        db_session.commit()

        assert perm.description == desc

    def test_permission_update(self, db_session, sample_permission):
        """测试更新权限"""
        sample_permission.perm_name = "更新后的权限"
        sample_permission.description = "新的描述"
        db_session.commit()

        db_session.refresh(sample_permission)
        assert sample_permission.perm_name == "更新后的权限"

    def test_permission_delete(self, db_session):
        """测试删除权限"""
        perm = ApiPermission(
            perm_code="PERM_DELETE",
            perm_name="待删除",
            module="test",
        )
        db_session.add(perm)
        db_session.commit()
        pid = perm.id

        db_session.delete(perm)
        db_session.commit()

        deleted = db_session.query(ApiPermission).filter_by(id=pid).first()
        assert deleted is None

    def test_permission_is_active(self, db_session):
        """测试权限激活状态"""
        perm = ApiPermission(
            perm_code="PERM_ACTIVE",
            perm_name="激活测试",
            module="test",
            is_active=True,
        )
        db_session.add(perm)
        db_session.commit()

        assert perm.is_active is True

    def test_multiple_permissions(self, db_session):
        """测试多个权限"""
        codes = []
        perms = []
        for i in range(1, 6):
            code = f"PERM_BATCH_{i:03d}"
            codes.append(code)
            perms.append(
                ApiPermission(
                    perm_code=code,
                    perm_name=f"权限{i}",
                    module="batch",
                )
            )
        db_session.add_all(perms)
        db_session.commit()

        count = db_session.query(ApiPermission).filter(ApiPermission.perm_code.in_(codes)).count()
        assert count == len(codes)

    def test_permission_is_system(self, db_session):
        """测试系统权限标志"""
        perm = ApiPermission(
            perm_code="PERM_SYSTEM",
            perm_name="系统权限",
            module="system",
            is_system=True,
        )
        db_session.add(perm)
        db_session.commit()

        assert perm.is_system is True

    def test_permission_page_code(self, db_session):
        """测试页面编码"""
        perm = ApiPermission(
            perm_code="PERM_PAGE",
            perm_name="页面权限",
            module="project",
            page_code="project_detail",
            action="VIEW",
        )
        db_session.add(perm)
        db_session.commit()

        assert perm.page_code == "project_detail"
