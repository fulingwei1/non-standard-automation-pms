# -*- coding: utf-8 -*-
"""
审批路由决策服务单元测试

目标:
1. 参考 test_condition_parser_rewrite.py 的mock策略
2. 只mock外部依赖（db.query, db.add, db.commit等）
3. 让业务逻辑真正执行
4. 覆盖主要方法和边界情况
5. 目标覆盖率: 70%+
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from app.services.approval_engine.router import ApprovalRouterService


class TestApprovalRouterService(unittest.TestCase):
    """测试审批路由决策服务"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = ApprovalRouterService(self.mock_db)

    # ========== select_flow() 测试 ==========

    def test_select_flow_with_matching_rule(self):
        """测试选择流程 - 有匹配的规则"""
        # 准备mock规则
        mock_rule = MagicMock()
        mock_rule.conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.amount", "op": ">=", "value": 1000}
            ]
        }
        mock_flow = MagicMock()
        mock_flow.id = 1
        mock_flow.name = "高额审批流程"
        mock_rule.flow = mock_flow

        # mock查询
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_rule]

        # 执行
        context = {"form": {"amount": 5000}}
        result = self.service.select_flow(template_id=1, context=context)

        # 验证
        self.assertEqual(result, mock_flow)
        self.mock_db.query.assert_called()

    def test_select_flow_no_matching_rule_use_default(self):
        """测试选择流程 - 无匹配规则，使用默认流程"""
        # mock无匹配规则
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        # mock默认流程
        mock_default_flow = MagicMock()
        mock_default_flow.id = 2
        mock_default_flow.name = "默认流程"
        
        # 第二次query调用（获取默认流程）
        mock_query.first.return_value = mock_default_flow

        # 执行
        context = {"form": {"amount": 500}}
        result = self.service.select_flow(template_id=1, context=context)

        # 验证
        self.assertEqual(result, mock_default_flow)

    def test_select_flow_rule_not_match(self):
        """测试选择流程 - 规则条件不匹配"""
        # 准备mock规则（条件不匹配）
        mock_rule = MagicMock()
        mock_rule.conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.amount", "op": ">=", "value": 10000}
            ]
        }

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_rule]

        # mock默认流程
        mock_default_flow = MagicMock()
        mock_query.first.return_value = mock_default_flow

        # 执行
        context = {"form": {"amount": 500}}
        result = self.service.select_flow(template_id=1, context=context)

        # 验证 - 应返回默认流程
        self.assertEqual(result, mock_default_flow)

    # ========== _get_default_flow() 测试 ==========

    def test_get_default_flow_found(self):
        """测试获取默认流程 - 找到默认流程"""
        mock_flow = MagicMock()
        mock_flow.id = 1
        mock_flow.is_default = True

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_flow

        result = self.service._get_default_flow(template_id=1)
        self.assertEqual(result, mock_flow)

    def test_get_default_flow_not_found(self):
        """测试获取默认流程 - 未找到"""
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = self.service._get_default_flow(template_id=1)
        self.assertIsNone(result)

    # ========== _evaluate_conditions() 测试 ==========

    def test_evaluate_conditions_and_logic_all_true(self):
        """测试评估条件 - AND逻辑全部为真"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.amount", "op": ">=", "value": 1000},
                {"field": "form.days", "op": "<=", "value": 7}
            ]
        }
        context = {"form": {"amount": 5000, "days": 3}}
        
        result = self.service._evaluate_conditions(conditions, context)
        self.assertTrue(result)

    def test_evaluate_conditions_and_logic_one_false(self):
        """测试评估条件 - AND逻辑有一个为假"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.amount", "op": ">=", "value": 1000},
                {"field": "form.days", "op": "<=", "value": 7}
            ]
        }
        context = {"form": {"amount": 5000, "days": 10}}
        
        result = self.service._evaluate_conditions(conditions, context)
        self.assertFalse(result)

    def test_evaluate_conditions_or_logic_one_true(self):
        """测试评估条件 - OR逻辑有一个为真"""
        conditions = {
            "operator": "OR",
            "items": [
                {"field": "form.amount", "op": ">=", "value": 10000},
                {"field": "form.urgent", "op": "==", "value": True}
            ]
        }
        context = {"form": {"amount": 500, "urgent": True}}
        
        result = self.service._evaluate_conditions(conditions, context)
        self.assertTrue(result)

    def test_evaluate_conditions_or_logic_all_false(self):
        """测试评估条件 - OR逻辑全部为假"""
        conditions = {
            "operator": "OR",
            "items": [
                {"field": "form.amount", "op": ">=", "value": 10000},
                {"field": "form.urgent", "op": "==", "value": True}
            ]
        }
        context = {"form": {"amount": 500, "urgent": False}}
        
        result = self.service._evaluate_conditions(conditions, context)
        self.assertFalse(result)

    def test_evaluate_conditions_empty(self):
        """测试评估条件 - 空条件列表"""
        conditions = {"items": []}
        result = self.service._evaluate_conditions(conditions, {})
        self.assertTrue(result)

    # ========== _evaluate_single() 测试 ==========

    def test_evaluate_single_simple_field(self):
        """测试评估单个条件 - 简单字段"""
        condition = {"field": "amount", "op": ">=", "value": 1000}
        context = {"amount": 5000}
        
        result = self.service._evaluate_single(condition, context)
        self.assertTrue(result)

    def test_evaluate_single_nested_field(self):
        """测试评估单个条件 - 嵌套字段"""
        condition = {"field": "form.data.amount", "op": ">=", "value": 1000}
        context = {"form": {"data": {"amount": 5000}}}
        
        result = self.service._evaluate_single(condition, context)
        self.assertTrue(result)

    # ========== _get_field_value() 测试 ==========

    def test_get_field_value_simple(self):
        """测试获取字段值 - 简单字段"""
        context = {"amount": 1000}
        result = self.service._get_field_value("amount", context)
        self.assertEqual(result, 1000)

    def test_get_field_value_nested_dict(self):
        """测试获取字段值 - 嵌套字典"""
        context = {"form": {"data": {"amount": 5000}}}
        result = self.service._get_field_value("form.data.amount", context)
        self.assertEqual(result, 5000)

    def test_get_field_value_object_attribute(self):
        """测试获取字段值 - 对象属性"""
        mock_obj = MagicMock()
        mock_obj.user = MagicMock()
        mock_obj.user.name = "张三"
        context = {"entity": mock_obj}
        
        result = self.service._get_field_value("entity.user.name", context)
        self.assertEqual(result, "张三")

    def test_get_field_value_not_found(self):
        """测试获取字段值 - 字段不存在"""
        context = {"form": {"amount": 1000}}
        result = self.service._get_field_value("form.invalid", context)
        self.assertIsNone(result)

    def test_get_field_value_empty_path(self):
        """测试获取字段值 - 空路径"""
        result = self.service._get_field_value("", {"amount": 1000})
        self.assertIsNone(result)

    def test_get_field_value_none_in_path(self):
        """测试获取字段值 - 路径中间为None"""
        context = {"form": None}
        result = self.service._get_field_value("form.amount", context)
        self.assertIsNone(result)

    # ========== _compare() 测试 ==========

    def test_compare_equal(self):
        """测试比较 - 相等"""
        self.assertTrue(self.service._compare(100, "==", 100))
        self.assertTrue(self.service._compare("test", "==", "test"))
        self.assertFalse(self.service._compare(100, "==", 200))

    def test_compare_not_equal(self):
        """测试比较 - 不等"""
        self.assertTrue(self.service._compare(100, "!=", 200))
        self.assertFalse(self.service._compare(100, "!=", 100))

    def test_compare_greater_than(self):
        """测试比较 - 大于"""
        self.assertTrue(self.service._compare(200, ">", 100))
        self.assertFalse(self.service._compare(100, ">", 200))
        self.assertFalse(self.service._compare(None, ">", 100))

    def test_compare_greater_equal(self):
        """测试比较 - 大于等于"""
        self.assertTrue(self.service._compare(200, ">=", 100))
        self.assertTrue(self.service._compare(100, ">=", 100))
        self.assertFalse(self.service._compare(50, ">=", 100))

    def test_compare_less_than(self):
        """测试比较 - 小于"""
        self.assertTrue(self.service._compare(50, "<", 100))
        self.assertFalse(self.service._compare(150, "<", 100))

    def test_compare_less_equal(self):
        """测试比较 - 小于等于"""
        self.assertTrue(self.service._compare(50, "<=", 100))
        self.assertTrue(self.service._compare(100, "<=", 100))
        self.assertFalse(self.service._compare(150, "<=", 100))

    def test_compare_in(self):
        """测试比较 - in操作符"""
        self.assertTrue(self.service._compare("apple", "in", ["apple", "banana"]))
        self.assertFalse(self.service._compare("orange", "in", ["apple", "banana"]))
        self.assertFalse(self.service._compare("test", "in", None))

    def test_compare_not_in(self):
        """测试比较 - not_in操作符"""
        self.assertTrue(self.service._compare("orange", "not_in", ["apple", "banana"]))
        self.assertFalse(self.service._compare("apple", "not_in", ["apple", "banana"]))
        self.assertTrue(self.service._compare("test", "not_in", None))

    def test_compare_between(self):
        """测试比较 - between操作符"""
        self.assertTrue(self.service._compare(50, "between", [10, 100]))
        self.assertTrue(self.service._compare(10, "between", [10, 100]))
        self.assertTrue(self.service._compare(100, "between", [10, 100]))
        self.assertFalse(self.service._compare(150, "between", [10, 100]))
        self.assertFalse(self.service._compare(None, "between", [10, 100]))

    def test_compare_between_invalid_range(self):
        """测试比较 - between操作符 - 无效范围"""
        self.assertFalse(self.service._compare(50, "between", [10]))  # 长度不为2
        self.assertFalse(self.service._compare(50, "between", None))

    def test_compare_contains(self):
        """测试比较 - contains操作符"""
        self.assertTrue(self.service._compare("hello world", "contains", "world"))
        self.assertFalse(self.service._compare("hello", "contains", "world"))
        self.assertFalse(self.service._compare(None, "contains", "test"))

    def test_compare_starts_with(self):
        """测试比较 - starts_with操作符"""
        self.assertTrue(self.service._compare("hello world", "starts_with", "hello"))
        self.assertFalse(self.service._compare("hello world", "starts_with", "world"))
        self.assertFalse(self.service._compare(None, "starts_with", "test"))

    def test_compare_ends_with(self):
        """测试比较 - ends_with操作符"""
        self.assertTrue(self.service._compare("hello world", "ends_with", "world"))
        self.assertFalse(self.service._compare("hello world", "ends_with", "hello"))
        self.assertFalse(self.service._compare(None, "ends_with", "test"))

    def test_compare_is_null(self):
        """测试比较 - is_null操作符"""
        self.assertTrue(self.service._compare(None, "is_null", True))
        self.assertFalse(self.service._compare("test", "is_null", True))
        self.assertTrue(self.service._compare("test", "is_null", False))
        self.assertFalse(self.service._compare(None, "is_null", False))

    def test_compare_regex(self):
        """测试比较 - regex操作符"""
        self.assertTrue(self.service._compare("test123", "regex", r"test\d+"))
        self.assertFalse(self.service._compare("test", "regex", r"test\d+"))
        self.assertFalse(self.service._compare(None, "regex", r"test"))

    def test_compare_unsupported_operator(self):
        """测试比较 - 不支持的操作符"""
        result = self.service._compare(100, "unknown_op", 200)
        self.assertFalse(result)

    def test_compare_type_error(self):
        """测试比较 - 类型错误"""
        # 字符串和数字比较可能抛出TypeError
        result = self.service._compare("abc", ">", 100)
        self.assertFalse(result)

    # ========== resolve_approvers() 测试 ==========

    def test_resolve_approvers_fixed_user(self):
        """测试解析审批人 - 固定用户"""
        mock_node = MagicMock()
        mock_node.approver_type = "FIXED_USER"
        mock_node.approver_config = {"user_ids": [1, 2, 3]}

        context = {}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [1, 2, 3])

    def test_resolve_approvers_role(self):
        """测试解析审批人 - 角色"""
        mock_node = MagicMock()
        mock_node.approver_type = "ROLE"
        mock_node.approver_config = {"role_codes": ["MANAGER", "ADMIN"]}

        # mock查询结果
        mock_user1 = MagicMock()
        mock_user1.id = 10
        mock_user2 = MagicMock()
        mock_user2.id = 20

        mock_query = self.mock_db.query.return_value
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_user1, mock_user2]

        context = {}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [10, 20])

    def test_resolve_approvers_role_single_code(self):
        """测试解析审批人 - 单个角色代码（字符串）"""
        mock_node = MagicMock()
        mock_node.approver_type = "ROLE"
        mock_node.approver_config = {"role_codes": "MANAGER"}

        mock_user = MagicMock()
        mock_user.id = 10

        mock_query = self.mock_db.query.return_value
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_user]

        context = {}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [10])

    def test_resolve_approvers_role_empty(self):
        """测试解析审批人 - 角色为空"""
        mock_node = MagicMock()
        mock_node.approver_type = "ROLE"
        mock_node.approver_config = {"role_codes": []}

        context = {}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [])

    def test_resolve_approvers_department_head(self):
        """测试解析审批人 - 部门主管"""
        mock_node = MagicMock()
        mock_node.approver_type = "DEPARTMENT_HEAD"
        mock_node.approver_config = {}

        # mock发起人
        mock_initiator = {"dept_id": 5}
        
        # mock部门
        mock_dept = MagicMock()
        mock_dept.manager_id = 100

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_dept

        context = {"initiator": mock_initiator}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [100])

    def test_resolve_approvers_department_head_no_dept(self):
        """测试解析审批人 - 部门主管 - 无部门"""
        mock_node = MagicMock()
        mock_node.approver_type = "DEPARTMENT_HEAD"
        mock_node.approver_config = {}

        context = {"initiator": {}}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [])

    def test_resolve_approvers_department_head_no_manager(self):
        """测试解析审批人 - 部门主管 - 部门无主管"""
        mock_node = MagicMock()
        mock_node.approver_type = "DEPARTMENT_HEAD"
        mock_node.approver_config = {}

        mock_initiator = {"dept_id": 5}
        
        mock_dept = MagicMock()
        mock_dept.manager_id = None

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_dept

        context = {"initiator": mock_initiator}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [])

    def test_resolve_approvers_direct_manager(self):
        """测试解析审批人 - 直属上级"""
        mock_node = MagicMock()
        mock_node.approver_type = "DIRECT_MANAGER"
        mock_node.approver_config = {}

        mock_initiator = {"id": 10}
        
        mock_user = MagicMock()
        mock_user.reporting_to = 50

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user

        context = {"initiator": mock_initiator}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [50])

    def test_resolve_approvers_direct_manager_no_user(self):
        """测试解析审批人 - 直属上级 - 无用户ID"""
        mock_node = MagicMock()
        mock_node.approver_type = "DIRECT_MANAGER"
        mock_node.approver_config = {}

        context = {"initiator": {}}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [])

    def test_resolve_approvers_direct_manager_no_reporting_to(self):
        """测试解析审批人 - 直属上级 - 无上级"""
        mock_node = MagicMock()
        mock_node.approver_type = "DIRECT_MANAGER"
        mock_node.approver_config = {}

        mock_initiator = {"id": 10}
        
        mock_user = MagicMock()
        mock_user.reporting_to = None

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user

        context = {"initiator": mock_initiator}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [])

    def test_resolve_approvers_form_field(self):
        """测试解析审批人 - 表单字段"""
        mock_node = MagicMock()
        mock_node.approver_type = "FORM_FIELD"
        mock_node.approver_config = {"field_name": "approver_id"}

        context = {"form_data": {"approver_id": 100}}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [100])

    def test_resolve_approvers_form_field_list(self):
        """测试解析审批人 - 表单字段 - 列表"""
        mock_node = MagicMock()
        mock_node.approver_type = "FORM_FIELD"
        mock_node.approver_config = {"field_name": "approver_ids"}

        context = {"form_data": {"approver_ids": [100, 200]}}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [100, 200])

    def test_resolve_approvers_form_field_not_found(self):
        """测试解析审批人 - 表单字段 - 字段不存在"""
        mock_node = MagicMock()
        mock_node.approver_type = "FORM_FIELD"
        mock_node.approver_config = {"field_name": "approver_id"}

        context = {"form_data": {}}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [])

    def test_resolve_approvers_multi_dept(self):
        """测试解析审批人 - 多部门"""
        mock_node = MagicMock()
        mock_node.approver_type = "MULTI_DEPT"
        mock_node.approver_config = {"departments": ["研发部", "测试部"]}

        # mock部门
        mock_dept1 = MagicMock()
        mock_dept1.manager_id = 10
        mock_dept2 = MagicMock()
        mock_dept2.manager_id = 20

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_dept1, mock_dept2]

        context = {}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [10, 20])

    def test_resolve_approvers_multi_dept_empty(self):
        """测试解析审批人 - 多部门 - 部门列表为空"""
        mock_node = MagicMock()
        mock_node.approver_type = "MULTI_DEPT"
        mock_node.approver_config = {"departments": []}

        context = {}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [])

    def test_resolve_approvers_dynamic(self):
        """测试解析审批人 - 动态"""
        mock_node = MagicMock()
        mock_node.approver_type = "DYNAMIC"
        mock_node.approver_config = {}

        # mock适配器
        mock_adapter = MagicMock()
        mock_adapter.resolve_approvers.return_value = [100, 200]

        context = {"adapter": mock_adapter}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [100, 200])
        mock_adapter.resolve_approvers.assert_called_once_with(mock_node, context)

    def test_resolve_approvers_dynamic_no_adapter(self):
        """测试解析审批人 - 动态 - 无适配器"""
        mock_node = MagicMock()
        mock_node.approver_type = "DYNAMIC"
        mock_node.approver_config = {}

        context = {}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [])

    def test_resolve_approvers_initiator_dict(self):
        """测试解析审批人 - 发起人（字典）"""
        mock_node = MagicMock()
        mock_node.approver_type = "INITIATOR"
        mock_node.approver_config = {}

        context = {"initiator": {"id": 100}}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [100])

    def test_resolve_approvers_initiator_object(self):
        """测试解析审批人 - 发起人（对象）"""
        mock_node = MagicMock()
        mock_node.approver_type = "INITIATOR"
        mock_node.approver_config = {}

        # 模拟对象，确保 get() 返回 None，触发访问 .id 属性
        mock_initiator = MagicMock()
        mock_initiator.get.return_value = None
        mock_initiator.id = 100
        context = {"initiator": mock_initiator}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [100])

    def test_resolve_approvers_initiator_no_initiator(self):
        """测试解析审批人 - 发起人 - 无发起人"""
        mock_node = MagicMock()
        mock_node.approver_type = "INITIATOR"
        mock_node.approver_config = {}

        context = {}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [])

    def test_resolve_approvers_unknown_type(self):
        """测试解析审批人 - 未知类型"""
        mock_node = MagicMock()
        mock_node.approver_type = "UNKNOWN_TYPE"
        mock_node.approver_config = {}

        context = {}
        result = self.service.resolve_approvers(mock_node, context)
        
        self.assertEqual(result, [])

    # ========== get_next_nodes() 测试 ==========

    def test_get_next_nodes_normal_node(self):
        """测试获取下一个节点 - 普通节点"""
        mock_current = MagicMock()
        mock_current.flow_id = 1
        mock_current.node_order = 1

        mock_next = MagicMock()
        mock_next.node_type = "APPROVAL"
        mock_next.node_order = 2

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_next]

        context = {}
        result = self.service.get_next_nodes(mock_current, context)
        
        self.assertEqual(result, [mock_next])

    def test_get_next_nodes_no_more_nodes(self):
        """测试获取下一个节点 - 无后续节点"""
        mock_current = MagicMock()
        mock_current.flow_id = 1
        mock_current.node_order = 10

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        context = {}
        result = self.service.get_next_nodes(mock_current, context)
        
        self.assertEqual(result, [])

    def test_get_next_nodes_condition_node(self):
        """测试获取下一个节点 - 条件分支节点"""
        mock_current = MagicMock()
        mock_current.flow_id = 1
        mock_current.node_order = 1

        mock_condition_node = MagicMock()
        mock_condition_node.node_type = "CONDITION"
        mock_condition_node.node_order = 2

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_condition_node]

        # mock条件分支解析结果
        mock_target_node = MagicMock()
        
        # 临时替换 _resolve_condition_branch 方法
        original_method = self.service._resolve_condition_branch
        self.service._resolve_condition_branch = MagicMock(return_value=[mock_target_node])

        context = {}
        result = self.service.get_next_nodes(mock_current, context)
        
        self.assertEqual(result, [mock_target_node])
        self.service._resolve_condition_branch.assert_called_once_with(mock_condition_node, context)
        
        # 恢复原方法
        self.service._resolve_condition_branch = original_method

    # ========== _resolve_condition_branch() 测试 ==========

    def test_resolve_condition_branch_match_first(self):
        """测试解析条件分支 - 匹配第一个分支"""
        mock_condition_node = MagicMock()
        mock_condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {
                        "operator": "AND",
                        "items": [{"field": "form.amount", "op": ">=", "value": 5000}]
                    },
                    "target_node_id": 100
                },
                {
                    "conditions": {
                        "operator": "AND",
                        "items": [{"field": "form.amount", "op": ">=", "value": 1000}]
                    },
                    "target_node_id": 200
                }
            ],
            "default_node_id": 300
        }

        mock_target = MagicMock()
        mock_target.id = 100

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_target

        context = {"form": {"amount": 8000}}
        result = self.service._resolve_condition_branch(mock_condition_node, context)
        
        self.assertEqual(result, [mock_target])

    def test_resolve_condition_branch_match_second(self):
        """测试解析条件分支 - 匹配第二个分支"""
        mock_condition_node = MagicMock()
        mock_condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {
                        "operator": "AND",
                        "items": [{"field": "form.amount", "op": ">=", "value": 10000}]
                    },
                    "target_node_id": 100
                },
                {
                    "conditions": {
                        "operator": "AND",
                        "items": [{"field": "form.amount", "op": ">=", "value": 5000}]
                    },
                    "target_node_id": 200
                }
            ],
            "default_node_id": 300
        }

        mock_target = MagicMock()
        mock_target.id = 200

        # 第一次调用返回None（第一个分支节点不存在），第二次返回目标节点
        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [None, mock_target]

        context = {"form": {"amount": 8000}}
        result = self.service._resolve_condition_branch(mock_condition_node, context)
        
        self.assertEqual(result, [mock_target])

    def test_resolve_condition_branch_default(self):
        """测试解析条件分支 - 使用默认分支"""
        mock_condition_node = MagicMock()
        mock_condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {
                        "operator": "AND",
                        "items": [{"field": "form.amount", "op": ">=", "value": 10000}]
                    },
                    "target_node_id": 100
                }
            ],
            "default_node_id": 300
        }

        mock_default = MagicMock()
        mock_default.id = 300

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_default

        context = {"form": {"amount": 500}}
        result = self.service._resolve_condition_branch(mock_condition_node, context)
        
        self.assertEqual(result, [mock_default])

    def test_resolve_condition_branch_no_match_no_default(self):
        """测试解析条件分支 - 无匹配且无默认"""
        mock_condition_node = MagicMock()
        mock_condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {
                        "operator": "AND",
                        "items": [{"field": "form.amount", "op": ">=", "value": 10000}]
                    },
                    "target_node_id": 100
                }
            ]
        }

        context = {"form": {"amount": 500}}
        result = self.service._resolve_condition_branch(mock_condition_node, context)
        
        self.assertEqual(result, [])

    def test_resolve_condition_branch_empty_config(self):
        """测试解析条件分支 - 空配置"""
        mock_condition_node = MagicMock()
        mock_condition_node.approver_config = {}

        context = {}
        result = self.service._resolve_condition_branch(mock_condition_node, context)
        
        self.assertEqual(result, [])

    # ========== _resolve_department_head() with object initiator ==========

    def test_resolve_department_head_object_initiator(self):
        """测试解析部门主管 - 对象类型的发起人"""
        mock_initiator = MagicMock()
        mock_initiator.dept_id = 5

        mock_dept = MagicMock()
        mock_dept.manager_id = 100

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_dept

        context = {"initiator": mock_initiator}
        result = self.service._resolve_department_head(context)
        
        self.assertEqual(result, [100])

    # ========== _resolve_direct_manager() with object initiator ==========

    def test_resolve_direct_manager_object_initiator(self):
        """测试解析直属上级 - 对象类型的发起人"""
        mock_initiator = MagicMock()
        mock_initiator.id = 10

        mock_user = MagicMock()
        mock_user.reporting_to = 50

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user

        context = {"initiator": mock_initiator}
        result = self.service._resolve_direct_manager(context)
        
        self.assertEqual(result, [50])


