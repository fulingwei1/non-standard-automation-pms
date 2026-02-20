# -*- coding: utf-8 -*-
"""
审批路由服务增强测试
补充覆盖核心业务逻辑和异常场景,提升覆盖率到60%+
"""
import pytest
from unittest.mock import MagicMock, patch
import re

from app.services.approval_engine.router import ApprovalRouterService


@pytest.fixture
def db_mock():
    """数据库mock"""
    return MagicMock()


@pytest.fixture
def router(db_mock):
    """路由服务实例"""
    return ApprovalRouterService(db_mock)


@pytest.fixture
def sample_context():
    """示例上下文"""
    return {
        "form_data": {
            "leave_days": 5,
            "reason": "休假",
            "amount": 50000.0
        },
        "entity": {
            "gross_margin": 0.25,
            "total_amount": 100000.0,
            "priority": "HIGH"
        },
        "initiator": {
            "id": 100,
            "dept_id": 5,
            "username": "zhangsan"
        }
    }


class TestSelectFlow:
    """测试选择审批流程"""
    
    def test_select_flow_with_matching_rule(self, router, db_mock, sample_context):
        """测试匹配规则选择流程"""
        # Mock规则
        rule1 = MagicMock()
        rule1.conditions = {
            "operator": "AND",
            "items": [
                {"field": "form_data.leave_days", "op": "<=", "value": 7}
            ]
        }
        rule1.flow = MagicMock(name="短期请假流程")
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = [rule1]
        db_mock.query.return_value = mock_query
        
        result = router.select_flow(template_id=1, context=sample_context)
        
        assert result == rule1.flow
    
    def test_select_flow_no_matching_use_default(self, router, db_mock, sample_context):
        """测试无匹配规则使用默认流程"""
        # Mock无匹配规则
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []
        
        # Mock默认流程
        default_flow = MagicMock(name="默认流程")
        mock_query.first.return_value = default_flow
        
        db_mock.query.return_value = mock_query
        
        result = router.select_flow(template_id=1, context=sample_context)
        
        assert result == default_flow
    
    def test_select_flow_multiple_rules_first_match(self, router, db_mock, sample_context):
        """测试多个规则时选择第一个匹配的"""
        rule1 = MagicMock()
        rule1.conditions = {
            "operator": "AND",
            "items": [
                {"field": "form_data.leave_days", "op": ">", "value": 10}
            ]
        }
        rule1.flow = MagicMock(name="长期请假流程")
        
        rule2 = MagicMock()
        rule2.conditions = {
            "operator": "AND",
            "items": [
                {"field": "form_data.leave_days", "op": "<=", "value": 7}
            ]
        }
        rule2.flow = MagicMock(name="短期请假流程")
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = [rule1, rule2]
        mock_query.first.return_value = None
        db_mock.query.return_value = mock_query
        
        with patch.object(router, '_evaluate_conditions') as mock_eval:
            mock_eval.side_effect = [False, True]  # 第一个不匹配,第二个匹配
            
            result = router.select_flow(template_id=1, context=sample_context)
            
            assert result == rule2.flow


class TestEvaluateConditions:
    """测试评估条件表达式"""
    
    def test_evaluate_conditions_and_all_true(self, router, sample_context):
        """测试AND操作符全部为真"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form_data.leave_days", "op": "<=", "value": 7},
                {"field": "entity.priority", "op": "==", "value": "HIGH"}
            ]
        }
        
        result = router._evaluate_conditions(conditions, sample_context)
        
        assert result is True
    
    def test_evaluate_conditions_and_has_false(self, router, sample_context):
        """测试AND操作符有假值"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form_data.leave_days", "op": "<=", "value": 3},
                {"field": "entity.priority", "op": "==", "value": "HIGH"}
            ]
        }
        
        result = router._evaluate_conditions(conditions, sample_context)
        
        assert result is False
    
    def test_evaluate_conditions_or_has_true(self, router, sample_context):
        """测试OR操作符有真值"""
        conditions = {
            "operator": "OR",
            "items": [
                {"field": "form_data.leave_days", "op": ">", "value": 10},
                {"field": "entity.priority", "op": "==", "value": "HIGH"}
            ]
        }
        
        result = router._evaluate_conditions(conditions, sample_context)
        
        assert result is True
    
    def test_evaluate_conditions_empty_items(self, router, sample_context):
        """测试空条件列表返回True"""
        conditions = {
            "operator": "AND",
            "items": []
        }
        
        result = router._evaluate_conditions(conditions, sample_context)
        
        assert result is True


