# -*- coding: utf-8 -*-
"""节点管理模块 单元测试"""
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from app.services.stage_template.node_management import NodeManagementMixin


def _make_mixin():
    mixin = NodeManagementMixin()
    mixin.db = MagicMock()
    return mixin


class TestAddNode:
    def test_add_node_success(self):
        mixin = _make_mixin()
        stage = MagicMock()
        mixin.db.query.return_value.filter.return_value.first.return_value = stage

        with patch("app.services.stage_template.node_management.NodeDefinition") as MockND:
            instance = MagicMock()
            MockND.return_value = instance
            result = mixin.add_node(
                stage_definition_id=1,
                node_code="N01",
                node_name="测试节点",
            )
            mixin.db.add.assert_called_once_with(instance)
            mixin.db.flush.assert_called_once()

    def test_add_node_stage_not_found(self):
        mixin = _make_mixin()
        mixin.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            mixin.add_node(stage_definition_id=999, node_code="N01", node_name="X")


class TestUpdateNode:
    def test_update_success(self):
        mixin = _make_mixin()
        node = MagicMock()
        node.id = 1
        mixin.db.query.return_value.filter.return_value.first.return_value = node
        result = mixin.update_node(1, node_name="新名称")
        assert result is not None
        mixin.db.flush.assert_called()

    def test_update_not_found(self):
        mixin = _make_mixin()
        mixin.db.query.return_value.filter.return_value.first.return_value = None
        result = mixin.update_node(999)
        assert result is None


class TestDeleteNode:
    def test_delete_success(self):
        mixin = _make_mixin()
        mixin._remove_node_from_dependencies = MagicMock()
        node = MagicMock()
        mixin.db.query.return_value.filter.return_value.first.return_value = node
        assert mixin.delete_node(1) is True
        mixin.db.delete.assert_called_once_with(node)

    def test_delete_not_found(self):
        mixin = _make_mixin()
        mixin.db.query.return_value.filter.return_value.first.return_value = None
        assert mixin.delete_node(999) is False


class TestReorderNodes:
    def test_reorder(self):
        mixin = _make_mixin()
        result = mixin.reorder_nodes(1, [3, 1, 2])
        assert result is True
        mixin.db.flush.assert_called()


class TestSetNodeDependencies:
    def test_node_not_found(self):
        mixin = _make_mixin()
        mixin.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            mixin.set_node_dependencies(999, [1])
