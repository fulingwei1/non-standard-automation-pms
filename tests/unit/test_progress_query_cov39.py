# -*- coding: utf-8 -*-
"""
第三十九批覆盖率测试 - stage_instance/progress_query.py
"""
import pytest
from datetime import date
from unittest.mock import MagicMock

pytest.importorskip("app.services.stage_instance.progress_query",
                    reason="import failed, skip")

from app.services.stage_instance.progress_query import ProgressQueryMixin


def _make_node(nid, status="PENDING", sequence=0):
    n = MagicMock()
    n.id = nid
    n.node_code = f"N{nid:03d}"
    n.node_name = f"节点{nid}"
    n.node_type = "TASK"
    n.status = status
    n.sequence = sequence
    n.completion_method = "MANUAL"
    n.is_required = True
    n.planned_date = None
    n.actual_date = None
    n.completed_by = None
    n.completed_at = None
    n.attachments = []
    n.dependency_node_instance_ids = []
    return n


def _make_stage(sid, status="PENDING", sequence=0, nodes=None):
    s = MagicMock()
    s.id = sid
    s.stage_code = f"S{sid:02d}"
    s.stage_name = f"阶段{sid}"
    s.status = status
    s.sequence = sequence
    s.planned_start_date = date(2024, 1, 1)
    s.planned_end_date = date(2024, 2, 1)
    s.actual_start_date = None
    s.actual_end_date = None
    s.is_modified = False
    s.remark = None
    s.nodes = nodes or []
    return s


class ConcreteProgressService(ProgressQueryMixin):
    def __init__(self, db):
        self.db = db

    def _check_node_dependencies(self, node):
        return True


class TestProgressQueryMixin:

    def setup_method(self):
        self.db = MagicMock()
        self.svc = ConcreteProgressService(self.db)

    def test_get_project_progress_empty(self):
        mock_q = MagicMock()
        self.db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.options.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = []

        result = self.svc.get_project_progress(project_id=1)
        assert result["total_stages"] == 0
        assert result["progress_pct"] == 0
        assert result["stages"] == []

    def test_get_project_progress_all_completed(self):
        nodes = [_make_node(1, "COMPLETED"), _make_node(2, "COMPLETED")]
        stage = _make_stage(1, "COMPLETED", nodes=nodes)

        mock_q = MagicMock()
        self.db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.options.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = [stage]

        result = self.svc.get_project_progress(project_id=1)
        assert result["progress_pct"] == 100.0
        assert result["completed_stages"] == 1

    def test_get_project_progress_in_progress_stage(self):
        nodes = [_make_node(1, "COMPLETED"), _make_node(2, "PENDING")]
        stage = _make_stage(1, "IN_PROGRESS", nodes=nodes)

        mock_q = MagicMock()
        self.db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.options.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = [stage]

        result = self.svc.get_project_progress(project_id=1)
        assert result["current_stage"] is not None
        assert result["current_stage"]["stage_code"] == "S01"
        assert result["progress_pct"] == 50.0

    def test_get_stage_detail_not_found(self):
        mock_q = MagicMock()
        self.db.query.return_value = mock_q
        mock_q.options.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = None

        result = self.svc.get_stage_detail(stage_instance_id=999)
        assert result is None

    def test_get_stage_detail_returns_nodes(self):
        nodes = [_make_node(1, "COMPLETED", 0), _make_node(2, "PENDING", 1)]
        stage = _make_stage(1, "IN_PROGRESS", nodes=nodes)

        mock_q = MagicMock()
        self.db.query.return_value = mock_q
        mock_q.options.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = stage

        result = self.svc.get_stage_detail(stage_instance_id=1)
        assert result is not None
        assert len(result["nodes"]) == 2

    def test_progress_pct_partial(self):
        nodes = [_make_node(1, "COMPLETED"), _make_node(2, "PENDING"), _make_node(3, "PENDING")]
        stage = _make_stage(1, "IN_PROGRESS", nodes=nodes)

        mock_q = MagicMock()
        self.db.query.return_value = mock_q
        mock_q.filter.return_value = mock_q
        mock_q.options.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = [stage]

        result = self.svc.get_project_progress(project_id=1)
        assert abs(result["progress_pct"] - 33.3) < 0.1
