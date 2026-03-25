# -*- coding: utf-8 -*-
"""
工程师绩效数据范围控制单元测试

覆盖规则：
- OWN 范围：只能看到自己的绩效数据
- DEPARTMENT 范围：只能看到本部门的绩效数据
- ALL 范围：可以看到全部绩效数据
- 非授权用户访问他人详情被拒绝
- 异常场景 fail-closed（安全优先）
- 超级管理员跳过范围过滤

测试层级：service/unit 级，通过 mock 隔离数据库依赖
"""

from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.models.permission import ScopeType


# ---------------------------------------------------------------------------
# Fixtures / Helpers
# ---------------------------------------------------------------------------

def _make_user(user_id=1, is_superuser=False, department_id=10):
    """构造模拟用户"""
    user = MagicMock()
    user.id = user_id
    user.is_superuser = is_superuser
    user.department_id = department_id
    return user


def _make_perf_result(user_id, department_id, created_by=None):
    """构造模拟绩效结果数据"""
    data = MagicMock()
    data.user_id = user_id
    data.department_id = department_id
    data.created_by = created_by or user_id
    data.owner_id = user_id
    data.org_unit_id = department_id
    return data


def _make_query_with_model():
    """构造带 column_descriptions 的模拟 Query"""
    from app.models.performance.result_evaluation import PerformanceResult

    query = MagicMock()
    query.column_descriptions = [{"entity": PerformanceResult}]
    # 让 filter 返回新的 mock query 以便链式调用
    filtered = MagicMock()
    query.filter.return_value = filtered
    return query, filtered


RESOURCE_TYPE = "engineer_performance"


# ===========================================================================
# 一、apply_data_scope 查询过滤测试
# ===========================================================================

