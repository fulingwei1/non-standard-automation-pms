# -*- coding: utf-8 -*-
"""
execution_logger.py 增强单元测试

覆盖所有核心方法和边界条件，使用 Mock 避免数据库依赖
"""

import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, call
from typing import Optional

from app.services.approval_engine.execution_logger import (
    ApprovalExecutionLogger,
    ExecutionLogger,
)


class TestApprovalExecutionLoggerInit(unittest.TestCase):
    """测试初始化和配置"""

    def test_init_creates_logger_with_db_session(self):
        """测试初始化时正确设置数据库会话"""
        mock_db = MagicMock()
        logger = ApprovalExecutionLogger(mock_db)
        self.assertEqual(logger.db, mock_db)

    def test_init_enables_all_logging_flags(self):
        """测试初始化时启用所有日志标志"""
        mock_db = MagicMock()
        logger = ApprovalExecutionLogger(mock_db)
        self.assertTrue(logger.log_actions)
        self.assertTrue(logger.log_routing)
        self.assertTrue(logger.log_performance)
        self.assertTrue(logger.log_errors)

    def test_alias_execution_logger_exists(self):
        """测试向后兼容别名"""
        self.assertIs(ExecutionLogger, ApprovalExecutionLogger)


class TestInstanceLifecycleLogs(unittest.TestCase):
    """测试审批实例生命周期日志"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.logger = ApprovalExecutionLogger(self.mock_db)

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_instance_created_basic(self, mock_log):
        """测试基本实例创建日志"""
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.instance_no = "INS-001"
        mock_instance.entity_type = "CONTRACT"
        mock_instance.entity_id = 100
        mock_instance.template_id = 10
        mock_instance.flow_id = 20
        mock_instance.status = "PENDING"

        mock_user = MagicMock()
        mock_user.id = 5
        mock_user.username = "test_user"
        mock_user.real_name = "Test User"

        self.logger.log_instance_created(mock_instance, mock_user)

        mock_log.assert_called_once()
        call_args = mock_log.call_args
        self.assertIn("instance_id", call_args.kwargs["context"])
        self.assertEqual(call_args.kwargs["context"]["instance_id"], 1)

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_instance_created_with_context(self, mock_log):
        """测试实例创建日志包含额外上下文"""
        mock_instance = MagicMock()
        mock_instance.id = 2
        mock_instance.instance_no = "INS-002"
        mock_instance.entity_type = "PURCHASE"
        mock_instance.entity_id = 200
        mock_instance.template_id = 15
        mock_instance.flow_id = 25
        mock_instance.status = "PENDING"

        mock_user = MagicMock()
        mock_user.id = 10
        mock_user.username = "admin"
        mock_user.real_name = None

        extra_context = {"priority": "HIGH", "amount": 50000}
        self.logger.log_instance_created(mock_instance, mock_user, extra_context)

        call_args = mock_log.call_args
        self.assertEqual(call_args.kwargs["context"]["priority"], "HIGH")
        self.assertEqual(call_args.kwargs["context"]["amount"], 50000)

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_instance_created_creates_action_log(self, mock_log):
        """测试实例创建时创建数据库操作日志"""
        mock_instance = MagicMock()
        mock_instance.id = 3
        mock_instance.instance_no = "INS-003"
        mock_instance.entity_type = "CONTRACT"
        mock_instance.entity_id = 300
        mock_instance.template_id = 30
        mock_instance.flow_id = 40
        mock_instance.status = "PENDING"

        mock_user = MagicMock()
        mock_user.id = 15
        mock_user.username = "user1"
        mock_user.real_name = "User One"

        self.logger.log_instance_created(mock_instance, mock_user)

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_instance_status_change(self, mock_log):
        """测试状态变更日志"""
        mock_instance = MagicMock()
        mock_instance.id = 4
        mock_instance.instance_no = "INS-004"

        mock_operator = MagicMock()
        mock_operator.id = 20

        self.logger.log_instance_status_change(
            mock_instance, "PENDING", "APPROVED", "正常流程", mock_operator
        )

        call_args = mock_log.call_args
        self.assertEqual(call_args.kwargs["context"]["old_status"], "PENDING")
        self.assertEqual(call_args.kwargs["context"]["new_status"], "APPROVED")
        self.assertEqual(call_args.kwargs["context"]["reason"], "正常流程")

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_instance_status_change_without_operator(self, mock_log):
        """测试无操作人的状态变更"""
        mock_instance = MagicMock()
        mock_instance.id = 5
        mock_instance.instance_no = "INS-005"

        self.logger.log_instance_status_change(
            mock_instance, "PENDING", "REJECTED", "自动拒绝", None
        )

        call_args = mock_log.call_args
        self.assertIsNone(call_args.kwargs["context"]["operator_id"])

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_instance_completed(self, mock_log):
        """测试实例完成日志"""
        mock_instance = MagicMock()
        mock_instance.id = 6
        mock_instance.instance_no = "INS-006"
        mock_instance.status = "APPROVED"
        mock_instance.completed_nodes = 5
        mock_instance.total_nodes = 5
        mock_instance.completed_at = datetime.now()
        mock_instance.current_status = "IN_PROGRESS"

        mock_operator = MagicMock()
        mock_operator.id = 25
        mock_operator.username = "final_approver"
        mock_operator.real_name = "Final Approver"

        self.logger.log_instance_completed(mock_instance, mock_operator, "全部审批通过")

        self.mock_db.add.assert_called_once()
        call_args = mock_log.call_args
        self.assertEqual(call_args.kwargs["context"]["final_status"], "APPROVED")

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_instance_completed_terminated(self, mock_log):
        """测试实例终止日志"""
        mock_instance = MagicMock()
        mock_instance.id = 7
        mock_instance.instance_no = "INS-007"
        mock_instance.status = "REJECTED"
        mock_instance.completed_nodes = 2
        mock_instance.total_nodes = 5
        mock_instance.completed_at = datetime.now()
        mock_instance.current_status = "IN_PROGRESS"

        mock_operator = MagicMock()
        mock_operator.id = 30
        mock_operator.username = "rejector"
        mock_operator.real_name = None

        self.logger.log_instance_completed(mock_instance, mock_operator)

        action_log = self.mock_db.add.call_args[0][0]
        self.assertEqual(action_log.action, "TERMINATE")


class TestTaskLifecycleLogs(unittest.TestCase):
    """测试审批任务生命周期日志"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.logger = ApprovalExecutionLogger(self.mock_db)

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_task_created(self, mock_log):
        """测试任务创建日志"""
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.instance_id = 10
        mock_task.assignee_id = 100
        mock_task.task_type = "APPROVAL"
        mock_task.due_at = datetime.now() + timedelta(days=1)

        mock_node = MagicMock()
        mock_node.id = 5
        mock_node.node_code = "DEPT_HEAD"
        mock_node.node_name = "部门负责人审批"

        self.logger.log_task_created(mock_task, mock_node)

        call_args = mock_log.call_args
        self.assertEqual(call_args.kwargs["context"]["task_id"], 1)
        self.assertEqual(call_args.kwargs["context"]["node_code"], "DEPT_HEAD")
        self.mock_db.add.assert_called_once()

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_task_created_cc_type(self, mock_log):
        """测试抄送任务创建日志"""
        mock_task = MagicMock()
        mock_task.id = 2
        mock_task.instance_id = 11
        mock_task.assignee_id = 101
        mock_task.task_type = "CC"
        mock_task.due_at = None

        mock_node = MagicMock()
        mock_node.id = 6
        mock_node.node_code = "CC_HR"
        mock_node.node_name = "抄送人力资源"

        self.logger.log_task_created(mock_task, mock_node)

        action_log = self.mock_db.add.call_args[0][0]
        self.assertEqual(action_log.action, "READ_CC")

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_task_created_with_context(self, mock_log):
        """测试任务创建日志包含额外上下文"""
        mock_task = MagicMock()
        mock_task.id = 3
        mock_task.instance_id = 12
        mock_task.assignee_id = 102
        mock_task.task_type = "APPROVAL"
        mock_task.due_at = None

        mock_node = MagicMock()
        mock_node.id = 7
        mock_node.node_code = "FINANCE"
        mock_node.node_name = "财务审批"

        context = {"auto_assigned": True, "rule": "ROUND_ROBIN"}
        self.logger.log_task_created(mock_task, mock_node, context)

        call_args = mock_log.call_args
        self.assertTrue(call_args.kwargs["context"]["auto_assigned"])
        self.assertEqual(call_args.kwargs["context"]["rule"], "ROUND_ROBIN")

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_task_completed_approved(self, mock_log):
        """测试任务审批通过日志"""
        mock_task = MagicMock()
        mock_task.id = 4
        mock_task.instance_id = 13
        mock_task.node_id = 8
        mock_task.assignee_id = 103

        mock_operator = MagicMock()
        mock_operator.id = 103
        mock_operator.username = "approver1"
        mock_operator.real_name = "Approver One"

        self.logger.log_task_completed(mock_task, mock_operator, "APPROVED", "同意")

        action_log = self.mock_db.add.call_args[0][0]
        self.assertEqual(action_log.action, "APPROVE")
        self.assertEqual(action_log.comment, "同意")

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_task_completed_rejected(self, mock_log):
        """测试任务拒绝日志"""
        mock_task = MagicMock()
        mock_task.id = 5
        mock_task.instance_id = 14
        mock_task.node_id = 9
        mock_task.assignee_id = 104

        mock_operator = MagicMock()
        mock_operator.id = 104
        mock_operator.username = "rejector1"
        mock_operator.real_name = None

        self.logger.log_task_completed(mock_task, mock_operator, "REJECTED", "不符合要求")

        action_log = self.mock_db.add.call_args[0][0]
        self.assertEqual(action_log.action, "REJECT")
        self.assertEqual(action_log.before_status, "PENDING")
        self.assertEqual(action_log.after_status, "REJECTED")

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_task_completed_returned(self, mock_log):
        """测试任务退回日志"""
        mock_task = MagicMock()
        mock_task.id = 6
        mock_task.instance_id = 15
        mock_task.node_id = 10
        mock_task.assignee_id = 105

        mock_operator = MagicMock()
        mock_operator.id = 105
        mock_operator.username = "reviewer"
        mock_operator.real_name = "Reviewer"

        self.logger.log_task_completed(mock_task, mock_operator, "RETURNED")

        action_log = self.mock_db.add.call_args[0][0]
        self.assertEqual(action_log.action, "RETURN")

    @patch("app.services.approval_engine.execution_logger.log_warning_with_context")
    def test_log_task_timeout(self, mock_log):
        """测试任务超时日志"""
        mock_task = MagicMock()
        mock_task.id = 7
        mock_task.instance_id = 16
        mock_task.node_id = 11
        mock_task.assignee_id = 106
        mock_task.due_at = datetime.now() - timedelta(hours=2)

        self.logger.log_task_timeout(mock_task, "AUTO_APPROVE")

        call_args = mock_log.call_args
        self.assertEqual(call_args.kwargs["context"]["timeout_action"], "AUTO_APPROVE")
        action_log = self.mock_db.add.call_args[0][0]
        self.assertEqual(action_log.action, "TIMEOUT")

    @patch("app.services.approval_engine.execution_logger.log_warning_with_context")
    def test_log_task_timeout_without_due_at(self, mock_log):
        """测试无截止时间的任务超时日志"""
        mock_task = MagicMock()
        mock_task.id = 8
        mock_task.instance_id = 17
        mock_task.node_id = 12
        mock_task.assignee_id = 107
        mock_task.due_at = None

        self.logger.log_task_timeout(mock_task, "ESCALATE")

        call_args = mock_log.call_args
        self.assertIsNone(call_args.kwargs["context"]["due_at"])


