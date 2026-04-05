# -*- coding: utf-8 -*-
"""
测试角色管理服务

测试 app/services/role_management/service.py
"""

import pytest
from unittest.mock import MagicMock, patch, create_autospec
from sqlalchemy.orm import Session
import sys
import os

# Mock missing modules before importing target modules
sys.modules['app.services.permission_audit_service'] = MagicMock()
sys.modules['app.services.notification_handlers'] = MagicMock()
sys.modules['app.services.notification_handlers.email_handler'] = MagicMock()

import json


class TestRoleManagementService:
    """测试 RoleManagementService"""

    def test_service_init(self):
        """测试服务初始化"""
        from app.services.role_management.service import RoleManagementService
        
        mock_db = MagicMock(spec=Session)
        service = RoleManagementService(mock_db)
        
        assert service.db is not None

    def test_reserved_role_codes_exist(self):
        """测试保留角色编码定义存在"""
        from app.services.role_management.service import RESERVED_ROLE_CODES
        
        # 应该包含系统预置角色
        assert "ADMIN" in RESERVED_ROLE_CODES
        assert "admin" in RESERVED_ROLE_CODES
        assert "SUPERUSER" in RESERVED_ROLE_CODES
        assert "ROOT" in RESERVED_ROLE_CODES

    def test_reserved_role_codes_case_sensitive(self):
        """测试保留角色编码大小写敏感"""
        from app.services.role_management.service import RESERVED_ROLE_CODES
        
        # 验证大小写变体
        assert "Administrator" in RESERVED_ROLE_CODES
        assert "ADMINISTRATOR" in RESERVED_ROLE_CODES

    def test_reserved_role_codes_tenant_admin(self):
        """测试租户管理员保留编码"""
        from app.services.role_management.service import RESERVED_ROLE_CODES
        
        assert "TENANT_ADMIN" in RESERVED_ROLE_CODES
        assert "tenant_admin" in RESERVED_ROLE_CODES

    @pytest.fixture
    def mock_db_session(self):
        """创建模拟数据库会话"""
        db = MagicMock(spec=Session)
        return db

    def test_role_scope_filter(self, mock_db_session):
        """测试角色范围过滤方法"""
        from app.services.role_management.service import RoleManagementService
        
        service = RoleManagementService(mock_db_session)
        
        # 测试租户过滤
        result_none = service._role_scope_filter(None)
        assert result_none is True
        
        # 测试有租户ID的情况
        result_with_tenant = service._role_scope_filter(123)
        assert result_with_tenant is not None

    def test_permission_scope_filter(self, mock_db_session):
        """测试权限范围过滤方法"""
        from app.services.role_management.service import RoleManagementService
        
        service = RoleManagementService(mock_db_session)
        
        # 测试无租户
        result_none = service._permission_scope_filter(None)
        assert result_none is True
        
        # 测试有租户
        result_with_tenant = service._permission_scope_filter(123)
        assert result_with_tenant is not None

    def test_get_role_by_id_not_found(self, mock_db_session):
        """测试获取不存在的角色"""
        from app.services.role_management.service import RoleManagementService
        from fastapi import HTTPException
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = None
        
        service = RoleManagementService(mock_db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.get_role_by_id(9999)
        
        assert exc_info.value.status_code == 404

    def test_get_role_by_id_success(self, mock_db_session):
        """测试成功获取角色"""
        from app.services.role_management.service import RoleManagementService
        
        mock_role = MagicMock()
        mock_role.id = 1
        mock_role.role_code = "TEST_ROLE"
        mock_role.role_name = "测试角色"
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_role
        
        service = RoleManagementService(mock_db_session)
        role = service.get_role_by_id(1)
        
        assert role is not None
        assert role.id == 1

    def test_list_roles_by_tenant(self, mock_db_session):
        """测试列出角色"""
        from app.services.role_management.service import RoleManagementService
        
        mock_roles = []
        for i in range(3):
            role = MagicMock()
            role.id = i + 1
            role.role_code = f"ROLE_{i}"
            role.role_name = f"角色{i}"
            role.description = None
            role.data_scope = "OWN"
            role.is_active = True
            role.is_system = False
            role.parent_id = None
            role.sort_order = i
            role.tenant_id = 1
            mock_roles.append(role)
        
        mock_query = MagicMock()
        mock_query.count.return_value = 3
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_roles
        mock_db_session.query.return_value = mock_query
        
        service = RoleManagementService(mock_db_session)
        result = service.list_roles_by_tenant(tenant_id=1, page=1, page_size=10)
        
        assert result['total'] == 3
        assert len(result['items']) == 3

    def test_create_role_reserved_code(self, mock_db_session):
        """测试创建保留编码角色应失败"""
        from app.services.role_management.service import RoleManagementService
        from fastapi import HTTPException
        
        service = RoleManagementService(mock_db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.create_role(
                role_code="ADMIN",
                role_name="管理员",
                tenant_id=1
            )
        
        assert exc_info.value.status_code == 400
        assert "系统保留" in str(exc_info.value.detail)

    def test_create_role_duplicate(self, mock_db_session):
        """测试创建重复角色应失败"""
        from app.services.role_management.service import RoleManagementService
        from fastapi import HTTPException
        
        mock_existing = MagicMock()
        mock_existing.role_code = "TEST_ROLE"
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_existing
        
        service = RoleManagementService(mock_db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.create_role(
                role_code="TEST_ROLE",
                role_name="测试角色",
                tenant_id=1
            )
        
        assert exc_info.value.status_code == 400
        assert "已存在" in str(exc_info.value.detail)

    def test_delete_system_role(self, mock_db_session):
        """测试删除系统预置角色应失败"""
        from app.services.role_management.service import RoleManagementService
        from fastapi import HTTPException
        
        mock_role = MagicMock()
        mock_role.id = 1
        mock_role.is_system = True
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_role
        
        service = RoleManagementService(mock_db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.delete_role(1)
        
        assert exc_info.value.status_code == 400
        assert "系统预置" in str(exc_info.value.detail)

    def test_delete_role_with_users(self, mock_db_session):
        """测试删除有关联用户的角色应失败"""
        from app.services.role_management.service import RoleManagementService
        from fastapi import HTTPException
        
        mock_role = MagicMock()
        mock_role.id = 1
        mock_role.is_system = False
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_role
        mock_db_session.query.return_value.filter.return_value.count.return_value = 5
        
        service = RoleManagementService(mock_db_session)
        
        with pytest.raises(HTTPException) as exc_info:
            service.delete_role(1)
        
        assert exc_info.value.status_code == 400
        assert "无法删除" in str(exc_info.value.detail)

    def test_role_to_dict(self, mock_db_session):
        """测试角色转字典方法"""
        from app.services.role_management.service import RoleManagementService
        
        mock_role = MagicMock()
        mock_role.id = 1
        mock_role.role_code = "TEST_ROLE"
        mock_role.role_name = "测试角色"
        mock_role.description = "测试描述"
        mock_role.data_scope = "OWN"
        mock_role.is_active = True
        mock_role.is_system = False
        mock_role.parent_id = None
        mock_role.sort_order = 1
        mock_role.tenant_id = 1
        
        service = RoleManagementService(mock_db_session)
        result = service._role_to_dict(mock_role)
        
        assert result['id'] == 1
        assert result['role_code'] == "TEST_ROLE"
        assert result['role_name'] == "测试角色"
        assert result['is_active'] is True

    def test_would_create_cycle(self, mock_db_session):
        """测试循环引用检测"""
        from app.services.role_management.service import RoleManagementService
        
        service = RoleManagementService(mock_db_session)
        
        # 测试不形成循环
        mock_role = MagicMock()
        mock_role.parent_id = None
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_role
        
        result = service._would_create_cycle(1, 2)
        assert result is False

    def test_get_role_hierarchy_tree(self, mock_db_session):
        """测试获取角色层级树"""
        from app.services.role_management.service import RoleManagementService
        
        mock_role = MagicMock()
        mock_role.id = 1
        mock_role.role_code = "PARENT"
        mock_role.role_name = "父角色"
        mock_role.parent_id = None
        mock_role.data_scope = "OWN"
        mock_role.is_active = True
        
        mock_query = MagicMock()
        mock_query.order_by.return_value.all.return_value = [mock_role]
        mock_db_session.query.return_value = mock_query
        
        service = RoleManagementService(mock_db_session)
        result = service.get_role_hierarchy_tree(tenant_id=1)
        
        assert isinstance(result, list)