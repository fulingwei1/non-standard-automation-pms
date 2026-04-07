# -*- coding: utf-8 -*-
"""
权限管理服务测试配置
提供通用 fixtures
"""

import pytest
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


@pytest.fixture
def mock_superuser():
    """创建模拟超级管理员用户"""
    user = Mock()
    user.id = 999
    user.username = "admin"
    user.email = "admin@example.com"
    user.tenant_id = None
    user.is_active = True
    user.is_superuser = True
    return user


@pytest.fixture
def mock_role():
    """创建模拟角色"""
    role = Mock()
    role.id = 1
    role.role_code = "ROLE_USER"
    role.role_name = "普通用户"
    role.is_active = True
    role.tenant_id = 1
    role.is_system = False
    role.data_scope = "OWN"
    return role


@pytest.fixture
def mock_menu_permission():
    """创建模拟菜单权限"""
    menu = Mock()
    menu.id = 1
    menu.menu_code = "dashboard"
    menu.menu_name = "仪表盘"
    menu.menu_path = "/dashboard"
    menu.menu_icon = "dashboard"
    menu.menu_type = "menu"
    menu.sort_order = 1
    menu.is_active = True
    menu.is_visible = True
    menu.parent_id = None
    return menu