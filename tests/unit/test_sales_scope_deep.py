# -*- coding: utf-8 -*-
"""sales_scope 深度测试"""

from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.models.permission import ScopeType
from app.services.sales.sales_scope import (
    RT_SALES,
    SalesScopeContext,
    _check_finance_role,
    apply_finance_scope,
    apply_owner_scope,
    can_access_finance_entity,
    can_access_sales_entity,
    resolve_sales_scope,
)


class DummyColumn:
    def __eq__(self, other):
        return ("eq", other)

    def in_(self, values):
        return ("in", tuple(values))


class DummyDeptColumn:
    def in_(self, values):
        return ("dept_in", tuple(values))


class DummyUserModel:
    id = "user.id"
    department_id = DummyDeptColumn()


class FakeQuery:
    def __init__(self):
        self.ops = []

    def filter(self, *args):
        self.ops.append(("filter", args))
        return self

    def join(self, *args):
        self.ops.append(("join", args))
        return self


def _user(user_id=1, is_superuser=False, roles=None):
    return SimpleNamespace(id=user_id, is_superuser=is_superuser, roles=roles or [])


def _user_role(role_code="sales", is_active=True, data_scope=None):
    return SimpleNamespace(role=SimpleNamespace(role_code=role_code, is_active=is_active, data_scope=data_scope))


