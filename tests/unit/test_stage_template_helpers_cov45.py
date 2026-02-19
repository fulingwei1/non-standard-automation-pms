# -*- coding: utf-8 -*-
"""
第四十五批覆盖：stage_template/helpers.py
"""

import pytest
from unittest.mock import MagicMock, call

pytest.importorskip("app.services.stage_template.helpers")

from app.services.stage_template.helpers import HelpersMixin


class ConcreteTemplateHelpers(HelpersMixin):
    def __init__(self, db):
        self.db = db


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def helper(mock_db):
    return ConcreteTemplateHelpers(mock_db)


class TestClearDefaultTemplate:
    def test_clears_default_flag(self, helper, mock_db):
        mock_db.query.return_value.filter.return_value.update.return_value = 2
        helper._clear_default_template("PRODUCT")
        mock_db.query.return_value.filter.return_value.update.assert_called_once_with(
            {"is_default": False}
        )


class TestRemoveNodeFromDependencies:
    def test_removes_node_from_deps(self, helper, mock_db):
        node = MagicMock()
        node.dependency_node_ids = [1, 2, 3]
        mock_db.query.return_value.filter.return_value.all.return_value = [node]

        helper._remove_node_from_dependencies(2)
        assert node.dependency_node_ids == [1, 3]

    def test_node_not_in_deps_unchanged(self, helper, mock_db):
        node = MagicMock()
        node.dependency_node_ids = [1, 3]
        mock_db.query.return_value.filter.return_value.all.return_value = [node]

        helper._remove_node_from_dependencies(99)
        assert node.dependency_node_ids == [1, 3]

    def test_no_nodes_with_deps(self, helper, mock_db):
        mock_db.query.return_value.filter.return_value.all.return_value = []
        # Should not raise
        helper._remove_node_from_dependencies(5)

    def test_empty_deps_after_removal_set_to_none(self, helper, mock_db):
        node = MagicMock()
        node.dependency_node_ids = [5]
        mock_db.query.return_value.filter.return_value.all.return_value = [node]

        helper._remove_node_from_dependencies(5)
        assert node.dependency_node_ids is None


class TestHasCircularDependency:
    def test_no_circular_dependency(self, helper, mock_db):
        # dep_id=2 depends on dep_id=3, not on node_id=1
        dep_node = MagicMock()
        dep_node.id = 2
        dep_node.dependency_node_ids = [3]
        third_node = MagicMock()
        third_node.dependency_node_ids = []

        mock_db.query.return_value.filter.return_value.first.side_effect = [dep_node, third_node]
        result = helper._has_circular_dependency(1, [2], template_id=10)
        assert result is False

    def test_circular_dependency_detected(self, helper, mock_db):
        # node_id=1, new_dep=[2], node 2 -> [1] => circular
        dep_node = MagicMock()
        dep_node.id = 2
        dep_node.dependency_node_ids = [1]  # points back to node_id=1

        mock_db.query.return_value.filter.return_value.first.return_value = dep_node
        result = helper._has_circular_dependency(1, [2], template_id=10)
        assert result is True

    def test_no_new_deps_no_circular(self, helper, mock_db):
        result = helper._has_circular_dependency(1, [], template_id=10)
        assert result is False


class TestGetDependencyCodes:
    def test_returns_codes_for_deps(self, helper, mock_db):
        node = MagicMock()
        node.dependency_node_ids = [1, 2]

        dep1 = MagicMock(node_code="N001")
        dep2 = MagicMock(node_code="N002")
        mock_db.query.return_value.filter.return_value.all.return_value = [dep1, dep2]

        result = helper._get_dependency_codes(node)
        assert "N001" in result
        assert "N002" in result

    def test_no_deps_returns_empty(self, helper, mock_db):
        node = MagicMock()
        node.dependency_node_ids = None
        result = helper._get_dependency_codes(node)
        assert result == []
