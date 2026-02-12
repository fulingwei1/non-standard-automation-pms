# -*- coding: utf-8 -*-
"""WorkflowEngine 单元测试"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, PropertyMock


class TestWorkflowEngine:
    """WorkflowEngine 测试"""

    def _make_engine(self):
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        db = MagicMock()
        return WorkflowEngine(db), db

    # -- create_instance --

    def test_create_instance_success(self):
        engine, db = self._make_engine()
        flow = MagicMock(id=1, flow_code="ECN_FLOW", nodes=[MagicMock(), MagicMock()])
        db.query.return_value.filter.return_value.first.return_value = flow

        inst = engine.create_instance(
            flow_code="ECN_FLOW",
            business_type="ECN",
            business_id=10,
            business_title="Test",
            submitted_by=1,
        )
        assert inst is not None
        db.add.assert_called_once()
        db.commit.assert_called_once()

    def test_create_instance_flow_not_found(self):
        engine, db = self._make_engine()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="不存在或未启用"):
            engine.create_instance("INVALID", "ECN", 1, "t", 1)

    # -- get_current_node --

    def test_get_current_node_with_node_id(self):
        engine, db = self._make_engine()
        instance = MagicMock(current_status="PENDING", current_node_id=5, flow_id=1)
        node = MagicMock(id=5)
        db.query.return_value.filter.return_value.first.return_value = node

        result = engine.get_current_node(instance)
        assert result == node

    def test_get_current_node_no_node_id(self):
        engine, db = self._make_engine()
        instance = MagicMock(current_status="PENDING", current_node_id=None, flow_id=1)
        node = MagicMock(id=1)
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = node

        result = engine.get_current_node(instance)
        assert result == node

    def test_get_current_node_completed_status(self):
        engine, db = self._make_engine()
        instance = MagicMock(current_status="APPROVED")

        result = engine.get_current_node(instance)
        assert result is None

    # -- evaluate_node_conditions --

    def test_evaluate_node_conditions_no_condition(self):
        engine, _ = self._make_engine()
        node = MagicMock(spec=[])  # no condition_expression or condition_expr
        instance = MagicMock()
        assert engine.evaluate_node_conditions(node, instance) is True

    def test_evaluate_node_conditions_empty_string(self):
        engine, _ = self._make_engine()
        node = MagicMock(condition_expression="", condition_expr="")
        instance = MagicMock()
        assert engine.evaluate_node_conditions(node, instance) is True

    # -- submit_approval --

    def test_submit_approval_no_node_raises(self):
        engine, db = self._make_engine()
        instance = MagicMock(current_status="approved", current_node_id=None)

        with pytest.raises(ValueError, match="没有可审批的节点"):
            engine.submit_approval(instance, 1, "APPROVED")

    def test_submit_approval_success(self):
        engine, db = self._make_engine()
        node = MagicMock(id=1, flow_id=1, role_type="USER", sequence=1)
        node.role = MagicMock()
        instance = MagicMock(
            id=1, current_status="PENDING", current_node_id=1,
            flow_id=1, completed_nodes=0
        )

        with patch.object(engine, 'get_current_node', return_value=node), \
             patch.object(engine, 'evaluate_node_conditions', return_value=True), \
             patch.object(engine, '_get_approver_name', return_value="张三"), \
             patch.object(engine, '_get_approver_role', return_value="用户"), \
             patch.object(engine, '_update_instance_status'), \
             patch.object(engine, '_find_next_node', return_value=None):
            record = engine.submit_approval(instance, 1, "APPROVED", "ok")
            assert record is not None

    # -- is_expired --

    def test_is_expired_with_due_date_past(self):
        engine, _ = self._make_engine()
        instance = MagicMock(due_date=datetime.now() - timedelta(hours=1))
        assert engine.is_expired(instance) is True

    def test_is_expired_with_due_date_future(self):
        engine, _ = self._make_engine()
        instance = MagicMock(due_date=datetime.now() + timedelta(hours=1))
        assert engine.is_expired(instance) is False

    def test_is_expired_no_dates(self):
        engine, _ = self._make_engine()
        instance = MagicMock(spec=[])  # no due_date, no created_at
        assert engine.is_expired(instance) is False

    # -- _generate_instance_no --

    def test_generate_instance_no_format(self):
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        no = WorkflowEngine._generate_instance_no()
        assert no.startswith("AP")
        assert len(no) > 10

    # -- _get_first_node_timeout --

    def test_get_first_node_timeout_default(self):
        engine, _ = self._make_engine()
        flow = MagicMock(spec=[])  # no first_node_timeout
        assert engine._get_first_node_timeout(flow) == 48

    def test_get_first_node_timeout_custom(self):
        engine, _ = self._make_engine()
        flow = MagicMock(first_node_timeout=24)
        assert engine._get_first_node_timeout(flow) == 24

    # -- _get_approver_role --

    def test_get_approver_role_user(self):
        engine, _ = self._make_engine()
        from app.services.approval_engine.models import ApprovalNodeRole
        node = MagicMock(role_type=ApprovalNodeRole.USER.value)
        assert engine._get_approver_role(node) == "用户"

    def test_get_approver_role_role(self):
        engine, _ = self._make_engine()
        from app.services.approval_engine.models import ApprovalNodeRole
        node = MagicMock(role_type=ApprovalNodeRole.ROLE.value)
        assert engine._get_approver_role(node) == "角色"

    def test_get_approver_role_department(self):
        engine, _ = self._make_engine()
        from app.services.approval_engine.models import ApprovalNodeRole
        node = MagicMock(role_type=ApprovalNodeRole.DEPARTMENT.value)
        assert engine._get_approver_role(node) == "部门"


class TestApprovalFlowResolver:
    """ApprovalFlowResolver 测试"""

    def _make_resolver(self):
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        db = MagicMock()
        return WorkflowEngine.ApprovalFlowResolver(db), db

    def test_get_approval_flow_found(self):
        resolver, db = self._make_resolver()
        flow = MagicMock(id=1)
        db.query.return_value.filter.return_value.first.return_value = flow
        result = resolver.get_approval_flow("ECN_FLOW")
        assert result == flow

    def test_get_approval_flow_not_found(self):
        resolver, db = self._make_resolver()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在或未启用"):
            resolver.get_approval_flow("INVALID")

    def test_determine_approval_flow_known(self):
        resolver, _ = self._make_resolver()
        assert resolver.determine_approval_flow("ECN") == "ECN_FLOW"
        assert resolver.determine_approval_flow("QUOTE") == "QUOTE_FLOW"

    def test_determine_approval_flow_unknown(self):
        resolver, _ = self._make_resolver()
        assert resolver.determine_approval_flow("UNKNOWN") is None


class TestApprovalRouter:
    """ApprovalRouter (workflow_engine 内的) 测试"""

    def _make_router(self):
        from app.services.approval_engine.workflow_engine import ApprovalRouter
        db = MagicMock()
        return ApprovalRouter(db), db

    def test_determine_approval_flow_ecn(self):
        router, _ = self._make_router()
        assert router.determine_approval_flow("ECN", {}) == "ECN_STANDARD"

    def test_determine_approval_flow_invoice_low(self):
        router, _ = self._make_router()
        result = router.determine_approval_flow("SALES_INVOICE", {"amount": 10000})
        assert result == "SALES_INVOICE_SINGLE"

    def test_determine_approval_flow_invoice_high(self):
        router, _ = self._make_router()
        result = router.determine_approval_flow("SALES_INVOICE", {"amount": 100000})
        assert result == "SALES_INVOICE_MULTI"

    def test_determine_approval_flow_quote(self):
        router, _ = self._make_router()
        assert router.determine_approval_flow("SALES_QUOTE", {}) == "SALES_QUOTE_SINGLE"

    def test_determine_approval_flow_unknown(self):
        router, _ = self._make_router()
        assert router.determine_approval_flow("UNKNOWN", {}) is None

    def test_get_approval_flow(self):
        router, db = self._make_router()
        flow = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = flow
        assert router.get_approval_flow("ECN") == flow

    def test_create_approval_instance_unknown_type(self):
        router, _ = self._make_router()
        with pytest.raises(ValueError, match="未找到业务类型"):
            router.create_approval_instance("UNKNOWN", {}, 1)
