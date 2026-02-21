# -*- coding: utf-8 -*-
"""
审批路由决策服务增强测试

测试 app/services/approval_engine/router.py 的所有核心方法
目标覆盖率: 70%+
"""

import re
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.approval_engine.router import ApprovalRouterService


@pytest.fixture
def mock_db():
    """Mock 数据库会话"""
    return MagicMock()


@pytest.fixture
def router_service(mock_db):
    """创建路由服务实例"""
    return ApprovalRouterService(mock_db)


@pytest.fixture
def sample_context():
    """创建示例上下文数据"""
    return {
        "form_data": {
            "leave_days": 2,
            "amount": 50000,
            "department": "engineering",
            "reason": "项目需求",
            "approver_id": 100,
        },
        "initiator": {
            "id": 1,
            "dept_id": 10,
            "reporting_to": 20,
            "name": "张三",
        },
        "entity": {
            "id": 101,
            "gross_margin": 0.25,
            "total_amount": 100000,
        },
    }


@pytest.fixture
def mock_node():
    """创建Mock节点"""
    node = MagicMock()
    node.id = 1
    node.flow_id = 100
    node.node_order = 1
    node.node_type = "APPROVAL"
    node.approver_type = "FIXED_USER"
    node.approver_config = {"user_ids": [1, 2, 3]}
    node.is_active = True
    return node


@pytest.mark.unit
class TestSelectFlow:
    """测试 select_flow 方法"""

    def test_select_flow_with_matching_rule(self, router_service, mock_db, sample_context):
        """测试有匹配规则时选择流程"""
        # 创建mock规则和流程
        mock_rule = MagicMock()
        mock_rule.conditions = {
            "operator": "AND",
            "items": [{"field": "form_data.amount", "op": ">=", "value": 10000}]
        }
        mock_flow = MagicMock()
        mock_flow.id = 100
        mock_flow.flow_name = "大额审批流程"
        mock_rule.flow = mock_flow

        # Mock 数据库查询返回规则列表
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_rule]
        mock_db.query.return_value = mock_query

        result = router_service.select_flow(template_id=1, context=sample_context)

        assert result == mock_flow
        mock_db.query.assert_called()

    def test_select_flow_no_matching_rule_returns_default(self, router_service, mock_db, sample_context):
        """测试无匹配规则时返回默认流程"""
        # Mock 查询返回空规则列表
        mock_query_rules = MagicMock()
        mock_query_rules.filter.return_value.order_by.return_value.all.return_value = []

        # Mock 默认流程
        mock_default_flow = MagicMock()
        mock_default_flow.id = 200
        mock_default_flow.flow_name = "默认流程"
        mock_query_default = MagicMock()
        mock_query_default.filter.return_value.first.return_value = mock_default_flow

        # 设置query的多次调用返回不同结果
        mock_db.query.side_effect = [mock_query_rules, mock_query_default]

        result = router_service.select_flow(template_id=1, context=sample_context)

        assert result == mock_default_flow

    def test_select_flow_multiple_rules_priority(self, router_service, mock_db, sample_context):
        """测试多条规则时按优先级匹配"""
        # 创建两条规则
        mock_rule1 = MagicMock()
        mock_rule1.conditions = {"operator": "AND", "items": [{"field": "form_data.amount", "op": ">", "value": 100000}]}
        mock_rule1.flow = MagicMock(id=101, flow_name="高额流程")

        mock_rule2 = MagicMock()
        mock_rule2.conditions = {"operator": "AND", "items": [{"field": "form_data.amount", "op": ">=", "value": 10000}]}
        mock_rule2.flow = MagicMock(id=102, flow_name="中额流程")

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [mock_rule1, mock_rule2]
        mock_db.query.return_value = mock_query

        result = router_service.select_flow(template_id=1, context=sample_context)

        # amount=50000，不匹配rule1(>100000)，应该匹配rule2(>=10000)
        assert result == mock_rule2.flow


