# -*- coding: utf-8 -*-
"""
DataScopeService 综合单元测试

测试覆盖:
- get_user_org_units: 获取用户所属组织单元
- get_accessible_org_units: 获取用户可访问的组织单元
- _find_ancestor_by_type: 查找指定类型的祖先组织
- _get_subtree_ids: 获取组织的子树ID
- apply_data_scope: 应用数据权限过滤
- can_access_data: 检查数据访问权限
"""

from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.models.permission import ScopeType


class TestGetUserOrgUnits:
    """测试 get_user_org_units 方法"""

    def test_returns_empty_list_when_no_assignments(self):
        """测试无分配时返回空列表"""
        from app.services.data_scope_service import DataScopeService

        mock_db = MagicMock()
        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = []

        result = DataScopeService.get_user_org_units(mock_db, user_id=1)

        assert result == []

    def test_returns_org_unit_ids_from_assignments(self):
        """测试从分配记录获取组织单元ID"""
        from app.services.data_scope_service import DataScopeService

        mock_db = MagicMock()
        mock_assignment1 = MagicMock()
        mock_assignment1.org_unit_id = 10
        mock_assignment2 = MagicMock()
        mock_assignment2.org_unit_id = 20

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [
            mock_assignment1,
            mock_assignment2,
        ]

        result = DataScopeService.get_user_org_units(mock_db, user_id=1)

        assert set(result) == {10, 20}

    def test_handles_exception_gracefully(self):
        """测试异常处理"""
        from app.services.data_scope_service import DataScopeService

        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")

        result = DataScopeService.get_user_org_units(mock_db, user_id=1)

        assert result == []

    def test_removes_duplicates(self):
        """测试去重"""
        from app.services.data_scope_service import DataScopeService

        mock_db = MagicMock()
        # 模拟多个分配指向同一组织
        mock_assignment1 = MagicMock()
        mock_assignment1.org_unit_id = 10
        mock_assignment2 = MagicMock()
        mock_assignment2.org_unit_id = 10

        mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [
            mock_assignment1,
            mock_assignment2,
        ]

        result = DataScopeService.get_user_org_units(mock_db, user_id=1)

        assert result == [10]


class TestGetAccessibleOrgUnits:
    """测试 get_accessible_org_units 方法"""

    def test_all_scope_returns_all_active_units(self):
        """测试 ALL 范围返回所有活跃单元"""
        from app.services.data_scope_service import DataScopeService

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [
            MagicMock(id=1),
            MagicMock(id=2),
            MagicMock(id=3),
        ]

        result = DataScopeService.get_accessible_org_units(
            mock_db, user_id=1, scope_type=ScopeType.ALL.value
        )

        assert result == [1, 2, 3]

    def test_returns_empty_when_user_has_no_orgs(self):
        """测试用户无组织时返回空列表"""
        from app.services.data_scope_service import DataScopeService

        mock_db = MagicMock()

        with patch.object(
            DataScopeService, "get_user_org_units", return_value=[]
        ):
            result = DataScopeService.get_accessible_org_units(
                mock_db, user_id=1, scope_type=ScopeType.DEPARTMENT.value
            )

        assert result == []

    def test_team_scope_returns_only_user_orgs(self):
        """测试 TEAM 范围只返回用户所属组织"""
        from app.services.data_scope_service import DataScopeService

        mock_db = MagicMock()
        mock_org = MagicMock()
        mock_org.id = 10

        mock_db.query.return_value.filter.return_value.first.return_value = mock_org

        with patch.object(
            DataScopeService, "get_user_org_units", return_value=[10]
        ):
            result = DataScopeService.get_accessible_org_units(
                mock_db, user_id=1, scope_type=ScopeType.TEAM.value
            )

        assert 10 in result

    def test_department_scope_uses_find_ancestor(self):
        """测试 DEPARTMENT 范围使用祖先查找"""
        from app.services.data_scope_service import DataScopeService

        mock_db = MagicMock()
        mock_org = MagicMock()
        mock_org.id = 10

        mock_db.query.return_value.filter.return_value.first.return_value = mock_org

        with patch.object(
            DataScopeService, "get_user_org_units", return_value=[10]
        ):
            with patch.object(
                DataScopeService, "_find_ancestor_by_type", return_value=None
            ):
                result = DataScopeService.get_accessible_org_units(
                    mock_db, user_id=1, scope_type=ScopeType.DEPARTMENT.value
                )

        # 没找到部门祖先，应该返回用户当前组织
        assert 10 in result

    def test_business_unit_scope_gets_subtree(self):
        """测试 BUSINESS_UNIT 范围获取子树"""
        from app.services.data_scope_service import DataScopeService

        mock_db = MagicMock()
        mock_org = MagicMock()
        mock_org.id = 10

        mock_bu = MagicMock()
        mock_bu.id = 5

        mock_db.query.return_value.filter.return_value.first.return_value = mock_org

        with patch.object(
            DataScopeService, "get_user_org_units", return_value=[10]
        ):
            with patch.object(
                DataScopeService, "_find_ancestor_by_type", return_value=mock_bu
            ):
                with patch.object(
                    DataScopeService, "_get_subtree_ids", return_value={5, 10, 11}
                ):
                    result = DataScopeService.get_accessible_org_units(
                        mock_db, user_id=1, scope_type=ScopeType.BUSINESS_UNIT.value
                    )

        assert set(result) == {5, 10, 11}


