"""Tests for app/services/stage_template/helpers.py"""
import pytest
from unittest.mock import MagicMock, patch

try:
    from app.services.stage_template.helpers import HelpersMixin
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


def test_clear_default_template_calls_update():
    """_clear_default_template 执行 update 操作"""
    db = _make_db()
    update_mock = MagicMock()
    db.query.return_value.filter.return_value.update = update_mock
    helper = ConcreteHelper(db)
    helper._clear_default_template("type_A")
    update_mock.assert_called_once_with({"is_default": False})


def test_remove_node_from_dependencies_no_nodes():
    """没有引用该节点的节点时静默成功"""
    db = _make_db()
    db.query.return_value.filter.return_value.all.return_value = []
    helper = ConcreteHelper(db)
    helper._remove_node_from_dependencies(42)  # should not raise


def test_remove_node_from_dependencies_removes_id():
    """从依赖列表中移除指定节点ID"""
    db = _make_db()
    node = MagicMock()
    node.dependency_node_ids = [10, 42, 30]
    db.query.return_value.filter.return_value.all.return_value = [node]
    helper = ConcreteHelper(db)
    helper._remove_node_from_dependencies(42)
    assert 42 not in node.dependency_node_ids


def test_has_circular_dependency_no_cycle():
    """无循环依赖时返回 False"""
    db = _make_db()
    # Dependency node has no further deps
    dep_node = MagicMock()
    dep_node.dependency_node_ids = None
    db.query.return_value.filter.return_value.first.return_value = dep_node
    helper = ConcreteHelper(db)
    result = helper._has_circular_dependency(100, [200], 1)
    assert result is False


def test_has_circular_dependency_detects_cycle():
    """存在循环依赖时返回 True"""
    db = _make_db()
    # dep_node (id=200) points back to node_id=100 => cycle
    dep_node = MagicMock()
    dep_node.dependency_node_ids = [100]
    db.query.return_value.filter.return_value.first.return_value = dep_node
    helper = ConcreteHelper(db)
    result = helper._has_circular_dependency(100, [200], 1)
    assert result is True


def test_get_dependency_codes_no_deps():
    """没有依赖时返回空列表"""
    db = _make_db()
    node = MagicMock()
    node.dependency_node_ids = None
    helper = ConcreteHelper(db)
    result = helper._get_dependency_codes(node)
    assert result == []


def test_get_dependency_codes_returns_codes():
    """有依赖时返回对应节点编码列表"""
    db = _make_db()
    dep1 = MagicMock()
    dep1.node_code = "N01"
    dep2 = MagicMock()
    dep2.node_code = "N02"
    db.query.return_value.filter.return_value.all.return_value = [dep1, dep2]
    node = MagicMock()
    node.dependency_node_ids = [1, 2]
    helper = ConcreteHelper(db)
    result = helper._get_dependency_codes(node)
    assert "N01" in result
    assert "N02" in result