@pytest.mark.unit
class TestGetDefaultFlow:
    """测试 _get_default_flow 方法"""

    def test_get_default_flow_exists(self, router_service, mock_db):
        """测试获取存在的默认流程"""
        mock_flow = MagicMock()
        mock_flow.id = 1
        mock_flow.is_default = True

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_flow
        mock_db.query.return_value = mock_query

        result = router_service._get_default_flow(template_id=1)

        assert result == mock_flow

    def test_get_default_flow_not_exists(self, router_service, mock_db):
        """测试默认流程不存在时返回None"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = router_service._get_default_flow(template_id=999)

        assert result is None


@pytest.mark.unit
class TestEvaluateConditions:
    """测试 _evaluate_conditions 方法"""

    def test_evaluate_conditions_empty_items(self, router_service, sample_context):
        """测试空条件项返回True"""
        conditions = {"operator": "AND", "items": []}
        result = router_service._evaluate_conditions(conditions, sample_context)
        assert result is True

    def test_evaluate_conditions_and_all_true(self, router_service, sample_context):
        """测试AND操作符所有条件为真"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form_data.amount", "op": ">=", "value": 10000},
                {"field": "form_data.department", "op": "==", "value": "engineering"},
            ]
        }
        result = router_service._evaluate_conditions(conditions, sample_context)
        assert result is True

    def test_evaluate_conditions_and_partial_false(self, router_service, sample_context):
        """测试AND操作符部分条件为假"""
        conditions = {
            "operator": "AND",
            "items": [
                {"field": "form_data.amount", "op": ">", "value": 100000},  # False
                {"field": "form_data.department", "op": "==", "value": "engineering"},  # True
            ]
        }
        result = router_service._evaluate_conditions(conditions, sample_context)
        assert result is False

    def test_evaluate_conditions_or_any_true(self, router_service, sample_context):
        """测试OR操作符任一条件为真"""
        conditions = {
            "operator": "OR",
            "items": [
                {"field": "form_data.amount", "op": ">", "value": 100000},  # False
                {"field": "form_data.department", "op": "==", "value": "engineering"},  # True
            ]
        }
        result = router_service._evaluate_conditions(conditions, sample_context)
        assert result is True

    def test_evaluate_conditions_or_all_false(self, router_service, sample_context):
        """测试OR操作符所有条件为假"""
        conditions = {
            "operator": "OR",
            "items": [
                {"field": "form_data.amount", "op": ">", "value": 100000},  # False
                {"field": "form_data.department", "op": "==", "value": "sales"},  # False
            ]
        }
        result = router_service._evaluate_conditions(conditions, sample_context)
        assert result is False


@pytest.mark.unit
class TestEvaluateSingle:
    """测试 _evaluate_single 方法"""

    def test_evaluate_single_simple_equal(self, router_service, sample_context):
        """测试简单相等条件"""
        condition = {"field": "form_data.leave_days", "op": "==", "value": 2}
        result = router_service._evaluate_single(condition, sample_context)
        assert result is True

    def test_evaluate_single_not_equal(self, router_service, sample_context):
        """测试不等条件"""
        condition = {"field": "form_data.leave_days", "op": "!=", "value": 5}
        result = router_service._evaluate_single(condition, sample_context)
        assert result is True

    def test_evaluate_single_missing_field(self, router_service, sample_context):
        """测试缺失字段返回False"""
        condition = {"field": "form_data.nonexistent", "op": "==", "value": "test"}
        result = router_service._evaluate_single(condition, sample_context)
        assert result is False