class TestRoutingLogs(unittest.TestCase):
    """测试路由决策日志"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.logger = ApprovalExecutionLogger(self.mock_db)

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_flow_selection(self, mock_log):
        """测试流程选择日志"""
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.instance_no = "INS-001"

        self.logger.log_flow_selection(
            mock_instance, 10, "标准采购流程", "AMOUNT_BASED", "amount > 10000"
        )

        call_args = mock_log.call_args
        self.assertEqual(call_args.kwargs["context"]["selected_flow_id"], 10)
        self.assertEqual(call_args.kwargs["context"]["flow_name"], "标准采购流程")

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_flow_selection_without_routing_rule(self, mock_log):
        """测试无路由规则的流程选择"""
        mock_instance = MagicMock()
        mock_instance.id = 2
        mock_instance.instance_no = "INS-002"

        self.logger.log_flow_selection(mock_instance, 15, "默认流程")

        call_args = mock_log.call_args
        self.assertIsNone(call_args.kwargs["context"]["routing_rule"])

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_node_transition_orm_style(self, mock_log):
        """测试节点流转日志（ORM 对象方式）"""
        mock_instance = MagicMock()
        mock_instance.id = 3
        mock_instance.instance_no = "INS-003"
        mock_instance.initiator_id = 50

        mock_from_node = MagicMock()
        mock_from_node.id = 10
        mock_from_node.node_name = "部门审批"

        mock_to_node = MagicMock()
        mock_to_node.id = 11
        mock_to_node.node_name = "财务审批"

        self.logger.log_node_transition(
            mock_instance, mock_from_node, mock_to_node, "审批通过"
        )

        call_args = mock_log.call_args
        self.assertEqual(call_args.kwargs["context"]["from_node_id"], 10)
        self.assertEqual(call_args.kwargs["context"]["to_node_id"], 11)

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_node_transition_from_start(self, mock_log):
        """测试从开始节点流转"""
        mock_instance = MagicMock()
        mock_instance.id = 4
        mock_instance.instance_no = "INS-004"
        mock_instance.initiator_id = 51

        mock_to_node = MagicMock()
        mock_to_node.id = 12
        mock_to_node.node_name = "提交申请"

        self.logger.log_node_transition(mock_instance, None, mock_to_node, "开始流程")

        call_args = mock_log.call_args
        self.assertEqual(call_args.kwargs["context"]["from_node_name"], "开始")

    def test_log_node_transition_id_style(self):
        """测试节点流转日志（ID 方式）"""
        self.logger.log_node_transition(
            instance_id=100, from_node_id=20, to_node_id=21, trigger="AUTO"
        )

        action_log = self.mock_db.add.call_args[0][0]
        self.assertEqual(action_log.instance_id, 100)
        self.assertEqual(action_log.before_node_id, 20)
        self.assertEqual(action_log.after_node_id, 21)

    def test_log_node_transition_id_style_positional(self):
        """测试节点流转日志（ID 方式，位置参数）"""
        self.logger.log_node_transition(101, 22, 23, "MANUAL")

        action_log = self.mock_db.add.call_args[0][0]
        self.assertEqual(action_log.instance_id, 101)
        self.assertEqual(action_log.comment, "节点流转, trigger=MANUAL")

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_condition_evaluation_matched(self, mock_log):
        """测试条件评估通过日志"""
        mock_node = MagicMock()
        mock_node.id = 30
        mock_node.node_code = "CONDITIONAL_NODE"

        mock_instance = MagicMock()
        mock_instance.id = 5
        mock_instance.instance_no = "INS-005"

        self.logger.log_condition_evaluation(
            mock_node, mock_instance, "amount > 5000", True, matched=True
        )

        call_args = mock_log.call_args
        self.assertTrue(call_args.kwargs["context"]["matched"])

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_condition_evaluation_not_matched(self, mock_log):
        """测试条件评估失败日志"""
        mock_node = MagicMock()
        mock_node.id = 31
        mock_node.node_code = "CONDITIONAL_NODE_2"

        mock_instance = MagicMock()
        mock_instance.id = 6
        mock_instance.instance_no = "INS-006"

        self.logger.log_condition_evaluation(
            mock_node, mock_instance, "priority == 'URGENT'", False, matched=False
        )

        call_args = mock_log.call_args
        self.assertFalse(call_args.kwargs["context"]["matched"])


class TestPerformanceAndDebugLogs(unittest.TestCase):
    """测试性能和调试日志"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.logger = ApprovalExecutionLogger(self.mock_db)

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_performance_metric(self, mock_log):
        """测试性能指标日志"""
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.instance_no = "INS-001"

        self.logger.log_performance_metric(mock_instance, "routing_time", 125.5, "ms")

        call_args = mock_log.call_args
        self.assertEqual(call_args.kwargs["context"]["metric_name"], "routing_time")
        self.assertEqual(call_args.kwargs["context"]["value"], 125.5)

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_performance_metric_disabled(self, mock_log):
        """测试性能日志禁用时不记录"""
        self.logger.log_performance = False

        mock_instance = MagicMock()
        mock_instance.id = 2
        mock_instance.instance_no = "INS-002"

        self.logger.log_performance_metric(
            mock_instance, "query_time", 50.0, "ms"
        )

        mock_log.assert_not_called()

    @patch("app.services.approval_engine.execution_logger.logger")
    def test_log_debug_info(self, mock_logger):
        """测试调试信息日志"""
        self.logger.log_debug_info(100, "变量值检查", {"var1": 10, "var2": "test"})

        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args
        self.assertIn("[DEBUG]", call_args[0][0])


