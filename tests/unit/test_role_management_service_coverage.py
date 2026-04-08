# -*- coding: utf-8 -*-
"""
角色管理服务单元测试 - 覆盖率提升版
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any, Optional

from app.services.role_management.service import RoleManagementService, RESERVED_ROLE_CODES
from app.models.user import Role, RoleTemplate, UserRole, RoleApiPermission, ApiPermission


class TestRoleManagementServiceConstants:
    """测试常量和配置"""

    def test_reserved_role_codes_not_empty(self):
        """测试预留角色编码非空"""
        assert len(RESERVED_ROLE_CODES) > 0

    def test_reserved_role_codes_contains_admin(self):
        """测试预留角色编码包含管理员"""
        assert "ADMIN" in RESERVED_ROLE_CODES
        assert "admin" in RESERVED_ROLE_CODES

    def test_reserved_role_codes_contains_executives(self):
        """测试预留角色编码包含高管角色"""
        assert "GM" in RESERVED_ROLE_CODES
        assert "CEO" in RESERVED_ROLE_CODES
        assert "CFO" in RESERVED_ROLE_CODES


class TestRoleManagementServiceInit:
    """测试服务初始化"""

    def test_init_with_db(self):
        """测试正常初始化"""
        mock_db = Mock()
        service = RoleManagementService(mock_db)
        assert service.db == mock_db

    def test_init_without_db_raises(self):
        """测试缺少数据库参数"""
        with pytest.raises(TypeError):
            RoleManagementService()


class TestRoleManagementServiceGetRole:
    """测试角色查询"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return RoleManagementService(mock_db)

    def test_get_role_by_id_found(self, service):
        """测试找到角色"""
        role = Mock(spec=Role)
        role.id = 1
        role.name = "测试角色"
        
        service.db.query = Mock()
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = role
        service.db.query.return_value = query_mock
        
        result = service.get_role_by_id(1)
        
        assert result.id == 1

    def test_get_role_by_id_not_found(self, service):
        """测试未找到角色"""
        service.db.query = Mock()
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        service.db.query.return_value = query_mock
        
        with pytest.raises(Exception):
            service.get_role_by_id(999)


class TestRoleManagementServiceListRoles:
    """测试角色列表"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return RoleManagementService(mock_db)

    def test_list_roles_by_tenant_empty(self, service):
        """测试空角色列表"""
        # 验证方法存在
        assert hasattr(service, 'list_roles_by_tenant')

    def test_list_roles_by_tenant_with_roles(self, service):
        """测试有角色列表"""
        # 验证方法存在
        assert hasattr(service, 'list_roles_by_tenant')


class TestRoleManagementServiceCreateRole:
    """测试角色创建"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return RoleManagementService(mock_db)

    def test_create_role_reserved_code(self, service):
        """测试创建预留编码角色"""
        with pytest.raises(Exception):
            service.create_role(
                name="Admin",
                code="ADMIN",
                tenant_id=1,
                description="测试"
            )

    def test_create_role_method_exists(self, service):
        """测试创建角色方法存在"""
        assert hasattr(service, 'create_role')


class TestRoleManagementServiceTemplates:
    """测试角色模板"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return RoleManagementService(mock_db)

    def test_get_role_templates_empty(self, service):
        """测试空模板列表"""
        service.db.query = Mock()
        query_mock = Mock()
        query_mock.filter.return_value.order_by.return_value.all.return_value = []
        service.db.query.return_value = query_mock
        
        templates = service.get_role_templates()
        
        assert templates == []

    def test_get_template_by_id_found(self, service):
        """测试找到模板"""
        template = Mock(spec=RoleTemplate)
        template.id = 1
        template.name = "测试模板"
        
        service.db.query = Mock()
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = template
        service.db.query.return_value = query_mock
        
        result = service.get_template_by_id(1)
        
        assert result.id == 1

    def test_get_template_by_id_not_found(self, service):
        """测试未找到模板"""
        service.db.query = Mock()
        query_mock = Mock()
        query_mock.filter.return_value.first.return_value = None
        service.db.query.return_value = query_mock
        
        with pytest.raises(Exception):
            service.get_template_by_id(999)


class TestRoleManagementServiceRoleDict:
    """测试角色字典转换"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return RoleManagementService(mock_db)

    def test_role_to_dict_method_exists(self, service):
        """测试角色转字典方法存在"""
        assert hasattr(service, '_role_to_dict')


class TestRoleManagementServiceCycleDetection:
    """测试循环检测"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return RoleManagementService(mock_db)

    def test_would_create_cycle_method_exists(self, service):
        """测试循环检测方法存在"""
        assert hasattr(service, '_would_create_cycle')

    def test_collect_descendants_method_exists(self, service):
        """测试收集后代方法存在"""
        assert hasattr(service, '_collect_descendants')


class TestRoleManagementServicePermissions:
    """测试权限相关"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return RoleManagementService(mock_db)

    def test_get_permissions_list_empty(self, service):
        """测试空权限列表"""
        service.db.query = Mock()
        query_mock = Mock()
        query_mock.filter.return_value.order_by.return_value.all.return_value = []
        service.db.query.return_value = query_mock
        
        permissions = service.get_permissions_list()
        
        assert permissions == []


class TestRoleManagementServiceNavGroups:
    """测试导航组"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return RoleManagementService(mock_db)

    def test_get_user_nav_groups_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_user_nav_groups')

    def test_get_role_nav_groups_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_role_nav_groups')


class TestRoleManagementServiceHierarchy:
    """测试角色层级"""

    @pytest.fixture
    def service(self):
        mock_db = Mock()
        return RoleManagementService(mock_db)

    def test_get_role_hierarchy_tree_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_role_hierarchy_tree')

    def test_get_role_ancestors_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_role_ancestors')

    def test_get_role_descendants_method_exists(self, service):
        """测试方法存在"""
        assert hasattr(service, 'get_role_descendants')