class TestApplyDataScopeEngPerf:
    """测试 DataScopeServiceEnhanced.apply_data_scope 对工程师绩效的范围过滤"""

    def setup_method(self):
        self.db = MagicMock()

    # ---- ALL 范围 ----

    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_all_scope_returns_unfiltered_query(self, mock_get_scopes):
        """ALL 范围：返回原始查询，不做过滤"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {RESOURCE_TYPE: ScopeType.ALL.value}
        user = _make_user(user_id=1)
        query, _ = _make_query_with_model()

        result = DataScopeServiceEnhanced.apply_data_scope(
            query, self.db, user, RESOURCE_TYPE,
            owner_field="created_by",
        )
        # ALL 范围应返回原始 query，不调用 filter
        assert result is query

    # ---- OWN 范围 ----

    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_own_scope_filters_by_owner(self, mock_get_scopes):
        """OWN 范围：只能看到自己的数据（通过 created_by 字段过滤）"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {RESOURCE_TYPE: ScopeType.OWN.value}
        user = _make_user(user_id=42)
        query, _ = _make_query_with_model()

        DataScopeServiceEnhanced.apply_data_scope(
            query, self.db, user, RESOURCE_TYPE,
            owner_field="created_by",
        )
        # 应该调用 filter，限制到当前用户
        query.filter.assert_called()

    # ---- DEPARTMENT 范围 ----

    @patch("app.services.data_scope_service_enhanced.DataScopeServiceEnhanced.get_accessible_org_units")
    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_department_scope_filters_by_dept(self, mock_get_scopes, mock_get_orgs):
        """DEPARTMENT 范围：只能看到本部门及子部门的数据"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {RESOURCE_TYPE: ScopeType.DEPARTMENT.value}
        mock_get_orgs.return_value = [10, 11, 12]  # 部门10及子部门11、12
        user = _make_user(user_id=1, department_id=10)
        query, _ = _make_query_with_model()

        DataScopeServiceEnhanced.apply_data_scope(
            query, self.db, user, RESOURCE_TYPE,
            owner_field="created_by",
        )
        query.filter.assert_called()
        mock_get_orgs.assert_called_once_with(self.db, 1, ScopeType.DEPARTMENT.value)

    @patch("app.services.data_scope_service_enhanced.DataScopeServiceEnhanced.get_accessible_org_units")
    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_department_scope_empty_orgs_returns_empty(self, mock_get_scopes, mock_get_orgs):
        """DEPARTMENT 范围：无关联组织单元时返回空结果"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {RESOURCE_TYPE: ScopeType.DEPARTMENT.value}
        mock_get_orgs.return_value = []  # 用户无关联组织
        user = _make_user(user_id=1)
        query, _ = _make_query_with_model()

        DataScopeServiceEnhanced.apply_data_scope(
            query, self.db, user, RESOURCE_TYPE,
            owner_field="created_by",
        )
        # 应该调用 filter(False) 返回空结果
        query.filter.assert_called_once_with(False)

    # ---- 超级管理员 ----

    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_superuser_skips_scope_filter(self, mock_get_scopes):
        """超级管理员跳过数据权限过滤，返回原始查询"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        user = _make_user(user_id=99, is_superuser=True)
        query, _ = _make_query_with_model()

        result = DataScopeServiceEnhanced.apply_data_scope(
            query, self.db, user, RESOURCE_TYPE,
            owner_field="created_by",
        )
        assert result is query
        mock_get_scopes.assert_not_called()

    # ---- 默认 scope 回退 ----

    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_no_scope_configured_defaults_to_own(self, mock_get_scopes):
        """未配置 engineer_performance 资源范围时，默认回退到 OWN"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        # 返回空字典，没有 engineer_performance 的配置
        mock_get_scopes.return_value = {}
        user = _make_user(user_id=7)
        query, _ = _make_query_with_model()

        DataScopeServiceEnhanced.apply_data_scope(
            query, self.db, user, RESOURCE_TYPE,
            owner_field="created_by",
        )
        # 默认 OWN，应该调用 filter
        query.filter.assert_called()

    # ---- 异常 fail-closed ----

    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_exception_returns_empty_result(self, mock_get_scopes):
        """权限查询异常时 fail-closed，返回空结果"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.side_effect = RuntimeError("DB down")
        user = _make_user(user_id=1)
        query, _ = _make_query_with_model()

        DataScopeServiceEnhanced.apply_data_scope(
            query, self.db, user, RESOURCE_TYPE,
            owner_field="created_by",
        )
        # 异常时应该 filter(False)
        query.filter.assert_called_once_with(False)


# ===========================================================================
# 二、can_access_data 单条记录访问控制测试
# ===========================================================================

class TestCanAccessDataEngPerf:
    """测试 DataScopeServiceEnhanced.can_access_data 对单条绩效记录的访问控制"""

    def setup_method(self):
        self.db = MagicMock()

    # ---- OWN 范围 ----

    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_own_scope_can_access_self(self, mock_get_scopes):
        """OWN 范围：可以访问自己的绩效"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {RESOURCE_TYPE: ScopeType.OWN.value}
        user = _make_user(user_id=5)
        data = _make_perf_result(user_id=5, department_id=10)

        result = DataScopeServiceEnhanced.can_access_data(
            self.db, user, RESOURCE_TYPE, data,
            owner_field="created_by",
        )
        assert result is True

    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_own_scope_cannot_access_others(self, mock_get_scopes):
        """OWN 范围：不能访问他人的绩效"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {RESOURCE_TYPE: ScopeType.OWN.value}
        user = _make_user(user_id=5)
        data = _make_perf_result(user_id=99, department_id=20)

        result = DataScopeServiceEnhanced.can_access_data(
            self.db, user, RESOURCE_TYPE, data,
            owner_field="created_by",
        )
        assert result is False

    # ---- DEPARTMENT 范围 ----

    @patch("app.services.data_scope_service_enhanced.DataScopeServiceEnhanced.get_accessible_org_units")
    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_dept_scope_can_access_same_dept(self, mock_get_scopes, mock_get_orgs):
        """DEPARTMENT 范围：可以访问同部门成员的绩效"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {RESOURCE_TYPE: ScopeType.DEPARTMENT.value}
        mock_get_orgs.return_value = [10, 11]
        user = _make_user(user_id=1, department_id=10)
        data = _make_perf_result(user_id=88, department_id=10)

        result = DataScopeServiceEnhanced.can_access_data(
            self.db, user, RESOURCE_TYPE, data,
            org_field="department_id",
        )
        assert result is True

    @patch("app.services.data_scope_service_enhanced.DataScopeServiceEnhanced.get_accessible_org_units")
    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_dept_scope_cannot_access_other_dept(self, mock_get_scopes, mock_get_orgs):
        """DEPARTMENT 范围：不能访问其他部门的绩效"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {RESOURCE_TYPE: ScopeType.DEPARTMENT.value}
        mock_get_orgs.return_value = [10, 11]  # 只能访问部门10和11
        user = _make_user(user_id=1, department_id=10)
        data = _make_perf_result(user_id=99, department_id=30)  # 部门30

        result = DataScopeServiceEnhanced.can_access_data(
            self.db, user, RESOURCE_TYPE, data,
            org_field="department_id",
        )
        assert result is False

    @patch("app.services.data_scope_service_enhanced.DataScopeServiceEnhanced.get_accessible_org_units")
    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_dept_scope_can_access_sub_dept(self, mock_get_scopes, mock_get_orgs):
        """DEPARTMENT 范围：可以访问子部门的绩效"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {RESOURCE_TYPE: ScopeType.DEPARTMENT.value}
        mock_get_orgs.return_value = [10, 11, 12]  # 10是父部门，11、12是子部门
        user = _make_user(user_id=1, department_id=10)
        data = _make_perf_result(user_id=77, department_id=12)  # 子部门12

        result = DataScopeServiceEnhanced.can_access_data(
            self.db, user, RESOURCE_TYPE, data,
            org_field="department_id",
        )
        assert result is True

    # ---- ALL 范围 ----

    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_all_scope_can_access_any(self, mock_get_scopes):
        """ALL 范围：可以访问任何人的绩效"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {RESOURCE_TYPE: ScopeType.ALL.value}
        user = _make_user(user_id=1)
        data = _make_perf_result(user_id=999, department_id=50)

        result = DataScopeServiceEnhanced.can_access_data(
            self.db, user, RESOURCE_TYPE, data,
            owner_field="created_by",
        )
        assert result is True

    # ---- 超级管理员 ----

    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_superuser_can_access_any(self, mock_get_scopes):
        """超级管理员可以访问任何人的绩效"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        user = _make_user(user_id=99, is_superuser=True)
        data = _make_perf_result(user_id=888, department_id=50)

        result = DataScopeServiceEnhanced.can_access_data(
            self.db, user, RESOURCE_TYPE, data,
            owner_field="created_by",
        )
        assert result is True
        mock_get_scopes.assert_not_called()

    # ---- 异常 fail-closed ----

    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_exception_denies_access(self, mock_get_scopes):
        """权限查询异常时 fail-closed，拒绝访问"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.side_effect = RuntimeError("DB down")
        user = _make_user(user_id=1)
        data = _make_perf_result(user_id=1, department_id=10)

        result = DataScopeServiceEnhanced.can_access_data(
            self.db, user, RESOURCE_TYPE, data,
            owner_field="created_by",
        )
        assert result is False

    # ---- 未配置默认回退 ----

    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_no_scope_defaults_to_own_denies_other(self, mock_get_scopes):
        """未配置范围时默认 OWN，拒绝访问他人数据"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {}  # 没有配置 engineer_performance
        user = _make_user(user_id=5)
        data = _make_perf_result(user_id=99, department_id=20)

        result = DataScopeServiceEnhanced.can_access_data(
            self.db, user, RESOURCE_TYPE, data,
            owner_field="created_by",
        )
        assert result is False


