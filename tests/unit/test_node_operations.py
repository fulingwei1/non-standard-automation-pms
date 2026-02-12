# -*- coding: utf-8 -*-
"""节点操作 单元测试"""
from unittest.mock import MagicMock

import pytest

from app.models.enums import StageStatusEnum
from app.services.stage_instance.node_operations import NodeOperationsMixin


def _make_mixin():
    m = NodeOperationsMixin()
    m.db = MagicMock()
    m._check_node_dependencies = MagicMock(return_value=True)
    m.start_stage = MagicMock()
    m._check_tasks_completion = MagicMock()
    m._validate_node_completion = MagicMock()
    m._try_auto_complete_next_nodes = MagicMock()
    m._check_stage_completion = MagicMock()
    return m


def _make_node(status="PENDING", project_id=1):
    n = MagicMock()
    n.id = 1
    n.status = status
    n.project_id = project_id
    n.stage_instance = MagicMock()
    n.stage_instance.id = 10
    n.stage_instance.status = StageStatusEnum.PENDING.value
    return n


class TestStartNode:
    def test_success(self):
        m = _make_mixin()
        node = _make_node(status=StageStatusEnum.PENDING.value)
        m.db.query.return_value.filter.return_value.first.return_value = node
        result = m.start_node(1)
        assert result.status == StageStatusEnum.IN_PROGRESS.value

    def test_not_found(self):
        m = _make_mixin()
        m.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            m.start_node(999)

    def test_wrong_status(self):
        m = _make_mixin()
        node = _make_node(status=StageStatusEnum.COMPLETED.value)
        m.db.query.return_value.filter.return_value.first.return_value = node
        with pytest.raises(ValueError, match="无法开始"):
            m.start_node(1)

    def test_dependency_not_met(self):
        m = _make_mixin()
        m._check_node_dependencies.return_value = False
        node = _make_node(status=StageStatusEnum.PENDING.value)
        m.db.query.return_value.filter.return_value.first.return_value = node
        with pytest.raises(ValueError, match="依赖"):
            m.start_node(1)


class TestCompleteNode:
    def test_not_found(self):
        m = _make_mixin()
        m.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            m.complete_node(999)

    def test_wrong_status(self):
        m = _make_mixin()
        node = _make_node(status=StageStatusEnum.COMPLETED.value)
        m.db.query.return_value.filter.return_value.first.return_value = node
        with pytest.raises(ValueError, match="无法完成"):
            m.complete_node(1)


class TestSkipNode:
    def test_success(self):
        m = _make_mixin()
        node = _make_node(status=StageStatusEnum.PENDING.value)
        m.db.query.return_value.filter.return_value.first.return_value = node
        result = m.skip_node(1, reason="跳过")
        assert result.status == StageStatusEnum.SKIPPED.value

    def test_not_found(self):
        m = _make_mixin()
        m.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            m.skip_node(999)


class TestAssignNode:
    def test_success(self):
        m = _make_mixin()
        node = _make_node()
        m.db.query.return_value.filter.return_value.first.return_value = node
        result = m.assign_node(1, assignee_id=42)
        assert result.assignee_id == 42

    def test_not_found(self):
        m = _make_mixin()
        m.db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError, match="不存在"):
            m.assign_node(999, assignee_id=1)
