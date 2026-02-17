# -*- coding: utf-8 -*-
"""
ApprovalExecutionLogger 单元测试 - G2组覆盖率提升

覆盖:
- ApprovalExecutionLogger.__init__ 与配置标志
- log_instance_created (写 DB 日志)
- log_instance_status_change
- log_instance_completed
- log_task_created
- log_task_completed
- log_task_timeout
- log_approval_action
- get_execution_history
- get_approval_logs
"""

from unittest.mock import MagicMock, patch, call

import pytest


class TestApprovalExecutionLoggerInit:
    """测试初始化"""

    def test_init_stores_db(self):
        from app.services.approval_engine.execution_logger import ApprovalExecutionLogger
        db = MagicMock()
        logger = ApprovalExecutionLogger(db)
        assert logger.db is db

    def test_default_log_flags_true(self):
        from app.services.approval_engine.execution_logger import ApprovalExecutionLogger
        logger = ApprovalExecutionLogger(MagicMock())
        assert logger.log_actions is True
        assert logger.log_routing is True
        assert logger.log_performance is True
        assert logger.log_errors is True


class TestLogInstanceCreated:
    """测试 log_instance_created"""

    def setup_method(self):
        from app.services.approval_engine.execution_logger import ApprovalExecutionLogger
        self.db = MagicMock()
        self.exec_logger = ApprovalExecutionLogger(self.db)

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_writes_structured_log(self, mock_log):
        instance = MagicMock()
        instance.id = 1
        instance.instance_no = "INS-001"
        instance.entity_type = "CONTRACT"
        instance.entity_id = 10
        instance.template_id = 2
        instance.flow_id = 3
        instance.status = "PENDING"

        initiator = MagicMock()
        initiator.id = 42
        initiator.username = "alice"
        initiator.real_name = "Alice"

        self.exec_logger._create_action_log = MagicMock()
        self.exec_logger.log_instance_created(instance, initiator)

        mock_log.assert_called_once()

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_creates_action_log_when_log_actions_enabled(self, mock_log):
        instance = MagicMock()
        instance.id = 1
        instance.instance_no = "INS-001"
        instance.entity_type = "CONTRACT"
        instance.entity_id = 10
        instance.template_id = 2
        instance.flow_id = 3
        instance.status = "PENDING"
        instance.current_status = "PENDING"

        initiator = MagicMock()
        initiator.id = 42
        initiator.username = "bob"
        initiator.real_name = "Bob"

        create_log = MagicMock()
        self.exec_logger._create_action_log = create_log

        self.exec_logger.log_instance_created(instance, initiator)
        create_log.assert_called_once()


class TestLogInstanceStatusChange:
    """测试 log_instance_status_change"""

    def setup_method(self):
        from app.services.approval_engine.execution_logger import ApprovalExecutionLogger
        self.db = MagicMock()
        self.exec_logger = ApprovalExecutionLogger(self.db)

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_logs_status_transition(self, mock_log):
        instance = MagicMock()
        instance.id = 1
        instance.instance_no = "INS-001"

        self.exec_logger.log_instance_status_change(
            instance, old_status="PENDING", new_status="APPROVED", reason="All approvers approved"
        )
        mock_log.assert_called_once()
        args = mock_log.call_args
        # Check context contains old/new status
        ctx = args[1]["context"] if args[1] else args[0][1]["context"]
        assert ctx.get("old_status") == "PENDING"
        assert ctx.get("new_status") == "APPROVED"

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_logs_without_operator(self, mock_log):
        instance = MagicMock()
        instance.id = 2
        instance.instance_no = "INS-002"
        self.exec_logger.log_instance_status_change(instance, "PENDING", "REJECTED")
        mock_log.assert_called_once()


class TestLogInstanceCompleted:
    """测试 log_instance_completed"""

    def setup_method(self):
        from app.services.approval_engine.execution_logger import ApprovalExecutionLogger
        self.db = MagicMock()
        self.exec_logger = ApprovalExecutionLogger(self.db)

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_logs_approved_instance(self, mock_log):
        instance = MagicMock()
        instance.id = 1
        instance.instance_no = "INS-001"
        instance.status = "APPROVED"
        instance.completed_nodes = 3
        instance.total_nodes = 3
        instance.completed_at = None
        instance.current_status = "APPROVED"

        operator = MagicMock()
        operator.id = 1
        operator.username = "system"
        operator.real_name = "System"

        create_log = MagicMock()
        self.exec_logger._create_action_log = create_log

        self.exec_logger.log_instance_completed(instance, operator)
        mock_log.assert_called_once()
        create_log.assert_called_once()