class TestGetFieldValue:
    """测试获取字段值"""
    
    def test_get_field_value_form_data(self, router, sample_context):
        """测试获取表单字段"""
        value = router._get_field_value("form_data.leave_days", sample_context)
        assert value == 5
    
    def test_get_field_value_entity(self, router, sample_context):
        """测试获取实体字段"""
        value = router._get_field_value("entity.gross_margin", sample_context)
        assert value == 0.25
    
    def test_get_field_value_initiator(self, router, sample_context):
        """测试获取发起人字段"""
        value = router._get_field_value("initiator.id", sample_context)
        assert value == 100
    
    def test_get_field_value_nested_path(self, router, sample_context):
        """测试嵌套路径"""
        value = router._get_field_value("form_data.reason", sample_context)
        assert value == "休假"
    
    def test_get_field_value_not_found(self, router, sample_context):
        """测试字段不存在"""
        value = router._get_field_value("form_data.nonexistent", sample_context)
        assert value is None
    
    def test_get_field_value_empty_path(self, router, sample_context):
        """测试空路径"""
        value = router._get_field_value("", sample_context)
        assert value is None


class TestCompare:
    """测试比较操作"""
    
    def test_compare_equal(self, router):
        """测试相等比较"""
        assert router._compare(5, "==", 5) is True
        assert router._compare(5, "==", 6) is False
    
    def test_compare_not_equal(self, router):
        """测试不等比较"""
        assert router._compare(5, "!=", 6) is True
        assert router._compare(5, "!=", 5) is False
    
    def test_compare_greater_than(self, router):
        """测试大于比较"""
        assert router._compare(10, ">", 5) is True
        assert router._compare(5, ">", 10) is False
        assert router._compare(None, ">", 5) is False
    
    def test_compare_greater_equal(self, router):
        """测试大于等于比较"""
        assert router._compare(10, ">=", 10) is True
        assert router._compare(10, ">=", 5) is True
        assert router._compare(5, ">=", 10) is False
    
    def test_compare_less_than(self, router):
        """测试小于比较"""
        assert router._compare(5, "<", 10) is True
        assert router._compare(10, "<", 5) is False
    
    def test_compare_less_equal(self, router):
        """测试小于等于比较"""
        assert router._compare(5, "<=", 5) is True
        assert router._compare(5, "<=", 10) is True
        assert router._compare(10, "<=", 5) is False
    
    def test_compare_in(self, router):
        """测试in操作符"""
        assert router._compare("A", "in", ["A", "B", "C"]) is True
        assert router._compare("D", "in", ["A", "B", "C"]) is False
        assert router._compare("A", "in", None) is False
    
    def test_compare_not_in(self, router):
        """测试not_in操作符"""
        assert router._compare("D", "not_in", ["A", "B", "C"]) is True
        assert router._compare("A", "not_in", ["A", "B", "C"]) is False
    
    def test_compare_between(self, router):
        """测试between操作符"""
        assert router._compare(5, "between", [1, 10]) is True
        assert router._compare(15, "between", [1, 10]) is False
        assert router._compare(None, "between", [1, 10]) is False
    
    def test_compare_contains(self, router):
        """测试contains操作符"""
        assert router._compare("hello world", "contains", "world") is True
        assert router._compare("hello world", "contains", "foo") is False
        assert router._compare(None, "contains", "foo") is False
    
    def test_compare_starts_with(self, router):
        """测试starts_with操作符"""
        assert router._compare("hello world", "starts_with", "hello") is True
        assert router._compare("hello world", "starts_with", "world") is False
    
    def test_compare_ends_with(self, router):
        """测试ends_with操作符"""
        assert router._compare("hello world", "ends_with", "world") is True
        assert router._compare("hello world", "ends_with", "hello") is False
    
    def test_compare_is_null(self, router):
        """测试is_null操作符"""
        assert router._compare(None, "is_null", True) is True
        assert router._compare("value", "is_null", True) is False
        assert router._compare(None, "is_null", False) is False
    
    def test_compare_regex(self, router):
        """测试regex操作符"""
        assert router._compare("test123", "regex", r"test\d+") is True
        assert router._compare("test", "regex", r"test\d+") is False
    
    def test_compare_invalid_operator(self, router):
        """测试无效操作符"""
        assert router._compare(5, "invalid_op", 5) is False
    
    def test_compare_type_error(self, router):
        """测试类型错误"""
        # 比较不同类型时应该返回False而不是抛出异常
        assert router._compare("string", ">", 5) is False


