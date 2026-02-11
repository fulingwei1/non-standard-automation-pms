# -*- coding: utf-8 -*-
"""Tests for approval_engine/execution_logger.py"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime


class TestApprovalExecutionLogger:
    def setup_method(self):
        self.db = MagicMock()
        with patch("app.services.approval_engine.execution_logger.get_logger"):
            from app.services.approval_engine.execution_logger import ApprovalExecutionLogger
            self.logger = ApprovalExecutionLogger(self.db)

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_instance_created(self, mock_log):
        instance = MagicMock(id=1, instance_no="INS-001", entity_type="PROJECT",
                             entity_id=10, template_id=1, flow_id=1, status="PENDING")
        user = MagicMock(id=1, username="admin", real_name="管理员")
        self.logger.log_instance_created(instance, user)
        mock_log.assert_called_once()
        self.db.add.assert_called_once()
        self.db.commit.assert_called_once()

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_instance_status_change(self, mock_log):
        instance = MagicMock(id=1, instance_no="INS-001")
        self.logger.log_instance_status_change(instance, "PENDING", "APPROVED")
        mock_log.assert_called_once()

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_task_completed(self, mock_log):
        task = MagicMock(id=1, instance_id=1, node_id=1, assignee_id=2)
        user = MagicMock(id=2, username="user1", real_name="用户1")
        self.logger.log_task_completed(task, user, "APPROVED", "同意")
        mock_log.assert_called_once()
        self.db.add.assert_called()

    @patch("app.services.approval_engine.execution_logger.log_warning_with_context")
    def test_log_task_timeout(self, mock_log):
        task = MagicMock(id=1, instance_id=1, node_id=1, assignee_id=2, due_at=None)
        self.logger.log_task_timeout(task, "AUTO_APPROVE")
        mock_log.assert_called_once()

    def test_log_execution_simplified(self):
        self.logger.log_execution(instance_id=1, action="SUBMIT", actor_id=1)
        self.db.add.assert_called()

    def test_get_execution_history(self):
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = self.logger.get_execution_history(1)
        assert result == []

    def test_get_approval_logs_with_filters(self):
        self.db.query.return_value.filter.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = self.logger.get_approval_logs(1, node_id=1, approver_id=2)
        assert result == []

    def test_log_node_transition_with_ids(self):
        self.logger.log_node_transition(instance_id=1, from_node_id=1, to_node_id=2, trigger="AUTO")
        self.db.add.assert_called()

    def test_create_action_log_exception_handled(self):
        self.db.add.side_effect = Exception("DB error")
        # Should not raise
        self.logger._create_action_log(instance_id=1, operator_id=1, operator_name="test", action="TEST")

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_flow_selection(self, mock_log):
        instance = MagicMock(id=1, instance_no="INS-001")
        self.logger.log_flow_selection(instance, flow_id=1, flow_name="默认流程")
        mock_log.assert_called_once()

    @patch("app.services.approval_engine.execution_logger.log_info_with_context")
    def test_log_performance_metric(self, mock_log):
        instance = MagicMock(id=1, instance_no="INS-001")
        self.logger.log_performance_metric(instance, "processing_time", 150.0, "ms")
        mock_log.assert_called_once()