class TestFindAncestorByType:
    """测试 _find_ancestor_by_type 方法"""

    def test_returns_self_if_matches_type(self):
        """测试自身匹配类型时返回自身"""
        from app.services.data_scope_service import DataScopeService

        mock_db = MagicMock()
        mock_org = MagicMock()
        mock_org.unit_type = "DEPARTMENT"
        mock_org.parent_id = None

        result = DataScopeService._find_ancestor_by_type(
            mock_db, mock_org, "DEPARTMENT"
        )

        assert result == mock_org

    def test_returns_none_when_no_matching_ancestor(self):
        """测试无匹配祖先时返回 None"""
        from app.services.data_scope_service import DataScopeService

        mock_db = MagicMock()
        mock_org = MagicMock()
        mock_org.unit_type = "TEAM"
        mock_org.parent_id = None

        result = DataScopeService._find_ancestor_by_type(
            mock_db, mock_org, "BUSINESS_UNIT"
        )

        assert result is None

    def test_traverses_up_to_find_ancestor(self):
        """测试向上遍历查找祖先"""
        from app.services.data_scope_service import DataScopeService

        mock_db = MagicMock()

        # 当前节点是 TEAM
        mock_team = MagicMock()
        mock_team.unit_type = "TEAM"
        mock_team.parent_id = 2

        # 父节点是 DEPARTMENT
        mock_dept = MagicMock()
        mock_dept.unit_type = "DEPARTMENT"
        mock_dept.parent_id = None

        mock_db.query.return_value.filter.return_value.first.return_value = mock_dept

        result = DataScopeService._find_ancestor_by_type(
            mock_db, mock_team, "DEPARTMENT"
        )

        assert result == mock_dept


class TestGetSubtreeIds:
    """测试 _get_subtree_ids 方法"""

    def test_returns_self_when_no_children(self):
        """测试无子节点时返回自身"""
        from app.services.data_scope_service import DataScopeService

        mock_db = MagicMock()
        mock_org = MagicMock()
        mock_org.path = "/1/"
        mock_org.id = 1

        # 只返回自身
        mock_db.query.return_value.filter.return_value.first.return_value = mock_org
        mock_db.query.return_value.filter.return_value.all.return_value = [
            MagicMock(id=1)
        ]

        result = DataScopeService._get_subtree_ids(mock_db, org_unit_id=1)

        assert 1 in result

    def test_returns_all_children_with_path(self):
        """测试使用路径查找所有子节点"""
        from app.services.data_scope_service import DataScopeService

        mock_db = MagicMock()
        mock_org = MagicMock()
        mock_org.path = "/1/"
        mock_org.id = 1

        # 返回自身和子节点
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_org
        mock_query.filter.return_value.all.return_value = [
            MagicMock(id=1),
            MagicMock(id=2),
            MagicMock(id=3),
        ]
        mock_db.query.return_value = mock_query

        result = DataScopeService._get_subtree_ids(mock_db, org_unit_id=1)

        assert 1 in result

    def test_handles_org_without_path(self):
        """测试处理无路径的组织"""
        from app.services.data_scope_service import DataScopeService

        mock_db = MagicMock()
        mock_org = MagicMock()
        mock_org.path = None
        mock_org.id = 1

        # 没有子节点
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_org
        mock_query.filter.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = DataScopeService._get_subtree_ids(mock_db, org_unit_id=1)

        assert 1 in result