class TestResolveApprovers:
    """测试解析审批人"""
    
    def test_resolve_approvers_fixed_user(self, router, db_mock, sample_context):
        """测试固定用户"""
        node = MagicMock()
        node.approver_type = "FIXED_USER"
        node.approver_config = {"user_ids": [100, 200, 300]}
        
        result = router.resolve_approvers(node, sample_context)
        
        assert result == [100, 200, 300]
    
    def test_resolve_approvers_role(self, router, db_mock, sample_context):
        """测试角色审批人"""
        node = MagicMock()
        node.approver_type = "ROLE"
        node.approver_config = {"role_codes": ["MANAGER", "DIRECTOR"]}
        
        # Mock用户查询
        mock_users = [MagicMock(id=100), MagicMock(id=200)]
        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value.all.return_value = mock_users
        db_mock.query.return_value = mock_query
        
        result = router.resolve_approvers(node, sample_context)
        
        assert result == [100, 200]
    
    def test_resolve_approvers_department_head(self, router, db_mock, sample_context):
        """测试部门主管"""
        node = MagicMock()
        node.approver_type = "DEPARTMENT_HEAD"
        node.approver_config = {}
        
        # Mock部门
        dept = MagicMock()
        dept.manager_id = 150
        
        db_mock.query.return_value.filter.return_value.first.return_value = dept
        
        result = router.resolve_approvers(node, sample_context)
        
        assert result == [150]
    
    def test_resolve_approvers_direct_manager(self, router, db_mock, sample_context):
        """测试直属上级"""
        node = MagicMock()
        node.approver_type = "DIRECT_MANAGER"
        node.approver_config = {}
        
        # Mock用户
        user = MagicMock()
        user.reporting_to = 120
        
        db_mock.query.return_value.filter.return_value.first.return_value = user
        
        result = router.resolve_approvers(node, sample_context)
        
        assert result == [120]
    
    def test_resolve_approvers_form_field(self, router, db_mock, sample_context):
        """测试表单字段"""
        node = MagicMock()
        node.approver_type = "FORM_FIELD"
        node.approver_config = {"field_name": "approver_id"}
        
        sample_context["form_data"]["approver_id"] = 180
        
        result = router.resolve_approvers(node, sample_context)
        
        assert result == [180]
    
    def test_resolve_approvers_form_field_list(self, router, db_mock, sample_context):
        """测试表单字段为列表"""
        node = MagicMock()
        node.approver_type = "FORM_FIELD"
        node.approver_config = {"field_name": "approver_ids"}
        
        sample_context["form_data"]["approver_ids"] = [180, 190, 200]
        
        result = router.resolve_approvers(node, sample_context)
        
        assert result == [180, 190, 200]
    
    def test_resolve_approvers_initiator(self, router, db_mock, sample_context):
        """测试发起人"""
        node = MagicMock()
        node.approver_type = "INITIATOR"
        node.approver_config = {}
        
        result = router.resolve_approvers(node, sample_context)
        
        assert result == [100]
    
    def test_resolve_approvers_dynamic_with_adapter(self, router, db_mock, sample_context):
        """测试动态解析（通过适配器）"""
        node = MagicMock()
        node.approver_type = "DYNAMIC"
        node.approver_config = {}
        
        # Mock适配器
        adapter = MagicMock()
        adapter.resolve_approvers.return_value = [100, 200]
        sample_context["adapter"] = adapter
        
        result = router.resolve_approvers(node, sample_context)
        
        assert result == [100, 200]
        adapter.resolve_approvers.assert_called_once_with(node, sample_context)
    
    def test_resolve_approvers_unknown_type(self, router, db_mock, sample_context):
        """测试未知审批人类型"""
        node = MagicMock()
        node.approver_type = "UNKNOWN"
        node.approver_config = {}
        
        result = router.resolve_approvers(node, sample_context)
        
        assert result == []


