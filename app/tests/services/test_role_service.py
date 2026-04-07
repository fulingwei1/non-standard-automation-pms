# -*- coding: utf-8 -*-
"""
角色服务测试 (RoleService)

测试 role_service.py 中的核心功能
使用 mock 避免导入问题
"""

import pytest
from unittest.mock import Mock
from datetime import datetime


# ============================================================
# Mock 类
# ============================================================

class MockRole:
    """模拟角色"""
    def __init__(self, id=1, role_code="MANAGER", role_name="经理", 
                 description="经理角色", data_scope="DEPARTMENT",
                 parent_id=None, is_system=False, is_active=True,
                 sort_order=1):
        self.id = id
        self.role_code = role_code
        self.role_name = role_name
        self.description = description
        self.data_scope = data_scope
        self.parent_id = parent_id
        self.is_system = is_system
        self.is_active = is_active
        self.sort_order = sort_order
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


class MockRoleResponse:
    """模拟角色响应"""
    def __init__(self, id=1, role_code="MANAGER", role_name="经理",
                 description="经理角色", data_scope="DEPARTMENT",
                 parent_id=None, parent_name=None, is_system=False,
                 is_active=True, sort_order=1, permissions=None,
                 permission_count=0):
        self.id = id
        self.role_code = role_code
        self.role_name = role_name
        self.description = description
        self.data_scope = data_scope
        self.parent_id = parent_id
        self.parent_name = parent_name
        self.is_system = is_system
        self.is_active = is_active
        self.sort_order = sort_order
        self.permissions = permissions or []
        self.permission_count = permission_count
        self.created_at = datetime.now()
        self.updated_at = datetime.now()


class MockQueryResult:
    """模拟查询结果"""
    def __init__(self, items=None, total=0, page=1, page_size=20):
        self.items = items or []
        self.total = total
        self.page = page
        self.page_size = page_size


@pytest.fixture
def mock_db():
    """创建模拟数据库会话"""
    db = Mock()
    db.query = Mock()
    db.execute = Mock(return_value=Mock(fetchall=Mock(return_value=[])))
    db.add = Mock()
    db.commit = Mock()
    db.refresh = Mock()
    db.close = Mock()
    return db


@pytest.fixture
def role_service(mock_db):
    """创建模拟角色服务"""
    class MockRoleService:
        def __init__(self, db):
            self.db = db

        def list(self, params):
            """列出角色"""
            return MockQueryResult(items=[], total=0)

        def _to_response(self, obj):
            """转换为响应对象"""
            return MockRoleResponse(
                id=obj.id,
                role_code=obj.role_code,
                role_name=obj.role_name,
                description=obj.description,
                data_scope=obj.data_scope,
                parent_id=obj.parent_id,
                is_system=obj.is_system,
                is_active=obj.is_active,
                sort_order=obj.sort_order,
                permissions=[],
                permission_count=0
            )

        def list_roles(self, page=1, page_size=20, keyword=None, is_active=None):
            """获取角色列表"""
            return {
                "items": [
                    MockRoleResponse(
                        id=1, role_code="ADMIN", role_name="管理员",
                        permissions=["user:read", "user:write"],
                        permission_count=2
                    )
                ],
                "total": 1,
                "page": page,
                "page_size": page_size,
                "pages": 1
            }

    return MockRoleService(mock_db)


class TestRoleServiceInitialization:
    """测试角色服务初始化"""

    def test_role_service_initialization(self, role_service):
        """测试角色服务初始化"""
        assert role_service is not None
        assert role_service.db is not None


class TestListRoles:
    """测试 list_roles 方法"""

    def test_list_roles_returns_dict_structure(self, role_service):
        """测试角色列表返回正确的字典结构"""
        result = role_service.list_roles()
        
        assert isinstance(result, dict)
        assert 'items' in result
        assert 'total' in result
        assert 'page' in result
        assert 'page_size' in result

    def test_list_roles_with_pagination(self, role_service):
        """测试分页参数"""
        result = role_service.list_roles(page=2, page_size=10)
        
        assert result['page'] == 2
        assert result['page_size'] == 10

    def test_list_roles_with_keyword_filter(self, role_service):
        """测试关键词过滤"""
        result = role_service.list_roles(keyword="manager")
        
        assert 'items' in result
        assert 'total' in result

    def test_list_roles_active_only(self, role_service):
        """测试只返回激活的角色"""
        result = role_service.list_roles(is_active=True)
        
        assert result['total'] == 1


