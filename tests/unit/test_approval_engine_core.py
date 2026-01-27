# -*- coding: utf-8 -*-
"""
approval_engine/core.py 单元测试

测试审批引擎核心类的各个方法
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from app.models.approval import (
    ApprovalActionLog,
)
from app.services.approval_engine.engine.core import ApprovalEngineCore


@pytest.mark.unit
class TestApprovalEngineCoreInit:
    """测试 ApprovalEngineCore 初始化"""

    def test_init_with_db_session(self):
        """测试使用数据库会话初始化"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        assert service.db == mock_db
        assert service.router is not None
        assert service.executor is not None
        assert service.notify is not None
        assert service.delegate_service is not None


@pytest.mark.unit
class TestGenerateInstanceNo:
    """测试 _generate_instance_no 方法"""

    def test_generate_first_instance_today(self):
        """测试当天第一个实例编号"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        # Mock query to return 0 existing instances
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 0
        mock_db.query.return_value = mock_query

        now = datetime.now()
        prefix = f"AP{now.strftime('%y%m%d')}"

        result = service._generate_instance_no(prefix)

        assert result == f"{prefix}0001"

    def test_generate_subsequent_instance(self):
        """测试当天后续实例编号"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        # Mock query to return 5 existing instances
        mock_query = MagicMock()
        mock_query.filter.return_value.count.return_value = 5
        mock_db.query.return_value = mock_query

        now = datetime.now()
        prefix = f"AP{now.strftime('%y%m%d')}"

        result = service._generate_instance_no(prefix)

        assert result == f"{prefix}0006"


@pytest.mark.unit
class TestGetFirstNode:
    """测试 _get_first_node 方法"""

    def test_get_first_node_success(self):
        """测试成功获取第一个节点"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        # Mock node with necessary attributes only
        mock_node = MagicMock()

        # Mock the filter method to return query
        mock_filter_result = MagicMock()
        mock_filter_result.order_by = MagicMock(return_value=mock_filter_result)
        mock_filter_result.first = MagicMock(return_value=mock_node)

        # Mock db.query to return an object that has filter method
        mock_query_obj = MagicMock()
        mock_query_obj.filter.return_value = mock_filter_result
        mock_db.query.return_value = mock_query_obj

        result = service._get_first_node(flow_id=100)

        assert result == mock_node

    def test_get_first_node_not_found(self):
        """测试第一个节点不存在"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        # Mock the filter method to return query
        mock_filter_result = MagicMock()
        mock_filter_result.order_by = MagicMock(return_value=mock_filter_result)
        mock_filter_result.first = MagicMock(return_value=None)

        mock_query_obj = MagicMock()
        mock_query_obj.filter.return_value = mock_filter_result
        mock_db.query.return_value = mock_query_obj

        result = service._get_first_node(flow_id=999)

        assert result is None

    def test_get_first_node_query_called_correctly(self):
        """测试查询是否正确调用"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        # Mock node
        mock_node = MagicMock()

        # Mock the filter method
        mock_filter_result = MagicMock()
        mock_filter_result.order_by = MagicMock(return_value=mock_filter_result)
        mock_filter_result.first = MagicMock(return_value=mock_node)

        mock_query_obj = MagicMock()
        mock_query_obj.filter.return_value = mock_filter_result
        mock_db.query.return_value = mock_query_obj

        # Call the method
        result = service._get_first_node(flow_id=100)

        # Verify the query was called with ApprovalNodeDefinition model
        mock_db.query.assert_called_once()
        # Verify filter was called
        mock_query_obj.filter.assert_called_once()
        # Verify order_by was called
        mock_filter_result.order_by.assert_called_once()
        # Verify first was called
        mock_filter_result.first.assert_called_once()


@pytest.mark.unit
class TestGetAndValidateTask:
    """测试 _get_and_validate_task 方法"""

    def test_get_and_validate_task_success(self):
        """测试成功获取并验证任务"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.assignee_id = 100
        mock_task.status = "PENDING"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_task
        mock_db.query.return_value = mock_query

        result = service._get_and_validate_task(task_id=1, user_id=100)

        assert result == mock_task

    def test_get_and_validate_task_not_found(self):
        """测试任务不存在"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = None
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="任务不存在"):
            service._get_and_validate_task(task_id=999, user_id=100)

    def test_get_and_validate_task_wrong_user(self):
        """测试用户无权操作任务"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.assignee_id = 999
        mock_task.status = "PENDING"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_task
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="无权操作"):
            service._get_and_validate_task(task_id=1, user_id=100)

    def test_get_and_validate_task_invalid_status(self):
        """测试任务状态不正确"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.assignee_id = 100
        mock_task.status = "APPROVED"

        mock_query = MagicMock()
        mock_query.filter.return_value.first.return_value = mock_task
        mock_db.query.return_value = mock_query

        with pytest.raises(ValueError, match="任务状态不正确"):
            service._get_and_validate_task(task_id=1, user_id=100)


@pytest.mark.unit
class TestGetAffectedUserIds:
    """测试 _get_affected_user_ids 方法"""

    def test_get_affected_user_ids_with_tasks(self):
        """测试有待处理任务时获取受影响用户"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 100

        mock_tasks = [
        MagicMock(assignee_id=1),
        MagicMock(assignee_id=2),
        MagicMock(assignee_id=3),
        ]

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = mock_tasks
        mock_db.query.return_value = mock_query

        result = service._get_affected_user_ids(mock_instance)

        assert result == [1, 2, 3]

    def test_get_affected_user_ids_empty_tasks(self):
        """测试没有待处理任务"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 100

        mock_query = MagicMock()
        mock_query.filter.return_value.all.return_value = []
        mock_db.query.return_value = mock_query

        result = service._get_affected_user_ids(mock_instance)

        assert result == []


@pytest.mark.unit
class TestLogAction:
    """测试 _log_action 方法"""

    def test_log_action_with_all_params(self):
        """测试记录操作日志（所有参数）"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        service._log_action(
        instance_id=100,
        operator_id=1,
        action="APPROVE",
        task_id=50,
        node_id=10,
        operator_name="Test User",
        comment="Test comment",
        attachments=[{"name": "file.pdf"}],
        action_detail={"key": "value"},
        before_status="PENDING",
        after_status="APPROVED",
        )

        mock_db.add.assert_called_once()
        added_log = mock_db.add.call_args[0][0]
        assert isinstance(added_log, ApprovalActionLog)
        assert added_log.instance_id == 100
        assert added_log.operator_id == 1
        assert added_log.action == "APPROVE"
        assert added_log.operator_name == "Test User"
        assert added_log.comment == "Test comment"
        assert isinstance(added_log.action_at, datetime)

    def test_log_action_minimal_params(self):
        """测试记录操作日志（最小参数）"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        service._log_action(
        instance_id=100,
        operator_id=1,
        action="APPROVE",
        )

        mock_db.add.assert_called_once()
        added_log = mock_db.add.call_args[0][0]
        assert isinstance(added_log, ApprovalActionLog)
        assert added_log.task_id is None
        assert added_log.node_id is None
        assert added_log.operator_name is None
        assert added_log.comment is None


@pytest.mark.unit
class TestAdvanceToNextNode:
    """测试 _advance_to_next_node 方法"""

    @patch("app.services.approval_engine.engine.core.get_adapter")
    def test_advance_to_next_node_no_next_nodes(self, mock_get_adapter):
        """测试没有下一节点时（审批完成）"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.form_data = {}
        mock_instance.initiator_id = 1
        mock_instance.initiator_dept_id = 10

        mock_current_task = MagicMock()
        mock_current_task.node = MagicMock()
        mock_current_task.node.id = 1

        # Mock router.get_next_nodes to return empty list
        with patch.object(service, "router") as mock_router:
            mock_router.get_next_nodes.return_value = []
            mock_adapter = MagicMock()
            mock_get_adapter.return_value = mock_adapter

            service._advance_to_next_node(mock_instance, mock_current_task)

            assert mock_instance.status == "APPROVED"
            assert isinstance(mock_instance.completed_at, datetime)
            mock_adapter.on_approved.assert_called_once_with(123, mock_instance)