class TestGetNextNodes:
    """测试获取下一个节点"""
    
    def test_get_next_nodes_normal(self, router, db_mock, sample_context):
        """测试正常后续节点"""
        current_node = MagicMock()
        current_node.flow_id = 1
        current_node.node_order = 1
        
        next_node = MagicMock()
        next_node.node_type = "APPROVAL"
        next_node.node_order = 2
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = [next_node]
        db_mock.query.return_value = mock_query
        
        result = router.get_next_nodes(current_node, sample_context)
        
        assert result == [next_node]
    
    def test_get_next_nodes_condition_branch(self, router, db_mock, sample_context):
        """测试条件分支节点"""
        current_node = MagicMock()
        current_node.flow_id = 1
        current_node.node_order = 1
        
        condition_node = MagicMock()
        condition_node.node_type = "CONDITION"
        condition_node.node_order = 2
        condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {
                        "operator": "AND",
                        "items": [{"field": "entity.priority", "op": "==", "value": "HIGH"}]
                    },
                    "target_node_id": 10
                }
            ]
        }
        
        target_node = MagicMock()
        target_node.id = 10
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = [condition_node]
        mock_query.first.return_value = target_node
        db_mock.query.return_value = mock_query
        
        result = router.get_next_nodes(current_node, sample_context)
        
        assert result == [target_node]
    
    def test_get_next_nodes_no_next(self, router, db_mock, sample_context):
        """测试无后续节点"""
        current_node = MagicMock()
        current_node.flow_id = 1
        current_node.node_order = 10
        
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value.all.return_value = []
        db_mock.query.return_value = mock_query
        
        result = router.get_next_nodes(current_node, sample_context)
        
        assert result == []


class TestResolveConditionBranch:
    """测试解析条件分支"""
    
    def test_resolve_condition_branch_match(self, router, db_mock, sample_context):
        """测试匹配条件分支"""
        condition_node = MagicMock()
        condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {
                        "operator": "AND",
                        "items": [{"field": "entity.priority", "op": "==", "value": "HIGH"}]
                    },
                    "target_node_id": 20
                }
            ]
        }
        
        target_node = MagicMock()
        target_node.id = 20
        
        db_mock.query.return_value.filter.return_value.first.return_value = target_node
        
        result = router._resolve_condition_branch(condition_node, sample_context)
        
        assert result == [target_node]
    
    def test_resolve_condition_branch_default(self, router, db_mock, sample_context):
        """测试使用默认分支"""
        condition_node = MagicMock()
        condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {
                        "operator": "AND",
                        "items": [{"field": "entity.priority", "op": "==", "value": "LOW"}]
                    },
                    "target_node_id": 20
                }
            ],
            "default_node_id": 30
        }
        
        default_node = MagicMock()
        default_node.id = 30
        
        db_mock.query.return_value.filter.return_value.first.return_value = default_node
        
        result = router._resolve_condition_branch(condition_node, sample_context)
        
        assert result == [default_node]
    
    def test_resolve_condition_branch_no_match_no_default(self, router, db_mock, sample_context):
        """测试无匹配且无默认分支"""
        condition_node = MagicMock()
        condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {
                        "operator": "AND",
                        "items": [{"field": "entity.priority", "op": "==", "value": "LOW"}]
                    },
                    "target_node_id": 20
                }
            ]
        }
        
        result = router._resolve_condition_branch(condition_node, sample_context)
        
        assert result == []