class TestErrorLogs(unittest.TestCase):
    """测试错误和异常日志"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.logger = ApprovalExecutionLogger(self.mock_db)

    @patch("app.services.approval_engine.execution_logger.log_error_with_context")
    def test_log_error_with_instance(self, mock_log):
        """测试带实例的错误日志"""
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.instance_no = "INS-001"

        error = ValueError("无效的审批数据")
        self.logger.log_error(mock_instance, error, "validate_approval_data")

        call_args = mock_log.call_args
        self.assertEqual(call_args.kwargs["context"]["error_type"], "ValueError")
        self.assertEqual(call_args.kwargs["context"]["operation"], "validate_approval_data")

    @patch("app.services.approval_engine.execution_logger.log_error_with_context")
    def test_log_error_without_instance(self, mock_log):
        """测试无实例的错误日志"""
        error = RuntimeError("系统错误")
        self.logger.log_error(None, error, "system_operation")

        call_args = mock_log.call_args
        self.assertIsNone(call_args.kwargs["context"]["instance_id"])

    @patch("app.services.approval_engine.execution_logger.log_error_with_context")
    def test_log_error_with_context(self, mock_log):
        """测试带额外上下文的错误日志"""
        mock_instance = MagicMock()
        mock_instance.id = 2
        mock_instance.instance_no = "INS-002"

        error = KeyError("missing_field")
        context = {"field": "approver_id", "step": "task_assignment"}
        self.logger.log_error(mock_instance, error, "assign_task", context)

        call_args = mock_log.call_args
        self.assertEqual(call_args.kwargs["context"]["field"], "approver_id")

    @patch("app.services.approval_engine.execution_logger.log_error_with_context")
    def test_log_validation_error(self, mock_log):
        """测试验证错误日志"""
        mock_instance = MagicMock()
        mock_instance.id = 3
        mock_instance.instance_no = "INS-003"

        self.logger.log_validation_error(
            mock_instance, "APPROVER_VALIDATION", "审批人不在授权范围内"
        )

        call_args = mock_log.call_args
        self.assertEqual(call_args.kwargs["context"]["validation_type"], "APPROVER_VALIDATION")

    @patch("app.services.approval_engine.execution_logger.log_error_with_context")
    def test_log_validation_error_with_context(self, mock_log):
        """测试带额外上下文的验证错误"""
        mock_instance = MagicMock()
        mock_instance.id = 4
        mock_instance.instance_no = "INS-004"

        context = {"expected": "DEPT_HEAD", "actual": "INTERN"}
        self.logger.log_validation_error(
            mock_instance, "ROLE_VALIDATION", "角色不匹配", context
        )

        call_args = mock_log.call_args
        self.assertEqual(call_args.kwargs["context"]["expected"], "DEPT_HEAD")


class TestActionLogCreation(unittest.TestCase):
    """测试操作日志创建辅助方法"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.logger = ApprovalExecutionLogger(self.mock_db)

    def test_create_action_log_basic(self):
        """测试基本操作日志创建"""
        self.logger._create_action_log(
            instance_id=1,
            operator_id=10,
            operator_name="Test User",
            action="APPROVE",
            comment="同意",
        )

        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()

    def test_create_action_log_full_params(self):
        """测试完整参数操作日志创建"""
        action_detail = {"reason": "符合要求", "score": 95}
        self.logger._create_action_log(
            instance_id=2,
            operator_id=20,
            operator_name="Operator",
            action="APPROVE",
            comment="优秀",
            task_id=100,
            node_id=50,
            before_status="PENDING",
            after_status="APPROVED",
            before_node_id=49,
            after_node_id=50,
            action_detail=action_detail,
        )

        action_log = self.mock_db.add.call_args[0][0]
        self.assertEqual(action_log.instance_id, 2)
        self.assertEqual(action_log.task_id, 100)
        self.assertEqual(action_log.node_id, 50)
        self.assertEqual(action_log.action_detail, action_detail)

    @patch("app.services.approval_engine.execution_logger.logger")
    def test_create_action_log_handles_exception(self, mock_logger):
        """测试操作日志创建异常处理"""
        self.mock_db.add.side_effect = Exception("Database error")

        # 不应该抛出异常
        self.logger._create_action_log(
            instance_id=3,
            operator_id=30,
            operator_name="User",
            action="REJECT",
        )

        mock_logger.error.assert_called_once()


