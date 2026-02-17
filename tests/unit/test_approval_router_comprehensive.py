# -*- coding: utf-8 -*-
"""
approval_engine/engine/router.py 单元测试 - 完整版

测试审批路由决策服务的各个方法
"""

import pytest
from unittest.mock import MagicMock, patch
from app.services.approval_engine.router import ApprovalRouterService


@pytest.mark.unit
class TestSelectFlow:
    """测试 select_flow 方法"""

    def test_select_flow_with_matching_rule(self):
        """测试匹配到路由规则"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        mock_flow = MagicMock()
        mock_flow.id = 100

        mock_rule = MagicMock()
        mock_rule.flow_id = 200
        mock_rule.flow = mock_flow
        mock_rule.conditions = {"operator": "AND", "items": []}

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_rule]

        mock_db.query.return_value = mock_query

        # Mock _evaluate_conditions to return True
        with patch.object(service, "_evaluate_conditions", return_value=True):
            result = service.select_flow(template_id=1, context={})

            assert result == mock_rule.flow

    def test_select_flow_with_default_flow(self):
        """测试使用默认流程"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        mock_flow = MagicMock()
        mock_flow.id = 100

        # Mock rules query to return no matching rules
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        # Mock _get_default_flow to return default flow
        mock_default_flow = MagicMock()
        with patch.object(service, "_get_default_flow", return_value=mock_default_flow):
            result = service.select_flow(template_id=1, context={})

            assert result == mock_default_flow

    def test_select_flow_no_matching_flow(self):
        """测试没有匹配的流程"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        # Mock rules query to return no rules
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        # Mock _get_default_flow to return None
        with patch.object(service, "_get_default_flow", return_value=None):
            result = service.select_flow(template_id=1, context={})

            assert result is None


@pytest.mark.unit
class TestCompareOperations:
    """测试 _compare 比较操作"""

    def test_compare_equal(self):
        """测试相等比较"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        assert service._compare(100, "==", 100) is True
        assert service._compare(100, "==", 200) is False

    def test_compare_not_equal(self):
        """测试不等比较"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        assert service._compare(100, "!=", 200) is True
        assert service._compare(100, "!=", 100) is False

    def test_compare_greater_than(self):
        """测试大于比较"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        assert service._compare(100, ">", 50) is True
        assert service._compare(100, ">", 100) is False

    def test_compare_less_than(self):
        """测试小于比较"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        assert service._compare(50, "<", 100) is True
        assert service._compare(100, "<", 50) is False

    def test_compare_in(self):
        """测试包含比较"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        assert service._compare(100, "in", [1, 2, 100]) is True
        assert service._compare(100, "in", [1, 2]) is False

    def test_compare_not_in(self):
        """测试不包含比较"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        assert service._compare(100, "not_in", [1, 2]) is True
        assert service._compare(100, "not_in", [1, 2, 100]) is False

    def test_compare_between(self):
        """测试区间比较"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        assert service._compare(50, "between", [10, 100]) is True
        assert service._compare(5, "between", [10, 100]) is False
        assert service._compare(150, "between", [10, 100]) is False

    def test_compare_contains(self):
        """测试字符串包含"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        assert service._compare("Hello World", "contains", "World") is True
        assert service._compare("Hello World", "contains", "Test") is False

    def test_compare_starts_with(self):
        """测试前缀"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        assert service._compare("Project-001", "starts_with", "Project") is True
        assert service._compare("Project-001", "starts_with", "Test") is False

    def test_compare_ends_with(self):
        """测试后缀"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        assert service._compare("file.txt", "ends_with", ".txt") is True
        assert service._compare("file.txt", "ends_with", ".pdf") is False

    def test_compare_is_null(self):
        """测试空值判断"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        assert service._compare(None, "is_null", True) is True
        assert service._compare(100, "is_null", False) is True

    def test_compare_not_null(self):
        """测试非空值判断"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        assert service._compare(100, "is_null", False) is True
        assert service._compare(None, "is_null", False) is False


@pytest.mark.unit
class TestEvaluateConditions:
    """测试 _evaluate_conditions 方法"""

    def test_evaluate_and_all_true(self):
        """测试AND条件：全部满足"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        conditions = {
        "operator": "AND",
        "items": [
        {"field": "form.amount", "op": ">", "value": 1000},
        {"field": "entity.status", "op": "==", "value": "APPROVED"},
        ],
        }

        context = {
        "form": {"amount": 5000},
        "entity": {"status": "APPROVED"},
        }

        result = service._evaluate_conditions(conditions, context)
        assert result is True

    def test_evaluate_and_all_false(self):
        """测试AND条件：不满足"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        conditions = {
        "operator": "AND",
        "items": [
        {"field": "form.amount", "op": ">", "value": 1000},
        ],
        }

        context = {
        "form": {"amount": 500},
        }

        result = service._evaluate_conditions(conditions, context)
        assert result is False

    def test_evaluate_or_one_true(self):
        """测试OR条件：有一个满足"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        conditions = {
        "operator": "OR",
        "items": [
        {"field": "form.amount", "op": ">", "value": 1000},
        {"field": "form.amount", "op": "<", "value": 1000},
        ],
        }

        context = {
        "form": {"amount": 500},
        }

        result = service._evaluate_conditions(conditions, context)
        assert result is True

    def test_evaluate_or_all_false(self):
        """测试OR条件：全部不满足"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        conditions = {
        "operator": "OR",
        "items": [
        {"field": "form.amount", "op": ">", "value": 10000},
        {"field": "form.amount", "op": "<", "value": 0},
        ],
        }

        context = {
        "form": {"amount": 500},
        }

        result = service._evaluate_conditions(conditions, context)
        assert result is False

    def test_evaluate_no_items(self):
        """测试空条件列表"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        conditions = {
        "operator": "AND",
        "items": [],
        }

        context = {
        "form": {"amount": 5000},
        }

        result = service._evaluate_conditions(conditions, context)
        assert result is True


