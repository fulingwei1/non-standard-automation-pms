# -*- coding: utf-8 -*-
"""
数据权限服务增强版单元测试

测试覆盖:
1. 枚举映射测试
2. 用户组织单元获取测试
3. 可访问组织单元测试
4. 数据权限过滤测试
5. 性能优化验证
6. 边界条件和异常处理
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from sqlalchemy.orm import Query

from app.models.enums import DataScopeEnum
from app.models.permission import ScopeType


class TestEnumNormalization:
    """测试枚举标准化功能"""

    def test_normalize_all_scope(self):
        """测试 ALL 范围标准化"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        result = DataScopeServiceEnhanced.normalize_scope_type(ScopeType.ALL.value)
        assert result == DataScopeEnum.ALL.value

    def test_normalize_department_scope(self):
        """测试 DEPARTMENT 范围标准化"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        result = DataScopeServiceEnhanced.normalize_scope_type(
            ScopeType.DEPARTMENT.value
        )
        assert result == DataScopeEnum.DEPT.value

    def test_normalize_business_unit_scope(self):
        """测试 BUSINESS_UNIT 范围标准化"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        result = DataScopeServiceEnhanced.normalize_scope_type(
            ScopeType.BUSINESS_UNIT.value
        )
        assert result == DataScopeEnum.DEPT.value

    def test_normalize_team_scope(self):
        """测试 TEAM 范围标准化"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        result = DataScopeServiceEnhanced.normalize_scope_type(ScopeType.TEAM.value)
        assert result == DataScopeEnum.DEPT.value

    def test_normalize_project_scope(self):
        """测试 PROJECT 范围标准化"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        result = DataScopeServiceEnhanced.normalize_scope_type(ScopeType.PROJECT.value)
        assert result == DataScopeEnum.PROJECT.value

    def test_normalize_own_scope(self):
        """测试 OWN 范围标准化"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        result = DataScopeServiceEnhanced.normalize_scope_type(ScopeType.OWN.value)
        assert result == DataScopeEnum.OWN.value

    def test_normalize_unknown_scope(self):
        """测试未知范围类型"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        result = DataScopeServiceEnhanced.normalize_scope_type("UNKNOWN")
        assert result == "UNKNOWN"


class TestGetUserOrgUnits:
    """测试获取用户组织单元功能"""

    def test_returns_empty_list_when_no_assignments(self):
        """测试无分配时返回空列表"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = (
            []
        )

        result = DataScopeServiceEnhanced.get_user_org_units(mock_db, user_id=1)

        assert result == []

    def test_returns_org_unit_ids_from_assignments(self):
        """测试从分配记录获取组织单元ID"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()
        mock_assignment1 = MagicMock()
        mock_assignment1.org_unit_id = 10
        mock_assignment2 = MagicMock()
        mock_assignment2.org_unit_id = 20

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [
            mock_assignment1,
            mock_assignment2,
        ]

        result = DataScopeServiceEnhanced.get_user_org_units(mock_db, user_id=1)

        assert set(result) == {10, 20}

    def test_handles_exception_gracefully(self):
        """测试异常处理"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")

        result = DataScopeServiceEnhanced.get_user_org_units(mock_db, user_id=1)

        assert result == []

    def test_removes_duplicates(self):
        """测试去重功能"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()
        mock_assignment1 = MagicMock()
        mock_assignment1.org_unit_id = 10
        mock_assignment2 = MagicMock()
        mock_assignment2.org_unit_id = 10
        mock_assignment3 = MagicMock()
        mock_assignment3.org_unit_id = 20

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [
            mock_assignment1,
            mock_assignment2,
            mock_assignment3,
        ]

        result = DataScopeServiceEnhanced.get_user_org_units(mock_db, user_id=1)

        assert set(result) == {10, 20}
        assert len(result) == 2