class TestSimplifiedInterfaces(unittest.TestCase):
    """测试简化接口"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.logger = ApprovalExecutionLogger(self.mock_db)

    def test_log_execution(self):
        """测试通用执行日志"""
        details = {"step": "validation", "result": "success"}
        self.logger.log_execution(100, "SUBMIT", 50, details)

        action_log = self.mock_db.add.call_args[0][0]
        self.assertEqual(action_log.instance_id, 100)
        self.assertEqual(action_log.operator_id, 50)
        self.assertEqual(action_log.action, "SUBMIT")
        self.assertEqual(action_log.action_detail, details)

    def test_log_execution_without_details(self):
        """测试无详情的执行日志"""
        self.logger.log_execution(101, "APPROVE", 51)

        action_log = self.mock_db.add.call_args[0][0]
        self.assertIsNone(action_log.action_detail)

    def test_log_approval_action_basic(self):
        """测试基本审批动作日志"""
        self.logger.log_approval_action(
            instance_id=200,
            node_id=10,
            approver_id=60,
            action="APPROVE",
            comment="同意申请",
        )

        action_log = self.mock_db.add.call_args[0][0]
        self.assertEqual(action_log.instance_id, 200)
        self.assertEqual(action_log.node_id, 10)
        self.assertEqual(action_log.comment, "同意申请")

    def test_log_approval_action_with_delegation(self):
        """测试委托审批动作日志"""
        self.logger.log_approval_action(
            instance_id=201,
            node_id=11,
            approver_id=61,
            action="DELEGATE",
            comment="委托给其他人",
            delegate_to=70,
        )

        action_log = self.mock_db.add.call_args[0][0]
        self.assertEqual(action_log.action, "DELEGATE")
        self.assertEqual(action_log.action_detail["delegate_to"], 70)

    def test_get_execution_history(self):
        """测试获取执行历史"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = ["log1", "log2", "log3"]

        result = self.logger.get_execution_history(300)

        self.assertEqual(len(result), 3)
        mock_query.order_by.assert_called_once()

    def test_get_approval_logs_all(self):
        """测试获取所有审批日志"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = ["log1", "log2"]

        result = self.logger.get_approval_logs(400)

        self.assertEqual(len(result), 2)

    def test_get_approval_logs_filtered_by_node(self):
        """测试按节点过滤审批日志"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = ["log1"]

        result = self.logger.get_approval_logs(401, node_id=20)

        self.assertEqual(len(result), 1)
        # filter 应该被调用两次：instance_id 和 node_id
        self.assertEqual(mock_query.filter.call_count, 2)

    def test_get_approval_logs_filtered_by_approver(self):
        """测试按审批人过滤审批日志"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = ["log1"]

        result = self.logger.get_approval_logs(402, approver_id=80)

        self.assertEqual(len(result), 1)
        self.assertEqual(mock_query.filter.call_count, 2)

    def test_get_approval_logs_filtered_by_both(self):
        """测试同时按节点和审批人过滤"""
        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []

        result = self.logger.get_approval_logs(403, node_id=21, approver_id=81)

        self.assertEqual(len(result), 0)
        self.assertEqual(mock_query.filter.call_count, 3)


class TestBatchOperationLogs(unittest.TestCase):
    """测试批量操作日志"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.logger = ApprovalExecutionLogger(self.mock_db)

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_batch_task_creation(self, mock_log):
        """测试批量任务创建日志"""
        mock_node = MagicMock()
        mock_node.id = 10
        mock_node.node_name = "并行审批节点"

        tasks = []
        for i in range(3):
            task = MagicMock()
            task.id = i + 1
            task.instance_id = 500
            task.assignee_id = 100 + i
            task.task_type = "APPROVAL"
            task.due_at = None
            tasks.append(task)

        self.logger.log_batch_task_creation(tasks, mock_node)

        # 验证批量日志
        call_args = mock_log.call_args_list[0]
        self.assertEqual(call_args.kwargs["context"]["task_count"], 3)

        # 验证每个任务都被记录
        self.assertEqual(self.mock_db.add.call_count, 3)

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_batch_task_creation_disabled_performance(self, mock_log):
        """测试性能日志禁用时的批量任务创建"""
        self.logger.log_performance = False

        mock_node = MagicMock()
        mock_node.id = 11
        mock_node.node_name = "节点"

        tasks = [MagicMock()]
        tasks[0].id = 1
        tasks[0].instance_id = 501
        tasks[0].assignee_id = 200
        tasks[0].task_type = "APPROVAL"
        tasks[0].due_at = None

        self.logger.log_batch_task_creation(tasks, mock_node)

        # 批量摘要日志不应该记录
        summary_logged = any(
            "批量任务创建" in str(call) for call in mock_log.call_args_list
        )
        self.assertFalse(summary_logged)

        # 单个任务日志仍然记录
        self.mock_db.add.assert_called_once()

    @patch("app.services.approval_engine.execution_logger.func")
    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_workflow_summary(self, mock_log, mock_func):
        """测试工作流摘要日志"""
        mock_instance = MagicMock()
        mock_instance.id = 600
        mock_instance.instance_no = "INS-600"
        mock_instance.status = "APPROVED"
        mock_instance.submitted_at = datetime.now() - timedelta(hours=5)

        # 模拟统计查询
        mock_stats = MagicMock()
        mock_stats.total_tasks = 10
        mock_stats.pending_tasks = 0
        mock_stats.approved_tasks = 8
        mock_stats.rejected_tasks = 2

        # Mock func.count 和 func.sum
        mock_func.count.return_value = MagicMock()
        mock_func.sum.return_value = MagicMock()
        mock_func.case.return_value = MagicMock()

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_stats

        self.logger.log_workflow_summary(mock_instance)

        call_args = mock_log.call_args
        self.assertEqual(call_args.kwargs["context"]["total_tasks"], 10)
        self.assertEqual(call_args.kwargs["context"]["approved_tasks"], 8)

    @patch("app.services.approval_engine.execution_logger.func")
    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_workflow_summary_no_submitted_at(self, mock_log, mock_func):
        """测试无提交时间的工作流摘要"""
        mock_instance = MagicMock()
        mock_instance.id = 601
        mock_instance.instance_no = "INS-601"
        mock_instance.status = "REJECTED"
        mock_instance.submitted_at = None

        mock_stats = MagicMock()
        mock_stats.total_tasks = 5
        mock_stats.pending_tasks = 1
        mock_stats.approved_tasks = 0
        mock_stats.rejected_tasks = 4

        # Mock func.count 和 func.sum
        mock_func.count.return_value = MagicMock()
        mock_func.sum.return_value = MagicMock()
        mock_func.case.return_value = MagicMock()

        mock_query = MagicMock()
        self.mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_stats

        self.logger.log_workflow_summary(mock_instance)

        call_args = mock_log.call_args
        self.assertEqual(call_args.kwargs["context"]["duration_hours"], 0)


