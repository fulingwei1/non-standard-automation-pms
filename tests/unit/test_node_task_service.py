# -*- coding: utf-8 -*-
"""
节点子任务服务单元测试

测试覆盖:
- 任务CRUD操作
- 任务状态流转
- 批量操作
- 进度统计
- 用户任务查询
"""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.services.node_task_service import NodeTaskService


class TestNodeTaskServiceInit:
    """服务初始化测试"""

    def test_init(self, db_session: Session):
        """测试服务初始化"""
        service = NodeTaskService(db_session)
        assert service.db == db_session


class TestGetTask:
    """获取任务测试"""

    def test_get_task_not_found(self, db_session: Session):
        """测试任务不存在时返回None"""
        service = NodeTaskService(db_session)
        result = service.get_task(99999)
        assert result is None


class TestListTasks:
    """获取任务列表测试"""

    def test_list_tasks_empty(self, db_session: Session):
        """测试节点无任务时返回空列表"""
        service = NodeTaskService(db_session)
        result = service.list_tasks(node_instance_id=99999)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_list_tasks_with_status_filter(self, db_session: Session):
        """测试按状态筛选"""
        service = NodeTaskService(db_session)
        result = service.list_tasks(node_instance_id=1, status='PENDING')
        assert isinstance(result, list)

    def test_list_tasks_with_assignee_filter(self, db_session: Session):
        """测试按执行人筛选"""
        service = NodeTaskService(db_session)
        result = service.list_tasks(node_instance_id=1, assignee_id=1)
        assert isinstance(result, list)


class TestCreateTask:
    """创建任务测试"""

    def test_create_task_node_not_found(self, db_session: Session):
        """测试节点不存在时抛出异常"""
        service = NodeTaskService(db_session)
        with pytest.raises(ValueError, match="节点实例.*不存在"):
            service.create_task(
                node_instance_id=99999,
                task_name="测试任务"
            )


class TestUpdateTask:
    """更新任务测试"""

    def test_update_task_not_found(self, db_session: Session):
        """测试任务不存在时返回None"""
        service = NodeTaskService(db_session)
        result = service.update_task(99999, task_name="新名称")
        assert result is None


class TestDeleteTask:
    """删除任务测试"""

    def test_delete_task_not_found(self, db_session: Session):
        """测试任务不存在时返回False"""
        service = NodeTaskService(db_session)
        result = service.delete_task(99999)
        assert result is False


class TestStartTask:
    """开始任务测试"""

    def test_start_task_not_found(self, db_session: Session):
        """测试任务不存在时抛出异常"""
        service = NodeTaskService(db_session)
        with pytest.raises(ValueError, match="任务.*不存在"):
            service.start_task(99999)


class TestCompleteTask:
    """完成任务测试"""

    def test_complete_task_not_found(self, db_session: Session):
        """测试任务不存在时抛出异常"""
        service = NodeTaskService(db_session)
        with pytest.raises(ValueError, match="任务.*不存在"):
            service.complete_task(99999)


class TestSkipTask:
    """跳过任务测试"""

    def test_skip_task_not_found(self, db_session: Session):
        """测试任务不存在时抛出异常"""
        service = NodeTaskService(db_session)
        with pytest.raises(ValueError, match="任务.*不存在"):
            service.skip_task(99999)


class TestAssignTask:
    """分配任务测试"""

    def test_assign_task_not_found(self, db_session: Session):
        """测试任务不存在时抛出异常"""
        service = NodeTaskService(db_session)
        with pytest.raises(ValueError, match="任务.*不存在"):
            service.assign_task(99999, assignee_id=1)


class TestSetTaskPriority:
    """设置任务优先级测试"""

    def test_set_task_priority_invalid(self, db_session: Session):
        """测试无效优先级时抛出异常"""
        service = NodeTaskService(db_session)
        with pytest.raises(ValueError, match="无效的优先级"):
            service.set_task_priority(1, priority="INVALID")

    def test_set_task_priority_task_not_found(self, db_session: Session):
        """测试任务不存在时抛出异常"""
        service = NodeTaskService(db_session)
        with pytest.raises(ValueError, match="任务.*不存在"):
            service.set_task_priority(99999, priority="HIGH")


class TestGetNodeTaskProgress:
    """获取节点任务进度测试"""

    def test_get_node_task_progress_empty(self, db_session: Session):
        """测试无任务时的进度统计"""
        service = NodeTaskService(db_session)
        result = service.get_node_task_progress(node_instance_id=99999)

        assert result['total'] == 0
        assert result['completed'] == 0
        assert result['in_progress'] == 0
        assert result['pending'] == 0
        assert result['skipped'] == 0
        assert result['progress_pct'] == 0
        assert result['total_estimated_hours'] == 0
        assert result['total_actual_hours'] == 0


class TestGetUserTasks:
    """获取用户任务测试"""

    def test_get_user_tasks_empty(self, db_session: Session):
        """测试用户无任务时返回空列表"""
        service = NodeTaskService(db_session)
        result = service.get_user_tasks(user_id=99999)
        assert isinstance(result, list)

    def test_get_user_tasks_with_project_filter(self, db_session: Session):
        """测试按项目筛选"""
        service = NodeTaskService(db_session)
        result = service.get_user_tasks(user_id=1, project_id=1)
        assert isinstance(result, list)

    def test_get_user_tasks_with_status_filter(self, db_session: Session):
        """测试按状态筛选"""
        service = NodeTaskService(db_session)
        result = service.get_user_tasks(user_id=1, status='PENDING')
        assert isinstance(result, list)


class TestReorderTasks:
    """重新排序任务测试"""

    def test_reorder_tasks_empty_list(self, db_session: Session):
        """测试空列表排序"""
        service = NodeTaskService(db_session)
        result = service.reorder_tasks(node_instance_id=1, task_ids=[])
        assert result is True


class TestBatchCreateTasks:
    """批量创建任务测试"""

    def test_batch_create_tasks_node_not_found(self, db_session: Session):
        """测试节点不存在时抛出异常"""
        service = NodeTaskService(db_session)
        with pytest.raises(ValueError):
            service.batch_create_tasks(
                node_instance_id=99999,
                tasks_data=[{"task_name": "任务1"}]
            )