@pytest.mark.unit
class TestGetFieldValue:
    """测试 _get_field_value 方法"""

    def test_get_field_value_nested_dict(self, router_service, sample_context):
        """测试获取嵌套字典值"""
        result = router_service._get_field_value("form_data.amount", sample_context)
        assert result == 50000

    def test_get_field_value_nested_object(self, router_service):
        """测试获取嵌套对象属性"""
        mock_obj = MagicMock()
        mock_obj.user = MagicMock()
        mock_obj.user.name = "Alice"
        context = {"initiator": mock_obj}

        result = router_service._get_field_value("initiator.user.name", context)
        assert result == "Alice"

    def test_get_field_value_top_level(self, router_service, sample_context):
        """测试获取顶级字段"""
        result = router_service._get_field_value("form_data", sample_context)
        assert result == sample_context["form_data"]

    def test_get_field_value_missing_path(self, router_service, sample_context):
        """测试缺失路径返回None"""
        result = router_service._get_field_value("form_data.nonexistent.field", sample_context)
        assert result is None

    def test_get_field_value_empty_path(self, router_service, sample_context):
        """测试空路径返回None"""
        result = router_service._get_field_value("", sample_context)
        assert result is None

    def test_get_field_value_none_intermediate(self, router_service):
        """测试中间值为None时返回None"""
        context = {"form_data": {"nested": None}}
        result = router_service._get_field_value("form_data.nested.field", context)
        assert result is None


@pytest.mark.unit
class TestCompare:
    """测试 _compare 方法 - 所有比较操作符"""

    def test_compare_equal(self, router_service):
        """测试相等操作符"""
        assert router_service._compare(10, "==", 10) is True
        assert router_service._compare("test", "==", "test") is True
        assert router_service._compare(10, "==", 20) is False

    def test_compare_not_equal(self, router_service):
        """测试不等操作符"""
        assert router_service._compare(10, "!=", 20) is True
        assert router_service._compare(10, "!=", 10) is False

    def test_compare_greater_than(self, router_service):
        """测试大于操作符"""
        assert router_service._compare(20, ">", 10) is True
        assert router_service._compare(10, ">", 20) is False
        assert router_service._compare(None, ">", 10) is False

    def test_compare_greater_equal(self, router_service):
        """测试大于等于操作符"""
        assert router_service._compare(20, ">=", 10) is True
        assert router_service._compare(10, ">=", 10) is True
        assert router_service._compare(5, ">=", 10) is False

    def test_compare_less_than(self, router_service):
        """测试小于操作符"""
        assert router_service._compare(5, "<", 10) is True
        assert router_service._compare(20, "<", 10) is False

    def test_compare_less_equal(self, router_service):
        """测试小于等于操作符"""
        assert router_service._compare(5, "<=", 10) is True
        assert router_service._compare(10, "<=", 10) is True
        assert router_service._compare(15, "<=", 10) is False

    def test_compare_in_list(self, router_service):
        """测试in操作符"""
        assert router_service._compare("A", "in", ["A", "B", "C"]) is True
        assert router_service._compare("D", "in", ["A", "B", "C"]) is False
        assert router_service._compare("X", "in", []) is False

    def test_compare_not_in_list(self, router_service):
        """测试not_in操作符"""
        assert router_service._compare("D", "not_in", ["A", "B", "C"]) is True
        assert router_service._compare("A", "not_in", ["A", "B", "C"]) is False
        assert router_service._compare("X", "not_in", []) is True

    def test_compare_between(self, router_service):
        """测试between操作符"""
        assert router_service._compare(15, "between", [10, 20]) is True
        assert router_service._compare(10, "between", [10, 20]) is True
        assert router_service._compare(20, "between", [10, 20]) is True
        assert router_service._compare(5, "between", [10, 20]) is False
        assert router_service._compare(None, "between", [10, 20]) is False
        assert router_service._compare(15, "between", [10]) is False  # 无效范围

    def test_compare_contains(self, router_service):
        """测试contains操作符"""
        assert router_service._compare("hello world", "contains", "world") is True
        assert router_service._compare("hello", "contains", "xyz") is False
        assert router_service._compare(None, "contains", "test") is False

    def test_compare_starts_with(self, router_service):
        """测试starts_with操作符"""
        assert router_service._compare("hello world", "starts_with", "hello") is True
        assert router_service._compare("hello world", "starts_with", "world") is False
        assert router_service._compare(None, "starts_with", "test") is False

    def test_compare_ends_with(self, router_service):
        """测试ends_with操作符"""
        assert router_service._compare("hello world", "ends_with", "world") is True
        assert router_service._compare("hello world", "ends_with", "hello") is False
        assert router_service._compare(None, "ends_with", "test") is False

    def test_compare_is_null(self, router_service):
        """测试is_null操作符"""
        assert router_service._compare(None, "is_null", True) is True
        assert router_service._compare("value", "is_null", False) is True
        assert router_service._compare(None, "is_null", False) is False

    def test_compare_regex(self, router_service):
        """测试regex操作符"""
        assert router_service._compare("test123", "regex", r"^test\d+$") is True
        assert router_service._compare("test", "regex", r"^test\d+$") is False
        assert router_service._compare(None, "regex", r"^test$") is False

    def test_compare_invalid_operator(self, router_service):
        """测试无效操作符返回False"""
        assert router_service._compare(10, "invalid_op", 10) is False

    def test_compare_type_error_handling(self, router_service):
        """测试类型错误处理"""
        # 比较不兼容类型时应返回False而不是抛出异常
        assert router_service._compare("string", ">", 10) is False


