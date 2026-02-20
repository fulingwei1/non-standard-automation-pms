# -*- coding: utf-8 -*-
"""
审批路由服务增强单元测试

测试覆盖：
- 流程选择逻辑
- 条件表达式评估（所有操作符）
- 审批人解析（所有类型）
- 节点路由决策
- 边界条件和异常处理
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from typing import Dict, Any

from app.services.approval_engine.router import ApprovalRouterService


class TestApprovalRouterService(unittest.TestCase):
    """审批路由服务测试"""

    def setUp(self):
        """测试前准备"""
        self.db_mock = MagicMock()
        self.service = ApprovalRouterService(self.db_mock)

    def tearDown(self):
        """测试后清理"""
        self.db_mock.reset_mock()

    # ==================== 流程选择测试 ====================

    def test_select_flow_with_matching_rule(self):
        """测试选择匹配的流程"""
        # 准备数据
        rule1 = MagicMock()
        rule1.conditions = {"operator": "AND", "items": [{"field": "form_data.amount", "op": "<=", "value": 1000}]}
        flow1 = MagicMock()
        flow1.id = 1
        flow1.flow_name = "小额流程"
        rule1.flow = flow1

        rule2 = MagicMock()
        rule2.conditions = {"operator": "AND", "items": [{"field": "form_data.amount", "op": ">", "value": 1000}]}
        flow2 = MagicMock()
        flow2.id = 2
        flow2.flow_name = "大额流程"
        rule2.flow = flow2

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.all.return_value = [rule1, rule2]

        self.db_mock.query.return_value = query_mock

        # 执行
        context = {"form_data": {"amount": 500}}
        result = self.service.select_flow(template_id=1, context=context)

        # 验证
        self.assertEqual(result.id, 1)
        self.assertEqual(result.flow_name, "小额流程")

    def test_select_flow_no_matching_rule_use_default(self):
        """测试无匹配规则时使用默认流程"""
        # 准备数据
        rule1 = MagicMock()
        rule1.conditions = {"operator": "AND", "items": [{"field": "form.amount", "op": ">", "value": 1000}]}
        rule1.flow = MagicMock(id=1)

        query_mock = MagicMock()
        filter_mock = MagicMock()
        order_by_mock = MagicMock()

        # 第一次查询返回规则
        all_mock1 = MagicMock()
        all_mock1.all.return_value = [rule1]

        # 第二次查询返回默认流程
        first_mock = MagicMock()
        default_flow = MagicMock(id=999, flow_name="默认流程", is_default=True)
        first_mock.first.return_value = default_flow

        self.db_mock.query.side_effect = [
            MagicMock(filter=lambda *args, **kwargs: MagicMock(order_by=lambda *a: all_mock1)),
            MagicMock(filter=lambda *args, **kwargs: first_mock)
        ]

        # 执行
        context = {"form_data": {"amount": 500}}
        result = self.service.select_flow(template_id=1, context=context)

        # 验证
        self.assertEqual(result.id, 999)
        self.assertEqual(result.flow_name, "默认流程")

    def test_select_flow_empty_rules(self):
        """测试空规则列表返回默认流程"""
        query_mock = MagicMock()
        filter_mock = MagicMock()
        order_by_mock = MagicMock()
        all_mock = MagicMock()

        all_mock.all.return_value = []

        default_flow = MagicMock(id=100, is_default=True)
        first_mock = MagicMock()
        first_mock.first.return_value = default_flow

        self.db_mock.query.side_effect = [
            MagicMock(filter=lambda *args, **kwargs: MagicMock(order_by=lambda *a: all_mock)),
            MagicMock(filter=lambda *args, **kwargs: first_mock)
        ]

        context = {"form_data": {}}
        result = self.service.select_flow(template_id=1, context=context)

        self.assertEqual(result.id, 100)

    def test_get_default_flow(self):
        """测试获取默认流程"""
        default_flow = MagicMock(id=10, is_default=True, is_active=True)
        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = default_flow

        self.db_mock.query.return_value = query_mock

        result = self.service._get_default_flow(template_id=1)

        self.assertEqual(result.id, 10)
        self.assertTrue(result.is_default)

    # ==================== 条件评估测试 ====================

    def test_evaluate_conditions_and_all_true(self):
        """测试AND条件全部为真"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form_data.amount", "op": "<=", "value": 1000},
                {"field": "form_data.type", "op": "==", "value": "A"}
            ]
        }
        context = {"form_data": {"amount": 500, "type": "A"}}

        result = self.service._evaluate_conditions(conditions, context)

        self.assertTrue(result)

    def test_evaluate_conditions_and_partial_false(self):
        """测试AND条件部分为假"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form_data.amount", "op": "<=", "value": 1000},
                {"field": "form_data.type", "op": "==", "value": "B"}
            ]
        }
        context = {"form_data": {"amount": 500, "type": "A"}}

        result = self.service._evaluate_conditions(conditions, context)

        self.assertFalse(result)

    def test_evaluate_conditions_or_partial_true(self):
        """测试OR条件部分为真"""
        conditions = {
            "operator": "OR",
            "items": [
                {"field": "form_data.amount", "op": ">", "value": 1000},
                {"field": "form_data.type", "op": "==", "value": "A"}
            ]
        }
        context = {"form_data": {"amount": 500, "type": "A"}}

        result = self.service._evaluate_conditions(conditions, context)

        self.assertTrue(result)

    def test_evaluate_conditions_empty_items(self):
        """测试空条件列表返回True"""
        conditions = {"operator": "AND", "items": []}
        context = {}

        result = self.service._evaluate_conditions(conditions, context)

        self.assertTrue(result)

    # ==================== 字段值获取测试 ====================

    def test_get_field_value_nested_dict(self):
        """测试获取嵌套字典值"""
        context = {
            "form_data": {"leave": {"days": 3, "type": "annual"}},
            "initiator": {"name": "张三"}
        }

        result = self.service._get_field_value("form_data.leave.days", context)
        self.assertEqual(result, 3)

    def test_get_field_value_object_attribute(self):
        """测试获取对象属性"""
        user = MagicMock()
        user.dept_id = 10
        user.name = "李四"

        context = {"initiator": user}

        result = self.service._get_field_value("initiator.dept_id", context)
        self.assertEqual(result, 10)

    def test_get_field_value_not_found(self):
        """测试获取不存在的字段返回None"""
        context = {"form_data": {"amount": 100}}

        result = self.service._get_field_value("form_data.nonexistent.field", context)
        self.assertIsNone(result)

    def test_get_field_value_empty_path(self):
        """测试空路径返回None"""
        context = {"form_data": {}}

        result = self.service._get_field_value("", context)
        self.assertIsNone(result)

    # ==================== 比较操作测试 ====================

    def test_compare_equal(self):
        """测试相等比较"""
        self.assertTrue(self.service._compare(100, "==", 100))
        self.assertFalse(self.service._compare(100, "==", 200))

    def test_compare_not_equal(self):
        """测试不等比较"""
        self.assertTrue(self.service._compare(100, "!=", 200))
        self.assertFalse(self.service._compare(100, "!=", 100))

    def test_compare_greater_than(self):
        """测试大于比较"""
        self.assertTrue(self.service._compare(200, ">", 100))
        self.assertFalse(self.service._compare(100, ">", 200))
        self.assertFalse(self.service._compare(None, ">", 100))

    def test_compare_greater_equal(self):
        """测试大于等于比较"""
        self.assertTrue(self.service._compare(100, ">=", 100))
        self.assertTrue(self.service._compare(200, ">=", 100))
        self.assertFalse(self.service._compare(50, ">=", 100))

    def test_compare_less_than(self):
        """测试小于比较"""
        self.assertTrue(self.service._compare(50, "<", 100))
        self.assertFalse(self.service._compare(150, "<", 100))

    def test_compare_less_equal(self):
        """测试小于等于比较"""
        self.assertTrue(self.service._compare(100, "<=", 100))
        self.assertTrue(self.service._compare(50, "<=", 100))
        self.assertFalse(self.service._compare(150, "<=", 100))

    def test_compare_in(self):
        """测试in操作"""
        self.assertTrue(self.service._compare("A", "in", ["A", "B", "C"]))
        self.assertFalse(self.service._compare("D", "in", ["A", "B", "C"]))
        self.assertFalse(self.service._compare("A", "in", None))

    def test_compare_not_in(self):
        """测试not_in操作"""
        self.assertTrue(self.service._compare("D", "not_in", ["A", "B", "C"]))
        self.assertFalse(self.service._compare("A", "not_in", ["A", "B", "C"]))

    def test_compare_between(self):
        """测试between操作（闭区间）"""
        self.assertTrue(self.service._compare(50, "between", [10, 100]))
        self.assertTrue(self.service._compare(10, "between", [10, 100]))
        self.assertTrue(self.service._compare(100, "between", [10, 100]))
        self.assertFalse(self.service._compare(150, "between", [10, 100]))
        self.assertFalse(self.service._compare(None, "between", [10, 100]))
        self.assertFalse(self.service._compare(50, "between", [10]))  # 无效范围

    def test_compare_contains(self):
        """测试字符串包含"""
        self.assertTrue(self.service._compare("hello world", "contains", "world"))
        self.assertFalse(self.service._compare("hello", "contains", "world"))
        self.assertFalse(self.service._compare(None, "contains", "world"))

    def test_compare_starts_with(self):
        """测试字符串前缀"""
        self.assertTrue(self.service._compare("hello world", "starts_with", "hello"))
        self.assertFalse(self.service._compare("world hello", "starts_with", "hello"))

    def test_compare_ends_with(self):
        """测试字符串后缀"""
        self.assertTrue(self.service._compare("hello world", "ends_with", "world"))
        self.assertFalse(self.service._compare("world hello", "ends_with", "world"))

    def test_compare_is_null(self):
        """测试空值判断"""
        self.assertTrue(self.service._compare(None, "is_null", True))
        self.assertFalse(self.service._compare("value", "is_null", True))
        self.assertTrue(self.service._compare("value", "is_null", False))

    def test_compare_regex(self):
        """测试正则匹配"""
        self.assertTrue(self.service._compare("test@example.com", "regex", r"^\w+@\w+\.\w+$"))
        self.assertFalse(self.service._compare("invalid-email", "regex", r"^\w+@\w+\.\w+$"))
        self.assertFalse(self.service._compare(None, "regex", r"^\w+$"))

    def test_compare_unknown_operator(self):
        """测试未知操作符返回False"""
        self.assertFalse(self.service._compare(100, "unknown_op", 100))

    def test_compare_type_error(self):
        """测试类型错误返回False"""
        self.assertFalse(self.service._compare("text", ">", 100))

    # ==================== 审批人解析测试 ====================

    def test_resolve_approvers_fixed_user(self):
        """测试固定用户审批人"""
        node = MagicMock()
        node.approver_type = "FIXED_USER"
        node.approver_config = {"user_ids": [1, 2, 3]}

        result = self.service.resolve_approvers(node, {})

        self.assertEqual(result, [1, 2, 3])

    def test_resolve_approvers_role(self):
        """测试角色审批人"""
        node = MagicMock()
        node.approver_type = "ROLE"
        node.approver_config = {"role_codes": ["MANAGER", "DIRECTOR"]}

        user1 = MagicMock(id=10)
        user2 = MagicMock(id=20)

        query_mock = MagicMock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [user1, user2]

        self.db_mock.query.return_value = query_mock

        result = self.service.resolve_approvers(node, {})

        self.assertEqual(result, [10, 20])

    def test_resolve_approvers_department_head(self):
        """测试部门主管审批人"""
        node = MagicMock()
        node.approver_type = "DEPARTMENT_HEAD"
        node.approver_config = {}

        initiator = {"dept_id": 5}
        dept = MagicMock(id=5, manager_id=100)

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = dept

        self.db_mock.query.return_value = query_mock

        context = {"initiator": initiator}
        result = self.service.resolve_approvers(node, context)

        self.assertEqual(result, [100])

    def test_resolve_approvers_direct_manager(self):
        """测试直属上级审批人"""
        node = MagicMock()
        node.approver_type = "DIRECT_MANAGER"
        node.approver_config = {}

        initiator = {"id": 10}
        user = MagicMock(id=10, reporting_to=50)

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = user

        self.db_mock.query.return_value = query_mock

        context = {"initiator": initiator}
        result = self.service.resolve_approvers(node, context)

        self.assertEqual(result, [50])

    def test_resolve_approvers_form_field_single(self):
        """测试表单字段审批人（单个）"""
        node = MagicMock()
        node.approver_type = "FORM_FIELD"
        node.approver_config = {"field_name": "approver_id"}

        context = {"form_data": {"approver_id": 99}}
        result = self.service.resolve_approvers(node, context)

        self.assertEqual(result, [99])

    def test_resolve_approvers_form_field_multiple(self):
        """测试表单字段审批人（多个）"""
        node = MagicMock()
        node.approver_type = "FORM_FIELD"
        node.approver_config = {"field_name": "approver_ids"}

        context = {"form_data": {"approver_ids": [11, 22, 33]}}
        result = self.service.resolve_approvers(node, context)

        self.assertEqual(result, [11, 22, 33])

    def test_resolve_approvers_multi_dept(self):
        """测试多部门审批人"""
        node = MagicMock()
        node.approver_type = "MULTI_DEPT"
        node.approver_config = {"departments": ["研发部", "质量部", "生产部"]}

        dept1 = MagicMock(dept_name="研发部", manager_id=101)
        dept2 = MagicMock(dept_name="质量部", manager_id=102)
        dept3 = MagicMock(dept_name="生产部", manager_id=103)

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [dept1, dept2, dept3]

        self.db_mock.query.return_value = query_mock

        result = self.service.resolve_approvers(node, {})

        self.assertEqual(sorted(result), [101, 102, 103])

    def test_resolve_approvers_dynamic_with_adapter(self):
        """测试动态审批人（通过适配器）"""
        node = MagicMock()
        node.approver_type = "DYNAMIC"
        node.approver_config = {}

        adapter = MagicMock()
        adapter.resolve_approvers.return_value = [200, 201]

        context = {"adapter": adapter}
        result = self.service.resolve_approvers(node, context)

        self.assertEqual(result, [200, 201])
        adapter.resolve_approvers.assert_called_once_with(node, context)

    def test_resolve_approvers_initiator(self):
        """测试发起人审批人（退回场景）"""
        node = MagicMock()
        node.approver_type = "INITIATOR"
        node.approver_config = {}

        initiator = {"id": 88}
        context = {"initiator": initiator}
        result = self.service.resolve_approvers(node, context)

        self.assertEqual(result, [88])

    def test_resolve_approvers_initiator_object(self):
        """测试发起人对象形式"""
        node = MagicMock()
        node.approver_type = "INITIATOR"
        node.approver_config = {}

        initiator = MagicMock()
        initiator.id = 77
        type(initiator).id = PropertyMock(return_value=77)
        initiator.get.return_value = None  # 确保get方法返回None，让代码走hasattr分支
        
        context = {"initiator": initiator}
        result = self.service.resolve_approvers(node, context)

        self.assertEqual(result, [77])

    def test_resolve_approvers_unknown_type(self):
        """测试未知类型返回空列表"""
        node = MagicMock()
        node.approver_type = "UNKNOWN"
        node.approver_config = {}

        result = self.service.resolve_approvers(node, {})

        self.assertEqual(result, [])

    # ==================== 节点路由测试 ====================

    def test_get_next_nodes_normal_node(self):
        """测试获取普通下一节点"""
        current_node = MagicMock()
        current_node.flow_id = 1
        current_node.node_order = 10

        next_node = MagicMock(node_type="APPROVAL", node_order=20)

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.all.return_value = [next_node]

        self.db_mock.query.return_value = query_mock

        result = self.service.get_next_nodes(current_node, {})

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].node_type, "APPROVAL")

    def test_get_next_nodes_no_next(self):
        """测试无下一节点（流程结束）"""
        current_node = MagicMock()
        current_node.flow_id = 1
        current_node.node_order = 100

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.order_by.return_value = query_mock
        query_mock.all.return_value = []

        self.db_mock.query.return_value = query_mock

        result = self.service.get_next_nodes(current_node, {})

        self.assertEqual(result, [])

    def test_get_next_nodes_condition_branch(self):
        """测试条件分支节点"""
        current_node = MagicMock()
        current_node.flow_id = 1
        current_node.node_order = 10

        condition_node = MagicMock()
        condition_node.node_type = "CONDITION"
        condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {"operator": "AND", "items": [{"field": "form.amount", "op": ">", "value": 1000}]},
                    "target_node_id": 100
                }
            ],
            "default_node_id": 200
        }

        target_node = MagicMock(id=100, node_type="APPROVAL")

        # 第一次查询返回条件节点
        query_mock1 = MagicMock()
        query_mock1.filter.return_value = query_mock1
        query_mock1.order_by.return_value = query_mock1
        query_mock1.all.return_value = [condition_node]

        # 第二次查询返回目标节点
        query_mock2 = MagicMock()
        query_mock2.filter.return_value = query_mock2
        query_mock2.first.return_value = target_node

        self.db_mock.query.side_effect = [query_mock1, query_mock2]

        context = {"form_data": {"amount": 5000}}
        result = self.service.get_next_nodes(current_node, context)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 100)

    def test_resolve_condition_branch_default(self):
        """测试条件分支无匹配走默认分支"""
        condition_node = MagicMock()
        condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {"operator": "AND", "items": [{"field": "form.amount", "op": ">", "value": 1000}]},
                    "target_node_id": 100
                }
            ],
            "default_node_id": 200
        }

        default_node = MagicMock(id=200, node_type="APPROVAL")

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = default_node

        self.db_mock.query.return_value = query_mock

        context = {"form_data": {"amount": 500}}
        result = self.service._resolve_condition_branch(condition_node, context)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, 200)

    # ==================== 边界条件测试 ====================

    def test_resolve_role_approvers_empty_roles(self):
        """测试角色为空时返回空列表"""
        config = {"role_codes": []}
        result = self.service._resolve_role_approvers(config, {})
        self.assertEqual(result, [])

    def test_resolve_role_approvers_single_string(self):
        """测试单个角色字符串"""
        config = {"role_codes": "ADMIN"}

        user1 = MagicMock(id=10)
        query_mock = MagicMock()
        query_mock.join.return_value = query_mock
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [user1]

        self.db_mock.query.return_value = query_mock

        result = self.service._resolve_role_approvers(config, {})
        self.assertEqual(result, [10])

    def test_resolve_department_head_no_dept_id(self):
        """测试无部门ID返回空列表"""
        initiator = {"id": 1}  # 无dept_id
        context = {"initiator": initiator}

        result = self.service._resolve_department_head(context)
        self.assertEqual(result, [])

    def test_resolve_department_head_no_manager(self):
        """测试部门无主管返回空列表"""
        initiator = {"dept_id": 5}
        dept = MagicMock(id=5, manager_id=None)

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = dept

        self.db_mock.query.return_value = query_mock

        context = {"initiator": initiator}
        result = self.service._resolve_department_head(context)
        self.assertEqual(result, [])

    def test_resolve_direct_manager_no_reporting_to(self):
        """测试无直属上级返回空列表"""
        initiator = {"id": 10}
        user = MagicMock(id=10, reporting_to=None)

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.first.return_value = user

        self.db_mock.query.return_value = query_mock

        context = {"initiator": initiator}
        result = self.service._resolve_direct_manager(context)
        self.assertEqual(result, [])

    def test_resolve_multi_dept_approvers_empty_depts(self):
        """测试空部门列表返回空列表"""
        config = {"departments": []}
        result = self.service._resolve_multi_dept_approvers(config, {})
        self.assertEqual(result, [])

    def test_resolve_multi_dept_approvers_some_without_manager(self):
        """测试部分部门无主管"""
        config = {"departments": ["研发部", "质量部"]}

        dept1 = MagicMock(dept_name="研发部", manager_id=101)
        dept2 = MagicMock(dept_name="质量部", manager_id=None)

        query_mock = MagicMock()
        query_mock.filter.return_value = query_mock
        query_mock.all.return_value = [dept1, dept2]

        self.db_mock.query.return_value = query_mock

        result = self.service._resolve_multi_dept_approvers(config, {})
        self.assertEqual(result, [101])

    def test_resolve_condition_branch_no_matching_no_default(self):
        """测试无匹配且无默认分支返回空列表"""
        condition_node = MagicMock()
        condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {"operator": "AND", "items": [{"field": "form.amount", "op": ">", "value": 1000}]},
                    "target_node_id": 100
                }
            ]
        }

        context = {"form_data": {"amount": 500}}
        result = self.service._resolve_condition_branch(condition_node, context)

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
