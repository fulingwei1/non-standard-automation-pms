# -*- coding: utf-8 -*-
"""第二十批 - node_operations 单元测试"""
import pytest
pytest.importorskip("app.services.stage_instance.node_operations")

from unittest.mock import MagicMock, patch
from app.services.stage_instance.node_operations import NodeOperationsMixin
from app.models.enums import StageStatusEnum


class ConcreteNodeOps(NodeOperationsMixin):
    """具体测试类"""
    def __init__(self, db):
        self.db = db

    def _check_node_dependencies(self, node):
        return True

    def _check_tasks_completion(self, node):
        pass

    def _validate_node_completion(self, node, attachments, approval_record_id):
        pass

    def _try_auto_complete_next_nodes(self, node):
        pass

    def _check_stage_completion(self, stage_instance_id):
        pass

    def start_stage(self, stage_id):
        pass


def make_db():
    return MagicMock()


def make_node_instance(id=1, status="PENDING", project_id=10, stage_instance_id=5):
    n = MagicMock()
    n.id = id
    n.status = status
    n.project_id = project_id
    n.stage_instance_id = stage_instance_id
    n.stage_instance = MagicMock()
    n.stage_instance.status = StageStatusEnum.PENDING.value
    n.stage_instance.id = stage_instance_id
    return n


class TestStartNode:
    def test_start_node_not_found_raises(self):
        db = make_db()
        svc = ConcreteNodeOps(db)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q
        with pytest.raises(ValueError, match="不存在"):
            svc.start_node(node_instance_id=999)

    def test_start_node_wrong_status_raises(self):
        db = make_db()
        svc = ConcreteNodeOps(db)
        node = make_node_instance(status=StageStatusEnum.COMPLETED.value)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = node
        db.query.return_value = q
        with pytest.raises(ValueError):
            svc.start_node(node_instance_id=1)

    def test_start_node_dependencies_not_met_raises(self):
        db = make_db()
        svc = ConcreteNodeOps(db)
        svc._check_node_dependencies = lambda n: False
        node = make_node_instance(status=StageStatusEnum.PENDING.value)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = node
        q.update.return_value = 1
        db.query.return_value = q
        with pytest.raises(ValueError, match="前置依赖"):
            svc.start_node(node_instance_id=1)

    def test_start_node_success(self):
        db = make_db()
        svc = ConcreteNodeOps(db)
        node = make_node_instance(status=StageStatusEnum.PENDING.value)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = node
        q.update.return_value = 1
        db.query.return_value = q
        result = svc.start_node(node_instance_id=1)
        assert node.status == StageStatusEnum.IN_PROGRESS.value
        db.flush.assert_called_once()
        assert result is node


class TestCompleteNode:
    def test_complete_node_not_found_raises(self):
        db = make_db()
        svc = ConcreteNodeOps(db)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q
        with pytest.raises(ValueError, match="不存在"):
            svc.complete_node(node_instance_id=999)

    def test_complete_node_wrong_status_raises(self):
        db = make_db()
        svc = ConcreteNodeOps(db)
        node = make_node_instance(status=StageStatusEnum.SKIPPED.value)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = node
        db.query.return_value = q
        with pytest.raises(ValueError):
            svc.complete_node(node_instance_id=1)

    def test_complete_node_success(self):
        db = make_db()
        svc = ConcreteNodeOps(db)
        node = make_node_instance(status=StageStatusEnum.IN_PROGRESS.value)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = node
        db.query.return_value = q
        result = svc.complete_node(node_instance_id=1, completed_by=42, remark="done")
        assert node.status == StageStatusEnum.COMPLETED.value
        assert node.completed_by == 42
        assert node.remark == "done"
        assert result is node


class TestSkipNode:
    def test_skip_node_not_found_raises(self):
        db = make_db()
        svc = ConcreteNodeOps(db)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q
        with pytest.raises(ValueError, match="不存在"):
            svc.skip_node(node_instance_id=999)

    def test_skip_node_success(self):
        db = make_db()
        svc = ConcreteNodeOps(db)
        node = make_node_instance(status=StageStatusEnum.PENDING.value)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = node
        db.query.return_value = q
        result = svc.skip_node(node_instance_id=1, reason="不需要")
        assert node.status == StageStatusEnum.SKIPPED.value
        assert node.remark == "不需要"
        assert result is node


class TestAssignNode:
    def test_assign_node_not_found_raises(self):
        db = make_db()
        svc = ConcreteNodeOps(db)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q
        with pytest.raises(ValueError, match="不存在"):
            svc.assign_node(node_instance_id=999, assignee_id=1)

    def test_assign_node_success(self):
        db = make_db()
        svc = ConcreteNodeOps(db)
        node = make_node_instance()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = node
        db.query.return_value = q
        result = svc.assign_node(node_instance_id=1, assignee_id=7)
        assert node.assignee_id == 7
        assert result is node
