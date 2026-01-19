# -*- coding: utf-8 -*-
"""
销售权限模块单元测试

测试 app/core/sales_permissions.py 中的销售权限功能
"""

from unittest.mock import MagicMock, patch

import pytest


class MockUser:
    """模拟用户对象"""

    def __init__(
        self,
        is_superuser: bool = False,
        roles: list = None,
        department: str = None,
        user_id: int = 1,
    ):
        self.is_superuser = is_superuser
        self.id = user_id
        self.department = department
        self.roles = roles or []


class MockUserRole:
    """模拟用户角色关联对象"""

    def __init__(self, role_code: str, role_name: str = None):
        self.role = MagicMock()
        self.role.role_code = role_code
        self.role.role_name = role_name or role_code
        self.role.is_active = True


class TestGetSalesDataScope:
    """销售数据范围权限测试"""

    def test_get_sales_data_scope_superuser(self):
        """测试超级用户返回ALL"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(is_superuser=True)
        db = MagicMock()
        assert get_sales_data_scope(user, db) == "ALL"

    def test_get_sales_data_scope_sales_director(self):
        """测试销售总监返回ALL"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(roles=[MockUserRole("SALES_DIRECTOR", "销售总监")])
        db = MagicMock()
        assert get_sales_data_scope(user, db) == "ALL"

    def test_get_sales_data_scope_sales_director_chinese(self):
        """测试中文销售总监返回ALL"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(roles=[MockUserRole("销售总监", "销售总监")])
        db = MagicMock()
        assert get_sales_data_scope(user, db) == "ALL"

    def test_get_sales_data_scope_sales_manager(self):
        """测试销售经理返回TEAM"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(roles=[MockUserRole("SALES_MANAGER", "销售经理")])
        db = MagicMock()
        assert get_sales_data_scope(user, db) == "TEAM"

    def test_get_sales_data_scope_finance(self):
        """测试财务返回FINANCE_ONLY"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(roles=[MockUserRole("FINANCE", "财务")])
        db = MagicMock()
        assert get_sales_data_scope(user, db) == "FINANCE_ONLY"

    def test_get_sales_data_scope_sales(self):
        """测试销售返回OWN"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(roles=[MockUserRole("SALES", "销售")])
        db = MagicMock()
        assert get_sales_data_scope(user, db) == "OWN"

    def test_get_sales_data_scope_presales(self):
        """测试售前返回OWN"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(roles=[MockUserRole("PRESALES", "售前")])
        db = MagicMock()
        assert get_sales_data_scope(user, db) == "OWN"

    def test_get_sales_data_scope_no_role(self):
        """测试无角色返回NONE"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(roles=[])
        db = MagicMock()
        assert get_sales_data_scope(user, db) == "NONE"

    def test_get_sales_data_scope_unknown_role(self):
        """测试未知角色返回NONE"""
        from app.core.sales_permissions import get_sales_data_scope

        user = MockUser(roles=[MockUserRole("ENGINEER", "工程师")])
        db = MagicMock()
        assert get_sales_data_scope(user, db) == "NONE"


class TestCheckSalesCreatePermission:
    """销售创建权限测试"""

    def test_check_sales_create_permission_superuser(self):
        """测试超级用户有创建权限"""
        from app.core.sales_permissions import check_sales_create_permission

        user = MockUser(is_superuser=True)
        db = MagicMock()
        assert check_sales_create_permission(user, db) is True

    def test_check_sales_create_permission_sales_director(self):
        """测试销售总监有创建权限"""
        from app.core.sales_permissions import check_sales_create_permission

        user = MockUser(roles=[MockUserRole("SALES_DIRECTOR")])
        db = MagicMock()
        assert check_sales_create_permission(user, db) is True

    def test_check_sales_create_permission_sales_manager(self):
        """测试销售经理有创建权限"""
        from app.core.sales_permissions import check_sales_create_permission

        user = MockUser(roles=[MockUserRole("SALES_MANAGER")])
        db = MagicMock()
        assert check_sales_create_permission(user, db) is True

    def test_check_sales_create_permission_sales(self):
        """测试销售有创建权限"""
        from app.core.sales_permissions import check_sales_create_permission

        user = MockUser(roles=[MockUserRole("SALES")])
        db = MagicMock()
        assert check_sales_create_permission(user, db) is True

    def test_check_sales_create_permission_finance(self):
        """测试财务无创建权限"""
        from app.core.sales_permissions import check_sales_create_permission

        user = MockUser(roles=[MockUserRole("FINANCE")])
        db = MagicMock()
        assert check_sales_create_permission(user, db) is False

    def test_check_sales_create_permission_no_role(self):
        """测试无角色无创建权限"""
        from app.core.sales_permissions import check_sales_create_permission

        user = MockUser(roles=[])
        db = MagicMock()
        assert check_sales_create_permission(user, db) is False


