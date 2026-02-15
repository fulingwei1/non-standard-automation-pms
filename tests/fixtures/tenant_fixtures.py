# -*- coding: utf-8 -*-
"""
租户隔离测试 Fixtures

提供租户相关的测试数据准备功能
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.models.tenant import Tenant, TenantStatus, TenantPlan
from app.models.user import User
from app.models.project import Project
from app.core.security import get_password_hash


@pytest.fixture
def tenant_a(db: Session) -> Tenant:
    """创建租户A"""
    tenant = Tenant(
        tenant_code="tenant_a",
        tenant_name="租户A公司",
        status=TenantStatus.ACTIVE.value,
        plan_type=TenantPlan.STANDARD.value,
        max_users=50,
        max_roles=20,
        max_storage_gb=10,
        contact_name="张三",
        contact_email="zhangsan@tenant-a.com",
        contact_phone="13800138000",
        expired_at=datetime.utcnow() + timedelta(days=365)
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def tenant_b(db: Session) -> Tenant:
    """创建租户B"""
    tenant = Tenant(
        tenant_code="tenant_b",
        tenant_name="租户B公司",
        status=TenantStatus.ACTIVE.value,
        plan_type=TenantPlan.ENTERPRISE.value,
        max_users=200,
        max_roles=50,
        max_storage_gb=100,
        contact_name="李四",
        contact_email="lisi@tenant-b.com",
        contact_phone="13900139000",
        expired_at=datetime.utcnow() + timedelta(days=730)
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def tenant_c(db: Session) -> Tenant:
    """创建租户C（暂停状态）"""
    tenant = Tenant(
        tenant_code="tenant_c",
        tenant_name="租户C公司",
        status=TenantStatus.SUSPENDED.value,
        plan_type=TenantPlan.FREE.value,
        max_users=5,
        max_roles=5,
        max_storage_gb=1,
        contact_name="王五",
        contact_email="wangwu@tenant-c.com",
        contact_phone="13700137000",
        expired_at=datetime.utcnow() + timedelta(days=30)
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@pytest.fixture
def user_a(db: Session, tenant_a: Tenant) -> User:
    """创建租户A的普通用户"""
    user = User(
        tenant_id=tenant_a.id,
        username="user_a",
        password_hash=get_password_hash("password123"),
        email="user_a@tenant-a.com",
        real_name="用户A",
        department="技术部",
        position="工程师",
        is_active=True,
        is_superuser=False,
        is_tenant_admin=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_b(db: Session, tenant_b: Tenant) -> User:
    """创建租户B的普通用户"""
    user = User(
        tenant_id=tenant_b.id,
        username="user_b",
        password_hash=get_password_hash("password123"),
        email="user_b@tenant-b.com",
        real_name="用户B",
        department="开发部",
        position="开发工程师",
        is_active=True,
        is_superuser=False,
        is_tenant_admin=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def tenant_admin_a(db: Session, tenant_a: Tenant) -> User:
    """创建租户A的租户管理员"""
    user = User(
        tenant_id=tenant_a.id,
        username="tenant_admin_a",
        password_hash=get_password_hash("password123"),
        email="admin_a@tenant-a.com",
        real_name="租户A管理员",
        department="管理部",
        position="管理员",
        is_active=True,
        is_superuser=False,
        is_tenant_admin=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def superuser(db: Session) -> User:
    """创建超级管理员（不属于任何租户）"""
    user = User(
        tenant_id=None,
        username="superuser",
        password_hash=get_password_hash("password123"),
        email="superuser@system.com",
        real_name="超级管理员",
        department="系统部",
        position="系统管理员",
        is_active=True,
        is_superuser=True,
        is_tenant_admin=False
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def project_a(db: Session, tenant_a: Tenant, user_a: User) -> Project:
    """创建租户A的项目"""
    project = Project(
        tenant_id=tenant_a.id,
        project_code="PROJ_A_001",
        project_name="租户A项目1",
        project_type="NEW_PROJECT",
        created_by=user_a.id,
        pm_id=user_a.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def project_b(db: Session, tenant_b: Tenant, user_b: User) -> Project:
    """创建租户B的项目"""
    project = Project(
        tenant_id=tenant_b.id,
        project_code="PROJ_B_001",
        project_name="租户B项目1",
        project_type="NEW_PROJECT",
        created_by=user_b.id,
        pm_id=user_b.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@pytest.fixture
def multiple_projects_a(db: Session, tenant_a: Tenant, user_a: User) -> list:
    """创建租户A的多个项目（用于列表测试）"""
    projects = []
    for i in range(5):
        project = Project(
            tenant_id=tenant_a.id,
            project_code=f"PROJ_A_{i+10:03d}",
            project_name=f"租户A项目{i+10}",
            project_type="NEW_PROJECT",
            created_by=user_a.id,
            pm_id=user_a.id
        )
        db.add(project)
        projects.append(project)
    db.commit()
    return projects


@pytest.fixture
def multiple_projects_b(db: Session, tenant_b: Tenant, user_b: User) -> list:
    """创建租户B的多个项目（用于列表测试）"""
    projects = []
    for i in range(5):
        project = Project(
            tenant_id=tenant_b.id,
            project_code=f"PROJ_B_{i+10:03d}",
            project_name=f"租户B项目{i+10}",
            project_type="NEW_PROJECT",
            created_by=user_b.id,
            pm_id=user_b.id
        )
        db.add(project)
        projects.append(project)
    db.commit()
    return projects


def create_tenant(db: Session, tenant_code: str, tenant_name: str, **kwargs) -> Tenant:
    """创建租户的辅助函数"""
    tenant = Tenant(
        tenant_code=tenant_code,
        tenant_name=tenant_name,
        status=kwargs.get("status", TenantStatus.ACTIVE.value),
        plan_type=kwargs.get("plan_type", TenantPlan.STANDARD.value),
        max_users=kwargs.get("max_users", 50),
        max_roles=kwargs.get("max_roles", 20),
        max_storage_gb=kwargs.get("max_storage_gb", 10),
        **{k: v for k, v in kwargs.items() if k not in ["status", "plan_type", "max_users", "max_roles", "max_storage_gb"]}
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


def create_user(
    db: Session,
    username: str,
    tenant_id: int = None,
    is_superuser: bool = False,
    is_tenant_admin: bool = False,
    **kwargs
) -> User:
    """创建用户的辅助函数"""
    user = User(
        tenant_id=tenant_id,
        username=username,
        password_hash=get_password_hash(kwargs.get("password", "password123")),
        email=kwargs.get("email", f"{username}@example.com"),
        real_name=kwargs.get("real_name", username),
        department=kwargs.get("department", "技术部"),
        position=kwargs.get("position", "工程师"),
        is_active=kwargs.get("is_active", True),
        is_superuser=is_superuser,
        is_tenant_admin=is_tenant_admin
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_project(
    db: Session,
    tenant_id: int,
    created_by: int,
    project_code: str,
    project_name: str,
    **kwargs
) -> Project:
    """创建项目的辅助函数"""
    project = Project(
        tenant_id=tenant_id,
        project_code=project_code,
        project_name=project_name,
        project_type=kwargs.get("project_type", "NEW_PROJECT"),
        created_by=created_by,
        pm_id=kwargs.get("pm_id", created_by),
        **{k: v for k, v in kwargs.items() if k not in ["project_type", "pm_id"]}
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
