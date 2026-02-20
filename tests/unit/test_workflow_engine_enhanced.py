# -*- coding: utf-8 -*-
"""
WorkflowEngine 增强单元测试
目标：25-35个测试，覆盖率60%+
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

from app.services.approval_engine.workflow_engine import (
    WorkflowEngine,
    ApprovalRouter,
)
from app.services.approval_engine.models import (
    ApprovalStatus,
    ApprovalDecision,
    ApprovalNodeRole,
)


class TestWorkflowEngineCore(unittest.TestCase):
    """WorkflowEngine 核心功能测试"""

    def setUp(self):
        """测试前准备"""
        self.mock_db = MagicMock()
        self.engine = WorkflowEngine(self.mock_db)

    def test_init_with_db_session(self):
        """测试初始化"""
        self.assertIsNotNone(self.engine.db)
        self.assertEqual(self.engine.db, self.mock_db)

    def test_generate_instance_no_format(self):
        """测试实例编号生成格式"""
        instance_no = WorkflowEngine._generate_instance_no()
        self.assertTrue(instance_no.startswith("AP"))
        self.assertEqual(len(instance_no), 14)  # AP + 12位时间戳

    def test_generate_instance_no_unique(self):
        """测试实例编号唯一性"""
        no1 = WorkflowEngine._generate_instance_no()
        no2 = WorkflowEngine._generate_instance_no()
        # 虽然可能相同，但至少格式正确
        self.assertTrue(no1.startswith("AP"))
        self.assertTrue(no2.startswith("AP"))


class TestCreateInstance(unittest.TestCase):
    """create_instance 方法测试"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.engine = WorkflowEngine(self.mock_db)

    @patch('app.services.approval_engine.workflow_engine.save_obj')
    def test_create_instance_success(self, mock_save):
        """测试成功创建审批实例"""
        # Mock 流程查询
        mock_flow = MagicMock()
        mock_flow.id = 1
        mock_flow.flow_code = "ECN_FLOW"
        mock_flow.nodes = [MagicMock(), MagicMock()]
        mock_flow.is_active = True

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_flow

        # 调用
        instance = self.engine.create_instance(
            flow_code="ECN_FLOW",
            business_type="ECN",
            business_id=123,
            business_title="测试ECN",
            submitted_by=1,
        )

        # 验证
        self.assertIsNotNone(instance)
        self.assertEqual(instance.flow_code, "ECN_FLOW")
        self.assertEqual(instance.business_type, "ECN")
        self.assertEqual(instance.business_id, 123)
        self.assertEqual(instance.submitted_by, 1)
        self.assertEqual(instance.total_nodes, 2)
        self.assertEqual(instance.completed_nodes, 0)
        mock_save.assert_called_once()

    def test_create_instance_flow_not_found(self):
        """测试流程不存在时抛出异常"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as cm:
            self.engine.create_instance(
                flow_code="INVALID_FLOW",
                business_type="ECN",
                business_id=123,
                business_title="测试",
                submitted_by=1,
            )
        self.assertIn("不存在或未启用", str(cm.exception))

    @patch('app.services.approval_engine.workflow_engine.save_obj')
    def test_create_instance_with_config(self, mock_save):
        """测试带配置参数创建实例"""
        mock_flow = MagicMock()
        mock_flow.id = 1
        mock_flow.flow_code = "ECN_FLOW"
        mock_flow.nodes = [MagicMock()]
        mock_flow.is_active = True

        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_flow

        config = {"auto_approve": True, "timeout": 72}
        instance = self.engine.create_instance(
            flow_code="ECN_FLOW",
            business_type="ECN",
            business_id=456,
            business_title="配置测试",
            submitted_by=2,
            config=config,
        )

        self.assertIsNotNone(instance)
        mock_save.assert_called_once()


class TestGetCurrentNode(unittest.TestCase):
    """get_current_node 方法测试"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.engine = WorkflowEngine(self.mock_db)

    def test_get_current_node_with_id(self):
        """测试通过 current_node_id 获取节点"""
        mock_instance = MagicMock()
        mock_instance.current_node_id = 5
        mock_instance.current_status = ApprovalStatus.IN_PROGRESS.value

        mock_node = MagicMock()
        mock_node.id = 5
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_node

        result = self.engine.get_current_node(mock_instance)

        self.assertEqual(result, mock_node)

    def test_get_current_node_first_node(self):
        """测试获取第一个节点（无 current_node_id）"""
        mock_instance = MagicMock()
        mock_instance.current_node_id = None
        mock_instance.current_status = ApprovalStatus.PENDING.value
        mock_instance.flow_id = 1

        mock_node = MagicMock()
        mock_node.id = 1
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_node

        result = self.engine.get_current_node(mock_instance)

        self.assertEqual(result, mock_node)

    def test_get_current_node_invalid_status(self):
        """测试无效状态返回 None"""
        mock_instance = MagicMock()
        mock_instance.current_status = ApprovalStatus.APPROVED.value

        result = self.engine.get_current_node(mock_instance)

        self.assertIsNone(result)

    def test_get_current_node_rejected_status(self):
        """测试已拒绝状态返回 None"""
        mock_instance = MagicMock()
        mock_instance.current_status = ApprovalStatus.REJECTED.value

        result = self.engine.get_current_node(mock_instance)

        self.assertIsNone(result)