class TestSalesScopeDeep:
    def test_resolve_sales_scope_superuser_and_finance_role(self):
        user = _user(7, is_superuser=True, roles=[_user_role("finance")])

        ctx = resolve_sales_scope(Mock(), user, "quote")

        assert ctx.scope_type == ScopeType.ALL.value
        assert ctx.user_id == 7
        assert ctx.resource_type == "quote"
        assert ctx.accessible_dept_ids is None
        assert ctx.is_finance_role is True

    def test_resolve_sales_scope_exact_fallback_role_and_department_team(self):
        db = Mock()
        user = _user(3, roles=[_user_role("sales", data_scope=ScopeType.DEPARTMENT.value)])

        with patch("app.services.sales.sales_scope.PermissionService.get_user_data_scopes", return_value={"quote": ScopeType.TEAM.value}), \
             patch("app.services.sales.sales_scope.UserScopeService.get_subordinate_ids", return_value={8, 9}):
            team_ctx = resolve_sales_scope(db, user, "quote")

        assert team_ctx.scope_type == ScopeType.TEAM.value
        assert team_ctx.resource_type == "quote"
        assert team_ctx.accessible_user_ids == {3, 8, 9}
        assert team_ctx.accessible_dept_ids == []

        with patch("app.services.sales.sales_scope.PermissionService.get_user_data_scopes", return_value={RT_SALES: ScopeType.DEPARTMENT.value}), \
             patch("app.services.data_scope.data_scope_service_enhanced.DataScopeServiceEnhanced.get_accessible_org_units", return_value=[11, 12]):
            dept_ctx = resolve_sales_scope(db, user, "contract")

        assert dept_ctx.scope_type == ScopeType.DEPARTMENT.value
        assert dept_ctx.resource_type == RT_SALES
        assert dept_ctx.accessible_dept_ids == [11, 12]

        with patch("app.services.sales.sales_scope.PermissionService.get_user_data_scopes", return_value={}), \
             patch("app.services.data_scope.data_scope_service_enhanced.DataScopeServiceEnhanced.get_accessible_org_units", return_value=[21]):
            role_ctx = resolve_sales_scope(db, user, "customer")

        assert role_ctx.scope_type == ScopeType.DEPARTMENT.value
        assert role_ctx.resource_type == RT_SALES
        assert role_ctx.accessible_dept_ids == [21]

    def test_resolve_sales_scope_department_without_org_units_and_default_own(self):
        db = Mock()
        user = _user(5, roles=[_user_role("sales", data_scope=ScopeType.DEPARTMENT.value)])

        with patch("app.services.sales.sales_scope.PermissionService.get_user_data_scopes", return_value={RT_SALES: ScopeType.DEPARTMENT.value}), \
             patch("app.services.data_scope.data_scope_service_enhanced.DataScopeServiceEnhanced.get_accessible_org_units", return_value=[]):
            ctx = resolve_sales_scope(db, user, "opportunity")

        assert ctx.scope_type == ScopeType.OWN.value
        assert ctx.accessible_dept_ids == []
        assert ctx.resource_type == RT_SALES

        with patch("app.services.sales.sales_scope.PermissionService.get_user_data_scopes", return_value={}):
            own_ctx = resolve_sales_scope(db, _user(6), "customer")

        assert own_ctx.scope_type == ScopeType.OWN.value
        assert own_ctx.accessible_dept_ids == []
        assert own_ctx.accessible_user_ids == set()

    def test_apply_owner_scope_and_finance_scope(self):
        owner_col = DummyColumn()

        q1 = FakeQuery()
        assert apply_owner_scope(q1, SalesScopeContext(scope_type=ScopeType.ALL.value, user_id=1), owner_col) is q1
        assert q1.ops == []

        q2 = FakeQuery()
        apply_owner_scope(q2, SalesScopeContext(scope_type=ScopeType.OWN.value, user_id=2), owner_col)
        assert q2.ops == [("filter", (("eq", 2),))]

        q3 = FakeQuery()
        apply_owner_scope(q3, SalesScopeContext(scope_type=ScopeType.TEAM.value, user_id=3, accessible_user_ids={4, 5}), owner_col)
        assert q3.ops == [("filter", (("in", (4, 5)),))] or q3.ops == [("filter", (("in", (5, 4)),))]

        q4 = FakeQuery()
        apply_owner_scope(q4, SalesScopeContext(scope_type=ScopeType.TEAM.value, user_id=3, accessible_user_ids=set()), owner_col)
        assert q4.ops == [("filter", (("eq", 3),))]

        q5 = FakeQuery()
        with patch("app.services.sales.sales_scope.User", DummyUserModel):
            apply_owner_scope(q5, SalesScopeContext(scope_type=ScopeType.DEPARTMENT.value, user_id=3, accessible_dept_ids=[10]), owner_col)
        assert q5.ops[0][0] == "join"
        assert q5.ops[1] == ("filter", (("dept_in", (10,)),))

        q6 = FakeQuery()
        apply_owner_scope(q6, SalesScopeContext(scope_type=ScopeType.DEPARTMENT.value, user_id=3, accessible_dept_ids=[]), owner_col)
        assert q6.ops == [("filter", (("eq", 3),))]

        q7 = FakeQuery()
        apply_finance_scope(q7, SalesScopeContext(scope_type=ScopeType.ALL.value, user_id=1), None)
        assert q7.ops == []

        q8 = FakeQuery()
        apply_finance_scope(q8, SalesScopeContext(scope_type=ScopeType.OWN.value, user_id=1, is_finance_role=True), None)
        assert q8.ops == []

        q9 = FakeQuery()
        apply_finance_scope(q9, SalesScopeContext(scope_type=ScopeType.OWN.value, user_id=6), owner_col)
        assert q9.ops == [("filter", (("eq", 6),))]

        q10 = FakeQuery()
        apply_finance_scope(q10, SalesScopeContext(scope_type=ScopeType.OWN.value, user_id=6), None)
        assert q10.ops == [("filter", (False,))]

    def test_can_access_helpers_and_finance_role_check(self):
        all_ctx = SalesScopeContext(scope_type=ScopeType.ALL.value, user_id=1)
        own_ctx = SalesScopeContext(scope_type=ScopeType.OWN.value, user_id=2)
        team_ctx = SalesScopeContext(scope_type=ScopeType.TEAM.value, user_id=3, accessible_user_ids={3, 4})
        dept_ctx = SalesScopeContext(scope_type=ScopeType.DEPARTMENT.value, user_id=5, accessible_dept_ids=[7, 8])
        finance_ctx = SalesScopeContext(scope_type=ScopeType.OWN.value, user_id=9, is_finance_role=True)

        assert can_access_sales_entity(all_ctx, owner_id=None) is True
        assert can_access_sales_entity(own_ctx, owner_id=None) is False
        assert can_access_sales_entity(own_ctx, owner_id=2) is True
        assert can_access_sales_entity(team_ctx, owner_id=4) is True
        assert can_access_sales_entity(team_ctx, owner_id=8) is False
        assert can_access_sales_entity(dept_ctx, owner_id=99, owner_dept_id=8) is True
        assert can_access_sales_entity(dept_ctx, owner_id=5, owner_dept_id=None) is True
        assert can_access_sales_entity(dept_ctx, owner_id=99, owner_dept_id=None) is False
        assert can_access_finance_entity(finance_ctx) is True
        assert can_access_finance_entity(own_ctx, owner_id=2) is True
        assert can_access_finance_entity(own_ctx, owner_id=None) is False

        assert _check_finance_role(_user(1, roles=[_user_role("财务经理")])) is True
        assert _check_finance_role(_user(1, roles=[_user_role("sales")])) is False
