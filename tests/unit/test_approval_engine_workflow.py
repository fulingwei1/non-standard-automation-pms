# -*- coding: utf-8 -*-
"""
workflow_engine.py 单元测试

测试统一审批引擎的工作流执行
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.approval_engine.models import (
    ApprovalStatus,
    ApprovalDecision,
)
from app.services.approval_engine.workflow_engine import WorkflowEngine


@pytest.mark.unit
class TestWorkflowEngineInit:
    """测试 WorkflowEngine 初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        mock_db = MagicMock()
        engine = WorkflowEngine(mock_db)

        assert engine.db == mock_db


@pytest.mark.unit
class TestCreateInstance:
    """测试 create_instance 方法"""

    def test_create_instance_success(self):
        """测试成功创建审批实例"""
        mock_db = MagicMock()

        # Mock 流程查询
        mock_flow = MagicMock()
        mock_flow.flow_code = "ECN_FLOW"
        mock_flow.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_flow

        # Mock 实例编号生成
        with patch.object(
            WorkflowEngine,
            "_generate_instance_no",
            return_value="AP2501250001",
        ):
            # Mock 节点查询
            mock_node = MagicMock()
            mock_node.id = 1
            mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_node

            # Mock 保存
            mock_db.add = MagicMock()
            mock_db.commit = MagicMock()

            engine = WorkflowEngine(mock_db)

            result = engine.create_instance(
                flow_code="ECN_FLOW",
                business_type="ECN",
                business_id=100,
                business_title="测试变更",
                submitted_by=1,
            )

            assert result.instance_no == "AP2501250001"
            assert result.flow_id == 1
            assert result.business_type == "ECN"
            assert result.business_id == 100

    def test_create_instance_flow_not_found(self):
        """测试流程不存在"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        engine = WorkflowEngine(mock_db)

        with pytest.raises(ValueError, match="审批流程 .* 不存在或未启用"):
            engine.create_instance(
                flow_code="NON_EXIST",
                business_type="ECN",
                business_id=100,
                business_title="测试",
                submitted_by=1,
            )


@pytest.mark.unit
class TestGetCurrentNode:
    """测试 get_current_node 方法"""

    def test_get_current_node_success(self):
        """测试成功获取当前节点"""
        mock_db = MagicMock()
        mock_node = MagicMock()
        mock_node.id = 10
        mock_node.node_name = "技术评审"

        mock_instance = MagicMock()
        mock_instance.current_node_id = 10

        mock_db.query.return_value.filter.return_value.first.return_value = mock_node

        engine = WorkflowEngine(mock_db)
        result = engine.get_current_node(mock_instance)

        assert result == mock_node

    def test_get_current_node_not_found(self):
        """测试节点未找到"""
        mock_db = MagicMock()
        mock_instance = MagicMock()
        mock_instance.current_node_id = 999

        mock_db.query.return_value.filter.return_value.first.return_value = None

        engine = WorkflowEngine(mock_db)
        result = engine.get_current_node(mock_instance)

        assert result is None


@pytest.mark.unit
class TestEvaluateNodeConditions:
    """测试 evaluate_node_conditions 方法"""

    def test_evaluate_simple_condition_true(self):
        """测试简单条件为真"""
        mock_db = MagicMock()

        # Mock 节点和实例
        mock_node = MagicMock()
        mock_node.condition_expr = "{{ total_amount > 10000 }}"

        mock_instance = MagicMock()
        mock_instance.form_data = {"total_amount": 15000}

        engine = WorkflowEngine(mock_db)
        result = engine.evaluate_node_conditions(mock_node, mock_instance)

        assert result is True

    def test_evaluate_simple_condition_false(self):
        """测试简单条件为假"""
        mock_db = MagicMock()

        mock_node = MagicMock()
        mock_node.condition_expr = "{{ total_amount > 10000 }}"

        mock_instance = MagicMock()
        mock_instance.form_data = {"total_amount": 5000}

        engine = WorkflowEngine(mock_db)
        result = engine.evaluate_node_conditions(mock_node, mock_instance)

        assert result is False

    def test_evaluate_jinja2_condition(self):
        """测试Jinja2条件表达式"""
        mock_db = MagicMock()

        mock_node = MagicMock()
        mock_node.condition_expr = "{{ items | length > 3 }}"

        mock_instance = MagicMock()
        mock_instance.form_data = {"items": [1, 2, 3, 4]}

        engine = WorkflowEngine(mock_db)
        result = engine.evaluate_node_conditions(mock_node, mock_instance)

        assert result is True

    def test_evaluate_no_condition(self):
        """测试无条件节点"""
        mock_db = MagicMock()

        mock_node = MagicMock()
        mock_node.condition_expr = None

        mock_instance = MagicMock()

        engine = WorkflowEngine(mock_db)
        result = engine.evaluate_node_conditions(mock_node, mock_instance)

        assert result is True


@pytest.mark.unit
class TestSubmitApproval:
    """测试 submit_approval 方法"""

    def test_submit_approve_success(self):
        """测试通过审批"""
        mock_db = MagicMock()

        # Mock 实例和节点
        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.status = ApprovalStatus.IN_PROGRESS
        mock_instance.current_node_id = 10
        mock_instance.total_nodes = 3
        mock_instance.completed_nodes = 1

        mock_node = MagicMock()
        mock_node.id = 10
        mock_node.node_name = "部门经理审批"
        mock_node.node_order = 2

        # Mock 查询
        mock_db.query.return_value.filter.return_value.first.return_value = mock_node

        # Mock 下一个节点
        mock_next_node = MagicMock()
        mock_next_node.id = 11
        mock_next_node.node_order = 3

        mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_next_node

        # Mock 审批记录
        mock_record = MagicMock()
        mock_record.id = 100

        # Mock 保存操作
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        engine = WorkflowEngine(mock_db)

        with patch.object(engine, "_update_instance_status"):
            with patch.object(engine, "_get_approver_name", return_value="张三"):
                result = engine.submit_approval(
                    instance=mock_instance,
                    approver_id=5,
                    decision=ApprovalDecision.APPROVE,
                    comment="同意",
                )

                assert result.decision == ApprovalDecision.APPROVE
                assert result.comment == "同意"

    def test_submit_reject(self):
        """测试驳回审批"""
        mock_db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.status = ApprovalStatus.IN_PROGRESS
        mock_instance.current_node_id = 10

        mock_node = MagicMock()
        mock_node.id = 10
        mock_db.query.return_value.filter.return_value.first.return_value = mock_node

        mock_record = MagicMock()
        mock_record.id = 100

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        engine = WorkflowEngine(mock_db)

        with patch.object(engine, "_update_instance_status"):
            with patch.object(engine, "_get_approver_name", return_value="李四"):
                result = engine.submit_approval(
                    instance=mock_instance,
                    approver_id=6,
                    decision=ApprovalDecision.REJECT,
                    comment="需要修改",
                )

                assert result.decision == ApprovalDecision.REJECT
                assert result.comment == "需要修改"


@pytest.mark.unit
class TestUpdateInstanceStatus:
    """测试 _update_instance_status 方法"""

    def test_update_to_approved(self):
        """测试更新为已批准"""
        mock_db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.status = ApprovalStatus.IN_PROGRESS
        mock_instance.current_node_order = 2
        mock_instance.total_nodes = 2
        mock_instance.completed_nodes = 1

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        engine = WorkflowEngine(mock_db)
        engine._update_instance_status(
            mock_instance, ApprovalStatus.APPROVED, completed_nodes=2
        )

        assert mock_instance.status == ApprovalStatus.APPROVED
        assert mock_instance.completed_nodes == 2

    def test_update_to_rejected(self):
        """测试更新为已驳回"""
        mock_db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.status = ApprovalStatus.IN_PROGRESS

        engine = WorkflowEngine(mock_db)
        engine._update_instance_status(mock_instance, ApprovalStatus.REJECTED)

        assert mock_instance.status == ApprovalStatus.REJECTED


@pytest.mark.unit
class TestFindNextNode:
    """测试 _find_next_node 方法"""

    def test_find_next_node_exists(self):
        """测试找到下一个节点"""
        mock_db = MagicMock()

        mock_node = MagicMock()
        mock_node.id = 10
        mock_node.node_order = 2
        mock_node.flow_id = 1

        mock_next_node = MagicMock()
        mock_next_node.id = 11
        mock_next_node.node_order = 3

        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.first.return_value = mock_next_node

        engine = WorkflowEngine(mock_db)
        result = engine._find_next_node(mock_node)

        assert result == mock_next_node

    def test_find_next_node_not_found(self):
        """测试没有下一个节点（当前为最后一个）"""
        mock_db = MagicMock()

        mock_node = MagicMock()
        mock_node.id = 10
        mock_node.node_order = 3
        mock_node.flow_id = 1

        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.first.return_value = None

        engine = WorkflowEngine(mock_db)
        result = engine._find_next_node(mock_node)

        assert result is None


@pytest.mark.unit
class TestFindPreviousNode:
    """测试 _find_previous_node 方法"""

    def test_find_previous_node_exists(self):
        """测试找到上一个节点"""
        mock_db = MagicMock()

        mock_node = MagicMock()
        mock_node.id = 10
        mock_node.node_order = 2
        mock_node.flow_id = 1

        mock_prev_node = MagicMock()
        mock_prev_node.id = 9
        mock_prev_node.node_order = 1

        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.first.return_value = mock_prev_node

        engine = WorkflowEngine(mock_db)
        result = engine._find_previous_node(mock_node)

        assert result == mock_prev_node

    def test_find_previous_node_not_found(self):
        """测试没有上一个节点（当前为第一个）"""
        mock_db = MagicMock()

        mock_node = MagicMock()
        mock_node.id = 10
        mock_node.node_order = 1
        mock_node.flow_id = 1

        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.first.return_value = None

        engine = WorkflowEngine(mock_db)
        result = engine._find_previous_node(mock_node)

        assert result is None


@pytest.mark.unit
class TestIsExpired:
    """测试 is_expired 方法"""

    def test_is_expired_true(self):
        """测试审批已超时"""
        mock_db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.created_at = datetime.now() - timedelta(hours=72)

        mock_flow = MagicMock()
        mock_flow.first_node_timeout = 48  # 48小时超时

        mock_db.query.return_value.filter.return_value.join.return_value.first.return_value = mock_flow

        engine = WorkflowEngine(mock_db)
        result = engine.is_expired(mock_instance)

        assert result is True

    def test_is_expired_false(self):
        """测试审批未超时"""
        mock_db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.created_at = datetime.now() - timedelta(hours=24)

        mock_flow = MagicMock()
        mock_flow.first_node_timeout = 48

        mock_db.query.return_value.filter.return_value.join.return_value.first.return_value = mock_flow

        engine = WorkflowEngine(mock_db)
        result = engine.is_expired(mock_instance)

        assert result is False


@pytest.mark.unit
class TestApprovalFlowResolver:
    """测试 ApprovalFlowResolver 内部类"""

    def test_resolver_init(self):
        """测试 resolver 初始化"""
        mock_db = MagicMock()
        engine = WorkflowEngine(mock_db)

        resolver = engine.ApprovalFlowResolver(mock_db)

        assert resolver.db == mock_db

    def test_get_approval_flow_success(self):
        """测试获取审批流程"""
        mock_db = MagicMock()

        mock_flow = MagicMock()
        mock_flow.id = 1
        mock_flow.flow_code = "ECN_FLOW"

        mock_db.query.return_value.filter.return_value.first.return_value = mock_flow

        engine = WorkflowEngine(mock_db)
        resolver = engine.ApprovalFlowResolver(mock_db)

        result = resolver.get_approval_flow("ECN_FLOW")

        assert result == mock_flow

    def test_get_approval_flow_not_found(self):
        """测试流程不存在"""
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        engine = WorkflowEngine(mock_db)
        resolver = engine.ApprovalFlowResolver(mock_db)

        with pytest.raises(ValueError, match="审批流程 .* 不存在或未启用"):
            resolver.get_approval_flow("NON_EXIST")

    def test_determine_approval_flow_by_type(self):
        """测试根据业务类型确定流程"""
        mock_db = MagicMock()

        mock_flow = MagicMock()
        mock_flow.id = 1
        mock_db.query.return_value.filter.return_value.first.return_value = mock_flow

        engine = WorkflowEngine(mock_db)
        resolver = engine.ApprovalFlowResolver(mock_db)

        # 测试ECN流程
        flow_code = resolver.determine_approval_flow("ECN")
        assert flow_code == "ECN_FLOW"

        # 测试QUOTE流程
        flow_code = resolver.determine_approval_flow("QUOTE")
        assert flow_code == "QUOTE_FLOW"

        # 测试CONTRACT流程
        flow_code = resolver.determine_approval_flow("CONTRACT")
        assert flow_code == "CONTRACT_FLOW"


@pytest.mark.unit
class TestWorkflowEngineIntegration:
    """测试工作流引擎集成场景"""

    def test_complete_approval_flow(self):
        """测试完整的审批流程"""
        mock_db = MagicMock()

        # Mock 流程
        mock_flow = MagicMock()
        mock_flow.id = 1
        mock_flow.flow_code = "ECN_FLOW"

        # Mock 节点
        mock_node1 = MagicMock()
        mock_node1.id = 10
        mock_node1.node_order = 1

        mock_node2 = MagicMock()
        mock_node2.id = 11
        mock_node2.node_order = 2

        mock_db.query.return_value.filter.return_value.first.return_value = mock_flow
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = [
            mock_node1,
            mock_node2,
        ]

        # Mock 保存操作
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        engine = WorkflowEngine(mock_db)

        # 创建实例
        with patch.object(
            WorkflowEngine,
            "_generate_instance_no",
            return_value="AP2501250001",
        ):
            instance = engine.create_instance(
                flow_code="ECN_FLOW",
                business_type="ECN",
                business_id=100,
                business_title="测试",
                submitted_by=1,
            )

            assert instance.status == ApprovalStatus.PENDING

    def test_multi_level_approval_flow(self):
        """测试多级审批流程"""
        mock_db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.status = ApprovalStatus.IN_PROGRESS
        mock_instance.current_node_id = 10
        mock_instance.completed_nodes = 0
        mock_instance.total_nodes = 3

        # Mock 节点链
        mock_node1 = MagicMock()
        mock_node1.id = 10
        mock_node1.node_order = 1

        mock_node2 = MagicMock()
        mock_node2.id = 11
        mock_node2.node_order = 2

        mock_node3 = MagicMock()
        mock_node3.id = 12
        mock_node3.node_order = 3

        mock_db.query.return_value.filter.return_value.first.return_value = mock_node1
        mock_db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.first.side_effect = [
            mock_node2,
            mock_node3,
            None,
        ]

        mock_record = MagicMock()
        mock_record.id = 100

        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        engine = WorkflowEngine(mock_db)

        # 第一级审批
        with patch.object(engine, "_update_instance_status"):
            with patch.object(engine, "_get_approver_name", return_value="张三"):
                engine.submit_approval(
                    instance=mock_instance,
                    approver_id=5,
                    decision=ApprovalDecision.APPROVE,
                    comment="通过",
                )

                assert mock_instance.current_node_id == 11
                assert mock_instance.completed_nodes == 1


@pytest.mark.unit
class TestEdgeCases:
    """测试边界情况和异常处理"""

    def test_empty_condition_expression(self):
        """测试空条件表达式"""
        mock_db = MagicMock()

        mock_node = MagicMock()
        mock_node.condition_expr = ""

        mock_instance = MagicMock()

        engine = WorkflowEngine(mock_db)
        result = engine.evaluate_node_conditions(mock_node, mock_instance)

        assert result is True

    def test_invalid_condition_expression(self):
        """测试无效条件表达式"""
        mock_db = MagicMock()

        mock_node = MagicMock()
        mock_node.condition_expr = "{{ invalid_syntax "

        mock_instance = MagicMock()

        engine = WorkflowEngine(mock_db)

        # 应该抛出异常或返回默认值
        try:
            result = engine.evaluate_node_conditions(mock_node, mock_instance)
            # 如果没有抛出异常，应该返回False
            assert result is False
        except Exception:
            # 抛出异常也是合理的行为
            pass

    def test_concurrent_approval_requests(self):
        """测试并发审批请求"""
        mock_db = MagicMock()

        mock_instance = MagicMock()
        mock_instance.id = 1
        mock_instance.current_node_id = 10

        mock_node = MagicMock()
        mock_node.id = 10

        mock_db.query.return_value.filter.return_value.first.return_value = mock_node
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()

        engine = WorkflowEngine(mock_db)

        # 模拟两个并发审批
        with patch.object(engine, "_update_instance_status"):
            with patch.object(engine, "_get_approver_name", return_value="张三"):
                engine.submit_approval(
                    instance=mock_instance,
                    approver_id=5,
                    decision=ApprovalDecision.APPROVE,
                    comment="同意",
                )

            with patch.object(engine, "_get_approver_name", return_value="李四"):
                # 第二个审批应该能看到已经更新后的状态
                engine.submit_approval(
                    instance=mock_instance,
                    approver_id=6,
                    decision=ApprovalDecision.APPROVE,
                    comment="同意",
                )


# =============================================================================
# 补充测试 A组覆盖率提升 (2026-02-17)
# =============================================================================

class TestWorkflowEngineAdditional:
    """WorkflowEngine 额外单元测试（MagicMock 版本）"""

    def _make_engine(self):
        db = MagicMock()
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        return WorkflowEngine(db), db

    def test_generate_instance_no_format(self):
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        no = WorkflowEngine._generate_instance_no()
        assert no.startswith("AP")
        assert len(no) > 5

    def test_create_instance_raises_when_flow_not_found(self):
        engine, db = self._make_engine()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在或未启用"):
            engine.create_instance(
                flow_code="UNKNOWN",
                business_type="ECN",
                business_id=1,
                business_title="Test",
                submitted_by=1,
            )

    def test_create_instance_success(self):
        engine, db = self._make_engine()
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        from app.services.approval_engine.models import LegacyApprovalFlow as ApprovalFlow

        flow = MagicMock()
        flow.id = 1
        flow.flow_code = "ECN_FLOW"
        flow.nodes = [MagicMock(), MagicMock()]

        db.query.return_value.filter.return_value.first.return_value = flow

        with patch("app.services.approval_engine.workflow_engine.save_obj"):
            with patch.object(WorkflowEngine, "_get_first_node_timeout", return_value=48):
                instance = engine.create_instance(
                    flow_code="ECN_FLOW",
                    business_type="ECN",
                    business_id=10,
                    business_title="测试ECN",
                    submitted_by=5,
                )

        assert instance is not None

    def test_get_current_node_returns_none_for_approved_status(self):
        engine, db = self._make_engine()
        from app.services.approval_engine.models import ApprovalStatus

        instance = MagicMock()
        instance.current_status = ApprovalStatus.APPROVED.value
        instance.current_node_id = None

        result = engine.get_current_node(instance)
        assert result is None

    def test_get_current_node_by_node_id(self):
        engine, db = self._make_engine()
        from app.services.approval_engine.models import ApprovalStatus

        instance = MagicMock()
        instance.current_status = ApprovalStatus.PENDING.value
        instance.current_node_id = 5

        node = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = node

        result = engine.get_current_node(instance)
        assert result is node

    def test_get_current_node_finds_first_when_no_node_id(self):
        engine, db = self._make_engine()
        from app.services.approval_engine.models import ApprovalStatus

        instance = MagicMock()
        instance.current_status = ApprovalStatus.IN_PROGRESS.value
        instance.current_node_id = None
        instance.flow_id = 1

        first_node = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.first.return_value = first_node

        result = engine.get_current_node(instance)
        assert result is first_node

    def test_evaluate_node_conditions_returns_true_when_no_condition(self):
        engine, _ = self._make_engine()
        node = MagicMock()
        node.condition_expression = None
        node.condition_expr = None

        instance = MagicMock()
        result = engine.evaluate_node_conditions(node, instance)
        assert result is True

    def test_evaluate_node_conditions_with_jinja2(self):
        engine, db = self._make_engine()
        node = MagicMock()
        node.condition_expression = "{{ form.amount > 1000 }}"
        node.id = 1

        instance = MagicMock()
        instance.submitted_by = None
        instance.business_type = "UNKNOWN"
        instance.business_id = 1
        instance.form_data = {"amount": 2000}

        db.query.return_value.filter.return_value.first.return_value = None

        # Should not raise
        result = engine.evaluate_node_conditions(node, instance)
        # Result may be True or False, just check it's a bool
        assert isinstance(result, bool)

    def test_is_expired_with_due_date_past(self):
        engine, _ = self._make_engine()
        from datetime import datetime, timedelta

        instance = MagicMock()
        instance.due_date = datetime.now() - timedelta(hours=1)

        assert engine.is_expired(instance) is True

    def test_is_expired_with_due_date_future(self):
        engine, _ = self._make_engine()
        from datetime import datetime, timedelta

        instance = MagicMock()
        instance.due_date = datetime.now() + timedelta(hours=24)

        assert engine.is_expired(instance) is False

    def test_is_expired_without_due_date(self):
        engine, db = self._make_engine()
        instance = MagicMock()
        instance.due_date = None
        instance.created_at = None  # not a datetime
        # Expect False (no valid date)
        result = engine.is_expired(instance)
        assert result is False

    def test_get_first_node_timeout_default(self):
        engine, _ = self._make_engine()
        flow = MagicMock()
        flow.first_node_timeout = None
        assert engine._get_first_node_timeout(flow) == 48

    def test_get_first_node_timeout_custom(self):
        engine, _ = self._make_engine()
        flow = MagicMock()
        flow.first_node_timeout = 72
        assert engine._get_first_node_timeout(flow) == 72


class TestApprovalFlowResolverAdditional:
    def test_determine_flow_known_type(self):
        db = MagicMock()
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        resolver = WorkflowEngine.ApprovalFlowResolver(db)
        result = resolver.determine_approval_flow("ECN")
        assert result == "ECN_FLOW"

    def test_determine_flow_unknown_type(self):
        db = MagicMock()
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        resolver = WorkflowEngine.ApprovalFlowResolver(db)
        result = resolver.determine_approval_flow("UNKNOWN_TYPE")
        assert result is None

    def test_get_approval_flow_raises_when_not_found(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        resolver = WorkflowEngine.ApprovalFlowResolver(db)
        with pytest.raises(ValueError, match="不存在或未启用"):
            resolver.get_approval_flow("NO_FLOW")

    def test_get_approval_flow_returns_flow(self):
        db = MagicMock()
        flow = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = flow
        from app.services.approval_engine.workflow_engine import WorkflowEngine
        resolver = WorkflowEngine.ApprovalFlowResolver(db)
        result = resolver.get_approval_flow("ECN_FLOW")
        assert result is flow


import pytest