@pytest.mark.unit
class TestResolveApprovers:
    """测试 resolve_approvers 方法"""

    def test_resolve_approvers_fixed_user(self, router_service, mock_node, sample_context):
        """测试固定用户类型"""
        mock_node.approver_type = "FIXED_USER"
        mock_node.approver_config = {"user_ids": [1, 2, 3]}

        result = router_service.resolve_approvers(mock_node, sample_context)

        assert result == [1, 2, 3]

    def test_resolve_approvers_form_field_single(self, router_service, mock_node, sample_context):
        """测试表单字段类型 - 单个用户"""
        mock_node.approver_type = "FORM_FIELD"
        mock_node.approver_config = {"field_name": "approver_id"}

        result = router_service.resolve_approvers(mock_node, sample_context)

        assert result == [100]

    def test_resolve_approvers_form_field_list(self, router_service, mock_node, sample_context):
        """测试表单字段类型 - 多个用户"""
        sample_context["form_data"]["approver_ids"] = [10, 20, 30]
        mock_node.approver_type = "FORM_FIELD"
        mock_node.approver_config = {"field_name": "approver_ids"}

        result = router_service.resolve_approvers(mock_node, sample_context)

        assert result == [10, 20, 30]

    def test_resolve_approvers_form_field_missing(self, router_service, mock_node, sample_context):
        """测试表单字段缺失时返回空列表"""
        mock_node.approver_type = "FORM_FIELD"
        mock_node.approver_config = {"field_name": "nonexistent_field"}

        result = router_service.resolve_approvers(mock_node, sample_context)

        assert result == []

    def test_resolve_approvers_initiator(self, router_service, mock_node, sample_context):
        """测试发起人类型"""
        mock_node.approver_type = "INITIATOR"
        mock_node.approver_config = {}

        result = router_service.resolve_approvers(mock_node, sample_context)

        assert result == [1]

    def test_resolve_approvers_initiator_none(self, router_service, mock_node):
        """测试发起人类型 - 空上下文"""
        context = {}

        mock_node.approver_type = "INITIATOR"
        mock_node.approver_config = {}

        result = router_service.resolve_approvers(mock_node, context)

        assert result == []

    def test_resolve_approvers_dynamic_with_adapter(self, router_service, mock_node, sample_context):
        """测试动态类型使用适配器"""
        mock_adapter = MagicMock()
        mock_adapter.resolve_approvers.return_value = [100, 200]
        sample_context["adapter"] = mock_adapter

        mock_node.approver_type = "DYNAMIC"
        mock_node.approver_config = {}

        result = router_service.resolve_approvers(mock_node, sample_context)

        assert result == [100, 200]
        mock_adapter.resolve_approvers.assert_called_once_with(mock_node, sample_context)

    def test_resolve_approvers_dynamic_no_adapter(self, router_service, mock_node, sample_context):
        """测试动态类型无适配器时返回空列表"""
        mock_node.approver_type = "DYNAMIC"
        mock_node.approver_config = {}

        result = router_service.resolve_approvers(mock_node, sample_context)

        assert result == []

    def test_resolve_approvers_unknown_type(self, router_service, mock_node, sample_context):
        """测试未知类型返回空列表"""
        mock_node.approver_type = "UNKNOWN_TYPE"
        mock_node.approver_config = {}

        result = router_service.resolve_approvers(mock_node, sample_context)

        assert result == []