@pytest.mark.unit
class TestReturnToNode:
    """测试 _return_to_node 方法"""

    def test_return_to_node_success(self):
        """测试成功退回到指定节点"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.form_data = {}
        mock_instance.initiator_id = 1
        mock_instance.initiator_dept_id = 10

        mock_target_node = MagicMock()
        mock_target_node.id = 5

        # Mock query for tasks
        mock_query = MagicMock()
        mock_query.filter.return_value.update.return_value = None
        mock_db.query.return_value = mock_query

        # Mock _create_node_tasks
        with patch.object(service, "_create_node_tasks"):
            service._return_to_node(mock_instance, mock_target_node)

            assert mock_instance.current_node_id == 5
            mock_query.filter.assert_called_once()
            mock_query.filter.return_value.update.assert_called_once_with(
            {"status": "CANCELLED"}, synchronize_session=False
            )

    def test_return_to_node_cancel_multiple_tasks(self):
        """测试取消多个待处理任务"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        mock_instance = MagicMock()
        mock_instance.id = 100
        mock_instance.form_data = {}
        mock_instance.initiator_id = 1
        mock_instance.initiator_dept_id = 10

        mock_target_node = MagicMock()
        mock_target_node.id = 5

        # Mock update to track count
        update_call_count = [0]

        def update_side_effect(*args, **kwargs):
            update_call_count[0] += 1
            return MagicMock()

            mock_query = MagicMock()
            mock_query.filter.return_value.update.side_effect = update_side_effect
            mock_db.query.return_value = mock_query

            with patch.object(service, "_create_node_tasks"):
                service._return_to_node(mock_instance, mock_target_node)

                # Should update all pending tasks
                assert update_call_count[0] == 1


@pytest.mark.unit
class TestApprovalEngineCoreIntegration:
    """集成测试"""

    def test_all_private_methods_callable(self):
        """测试所有私有方法可调用"""
        mock_db = MagicMock()
        service = ApprovalEngineCore(mock_db)

        # Verify all private methods exist
        assert hasattr(service, "_generate_instance_no")
        assert hasattr(service, "_get_first_node")
        assert hasattr(service, "_create_node_tasks")
        assert hasattr(service, "_advance_to_next_node")
        assert hasattr(service, "_return_to_node")
        assert hasattr(service, "_get_and_validate_task")
        assert hasattr(service, "_get_affected_user_ids")
        assert hasattr(service, "_log_action")
