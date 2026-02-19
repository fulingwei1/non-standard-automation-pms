# -*- coding: utf-8 -*-
"""
第三十二批覆盖率测试 - 节点子任务服务 (扩展)
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime

try:
    from app.services.node_task_service import NodeTaskService
    from app.models.enums import StageStatusEnum
    HAS_NTS = True
except Exception:
    HAS_NTS = False

pytestmark = pytest.mark.skipif(not HAS_NTS, reason="node_task_service 导入失败")


def make_service():
    db = MagicMock()
    svc = NodeTaskService(db)
    return svc, db


class TestNodeTaskServiceInit:
    def test_init(self):
        db = MagicMock()
        svc = NodeTaskService(db)
        assert svc.db is db


class TestCreateTask:
    def test_create_task_node_not_found(self):
        """节点不存在时抛出ValueError"""
        svc, db = make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            svc.create_task(node_instance_id=999, task_name="测试任务")

    def test_create_task_auto_generates_code(self):
        """自动生成任务编码"""
        svc, db = make_service()
        mock_node = MagicMock()
        mock_node.id = 1
        mock_node.node_code = "NODE01"
        mock_node.assignee_id = 5

        db.query.return_value.filter.return_value.first.return_value = mock_node
        db.query.return_value.filter.return_value.count.return_value = 2

        mock_task = MagicMock()
        db.add.return_value = None
        db.flush.return_value = None

        with patch("app.services.node_task_service.NodeTask", return_value=mock_task):
            result = svc.create_task(node_instance_id=1, task_name="新任务")
        assert result is mock_task

    def test_create_task_inherits_assignee(self):
        """未指定执行人时继承节点负责人"""
        svc, db = make_service()
        mock_node = MagicMock()
        mock_node.id = 1
        mock_node.node_code = "N01"
        mock_node.assignee_id = 42

        db.query.return_value.filter.return_value.first.return_value = mock_node
        db.query.return_value.filter.return_value.count.return_value = 0

        mock_task = MagicMock()
        with patch("app.services.node_task_service.NodeTask", return_value=mock_task) as MockTask:
            svc.create_task(node_instance_id=1, task_name="任务", assignee_id=None)
            call_kwargs = MockTask.call_args[1]
            assert call_kwargs.get("assignee_id") == 42


class TestGetTask:
    def test_get_task_found(self):
        """获取已存在的任务"""
        svc, db = make_service()
        mock_task = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_task
        result = svc.get_task(1)
        assert result is mock_task

    def test_get_task_not_found(self):
        """任务不存在返回None"""
        svc, db = make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        result = svc.get_task(999)
        assert result is None


class TestListTasks:
    def test_list_tasks_all(self):
        """列出节点的所有任务"""
        svc, db = make_service()
        mock_tasks = [MagicMock(), MagicMock()]
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_tasks
        result = svc.list_tasks(node_instance_id=1)
        assert len(result) == 2

    def test_list_tasks_with_status_filter(self):
        """按状态筛选任务"""
        svc, db = make_service()
        db.query.return_value.filter.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = svc.list_tasks(node_instance_id=1, status="PENDING")
        assert result == []


class TestUpdateTask:
    def test_update_task_not_found(self):
        """更新不存在的任务返回None"""
        svc, db = make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        result = svc.update_task(999, task_name="新名称")
        assert result is None

    def test_update_task_success(self):
        """成功更新任务属性"""
        svc, db = make_service()
        mock_task = MagicMock(spec=["task_name", "description", "id"])
        mock_task.task_name = "旧名称"
        db.query.return_value.filter.return_value.first.return_value = mock_task
        result = svc.update_task(1, task_name="新名称")
        assert result is mock_task


class TestDeleteTask:
    def test_delete_task_not_found(self):
        """删除不存在的任务返回False"""
        svc, db = make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        result = svc.delete_task(999)
        assert result is False

    def test_delete_task_success(self):
        """成功删除任务"""
        svc, db = make_service()
        mock_task = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_task
        result = svc.delete_task(1)
        assert result is True
        db.delete.assert_called_once_with(mock_task)


class TestStartAndCompleteTask:
    def test_start_task_not_found(self):
        svc, db = make_service()
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError):
            svc.start_task(999)

    def test_start_task_wrong_status(self):
        svc, db = make_service()
        mock_task = MagicMock()
        mock_task.status = StageStatusEnum.COMPLETED.value
        db.query.return_value.filter.return_value.first.return_value = mock_task
        with pytest.raises(ValueError, match="无法开始"):
            svc.start_task(1)

    def test_start_task_success(self):
        svc, db = make_service()
        mock_task = MagicMock()
        mock_task.status = StageStatusEnum.PENDING.value
        db.query.return_value.filter.return_value.first.return_value = mock_task
        result = svc.start_task(1, actual_start_date=date(2024, 1, 1))
        assert result is mock_task
        assert mock_task.status == StageStatusEnum.IN_PROGRESS.value

    def test_complete_task_success(self):
        svc, db = make_service()
        mock_task = MagicMock()
        mock_task.status = StageStatusEnum.IN_PROGRESS.value
        mock_task.node_instance_id = 10
        db.query.return_value.filter.return_value.first.return_value = mock_task

        with patch.object(svc, "_check_node_auto_complete"):
            result = svc.complete_task(1, completed_by=5, actual_hours=8)
        assert result is mock_task
        assert mock_task.status == StageStatusEnum.COMPLETED.value

    def test_skip_task_success(self):
        svc, db = make_service()
        mock_task = MagicMock()
        mock_task.status = StageStatusEnum.PENDING.value
        mock_task.node_instance_id = 10
        db.query.return_value.filter.return_value.first.return_value = mock_task

        with patch.object(svc, "_check_node_auto_complete"):
            result = svc.skip_task(1, reason="不需要")
        assert result is mock_task
        assert mock_task.status == StageStatusEnum.SKIPPED.value


class TestGetNodeTaskProgress:
    def test_progress_empty_tasks(self):
        svc, db = make_service()
        db.query.return_value.filter.return_value.all.return_value = []
        result = svc.get_node_task_progress(node_instance_id=1)
        assert result["total"] == 0
        assert result["progress_pct"] == 0

    def test_progress_all_completed(self):
        svc, db = make_service()
        tasks = []
        for _ in range(3):
            t = MagicMock()
            t.status = StageStatusEnum.COMPLETED.value
            t.estimated_hours = 8
            t.actual_hours = 7
            tasks.append(t)
        db.query.return_value.filter.return_value.all.return_value = tasks
        result = svc.get_node_task_progress(node_instance_id=1)
        assert result["completed"] == 3
        assert result["progress_pct"] == 100.0

    def test_progress_mixed_statuses(self):
        svc, db = make_service()
        statuses = [
            StageStatusEnum.COMPLETED.value,
            StageStatusEnum.IN_PROGRESS.value,
            StageStatusEnum.PENDING.value,
            StageStatusEnum.SKIPPED.value,
        ]
        tasks = []
        for s in statuses:
            t = MagicMock()
            t.status = s
            t.estimated_hours = 4
            t.actual_hours = 3
            tasks.append(t)
        db.query.return_value.filter.return_value.all.return_value = tasks
        result = svc.get_node_task_progress(node_instance_id=1)
        assert result["total"] == 4
        assert result["completed"] == 1
        assert result["skipped"] == 1