@pytest.mark.unit
class TestResolveRoleApprovers:
    """测试 _resolve_role_approvers 方法"""

    def test_resolve_role_approvers_single_role(self, router_service, mock_db, sample_context):
        """测试单个角色解析"""
        config = {"role_codes": ["SALES_MANAGER"]}

        # Mock 查询结果
        mock_user1 = MagicMock()
        mock_user1.id = 10
        mock_user2 = MagicMock()
        mock_user2.id = 20

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value.all.return_value = [mock_user1, mock_user2]
        mock_db.query.return_value = mock_query

        result = router_service._resolve_role_approvers(config, sample_context)

        assert result == [10, 20]

    def test_resolve_role_approvers_multiple_roles(self, router_service, mock_db, sample_context):
        """测试多个角色解析"""
        config = {"role_codes": ["SALES_MANAGER", "DEPT_HEAD"]}

        mock_user1 = MagicMock()
        mock_user1.id = 10

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value.all.return_value = [mock_user1]
        mock_db.query.return_value = mock_query

        result = router_service._resolve_role_approvers(config, sample_context)

        assert result == [10]

    def test_resolve_role_approvers_string_role(self, router_service, mock_db, sample_context):
        """测试字符串形式的角色代码"""
        config = {"role_codes": "SALES_MANAGER"}

        mock_query = MagicMock()
        mock_query.join.return_value = mock_query
        mock_query.filter.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = router_service._resolve_role_approvers(config, sample_context)

        assert result == []

    def test_resolve_role_approvers_empty_config(self, router_service, mock_db, sample_context):
        """测试空配置返回空列表"""
        config = {}

        result = router_service._resolve_role_approvers(config, sample_context)

        assert result == []


