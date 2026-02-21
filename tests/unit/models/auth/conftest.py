# -*- coding: utf-8 -*-
"""
Auth Models 测试的 Fixtures
"""

import pytest


@pytest.fixture
def sample_role(db_session):
    """创建示例角色"""
    from app.models.permission import Role
    
    role = Role(
        role_code="ROLE001",
        role_name="测试角色",
        description="这是一个测试角色"
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture
def sample_permission(db_session):
    """创建示例权限"""
    from app.models.permission import Permission
    
    permission = Permission(
        permission_code="PERM001",
        permission_name="测试权限",
        resource="test",
        action="read"
    )
    db_session.add(permission)
    db_session.commit()
    db_session.refresh(permission)
    return permission