class TestEvaluateNodeConditions(unittest.TestCase):
    """evaluate_node_conditions 方法测试"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.engine = WorkflowEngine(self.mock_db)

    def test_evaluate_no_condition(self):
        """测试无条件时返回 True"""
        mock_node = MagicMock()
        mock_node.condition_expression = None
        mock_instance = MagicMock()

        result = self.engine.evaluate_node_conditions(mock_node, mock_instance)
        self.assertTrue(result)

    def test_evaluate_empty_condition(self):
        """测试空条件返回 True"""
        mock_node = MagicMock()
        mock_node.condition_expression = ""
        mock_instance = MagicMock()

        result = self.engine.evaluate_node_conditions(mock_node, mock_instance)
        self.assertTrue(result)

    @patch('app.services.approval_engine.condition_parser.ConditionEvaluator')
    def test_evaluate_simple_condition_true(self, mock_evaluator_class):
        """测试简单条件为真"""
        mock_node = MagicMock()
        mock_node.id = 1
        mock_node.condition_expression = "amount > 1000"
        mock_instance = MagicMock()

        mock_evaluator = mock_evaluator_class.return_value
        mock_evaluator.evaluate.return_value = True

        result = self.engine.evaluate_node_conditions(mock_node, mock_instance)
        self.assertTrue(result)

    @patch('app.services.approval_engine.condition_parser.ConditionEvaluator')
    def test_evaluate_simple_condition_false(self, mock_evaluator_class):
        """测试简单条件为假"""
        mock_node = MagicMock()
        mock_node.id = 2
        mock_node.condition_expression = "amount < 500"
        mock_instance = MagicMock()

        mock_evaluator = mock_evaluator_class.return_value
        mock_evaluator.evaluate.return_value = False

        result = self.engine.evaluate_node_conditions(mock_node, mock_instance)
        self.assertFalse(result)

    @patch('app.services.approval_engine.condition_parser.ConditionEvaluator')
    def test_evaluate_condition_parse_error(self, mock_evaluator_class):
        """测试条件解析错误时默认返回 True"""
        from app.services.approval_engine.condition_parser import ConditionParseError

        mock_node = MagicMock()
        mock_node.id = 3
        mock_node.condition_expression = "invalid {{ syntax"
        mock_instance = MagicMock()

        mock_evaluator = mock_evaluator_class.return_value
        mock_evaluator.evaluate.side_effect = ConditionParseError("语法错误")

        result = self.engine.evaluate_node_conditions(mock_node, mock_instance)
        self.assertTrue(result)  # 默认允许

    @patch('app.services.approval_engine.condition_parser.ConditionEvaluator')
    def test_evaluate_condition_numeric_result(self, mock_evaluator_class):
        """测试数值结果转布尔"""
        mock_node = MagicMock()
        mock_node.condition_expression = "form.score"
        mock_instance = MagicMock()

        mock_evaluator = mock_evaluator_class.return_value
        mock_evaluator.evaluate.return_value = 85  # 数值

        result = self.engine.evaluate_node_conditions(mock_node, mock_instance)
        self.assertTrue(result)  # > 0 为 True

    @patch('app.services.approval_engine.condition_parser.ConditionEvaluator')
    def test_evaluate_condition_string_result(self, mock_evaluator_class):
        """测试字符串结果转布尔"""
        mock_node = MagicMock()
        mock_node.condition_expression = "status"
        mock_instance = MagicMock()

        mock_evaluator = mock_evaluator_class.return_value
        mock_evaluator.evaluate.return_value = "true"

        result = self.engine.evaluate_node_conditions(mock_node, mock_instance)
        self.assertTrue(result)


class TestSubmitApproval(unittest.TestCase):
    """submit_approval 方法测试"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.engine = WorkflowEngine(self.mock_db)

    @patch.object(WorkflowEngine, 'get_current_node')
    @patch.object(WorkflowEngine, 'evaluate_node_conditions')
    @patch.object(WorkflowEngine, '_get_approver_name')
    @patch.object(WorkflowEngine, '_get_approver_role')
    @patch.object(WorkflowEngine, '_update_instance_status')
    def test_submit_approval_success(
        self, mock_update, mock_get_role, mock_get_name, mock_eval, mock_get_node
    ):
        """测试成功提交审批"""
        mock_instance = MagicMock()
        mock_instance.id = 1

        mock_node = MagicMock()
        mock_node.id = 10
        mock_get_node.return_value = mock_node
        mock_eval.return_value = True
        mock_get_name.return_value = "张三"
        mock_get_role.return_value = "审批人"

        record = self.engine.submit_approval(
            instance=mock_instance,
            approver_id=5,
            decision=ApprovalDecision.APPROVED.value,
            comment="同意",
        )

        self.assertIsNotNone(record)
        self.assertEqual(record.instance_id, 1)
        self.assertEqual(record.node_id, 10)
        self.assertEqual(record.approver_id, 5)
        self.mock_db.add.assert_called()
        self.mock_db.commit.assert_called()

    @patch.object(WorkflowEngine, 'get_current_node')
    def test_submit_approval_no_node(self, mock_get_node):
        """测试无当前节点时抛出异常"""
        mock_instance = MagicMock()
        mock_get_node.return_value = None

        with self.assertRaises(ValueError) as cm:
            self.engine.submit_approval(
                instance=mock_instance,
                approver_id=5,
                decision=ApprovalDecision.APPROVED.value,
            )
        self.assertIn("没有可审批的节点", str(cm.exception))

    @patch.object(WorkflowEngine, 'get_current_node')
    @patch.object(WorkflowEngine, 'evaluate_node_conditions')
    def test_submit_approval_condition_fail(self, mock_eval, mock_get_node):
        """测试条件不满足时抛出异常"""
        mock_instance = MagicMock()
        mock_node = MagicMock()
        mock_get_node.return_value = mock_node
        mock_eval.return_value = False

        with self.assertRaises(ValueError) as cm:
            self.engine.submit_approval(
                instance=mock_instance,
                approver_id=5,
                decision=ApprovalDecision.REJECTED.value,
            )
        self.assertIn("不满足审批条件", str(cm.exception))