class TestCheckSalesEditPermission:
    """销售编辑权限测试"""

    def test_check_sales_edit_permission_superuser(self):
        """测试超级用户有编辑权限"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(is_superuser=True)
        db = MagicMock()
        assert check_sales_edit_permission(user, db) is True

    def test_check_sales_edit_permission_sales_director(self):
        """测试销售总监有编辑权限"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(roles=[MockUserRole("SALES_DIRECTOR")])
        db = MagicMock()
        assert check_sales_edit_permission(user, db) is True

    def test_check_sales_edit_permission_sales_manager(self):
        """测试销售经理有编辑权限"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(roles=[MockUserRole("SALES_MANAGER")])
        db = MagicMock()
        assert check_sales_edit_permission(user, db) is True

    def test_check_sales_edit_permission_sales_own_created(self):
        """测试销售可编辑自己创建的数据"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(roles=[MockUserRole("SALES")], user_id=1)
        db = MagicMock()
        assert check_sales_edit_permission(user, db, entity_created_by=1) is True

    def test_check_sales_edit_permission_sales_own_owned(self):
        """测试销售可编辑自己负责的数据"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(roles=[MockUserRole("SALES")], user_id=1)
        db = MagicMock()
        assert check_sales_edit_permission(user, db, entity_owner_id=1) is True

    def test_check_sales_edit_permission_sales_others(self):
        """测试销售不能编辑他人的数据"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(roles=[MockUserRole("SALES")], user_id=1)
        db = MagicMock()
        assert check_sales_edit_permission(user, db, entity_created_by=2, entity_owner_id=2) is False

    def test_check_sales_edit_permission_finance(self):
        """测试财务无编辑权限"""
        from app.core.sales_permissions import check_sales_edit_permission

        user = MockUser(roles=[MockUserRole("FINANCE")])
        db = MagicMock()
        assert check_sales_edit_permission(user, db) is False


class TestCheckSalesDeletePermission:
    """销售删除权限测试"""

    def test_check_sales_delete_permission_superuser(self):
        """测试超级用户有删除权限"""
        from app.core.sales_permissions import check_sales_delete_permission

        user = MockUser(is_superuser=True)
        db = MagicMock()
        assert check_sales_delete_permission(user, db) is True

    def test_check_sales_delete_permission_sales_director(self):
        """测试销售总监有删除权限"""
        from app.core.sales_permissions import check_sales_delete_permission

        user = MockUser(roles=[MockUserRole("SALES_DIRECTOR")])
        db = MagicMock()
        assert check_sales_delete_permission(user, db) is True

    def test_check_sales_delete_permission_creator(self):
        """测试创建人可删除"""
        from app.core.sales_permissions import check_sales_delete_permission

        user = MockUser(roles=[MockUserRole("SALES")], user_id=1)
        db = MagicMock()
        assert check_sales_delete_permission(user, db, entity_created_by=1) is True

    def test_check_sales_delete_permission_non_creator(self):
        """测试非创建人不能删除"""
        from app.core.sales_permissions import check_sales_delete_permission

        user = MockUser(roles=[MockUserRole("SALES")], user_id=1)
        db = MagicMock()
        assert check_sales_delete_permission(user, db, entity_created_by=2) is False

    def test_check_sales_delete_permission_sales_manager(self):
        """测试销售经理无删除权限（非创建人）"""
        from app.core.sales_permissions import check_sales_delete_permission

        user = MockUser(roles=[MockUserRole("SALES_MANAGER")], user_id=1)
        db = MagicMock()
        assert check_sales_delete_permission(user, db, entity_created_by=2) is False


