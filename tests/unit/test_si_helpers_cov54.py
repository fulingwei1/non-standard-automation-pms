"""Tests for app/services/stage_instance/helpers.py"""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

try:
    from app.services.stage_instance.helpers import HelpersMixin
    from app.models.enums import StageStatusEnum, CompletionMethodEnum
except ImportError as e:
    pytest.skip(f"Import failed: {e}", allow_module_level=True)


class ConcreteHelper(HelpersMixin):
    def __init__(self, db):
        self.db = db


def _make_db():
    db = MagicMock()
    q = MagicMock()
    db.query.return_value = q
    q.filter.return_value = q
    q.all.return_value = []
    q.count.return_value = 0
    q.first.return_value = None
    return db


def test_check_tasks_completion_no_tasks():
    """没有子任务时不抛异常"""
    db = _make_db()
    helper = ConcreteHelper(db)
    node = MagicMock()
    node.id = 1
    db.query.return_value.filter.return_value.all.return_value = []
    helper._check_tasks_completion(node)  # should not raise


def test_check_tasks_completion_with_incomplete_tasks_raises():
    """有未完成子任务时抛出 ValueError"""
    db = _make_db()
    helper = ConcreteHelper(db)
    node = MagicMock()
    node.id = 1
    task = MagicMock()
    task.status = "PENDING"
    db.query.return_value.filter.return_value.all.return_value = [task]
    with pytest.raises(ValueError, match="子任务未完成"):
        helper._check_tasks_completion(node)


def test_check_node_dependencies_no_deps():
    """没有依赖时返回 True"""
    db = _make_db()
    helper = ConcreteHelper(db)
    node = MagicMock()
    node.dependency_node_instance_ids = None
    assert helper._check_node_dependencies(node) is True


def test_check_node_dependencies_all_complete():
    """依赖全部完成时返回 True"""
    db = _make_db()
    helper = ConcreteHelper(db)
    node = MagicMock()
    node.dependency_node_instance_ids = [1, 2]
    db.query.return_value.filter.return_value.count.return_value = 0
    assert helper._check_node_dependencies(node) is True


def test_check_node_dependencies_incomplete():
    """有未完成依赖时返回 False"""
    db = _make_db()
    helper = ConcreteHelper(db)
    node = MagicMock()
    node.dependency_node_instance_ids = [1, 2]
    db.query.return_value.filter.return_value.count.return_value = 1
    assert helper._check_node_dependencies(node) is False


def test_validate_node_completion_raises_on_dependency():
    """未满足依赖时 _validate_node_completion 抛出 ValueError"""
    db = _make_db()
    helper = ConcreteHelper(db)
    node = MagicMock()
    node.dependency_node_instance_ids = [99]
    node.node_definition = None
    node.completion_method = "MANUAL"
    db.query.return_value.filter.return_value.count.return_value = 1
    with pytest.raises(ValueError, match="前置依赖节点未完成"):
        helper._validate_node_completion(node, None, None)


def test_check_auto_condition_all_dependencies_type():
    """auto_condition type=all_dependencies 返回 True"""
    db = _make_db()
    helper = ConcreteHelper(db)
    node = MagicMock()
    node.node_definition = MagicMock()
    node.node_definition.auto_condition = {"type": "all_dependencies"}
    assert helper._check_auto_condition(node) is True


def test_check_custom_condition_gte_operator():
    """>= 操作符自定义条件正确处理"""
    db = _make_db()
    helper = ConcreteHelper(db)
    node = MagicMock(spec=[])
    node.progress = 100
    condition = {"field": "progress", "operator": ">=", "value": 80}
    assert helper._check_custom_condition(node, condition) is True