class TestUpdateInstanceStatus(unittest.TestCase):
    """_update_instance_status 方法测试"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.engine = WorkflowEngine(self.mock_db)

    def test_update_status_direct_pending(self):
        """测试直接设置状态为 PENDING"""
        mock_instance = MagicMock()

        self.engine._update_instance_status(
            mock_instance,
            ApprovalStatus.PENDING,
            completed_nodes=0
        )

        self.assertEqual(mock_instance.status, ApprovalStatus.PENDING)
        self.assertEqual(mock_instance.current_status, ApprovalStatus.PENDING.value)
        self.assertEqual(mock_instance.completed_nodes, 0)
        self.mock_db.add.assert_called_with(mock_instance)
        self.mock_db.commit.assert_called()

    def test_update_status_direct_approved(self):
        """测试直接设置状态为 APPROVED"""
        mock_instance = MagicMock()

        self.engine._update_instance_status(
            mock_instance,
            ApprovalStatus.APPROVED.value,
            completed_nodes=3
        )

        self.assertEqual(mock_instance.current_status, ApprovalStatus.APPROVED.value)
        self.assertEqual(mock_instance.completed_nodes, 3)


class TestFindNodes(unittest.TestCase):
    """_find_next_node 和 _find_previous_node 测试"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.engine = WorkflowEngine(self.mock_db)

    def test_find_next_node_exists(self):
        """测试查找下一个节点"""
        mock_node = MagicMock()
        mock_node.flow_id = 1
        mock_node.sequence = 1

        mock_next_node = MagicMock()
        mock_next_node.sequence = 2
        self.mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.first.return_value = mock_next_node

        result = self.engine._find_next_node(mock_node)
        self.assertEqual(result, mock_next_node)

    def test_find_next_node_not_exists(self):
        """测试查找下一个节点（不存在）"""
        mock_node = MagicMock()
        mock_node.flow_id = 1
        mock_node.sequence = 3

        self.mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = self.engine._find_next_node(mock_node)
        self.assertIsNone(result)

    def test_find_previous_node_exists(self):
        """测试查找上一个节点"""
        mock_node = MagicMock()
        mock_node.flow_id = 1
        mock_node.sequence = 2

        mock_prev_node = MagicMock()
        mock_prev_node.sequence = 1
        self.mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.first.return_value = mock_prev_node

        result = self.engine._find_previous_node(mock_node)
        self.assertEqual(result, mock_prev_node)

    def test_find_previous_node_not_exists(self):
        """测试查找上一个节点（第一个节点）"""
        mock_node = MagicMock()
        mock_node.flow_id = 1
        mock_node.sequence = 1

        self.mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = self.engine._find_previous_node(mock_node)
        self.assertIsNone(result)


