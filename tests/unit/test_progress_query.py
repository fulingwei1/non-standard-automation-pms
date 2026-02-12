# -*- coding: utf-8 -*-
"""进度查询模块 单元测试"""
from unittest.mock import MagicMock

import pytest

from app.models.enums import StageStatusEnum
from app.services.stage_instance.progress_query import ProgressQueryMixin


def _make_mixin():
    m = ProgressQueryMixin()
    m.db = MagicMock()
    m._check_node_dependencies = MagicMock(return_value=True)
    return m


def _make_node(status="COMPLETED", sequence=0):
    n = MagicMock()
    n.id = 1
    n.node_code = "N01"
    n.node_name = "节点1"
    n.node_type = "TASK"
    n.status = status
    n.sequence = sequence
    n.completion_method = "MANUAL"
    n.is_required = True
    n.planned_date = None
    n.actual_date = None
    n.completed_by = None
    n.completed_at = None
    n.attachments = None
    n.dependency_node_instance_ids = None
    return n


def _make_stage(status="COMPLETED", sequence=1, nodes=None):
    s = MagicMock()
    s.id = 1
    s.stage_code = "S01"
    s.stage_name = "阶段1"
    s.status = status
    s.sequence = sequence
    s.nodes = nodes or []
    s.planned_start_date = None
    s.planned_end_date = None
    s.actual_start_date = None
    s.actual_end_date = None
    s.is_modified = False
    s.remark = None
    s.project_id = 1
    return s


class TestGetProjectProgress:
    def test_empty_project(self):
        m = _make_mixin()
        m.db.query.return_value.filter.return_value.options.return_value.order_by.return_value.all.return_value = []
        result = m.get_project_progress(1)
        assert result["total_stages"] == 0
        assert result["progress_pct"] == 0

    def test_with_completed_stage(self):
        m = _make_mixin()
        node = _make_node(status=StageStatusEnum.COMPLETED.value)
        stage = _make_stage(status=StageStatusEnum.COMPLETED.value, nodes=[node])
        m.db.query.return_value.filter.return_value.options.return_value.order_by.return_value.all.return_value = [stage]
        result = m.get_project_progress(1)
        assert result["total_stages"] == 1
        assert result["completed_stages"] == 1
        assert result["progress_pct"] == 100.0

    def test_current_stage_detected(self):
        m = _make_mixin()
        node = _make_node(status=StageStatusEnum.PENDING.value)
        stage = _make_stage(status=StageStatusEnum.IN_PROGRESS.value, nodes=[node])
        m.db.query.return_value.filter.return_value.options.return_value.order_by.return_value.all.return_value = [stage]
        result = m.get_project_progress(1)
        assert result["current_stage"] is not None


class TestGetStageDetail:
    def test_not_found(self):
        m = _make_mixin()
        m.db.query.return_value.options.return_value.filter.return_value.first.return_value = None
        result = m.get_stage_detail(999)
        assert result is None

    def test_returns_detail(self):
        m = _make_mixin()
        node = _make_node()
        stage = _make_stage(nodes=[node])
        m.db.query.return_value.options.return_value.filter.return_value.first.return_value = stage
        result = m.get_stage_detail(1)
        assert result is not None
        assert len(result["nodes"]) == 1
