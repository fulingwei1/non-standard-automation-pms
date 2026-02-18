# -*- coding: utf-8 -*-
"""第九批: test_execution_logger_cov9.py - ApprovalExecutionLogger 单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

pytest.importorskip("app.services.approval_engine.execution_logger")

from app.services.approval_engine.execution_logger import ApprovalExecutionLogger


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def logger_obj(mock_db):
    return ApprovalExecutionLogger(db=mock_db)


def make_instance(id=1, instance_no="I-001", entity_type="ECN", entity_id=100, template_id=10):
    inst = MagicMock()
    inst.id = id
    inst.instance_no = instance_no
    inst.entity_type = entity_type
    inst.entity_id = entity_id
    inst.template_id = template_id
    inst.status = "PENDING"
    inst.current_node_id = 5
    return inst


def make_task(id=1, task_no="T-001"):
    task = MagicMock()
    task.id = id
    task.task_no = task_no
    task.node_id = 5
    task.instance_id = 1
    task.node_code = "N001"
    task.assignee_id = 10
    task.status = "PENDING"
    return task


def make_node():
    node = MagicMock()
    node.id = 5
    node.node_code = "N001"
    return node


def make_user(id=1, name="测试用户"):
    user = MagicMock()
    user.id = id
    user.full_name = name
    user.real_name = name
    user.username = "test_user"
    return user


class TestApprovalExecutionLoggerInit:
    """测试初始化"""

    def test_init_sets_db(self, logger_obj, mock_db):
        assert logger_obj.db is mock_db

    def test_init_log_flags(self, logger_obj):
        assert logger_obj.log_actions is True
        assert logger_obj.log_routing is True
        assert logger_obj.log_performance is True
        assert logger_obj.log_errors is True


class TestLogInstanceCreated:
    """测试实例创建日志"""

    def test_log_instance_created_basic(self, logger_obj, mock_db):
        instance = make_instance()
        initiator = make_user()
        logger_obj.log_instance_created(instance, initiator)

    def test_log_instance_created_with_context(self, logger_obj, mock_db):
        instance = make_instance()
        initiator = make_user()
        ctx = {"source": "api", "ip": "127.0.0.1"}
        logger_obj.log_instance_created(instance, initiator, context=ctx)


class TestLogTaskCompleted:
    """测试任务完成日志"""

    def test_log_task_completed(self, logger_obj, mock_db):
        task = make_task()
        operator = make_user()
        # Signature: log_task_completed(self, task, operator, decision, comment=None)
        logger_obj.log_task_completed(task, operator, "APPROVED")

    def test_log_task_completed_with_comment(self, logger_obj, mock_db):
        task = make_task()
        operator = make_user()
        logger_obj.log_task_completed(task, operator, "REJECTED", comment="不符合规范")

    def test_log_task_timeout(self, logger_obj, mock_db):
        instance = make_instance()
        task = make_task()
        logger_obj.log_task_timeout(instance, task)


class TestLogFlowSelection:
    """测试路由日志"""

    def test_log_flow_selection(self, logger_obj, mock_db):
        instance = make_instance()
        # Signature: log_flow_selection(self, instance, flow_id, flow_name, routing_rule=None, condition=None)
        logger_obj.log_flow_selection(instance, flow_id=1, flow_name="主审批流程")


class TestLogConditionEvaluation:
    """测试条件评估日志"""

    def test_log_condition_evaluation_matched(self, logger_obj, mock_db):
        node = make_node()
        instance = make_instance()
        # Signature: log_condition_evaluation(self, node, instance, expression, result, matched=False)
        logger_obj.log_condition_evaluation(node, instance, "amount > 10000", True, matched=True)

    def test_log_condition_evaluation_not_matched(self, logger_obj, mock_db):
        node = make_node()
        instance = make_instance()
        logger_obj.log_condition_evaluation(node, instance, "amount > 50000", False, matched=False)


class TestLogError:
    """测试错误日志"""

    def test_log_error(self, logger_obj, mock_db):
        instance = make_instance()
        exc = ValueError("测试异常")
        # Signature: log_error(self, instance, error, operation, context=None)
        logger_obj.log_error(instance, exc, operation="routing", context={"step": "node"})

    def test_log_error_no_instance(self, logger_obj, mock_db):
        exc = RuntimeError("未知错误")
        logger_obj.log_error(None, exc, operation="startup")


class TestGetExecutionHistory:
    """测试获取执行历史"""

    def test_get_execution_history(self, logger_obj, mock_db):
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = logger_obj.get_execution_history(instance_id=1)
        assert isinstance(result, list)

    def test_get_approval_logs(self, logger_obj, mock_db):
        # get_approval_logs applies filter twice when node_id given
        chain = MagicMock()
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.all.return_value = []
        mock_db.query.return_value = chain
        result = logger_obj.get_approval_logs(instance_id=1, node_id=5)
        assert isinstance(result, list)