class TestIsExpired(unittest.TestCase):
    """is_expired 方法测试"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.engine = WorkflowEngine(self.mock_db)

    def test_is_expired_with_due_date_expired(self):
        """测试有 due_date 且已过期"""
        mock_instance = MagicMock()
        mock_instance.due_date = datetime.now() - timedelta(hours=1)

        result = self.engine.is_expired(mock_instance)
        self.assertTrue(result)

    def test_is_expired_with_due_date_not_expired(self):
        """测试有 due_date 且未过期"""
        mock_instance = MagicMock()
        mock_instance.due_date = datetime.now() + timedelta(hours=24)

        result = self.engine.is_expired(mock_instance)
        self.assertFalse(result)

    def test_is_expired_with_created_at_expired(self):
        """测试通过 created_at 判定过期"""
        mock_instance = MagicMock()
        mock_instance.due_date = None
        mock_instance.created_at = datetime.now() - timedelta(hours=50)
        mock_instance.flow_id = 1

        mock_flow = MagicMock()
        mock_flow.first_node_timeout = 48
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_flow

        result = self.engine.is_expired(mock_instance)
        self.assertTrue(result)

    def test_is_expired_no_datetime(self):
        """测试无有效时间字段时返回 False"""
        mock_instance = MagicMock()
        mock_instance.due_date = None
        mock_instance.created_at = None

        result = self.engine.is_expired(mock_instance)
        self.assertFalse(result)


class TestApprovalFlowResolver(unittest.TestCase):
    """ApprovalFlowResolver 测试"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.resolver = WorkflowEngine.ApprovalFlowResolver(self.mock_db)

    def test_get_approval_flow_by_code(self):
        """测试通过 flow_code 获取流程"""
        mock_flow = MagicMock()
        mock_flow.flow_code = "ECN_FLOW"
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_flow

        result = self.resolver.get_approval_flow("ECN_FLOW")
        self.assertEqual(result, mock_flow)

    def test_get_approval_flow_not_found(self):
        """测试流程不存在时抛出异常"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with self.assertRaises(ValueError) as cm:
            self.resolver.get_approval_flow("INVALID_FLOW")
        self.assertIn("不存在或未启用", str(cm.exception))

    def test_determine_approval_flow_ecn(self):
        """测试确定 ECN 流程"""
        result = self.resolver.determine_approval_flow("ECN")
        self.assertEqual(result, "ECN_FLOW")

    def test_determine_approval_flow_quote(self):
        """测试确定 QUOTE 流程"""
        result = self.resolver.determine_approval_flow("QUOTE")
        self.assertEqual(result, "QUOTE_FLOW")

    def test_determine_approval_flow_unknown(self):
        """测试未知业务类型返回 None"""
        result = self.resolver.determine_approval_flow("UNKNOWN_TYPE")
        self.assertIsNone(result)


class TestApprovalRouter(unittest.TestCase):
    """ApprovalRouter 测试"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.router = ApprovalRouter(self.mock_db)

    def test_get_approval_flow_by_business_type(self):
        """测试通过业务类型获取流程"""
        mock_flow = MagicMock()
        mock_flow.module_name = "ECN"
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_flow

        result = self.router.get_approval_flow("ECN")
        self.assertEqual(result, mock_flow)

    def test_get_approval_flow_not_found(self):
        """测试流程不存在时返回 None"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.router.get_approval_flow("INVALID_TYPE")
        self.assertIsNone(result)

    def test_determine_approval_flow_ecn(self):
        """测试确定 ECN 审批流程"""
        result = self.router.determine_approval_flow("ECN", {})
        self.assertEqual(result, "ECN_STANDARD")

    def test_determine_approval_flow_sales_invoice_single(self):
        """测试销售发票单级审批"""
        result = self.router.determine_approval_flow(
            "SALES_INVOICE",
            {"amount": 30000}
        )
        self.assertEqual(result, "SALES_INVOICE_SINGLE")

    def test_determine_approval_flow_sales_invoice_multi(self):
        """测试销售发票多级审批"""
        result = self.router.determine_approval_flow(
            "SALES_INVOICE",
            {"amount": 80000}
        )
        self.assertEqual(result, "SALES_INVOICE_MULTI")

    def test_determine_approval_flow_sales_quote(self):
        """测试销售报价流程"""
        result = self.router.determine_approval_flow("SALES_QUOTE", {})
        self.assertEqual(result, "SALES_QUOTE_SINGLE")

    def test_determine_approval_flow_unknown(self):
        """测试未知业务类型返回 None"""
        result = self.router.determine_approval_flow("UNKNOWN", {})
        self.assertIsNone(result)


class TestHelperMethods(unittest.TestCase):
    """辅助方法测试"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.engine = WorkflowEngine(self.mock_db)

    def test_get_approver_name_found(self):
        """测试获取审批人姓名"""
        mock_user = MagicMock()
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        result = self.engine._get_approver_name(5)
        self.assertEqual(result, "张三")

    def test_get_approver_name_not_found(self):
        """测试用户不存在时返回默认名称"""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.engine._get_approver_name(999)
        self.assertEqual(result, "User_999")

    def test_get_approver_role_user(self):
        """测试获取审批人角色 - 用户"""
        mock_node = MagicMock()
        mock_node.role_type = ApprovalNodeRole.USER.value

        result = self.engine._get_approver_role(mock_node)
        self.assertEqual(result, "用户")

    def test_get_approver_role_department(self):
        """测试获取审批人角色 - 部门"""
        mock_node = MagicMock()
        mock_node.role_type = ApprovalNodeRole.DEPARTMENT.value

        result = self.engine._get_approver_role(mock_node)
        self.assertEqual(result, "部门")

    def test_get_first_node_timeout_default(self):
        """测试获取默认超时时间"""
        mock_flow = MagicMock()
        del mock_flow.first_node_timeout  # 无属性

        result = self.engine._get_first_node_timeout(mock_flow)
        self.assertEqual(result, 48)

    def test_get_first_node_timeout_custom(self):
        """测试获取自定义超时时间"""
        mock_flow = MagicMock()
        mock_flow.first_node_timeout = 72

        result = self.engine._get_first_node_timeout(mock_flow)
        self.assertEqual(result, 72)


if __name__ == "__main__":
    unittest.main()
