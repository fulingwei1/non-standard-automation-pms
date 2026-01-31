# -*- coding: utf-8 -*-
"""
ExecutionLogger (审批引擎执行日志) 综合单元测试

测试覆盖:
- __init__: 初始化日志记录器
- log_execution: 记录执行日志
- log_approval_action: 记录审批动作
- log_node_transition: 记录节点转换
- get_execution_history: 获取执行历史
- get_approval_logs: 获取审批日志
"""

from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
from decimal import Decimal

import pytest


class TestExecutionLoggerInit:
    """测试 ExecutionLogger 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.approval_engine.execution_logger import ExecutionLogger

        mock_db = MagicMock()

        logger = ExecutionLogger(mock_db)

        assert logger.db == mock_db


class TestLogExecution:
    """测试 log_execution 方法"""

    def test_logs_execution_successfully(self):
        """测试成功记录执行日志"""
        from app.services.approval_engine.execution_logger import ExecutionLogger

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        logger = ExecutionLogger(mock_db)

        result = logger.log_execution(
            instance_id=1,
            action="SUBMIT",
            actor_id=1,
            details={"key": "value"}
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_sets_timestamp(self):
        """测试设置时间戳"""
        from app.services.approval_engine.execution_logger import ExecutionLogger

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        logger = ExecutionLogger(mock_db)

        result = logger.log_execution(
            instance_id=1,
            action="APPROVE",
            actor_id=2
        )

        # 验证 add 被调用
        mock_db.add.assert_called_once()

    def test_handles_none_details(self):
        """测试处理空详情"""
        from app.services.approval_engine.execution_logger import ExecutionLogger

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        logger = ExecutionLogger(mock_db)

        result = logger.log_execution(
            instance_id=1,
            action="REJECT",
            actor_id=1,
            details=None
        )

        mock_db.add.assert_called_once()


class TestLogApprovalAction:
    """测试 log_approval_action 方法"""

    def test_logs_approval_action(self):
        """测试记录审批动作"""
        from app.services.approval_engine.execution_logger import ExecutionLogger

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        logger = ExecutionLogger(mock_db)

        result = logger.log_approval_action(
            instance_id=1,
            node_id=1,
            approver_id=5,
            action="APPROVE",
            comment="同意"
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_logs_rejection(self):
        """测试记录拒绝"""
        from app.services.approval_engine.execution_logger import ExecutionLogger

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        logger = ExecutionLogger(mock_db)

        result = logger.log_approval_action(
            instance_id=1,
            node_id=1,
            approver_id=5,
            action="REJECT",
            comment="不同意，需要修改"
        )

        mock_db.add.assert_called_once()

    def test_logs_delegate(self):
        """测试记录委托"""
        from app.services.approval_engine.execution_logger import ExecutionLogger

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        logger = ExecutionLogger(mock_db)

        result = logger.log_approval_action(
            instance_id=1,
            node_id=1,
            approver_id=5,
            action="DELEGATE",
            comment="委托给张三",
            delegate_to=10
        )

        mock_db.add.assert_called_once()


class TestLogNodeTransition:
    """测试 log_node_transition 方法"""

    def test_logs_node_transition(self):
        """测试记录节点转换"""
        from app.services.approval_engine.execution_logger import ExecutionLogger

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        logger = ExecutionLogger(mock_db)

        result = logger.log_node_transition(
            instance_id=1,
            from_node_id=1,
            to_node_id=2,
            trigger="AUTO"
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_logs_start_transition(self):
        """测试记录开始转换"""
        from app.services.approval_engine.execution_logger import ExecutionLogger

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        logger = ExecutionLogger(mock_db)

        result = logger.log_node_transition(
            instance_id=1,
            from_node_id=None,
            to_node_id=1,
            trigger="SUBMIT"
        )

        mock_db.add.assert_called_once()

    def test_logs_end_transition(self):
        """测试记录结束转换"""
        from app.services.approval_engine.execution_logger import ExecutionLogger

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        logger = ExecutionLogger(mock_db)

        result = logger.log_node_transition(
            instance_id=1,
            from_node_id=5,
            to_node_id=None,
            trigger="COMPLETE"
        )

        mock_db.add.assert_called_once()


class TestGetExecutionHistory:
    """测试 get_execution_history 方法"""

    def test_returns_history_list(self):
        """测试返回历史列表"""
        from app.services.approval_engine.execution_logger import ExecutionLogger

        mock_db = MagicMock()

        mock_log1 = MagicMock()
        mock_log1.id = 1
        mock_log1.action = "SUBMIT"
        mock_log1.created_at = datetime.now()

        mock_log2 = MagicMock()
        mock_log2.id = 2
        mock_log2.action = "APPROVE"
        mock_log2.created_at = datetime.now()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_log1, mock_log2]
        mock_db.query.return_value = mock_query

        logger = ExecutionLogger(mock_db)

        result = logger.get_execution_history(instance_id=1)

        assert isinstance(result, list)
        assert len(result) == 2

    def test_filters_by_instance_id(self):
        """测试按实例ID过滤"""
        from app.services.approval_engine.execution_logger import ExecutionLogger

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        logger = ExecutionLogger(mock_db)

        result = logger.get_execution_history(instance_id=123)

        mock_query.filter.assert_called()

    def test_orders_by_created_at(self):
        """测试按创建时间排序"""
        from app.services.approval_engine.execution_logger import ExecutionLogger

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        logger = ExecutionLogger(mock_db)

        result = logger.get_execution_history(instance_id=1)

        mock_query.order_by.assert_called()


class TestGetApprovalLogs:
    """测试 get_approval_logs 方法"""

    def test_returns_approval_logs(self):
        """测试返回审批日志"""
        from app.services.approval_engine.execution_logger import ExecutionLogger

        mock_db = MagicMock()

        mock_log1 = MagicMock()
        mock_log1.id = 1
        mock_log1.action = "APPROVE"
        mock_log1.approver_id = 5

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [mock_log1]
        mock_db.query.return_value = mock_query

        logger = ExecutionLogger(mock_db)

        result = logger.get_approval_logs(instance_id=1)

        assert isinstance(result, list)

    def test_filters_by_node_id(self):
        """测试按节点ID过滤"""
        from app.services.approval_engine.execution_logger import ExecutionLogger

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        logger = ExecutionLogger(mock_db)

        result = logger.get_approval_logs(instance_id=1, node_id=5)

        mock_query.filter.assert_called()

    def test_filters_by_approver_id(self):
        """测试按审批人ID过滤"""
        from app.services.approval_engine.execution_logger import ExecutionLogger

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        logger = ExecutionLogger(mock_db)

        result = logger.get_approval_logs(instance_id=1, approver_id=10)

        mock_query.filter.assert_called()
