# -*- coding: utf-8 -*-
"""
数据权限服务增强版单元测试 v2
测试覆盖目标：70%+ (429行源码)
测试用例数量：25-35个
"""

import unittest
from unittest.mock import MagicMock, Mock, patch, PropertyMock
from typing import List, Set

from app.services.data_scope_service_enhanced import (
    DataScopeServiceEnhanced,
    SCOPE_TYPE_MAPPING,
)
from app.models.enums import DataScopeEnum
from app.models.permission import ScopeType


class TestDataScopeServiceEnhanced(unittest.TestCase):
    """数据权限服务增强版测试"""

    def setUp(self):
        """每个测试前的初始化"""
        self.db = MagicMock()
        self.user = MagicMock()
        self.user.id = 1
        self.user.is_superuser = False
        self.service = DataScopeServiceEnhanced()

    # ==================== normalize_scope_type 测试 ====================

    def test_normalize_scope_type_all(self):
        """测试 ALL 范围类型标准化"""
        result = DataScopeServiceEnhanced.normalize_scope_type(ScopeType.ALL.value)
        self.assertEqual(result, DataScopeEnum.ALL.value)

    def test_normalize_scope_type_business_unit(self):
        """测试 BUSINESS_UNIT 范围类型标准化"""
        result = DataScopeServiceEnhanced.normalize_scope_type(ScopeType.BUSINESS_UNIT.value)
        self.assertEqual(result, DataScopeEnum.DEPT.value)

    def test_normalize_scope_type_department(self):
        """测试 DEPARTMENT 范围类型标准化"""
        result = DataScopeServiceEnhanced.normalize_scope_type(ScopeType.DEPARTMENT.value)
        self.assertEqual(result, DataScopeEnum.DEPT.value)

    def test_normalize_scope_type_team(self):
        """测试 TEAM 范围类型标准化"""
        result = DataScopeServiceEnhanced.normalize_scope_type(ScopeType.TEAM.value)
        self.assertEqual(result, DataScopeEnum.DEPT.value)

    def test_normalize_scope_type_project(self):
        """测试 PROJECT 范围类型标准化"""
        result = DataScopeServiceEnhanced.normalize_scope_type(ScopeType.PROJECT.value)
        self.assertEqual(result, DataScopeEnum.PROJECT.value)

    def test_normalize_scope_type_own(self):
        """测试 OWN 范围类型标准化"""
        result = DataScopeServiceEnhanced.normalize_scope_type(ScopeType.OWN.value)
        self.assertEqual(result, DataScopeEnum.OWN.value)

    def test_normalize_scope_type_unknown(self):
        """测试未知范围类型（应返回原值）"""
        unknown_type = "UNKNOWN_TYPE"
        result = DataScopeServiceEnhanced.normalize_scope_type(unknown_type)
        self.assertEqual(result, unknown_type)

    # ==================== get_user_org_units 测试 ====================

    @patch('app.services.data_scope_service_enhanced.User')
    @patch('app.services.data_scope_service_enhanced.EmployeeOrgAssignment')
    def test_get_user_org_units_success(self, mock_assignment, mock_user):
        """测试成功获取用户组织单元"""
        # 模拟数据库查询返回
        assignment1 = MagicMock()
        assignment1.org_unit_id = 10
        assignment2 = MagicMock()
        assignment2.org_unit_id = 20

        query_mock = MagicMock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [assignment1, assignment2]

        self.db.query.return_value = query_mock

        result = DataScopeServiceEnhanced.get_user_org_units(self.db, 1)

        self.assertEqual(sorted(result), [10, 20])

    @patch('app.services.data_scope_service_enhanced.User')
    @patch('app.services.data_scope_service_enhanced.EmployeeOrgAssignment')
    def test_get_user_org_units_empty(self, mock_assignment, mock_user):
        """测试用户没有组织单元"""
        query_mock = MagicMock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = []

        self.db.query.return_value = query_mock

        result = DataScopeServiceEnhanced.get_user_org_units(self.db, 1)

        self.assertEqual(result, [])

    @patch('app.services.data_scope_service_enhanced.User')
    @patch('app.services.data_scope_service_enhanced.EmployeeOrgAssignment')
    def test_get_user_org_units_exception(self, mock_assignment, mock_user):
        """测试获取用户组织单元时异常处理"""
        query_mock = MagicMock()
        query_mock.join.side_effect = Exception("Database error")

        self.db.query.return_value = query_mock

        result = DataScopeServiceEnhanced.get_user_org_units(self.db, 1)

        self.assertEqual(result, [])

    @patch('app.services.data_scope_service_enhanced.User')
    @patch('app.services.data_scope_service_enhanced.EmployeeOrgAssignment')
    def test_get_user_org_units_duplicates(self, mock_assignment, mock_user):
        """测试去重功能（用户可能在同一组织有多个分配）"""
        assignment1 = MagicMock()
        assignment1.org_unit_id = 10
        assignment2 = MagicMock()
        assignment2.org_unit_id = 10  # 重复

        query_mock = MagicMock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [assignment1, assignment2]

        self.db.query.return_value = query_mock

        result = DataScopeServiceEnhanced.get_user_org_units(self.db, 1)

        self.assertEqual(result, [10])

    # ==================== _find_ancestor_by_type 测试 ====================

    @patch('app.services.data_scope_service_enhanced.OrganizationUnit')
    def test_find_ancestor_by_type_direct_match(self, mock_org_unit):
        """测试直接匹配祖先类型"""
        org_unit = MagicMock()
        org_unit.unit_type = "DEPARTMENT"
        org_unit.parent_id = None

        result = DataScopeServiceEnhanced._find_ancestor_by_type(
            self.db, org_unit, "DEPARTMENT"
        )

        self.assertEqual(result, org_unit)

    @patch('app.services.data_scope_service_enhanced.OrganizationUnit')
    def test_find_ancestor_by_type_parent_match(self, mock_org_unit):
        """测试父级匹配祖先类型"""
        parent_unit = MagicMock()
        parent_unit.unit_type = "BUSINESS_UNIT"
        parent_unit.parent_id = None

        child_unit = MagicMock()
        child_unit.unit_type = "TEAM"
        child_unit.parent_id = 100

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = parent_unit

        self.db.query.return_value = query_mock

        result = DataScopeServiceEnhanced._find_ancestor_by_type(
            self.db, child_unit, "BUSINESS_UNIT"
        )

        self.assertEqual(result, parent_unit)

    @patch('app.services.data_scope_service_enhanced.OrganizationUnit')
    def test_find_ancestor_by_type_no_match(self, mock_org_unit):
        """测试找不到匹配的祖先"""
        org_unit = MagicMock()
        org_unit.unit_type = "TEAM"
        org_unit.parent_id = None

        result = DataScopeServiceEnhanced._find_ancestor_by_type(
            self.db, org_unit, "BUSINESS_UNIT"
        )

        self.assertIsNone(result)

    @patch('app.services.data_scope_service_enhanced.OrganizationUnit')
    def test_find_ancestor_by_type_max_depth_protection(self, mock_org_unit):
        """测试最大深度保护（防止无限循环）"""
        # 创建一个循环引用的组织树
        org_unit = MagicMock()
        org_unit.unit_type = "TEAM"
        org_unit.parent_id = 1

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = org_unit  # 总是返回自己，形成循环

        self.db.query.return_value = query_mock

        result = DataScopeServiceEnhanced._find_ancestor_by_type(
            self.db, org_unit, "BUSINESS_UNIT"
        )

        # 应该在达到最大深度后返回 None
        self.assertIsNone(result)

    # ==================== _get_subtree_ids_optimized 测试 ====================

    @patch('app.services.data_scope_service_enhanced.OrganizationUnit')
    def test_get_subtree_ids_optimized_with_path(self, mock_org_unit):
        """测试使用 path 字段获取子树ID"""
        org = MagicMock()
        org.id = 1
        org.path = "/1/"
        org.is_active = True

        child1 = MagicMock()
        child1.id = 2
        child2 = MagicMock()
        child2.id = 3

        query_mock = MagicMock()
        filter_mock = MagicMock()
        filter_mock.all.return_value = [child1, child2]
        query_mock.filter.return_value = filter_mock
        query_mock.first.return_value = org

        self.db.query.return_value = query_mock

        result = DataScopeServiceEnhanced._get_subtree_ids_optimized(self.db, 1)

        self.assertEqual(result, {1, 2, 3})

    @patch('app.services.data_scope_service_enhanced.OrganizationUnit')
    def test_get_subtree_ids_optimized_no_path(self, mock_org_unit):
        """测试没有 path 字段时降级到递归方式"""
        org = MagicMock()
        org.id = 1
        org.path = None

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = org
        query_mock.all.return_value = []  # 没有子节点

        self.db.query.return_value = query_mock

        result = DataScopeServiceEnhanced._get_subtree_ids_optimized(self.db, 1)

        self.assertEqual(result, {1})

    @patch('app.services.data_scope_service_enhanced.OrganizationUnit')
    def test_get_subtree_ids_optimized_exception(self, mock_org_unit):
        """测试异常处理"""
        query_mock = MagicMock()
        query_mock.filter.side_effect = Exception("DB error")

        self.db.query.return_value = query_mock

        result = DataScopeServiceEnhanced._get_subtree_ids_optimized(self.db, 1)

        # 应该至少返回自己的ID
        self.assertEqual(result, {1})

    # ==================== _get_subtree_ids_recursive 测试 ====================

    @patch('app.services.data_scope_service_enhanced.OrganizationUnit')
    def test_get_subtree_ids_recursive_no_children(self, mock_org_unit):
        """测试递归获取子树（无子节点）"""
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = []

        self.db.query.return_value = query_mock

        result = DataScopeServiceEnhanced._get_subtree_ids_recursive(self.db, 1)

        self.assertEqual(result, {1})

    @patch('app.services.data_scope_service_enhanced.OrganizationUnit')
    def test_get_subtree_ids_recursive_with_children(self, mock_org_unit):
        """测试递归获取子树（有子节点）"""
        child1 = MagicMock()
        child1.id = 2
        child2 = MagicMock()
        child2.id = 3

        # 第一次调用返回子节点，后续调用返回空
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.side_effect = [[child1, child2], [], []]

        self.db.query.return_value = query_mock

        result = DataScopeServiceEnhanced._get_subtree_ids_recursive(self.db, 1)

        self.assertEqual(result, {1, 2, 3})

    # ==================== get_accessible_org_units 测试 ====================

    @patch('app.services.data_scope_service_enhanced.OrganizationUnit')
    def test_get_accessible_org_units_all_scope(self, mock_org_unit):
        """测试 ALL 范围返回所有组织单元"""
        org1 = MagicMock()
        org1.id = 1
        org2 = MagicMock()
        org2.id = 2

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [org1, org2]

        self.db.query.return_value = query_mock

        result = DataScopeServiceEnhanced.get_accessible_org_units(
            self.db, 1, ScopeType.ALL.value
        )

        self.assertEqual(sorted(result), [1, 2])

    @patch('app.services.data_scope_service_enhanced.DataScopeServiceEnhanced.get_user_org_units')
    def test_get_accessible_org_units_no_user_orgs(self, mock_get_user_orgs):
        """测试用户没有组织单元时返回空列表"""
        mock_get_user_orgs.return_value = []

        result = DataScopeServiceEnhanced.get_accessible_org_units(
            self.db, 1, ScopeType.DEPARTMENT.value
        )

        self.assertEqual(result, [])

    @patch('app.services.data_scope_service_enhanced.DataScopeServiceEnhanced._get_subtree_ids_optimized')
    @patch('app.services.data_scope_service_enhanced.DataScopeServiceEnhanced._find_ancestor_by_type')
    @patch('app.services.data_scope_service_enhanced.DataScopeServiceEnhanced.get_user_org_units')
    @patch('app.services.data_scope_service_enhanced.OrganizationUnit')
    def test_get_accessible_org_units_business_unit_scope(
        self, mock_org_unit, mock_get_user_orgs, mock_find_ancestor, mock_get_subtree
    ):
        """测试 BUSINESS_UNIT 范围"""
        mock_get_user_orgs.return_value = [10]

        org = MagicMock()
        org.id = 10

        bu = MagicMock()
        bu.id = 1

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = org

        self.db.query.return_value = query_mock

        mock_find_ancestor.return_value = bu
        mock_get_subtree.return_value = {1, 10, 11, 12}

        result = DataScopeServiceEnhanced.get_accessible_org_units(
            self.db, 1, ScopeType.BUSINESS_UNIT.value
        )

        self.assertEqual(result, [1, 10, 11, 12])

    @patch('app.services.data_scope_service_enhanced.DataScopeServiceEnhanced.get_user_org_units')
    @patch('app.services.data_scope_service_enhanced.OrganizationUnit')
    def test_get_accessible_org_units_team_scope(self, mock_org_unit, mock_get_user_orgs):
        """测试 TEAM 范围（仅返回用户所在组织）"""
        mock_get_user_orgs.return_value = [10, 20]

        org1 = MagicMock()
        org1.id = 10
        org2 = MagicMock()
        org2.id = 20

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.side_effect = [org1, org2]

        self.db.query.return_value = query_mock

        result = DataScopeServiceEnhanced.get_accessible_org_units(
            self.db, 1, ScopeType.TEAM.value
        )

        self.assertEqual(sorted(result), [10, 20])

    # ==================== apply_data_scope 测试 ====================

    def test_apply_data_scope_superuser(self):
        """测试超级管理员跳过数据权限过滤"""
        self.user.is_superuser = True
        query = MagicMock()

        result = DataScopeServiceEnhanced.apply_data_scope(
            query, self.db, self.user, "task"
        )

        self.assertEqual(result, query)
        query.filter.assert_not_called()

    @patch('app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes')
    def test_apply_data_scope_all_scope(self, mock_get_scopes):
        """测试 ALL 范围不添加过滤"""
        mock_get_scopes.return_value = {"task": ScopeType.ALL.value}
        query = MagicMock()

        result = DataScopeServiceEnhanced.apply_data_scope(
            query, self.db, self.user, "task"
        )

        self.assertEqual(result, query)

    @patch('app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes')
    @patch('app.services.data_scope_service_enhanced.DataScopeServiceEnhanced.get_accessible_org_units')
    def test_apply_data_scope_department_with_field(self, mock_get_orgs, mock_get_scopes):
        """测试部门范围过滤（模型有组织字段）"""
        mock_get_scopes.return_value = {"task": ScopeType.DEPARTMENT.value}
        mock_get_orgs.return_value = [10, 20]

        # 模拟查询对象
        model_class = MagicMock()
        model_class.__name__ = "Task"
        org_field_mock = MagicMock()
        model_class.org_unit_id = org_field_mock

        query = MagicMock()
        query.column_descriptions = [{"entity": model_class}]

        result = DataScopeServiceEnhanced.apply_data_scope(
            query, self.db, self.user, "task", org_field="org_unit_id"
        )

        # 验证调用了 filter 和 in_
        self.assertTrue(query.filter.called)

    @patch('app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes')
    @patch('app.services.data_scope_service_enhanced.DataScopeServiceEnhanced.get_accessible_org_units')
    def test_apply_data_scope_department_no_orgs(self, mock_get_orgs, mock_get_scopes):
        """测试部门范围但用户无可访问组织（返回空）"""
        mock_get_scopes.return_value = {"task": ScopeType.DEPARTMENT.value}
        mock_get_orgs.return_value = []

        model_class = MagicMock()
        model_class.__name__ = "Task"

        query = MagicMock()
        query.column_descriptions = [{"entity": model_class}]

        result = DataScopeServiceEnhanced.apply_data_scope(
            query, self.db, self.user, "task"
        )

        # 应该过滤为 False（空结果）
        query.filter.assert_called_with(False)

    @patch('app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes')
    def test_apply_data_scope_own_with_owner_field(self, mock_get_scopes):
        """测试 OWN 范围过滤（有 owner 字段）"""
        mock_get_scopes.return_value = {"task": ScopeType.OWN.value}

        model_class = MagicMock()
        model_class.__name__ = "Task"
        model_class.created_by = MagicMock()

        query = MagicMock()
        query.column_descriptions = [{"entity": model_class}]

        result = DataScopeServiceEnhanced.apply_data_scope(
            query, self.db, self.user, "task", owner_field="created_by"
        )

        # 验证调用了 filter
        self.assertTrue(query.filter.called)

    @patch('app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes')
    def test_apply_data_scope_project_with_pm_field(self, mock_get_scopes):
        """测试 PROJECT 范围过滤（有 PM 字段）"""
        mock_get_scopes.return_value = {"project": ScopeType.PROJECT.value}

        model_class = MagicMock()
        model_class.__name__ = "Project"
        model_class.created_by = MagicMock()
        model_class.pm_id = MagicMock()

        query = MagicMock()
        query.column_descriptions = [{"entity": model_class}]

        result = DataScopeServiceEnhanced.apply_data_scope(
            query, self.db, self.user, "project", pm_field="pm_id"
        )

        # 验证调用了 filter
        self.assertTrue(query.filter.called)

    @patch('app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes')
    def test_apply_data_scope_exception(self, mock_get_scopes):
        """测试异常处理（返回空结果）"""
        mock_get_scopes.side_effect = Exception("Permission service error")

        query = MagicMock()
        query.column_descriptions = [{"entity": MagicMock()}]

        result = DataScopeServiceEnhanced.apply_data_scope(
            query, self.db, self.user, "task"
        )

        # 异常时应返回空结果（安全优先）
        query.filter.assert_called_with(False)

    # ==================== can_access_data 测试 ====================

    def test_can_access_data_superuser(self):
        """测试超级管理员可以访问所有数据"""
        self.user.is_superuser = True
        data = MagicMock()

        result = DataScopeServiceEnhanced.can_access_data(
            self.db, self.user, "task", data
        )

        self.assertTrue(result)

    @patch('app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes')
    def test_can_access_data_all_scope(self, mock_get_scopes):
        """测试 ALL 范围允许访问所有数据"""
        mock_get_scopes.return_value = {"task": ScopeType.ALL.value}
        data = MagicMock()

        result = DataScopeServiceEnhanced.can_access_data(
            self.db, self.user, "task", data
        )

        self.assertTrue(result)

    @patch('app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes')
    @patch('app.services.data_scope_service_enhanced.DataScopeServiceEnhanced.get_accessible_org_units')
    def test_can_access_data_department_has_access(self, mock_get_orgs, mock_get_scopes):
        """测试部门范围，用户有访问权限"""
        mock_get_scopes.return_value = {"task": ScopeType.DEPARTMENT.value}
        mock_get_orgs.return_value = [10, 20]

        data = MagicMock()
        data.org_unit_id = 10

        result = DataScopeServiceEnhanced.can_access_data(
            self.db, self.user, "task", data, org_field="org_unit_id"
        )

        self.assertTrue(result)

    @patch('app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes')
    @patch('app.services.data_scope_service_enhanced.DataScopeServiceEnhanced.get_accessible_org_units')
    def test_can_access_data_department_no_access(self, mock_get_orgs, mock_get_scopes):
        """测试部门范围，用户无访问权限"""
        mock_get_scopes.return_value = {"task": ScopeType.DEPARTMENT.value}
        mock_get_orgs.return_value = [10, 20]

        data = MagicMock()
        data.org_unit_id = 30  # 不在可访问列表中

        result = DataScopeServiceEnhanced.can_access_data(
            self.db, self.user, "task", data, org_field="org_unit_id"
        )

        self.assertFalse(result)

    @patch('app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes')
    def test_can_access_data_own_is_owner(self, mock_get_scopes):
        """测试 OWN 范围，用户是所有者"""
        mock_get_scopes.return_value = {"task": ScopeType.OWN.value}

        data = MagicMock()
        data.created_by = 1  # 用户ID为1
        data.owner_id = None
        data.pm_id = None

        result = DataScopeServiceEnhanced.can_access_data(
            self.db, self.user, "task", data, owner_field="created_by"
        )

        self.assertTrue(result)

    @patch('app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes')
    def test_can_access_data_own_not_owner(self, mock_get_scopes):
        """测试 OWN 范围，用户不是所有者"""
        mock_get_scopes.return_value = {"task": ScopeType.OWN.value}

        data = MagicMock()
        data.created_by = 2  # 其他用户
        data.owner_id = None
        data.pm_id = None

        result = DataScopeServiceEnhanced.can_access_data(
            self.db, self.user, "task", data, owner_field="created_by"
        )

        self.assertFalse(result)

    @patch('app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes')
    def test_can_access_data_exception(self, mock_get_scopes):
        """测试异常处理（拒绝访问）"""
        mock_get_scopes.side_effect = Exception("Permission error")

        data = MagicMock()

        result = DataScopeServiceEnhanced.can_access_data(
            self.db, self.user, "task", data
        )

        # 异常时应拒绝访问（安全优先）
        self.assertFalse(result)

    @patch('app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes')
    @patch('app.services.data_scope_service_enhanced.DataScopeServiceEnhanced.get_accessible_org_units')
    def test_can_access_data_department_no_org_field(self, mock_get_orgs, mock_get_scopes):
        """测试数据没有组织字段时允许访问"""
        mock_get_scopes.return_value = {"task": ScopeType.DEPARTMENT.value}
        mock_get_orgs.return_value = [10, 20]

        data = MagicMock()
        # 模拟数据没有 org_unit_id 和 department_id
        data.org_unit_id = None
        data.department_id = None

        result = DataScopeServiceEnhanced.can_access_data(
            self.db, self.user, "task", data, org_field="org_unit_id"
        )

        self.assertTrue(result)

    # ==================== 边界条件测试 ====================

    def test_scope_type_mapping_completeness(self):
        """测试 SCOPE_TYPE_MAPPING 是否完整"""
        expected_keys = [
            ScopeType.ALL.value,
            ScopeType.BUSINESS_UNIT.value,
            ScopeType.DEPARTMENT.value,
            ScopeType.TEAM.value,
            ScopeType.PROJECT.value,
            ScopeType.OWN.value,
        ]

        for key in expected_keys:
            self.assertIn(key, SCOPE_TYPE_MAPPING)


if __name__ == "__main__":
    unittest.main()
