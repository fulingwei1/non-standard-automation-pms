# -*- coding: utf-8 -*-
"""
Auth Models 测试的 Fixtures
"""

import uuid

import pytest

from app.models.tenant import Tenant
from app.models.user import ApiPermission, Role


def _unique_code(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


@pytest.fixture
def sample_tenant(db_session):
    """创建示例租户"""
    tenant = Tenant(
        tenant_code=_unique_code("TENANT"),
        tenant_name="权限测试租户",
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)
    return tenant


@pytest.fixture
def sample_role(db_session):
    """创建示例角色"""
    role = Role(
        role_code=_unique_code("ROLE"),
        role_name="测试角色",
        description="这是一个测试角色",
    )
    db_session.add(role)
    db_session.commit()
    db_session.refresh(role)
    return role


@pytest.fixture
def sample_permission(db_session):
    """创建示例 API 权限"""
    permission = ApiPermission(
        perm_code=_unique_code("PERM"),
        perm_name="测试权限",
        module="test",
        action="VIEW",
    )
    db_session.add(permission)
    db_session.commit()
    db_session.refresh(permission)
    return permission
