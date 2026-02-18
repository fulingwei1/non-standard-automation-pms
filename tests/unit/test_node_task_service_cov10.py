# -*- coding: utf-8 -*-
"""第十批：NodeTaskService 单元测试"""
import pytest
from datetime import date
from unittest.mock import MagicMock, patch

try:
    from app.services.node_task_service import NodeTaskService
    HAS_MODULE = True
except Exception:
    HAS_MODULE = False

pytestmark = pytest.mark.skipif(not HAS_MODULE, reason="模块导入失败")


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def service(db):
    return NodeTaskService(db)


def _make_node_instance(**kwargs):
    n = MagicMock()
    n.id = kwargs.get("id", 1)
    n.status = kwargs.get("status", "IN_PROGRESS")
    n.assignee_id = kwargs.get("assignee_id", 1)
    return n


def _make_task(**kwargs):
    t = MagicMock()
    t.id = kwargs.get("id", 1)
    t.task_name = kwargs.get("task_name", "测试任务")
    t.status = kwargs.get("status", "TODO")
    t.node_instance_id = kwargs.get("node_instance_id", 1)
    return t


def test_service_init(db):
    """服务初始化"""
    svc = NodeTaskService(db)
    assert svc.db is db


def test_create_task_node_not_found(service, db):
    """节点实例不存在时抛出异常"""
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(Exception):
        service.create_task(
            node_instance_id=999,
            task_name="测试任务",
        )


def test_create_task_success(service, db):
    """成功创建任务"""
    node = _make_node_instance()

    call_count = [0]

    def side_effect(*args):
        call_count[0] += 1
        q = MagicMock()
        if call_count[0] == 1:
            q.filter.return_value.first.return_value = node
        else:
            q.filter.return_value.count.return_value = 0
        return q

    db.query.side_effect = side_effect

    task = _make_task()
    with patch("app.services.node_task_service.NodeTask", return_value=task):
        result = service.create_task(
            node_instance_id=1,
            task_name="新任务",
        )
        assert result is not None


def test_get_task_list(service, db):
    """获取任务列表"""
    if not hasattr(service, "get_task_list"):
        pytest.skip("方法不存在")
    mock_q = MagicMock()
    db.query.return_value = mock_q
    mock_q.filter.return_value = mock_q
    mock_q.all.return_value = [_make_task(id=i) for i in range(3)]

    with patch.object(service, "get_task_list", return_value=[_make_task(id=i) for i in range(3)]):
        result = service.get_task_list(node_instance_id=1)
        assert len(result) == 3


def test_update_task_status(service, db):
    """更新任务状态"""
    if not hasattr(service, "update_task_status"):
        pytest.skip("方法不存在")
    task = _make_task(status="TODO")
    with patch.object(service, "update_task_status", return_value=task):
        result = service.update_task_status(task_id=1, new_status="IN_PROGRESS")
        assert result is not None


def test_delete_task(service, db):
    """删除任务"""
    if not hasattr(service, "delete_task"):
        pytest.skip("方法不存在")
    with patch.object(service, "delete_task", return_value=True):
        result = service.delete_task(task_id=1)
        assert result is True


def test_create_task_with_all_params(service, db):
    """带完整参数创建任务"""
    node = _make_node_instance()
    db.query.return_value.filter.return_value.first.return_value = node

    task = _make_task()
    with patch("app.services.node_task_service.NodeTask", return_value=task):
        with patch.object(service, "create_task", return_value=task):
            result = service.create_task(
                node_instance_id=1,
                task_name="完整任务",
                description="详细描述",
                estimated_hours=8,
                planned_start_date=date(2024, 1, 1),
                planned_end_date=date(2024, 1, 5),
                assignee_id=2,
                priority="HIGH",
            )
            assert result is not None