# ===========================================================================
# 三、PermissionService.get_user_data_scopes 范围合并测试
# ===========================================================================

class TestDataScopeMerge:
    """测试多角色场景下数据范围取最大权限"""

    def setup_method(self):
        self.db = MagicMock()

    @patch("app.services.permission_service.PermissionService.get_user_effective_roles")
    def test_multiple_roles_take_highest_scope(self, mock_get_roles):
        """多角色时取最大范围：OWN + DEPARTMENT → DEPARTMENT"""
        from app.services.permission_service import PermissionService

        # 模拟两个角色
        role_own = MagicMock()
        role_own.id = 1
        role_dept = MagicMock()
        role_dept.id = 2
        mock_get_roles.return_value = [role_own, role_dept]

        # 模拟 RoleDataScope 查询
        rds_own = MagicMock()
        rds_own.resource_type = RESOURCE_TYPE
        rds_own.scope_rule_id = 101

        rds_dept = MagicMock()
        rds_dept.resource_type = RESOURCE_TYPE
        rds_dept.scope_rule_id = 102

        rule_own = MagicMock()
        rule_own.scope_type = "OWN"
        rule_dept = MagicMock()
        rule_dept.scope_type = "DEPARTMENT"

        # 设置 db.query 链
        rds_query = MagicMock()
        rds_query.filter.return_value = rds_query
        rds_query.all.return_value = [rds_own, rds_dept]

        rule_query = MagicMock()

        def query_side_effect(model):
            from app.models.permission import RoleDataScope, DataScopeRule
            if model is RoleDataScope:
                return rds_query
            if model is DataScopeRule:
                return rule_query
            return MagicMock()

        self.db.query.side_effect = query_side_effect

        # DataScopeRule 查询
        def rule_filter_side_effect(*args, **kwargs):
            mock_filtered = MagicMock()
            # 根据调用顺序返回不同的 rule
            if not hasattr(rule_filter_side_effect, '_call_count'):
                rule_filter_side_effect._call_count = 0
            rule_filter_side_effect._call_count += 1
            if rule_filter_side_effect._call_count == 1:
                mock_filtered.first.return_value = rule_own
            else:
                mock_filtered.first.return_value = rule_dept
            return mock_filtered

        rule_query.filter.side_effect = rule_filter_side_effect

        result = PermissionService.get_user_data_scopes(self.db, user_id=1)
        assert result.get(RESOURCE_TYPE) == "DEPARTMENT"


