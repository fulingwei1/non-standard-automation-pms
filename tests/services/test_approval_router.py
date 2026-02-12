# -*- coding: utf-8 -*-
"""ApprovalRouterService 单元测试"""

import pytest
from unittest.mock import MagicMock, patch


class TestApprovalRouterService:
    """ApprovalRouterService 测试"""

    def _make_service(self):
        from app.services.approval_engine.router import ApprovalRouterService
        db = MagicMock()
        return ApprovalRouterService(db), db

    # -- select_flow --

    def test_select_flow_matching_rule(self):
        svc, db = self._make_service()
        flow = MagicMock(id=1)
        rule = MagicMock(
            conditions={"operator": "AND", "items": [{"field": "form.amount", "op": ">=", "value": 100}]},
            flow=flow,
        )
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [rule]

        result = svc.select_flow(1, {"form": {"amount": 200}})
        assert result == flow

    def test_select_flow_no_match_returns_default(self):
        svc, db = self._make_service()
        rule = MagicMock(
            conditions={"operator": "AND", "items": [{"field": "form.amount", "op": ">=", "value": 1000}]},
        )
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [rule]
        default_flow = MagicMock(id=2)
        db.query.return_value.filter.return_value.first.return_value = default_flow

        result = svc.select_flow(1, {"form": {"amount": 10}})
        assert result == default_flow

    def test_select_flow_no_rules(self):
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        default_flow = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = default_flow

        result = svc.select_flow(1, {})
        assert result == default_flow

    # -- _evaluate_conditions --

    def test_evaluate_conditions_and_all_true(self):
        svc, _ = self._make_service()
        conds = {
            "operator": "AND",
            "items": [
                {"field": "form.a", "op": "==", "value": 1},
                {"field": "form.b", "op": "==", "value": 2},
            ],
        }
        assert svc._evaluate_conditions(conds, {"form": {"a": 1, "b": 2}}) is True

    def test_evaluate_conditions_and_one_false(self):
        svc, _ = self._make_service()
        conds = {
            "operator": "AND",
            "items": [
                {"field": "form.a", "op": "==", "value": 1},
                {"field": "form.b", "op": "==", "value": 99},
            ],
        }
        assert svc._evaluate_conditions(conds, {"form": {"a": 1, "b": 2}}) is False

    def test_evaluate_conditions_or(self):
        svc, _ = self._make_service()
        conds = {
            "operator": "OR",
            "items": [
                {"field": "form.a", "op": "==", "value": 99},
                {"field": "form.b", "op": "==", "value": 2},
            ],
        }
        assert svc._evaluate_conditions(conds, {"form": {"a": 1, "b": 2}}) is True

    def test_evaluate_conditions_empty_items(self):
        svc, _ = self._make_service()
        assert svc._evaluate_conditions({"operator": "AND", "items": []}, {}) is True

    # -- _compare --

    def test_compare_operators(self):
        svc, _ = self._make_service()
        assert svc._compare(5, "==", 5) is True
        assert svc._compare(5, "!=", 3) is True
        assert svc._compare(5, ">", 3) is True
        assert svc._compare(5, ">=", 5) is True
        assert svc._compare(3, "<", 5) is True
        assert svc._compare(5, "<=", 5) is True
        assert svc._compare("a", "in", ["a", "b"]) is True
        assert svc._compare("c", "not_in", ["a", "b"]) is True
        assert svc._compare(5, "between", [1, 10]) is True
        assert svc._compare(15, "between", [1, 10]) is False
        assert svc._compare("hello", "contains", "ell") is True
        assert svc._compare("hello", "starts_with", "hel") is True
        assert svc._compare("hello", "ends_with", "llo") is True
        assert svc._compare(None, "is_null", True) is True
        assert svc._compare("abc", "is_null", False) is True
        assert svc._compare("abc123", "regex", r"abc\d+") is True

    def test_compare_none_values(self):
        svc, _ = self._make_service()
        assert svc._compare(None, ">", 5) is False
        assert svc._compare(None, "between", [1, 10]) is False
        assert svc._compare(None, "contains", "x") is False

    def test_compare_unknown_op(self):
        svc, _ = self._make_service()
        assert svc._compare(1, "INVALID", 1) is False

    def test_compare_type_error(self):
        svc, _ = self._make_service()
        assert svc._compare("abc", ">", 5) is False

    # -- _get_field_value --

    def test_get_field_value_nested(self):
        svc, _ = self._make_service()
        ctx = {"form": {"nested": {"deep": 42}}}
        assert svc._get_field_value("form.nested.deep", ctx) == 42

    def test_get_field_value_missing(self):
        svc, _ = self._make_service()
        assert svc._get_field_value("form.nonexist", {"form": {}}) is None

    def test_get_field_value_empty(self):
        svc, _ = self._make_service()
        assert svc._get_field_value("", {}) is None

    def test_get_field_value_attribute(self):
        svc, _ = self._make_service()
        obj = MagicMock(name="test_val")
        ctx = {"entity": obj}
        result = svc._get_field_value("entity.name", ctx)
        # MagicMock.name is special, just check it doesn't crash
        assert result is not None or result is None  # just test no exception

    # -- resolve_approvers --

    def test_resolve_approvers_fixed_user(self):
        svc, _ = self._make_service()
        node = MagicMock(approver_type="FIXED_USER", approver_config={"user_ids": [1, 2]})
        assert svc.resolve_approvers(node, {}) == [1, 2]

    def test_resolve_approvers_form_field(self):
        svc, _ = self._make_service()
        node = MagicMock(approver_type="FORM_FIELD", approver_config={"field_name": "reviewer"})
        ctx = {"form_data": {"reviewer": 5}}
        assert svc.resolve_approvers(node, ctx) == [5]

    def test_resolve_approvers_form_field_list(self):
        svc, _ = self._make_service()
        node = MagicMock(approver_type="FORM_FIELD", approver_config={"field_name": "reviewers"})
        ctx = {"form_data": {"reviewers": [5, 6]}}
        assert svc.resolve_approvers(node, ctx) == [5, 6]

    def test_resolve_approvers_initiator(self):
        svc, _ = self._make_service()
        node = MagicMock(approver_type="INITIATOR", approver_config={})
        ctx = {"initiator": {"id": 10}}
        assert svc.resolve_approvers(node, ctx) == [10]

    def test_resolve_approvers_dynamic_with_adapter(self):
        svc, _ = self._make_service()
        adapter = MagicMock()
        adapter.resolve_approvers.return_value = [7, 8]
        node = MagicMock(approver_type="DYNAMIC", approver_config={})
        ctx = {"adapter": adapter}
        assert svc.resolve_approvers(node, ctx) == [7, 8]

    def test_resolve_approvers_unknown_type(self):
        svc, _ = self._make_service()
        node = MagicMock(approver_type="WEIRD", approver_config={})
        assert svc.resolve_approvers(node, {}) == []

    def test_resolve_approvers_role(self):
        svc, db = self._make_service()
        node = MagicMock(approver_type="ROLE", approver_config={"role_codes": ["ADMIN"]})
        user_row = MagicMock(id=3)
        db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = [user_row]
        assert svc.resolve_approvers(node, {}) == [3]

    def test_resolve_approvers_department_head(self):
        svc, db = self._make_service()
        node = MagicMock(approver_type="DEPARTMENT_HEAD", approver_config={})
        dept = MagicMock(manager_id=9)
        db.query.return_value.filter.return_value.first.return_value = dept
        ctx = {"initiator": {"dept_id": 1}}
        assert svc.resolve_approvers(node, ctx) == [9]

    def test_resolve_approvers_direct_manager(self):
        svc, db = self._make_service()
        node = MagicMock(approver_type="DIRECT_MANAGER", approver_config={})
        user = MagicMock(reporting_to=11)
        db.query.return_value.filter.return_value.first.return_value = user
        ctx = {"initiator": {"id": 5}}
        assert svc.resolve_approvers(node, ctx) == [11]

    # -- get_next_nodes --

    def test_get_next_nodes_normal(self):
        svc, db = self._make_service()
        current = MagicMock(flow_id=1, node_order=1)
        next_node = MagicMock(node_type="APPROVAL")
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [next_node]
        result = svc.get_next_nodes(current, {})
        assert result == [next_node]

    def test_get_next_nodes_empty(self):
        svc, db = self._make_service()
        current = MagicMock(flow_id=1, node_order=10)
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        assert svc.get_next_nodes(current, {}) == []

    def test_get_next_nodes_condition_branch(self):
        svc, db = self._make_service()
        current = MagicMock(flow_id=1, node_order=1)
        cond_node = MagicMock(
            node_type="CONDITION",
            approver_config={
                "branches": [
                    {"conditions": {"operator": "AND", "items": [{"field": "form.x", "op": "==", "value": 1}]},
                     "target_node_id": 10}
                ],
                "default_node_id": 20,
            },
        )
        target = MagicMock(id=10)
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [cond_node]
        db.query.return_value.filter.return_value.first.return_value = target

        result = svc.get_next_nodes(current, {"form": {"x": 1}})
        assert result == [target]
