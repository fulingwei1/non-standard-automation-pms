# -*- coding: utf-8 -*-
"""
角色管理服务测试配置
提供通用 fixtures
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_role():
    """创建模拟角色"""
    role = Mock()
    role.id = 1
    role.role_code = "ROLE_MANAGER"
    role.role_name = "经理"
    role.description = "经理角色"
    role.is_active = True
    role.is_system = False
    role.tenant_id = 1
    role.parent_id = None
    role.data_scope = "DEPARTMENT"
    role.sort_order = 1
    role.nav_groups = None
    role.ui_config = None
    role.created_at = datetime.now()
    role.updated_at = datetime.now()
    return role


@pytest.fixture
def mock_role_template():
    """创建模拟角色模板"""
    template = Mock()
    template.id = 1
    template.template_code = "TPL_MANAGER"
    template.template_name = "经理模板"
    template.description = "经理角色模板"
    template.role_type = "BUSINESS"
    template.scope_type = "GLOBAL"
    template.data_scope = "DEPARTMENT"
    template.level = 2
    template.permission_snapshot = '["user:read", "user:write"]'
    template.is_active = True
    template.version = 1
    template.version_note = "初始版本"
    template.source_role_id = None
    template.source_role_name = None
    template.created_at = datetime.now()
    template.updated_at = datetime.now()
    return template


@pytest.fixture
def mock_api_permission():
    """创建模拟API权限"""
    perm = Mock()
    perm.id = 1
    perm.perm_code = "user:read"
    perm.perm_name = "用户读取"
    perm.module = "user"
    perm.action = "read"
    perm.is_active = True
    perm.tenant_id = 1
    return perm


@pytest.fixture
def mock_user():
    """创建模拟用户"""
    user = Mock()
    user.id = 1
    user.username = "test_user"
    user.email = "test@example.com"
    user.tenant_id = 1
    user.is_active = True
    user.is_superuser = False
    return user