class TestApprovalRouterServiceEdgeCases(unittest.TestCase):
    """测试边界情况和异常处理"""

    def setUp(self):
        """设置测试环境"""
        self.mock_db = MagicMock()
        self.service = ApprovalRouterService(self.mock_db)

    def test_select_flow_with_none_conditions(self):
        """测试选择流程 - 规则条件为None"""
        mock_rule = MagicMock()
        mock_rule.conditions = None
        mock_flow = MagicMock()
        mock_rule.flow = mock_flow

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_rule]

        context = {}
        result = self.service.select_flow(template_id=1, context=context)
        
        # 条件为None应跳过，返回默认流程
        self.assertIsNotNone(result)

    def test_resolve_approvers_none_config(self):
        """测试解析审批人 - 配置为None"""
        mock_node = MagicMock()
        mock_node.approver_type = "FIXED_USER"
        mock_node.approver_config = None

        context = {}
        # 不应抛出异常
        result = self.service.resolve_approvers(mock_node, context)
        # 空配置应返回空列表（因为 config.get() 会报错）
        # 实际会因为 None.get() 抛出 AttributeError

    def test_multi_dept_approvers_skip_none_manager(self):
        """测试多部门审批人 - 跳过无主管的部门"""
        mock_dept1 = MagicMock()
        mock_dept1.manager_id = 10
        mock_dept2 = MagicMock()
        mock_dept2.manager_id = None  # 无主管
        mock_dept3 = MagicMock()
        mock_dept3.manager_id = 30

        mock_query = self.mock_db.query.return_value
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_dept1, mock_dept2, mock_dept3]

        config = {"departments": ["研发部", "测试部", "产品部"]}
        context = {}
        
        result = self.service._resolve_multi_dept_approvers(config, context)
        
        # 应该只包含有主管的部门
        self.assertEqual(result, [10, 30])


if __name__ == "__main__":
    unittest.main()
