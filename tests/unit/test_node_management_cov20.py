# -*- coding: utf-8 -*-
"""第二十批 - node_management 单元测试"""
import pytest
pytest.importorskip("app.services.stage_template.node_management")

from unittest.mock import MagicMock, patch, PropertyMock
from app.services.stage_template.node_management import NodeManagementMixin


class ConcreteNodeMgmt(NodeManagementMixin):
    """具体测试类"""
    def __init__(self, db):
        self.db = db

    def _remove_node_from_dependencies(self, node_id):
        pass

    def _has_circular_dependency(self, node_id, dep_ids, template_id):
        return False


def make_db():
    return MagicMock()


def make_node(id=1, stage_definition_id=10):
    n = MagicMock()
    n.id = id
    n.stage_definition_id = stage_definition_id
    n.node_code = "N001"
    n.node_name = "节点一"
    return n


class TestAddNode:
    def test_add_node_stage_not_found_raises(self):
        db = make_db()
        svc = ConcreteNodeMgmt(db)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q
        with pytest.raises(ValueError, match="不存在"):
            svc.add_node(stage_definition_id=99, node_code="X", node_name="节点")

    def test_add_node_success(self):
        db = make_db()
        svc = ConcreteNodeMgmt(db)
        stage = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = stage
        db.query.return_value = q

        with patch("app.services.stage_template.node_management.NodeDefinition") as MockNode:
            mock_node = MagicMock()
            MockNode.return_value = mock_node
            result = svc.add_node(
                stage_definition_id=1,
                node_code="N001",
                node_name="节点一",
            )
            db.add.assert_called_once_with(mock_node)
            db.flush.assert_called_once()
            assert result is mock_node

    def test_add_node_with_optional_params(self):
        db = make_db()
        svc = ConcreteNodeMgmt(db)
        stage = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = stage
        db.query.return_value = q

        with patch("app.services.stage_template.node_management.NodeDefinition") as MockNode:
            mock_node = MagicMock()
            MockNode.return_value = mock_node
            svc.add_node(
                stage_definition_id=1,
                node_code="N002",
                node_name="节点二",
                estimated_days=3,
                completion_method="APPROVAL",
                dependency_node_ids=[10, 11],
            )
            MockNode.assert_called_once()


class TestUpdateNode:
    def test_update_node_not_found_returns_none(self):
        db = make_db()
        svc = ConcreteNodeMgmt(db)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q
        result = svc.update_node(node_id=999, node_name="新名称")
        assert result is None

    def test_update_node_success(self):
        db = make_db()
        svc = ConcreteNodeMgmt(db)
        node = MagicMock()
        node.id = 1
        # hasattr returns True for any attribute on MagicMock
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = node
        db.query.return_value = q
        result = svc.update_node(node_id=1, node_name="更新名称", estimated_days=5)
        db.flush.assert_called_once()
        assert result is node


class TestDeleteNode:
    def test_delete_node_not_found_returns_false(self):
        db = make_db()
        svc = ConcreteNodeMgmt(db)
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = None
        db.query.return_value = q
        assert svc.delete_node(999) is False

    def test_delete_node_success(self):
        db = make_db()
        svc = ConcreteNodeMgmt(db)
        node = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.first.return_value = node
        db.query.return_value = q
        result = svc.delete_node(1)
        db.delete.assert_called_once_with(node)
        assert result is True


class TestReorderNodes:
    def test_reorder_nodes_updates_sequence(self):
        db = make_db()
        svc = ConcreteNodeMgmt(db)
        q = MagicMock()
        q.filter.return_value = q
        q.update.return_value = 1
        db.query.return_value = q
        result = svc.reorder_nodes(stage_id=1, node_ids=[3, 1, 2])
        assert result is True
        db.flush.assert_called_once()