class TestLogFlagControl(unittest.TestCase):
    """测试日志标志控制"""

    def setUp(self):
        self.mock_db = MagicMock()
        self.logger = ApprovalExecutionLogger(self.mock_db)

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_actions_disabled(self, mock_log):
        """测试禁用操作日志"""
        self.logger.log_actions = False

        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.instance_no = "INS-001"
        mock_instance.entity_type = "CONTRACT"
        mock_instance.entity_id = 100
        mock_instance.template_id = 10
        mock_instance.flow_id = 20
        mock_instance.status = "PENDING"

        mock_user = MagicMock()
        mock_user.id = 5
        mock_user.username = "test"
        mock_user.real_name = "Test"

        self.logger.log_instance_created(mock_instance, mock_user)

        # 结构化日志仍然记录
        mock_log.assert_called_once()
        # 但数据库日志不记录
        self.mock_db.add.assert_not_called()

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_routing_disabled(self, mock_log):
        """测试禁用路由日志"""
        self.logger.log_routing = False

        mock_instance = MagicMock()
        mock_instance.id = 2
        mock_instance.instance_no = "INS-002"

        self.logger.log_flow_selection(mock_instance, 10, "流程A")

        mock_log.assert_not_called()


if __name__ == "__main__":
    unittest.main()