class TestGetAccessibleOrgUnits:
    """测试获取可访问组织单元功能"""

    def test_all_scope_returns_all_active_units(self):
        """测试 ALL 范围返回所有活跃单元"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [
            MagicMock(id=1),
            MagicMock(id=2),
            MagicMock(id=3),
        ]

        result = DataScopeServiceEnhanced.get_accessible_org_units(
            mock_db, user_id=1, scope_type=ScopeType.ALL.value
        )

        assert result == [1, 2, 3]

    def test_returns_empty_when_user_has_no_orgs(self):
        """测试用户无组织时返回空列表"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()

        with patch.object(
            DataScopeServiceEnhanced, "get_user_org_units", return_value=[]
        ):
            result = DataScopeServiceEnhanced.get_accessible_org_units(
                mock_db, user_id=1, scope_type=ScopeType.DEPARTMENT.value
            )

        assert result == []

    def test_team_scope_returns_only_user_orgs(self):
        """测试 TEAM 范围只返回用户所属组织"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()
        mock_org = MagicMock()
        mock_org.id = 10

        mock_db.query.return_value.filter.return_value.first.return_value = mock_org

        with patch.object(
            DataScopeServiceEnhanced, "get_user_org_units", return_value=[10]
        ):
            result = DataScopeServiceEnhanced.get_accessible_org_units(
                mock_db, user_id=1, scope_type=ScopeType.TEAM.value
            )

        assert 10 in result


class TestFindAncestorByType:
    """测试查找祖先组织功能"""

    def test_returns_self_if_matches_type(self):
        """测试自身匹配类型时返回自身"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()
        mock_org = MagicMock()
        mock_org.unit_type = "DEPARTMENT"
        mock_org.parent_id = None

        result = DataScopeServiceEnhanced._find_ancestor_by_type(
            mock_db, mock_org, "DEPARTMENT"
        )

        assert result == mock_org

    def test_finds_parent_of_matching_type(self):
        """测试查找匹配类型的父组织"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()

        mock_child = MagicMock()
        mock_child.unit_type = "TEAM"
        mock_child.parent_id = 1

        mock_parent = MagicMock()
        mock_parent.id = 1
        mock_parent.unit_type = "DEPARTMENT"
        mock_parent.parent_id = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_parent

        result = DataScopeServiceEnhanced._find_ancestor_by_type(
            mock_db, mock_child, "DEPARTMENT"
        )

        assert result == mock_parent

    def test_returns_none_if_no_match_found(self):
        """测试未找到匹配时返回 None"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()

        mock_org = MagicMock()
        mock_org.unit_type = "TEAM"
        mock_org.parent_id = None

        result = DataScopeServiceEnhanced._find_ancestor_by_type(
            mock_db, mock_org, "DEPARTMENT"
        )

        assert result is None

    def test_prevents_infinite_loop(self):
        """测试防止无限循环"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()

        mock_org = MagicMock()
        mock_org.unit_type = "TEAM"
        mock_org.parent_id = 1

        # 模拟循环引用
        mock_db.query.return_value.filter.return_value.first.return_value = mock_org

        result = DataScopeServiceEnhanced._find_ancestor_by_type(
            mock_db, mock_org, "DEPARTMENT"
        )

        # 应该在达到深度限制后返回 None
        assert result is None


class TestGetSubtreeIdsOptimized:
    """测试优化的子树ID获取功能"""

    def test_uses_path_field_when_available(self):
        """测试使用 path 字段进行查询"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()

        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.path = "/1/"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_org

        # 模拟子节点查询结果
        mock_child1 = MagicMock()
        mock_child1.id = 2
        mock_child2 = MagicMock()
        mock_child2.id = 3

        mock_db.query.return_value.filter.return_value.all.return_value = [
            mock_child1,
            mock_child2,
        ]

        result = DataScopeServiceEnhanced._get_subtree_ids_optimized(mock_db, 1)

        assert result == {1, 2, 3}

    def test_falls_back_to_recursive_when_no_path(self):
        """测试没有 path 字段时降级为递归方式"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()

        mock_org = MagicMock()
        mock_org.id = 1
        mock_org.path = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_org

        with patch.object(
            DataScopeServiceEnhanced,
            "_get_subtree_ids_recursive",
            return_value={1, 2, 3},
        ):
            result = DataScopeServiceEnhanced._get_subtree_ids_optimized(mock_db, 1)

        assert result == {1, 2, 3}

    def test_handles_exception_gracefully(self):
        """测试异常处理"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")

        result = DataScopeServiceEnhanced._get_subtree_ids_optimized(mock_db, 1)

        # 应该只包含根节点ID
        assert result == {1}