@pytest.mark.unit
class TestResolveDepartmentHead:
    """测试 _resolve_department_head 方法"""

    def test_resolve_department_head_dict_initiator(self, router_service, mock_db, sample_context):
        """测试字典形式的发起人"""
        mock_dept = MagicMock()
        mock_dept.manager_id = 50

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_dept
        mock_db.query.return_value = mock_query

        result = router_service._resolve_department_head(sample_context)

        assert result == [50]

    def test_resolve_department_head_object_initiator(self, router_service, mock_db):
        """测试对象形式的发起人"""
        initiator = MagicMock()
        initiator.dept_id = 10
        context = {"initiator": initiator}

        mock_dept = MagicMock()
        mock_dept.manager_id = 60

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_dept
        mock_db.query.return_value = mock_query

        result = router_service._resolve_department_head(context)

        assert result == [60]

    def test_resolve_department_head_no_dept_id(self, router_service, mock_db):
        """测试无部门ID时返回空列表"""
        context = {"initiator": {}}

        result = router_service._resolve_department_head(context)

        assert result == []

    def test_resolve_department_head_no_manager(self, router_service, mock_db, sample_context):
        """测试部门无主管时返回空列表"""
        mock_dept = MagicMock()
        mock_dept.manager_id = None

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_dept
        mock_db.query.return_value = mock_query

        result = router_service._resolve_department_head(sample_context)

        assert result == []

    def test_resolve_department_head_dept_not_found(self, router_service, mock_db, sample_context):
        """测试部门不存在时返回空列表"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = router_service._resolve_department_head(sample_context)

        assert result == []


@pytest.mark.unit
class TestResolveDirectManager:
    """测试 _resolve_direct_manager 方法"""

    def test_resolve_direct_manager_dict_initiator(self, router_service, mock_db, sample_context):
        """测试字典形式的发起人"""
        mock_user = MagicMock()
        mock_user.reporting_to = 20

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query

        result = router_service._resolve_direct_manager(sample_context)

        assert result == [20]

    def test_resolve_direct_manager_object_initiator(self, router_service, mock_db):
        """测试对象形式的发起人"""
        initiator = MagicMock()
        initiator.id = 5
        context = {"initiator": initiator}

        mock_user = MagicMock()
        mock_user.reporting_to = 30

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query

        result = router_service._resolve_direct_manager(context)

        assert result == [30]

    def test_resolve_direct_manager_no_user_id(self, router_service, mock_db):
        """测试无用户ID时返回空列表"""
        context = {"initiator": {}}

        result = router_service._resolve_direct_manager(context)

        assert result == []

    def test_resolve_direct_manager_no_reporting_to(self, router_service, mock_db, sample_context):
        """测试无上级时返回空列表"""
        mock_user = MagicMock()
        mock_user.reporting_to = None

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_user
        mock_db.query.return_value = mock_query

        result = router_service._resolve_direct_manager(sample_context)

        assert result == []


@pytest.mark.unit
class TestResolveMultiDeptApprovers:
    """测试 _resolve_multi_dept_approvers 方法"""

    def test_resolve_multi_dept_approvers_multiple_depts(self, router_service, mock_db, sample_context):
        """测试多个部门审批人"""
        config = {"departments": ["工程部", "采购部", "质量部"]}

        mock_dept1 = MagicMock()
        mock_dept1.manager_id = 100
        mock_dept2 = MagicMock()
        mock_dept2.manager_id = 200
        mock_dept3 = MagicMock()
        mock_dept3.manager_id = None  # 无主管

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = [mock_dept1, mock_dept2, mock_dept3]
        mock_db.query.return_value = mock_query

        result = router_service._resolve_multi_dept_approvers(config, sample_context)

        assert result == [100, 200]

    def test_resolve_multi_dept_approvers_empty_config(self, router_service, mock_db, sample_context):
        """测试空配置返回空列表"""
        config = {}

        result = router_service._resolve_multi_dept_approvers(config, sample_context)

        assert result == []


@pytest.mark.unit
class TestGetNextNodes:
    """测试 get_next_nodes 方法"""

    def test_get_next_nodes_normal_flow(self, router_service, mock_db, mock_node, sample_context):
        """测试正常获取下一个节点"""
        current_node = mock_node
        current_node.flow_id = 100
        current_node.node_order = 1

        next_node = MagicMock()
        next_node.id = 2
        next_node.node_type = "APPROVAL"
        next_node.node_order = 2

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = [next_node]
        mock_db.query.return_value = mock_query

        result = router_service.get_next_nodes(current_node, sample_context)

        assert result == [next_node]

    def test_get_next_nodes_no_next(self, router_service, mock_db, mock_node, sample_context):
        """测试无下一个节点时返回空列表"""
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = router_service.get_next_nodes(mock_node, sample_context)

        assert result == []

    def test_get_next_nodes_condition_node(self, router_service, mock_db, mock_node, sample_context):
        """测试下一个节点为条件分支节点"""
        condition_node = MagicMock()
        condition_node.id = 2
        condition_node.node_type = "CONDITION"
        condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {"operator": "AND", "items": [{"field": "form_data.amount", "op": ">=", "value": 10000}]},
                    "target_node_id": 10
                }
            ],
            "default_node_id": 20
        }

        target_node = MagicMock()
        target_node.id = 10

        # Mock 查询：第一次返回条件节点，第二次返回目标节点
        mock_query1 = MagicMock()
        mock_query1.filter.return_value.order_by.return_value.all.return_value = [condition_node]

        mock_query2 = MagicMock()
        mock_query2.filter.return_value.first.return_value = target_node

        mock_db.query.side_effect = [mock_query1, mock_query2]

        result = router_service.get_next_nodes(mock_node, sample_context)

        assert result == [target_node]


@pytest.mark.unit
class TestResolveConditionBranch:
    """测试 _resolve_condition_branch 方法"""

    def test_resolve_condition_branch_matching(self, router_service, mock_db, sample_context):
        """测试匹配条件分支"""
        condition_node = MagicMock()
        condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {"operator": "AND", "items": [{"field": "form_data.amount", "op": ">=", "value": 10000}]},
                    "target_node_id": 100
                }
            ]
        }

        target_node = MagicMock()
        target_node.id = 100

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = target_node
        mock_db.query.return_value = mock_query

        result = router_service._resolve_condition_branch(condition_node, sample_context)

        assert result == [target_node]

    def test_resolve_condition_branch_default(self, router_service, mock_db, sample_context):
        """测试使用默认分支"""
        condition_node = MagicMock()
        condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {"operator": "AND", "items": [{"field": "form_data.amount", "op": ">", "value": 100000}]},
                    "target_node_id": 100
                }
            ],
            "default_node_id": 200
        }

        default_node = MagicMock()
        default_node.id = 200

        # 条件不匹配（50000 > 100000为False），直接查询默认节点
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = default_node
        mock_db.query.return_value = mock_query

        result = router_service._resolve_condition_branch(condition_node, sample_context)

        assert result == [default_node]

    def test_resolve_condition_branch_no_match_no_default(self, router_service, mock_db, sample_context):
        """测试无匹配且无默认分支时返回空列表"""
        condition_node = MagicMock()
        condition_node.approver_config = {
            "branches": [
                {
                    "conditions": {"operator": "AND", "items": [{"field": "form_data.amount", "op": ">", "value": 100000}]},
                    "target_node_id": 100
                }
            ]
        }

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        result = router_service._resolve_condition_branch(condition_node, sample_context)

        assert result == []

    def test_resolve_condition_branch_empty_branches(self, router_service, mock_db, sample_context):
        """测试空分支配置"""
        condition_node = MagicMock()
        condition_node.approver_config = {"branches": []}

        result = router_service._resolve_condition_branch(condition_node, sample_context)

        assert result == []


@pytest.mark.unit
class TestEdgeCases:
    """测试边界情况和异常处理"""

    def test_resolve_approvers_role_type(self, router_service, mock_db, mock_node, sample_context):
        """测试ROLE类型审批人解析"""
        mock_node.approver_type = "ROLE"
        mock_node.approver_config = {"role_codes": ["MANAGER"]}

        with patch.object(router_service, '_resolve_role_approvers', return_value=[10, 20]):
            result = router_service.resolve_approvers(mock_node, sample_context)
            assert result == [10, 20]

    def test_resolve_approvers_department_head_type(self, router_service, mock_db, mock_node, sample_context):
        """测试DEPARTMENT_HEAD类型审批人解析"""
        mock_node.approver_type = "DEPARTMENT_HEAD"
        mock_node.approver_config = {}

        with patch.object(router_service, '_resolve_department_head', return_value=[50]):
            result = router_service.resolve_approvers(mock_node, sample_context)
            assert result == [50]

    def test_resolve_approvers_direct_manager_type(self, router_service, mock_db, mock_node, sample_context):
        """测试DIRECT_MANAGER类型审批人解析"""
        mock_node.approver_type = "DIRECT_MANAGER"
        mock_node.approver_config = {}

        with patch.object(router_service, '_resolve_direct_manager', return_value=[30]):
            result = router_service.resolve_approvers(mock_node, sample_context)
            assert result == [30]

    def test_resolve_approvers_multi_dept_type(self, router_service, mock_db, mock_node, sample_context):
        """测试MULTI_DEPT类型审批人解析"""
        mock_node.approver_type = "MULTI_DEPT"
        mock_node.approver_config = {"departments": ["工程部", "采购部"]}

        with patch.object(router_service, '_resolve_multi_dept_approvers', return_value=[100, 200]):
            result = router_service.resolve_approvers(mock_node, sample_context)
            assert result == [100, 200]

    def test_compare_with_numeric_strings(self, router_service):
        """测试数字字符串比较"""
        # contains 会将值转为字符串
        assert router_service._compare(12345, "contains", "23") is True

    def test_get_field_value_with_numeric_key(self, router_service):
        """测试数字键的字段访问"""
        context = {"data": {"0": "value"}}
        # 因为split会产生字符串"0"，所以可以正常访问
        result = router_service._get_field_value("data.0", context)
        assert result == "value"