class TestApplyDataScope:
    """测试 apply_data_scope 方法"""

    def test_superuser_bypasses_filter(self):
        """测试超级用户绕过过滤"""
        from app.services.data_scope_service import DataScopeService

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = True

        result = DataScopeService.apply_data_scope(
            mock_query, mock_db, mock_user, "project"
        )

        assert result == mock_query

    def test_all_scope_returns_unfiltered_query(self):
        """测试 ALL 范围返回未过滤查询"""
        from app.services.data_scope_service import DataScopeService
        from app.services.permission_service import PermissionService

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.column_descriptions = [{"entity": MagicMock}]
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1

        with patch.object(
            PermissionService,
            "get_user_data_scopes",
            return_value={"project": ScopeType.ALL.value},
        ):
            result = DataScopeService.apply_data_scope(
                mock_query, mock_db, mock_user, "project"
            )

        assert result == mock_query

    def test_own_scope_filters_by_owner(self):
        """测试 OWN 范围按所有者过滤"""
        from app.services.data_scope_service import DataScopeService
        from app.services.permission_service import PermissionService

        mock_db = MagicMock()
        mock_query = MagicMock()

        # 模拟模型类
        mock_model = MagicMock()
        mock_model.created_by = MagicMock()
        mock_model.owner_id = MagicMock()
        mock_query.column_descriptions = [{"entity": mock_model}]

        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1

        with patch.object(
            PermissionService,
            "get_user_data_scopes",
            return_value={"project": ScopeType.OWN.value},
        ):
            result = DataScopeService.apply_data_scope(
                mock_query, mock_db, mock_user, "project"
            )

        # 验证过滤器被调用
        mock_query.filter.assert_called()

    def test_department_scope_filters_by_org(self):
        """测试 DEPARTMENT 范围按组织过滤"""
        from app.services.data_scope_service import DataScopeService
        from app.services.permission_service import PermissionService

        mock_db = MagicMock()
        mock_query = MagicMock()

        # 模拟模型类
        mock_model = MagicMock()
        mock_model.org_unit_id = MagicMock()
        mock_query.column_descriptions = [{"entity": mock_model}]

        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1

        with patch.object(
            PermissionService,
            "get_user_data_scopes",
            return_value={"project": ScopeType.DEPARTMENT.value},
        ):
            with patch.object(
                DataScopeService, "get_accessible_org_units", return_value=[10, 20]
            ):
                result = DataScopeService.apply_data_scope(
                    mock_query, mock_db, mock_user, "project"
                )

        mock_query.filter.assert_called()

    def test_empty_accessible_orgs_returns_false_filter(self):
        """测试无可访问组织时返回 False 过滤"""
        from app.services.data_scope_service import DataScopeService
        from app.services.permission_service import PermissionService

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.column_descriptions = [{"entity": MagicMock}]

        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1

        with patch.object(
            PermissionService,
            "get_user_data_scopes",
            return_value={"project": ScopeType.DEPARTMENT.value},
        ):
            with patch.object(
                DataScopeService, "get_accessible_org_units", return_value=[]
            ):
                result = DataScopeService.apply_data_scope(
                    mock_query, mock_db, mock_user, "project"
                )

        mock_query.filter.assert_called_with(False)