# ===========================================================================
# 四、跨角色场景端到端测试
# ===========================================================================

class TestEngPerfScopeScenarios:
    """模拟真实业务场景的端到端范围测试"""

    def setup_method(self):
        self.db = MagicMock()

    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_engineer_cannot_view_colleague_detail(self, mock_get_scopes):
        """普通工程师(OWN)不能查看同事的绩效详情"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {RESOURCE_TYPE: "OWN"}
        engineer = _make_user(user_id=10, department_id=5)
        colleague_data = _make_perf_result(user_id=11, department_id=5)

        assert DataScopeServiceEnhanced.can_access_data(
            self.db, engineer, RESOURCE_TYPE, colleague_data,
            owner_field="created_by",
        ) is False

    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_engineer_can_view_own_detail(self, mock_get_scopes):
        """普通工程师(OWN)可以查看自己的绩效详情"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {RESOURCE_TYPE: "OWN"}
        engineer = _make_user(user_id=10, department_id=5)
        own_data = _make_perf_result(user_id=10, department_id=5)

        assert DataScopeServiceEnhanced.can_access_data(
            self.db, engineer, RESOURCE_TYPE, own_data,
            owner_field="created_by",
        ) is True

    @patch("app.services.data_scope_service_enhanced.DataScopeServiceEnhanced.get_accessible_org_units")
    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_manager_can_view_dept_member(self, mock_get_scopes, mock_get_orgs):
        """部门经理(DEPARTMENT)可以查看本部门工程师的绩效"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {RESOURCE_TYPE: "DEPARTMENT"}
        mock_get_orgs.return_value = [5, 6]  # 部门5和子部门6
        manager = _make_user(user_id=1, department_id=5)
        member_data = _make_perf_result(user_id=10, department_id=5)

        assert DataScopeServiceEnhanced.can_access_data(
            self.db, manager, RESOURCE_TYPE, member_data,
            org_field="department_id",
        ) is True

    @patch("app.services.data_scope_service_enhanced.DataScopeServiceEnhanced.get_accessible_org_units")
    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_manager_cannot_view_other_dept(self, mock_get_scopes, mock_get_orgs):
        """部门经理(DEPARTMENT)不能查看其他部门工程师的绩效"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {RESOURCE_TYPE: "DEPARTMENT"}
        mock_get_orgs.return_value = [5, 6]
        manager = _make_user(user_id=1, department_id=5)
        other_dept_data = _make_perf_result(user_id=20, department_id=8)

        assert DataScopeServiceEnhanced.can_access_data(
            self.db, manager, RESOURCE_TYPE, other_dept_data,
            org_field="department_id",
        ) is False

    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_hr_admin_can_view_all(self, mock_get_scopes):
        """HR/管理员(ALL)可以查看全公司绩效"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {RESOURCE_TYPE: "ALL"}
        hr = _make_user(user_id=100, department_id=1)
        any_data = _make_perf_result(user_id=999, department_id=50)

        assert DataScopeServiceEnhanced.can_access_data(
            self.db, hr, RESOURCE_TYPE, any_data,
            owner_field="created_by",
        ) is True

    @patch("app.services.data_scope_service_enhanced.DataScopeServiceEnhanced.get_accessible_org_units")
    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_ranking_query_filtered_by_dept_scope(self, mock_get_scopes, mock_get_orgs):
        """DEPARTMENT 范围下排行榜查询只包含本部门数据"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {RESOURCE_TYPE: "DEPARTMENT"}
        mock_get_orgs.return_value = [5]
        manager = _make_user(user_id=1, department_id=5)
        query, filtered = _make_query_with_model()

        result = DataScopeServiceEnhanced.apply_data_scope(
            query, self.db, manager, RESOURCE_TYPE,
            owner_field="created_by",
        )
        # 应该对 query 调用 filter
        query.filter.assert_called()

    @patch("app.services.data_scope_service_enhanced.PermissionService.get_user_data_scopes")
    def test_ranking_query_unfiltered_for_all_scope(self, mock_get_scopes):
        """ALL 范围下排行榜查询不过滤"""
        from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced

        mock_get_scopes.return_value = {RESOURCE_TYPE: "ALL"}
        hr = _make_user(user_id=100)
        query, _ = _make_query_with_model()

        result = DataScopeServiceEnhanced.apply_data_scope(
            query, self.db, hr, RESOURCE_TYPE,
            owner_field="created_by",
        )
        assert result is query
