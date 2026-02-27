# -*- coding: utf-8 -*-
"""
WorkflowEngine 单元测试 - 重写版本

目标：
1. 只mock外部依赖（数据库查询、User对象）
2. 构造真实的 ApprovalFlow/Instance/Node 对象测试核心业务逻辑
3. 达到70%+覆盖率

覆盖的核心方法：
- create_instance()
- get_current_node()
- evaluate_node_conditions()
- submit_approval()
- _update_instance_status()
- _find_next_node()
- _find_previous_node()
- is_expired()
- _build_condition_context()
- _get_business_entity_data()
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

from app.services.approval_engine.workflow_engine import (
    WorkflowEngine,
    ApprovalRouter,
)
from app.services.approval_engine.models import (
    LegacyApprovalFlow as ApprovalFlow,
    LegacyApprovalInstance as ApprovalInstance,
    LegacyApprovalNode as ApprovalNode,
    LegacyApprovalRecord as ApprovalRecord,
    ApprovalStatus,
    ApprovalDecision,
    ApprovalNodeRole,
    ApprovalFlowType,
)


class TestWorkflowEngineCore(unittest.TestCase):
    """测试 WorkflowEngine 核心功能"""

    def setUp(self):
        """测试前置设置"""
        self.db = MagicMock()
        self.engine = WorkflowEngine(self.db)

    # ========== 初始化测试 ==========

    def test_init(self):
        """测试初始化"""
        self.assertIs(self.engine.db, self.db)

    def test_generate_instance_no(self):
        """测试生成实例编号"""
        instance_no = self.engine._generate_instance_no()
        self.assertTrue(instance_no.startswith("AP"))
        self.assertEqual(len(instance_no), 14)  # AP + 12位时间戳

    # ========== create_instance() 测试 ==========

    def test_create_instance_success(self):
        """测试成功创建审批实例"""
        # 构造真实的 ApprovalFlow 对象
        flow = ApprovalFlow(
            id=1,
            flow_code="ECN_FLOW",
            flow_name="ECN审批",
            flow_type=ApprovalFlowType.MULTI_LEVEL.value,
            module_name="ECN",
            is_active=True,
            version=1,
        )
        flow.nodes = [
            ApprovalNode(id=1, flow_id=1, node_code="N1", node_name="技术审批", sequence=1),
            ApprovalNode(id=2, flow_id=1, node_code="N2", node_name="财务审批", sequence=2),
        ]

        # Mock 数据库查询返回真实对象
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = flow
        self.db.query.return_value = mock_query

        # 调用创建实例
        instance = self.engine.create_instance(
            flow_code="ECN_FLOW",
            business_type="ECN",
            business_id=100,
            business_title="ECN-001 技术变更",
            submitted_by=1,
        )

        # 验证实例属性
        self.assertIsInstance(instance, ApprovalInstance)
        self.assertEqual(instance.flow_id, 1)
        self.assertEqual(instance.flow_code, "ECN_FLOW")
        self.assertEqual(instance.business_type, "ECN")
        self.assertEqual(instance.business_id, 100)
        self.assertEqual(instance.business_title, "ECN-001 技术变更")
        self.assertEqual(instance.submitted_by, 1)
        self.assertEqual(instance.current_status, ApprovalStatus.PENDING.value)
        self.assertEqual(instance.total_nodes, 2)
        self.assertEqual(instance.completed_nodes, 0)
        self.assertIsNotNone(instance.instance_no)
        self.assertIsNotNone(instance.submitted_at)
        self.assertIsNotNone(instance.due_date)

    def test_create_instance_flow_not_found(self):
        """测试流程不存在时抛出异常"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        with self.assertRaises(ValueError) as ctx:
            self.engine.create_instance(
                flow_code="INVALID_FLOW",
                business_type="ECN",
                business_id=100,
                business_title="测试",
                submitted_by=1,
            )
        self.assertIn("不存在或未启用", str(ctx.exception))

    def test_create_instance_with_config(self):
        """测试创建实例时传入配置"""
        flow = ApprovalFlow(
            id=1,
            flow_code="ECN_FLOW",
            flow_name="ECN审批",
            is_active=True,
        )
        flow.nodes = [ApprovalNode(id=1, flow_id=1, sequence=1)]

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = flow
        self.db.query.return_value = mock_query

        config = {"priority": "high"}
        instance = self.engine.create_instance(
            flow_code="ECN_FLOW",
            business_type="ECN",
            business_id=100,
            business_title="测试",
            submitted_by=1,
            config=config,
        )

        self.assertIsNotNone(instance)

    # ========== get_current_node() 测试 ==========

    def test_get_current_node_with_current_node_id(self):
        """测试从 current_node_id 获取当前节点"""
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            current_node_id=10,
            current_status=ApprovalStatus.IN_PROGRESS.value,
        )

        node = ApprovalNode(
            id=10,
            flow_id=1,
            node_code="N1",
            node_name="审批节点1",
            sequence=1,
        )

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = node
        self.db.query.return_value = mock_query

        current_node = self.engine.get_current_node(instance)

        self.assertIsNotNone(current_node)
        self.assertEqual(current_node.id, 10)
        self.assertEqual(current_node.node_name, "审批节点1")

    def test_get_current_node_without_current_node_id(self):
        """测试没有 current_node_id 时获取第一个节点"""
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            current_node_id=None,
            current_status=ApprovalStatus.PENDING.value,
        )

        node = ApprovalNode(
            id=1,
            flow_id=1,
            node_code="N1",
            node_name="第一个节点",
            sequence=1,
        )

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = node
        self.db.query.return_value = mock_query

        current_node = self.engine.get_current_node(instance)

        self.assertIsNotNone(current_node)
        self.assertEqual(current_node.id, 1)

    def test_get_current_node_when_approved(self):
        """测试已通过的实例返回 None"""
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            current_status=ApprovalStatus.APPROVED.value,
        )

        current_node = self.engine.get_current_node(instance)
        self.assertIsNone(current_node)

    def test_get_current_node_when_rejected(self):
        """测试已驳回的实例返回 None"""
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            current_status=ApprovalStatus.REJECTED.value,
        )

        current_node = self.engine.get_current_node(instance)
        self.assertIsNone(current_node)

    # ========== evaluate_node_conditions() 测试 ==========

    def test_evaluate_node_conditions_no_condition(self):
        """测试无条件表达式时返回 True"""
        node = ApprovalNode(
            id=1,
            flow_id=1,
            condition_expression=None,
        )
        instance = ApprovalInstance(id=1, flow_id=1)

        result = self.engine.evaluate_node_conditions(node, instance)
        self.assertTrue(result)

    def test_evaluate_node_conditions_empty_condition(self):
        """测试空条件表达式时返回 True"""
        node = ApprovalNode(
            id=1,
            flow_id=1,
            condition_expression="",
        )
        instance = ApprovalInstance(id=1, flow_id=1)

        result = self.engine.evaluate_node_conditions(node, instance)
        self.assertTrue(result)

    @patch('app.services.approval_engine.condition_parser.ConditionEvaluator')
    def test_evaluate_node_conditions_true(self, mock_evaluator_class):
        """测试条件评估返回 True"""
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate.return_value = True
        mock_evaluator_class.return_value = mock_evaluator

        node = ApprovalNode(
            id=1,
            flow_id=1,
            condition_expression="amount > 1000",
        )
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            business_type="ECN",
            business_id=100,
        )

        # Mock User 查询
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_user_query

        result = self.engine.evaluate_node_conditions(node, instance)
        self.assertTrue(result)

    @patch('app.services.approval_engine.condition_parser.ConditionEvaluator')
    def test_evaluate_node_conditions_false(self, mock_evaluator_class):
        """测试条件评估返回 False"""
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate.return_value = False
        mock_evaluator_class.return_value = mock_evaluator

        node = ApprovalNode(
            id=1,
            flow_id=1,
            condition_expression="amount > 10000",
        )
        instance = ApprovalInstance(id=1, flow_id=1)

        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_user_query

        result = self.engine.evaluate_node_conditions(node, instance)
        self.assertFalse(result)

    @patch('app.services.approval_engine.condition_parser.ConditionEvaluator')
    def test_evaluate_node_conditions_parse_error(self, mock_evaluator_class):
        """测试条件解析失败时返回 True（默认允许）"""
        from app.services.approval_engine.condition_parser import ConditionParseError

        mock_evaluator = MagicMock()
        mock_evaluator.evaluate.side_effect = ConditionParseError("解析失败")
        mock_evaluator_class.return_value = mock_evaluator

        node = ApprovalNode(
            id=1,
            flow_id=1,
            condition_expression="invalid syntax {{",
        )
        instance = ApprovalInstance(id=1, flow_id=1)

        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_user_query

        result = self.engine.evaluate_node_conditions(node, instance)
        self.assertTrue(result)

    @patch('app.services.approval_engine.condition_parser.ConditionEvaluator')
    def test_evaluate_node_conditions_generic_exception(self, mock_evaluator_class):
        """测试通用异常时返回 True（默认允许）"""
        mock_evaluator = MagicMock()
        mock_evaluator.evaluate.side_effect = Exception("未知错误")
        mock_evaluator_class.return_value = mock_evaluator

        node = ApprovalNode(
            id=1,
            flow_id=1,
            condition_expression="amount > 1000",
        )
        instance = ApprovalInstance(id=1, flow_id=1)

        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_user_query

        result = self.engine.evaluate_node_conditions(node, instance)
        self.assertTrue(result)

    @patch('app.services.approval_engine.condition_parser.ConditionEvaluator')
    def test_evaluate_node_conditions_non_boolean_result(self, mock_evaluator_class):
        """测试条件评估返回非布尔值的类型转换"""
        mock_evaluator = MagicMock()
        
        # 测试数字类型
        mock_evaluator.evaluate.return_value = 5
        mock_evaluator_class.return_value = mock_evaluator
        node = ApprovalNode(id=1, flow_id=1, condition_expression="5")
        instance = ApprovalInstance(id=1, flow_id=1)
        
        mock_user_query = MagicMock()
        mock_user_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_user_query
        
        result = self.engine.evaluate_node_conditions(node, instance)
        self.assertTrue(result)  # 5 > 0 -> True
        
        # 测试字符串 "true"
        mock_evaluator.evaluate.return_value = "true"
        result = self.engine.evaluate_node_conditions(node, instance)
        self.assertTrue(result)
        
        # 测试字符串 "false"
        mock_evaluator.evaluate.return_value = "false"
        result = self.engine.evaluate_node_conditions(node, instance)
        self.assertFalse(result)

    # ========== _build_condition_context() 测试 ==========

    def test_build_condition_context_basic(self):
        """测试基础上下文构建"""
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            flow_code="ECN_FLOW",
            business_type="ECN",
            business_id=100,
            current_status=ApprovalStatus.PENDING.value,
            submitted_at=datetime.now(),
            submitted_by=None,
        )

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        context = self.engine._build_condition_context(instance)

        self.assertIn("instance", context)
        self.assertIn("form", context)
        self.assertIn("entity", context)
        self.assertIn("initiator", context)
        self.assertEqual(context["instance"]["id"], 1)
        self.assertEqual(context["instance"]["flow_code"], "ECN_FLOW")
        self.assertEqual(context["instance"]["business_type"], "ECN")

    def test_build_condition_context_with_submitter(self):
        """测试包含提交人信息的上下文"""
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            flow_code="ECN_FLOW",
            business_type="ECN",
            business_id=100,
            submitted_by=5,
            submitted_at=datetime.now(),
        )

        # Mock User 对象
        from app.models.user import User
        user = User(id=5, username="testuser", real_name="张三", department="技术部",
        password_hash="test_hash_123"
    )

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = user
        self.db.query.return_value = mock_query

        context = self.engine._build_condition_context(instance)

        self.assertIn("initiator", context)
        self.assertEqual(context["initiator"]["id"], 5)
        self.assertEqual(context["initiator"]["username"], "testuser")
        self.assertEqual(context["initiator"]["real_name"], "张三")
        self.assertEqual(context["initiator"]["department"], "技术部")
        # 验证别名
        self.assertIn("user", context)
        self.assertEqual(context["user"]["id"], 5)

    def test_build_condition_context_with_form_data(self):
        """测试包含表单数据的上下文"""
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            business_type="ECN",
            business_id=100,
            submitted_by=None,
        )
        instance.form_data = {"amount": 5000, "priority": "high", "days": 3}

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        context = self.engine._build_condition_context(instance)

        # 验证 form_data 合并到顶层
        self.assertIn("amount", context)
        self.assertEqual(context["amount"], 5000)
        self.assertEqual(context["priority"], "high")
        self.assertEqual(context["days"], 3)
        # 验证也在 form 中
        self.assertEqual(context["form"]["amount"], 5000)

    # ========== _get_business_entity_data() 测试 ==========

    def test_get_business_entity_data_ecn(self):
        """测试获取 ECN 业务实体数据"""
        from app.models.ecn import Ecn
        
        ecn = Ecn(
            id=100,
            ecn_no="ECN-001",
            ecn_type="技术变更",
            status="PENDING",
            change_reason="优化设计",
        )
        ecn.priority = "high"
        ecn.estimated_cost = Decimal("5000")

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = ecn
        self.db.query.return_value = mock_query

        data = self.engine._get_business_entity_data("ECN", 100)

        self.assertEqual(data["id"], 100)
        self.assertEqual(data["ecn_no"], "ECN-001")
        self.assertEqual(data["ecn_type"], "技术变更")
        self.assertEqual(data["status"], "PENDING")
        self.assertEqual(data["priority"], "high")
        self.assertEqual(data["estimated_cost"], Decimal("5000"))
        self.assertEqual(data["change_reason"], "优化设计")

    def test_get_business_entity_data_purchase_order(self):
        """测试获取采购订单业务实体数据"""
        from app.models.purchase import PurchaseOrder
        
        po = PurchaseOrder(
            id=200,
            order_no="PO-001",
            status="PENDING",
            total_amount=Decimal("10000"),
            supplier_id=1,
        )

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = po
        self.db.query.return_value = mock_query

        data = self.engine._get_business_entity_data("PURCHASE_ORDER", 200)

        self.assertEqual(data["id"], 200)
        self.assertEqual(data["order_no"], "PO-001")
        self.assertEqual(data["total_amount"], 10000.0)
        self.assertEqual(data["supplier_id"], 1)

    def test_get_business_entity_data_not_found(self):
        """测试业务实体不存在时返回空字典"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        data = self.engine._get_business_entity_data("ECN", 999)
        self.assertEqual(data, {})

    def test_get_business_entity_data_unknown_type(self):
        """测试未知业务类型返回空字典"""
        data = self.engine._get_business_entity_data("UNKNOWN_TYPE", 100)
        self.assertEqual(data, {})

    def test_get_business_entity_data_exception(self):
        """测试查询异常时返回空字典"""
        mock_query = MagicMock()
        mock_query.filter.side_effect = Exception("数据库错误")
        self.db.query.return_value = mock_query

        data = self.engine._get_business_entity_data("ECN", 100)
        self.assertEqual(data, {})

    # ========== submit_approval() 测试 ==========

    def test_submit_approval_success_approved(self):
        """测试成功提交审批（通过）"""
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            current_node_id=10,
            current_status=ApprovalStatus.IN_PROGRESS.value,
            completed_nodes=0,
        )

        node = ApprovalNode(
            id=10,
            flow_id=1,
            node_code="N1",
            sequence=1,
            condition_expression=None,
            role_type=ApprovalNodeRole.USER.value,  # 添加 role_type 属性
        )

        next_node = ApprovalNode(
            id=11,
            flow_id=1,
            node_code="N2",
            sequence=2,
        )

        from app.models.user import User
        user = User(id=5, username="approver", real_name="审批人",
        password_hash="test_hash_123"
    )

        # Mock 多个查询
        def mock_query_side_effect(model):
            mock_q = MagicMock()
            if model == ApprovalNode:
                # 第一次：get_current_node
                mock_q.filter.return_value.first.return_value = node
                # 第二次：_find_next_node
                mock_q.filter.return_value.filter.return_value.order_by.return_value.first.return_value = next_node
            elif model == User:
                mock_q.filter.return_value.first.return_value = user
            return mock_q

        self.db.query.side_effect = mock_query_side_effect

        record = self.engine.submit_approval(
            instance=instance,
            approver_id=5,
            decision=ApprovalDecision.APPROVED.value,
            comment="同意",
        )

        self.assertIsNotNone(record)
        self.assertEqual(record.decision, ApprovalDecision.APPROVED.value)
        self.assertEqual(record.comment, "同意")
        self.assertEqual(record.approver_id, 5)
        self.assertEqual(record.approver_name, "审批人")
        self.db.add.assert_called()
        self.db.commit.assert_called()

    def test_submit_approval_no_node(self):
        """测试没有可审批节点时抛出异常"""
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            current_status=ApprovalStatus.APPROVED.value,
        )

        with self.assertRaises(ValueError) as ctx:
            self.engine.submit_approval(
                instance=instance,
                approver_id=5,
                decision=ApprovalDecision.APPROVED.value,
            )
        self.assertIn("没有可审批的节点", str(ctx.exception))

    @patch.object(WorkflowEngine, 'evaluate_node_conditions', return_value=False)
    def test_submit_approval_condition_not_met(self, mock_evaluate):
        """测试条件不满足时抛出异常"""
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            current_node_id=10,
            current_status=ApprovalStatus.IN_PROGRESS.value,
        )

        node = ApprovalNode(
            id=10,
            flow_id=1,
            condition_expression="amount > 10000",
        )

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = node
        self.db.query.return_value = mock_query

        with self.assertRaises(ValueError) as ctx:
            self.engine.submit_approval(
                instance=instance,
                approver_id=5,
                decision=ApprovalDecision.APPROVED.value,
            )
        self.assertIn("不满足审批条件", str(ctx.exception))

    # ========== _get_approver_name() 测试 ==========

    def test_get_approver_name_user_found(self):
        """测试获取审批人姓名（用户存在）"""
        from app.models.user import User
        user = User(id=5, username="testuser", real_name="张三",
        password_hash="test_hash_123"
    )

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = user
        self.db.query.return_value = mock_query

        name = self.engine._get_approver_name(5)
        self.assertEqual(name, "张三")

    def test_get_approver_name_user_not_found(self):
        """测试获取审批人姓名（用户不存在）"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        name = self.engine._get_approver_name(999)
        self.assertEqual(name, "User_999")

    def test_get_approver_name_no_real_name(self):
        """测试获取审批人姓名（无真实姓名时使用用户名）"""
        from app.models.user import User
        user = User(id=5, username="testuser", real_name=None,
        password_hash="test_hash_123"
    )

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = user
        self.db.query.return_value = mock_query

        name = self.engine._get_approver_name(5)
        self.assertEqual(name, "testuser")

    # ========== _get_approver_role() 测试 ==========

    def test_get_approver_role_user(self):
        """测试获取审批角色（用户）"""
        node = ApprovalNode(
            id=1,
            flow_id=1,
            role_type=ApprovalNodeRole.USER.value,
        )
        role = self.engine._get_approver_role(node)
        self.assertEqual(role, "用户")

    def test_get_approver_role_role(self):
        """测试获取审批角色（角色）"""
        node = ApprovalNode(
            id=1,
            flow_id=1,
            role_type=ApprovalNodeRole.ROLE.value,
        )
        role = self.engine._get_approver_role(node)
        self.assertEqual(role, "角色")

    def test_get_approver_role_department(self):
        """测试获取审批角色（部门）"""
        node = ApprovalNode(
            id=1,
            flow_id=1,
            role_type=ApprovalNodeRole.DEPARTMENT.value,
        )
        role = self.engine._get_approver_role(node)
        self.assertEqual(role, "部门")

    # ========== _update_instance_status() 测试 ==========

    def test_update_instance_status_direct_call(self):
        """测试直接设置状态"""
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            current_status=ApprovalStatus.PENDING.value,
            completed_nodes=0,
        )

        self.engine._update_instance_status(
            instance,
            ApprovalStatus.APPROVED,
            completed_nodes=3,
        )

        self.assertEqual(instance.current_status, ApprovalStatus.APPROVED.value)
        self.assertEqual(instance.completed_nodes, 3)
        self.db.add.assert_called_with(instance)
        self.db.commit.assert_called()

    def test_update_instance_status_string_status(self):
        """测试使用字符串设置状态"""
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            current_status=ApprovalStatus.PENDING.value,
        )

        self.engine._update_instance_status(
            instance,
            "APPROVED",
            completed_nodes=2,
        )

        self.assertEqual(instance.current_status, "APPROVED")
        self.assertEqual(instance.completed_nodes, 2)

    # ========== _find_next_node() 测试 ==========

    def test_find_next_node_exists(self):
        """测试找到下一个节点"""
        current_node = ApprovalNode(
            id=1,
            flow_id=1,
            sequence=1,
        )

        next_node = ApprovalNode(
            id=2,
            flow_id=1,
            sequence=2,
        )

        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.first.return_value = next_node
        self.db.query.return_value = mock_query

        found = self.engine._find_next_node(current_node)

        self.assertIsNotNone(found)
        self.assertEqual(found.id, 2)

    def test_find_next_node_not_exists(self):
        """测试最后一个节点返回 None"""
        current_node = ApprovalNode(
            id=3,
            flow_id=1,
            sequence=3,
        )

        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        found = self.engine._find_next_node(current_node)
        self.assertIsNone(found)

    # ========== _find_previous_node() 测试 ==========

    def test_find_previous_node_exists(self):
        """测试找到上一个节点"""
        current_node = ApprovalNode(
            id=2,
            flow_id=1,
            sequence=2,
        )

        previous_node = ApprovalNode(
            id=1,
            flow_id=1,
            sequence=1,
        )

        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.first.return_value = previous_node
        self.db.query.return_value = mock_query

        found = self.engine._find_previous_node(current_node)

        self.assertIsNotNone(found)
        self.assertEqual(found.id, 1)

    def test_find_previous_node_not_exists(self):
        """测试第一个节点返回 None"""
        current_node = ApprovalNode(
            id=1,
            flow_id=1,
            sequence=1,
        )

        mock_query = MagicMock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        found = self.engine._find_previous_node(current_node)
        self.assertIsNone(found)

    # ========== _get_first_node_timeout() 测试 ==========

    def test_get_first_node_timeout_with_value(self):
        """测试获取超时时间（flow有设置）"""
        flow = ApprovalFlow(id=1, flow_code="TEST")
        flow.first_node_timeout = 24

        timeout = self.engine._get_first_node_timeout(flow)
        self.assertEqual(timeout, 24)

    def test_get_first_node_timeout_default(self):
        """测试获取超时时间（默认值）"""
        flow = ApprovalFlow(id=1, flow_code="TEST")
        flow.first_node_timeout = None

        timeout = self.engine._get_first_node_timeout(flow)
        self.assertEqual(timeout, 48)

    # ========== is_expired() 测试 ==========

    def test_is_expired_with_due_date_expired(self):
        """测试通过 due_date 判断已超时"""
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            due_date=datetime.now() - timedelta(hours=2),
        )

        result = self.engine.is_expired(instance)
        self.assertTrue(result)

    def test_is_expired_with_due_date_not_expired(self):
        """测试通过 due_date 判断未超时"""
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            due_date=datetime.now() + timedelta(hours=24),
        )

        result = self.engine.is_expired(instance)
        self.assertFalse(result)

    def test_is_expired_with_created_at_expired(self):
        """测试通过 created_at 判断已超时（无 due_date）"""
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            due_date=None,
        )
        instance.created_at = datetime.now() - timedelta(hours=50)

        flow = ApprovalFlow(id=1, flow_code="TEST")
        flow.first_node_timeout = 48

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = flow
        self.db.query.return_value = mock_query

        result = self.engine.is_expired(instance)
        self.assertTrue(result)

    def test_is_expired_with_created_at_not_expired(self):
        """测试通过 created_at 判断未超时"""
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            due_date=None,
        )
        instance.created_at = datetime.now() - timedelta(hours=24)

        flow = ApprovalFlow(id=1, flow_code="TEST")
        flow.first_node_timeout = 48

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = flow
        self.db.query.return_value = mock_query

        result = self.engine.is_expired(instance)
        self.assertFalse(result)

    def test_is_expired_no_date_info(self):
        """测试无日期信息时返回 False"""
        instance = ApprovalInstance(
            id=1,
            flow_id=1,
            due_date=None,
        )
        # 不设置 created_at

        result = self.engine.is_expired(instance)
        self.assertFalse(result)


