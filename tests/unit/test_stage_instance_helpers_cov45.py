# -*- coding: utf-8 -*-
"""
第四十五批覆盖：stage_instance/helpers.py
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

pytest.importorskip("app.services.stage_instance.helpers")

from app.services.stage_instance.helpers import HelpersMixin


class ConcreteHelpers(HelpersMixin):
    def __init__(self, db):
        self.db = db


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def helper(mock_db):
    return ConcreteHelpers(mock_db)


def _make_node(node_id=1, status="PENDING", completion_method="MANUAL", dependency_ids=None):
    node = MagicMock()
    node.id = node_id
    node.status = status
    node.completion_method = completion_method
    node.dependency_node_instance_ids = dependency_ids or []
    node.stage_instance_id = 10
    node.node_definition = None
    node.attachments = None
    return node


class TestCheckTasksCompletion:
    def test_no_tasks_no_error(self, helper, mock_db):
        node = _make_node()
        mock_db.query.return_value.filter.return_value.all.return_value = []
        # Should not raise
        helper._check_tasks_completion(node)

    def test_all_tasks_completed_no_error(self, helper, mock_db):
        node = _make_node()
        task = MagicMock(status="COMPLETED")
        mock_db.query.return_value.filter.return_value.all.return_value = [task]
        helper._check_tasks_completion(node)

    def test_incomplete_tasks_raises(self, helper, mock_db):
        node = _make_node()
        task = MagicMock(status="IN_PROGRESS")
        mock_db.query.return_value.filter.return_value.all.return_value = [task]
        with pytest.raises(ValueError, match="子任务未完成"):
            helper._check_tasks_completion(node)


class TestCheckNodeDependencies:
    def test_no_dependencies_returns_true(self, helper, mock_db):
        node = _make_node(dependency_ids=[])
        assert helper._check_node_dependencies(node) is True

    def test_all_dependencies_complete(self, helper, mock_db):
        node = _make_node(dependency_ids=[1, 2])
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        assert helper._check_node_dependencies(node) is True

    def test_incomplete_dependency(self, helper, mock_db):
        node = _make_node(dependency_ids=[1, 2])
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        assert helper._check_node_dependencies(node) is False


class TestValidateNodeCompletion:
    def test_raises_if_dependencies_not_met(self, helper, mock_db):
        node = _make_node(dependency_ids=[99])
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        with pytest.raises(ValueError, match="前置依赖节点未完成"):
            helper._validate_node_completion(node, None, None)

    def test_raises_if_no_attachments_required(self, helper, mock_db):
        node = _make_node(dependency_ids=[])
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        node_def = MagicMock(required_attachments=True)
        node.node_definition = node_def
        node.attachments = None
        with pytest.raises(ValueError, match="上传附件"):
            helper._validate_node_completion(node, None, None)

    def test_approval_method_requires_record(self, helper, mock_db):
        node = _make_node(dependency_ids=[])
        mock_db.query.return_value.filter.return_value.count.return_value = 0
        node.completion_method = "APPROVAL"
        node.node_definition = None
        with pytest.raises(ValueError, match="审批记录"):
            helper._validate_node_completion(node, None, None)


class TestCheckAutoCondition:
    def test_no_node_def_returns_true(self, helper, mock_db):
        node = _make_node()
        node.node_definition = None
        assert helper._check_auto_condition(node) is True

    def test_all_dependencies_condition(self, helper, mock_db):
        node = _make_node()
        node_def = MagicMock(auto_condition={"type": "all_dependencies"})
        node.node_definition = node_def
        assert helper._check_auto_condition(node) is True

    def test_tasks_complete_condition_no_tasks(self, helper, mock_db):
        node = _make_node()
        node_def = MagicMock(auto_condition={"type": "tasks_complete"})
        node.node_definition = node_def
        mock_db.query.return_value.filter.return_value.all.return_value = []
        assert helper._check_auto_condition(node) is True