@pytest.mark.unit
class TestResolveApprovers:
    """测试 resolve_approvers 方法"""

    def test_resolve_approvers_fixed_user(self):
        """测试指定用户类型的审批人"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        node = MagicMock()
        node.approver_type = "FIXED_USER"
        node.approver_config = {"user_ids": [1, 2, 3]}

        context = {}

        result = service.resolve_approvers(node, context)
        assert result == [1, 2, 3]

    def test_resolve_approvers_empty_config(self):
        """测试空配置返回空列表"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        node = MagicMock()
        node.approver_type = "FIXED_USER"
        node.approver_config = {}

        context = {}

        result = service.resolve_approvers(node, context)
        assert result == []

    def test_resolve_approvers_form_field(self):
        """测试表单字段类型的审批人"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        node = MagicMock()
        node.approver_type = "FORM_FIELD"
        node.approver_config = {"field_name": "approver_id"}

        context = {"form_data": {"approver_id": 100}}

        result = service.resolve_approvers(node, context)
        assert result == [100]

    def test_resolve_approvers_form_field_not_found(self):
        """测试表单字段未找到"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        node = MagicMock()
        node.approver_type = "FORM_FIELD"
        node.approver_config = {"field_name": "approver_id"}

        context = {"form_data": {}}

        result = service.resolve_approvers(node, context)
        assert result == []

    def test_resolve_approvers_initiator(self):
        """测试发起人类型"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        node = MagicMock()
        node.approver_type = "INITIATOR"
        node.approver_config = {}

        context = {"initiator": {"id": 1}}

        result = service.resolve_approvers(node, context)
        assert result == [1]

    def test_resolve_approvers_initiator_with_object(self):
        """测试发起人类型（对象形式）"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        class MockInitiator:
            def __init__(self):
                self.id = 1

            def get(self, key, default=None):
                if key == "id":
                    return self.id
                return default

        node = MagicMock()
        node.approver_type = "INITIATOR"
        node.approver_config = {}

        context = {"initiator": MockInitiator()}

        result = service.resolve_approvers(node, context)
        assert result == [1]

    def test_resolve_approvers_unknown_type(self):
        """测试未知类型返回空列表"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        node = MagicMock()
        node.approver_type = "UNKNOWN_TYPE"
        node.approver_config = {}

        context = {}

        result = service.resolve_approvers(node, context)
        assert result == []

    def test_resolve_approvers_dynamic_without_adapter(self):
        """测试动态类型无适配器"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        node = MagicMock()
        node.approver_type = "DYNAMIC"
        node.approver_config = {}

        context = {}

        result = service.resolve_approvers(node, context)
        assert result == []

    def test_resolve_approvers_dynamic_with_adapter(self):
        """测试动态类型有适配器"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        node = MagicMock()
        node.approver_type = "DYNAMIC"
        node.approver_config = {}

        mock_adapter = MagicMock()
        mock_adapter.resolve_approvers.return_value = [1, 2, 3]

        context = {"adapter": mock_adapter}

        result = service.resolve_approvers(node, context)
        assert result == [1, 2, 3]
        mock_adapter.resolve_approvers.assert_called_once_with(node, context)

    def test_get_field_value_not_found(self):
        """测试路径不存在"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        context = {"form": {"amount": 1000}}
        result = service._get_field_value("form.nonexistent", context)
        assert result is None


