# -*- coding: utf-8 -*-
"""
WorkflowEngine 和 ApprovalRouter 综合单元测试

测试覆盖:
- WorkflowEngine.__init__: 初始化工作流引擎
- WorkflowEngine.create_instance: 创建审批实例
- WorkflowEngine.get_current_node: 获取当前待审批节点
- WorkflowEngine.evaluate_node_conditions: 评估节点条件
- WorkflowEngine.submit_approval: 提交审批决策
- WorkflowEngine._update_instance_status: 更新实例状态
- WorkflowEngine._find_next_node: 查找下一个节点
- WorkflowEngine._find_previous_node: 查找上一个节点
- WorkflowEngine.is_expired: 检查实例是否超时
- ApprovalRouter.__init__: 初始化审批路由器
- ApprovalRouter.get_approval_flow: 获取审批流程
- ApprovalRouter.determine_approval_flow: 决定使用哪个审批流程
"""

from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
from decimal import Decimal

import pytest


class TestWorkflowEngineInit:
    """测试 WorkflowEngine 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        mock_db = MagicMock()

        engine = WorkflowEngine(mock_db)

        assert engine.db == mock_db


class TestCreateInstance:
    """测试 create_instance 方法"""

    def test_creates_instance_successfully(self):
        """测试成功创建审批实例"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        mock_db = MagicMock()

        mock_flow = MagicMock()
        mock_flow.id = 1
        mock_flow.flow_code = "TEST_FLOW"
        mock_flow.nodes = [MagicMock(), MagicMock()]

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_flow
        mock_db.query.return_value = mock_query
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.refresh = MagicMock()

        engine = WorkflowEngine(mock_db)

        result = engine.create_instance(
            flow_code="TEST_FLOW",
            business_type="TEST",
            business_id=1,
            business_title="测试审批",
            submitted_by=1
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_raises_for_missing_flow(self):
        """测试流程不存在时抛出异常"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        engine = WorkflowEngine(mock_db)

        with pytest.raises(ValueError) as exc_info:
            engine.create_instance(
                flow_code="NONEXISTENT",
                business_type="TEST",
                business_id=1,
                business_title="测试",
                submitted_by=1
            )

        assert "不存在或未启用" in str(exc_info.value)


class TestGetCurrentNode:
    """测试 get_current_node 方法"""

    def test_returns_none_for_completed_status(self):
        """测试已完成状态返回None"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        from app.services.approval_engine.models import ApprovalStatus

        mock_db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.current_status = ApprovalStatus.APPROVED.value

        engine = WorkflowEngine(mock_db)

        result = engine.get_current_node(mock_instance)

        assert result is None

    def test_returns_first_node_when_no_current(self):
        """测试无当前节点时返回第一个节点"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        from app.services.approval_engine.models import ApprovalStatus

        mock_db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.current_status = ApprovalStatus.PENDING.value
        mock_instance.current_node_id = None
        mock_instance.flow_id = 1

        mock_node = MagicMock()
        mock_node.id = 1
        mock_node.sequence = 1

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_node
        mock_db.query.return_value = mock_query

        engine = WorkflowEngine(mock_db)

        result = engine.get_current_node(mock_instance)

        assert result == mock_node

    def test_returns_next_node_when_has_current(self):
        """测试有当前节点时返回下一个节点"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        from app.services.approval_engine.models import ApprovalStatus

        mock_db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.current_status = ApprovalStatus.IN_PROGRESS.value
        mock_instance.current_node_id = 1
        mock_instance.flow_id = 1

        mock_current_node = MagicMock()
        mock_current_node.id = 1
        mock_current_node.sequence = 1

        mock_next_node = MagicMock()
        mock_next_node.id = 2
        mock_next_node.sequence = 2

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.side_effect = [mock_current_node, mock_next_node]
        mock_db.query.return_value = mock_query

        engine = WorkflowEngine(mock_db)

        result = engine.get_current_node(mock_instance)

        assert result == mock_next_node


class TestEvaluateNodeConditions:
    """测试 evaluate_node_conditions 方法"""

    def test_returns_true_for_no_condition(self):
        """测试无条件时返回True"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        mock_db = MagicMock()

        mock_node = MagicMock()
        mock_node.condition_expression = None

        mock_instance = MagicMock()

        engine = WorkflowEngine(mock_db)

        result = engine.evaluate_node_conditions(mock_node, mock_instance)

        assert result is True

    def test_returns_true_for_empty_condition(self):
        """测试空条件时返回True"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        mock_db = MagicMock()

        mock_node = MagicMock()
        mock_node.condition_expression = ""

        mock_instance = MagicMock()

        engine = WorkflowEngine(mock_db)

        result = engine.evaluate_node_conditions(mock_node, mock_instance)

        assert result is True


class TestSubmitApproval:
    """测试 submit_approval 方法"""

    def test_submits_approval_successfully(self):
        """测试成功提交审批"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        from app.services.approval_engine.models import ApprovalNodeRole

        mock_db = MagicMock()

        mock_node = MagicMock()
        mock_node.id = 1
        mock_node.role_type = ApprovalNodeRole.USER.value
        mock_node.condition_expression = None

        mock_instance = MagicMock()
        mock_instance.id = 1

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        engine = WorkflowEngine(mock_db)
        engine.get_current_node = MagicMock(return_value=mock_node)
        engine._get_approver_name = MagicMock(return_value="张三")
        engine._get_approver_role = MagicMock(return_value="用户")
        engine._update_instance_status = MagicMock()

        result = engine.submit_approval(
            instance=mock_instance,
            approver_id=1,
            decision="APPROVED",
            comment="同意"
        )

        mock_db.add.assert_called()
        mock_db.commit.assert_called()

    def test_raises_for_no_node(self):
        """测试无可审批节点时抛出异常"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        mock_db = MagicMock()

        mock_instance = MagicMock()

        engine = WorkflowEngine(mock_db)
        engine.get_current_node = MagicMock(return_value=None)

        with pytest.raises(ValueError) as exc_info:
            engine.submit_approval(
                instance=mock_instance,
                approver_id=1,
                decision="APPROVED"
            )

        assert "没有可审批的节点" in str(exc_info.value)


class TestGetApproverName:
    """测试 _get_approver_name 方法"""

    def test_returns_real_name(self):
        """测试返回真实姓名"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        mock_db = MagicMock()

        mock_user = MagicMock()
        mock_user.real_name = "张三"
        mock_user.username = "zhangsan"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        engine = WorkflowEngine(mock_db)

        result = engine._get_approver_name(1)

        assert result == "张三"

    def test_returns_username_when_no_real_name(self):
        """测试无真实姓名时返回用户名"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        mock_db = MagicMock()

        mock_user = MagicMock()
        mock_user.real_name = None
        mock_user.username = "zhangsan"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        engine = WorkflowEngine(mock_db)

        result = engine._get_approver_name(1)

        assert result == "zhangsan"

    def test_returns_fallback_when_no_user(self):
        """测试用户不存在时返回默认值"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        engine = WorkflowEngine(mock_db)

        result = engine._get_approver_name(999)

        assert result == "User_999"


class TestGetApproverRole:
    """测试 _get_approver_role 方法"""

    def test_returns_user_role(self):
        """测试返回用户角色"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        from app.services.approval_engine.models import ApprovalNodeRole

        mock_db = MagicMock()

        mock_node = MagicMock()
        mock_node.role_type = ApprovalNodeRole.USER.value

        engine = WorkflowEngine(mock_db)

        result = engine._get_approver_role(mock_node)

        assert result == "用户"

    def test_returns_role_role(self):
        """测试返回角色类型"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        from app.services.approval_engine.models import ApprovalNodeRole

        mock_db = MagicMock()

        mock_node = MagicMock()
        mock_node.role_type = ApprovalNodeRole.ROLE.value

        engine = WorkflowEngine(mock_db)

        result = engine._get_approver_role(mock_node)

        assert result == "角色"

    def test_returns_department_role(self):
        """测试返回部门类型"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        from app.services.approval_engine.models import ApprovalNodeRole

        mock_db = MagicMock()

        mock_node = MagicMock()
        mock_node.role_type = ApprovalNodeRole.DEPARTMENT.value

        engine = WorkflowEngine(mock_db)

        result = engine._get_approver_role(mock_node)

        assert result == "部门"


class TestUpdateInstanceStatus:
    """测试 _update_instance_status 方法"""

    def test_updates_to_approved_when_no_next_node(self):
        """测试无下一节点时更新为已批准"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        from app.services.approval_engine.models import ApprovalStatus, ApprovalDecision

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        mock_flow = MagicMock()
        mock_flow.total_nodes = 2

        mock_instance = MagicMock()
        mock_instance.flow = mock_flow
        mock_instance.current_status = ApprovalStatus.IN_PROGRESS.value

        mock_record = MagicMock()
        mock_record.decision = ApprovalDecision.APPROVED
        mock_record.node = MagicMock()

        engine = WorkflowEngine(mock_db)
        engine._find_next_node = MagicMock(return_value=None)

        engine._update_instance_status(mock_instance, mock_record)

        assert mock_instance.current_status == ApprovalStatus.APPROVED.value

    def test_moves_to_next_node_when_approved(self):
        """测试批准时移动到下一节点"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        from app.services.approval_engine.models import ApprovalStatus, ApprovalDecision

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        mock_flow = MagicMock()
        mock_flow.total_nodes = 3

        mock_instance = MagicMock()
        mock_instance.flow = mock_flow
        mock_instance.current_status = ApprovalStatus.PENDING.value
        mock_instance.completed_nodes = 0

        mock_next_node = MagicMock()
        mock_next_node.id = 2

        mock_record = MagicMock()
        mock_record.decision = ApprovalDecision.APPROVED
        mock_record.node = MagicMock()

        engine = WorkflowEngine(mock_db)
        engine._find_next_node = MagicMock(return_value=mock_next_node)

        engine._update_instance_status(mock_instance, mock_record)

        assert mock_instance.current_node_id == 2
        assert mock_instance.completed_nodes == 1

    def test_updates_to_rejected(self):
        """测试更新为已拒绝"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        from app.services.approval_engine.models import ApprovalStatus, ApprovalDecision

        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        mock_flow = MagicMock()

        mock_instance = MagicMock()
        mock_instance.flow = mock_flow
        mock_instance.current_status = ApprovalStatus.IN_PROGRESS.value

        mock_record = MagicMock()
        mock_record.decision = ApprovalDecision.REJECTED
        mock_record.node = MagicMock()

        engine = WorkflowEngine(mock_db)
        engine._find_previous_node = MagicMock(return_value=None)

        engine._update_instance_status(mock_instance, mock_record)

        assert mock_instance.current_status == ApprovalStatus.REJECTED.value


class TestFindNextNode:
    """测试 _find_next_node 方法"""

    def test_finds_next_node(self):
        """测试查找下一节点"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        mock_db = MagicMock()

        mock_next_node = MagicMock()
        mock_next_node.id = 2
        mock_next_node.sequence = 2

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_next_node
        mock_db.query.return_value = mock_query

        mock_instance = MagicMock()
        mock_instance.flow_id = 1

        mock_current_node = MagicMock()
        mock_current_node.sequence = 1

        engine = WorkflowEngine(mock_db)

        result = engine._find_next_node(mock_instance, mock_current_node)

        assert result == mock_next_node

    def test_returns_none_when_no_next(self):
        """测试无下一节点时返回None"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        mock_instance = MagicMock()
        mock_instance.flow_id = 1

        mock_current_node = MagicMock()
        mock_current_node.sequence = 10

        engine = WorkflowEngine(mock_db)

        result = engine._find_next_node(mock_instance, mock_current_node)

        assert result is None


class TestFindPreviousNode:
    """测试 _find_previous_node 方法"""

    def test_finds_previous_node(self):
        """测试查找上一节点"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        mock_db = MagicMock()

        mock_prev_node = MagicMock()
        mock_prev_node.id = 1
        mock_prev_node.sequence = 1

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = mock_prev_node
        mock_db.query.return_value = mock_query

        mock_instance = MagicMock()
        mock_instance.flow_id = 1

        mock_current_node = MagicMock()
        mock_current_node.sequence = 2

        engine = WorkflowEngine(mock_db)

        result = engine._find_previous_node(mock_instance, mock_current_node)

        assert result == mock_prev_node

    def test_returns_none_when_no_previous(self):
        """测试无上一节点时返回None"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        mock_db = MagicMock()

        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        mock_instance = MagicMock()
        mock_instance.flow_id = 1

        mock_current_node = MagicMock()
        mock_current_node.sequence = 1

        engine = WorkflowEngine(mock_db)

        result = engine._find_previous_node(mock_instance, mock_current_node)

        assert result is None


class TestIsExpired:
    """测试 is_expired 方法"""

    def test_returns_false_when_no_due_date(self):
        """测试无截止日期时返回False"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        mock_db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.due_date = None

        engine = WorkflowEngine(mock_db)

        result = engine.is_expired(mock_instance)

        assert result is False

    def test_returns_true_when_expired(self):
        """测试已过期时返回True"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        mock_db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.due_date = datetime.now() - timedelta(hours=1)

        engine = WorkflowEngine(mock_db)

        result = engine.is_expired(mock_instance)

        assert result is True

    def test_returns_false_when_not_expired(self):
        """测试未过期时返回False"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        mock_db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.due_date = datetime.now() + timedelta(hours=24)

        engine = WorkflowEngine(mock_db)

        result = engine.is_expired(mock_instance)

        assert result is False


class TestApprovalRouterInit:
    """测试 ApprovalRouter 初始化"""

    def test_initializes_with_db(self):
        """测试使用数据库会话初始化"""
        from app.services.approval_engine.workflow_engine import ApprovalRouter

        mock_db = MagicMock()

        router = ApprovalRouter(mock_db)

        assert router.db == mock_db


class TestGetApprovalFlow:
    """测试 get_approval_flow 方法"""

    def test_returns_flow(self):
        """测试返回审批流程"""
        from app.services.approval_engine.workflow_engine import ApprovalRouter

        mock_db = MagicMock()

        mock_flow = MagicMock()
        mock_flow.id = 1
        mock_flow.flow_code = "TEST_FLOW"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_flow

        router = ApprovalRouter(mock_db)

        result = router.get_approval_flow("TEST_TYPE")

        assert result == mock_flow

    def test_returns_none_when_not_found(self):
        """测试未找到时返回None"""
        from app.services.approval_engine.workflow_engine import ApprovalRouter

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        router = ApprovalRouter(mock_db)

        result = router.get_approval_flow("NONEXISTENT")

        assert result is None


class TestDetermineApprovalFlow:
    """测试 determine_approval_flow 方法"""

    def test_returns_ecn_standard_for_ecn(self):
        """测试ECN返回标准流程"""
        from app.services.approval_engine.workflow_engine import ApprovalRouter

        mock_db = MagicMock()

        router = ApprovalRouter(mock_db)

        result = router.determine_approval_flow("ECN", {})

        assert result == "ECN_STANDARD"

    def test_returns_single_for_small_invoice(self):
        """测试小额发票返回单级流程"""
        from app.services.approval_engine.workflow_engine import ApprovalRouter

        mock_db = MagicMock()

        router = ApprovalRouter(mock_db)

        result = router.determine_approval_flow("SALES_INVOICE", {"amount": 30000})

        assert result == "SALES_INVOICE_SINGLE"

    def test_returns_multi_for_large_invoice(self):
        """测试大额发票返回多级流程"""
        from app.services.approval_engine.workflow_engine import ApprovalRouter

        mock_db = MagicMock()

        router = ApprovalRouter(mock_db)

        result = router.determine_approval_flow("SALES_INVOICE", {"amount": 100000})

        assert result == "SALES_INVOICE_MULTI"

    def test_returns_quote_single_for_quote(self):
        """测试报价返回单级流程"""
        from app.services.approval_engine.workflow_engine import ApprovalRouter

        mock_db = MagicMock()

        router = ApprovalRouter(mock_db)

        result = router.determine_approval_flow("SALES_QUOTE", {})

        assert result == "SALES_QUOTE_SINGLE"

    def test_returns_none_for_unknown_type(self):
        """测试未知类型返回None"""
        from app.services.approval_engine.workflow_engine import ApprovalRouter

        mock_db = MagicMock()

        router = ApprovalRouter(mock_db)

        result = router.determine_approval_flow("UNKNOWN", {})

        assert result is None


class TestGetFirstNodeTimeout:
    """测试 _get_first_node_timeout 方法"""

    def test_returns_default_timeout(self):
        """测试返回默认超时时间"""
        from app.services.approval_engine.workflow_engine import WorkflowEngine

        mock_db = MagicMock()
        mock_flow = MagicMock()

        engine = WorkflowEngine(mock_db)

        result = engine._get_first_node_timeout(mock_flow)

        assert result == 48
