# -*- coding: utf-8 -*-
"""
测试Fixtures包

提供各种测试数据准备函数
"""

from .tenant_fixtures import (
    # Fixtures
    tenant_a,
    tenant_b,
    tenant_c,
    user_a,
    user_b,
    tenant_admin_a,
    superuser,
    project_a,
    project_b,
    multiple_projects_a,
    multiple_projects_b,
    
    # 辅助函数
    create_tenant,
    create_user,
    create_project,
)

__all__ = [
    # Fixtures
    "tenant_a",
    "tenant_b",
    "tenant_c",
    "user_a",
    "user_b",
    "tenant_admin_a",
    "superuser",
    "project_a",
    "project_b",
    "multiple_projects_a",
    "multiple_projects_b",
    
    # Helper functions
    "create_tenant",
    "create_user",
    "create_project",
]