@pytest.mark.unit
class TestRouterServiceIntegration:
    """集成测试"""

    def test_all_methods_callable(self):
        """测试所有公共方法可调用"""
        mock_db = MagicMock()
        service = ApprovalRouterService(db=mock_db)

        assert hasattr(service, "select_flow")
        assert hasattr(service, "resolve_approvers")
        assert hasattr(service, "get_next_nodes")
        assert hasattr(service, "_evaluate_conditions")
        assert hasattr(service, "_compare")


# =============================================================================
# 补充测试 A组覆盖率提升 (2026-02-17)
# =============================================================================

class TestApprovalRouterServiceMock:
    """ApprovalRouterService 快速单元测试（MagicMock）"""

    def _make_service(self):
        db = MagicMock()
        from app.services.approval_engine.router import ApprovalRouterService
        return ApprovalRouterService(db), db

    # ---- _compare 操作符 ----

    def test_compare_eq(self):
        svc, _ = self._make_service()
        assert svc._compare(5, "==", 5) is True
        assert svc._compare(5, "==", 6) is False

    def test_compare_neq(self):
        svc, _ = self._make_service()
        assert svc._compare(5, "!=", 6) is True
        assert svc._compare(5, "!=", 5) is False

    def test_compare_gt(self):
        svc, _ = self._make_service()
        assert svc._compare(10, ">", 5) is True
        assert svc._compare(5, ">", 10) is False
        assert svc._compare(None, ">", 5) is False

    def test_compare_gte(self):
        svc, _ = self._make_service()
        assert svc._compare(5, ">=", 5) is True
        assert svc._compare(4, ">=", 5) is False

    def test_compare_lt_lte(self):
        svc, _ = self._make_service()
        assert svc._compare(3, "<", 5) is True
        assert svc._compare(5, "<=", 5) is True

    def test_compare_in(self):
        svc, _ = self._make_service()
        assert svc._compare("A", "in", ["A", "B"]) is True
        assert svc._compare("C", "in", ["A", "B"]) is False
        assert svc._compare("A", "in", None) is False

    def test_compare_not_in(self):
        svc, _ = self._make_service()
        assert svc._compare("C", "not_in", ["A", "B"]) is True
        assert svc._compare("A", "not_in", None) is True

    def test_compare_between(self):
        svc, _ = self._make_service()
        assert svc._compare(5, "between", [1, 10]) is True
        assert svc._compare(15, "between", [1, 10]) is False
        assert svc._compare(None, "between", [1, 10]) is False

    def test_compare_contains(self):
        svc, _ = self._make_service()
        assert svc._compare("hello world", "contains", "world") is True
        assert svc._compare(None, "contains", "x") is False

    def test_compare_starts_with(self):
        svc, _ = self._make_service()
        assert svc._compare("foobar", "starts_with", "foo") is True
        assert svc._compare(None, "starts_with", "foo") is False

    def test_compare_ends_with(self):
        svc, _ = self._make_service()
        assert svc._compare("foobar", "ends_with", "bar") is True

    def test_compare_is_null(self):
        svc, _ = self._make_service()
        assert svc._compare(None, "is_null", True) is True
        assert svc._compare("x", "is_null", True) is False

    def test_compare_regex(self):
        svc, _ = self._make_service()
        assert svc._compare("abc123", "regex", r"\w+") is True

    def test_compare_unknown_op_returns_false(self):
        svc, _ = self._make_service()
        assert svc._compare(1, "weird_op", 1) is False

    def test_compare_type_error_returns_false(self):
        svc, _ = self._make_service()
        # Comparing string to int with > should return False (not raise)
        result = svc._compare("text", ">", 5)
        assert result is False

    # ---- _get_field_value ----

    def test_get_field_value_empty_returns_none(self):
        svc, _ = self._make_service()
        assert svc._get_field_value("", {}) is None

    def test_get_field_value_nested(self):
        svc, _ = self._make_service()
        ctx = {"form": {"leave_days": 5}}
        assert svc._get_field_value("form.leave_days", ctx) == 5

    def test_get_field_value_missing_key(self):
        svc, _ = self._make_service()
        assert svc._get_field_value("entity.amount", {}) is None

    # ---- _evaluate_conditions ----

    def test_evaluate_and_conditions_all_true(self):
        svc, _ = self._make_service()
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.amount", "op": ">", "value": 100},
                {"field": "form.days", "op": "<=", "value": 30},
            ]
        }
        ctx = {"form": {"amount": 500, "days": 15}}
        assert svc._evaluate_conditions(conditions, ctx) is True

    def test_evaluate_and_conditions_one_false(self):
        svc, _ = self._make_service()
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.amount", "op": ">", "value": 100},
                {"field": "form.days", "op": "<=", "value": 10},
            ]
        }
        ctx = {"form": {"amount": 500, "days": 20}}
        assert svc._evaluate_conditions(conditions, ctx) is False

    def test_evaluate_or_conditions_one_true(self):
        svc, _ = self._make_service()
        conditions = {
            "operator": "OR",
            "items": [
                {"field": "form.amount", "op": ">", "value": 9999},
                {"field": "form.type", "op": "==", "value": "STANDARD"},
            ]
        }
        ctx = {"form": {"amount": 100, "type": "STANDARD"}}
        assert svc._evaluate_conditions(conditions, ctx) is True

    def test_evaluate_empty_items_returns_true(self):
        svc, _ = self._make_service()
        assert svc._evaluate_conditions({"operator": "AND", "items": []}, {}) is True

    # ---- select_flow ----

    def test_select_flow_returns_default_when_no_rules(self):
        svc, db = self._make_service()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        default_flow = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = default_flow

        result = svc.select_flow(template_id=1, context={})
        assert result is default_flow

    def test_select_flow_matches_rule(self):
        svc, db = self._make_service()

        rule = MagicMock()
        rule.conditions = {"operator": "AND", "items": [{"field": "form.amount", "op": ">", "value": 1000}]}
        matched_flow = MagicMock()
        rule.flow = matched_flow

        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [rule]

        result = svc.select_flow(template_id=1, context={"form": {"amount": 5000}})
        assert result is matched_flow

    # ---- resolve_approvers ----

    def test_resolve_fixed_user(self):
        svc, _ = self._make_service()
        node = MagicMock()
        node.approver_type = "FIXED_USER"
        node.approver_config = {"user_ids": [1, 2, 3]}
        result = svc.resolve_approvers(node, {})
        assert result == [1, 2, 3]

    def test_resolve_initiator(self):
        svc, _ = self._make_service()
        node = MagicMock()
        node.approver_type = "INITIATOR"
        node.approver_config = {}
        ctx = {"initiator": {"id": 42}}
        result = svc.resolve_approvers(node, ctx)
        assert result == [42]

    def test_resolve_form_field(self):
        svc, _ = self._make_service()
        node = MagicMock()
        node.approver_type = "FORM_FIELD"
        node.approver_config = {"field_name": "approver_id"}
        ctx = {"form_data": {"approver_id": 7}}
        result = svc.resolve_approvers(node, ctx)
        assert result == [7]

    def test_resolve_unknown_type_returns_empty(self):
        svc, _ = self._make_service()
        node = MagicMock()
        node.approver_type = "UNKNOWN_TYPE"
        node.approver_config = {}
        result = svc.resolve_approvers(node, {})
        assert result == []

    # ---- get_next_nodes ----

    def test_get_next_nodes_returns_empty_when_no_next(self):
        svc, db = self._make_service()
        node = MagicMock()
        node.flow_id = 1
        node.node_order = 5

        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = svc.get_next_nodes(node, {})
        assert result == []

    def test_get_next_nodes_returns_next_sequential_node(self):
        svc, db = self._make_service()
        current_node = MagicMock()
        current_node.flow_id = 1
        current_node.node_order = 1

        next_node = MagicMock()
        next_node.node_type = "APPROVAL"

        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [next_node]
        result = svc.get_next_nodes(current_node, {})
        assert result == [next_node]


from unittest.mock import MagicMock, patch
import pytest