class TestCanAccessData:
    """测试 can_access_data 方法"""

    def test_superuser_always_has_access(self):
        """测试超级用户始终有权限"""
        from app.services.data_scope_service import DataScopeService

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = True
        mock_data = MagicMock()

        result = DataScopeService.can_access_data(
            mock_db, mock_user, "project", mock_data
        )

        assert result is True

    def test_all_scope_grants_access(self):
        """测试 ALL 范围授予访问权限"""
        from app.services.data_scope_service import DataScopeService
        from app.services.permission_service import PermissionService

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1
        mock_data = MagicMock()

        with patch.object(
            PermissionService,
            "get_user_data_scopes",
            return_value={"project": ScopeType.ALL.value},
        ):
            result = DataScopeService.can_access_data(
                mock_db, mock_user, "project", mock_data
            )

        assert result is True

    def test_own_scope_checks_owner_field(self):
        """测试 OWN 范围检查所有者字段"""
        from app.services.data_scope_service import DataScopeService
        from app.services.permission_service import PermissionService

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1

        mock_data = MagicMock()
        mock_data.created_by = 1  # 用户是创建者
        mock_data.owner_id = None
        mock_data.pm_id = None

        with patch.object(
            PermissionService,
            "get_user_data_scopes",
            return_value={"project": ScopeType.OWN.value},
        ):
            result = DataScopeService.can_access_data(
                mock_db, mock_user, "project", mock_data
            )

        assert result is True

    def test_own_scope_denies_non_owner(self):
        """测试 OWN 范围拒绝非所有者"""
        from app.services.data_scope_service import DataScopeService
        from app.services.permission_service import PermissionService

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1

        mock_data = MagicMock()
        mock_data.created_by = 2  # 其他用户是创建者
        mock_data.owner_id = 2
        mock_data.pm_id = 2

        with patch.object(
            PermissionService,
            "get_user_data_scopes",
            return_value={"project": ScopeType.OWN.value},
        ):
            result = DataScopeService.can_access_data(
                mock_db, mock_user, "project", mock_data
            )

        assert result is False

    def test_department_scope_checks_org_membership(self):
        """测试 DEPARTMENT 范围检查组织成员资格"""
        from app.services.data_scope_service import DataScopeService
        from app.services.permission_service import PermissionService

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1

        mock_data = MagicMock()
        mock_data.org_unit_id = 10

        with patch.object(
            PermissionService,
            "get_user_data_scopes",
            return_value={"project": ScopeType.DEPARTMENT.value},
        ):
            with patch.object(
                DataScopeService, "get_accessible_org_units", return_value=[10, 20]
            ):
                result = DataScopeService.can_access_data(
                    mock_db, mock_user, "project", mock_data
                )

        assert result is True

    def test_department_scope_denies_different_org(self):
        """测试 DEPARTMENT 范围拒绝不同组织"""
        from app.services.data_scope_service import DataScopeService
        from app.services.permission_service import PermissionService

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1

        mock_data = MagicMock()
        mock_data.org_unit_id = 30  # 不在可访问列表中
        mock_data.department_id = None

        with patch.object(
            PermissionService,
            "get_user_data_scopes",
            return_value={"project": ScopeType.DEPARTMENT.value},
        ):
            with patch.object(
                DataScopeService, "get_accessible_org_units", return_value=[10, 20]
            ):
                result = DataScopeService.can_access_data(
                    mock_db, mock_user, "project", mock_data
                )

        assert result is False

    def test_grants_access_when_data_has_no_org(self):
        """测试数据无组织字段时授予访问权限"""
        from app.services.data_scope_service import DataScopeService
        from app.services.permission_service import PermissionService

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1

        mock_data = MagicMock(spec=[])  # 无任何属性

        with patch.object(
            PermissionService,
            "get_user_data_scopes",
            return_value={"project": ScopeType.DEPARTMENT.value},
        ):
            with patch.object(
                DataScopeService, "get_accessible_org_units", return_value=[10]
            ):
                result = DataScopeService.can_access_data(
                    mock_db, mock_user, "project", mock_data
                )

        assert result is True


class TestEdgeCases:
    """测试边界情况"""

    def test_handles_none_scope_type(self):
        """测试处理 None 范围类型"""
        from app.services.data_scope_service import DataScopeService
        from app.services.permission_service import PermissionService

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1
        mock_data = MagicMock()
        mock_data.created_by = 1

        # 返回空字典，应该使用默认 OWN 范围
        with patch.object(
            PermissionService, "get_user_data_scopes", return_value={}
        ):
            result = DataScopeService.can_access_data(
                mock_db, mock_user, "project", mock_data
            )

        # 默认 OWN 范围，用户是创建者，应该有权限
        assert result is True

    def test_pm_field_grants_access(self):
        """测试项目经理字段授予访问权限"""
        from app.services.data_scope_service import DataScopeService
        from app.services.permission_service import PermissionService

        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.is_superuser = False
        mock_user.id = 1

        mock_data = MagicMock()
        mock_data.created_by = 2
        mock_data.owner_id = 2
        mock_data.pm_id = 1  # 用户是项目经理

        with patch.object(
            PermissionService,
            "get_user_data_scopes",
            return_value={"project": ScopeType.OWN.value},
        ):
            result = DataScopeService.can_access_data(
                mock_db, mock_user, "project", mock_data
            )

        assert result is True