class TestHasSalesAssessmentAccess:
    """技术评估权限测试"""

    def test_has_sales_assessment_access_superuser(self):
        """测试超级用户有技术评估权限"""
        from app.core.sales_permissions import has_sales_assessment_access

        user = MockUser(is_superuser=True)
        assert has_sales_assessment_access(user) is True

    def test_has_sales_assessment_access_sales(self):
        """测试销售有技术评估权限"""
        from app.core.sales_permissions import has_sales_assessment_access

        user = MockUser(roles=[MockUserRole("sales")])
        assert has_sales_assessment_access(user) is True

    def test_has_sales_assessment_access_presales(self):
        """测试售前有技术评估权限"""
        from app.core.sales_permissions import has_sales_assessment_access

        user = MockUser(roles=[MockUserRole("presales_engineer")])
        assert has_sales_assessment_access(user) is True

    def test_has_sales_assessment_access_te(self):
        """测试技术工程师有技术评估权限"""
        from app.core.sales_permissions import has_sales_assessment_access

        user = MockUser(roles=[MockUserRole("te")])
        assert has_sales_assessment_access(user) is True

    def test_has_sales_assessment_access_no_permission(self):
        """测试普通用户无技术评估权限"""
        from app.core.sales_permissions import has_sales_assessment_access

        user = MockUser(roles=[MockUserRole("engineer")])
        assert has_sales_assessment_access(user) is False


class TestHasSalesApprovalAccess:
    """销售审批权限测试"""

    def test_has_sales_approval_access_superuser(self):
        """测试超级用户有审批权限"""
        from app.core.sales_permissions import has_sales_approval_access

        user = MockUser(is_superuser=True)
        db = MagicMock()
        assert has_sales_approval_access(user, db) is True

    def test_has_sales_approval_access_sales_manager(self):
        """测试销售经理有审批权限"""
        from app.core.sales_permissions import has_sales_approval_access

        user = MockUser(roles=[MockUserRole("sales_manager")])
        db = MagicMock()
        assert has_sales_approval_access(user, db) is True

    def test_has_sales_approval_access_finance_manager(self):
        """测试财务经理有审批权限"""
        from app.core.sales_permissions import has_sales_approval_access

        user = MockUser(roles=[MockUserRole("finance_manager")])
        db = MagicMock()
        assert has_sales_approval_access(user, db) is True

    def test_has_sales_approval_access_gm(self):
        """测试总经理有审批权限"""
        from app.core.sales_permissions import has_sales_approval_access

        user = MockUser(roles=[MockUserRole("gm")])
        db = MagicMock()
        assert has_sales_approval_access(user, db) is True

    def test_has_sales_approval_access_no_permission(self):
        """测试销售无审批权限"""
        from app.core.sales_permissions import has_sales_approval_access

        user = MockUser(roles=[MockUserRole("sales")])
        db = MagicMock()
        assert has_sales_approval_access(user, db) is False


class TestCheckSalesApprovalPermission:
    """销售审批权限详细测试"""

    def test_check_sales_approval_permission_superuser(self):
        """测试超级用户可以审批"""
        from app.core.sales_permissions import check_sales_approval_permission

        user = MockUser(is_superuser=True)
        approval = MagicMock()
        db = MagicMock()
        assert check_sales_approval_permission(user, approval, db) is True

    def test_check_sales_approval_permission_no_role(self):
        """测试无审批角色无法审批"""
        from app.core.sales_permissions import check_sales_approval_permission

        user = MockUser(roles=[MockUserRole("sales")])
        approval = MagicMock()
        approval.approval_level = 1
        approval.approval_role = ""
        db = MagicMock()
        assert check_sales_approval_permission(user, approval, db) is False

    def test_check_sales_approval_permission_level1(self):
        """测试一级审批（销售经理）"""
        from app.core.sales_permissions import check_sales_approval_permission

        user = MockUser(roles=[MockUserRole("sales_manager")])
        approval = MagicMock()
        approval.approval_level = 1
        approval.approval_role = ""
        db = MagicMock()
        assert check_sales_approval_permission(user, approval, db) is True

    def test_check_sales_approval_permission_level2(self):
        """测试二级审批（销售总监）"""
        from app.core.sales_permissions import check_sales_approval_permission

        user = MockUser(roles=[MockUserRole("sales_director")])
        approval = MagicMock()
        approval.approval_level = 2
        approval.approval_role = ""
        db = MagicMock()
        assert check_sales_approval_permission(user, approval, db) is True

    def test_check_sales_approval_permission_specific_role(self):
        """测试指定审批角色"""
        from app.core.sales_permissions import check_sales_approval_permission

        user = MockUser(roles=[MockUserRole("finance_manager")])
        approval = MagicMock()
        approval.approval_level = 1
        approval.approval_role = "finance_manager"
        db = MagicMock()
        assert check_sales_approval_permission(user, approval, db) is True