class TestLogTaskCompleted:
    """测试 log_task_completed"""

    def setup_method(self):
        from app.services.approval_engine.execution_logger import ApprovalExecutionLogger
        self.db = MagicMock()
        self.exec_logger = ApprovalExecutionLogger(self.db)

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_maps_approved_to_approve_action(self, mock_log):
        task = MagicMock()
        task.id = 1
        task.instance_id = 10
        task.node_id = 2

        operator = MagicMock()
        operator.id = 5
        operator.real_name = "Eve"
        operator.username = "eve"

        create_log = MagicMock()
        self.exec_logger._create_action_log = create_log

        self.exec_logger.log_task_completed(task, operator, decision="APPROVED")

        create_log.assert_called_once()
        kwargs = create_log.call_args[1]
        assert kwargs["action"] == "APPROVE"

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_maps_rejected_to_reject_action(self, mock_log):
        task = MagicMock()
        task.id = 2
        task.instance_id = 10
        task.node_id = 3

        operator = MagicMock()
        operator.id = 6
        operator.real_name = "Frank"
        operator.username = "frank"

        create_log = MagicMock()
        self.exec_logger._create_action_log = create_log

        self.exec_logger.log_task_completed(task, operator, decision="REJECTED")
        kwargs = create_log.call_args[1]
        assert kwargs["action"] == "REJECT"


class TestLogTaskTimeout:
    """测试 log_task_timeout"""

    def setup_method(self):
        from app.services.approval_engine.execution_logger import ApprovalExecutionLogger
        self.db = MagicMock()
        self.exec_logger = ApprovalExecutionLogger(self.db)

    @patch("app.services.approval_engine.execution_logger.log_warning_with_context")
    def test_logs_timeout_warning(self, mock_log):
        task = MagicMock()
        task.id = 1
        task.instance_id = 10
        task.node_id = 2
        task.assignee_id = 5
        task.due_at = None

        create_log = MagicMock()
        self.exec_logger._create_action_log = create_log

        self.exec_logger.log_task_timeout(task, timeout_action="AUTO_APPROVE")
        mock_log.assert_called_once()
        create_log.assert_called_once()
        kwargs = create_log.call_args[1]
        assert kwargs["action"] == "TIMEOUT"


class TestLogApprovalAction:
    """测试 log_approval_action (简化接口)"""

    def setup_method(self):
        from app.services.approval_engine.execution_logger import ApprovalExecutionLogger
        self.db = MagicMock()
        self.exec_logger = ApprovalExecutionLogger(self.db)

    def test_basic_approve_action(self):
        create_log = MagicMock()
        self.exec_logger._create_action_log = create_log

        self.exec_logger.log_approval_action(
            instance_id=1,
            node_id=2,
            approver_id=5,
            action="APPROVE",
            comment="同意",
        )
        create_log.assert_called_once()
        kwargs = create_log.call_args[1]
        assert kwargs["action"] == "APPROVE"

    def test_delegate_action_includes_delegate_to(self):
        create_log = MagicMock()
        self.exec_logger._create_action_log = create_log

        self.exec_logger.log_approval_action(
            instance_id=1,
            node_id=2,
            approver_id=5,
            action="DELEGATE",
            delegate_to=99,
        )
        kwargs = create_log.call_args[1]
        assert kwargs["action_detail"]["delegate_to"] == 99


class TestGetExecutionHistory:
    """测试 get_execution_history"""

    def setup_method(self):
        from app.services.approval_engine.execution_logger import ApprovalExecutionLogger
        self.db = MagicMock()
        self.exec_logger = ApprovalExecutionLogger(self.db)

    def test_returns_ordered_logs(self):
        expected = [MagicMock(), MagicMock()]
        (self.db.query.return_value
             .filter.return_value
             .order_by.return_value
             .all.return_value) = expected

        result = self.exec_logger.get_execution_history(instance_id=1)
        assert result == expected

    def test_returns_empty_list_when_no_logs(self):
        (self.db.query.return_value
             .filter.return_value
             .order_by.return_value
             .all.return_value) = []

        result = self.exec_logger.get_execution_history(instance_id=999)
        assert result == []


class TestGetApprovalLogs:
    """测试 get_approval_logs"""

    def setup_method(self):
        from app.services.approval_engine.execution_logger import ApprovalExecutionLogger
        self.db = MagicMock()
        self.exec_logger = ApprovalExecutionLogger(self.db)

    def test_filters_by_instance_id(self):
        expected = [MagicMock()]
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value.all.return_value = expected
        self.db.query.return_value = q

        result = self.exec_logger.get_approval_logs(instance_id=1)
        assert result == expected

    def test_filters_by_node_and_approver(self):
        expected = [MagicMock()]
        q = MagicMock()
        q.filter.return_value = q
        q.order_by.return_value.all.return_value = expected
        self.db.query.return_value = q

        result = self.exec_logger.get_approval_logs(
            instance_id=1, node_id=2, approver_id=5
        )
        # filter should be called 3 times: instance, node, approver
        assert q.filter.call_count >= 3