class TestApprovalFlowResolver(unittest.TestCase):
    """测试 ApprovalFlowResolver 内部类"""

    def setUp(self):
        self.db = MagicMock()
        self.resolver = WorkflowEngine.ApprovalFlowResolver(self.db)

    def test_init(self):
        """测试初始化"""
        self.assertIs(self.resolver.db, self.db)

    def test_get_approval_flow_by_flow_code(self):
        """测试通过 flow_code 获取流程"""
        flow = ApprovalFlow(
            id=1,
            flow_code="ECN_FLOW",
            flow_name="ECN审批",
            is_active=True,
        )

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = flow
        self.db.query.return_value = mock_query

        result = self.resolver.get_approval_flow("ECN_FLOW")

        self.assertIsNotNone(result)
        self.assertEqual(result.flow_code, "ECN_FLOW")

    def test_get_approval_flow_by_module_name(self):
        """测试通过 module_name 获取流程（兼容）"""
        flow = ApprovalFlow(
            id=1,
            flow_code="ECN_FLOW",
            module_name="ECN",
            is_active=True,
        )

        mock_query1 = MagicMock()
        mock_query1.filter.return_value.first.return_value = None

        mock_query2 = MagicMock()
        mock_query2.filter.return_value.first.return_value = flow

        self.db.query.side_effect = [mock_query1, mock_query2]

        result = self.resolver.get_approval_flow("ECN")
        self.assertIsNotNone(result)

    def test_get_approval_flow_not_found(self):
        """测试流程不存在时抛出异常"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        with self.assertRaises(ValueError) as ctx:
            self.resolver.get_approval_flow("INVALID")
        self.assertIn("不存在或未启用", str(ctx.exception))

    def test_determine_approval_flow_ecn(self):
        """测试确定 ECN 流程编码"""
        result = self.resolver.determine_approval_flow("ECN")
        self.assertEqual(result, "ECN_FLOW")

    def test_determine_approval_flow_sales_quote(self):
        """测试确定销售报价流程编码"""
        result = self.resolver.determine_approval_flow("SALES_QUOTE")
        self.assertEqual(result, "SALES_QUOTE_FLOW")

    def test_determine_approval_flow_unknown(self):
        """测试未知业务类型返回 None"""
        result = self.resolver.determine_approval_flow("UNKNOWN")
        self.assertIsNone(result)


class TestApprovalRouter(unittest.TestCase):
    """测试 ApprovalRouter 类"""

    def setUp(self):
        self.db = MagicMock()
        self.router = ApprovalRouter(self.db)

    def test_init(self):
        """测试初始化"""
        self.assertIs(self.router.db, self.db)

    def test_get_approval_flow_success(self):
        """测试成功获取审批流程"""
        flow = ApprovalFlow(
            id=1,
            flow_code="ECN_FLOW",
            module_name="ECN",
            is_active=True,
        )

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = flow
        self.db.query.return_value = mock_query

        result = self.router.get_approval_flow("ECN")

        self.assertIsNotNone(result)
        self.assertEqual(result.module_name, "ECN")

    def test_get_approval_flow_not_found(self):
        """测试流程不存在时返回 None"""
        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        self.db.query.return_value = mock_query

        result = self.router.get_approval_flow("UNKNOWN")
        self.assertIsNone(result)

    def test_determine_approval_flow_ecn(self):
        """测试 ECN 业务类型确定流程"""
        result = self.router.determine_approval_flow("ECN", {})
        self.assertEqual(result, "ECN_STANDARD")

    def test_determine_approval_flow_sales_invoice_single(self):
        """测试销售发票金额 < 50000 使用单级流程"""
        result = self.router.determine_approval_flow("SALES_INVOICE", {"amount": 30000})
        self.assertEqual(result, "SALES_INVOICE_SINGLE")

    def test_determine_approval_flow_sales_invoice_multi(self):
        """测试销售发票金额 >= 50000 使用多级流程"""
        result = self.router.determine_approval_flow("SALES_INVOICE", {"amount": 60000})
        self.assertEqual(result, "SALES_INVOICE_MULTI")

    def test_determine_approval_flow_sales_quote(self):
        """测试销售报价使用单级流程"""
        result = self.router.determine_approval_flow("SALES_QUOTE", {})
        self.assertEqual(result, "SALES_QUOTE_SINGLE")

    def test_determine_approval_flow_unknown(self):
        """测试未知业务类型返回 None"""
        result = self.router.determine_approval_flow("UNKNOWN", {})
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