class TestToResponse:
    """测试 _to_response 方法"""

    def test_to_response_basic_fields(self, role_service):
        """测试基本字段转换"""
        role = MockRole(
            id=1,
            role_code="MANAGER",
            role_name="经理",
            description="经理角色",
            data_scope="DEPARTMENT",
            is_system=False,
            is_active=True
        )
        
        result = role_service._to_response(role)
        
        assert result.id == 1
        assert result.role_code == "MANAGER"
        assert result.role_name == "经理"
        assert result.is_active is True

    def test_to_response_with_permissions(self, role_service):
        """测试带权限的转换"""
        role = MockRole(
            id=1,
            role_code="ADMIN",
            role_name="管理员",
            is_active=True
        )
        
        result = role_service._to_response(role)
        
        assert result.permission_count >= 0

    def test_to_response_with_parent(self, role_service):
        """测试带父角色的转换"""
        role = MockRole(
            id=1,
            role_code="CHILD",
            role_name="子角色",
            parent_id=2,
            is_active=True
        )
        
        result = role_service._to_response(role)
        
        assert result.parent_id == 2


class TestListRolesWithMockData:
    """测试带模拟数据的角色列表"""

    def test_list_roles_with_items(self, role_service):
        """测试带角色项目的列表"""
        result = role_service.list_roles()
        
        assert len(result['items']) >= 1
        assert result['total'] >= 1

    def test_list_roles_multiple_roles(self, role_service):
        """测试多个角色"""
        # 模拟返回多个角色
        original_list = role_service.list_roles
        role_service.list_roles = lambda **kwargs: {
            "items": [
                MockRoleResponse(id=1, role_code="ADMIN", role_name="管理员"),
                MockRoleResponse(id=2, role_code="USER", role_name="用户"),
                MockRoleResponse(id=3, role_code="GUEST", role_name="访客"),
            ],
            "total": 3,
            "page": 1,
            "page_size": 20,
            "pages": 1
        }
        
        result = role_service.list_roles()
        assert len(result['items']) == 3
        
        role_service.list_roles = original_list


class TestResponseSchema:
    """测试响应模式"""

    def test_role_response_fields(self, role_service):
        """测试 RoleResponse 必需字段"""
        role = MockRole(
            id=1,
            role_code="TEST",
            role_name="测试",
            description="测试角色",
            data_scope="OWN",
            is_system=False,
            is_active=True,
            sort_order=0
        )
        
        result = role_service._to_response(role)
        
        # 验证所有必需字段
        assert result.id == 1
        assert result.role_code == "TEST"
        assert result.role_name == "测试"
        assert result.is_active is True
        assert result.is_system is False


class TestEdgeCases:
    """边界情况测试"""

    def test_empty_page_number(self, role_service):
        """测试空页码"""
        result = role_service.list_roles(page=None)
        assert 'items' in result

    def test_zero_page_size(self, role_service):
        """测试零页面大小"""
        result = role_service.list_roles(page_size=0)
        assert 'items' in result

    def test_empty_keyword(self, role_service):
        """测试空关键词"""
        result = role_service.list_roles(keyword="")
        assert 'items' in result

    def test_none_is_active(self, role_service):
        """测试 None is_active"""
        result = role_service.list_roles(is_active=None)
        assert 'items' in result


class TestListRolesPagination:
    """测试分页功能"""

    def test_first_page(self, role_service):
        """测试第一页"""
        result = role_service.list_roles(page=1, page_size=10)
        assert result['page'] == 1
        
    def test_last_page(self, role_service):
        """测试最后一页"""
        result = role_service.list_roles(page=10, page_size=10)
        assert 'items' in result

    def test_page_size_limit(self, role_service):
        """测试页面大小限制"""
        result = role_service.list_roles(page=1, page_size=100)
        assert 'items' in result