class TestFilterSalesDataByScope:
    """销售数据过滤测试"""

    def test_filter_sales_data_by_scope_all(self):
        """测试ALL范围不过滤"""
        from app.core.sales_permissions import filter_sales_data_by_scope

        user = MockUser(is_superuser=True)
        db = MagicMock()
        query = MagicMock()
        model_class = MagicMock()

        result = filter_sales_data_by_scope(query, user, db, model_class)
        assert result == query  # 不应该修改查询

    def test_filter_sales_data_by_scope_own(self):
        """测试OWN范围只查自己的数据"""
        from app.core.sales_permissions import filter_sales_data_by_scope

        user = MockUser(roles=[MockUserRole("SALES")], user_id=1)
        db = MagicMock()
        query = MagicMock()
        model_class = MagicMock()
        model_class.owner_id = MagicMock()

        filter_sales_data_by_scope(query, user, db, model_class)
        # 应该调用filter
        query.filter.assert_called()

    def test_filter_sales_data_by_scope_finance_only(self):
        """测试FINANCE_ONLY范围返回空结果"""
        from app.core.sales_permissions import filter_sales_data_by_scope

        user = MockUser(roles=[MockUserRole("FINANCE")])
        db = MagicMock()
        query = MagicMock()
        model_class = MagicMock()

        filter_sales_data_by_scope(query, user, db, model_class)
        # 应该调用filter(False)返回空结果
        query.filter.assert_called()

    def test_filter_sales_data_by_scope_none(self):
        """测试NONE范围返回空结果"""
        from app.core.sales_permissions import filter_sales_data_by_scope

        user = MockUser(roles=[])
        db = MagicMock()
        query = MagicMock()
        model_class = MagicMock()

        filter_sales_data_by_scope(query, user, db, model_class)
        # 应该调用filter(False)返回空结果
        query.filter.assert_called()


class TestFilterSalesFinanceDataByScope:
    """财务数据过滤测试"""

    def test_filter_sales_finance_data_by_scope_all(self):
        """测试ALL范围不过滤财务数据"""
        from app.core.sales_permissions import filter_sales_finance_data_by_scope

        user = MockUser(is_superuser=True)
        db = MagicMock()
        query = MagicMock()
        model_class = MagicMock()

        result = filter_sales_finance_data_by_scope(query, user, db, model_class)
        assert result == query

    def test_filter_sales_finance_data_by_scope_finance_only(self):
        """测试FINANCE_ONLY可以查看财务数据"""
        from app.core.sales_permissions import filter_sales_finance_data_by_scope

        user = MockUser(roles=[MockUserRole("FINANCE")])
        db = MagicMock()
        query = MagicMock()
        model_class = MagicMock()

        result = filter_sales_finance_data_by_scope(query, user, db, model_class)
        assert result == query  # 财务可以查看所有发票和收款


class TestRequireDependencies:
    """依赖函数测试"""

    def test_require_sales_create_permission_returns_callable(self):
        """测试require_sales_create_permission返回可调用对象"""
        from app.core.sales_permissions import require_sales_create_permission

        checker = require_sales_create_permission()
        assert callable(checker)

    def test_require_sales_edit_permission_returns_callable(self):
        """测试require_sales_edit_permission返回可调用对象"""
        from app.core.sales_permissions import require_sales_edit_permission

        checker = require_sales_edit_permission()
        assert callable(checker)

    def test_require_sales_delete_permission_returns_callable(self):
        """测试require_sales_delete_permission返回可调用对象"""
        from app.core.sales_permissions import require_sales_delete_permission

        checker = require_sales_delete_permission()
        assert callable(checker)

    def test_require_sales_assessment_access_returns_callable(self):
        """测试require_sales_assessment_access返回可调用对象"""
        from app.core.sales_permissions import require_sales_assessment_access

        checker = require_sales_assessment_access()
        assert callable(checker)

    def test_require_sales_approval_permission_returns_callable(self):
        """测试require_sales_approval_permission返回可调用对象"""
        from app.core.sales_permissions import require_sales_approval_permission

        checker = require_sales_approval_permission()
        assert callable(checker)