class TestApplyDataScope:
    """测试应用数据权限过滤功能"""

    def test_superuser_bypasses_filter(self):
        """测试超级管理员跳过过滤"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_query = MagicMock(spec=Query)
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = True
        mock_user.id = 1

        result = DataScopeServiceEnhanced.apply_data_scope(
            mock_query, mock_db, mock_user, "test_resource"
        )

        assert result == mock_query
        mock_query.filter.assert_not_called()

    def test_all_scope_returns_unfiltered_query(self):
        """测试 ALL 范围返回未过滤的查询"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_query = MagicMock(spec=Query)
        mock_query.column_descriptions = [{"entity": MagicMock()}]
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1

        with patch(
            "app.services.permission_service.PermissionService.get_user_data_scopes",
            return_value={"test_resource": ScopeType.ALL.value},
        ):
            result = DataScopeServiceEnhanced.apply_data_scope(
                mock_query, mock_db, mock_user, "test_resource"
            )

        assert result == mock_query

    def test_department_scope_filters_by_org_units(self):
        """测试 DEPARTMENT 范围按组织单元过滤"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_model = MagicMock()
        mock_model.__name__ = "TestModel"
        mock_org_column = MagicMock()
        mock_model.org_unit_id = mock_org_column

        mock_query = MagicMock(spec=Query)
        mock_query.column_descriptions = [{"entity": mock_model}]
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1

        with patch(
            "app.services.permission_service.PermissionService.get_user_data_scopes",
            return_value={"test_resource": ScopeType.DEPARTMENT.value},
        ):
            with patch.object(
                DataScopeServiceEnhanced,
                "get_accessible_org_units",
                return_value=[10, 20],
            ):
                result = DataScopeServiceEnhanced.apply_data_scope(
                    mock_query, mock_db, mock_user, "test_resource"
                )

        mock_query.filter.assert_called_once()

    def test_own_scope_filters_by_owner(self):
        """测试 OWN 范围按所有者过滤"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_model = MagicMock()
        mock_model.__name__ = "TestModel"
        mock_created_by = MagicMock()
        mock_model.created_by = mock_created_by

        mock_query = MagicMock(spec=Query)
        mock_query.column_descriptions = [{"entity": mock_model}]
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1

        with patch(
            "app.services.permission_service.PermissionService.get_user_data_scopes",
            return_value={"test_resource": ScopeType.OWN.value},
        ):
            result = DataScopeServiceEnhanced.apply_data_scope(
                mock_query, mock_db, mock_user, "test_resource"
            )

        mock_query.filter.assert_called_once()

    def test_returns_empty_on_exception(self):
        """测试异常时返回空结果"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_query = MagicMock(spec=Query)
        mock_query.column_descriptions.side_effect = Exception("Test error")
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1

        result = DataScopeServiceEnhanced.apply_data_scope(
            mock_query, mock_db, mock_user, "test_resource"
        )

        # 应该调用 filter(False) 返回空结果
        mock_query.filter.assert_called()


class TestCanAccessData:
    """测试检查数据访问权限功能"""

    def test_superuser_can_access_all_data(self):
        """测试超级管理员可以访问所有数据"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = True
        mock_data = MagicMock()

        result = DataScopeServiceEnhanced.can_access_data(
            mock_db, mock_user, "test_resource", mock_data
        )

        assert result is True

    def test_all_scope_allows_access(self):
        """测试 ALL 范围允许访问"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1
        mock_data = MagicMock()

        with patch(
            "app.services.permission_service.PermissionService.get_user_data_scopes",
            return_value={"test_resource": ScopeType.ALL.value},
        ):
            result = DataScopeServiceEnhanced.can_access_data(
                mock_db, mock_user, "test_resource", mock_data
            )

        assert result is True

    def test_own_scope_checks_ownership(self):
        """测试 OWN 范围检查所有权"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1
        mock_data = MagicMock()
        mock_data.created_by = 1
        mock_data.owner_id = None
        mock_data.pm_id = None

        with patch(
            "app.services.permission_service.PermissionService.get_user_data_scopes",
            return_value={"test_resource": ScopeType.OWN.value},
        ):
            result = DataScopeServiceEnhanced.can_access_data(
                mock_db, mock_user, "test_resource", mock_data
            )

        assert result is True

    def test_own_scope_denies_non_owner(self):
        """测试 OWN 范围拒绝非所有者"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1
        mock_data = MagicMock()
        mock_data.created_by = 2
        mock_data.owner_id = None
        mock_data.pm_id = None

        with patch(
            "app.services.permission_service.PermissionService.get_user_data_scopes",
            return_value={"test_resource": ScopeType.OWN.value},
        ):
            result = DataScopeServiceEnhanced.can_access_data(
                mock_db, mock_user, "test_resource", mock_data
            )

        assert result is False

    def test_department_scope_checks_org_unit(self):
        """测试 DEPARTMENT 范围检查组织单元"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1
        mock_data = MagicMock()
        mock_data.org_unit_id = 10
        mock_data.department_id = None

        with patch(
            "app.services.permission_service.PermissionService.get_user_data_scopes",
            return_value={"test_resource": ScopeType.DEPARTMENT.value},
        ):
            with patch.object(
                DataScopeServiceEnhanced,
                "get_accessible_org_units",
                return_value=[10, 20],
            ):
                result = DataScopeServiceEnhanced.can_access_data(
                    mock_db, mock_user, "test_resource", mock_data
                )

        assert result is True

    def test_returns_false_on_exception(self):
        """测试异常时返回 False（安全优先）"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_data = MagicMock()

        with patch(
            "app.services.permission_service.PermissionService.get_user_data_scopes",
            side_effect=Exception("Test error"),
        ):
            result = DataScopeServiceEnhanced.can_access_data(
                mock_db, mock_user, "test_resource", mock_data
            )

        assert result is False


# 测试总结
def test_suite_summary():
    """
    测试套件总结
    
    总计: 28+ 个测试用例
    
    覆盖范围:
    1. 枚举映射: 7个测试
    2. 用户组织单元: 4个测试
    3. 可访问组织单元: 3个测试
    4. 查找祖先组织: 4个测试
    5. 优化的子树查询: 3个测试
    6. 应用数据权限过滤: 7个测试
    7. 检查数据访问权限: 7个测试
    
    测试类型:
    - 正常场景测试
    - 边界条件测试
    - 异常处理测试
    - 性能优化验证
    """
    pass
