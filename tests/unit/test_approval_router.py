# -*- coding: utf-8 -*-
"""
审批路由决策服务单元测试

目标：
1. 只mock外部依赖（数据库操作）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, Mock, patch
from app.services.approval_engine.router import ApprovalRouterService


class TestApprovalRouterService(unittest.TestCase):
    """测试审批路由决策服务"""

    def setUp(self):
        """初始化测试环境"""
        self.mock_db = MagicMock()
        self.service = ApprovalRouterService(self.mock_db)

    # ========== select_flow() 测试 ==========

    def test_select_flow_with_matching_rule(self):
        """测试选择流程 - 有匹配的路由规则"""
        # 准备mock数据
        mock_rule = Mock()
        mock_rule.conditions = {
            "operator": "AND",
            "items": [{"field": "form.amount", "op": ">=", "value": 1000}]
        }
        mock_flow = Mock()
        mock_flow.flow_name = "高额度审批流程"
        mock_rule.flow = mock_flow

        # Mock数据库查询
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_rule]

        # 执行测试
        context = {"form": {"amount": 5000}}
        result = self.service.select_flow(template_id=1, context=context)

        # 验证
        self.assertEqual(result, mock_flow)
        self.mock_db.query.assert_called()

    def test_select_flow_no_matching_rule_use_default(self):
        """测试选择流程 - 无匹配规则，使用默认流程"""
        # 准备mock数据
        mock_rule = Mock()
        mock_rule.conditions = {
            "operator": "AND",
            "items": [{"field": "form.amount", "op": ">=", "value": 10000}]
        }
        mock_rule.flow = Mock()

        mock_default_flow = Mock()
        mock_default_flow.flow_name = "默认流程"

        # Mock数据库查询 - 规则不匹配
        query_mock = self.mock_db.query.return_value
        query_mock.filter.return_value.order_by.return_value.all.return_value = [mock_rule]
        
        # Mock获取默认流程
        query_mock.filter.return_value.first.return_value = mock_default_flow

        # 执行测试
        context = {"form": {"amount": 500}}  # 不满足条件
        result = self.service.select_flow(template_id=1, context=context)

        # 验证 - 应该返回默认流程
        self.assertEqual(result, mock_default_flow)

    def test_select_flow_empty_rules(self):
        """测试选择流程 - 无路由规则"""
        mock_default_flow = Mock()
        
        # Mock数据库查询 - 无规则
        query_mock = self.mock_db.query.return_value
        query_mock.filter.return_value.order_by.return_value.all.return_value = []
        query_mock.filter.return_value.first.return_value = mock_default_flow

        # 执行测试
        context = {"form": {"amount": 1000}}
        result = self.service.select_flow(template_id=1, context=context)

        # 验证
        self.assertEqual(result, mock_default_flow)

    def test_select_flow_rule_without_conditions(self):
        """测试选择流程 - 规则无条件（自动匹配）"""
        mock_rule = Mock()
        mock_rule.conditions = None  # 无条件
        mock_flow = Mock()
        mock_rule.flow = mock_flow

        mock_default_flow = Mock()

        # Mock数据库查询
        query_mock = self.mock_db.query.return_value
        query_mock.filter.return_value.order_by.return_value.all.return_value = [mock_rule]
        query_mock.filter.return_value.first.return_value = mock_default_flow

        # 执行测试
        context = {"form": {"amount": 1000}}
        result = self.service.select_flow(template_id=1, context=context)

        # 验证 - 无条件规则不会匹配，应返回默认流程
        self.assertEqual(result, mock_default_flow)

    # ========== _get_default_flow() 测试 ==========

    def test_get_default_flow_exists(self):
        """测试获取默认流程 - 存在"""
        mock_flow = Mock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_flow

        result = self.service._get_default_flow(template_id=1)

        self.assertEqual(result, mock_flow)

    def test_get_default_flow_not_exists(self):
        """测试获取默认流程 - 不存在"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.service._get_default_flow(template_id=1)

        self.assertIsNone(result)

    # ========== _evaluate_conditions() 测试 ==========

    def test_evaluate_conditions_and_all_true(self):
        """测试条件评估 - AND逻辑，全部满足"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.amount", "op": ">=", "value": 1000},
                {"field": "form.days", "op": "<=", "value": 7}
            ]
        }
        context = {"form": {"amount": 5000, "days": 5}}

        result = self.service._evaluate_conditions(conditions, context)
        self.assertTrue(result)

    def test_evaluate_conditions_and_partial_false(self):
        """测试条件评估 - AND逻辑，部分不满足"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form.amount", "op": ">=", "value": 1000},
                {"field": "form.days", "op": "<=", "value": 7}
            ]
        }
        context = {"form": {"amount": 5000, "days": 10}}  # days超限

        result = self.service._evaluate_conditions(conditions, context)
        self.assertFalse(result)

    def test_evaluate_conditions_or_any_true(self):
        """测试条件评估 - OR逻辑，有一个满足"""
        conditions = {
            "operator": "OR",
            "items": [
                {"field": "form.amount", "op": ">=", "value": 10000},
                {"field": "form.urgent", "op": "==", "value": True}
            ]
        }
        context = {"form": {"amount": 5000, "urgent": True}}

        result = self.service._evaluate_conditions(conditions, context)
        self.assertTrue(result)

    def test_evaluate_conditions_or_all_false(self):
        """测试条件评估 - OR逻辑，全部不满足"""
        conditions = {
            "operator": "OR",
            "items": [
                {"field": "form.amount", "op": ">=", "value": 10000},
                {"field": "form.urgent", "op": "==", "value": True}
            ]
        }
        context = {"form": {"amount": 5000, "urgent": False}}

        result = self.service._evaluate_conditions(conditions, context)
        self.assertFalse(result)

    def test_evaluate_conditions_empty_items(self):
        """测试条件评估 - 空条件列表"""
        conditions = {"operator": "AND", "items": []}
        context = {}

        result = self.service._evaluate_conditions(conditions, context)
        self.assertTrue(result)  # 空条件默认返回True

    # ========== _evaluate_single() 测试 ==========

    def test_evaluate_single_simple_equal(self):
        """测试单条件评估 - 相等"""
        condition = {"field": "form.status", "op": "==", "value": "APPROVED"}
        context = {"form": {"status": "APPROVED"}}

        result = self.service._evaluate_single(condition, context)
        self.assertTrue(result)

    def test_evaluate_single_greater_than(self):
        """测试单条件评估 - 大于"""
        condition = {"field": "form.amount", "op": ">", "value": 1000}
        context = {"form": {"amount": 5000}}

        result = self.service._evaluate_single(condition, context)
        self.assertTrue(result)

    def test_evaluate_single_field_not_found(self):
        """测试单条件评估 - 字段不存在"""
        condition = {"field": "form.nonexistent", "op": "==", "value": "test"}
        context = {"form": {"status": "APPROVED"}}

        result = self.service._evaluate_single(condition, context)
        self.assertFalse(result)  # 字段不存在，值为None，与"test"不等

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
        mock_user = Mock()
        mock_user.name = "张三"
        mock_user.dept_id = 100
        
        context = {"initiator": mock_user}
        result = self.service._get_field_value("initiator.name", context)
        self.assertEqual(result, "张三")

    def test_get_field_value_empty_path(self):
        """测试获取字段值 - 空路径"""
        context = {"amount": 1000}
        result = self.service._get_field_value("", context)
        self.assertIsNone(result)

    def test_get_field_value_not_found(self):
        """测试获取字段值 - 字段不存在"""
        context = {"form": {"amount": 1000}}
        result = self.service._get_field_value("form.invalid", context)
        self.assertIsNone(result)

    def test_get_field_value_nested_none(self):
        """测试获取字段值 - 中间值为None"""
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

    def test_compare_between(self):
        """测试比较 - between操作符"""
        self.assertTrue(self.service._compare(50, "between", [10, 100]))
        self.assertTrue(self.service._compare(10, "between", [10, 100]))
        self.assertTrue(self.service._compare(100, "between", [10, 100]))
        self.assertFalse(self.service._compare(150, "between", [10, 100]))
        self.assertFalse(self.service._compare(None, "between", [10, 100]))

    def test_compare_between_invalid_range(self):
        """测试比较 - between操作符，无效区间"""
        self.assertFalse(self.service._compare(50, "between", [10]))  # 长度不足
        self.assertFalse(self.service._compare(50, "between", "invalid"))  # 类型错误

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
        # 字符串和数字比较会抛出异常，应该捕获并返回False
        result = self.service._compare("abc", ">", 100)
        self.assertFalse(result)

    # ========== resolve_approvers() 测试 ==========

    def test_resolve_approvers_fixed_user(self):
        """测试解析审批人 - 固定用户"""
        mock_node = Mock()
        mock_node.approver_type = "FIXED_USER"
        mock_node.approver_config = {"user_ids": [1, 2, 3]}

        context = {}
        result = self.service.resolve_approvers(mock_node, context)

        self.assertEqual(result, [1, 2, 3])

    def test_resolve_approvers_fixed_user_empty(self):
        """测试解析审批人 - 固定用户（空列表）"""
        mock_node = Mock()
        mock_node.approver_type = "FIXED_USER"
        mock_node.approver_config = {}

        context = {}
        result = self.service.resolve_approvers(mock_node, context)

        self.assertEqual(result, [])

    def test_resolve_approvers_role(self):
        """测试解析审批人 - 角色"""
        mock_node = Mock()
        mock_node.approver_type = "ROLE"
        mock_node.approver_config = {"role_codes": ["MANAGER"]}

        # Mock数据库查询
        mock_users = [Mock(id=1), Mock(id=2)]
        self.mock_db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = mock_users

        context = {}
        result = self.service.resolve_approvers(mock_node, context)

        self.assertEqual(result, [1, 2])

    def test_resolve_approvers_department_head(self):
        """测试解析审批人 - 部门主管"""
        mock_node = Mock()
        mock_node.approver_type = "DEPARTMENT_HEAD"
        mock_node.approver_config = {}

        # Mock发起人
        context = {"initiator": {"dept_id": 10}}

        # Mock部门查询
        mock_dept = Mock()
        mock_dept.manager_id = 100
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_dept

        result = self.service.resolve_approvers(mock_node, context)

        self.assertEqual(result, [100])

    def test_resolve_approvers_department_head_no_manager(self):
        """测试解析审批人 - 部门主管（无主管）"""
        mock_node = Mock()
        mock_node.approver_type = "DEPARTMENT_HEAD"
        mock_node.approver_config = {}

        context = {"initiator": {"dept_id": 10}}

        # Mock部门查询 - 无主管
        mock_dept = Mock()
        mock_dept.manager_id = None
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_dept

        result = self.service.resolve_approvers(mock_node, context)

        self.assertEqual(result, [])

    def test_resolve_approvers_direct_manager(self):
        """测试解析审批人 - 直属上级"""
        mock_node = Mock()
        mock_node.approver_type = "DIRECT_MANAGER"
        mock_node.approver_config = {}

        context = {"initiator": {"id": 50}}

        # Mock用户查询
        mock_user = Mock()
        mock_user.reporting_to = 200
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = self.service.resolve_approvers(mock_node, context)

        self.assertEqual(result, [200])

    def test_resolve_approvers_direct_manager_no_manager(self):
        """测试解析审批人 - 直属上级（无上级）"""
        mock_node = Mock()
        mock_node.approver_type = "DIRECT_MANAGER"
        mock_node.approver_config = {}

        context = {"initiator": {"id": 50}}

        # Mock用户查询 - 无上级
        mock_user = Mock()
        mock_user.reporting_to = None
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = self.service.resolve_approvers(mock_node, context)

        self.assertEqual(result, [])

    def test_resolve_approvers_form_field(self):
        """测试解析审批人 - 表单字段"""
        mock_node = Mock()
        mock_node.approver_type = "FORM_FIELD"
        mock_node.approver_config = {"field_name": "approver_id"}

        context = {"form_data": {"approver_id": 123}}

        result = self.service.resolve_approvers(mock_node, context)

        self.assertEqual(result, [123])

    def test_resolve_approvers_form_field_list(self):
        """测试解析审批人 - 表单字段（列表）"""
        mock_node = Mock()
        mock_node.approver_type = "FORM_FIELD"
        mock_node.approver_config = {"field_name": "approver_ids"}

        context = {"form_data": {"approver_ids": [10, 20, 30]}}

        result = self.service.resolve_approvers(mock_node, context)

        self.assertEqual(result, [10, 20, 30])

    def test_resolve_approvers_form_field_not_found(self):
        """测试解析审批人 - 表单字段（字段不存在）"""
        mock_node = Mock()
        mock_node.approver_type = "FORM_FIELD"
        mock_node.approver_config = {"field_name": "nonexistent"}

        context = {"form_data": {"amount": 1000}}

        result = self.service.resolve_approvers(mock_node, context)

        self.assertEqual(result, [])

    def test_resolve_approvers_multi_dept(self):
        """测试解析审批人 - 多部门评估"""
        mock_node = Mock()
        mock_node.approver_type = "MULTI_DEPT"
        mock_node.approver_config = {"departments": ["研发部", "测试部"]}

        # Mock部门查询
        mock_dept1 = Mock()
        mock_dept1.manager_id = 101
        mock_dept2 = Mock()
        mock_dept2.manager_id = 102
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_dept1, mock_dept2]

        context = {}
        result = self.service.resolve_approvers(mock_node, context)

        self.assertEqual(result, [101, 102])

    def test_resolve_approvers_dynamic(self):
        """测试解析审批人 - 动态计算（通过适配器）"""
        mock_node = Mock()
        mock_node.approver_type = "DYNAMIC"
        mock_node.approver_config = {}

        # Mock适配器
        mock_adapter = Mock()
        mock_adapter.resolve_approvers.return_value = [300, 301]
        
        context = {"adapter": mock_adapter}
        result = self.service.resolve_approvers(mock_node, context)

        self.assertEqual(result, [300, 301])
        mock_adapter.resolve_approvers.assert_called_once_with(mock_node, context)

    def test_resolve_approvers_dynamic_no_adapter(self):
        """测试解析审批人 - 动态计算（无适配器）"""
        mock_node = Mock()
        mock_node.approver_type = "DYNAMIC"
        mock_node.approver_config = {}

        context = {}
        result = self.service.resolve_approvers(mock_node, context)

        self.assertEqual(result, [])

    def test_resolve_approvers_initiator(self):
        """测试解析审批人 - 发起人"""
        mock_node = Mock()
        mock_node.approver_type = "INITIATOR"
        mock_node.approver_config = {}

        context = {"initiator": {"id": 999}}
        result = self.service.resolve_approvers(mock_node, context)

        self.assertEqual(result, [999])

    def test_resolve_approvers_initiator_object(self):
        """测试解析审批人 - 发起人（对象）"""
        mock_node = Mock()
        mock_node.approver_type = "INITIATOR"
        mock_node.approver_config = {}

        mock_initiator = Mock()
        mock_initiator.get.return_value = None  # get("id") 返回None
        mock_initiator.id = 888  # 直接访问.id
        context = {"initiator": mock_initiator}
        result = self.service.resolve_approvers(mock_node, context)

        self.assertEqual(result, [888])

    def test_resolve_approvers_unknown_type(self):
        """测试解析审批人 - 未知类型"""
        mock_node = Mock()
        mock_node.approver_type = "UNKNOWN"
        mock_node.approver_config = {}

        context = {}
        result = self.service.resolve_approvers(mock_node, context)

        self.assertEqual(result, [])

    # ========== _resolve_role_approvers() 测试 ==========

    def test_resolve_role_approvers_single_role(self):
        """测试解析角色审批人 - 单个角色"""
        config = {"role_codes": "MANAGER"}
        context = {}

        # Mock数据库查询
        mock_users = [Mock(id=1), Mock(id=2)]
        self.mock_db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = mock_users

        result = self.service._resolve_role_approvers(config, context)

        self.assertEqual(result, [1, 2])

    def test_resolve_role_approvers_multiple_roles(self):
        """测试解析角色审批人 - 多个角色"""
        config = {"role_codes": ["MANAGER", "DIRECTOR"]}
        context = {}

        # Mock数据库查询
        mock_users = [Mock(id=1), Mock(id=2), Mock(id=3)]
        self.mock_db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = mock_users

        result = self.service._resolve_role_approvers(config, context)

        self.assertEqual(result, [1, 2, 3])

    def test_resolve_role_approvers_empty(self):
        """测试解析角色审批人 - 无角色"""
        config = {}
        context = {}

        result = self.service._resolve_role_approvers(config, context)

        self.assertEqual(result, [])

    # ========== _resolve_department_head() 测试 ==========

    def test_resolve_department_head_with_dict_initiator(self):
        """测试解析部门主管 - 字典形式的发起人"""
        context = {"initiator": {"dept_id": 10}}

        mock_dept = Mock()
        mock_dept.manager_id = 100
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_dept

        result = self.service._resolve_department_head(context)

        self.assertEqual(result, [100])

    def test_resolve_department_head_with_object_initiator(self):
        """测试解析部门主管 - 对象形式的发起人"""
        mock_initiator = Mock()
        mock_initiator.dept_id = 10
        context = {"initiator": mock_initiator}

        mock_dept = Mock()
        mock_dept.manager_id = 100
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_dept

        result = self.service._resolve_department_head(context)

        self.assertEqual(result, [100])

    def test_resolve_department_head_no_dept(self):
        """测试解析部门主管 - 无部门"""
        context = {"initiator": {}}

        result = self.service._resolve_department_head(context)

        self.assertEqual(result, [])

    # ========== _resolve_direct_manager() 测试 ==========

    def test_resolve_direct_manager_with_dict_initiator(self):
        """测试解析直属上级 - 字典形式的发起人"""
        context = {"initiator": {"id": 50}}

        mock_user = Mock()
        mock_user.reporting_to = 200
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = self.service._resolve_direct_manager(context)

        self.assertEqual(result, [200])

    def test_resolve_direct_manager_with_object_initiator(self):
        """测试解析直属上级 - 对象形式的发起人"""
        mock_initiator = Mock()
        mock_initiator.id = 50
        context = {"initiator": mock_initiator}

        mock_user = Mock()
        mock_user.reporting_to = 200
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = self.service._resolve_direct_manager(context)

        self.assertEqual(result, [200])

    def test_resolve_direct_manager_no_user_id(self):
        """测试解析直属上级 - 无用户ID"""
        context = {"initiator": {}}

        result = self.service._resolve_direct_manager(context)

        self.assertEqual(result, [])

    # ========== _resolve_multi_dept_approvers() 测试 ==========

    def test_resolve_multi_dept_approvers_success(self):
        """测试解析多部门审批人 - 成功"""
        config = {"departments": ["研发部", "测试部", "产品部"]}
        context = {}

        # Mock部门查询
        mock_dept1 = Mock()
        mock_dept1.manager_id = 101
        mock_dept2 = Mock()
        mock_dept2.manager_id = 102
        mock_dept3 = Mock()
        mock_dept3.manager_id = None  # 无主管
        self.mock_db.query.return_value.filter.return_value.all.return_value = [mock_dept1, mock_dept2, mock_dept3]

        result = self.service._resolve_multi_dept_approvers(config, context)

        self.assertEqual(result, [101, 102])  # 只包含有主管的部门

    def test_resolve_multi_dept_approvers_empty(self):
        """测试解析多部门审批人 - 无部门"""
        config = {}
        context = {}

        result = self.service._resolve_multi_dept_approvers(config, context)

        self.assertEqual(result, [])

    # ========== get_next_nodes() 测试 ==========

    def test_get_next_nodes_normal(self):
        """测试获取下一节点 - 普通节点"""
        mock_current_node = Mock()
        mock_current_node.flow_id = 1
        mock_current_node.node_order = 1

        # Mock下一节点
        mock_next_node = Mock()
        mock_next_node.node_type = "APPROVAL"
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_next_node]

        context = {}
        result = self.service.get_next_nodes(mock_current_node, context)

        self.assertEqual(result, [mock_next_node])

    def test_get_next_nodes_condition_branch(self):
        """测试获取下一节点 - 条件分支节点"""
        mock_current_node = Mock()
        mock_current_node.flow_id = 1
        mock_current_node.node_order = 1

        # Mock条件节点
        mock_condition_node = Mock()
        mock_condition_node.node_type = "CONDITION"
        mock_condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {"operator": "AND", "items": [{"field": "form.amount", "op": ">=", "value": 1000}]},
                    "target_node_id": 100
                }
            ],
            "default_node_id": 200
        }

        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_condition_node]

        # Mock目标节点
        mock_target_node = Mock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_target_node

        context = {"form": {"amount": 5000}}
        result = self.service.get_next_nodes(mock_current_node, context)

        self.assertEqual(result, [mock_target_node])

    def test_get_next_nodes_no_next(self):
        """测试获取下一节点 - 无后续节点"""
        mock_current_node = Mock()
        mock_current_node.flow_id = 1
        mock_current_node.node_order = 10

        self.mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

        context = {}
        result = self.service.get_next_nodes(mock_current_node, context)

        self.assertEqual(result, [])

    # ========== _resolve_condition_branch() 测试 ==========

    def test_resolve_condition_branch_matching(self):
        """测试解析条件分支 - 匹配条件"""
        mock_condition_node = Mock()
        mock_condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {"operator": "AND", "items": [{"field": "form.amount", "op": ">=", "value": 1000}]},
                    "target_node_id": 100
                },
                {
                    "conditions": {"operator": "AND", "items": [{"field": "form.amount", "op": "<", "value": 1000}]},
                    "target_node_id": 200
                }
            ],
            "default_node_id": 300
        }

        # Mock目标节点
        mock_target_node = Mock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_target_node

        context = {"form": {"amount": 5000}}
        result = self.service._resolve_condition_branch(mock_condition_node, context)

        self.assertEqual(result, [mock_target_node])

    def test_resolve_condition_branch_default(self):
        """测试解析条件分支 - 使用默认分支"""
        mock_condition_node = Mock()
        mock_condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {"operator": "AND", "items": [{"field": "form.amount", "op": ">=", "value": 10000}]},
                    "target_node_id": 100
                }
            ],
            "default_node_id": 300
        }

        # Mock默认节点
        mock_default_node = Mock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_default_node

        context = {"form": {"amount": 500}}  # 不满足任何条件
        result = self.service._resolve_condition_branch(mock_condition_node, context)

        self.assertEqual(result, [mock_default_node])

    def test_resolve_condition_branch_no_match_no_default(self):
        """测试解析条件分支 - 无匹配且无默认"""
        mock_condition_node = Mock()
        mock_condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {"operator": "AND", "items": [{"field": "form.amount", "op": ">=", "value": 10000}]},
                    "target_node_id": 100
                }
            ]
        }

        context = {"form": {"amount": 500}}
        result = self.service._resolve_condition_branch(mock_condition_node, context)

        self.assertEqual(result, [])

    def test_resolve_condition_branch_empty_branches(self):
        """测试解析条件分支 - 空分支配置"""
        mock_condition_node = Mock()
        mock_condition_node.approver_config = {}

        context = {"form": {"amount": 500}}
        result = self.service._resolve_condition_branch(mock_condition_node, context)

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
