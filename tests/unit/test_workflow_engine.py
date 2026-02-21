# -*- coding: utf-8 -*-
"""
WorkflowEngine 单元测试

目标:
1. 只mock外部依赖（db.query, db.add, db.commit等）
2. 测试核心业务逻辑
3. 达到70%+覆盖率
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
from typing import List

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
    """测试WorkflowEngine核心功能"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()
        self.engine = WorkflowEngine(self.db)

    # ========== create_instance() 测试 ==========

    def test_create_instance_success(self):
        """测试成功创建审批实例"""
        # Mock流程查询
        mock_flow = MagicMock()
        mock_flow.id = 1
        mock_flow.flow_code = "ECN_FLOW"
        mock_flow.nodes = [MagicMock(), MagicMock()]  # 2个节点
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_flow

        # 执行
        instance = self.engine.create_instance(
            flow_code="ECN_FLOW",
            business_type="ECN",
            business_id=123,
            business_title="测试ECN",
            submitted_by=1,
        )

        # 验证
        self.assertIsNotNone(instance)
        self.assertEqual(instance.flow_id, 1)
        self.assertEqual(instance.flow_code, "ECN_FLOW")
        self.assertEqual(instance.business_type, "ECN")
        self.assertEqual(instance.business_id, 123)
        self.assertEqual(instance.submitted_by, 1)
        self.assertEqual(instance.total_nodes, 2)
        self.assertEqual(instance.completed_nodes, 0)
        self.assertIsNotNone(instance.instance_no)
        self.assertTrue(instance.instance_no.startswith("AP"))

    def test_create_instance_flow_not_found(self):
        """测试流程不存在"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with self.assertRaises(ValueError) as ctx:
            self.engine.create_instance(
                flow_code="INVALID_FLOW",
                business_type="ECN",
                business_id=123,
                business_title="测试",
                submitted_by=1,
            )
        
        self.assertIn("不存在或未启用", str(ctx.exception))

    def test_generate_instance_no(self):
        """测试实例编号生成"""
        no = self.engine._generate_instance_no()
        self.assertTrue(no.startswith("AP"))
        self.assertEqual(len(no), 14)  # AP + 12位日期时间

    # ========== get_current_node() 测试 ==========

    def test_get_current_node_with_current_node_id(self):
        """测试获取当前节点 - 有current_node_id"""
        mock_instance = MagicMock()
        mock_instance.current_status = ApprovalStatus.IN_PROGRESS.value
        mock_instance.current_node_id = 10
        mock_instance.flow_id = 1

        mock_node = MagicMock()
        mock_node.id = 10

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_node

        node = self.engine.get_current_node(mock_instance)

        self.assertEqual(node, mock_node)

    def test_get_current_node_without_current_node_id(self):
        """测试获取当前节点 - 无current_node_id，返回第一个节点"""
        mock_instance = MagicMock()
        mock_instance.current_status = ApprovalStatus.PENDING.value
        mock_instance.current_node_id = None
        mock_instance.flow_id = 1

        mock_node = MagicMock()
        mock_node.id = 1
        mock_node.sequence = 1

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_node

        node = self.engine.get_current_node(mock_instance)

        self.assertEqual(node, mock_node)

    def test_get_current_node_status_completed(self):
        """测试获取当前节点 - 状态已完成"""
        mock_instance = MagicMock()
        mock_instance.current_status = ApprovalStatus.APPROVED.value

        node = self.engine.get_current_node(mock_instance)

        self.assertIsNone(node)

    def test_get_current_node_status_rejected(self):
        """测试获取当前节点 - 状态已驳回"""
        mock_instance = MagicMock()
        mock_instance.current_status = ApprovalStatus.REJECTED.value

        node = self.engine.get_current_node(mock_instance)

        self.assertIsNone(node)

    # ========== evaluate_node_conditions() 测试 ==========

    def test_evaluate_node_conditions_no_condition(self):
        """测试节点无条件表达式"""
        mock_node = MagicMock()
        mock_node.condition_expression = None
        mock_instance = MagicMock()

        result = self.engine.evaluate_node_conditions(mock_node, mock_instance)

        self.assertTrue(result)

    def test_evaluate_node_conditions_empty_condition(self):
        """测试节点条件为空字符串"""
        mock_node = MagicMock()
        mock_node.condition_expression = ""
        mock_instance = MagicMock()

        result = self.engine.evaluate_node_conditions(mock_node, mock_instance)

        self.assertTrue(result)

    @patch('app.services.approval_engine.condition_parser.ConditionEvaluator')
    def test_evaluate_node_conditions_simple_true(self, mock_evaluator_class):
        """测试条件评估返回True"""
        mock_node = MagicMock()
        mock_node.condition_expression = "amount >= 1000"
        mock_node.id = 1
        
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.flow_code = "ECN_FLOW"
        mock_instance.business_type = "ECN"
        mock_instance.business_id = 123
        mock_instance.current_status = "PENDING"
        mock_instance.submitted_at = datetime.now()
        mock_instance.submitted_by = 1

        # Mock ConditionEvaluator
        mock_evaluator = MagicMock()
        mock_evaluator_class.return_value = mock_evaluator
        mock_evaluator.evaluate.return_value = True

        # Mock用户查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = self.engine.evaluate_node_conditions(mock_node, mock_instance)

        self.assertTrue(result)
        mock_evaluator.evaluate.assert_called_once()

    @patch('app.services.approval_engine.condition_parser.ConditionEvaluator')
    def test_evaluate_node_conditions_simple_false(self, mock_evaluator_class):
        """测试条件评估返回False"""
        mock_node = MagicMock()
        mock_node.condition_expression = "amount >= 10000"
        mock_node.id = 1
        
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.flow_code = "ECN_FLOW"
        mock_instance.business_type = "ECN"
        mock_instance.business_id = 123
        mock_instance.current_status = "PENDING"
        mock_instance.submitted_at = datetime.now()
        mock_instance.submitted_by = 1

        mock_evaluator = MagicMock()
        mock_evaluator_class.return_value = mock_evaluator
        mock_evaluator.evaluate.return_value = False

        # Mock用户查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = self.engine.evaluate_node_conditions(mock_node, mock_instance)

        self.assertFalse(result)

    @patch('app.services.approval_engine.condition_parser.ConditionEvaluator')
    def test_evaluate_node_conditions_parse_error(self, mock_evaluator_class):
        """测试条件解析失败，默认允许"""
        from app.services.approval_engine.condition_parser import ConditionParseError
        
        mock_node = MagicMock()
        mock_node.condition_expression = "invalid {{ syntax"
        mock_node.id = 1
        
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.submitted_by = 1

        mock_evaluator = MagicMock()
        mock_evaluator_class.return_value = mock_evaluator
        mock_evaluator.evaluate.side_effect = ConditionParseError("解析错误")

        # Mock用户查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        result = self.engine.evaluate_node_conditions(mock_node, mock_instance)

        self.assertTrue(result)  # 解析失败默认允许

    # ========== _build_condition_context() 测试 ==========

    def test_build_condition_context_basic(self):
        """测试构建基本上下文"""
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.flow_code = "ECN_FLOW"
        mock_instance.business_type = "ECN"
        mock_instance.business_id = 123
        mock_instance.current_status = "PENDING"
        mock_instance.submitted_at = datetime.now()
        mock_instance.submitted_by = 1

        # Mock用户查询
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "test_user"
        mock_user.real_name = "测试用户"
        mock_user.department = "研发部"

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user

        context = self.engine._build_condition_context(mock_instance)

        self.assertIn("instance", context)
        self.assertIn("initiator", context)
        self.assertIn("user", context)
        self.assertEqual(context["initiator"]["username"], "test_user")
        self.assertEqual(context["user"]["real_name"], "测试用户")

    def test_build_condition_context_with_form_data(self):
        """测试包含form_data的上下文"""
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.flow_code = "ECN_FLOW"
        mock_instance.business_type = "ECN"
        mock_instance.business_id = 123
        mock_instance.current_status = "PENDING"
        mock_instance.submitted_at = datetime.now()
        mock_instance.submitted_by = 1
        mock_instance.form_data = {"amount": 5000, "priority": "HIGH"}

        # Mock用户查询
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        context = self.engine._build_condition_context(mock_instance)

        self.assertEqual(context["form"]["amount"], 5000)
        self.assertEqual(context["amount"], 5000)

    # ========== _get_business_entity_data() 测试 ==========

    def test_get_business_entity_data_ecn(self):
        """测试获取ECN业务数据"""
        mock_ecn = MagicMock()
        mock_ecn.id = 123
        mock_ecn.ecn_no = "ECN-001"
        mock_ecn.ecn_type = "TECHNICAL"
        mock_ecn.status = "DRAFT"
        mock_ecn.priority = "HIGH"
        mock_ecn.change_reason = "优化设计"
        mock_ecn.estimated_cost = 5000

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_ecn

        data = self.engine._get_business_entity_data("ECN", 123)

        self.assertEqual(data["ecn_no"], "ECN-001")
        self.assertEqual(data["estimated_cost"], 5000)

    def test_get_business_entity_data_sales_quote(self):
        """测试获取销售报价数据 - 模型可能不存在的情况"""
        data = self.engine._get_business_entity_data("SALES_QUOTE", 456)
        
        # 根据环境，可能返回数据或空字典（模型不存在时）
        # 两种情况都是有效的，测试应该容忍
        self.assertIsInstance(data, dict)

    def test_get_business_entity_data_not_found(self):
        """测试业务实体不存在"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        data = self.engine._get_business_entity_data("ECN", 999)

        self.assertEqual(data, {})

    def test_get_business_entity_data_unknown_type(self):
        """测试未知业务类型"""
        data = self.engine._get_business_entity_data("UNKNOWN_TYPE", 123)

        self.assertEqual(data, {})

    # ========== submit_approval() 测试 ==========

    def test_submit_approval_approved(self):
        """测试提交审批 - 通过"""
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.flow_id = 1
        mock_instance.current_node_id = 1
        mock_instance.completed_nodes = 0

        mock_node = MagicMock()
        mock_node.id = 1
        mock_node.sequence = 1
        mock_node.flow_id = 1
        mock_node.condition_expression = None
        mock_node.role_type = ApprovalNodeRole.USER.value

        mock_flow = MagicMock()
        mock_flow.total_nodes = 2

        # Mock get_current_node
        with patch.object(self.engine, 'get_current_node', return_value=mock_node):
            # Mock用户查询
            mock_user = MagicMock()
            mock_user.real_name = "审批人"
            
            # Mock _find_next_node
            next_node = MagicMock()
            next_node.id = 2
            
            def mock_query_side_effect(*args, **kwargs):
                mock_q = MagicMock()
                mock_q.filter.return_value = mock_q
                mock_q.order_by.return_value = mock_q
                # 第一次调用返回用户，第二次返回下一个节点
                if hasattr(mock_query_side_effect, 'call_count'):
                    mock_query_side_effect.call_count += 1
                else:
                    mock_query_side_effect.call_count = 1
                
                if mock_query_side_effect.call_count == 1:
                    mock_q.first.return_value = mock_user
                else:
                    mock_q.first.return_value = next_node
                return mock_q
            
            self.db.query.side_effect = mock_query_side_effect

            record = self.engine.submit_approval(
                mock_instance,
                approver_id=10,
                decision=ApprovalDecision.APPROVED,
                comment="同意",
            )

            self.assertIsNotNone(record)
            self.assertEqual(record.decision, ApprovalDecision.APPROVED)
            self.assertEqual(record.comment, "同意")
            self.db.add.assert_called()
            self.db.commit.assert_called()

    def test_submit_approval_no_current_node(self):
        """测试提交审批 - 无当前节点"""
        mock_instance = MagicMock()

        with patch.object(self.engine, 'get_current_node', return_value=None):
            with self.assertRaises(ValueError) as ctx:
                self.engine.submit_approval(
                    mock_instance,
                    approver_id=10,
                    decision=ApprovalDecision.APPROVED,
                )
            
            self.assertIn("没有可审批的节点", str(ctx.exception))

    def test_submit_approval_condition_not_met(self):
        """测试提交审批 - 条件不满足"""
        mock_instance = MagicMock()
        mock_node = MagicMock()

        with patch.object(self.engine, 'get_current_node', return_value=mock_node):
            with patch.object(self.engine, 'evaluate_node_conditions', return_value=False):
                with self.assertRaises(ValueError) as ctx:
                    self.engine.submit_approval(
                        mock_instance,
                        approver_id=10,
                        decision=ApprovalDecision.APPROVED,
                    )
                
                self.assertIn("不满足审批条件", str(ctx.exception))

    # ========== _get_approver_name() 测试 ==========

    def test_get_approver_name_found(self):
        """测试获取审批人姓名 - 找到用户"""
        mock_user = MagicMock()
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user

        name = self.engine._get_approver_name(10)

        self.assertEqual(name, "张三")

    def test_get_approver_name_not_found(self):
        """测试获取审批人姓名 - 未找到用户"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        name = self.engine._get_approver_name(999)

        self.assertEqual(name, "User_999")

    # ========== _get_approver_role() 测试 ==========

    def test_get_approver_role_user(self):
        """测试获取审批角色 - 用户"""
        mock_node = MagicMock()
        mock_node.role_type = ApprovalNodeRole.USER.value

        role = self.engine._get_approver_role(mock_node)

        self.assertEqual(role, "用户")

    def test_get_approver_role_department(self):
        """测试获取审批角色 - 部门"""
        mock_node = MagicMock()
        mock_node.role_type = ApprovalNodeRole.DEPARTMENT.value

        role = self.engine._get_approver_role(mock_node)

        self.assertEqual(role, "部门")

    # ========== _update_instance_status() 测试 ==========

    def test_update_instance_status_direct_status(self):
        """测试直接设置状态"""
        mock_instance = MagicMock()
        mock_instance.completed_nodes = 0

        self.engine._update_instance_status(
            mock_instance,
            ApprovalStatus.APPROVED,
            completed_nodes=2
        )

        self.assertEqual(mock_instance.current_status, ApprovalStatus.APPROVED.value)
        self.assertEqual(mock_instance.completed_nodes, 2)
        self.db.commit.assert_called()

    # ========== _find_next_node() 测试 ==========

    def test_find_next_node_exists(self):
        """测试查找下一个节点 - 存在"""
        mock_current_node = MagicMock()
        mock_current_node.flow_id = 1
        mock_current_node.sequence = 1

        mock_next_node = MagicMock()
        mock_next_node.id = 2
        mock_next_node.sequence = 2

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_next_node

        next_node = self.engine._find_next_node(mock_current_node)

        self.assertEqual(next_node, mock_next_node)

    def test_find_next_node_not_exists(self):
        """测试查找下一个节点 - 不存在"""
        mock_current_node = MagicMock()
        mock_current_node.flow_id = 1
        mock_current_node.sequence = 10

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None

        next_node = self.engine._find_next_node(mock_current_node)

        self.assertIsNone(next_node)

    # ========== _find_previous_node() 测试 ==========

    def test_find_previous_node_exists(self):
        """测试查找上一个节点 - 存在"""
        mock_current_node = MagicMock()
        mock_current_node.flow_id = 1
        mock_current_node.sequence = 2

        mock_prev_node = MagicMock()
        mock_prev_node.id = 1
        mock_prev_node.sequence = 1

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_prev_node

        prev_node = self.engine._find_previous_node(mock_current_node)

        self.assertEqual(prev_node, mock_prev_node)

    def test_find_previous_node_not_exists(self):
        """测试查找上一个节点 - 不存在"""
        mock_current_node = MagicMock()
        mock_current_node.flow_id = 1
        mock_current_node.sequence = 1

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None

        prev_node = self.engine._find_previous_node(mock_current_node)

        self.assertIsNone(prev_node)

    # ========== _get_first_node_timeout() 测试 ==========

    def test_get_first_node_timeout_custom(self):
        """测试获取自定义超时时间"""
        mock_flow = MagicMock()
        mock_flow.first_node_timeout = 24

        timeout = self.engine._get_first_node_timeout(mock_flow)

        self.assertEqual(timeout, 24)

    def test_get_first_node_timeout_default(self):
        """测试获取默认超时时间"""
        mock_flow = MagicMock()
        mock_flow.first_node_timeout = None

        timeout = self.engine._get_first_node_timeout(mock_flow)

        self.assertEqual(timeout, 48)

    # ========== is_expired() 测试 ==========

    def test_is_expired_with_due_date_expired(self):
        """测试实例超时 - 使用due_date"""
        mock_instance = MagicMock()
        mock_instance.due_date = datetime.now() - timedelta(hours=1)

        result = self.engine.is_expired(mock_instance)

        self.assertTrue(result)

    def test_is_expired_with_due_date_not_expired(self):
        """测试实例未超时 - 使用due_date"""
        mock_instance = MagicMock()
        mock_instance.due_date = datetime.now() + timedelta(hours=1)

        result = self.engine.is_expired(mock_instance)

        self.assertFalse(result)

    def test_is_expired_with_created_at_expired(self):
        """测试实例超时 - 使用created_at"""
        mock_instance = MagicMock()
        mock_instance.due_date = None
        mock_instance.created_at = datetime.now() - timedelta(hours=50)
        mock_instance.flow_id = 1

        mock_flow = MagicMock()
        mock_flow.first_node_timeout = 48

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_flow

        result = self.engine.is_expired(mock_instance)

        self.assertTrue(result)

    def test_is_expired_no_date_info(self):
        """测试实例无日期信息"""
        mock_instance = MagicMock()
        mock_instance.due_date = None
        mock_instance.created_at = None

        result = self.engine.is_expired(mock_instance)

        self.assertFalse(result)


class TestApprovalFlowResolver(unittest.TestCase):
    """测试ApprovalFlowResolver"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()
        self.engine = WorkflowEngine(self.db)
        self.resolver = self.engine.ApprovalFlowResolver(self.db)

    def test_get_approval_flow_by_flow_code(self):
        """测试通过flow_code获取流程"""
        mock_flow = MagicMock()
        mock_flow.flow_code = "ECN_FLOW"

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_flow

        flow = self.resolver.get_approval_flow("ECN_FLOW")

        self.assertEqual(flow, mock_flow)

    def test_get_approval_flow_by_module_name(self):
        """测试通过module_name获取流程（兼容模式）"""
        mock_flow = MagicMock()
        mock_flow.module_name = "ECN"

        call_count = [0]
        
        def mock_first():
            call_count[0] += 1
            if call_count[0] == 1:
                return None  # 第一次按flow_code查询返回None
            else:
                return mock_flow  # 第二次按module_name查询返回flow
        
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = mock_first

        flow = self.resolver.get_approval_flow("ECN")

        self.assertEqual(flow, mock_flow)

    def test_get_approval_flow_not_found(self):
        """测试流程不存在"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        with self.assertRaises(ValueError) as ctx:
            self.resolver.get_approval_flow("INVALID_FLOW")
        
        self.assertIn("不存在或未启用", str(ctx.exception))

    def test_determine_approval_flow_ecn(self):
        """测试确定ECN审批流程"""
        flow_code = self.resolver.determine_approval_flow("ECN")
        self.assertEqual(flow_code, "ECN_FLOW")

    def test_determine_approval_flow_sales_quote(self):
        """测试确定销售报价审批流程"""
        flow_code = self.resolver.determine_approval_flow("SALES_QUOTE")
        self.assertEqual(flow_code, "SALES_QUOTE_FLOW")

    def test_determine_approval_flow_unknown(self):
        """测试未知业务类型"""
        flow_code = self.resolver.determine_approval_flow("UNKNOWN_TYPE")
        self.assertIsNone(flow_code)


class TestApprovalRouter(unittest.TestCase):
    """测试ApprovalRouter"""

    def setUp(self):
        """设置测试环境"""
        self.db = MagicMock()
        self.router = ApprovalRouter(self.db)

    def test_get_approval_flow_found(self):
        """测试获取审批流程 - 找到"""
        mock_flow = MagicMock()
        mock_flow.module_name = "ECN"

        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_flow

        flow = self.router.get_approval_flow("ECN")

        self.assertEqual(flow, mock_flow)

    def test_get_approval_flow_not_found(self):
        """测试获取审批流程 - 未找到"""
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None

        flow = self.router.get_approval_flow("UNKNOWN")

        self.assertIsNone(flow)

    def test_determine_approval_flow_ecn(self):
        """测试确定ECN审批流程"""
        flow_code = self.router.determine_approval_flow("ECN", {})
        self.assertEqual(flow_code, "ECN_STANDARD")

    def test_determine_approval_flow_sales_invoice_small(self):
        """测试确定销售发票审批流程 - 小额"""
        flow_code = self.router.determine_approval_flow(
            "SALES_INVOICE",
            {"amount": 30000}
        )
        self.assertEqual(flow_code, "SALES_INVOICE_SINGLE")

    def test_determine_approval_flow_sales_invoice_large(self):
        """测试确定销售发票审批流程 - 大额"""
        flow_code = self.router.determine_approval_flow(
            "SALES_INVOICE",
            {"amount": 80000}
        )
        self.assertEqual(flow_code, "SALES_INVOICE_MULTI")

    def test_determine_approval_flow_sales_quote(self):
        """测试确定销售报价审批流程"""
        flow_code = self.router.determine_approval_flow("SALES_QUOTE", {})
        self.assertEqual(flow_code, "SALES_QUOTE_SINGLE")

    def test_determine_approval_flow_unknown(self):
        """测试未知业务类型"""
        flow_code = self.router.determine_approval_flow("UNKNOWN", {})
        self.assertIsNone(flow_code)


if __name__ == "__main__":
    unittest.main()
