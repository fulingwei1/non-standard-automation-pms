# -*- coding: utf-8 -*-
"""第二十五批 - project_timeline_service 单元测试"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, date

pytest.importorskip("app.services.project_timeline_service")

from app.services.project_timeline_service import (
    collect_status_change_events,
    collect_milestone_events,
    collect_task_events,
    collect_cost_events,
    collect_document_events,
    add_project_created_event,
)


# ── collect_status_change_events ──────────────────────────────────────────────

class TestCollectStatusChangeEvents:
    def test_returns_empty_when_no_logs(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = collect_status_change_events(db, project_id=1)
        assert result == []

    def test_creates_event_for_each_log(self):
        db = MagicMock()
        log = MagicMock()
        log.change_type = "STAGE_CHANGE"
        log.changed_at = datetime(2025, 3, 1)
        log.old_stage = "S1"
        log.new_stage = "S2"
        log.old_status = "ST01"
        log.new_status = "ST02"
        log.changer = MagicMock(username="admin")
        log.id = 10
        db.query.return_value.filter.return_value.all.return_value = [log]
        result = collect_status_change_events(db, project_id=1)
        assert len(result) == 1
        assert result[0].event_type == "STAGE_CHANGE"

    def test_event_title_contains_change_type(self):
        db = MagicMock()
        log = MagicMock()
        log.change_type = "STATUS_CHANGE"
        log.changed_at = datetime(2025, 4, 15)
        log.old_stage = None
        log.new_stage = None
        log.old_status = "ST01"
        log.new_status = "ST03"
        log.changer = None
        log.id = 5
        db.query.return_value.filter.return_value.all.return_value = [log]
        result = collect_status_change_events(db, project_id=1)
        assert "STATUS_CHANGE" in result[0].title

    def test_no_changer_yields_none_user_name(self):
        db = MagicMock()
        log = MagicMock()
        log.change_type = "STATUS_CHANGE"
        log.changed_at = datetime(2025, 5, 1)
        log.old_stage = "S2"
        log.new_stage = "S3"
        log.old_status = None
        log.new_status = None
        log.changer = None
        log.id = 3
        db.query.return_value.filter.return_value.all.return_value = [log]
        result = collect_status_change_events(db, project_id=1)
        assert result[0].user_name is None


# ── collect_milestone_events ──────────────────────────────────────────────────

class TestCollectMilestoneEvents:
    def test_returns_empty_when_no_milestones(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = collect_milestone_events(db, project_id=1)
        assert result == []

    def test_creates_created_event_for_milestone(self):
        db = MagicMock()
        ms = MagicMock()
        ms.milestone_name = "里程碑1"
        ms.created_at = datetime(2025, 2, 1)
        ms.planned_date = date(2025, 4, 1)
        ms.status = "IN_PROGRESS"
        ms.actual_date = None
        ms.id = 1
        db.query.return_value.filter.return_value.all.return_value = [ms]
        result = collect_milestone_events(db, project_id=1)
        types = [e.event_type for e in result]
        assert "MILESTONE_CREATED" in types

    def test_creates_completed_event_when_done(self):
        db = MagicMock()
        ms = MagicMock()
        ms.milestone_name = "里程碑2"
        ms.created_at = datetime(2025, 1, 1)
        ms.planned_date = date(2025, 3, 31)
        ms.status = "COMPLETED"
        ms.actual_date = datetime(2025, 3, 25)
        ms.id = 2
        db.query.return_value.filter.return_value.all.return_value = [ms]
        result = collect_milestone_events(db, project_id=1)
        types = [e.event_type for e in result]
        assert "MILESTONE_COMPLETED" in types
        assert "MILESTONE_CREATED" in types
        assert len(result) == 2

    def test_no_completed_event_without_actual_date(self):
        db = MagicMock()
        ms = MagicMock()
        ms.milestone_name = "里程碑3"
        ms.created_at = datetime(2025, 1, 1)
        ms.planned_date = date(2025, 6, 1)
        ms.status = "COMPLETED"
        ms.actual_date = None
        ms.id = 3
        db.query.return_value.filter.return_value.all.return_value = [ms]
        result = collect_milestone_events(db, project_id=1)
        types = [e.event_type for e in result]
        assert "MILESTONE_COMPLETED" not in types


# ── collect_task_events ───────────────────────────────────────────────────────

class TestCollectTaskEvents:
    def test_returns_empty_when_no_tasks(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = collect_task_events(db, project_id=1)
        assert result == []

    def test_creates_created_event_for_each_task(self):
        db = MagicMock()
        task = MagicMock()
        task.task_name = "任务A"
        task.created_at = datetime(2025, 2, 10)
        task.owner_name = "张三"
        task.status = "TODO"
        task.actual_end = None
        task.progress_pct = 0
        task.id = 1
        db.query.return_value.filter.return_value.all.return_value = [task]
        result = collect_task_events(db, project_id=1)
        types = [e.event_type for e in result]
        assert "TASK_CREATED" in types

    def test_creates_completed_event_when_done(self):
        db = MagicMock()
        task = MagicMock()
        task.task_name = "任务B"
        task.created_at = datetime(2025, 1, 5)
        task.owner_name = "李四"
        task.status = "COMPLETED"
        task.actual_end = datetime(2025, 4, 20)
        task.progress_pct = 100
        task.id = 2
        db.query.return_value.filter.return_value.all.return_value = [task]
        result = collect_task_events(db, project_id=1)
        types = [e.event_type for e in result]
        assert "TASK_COMPLETED" in types

    def test_no_completed_event_without_actual_end(self):
        db = MagicMock()
        task = MagicMock()
        task.task_name = "任务C"
        task.created_at = datetime(2025, 3, 1)
        task.owner_name = None
        task.status = "COMPLETED"
        task.actual_end = None
        task.progress_pct = 100
        task.id = 3
        db.query.return_value.filter.return_value.all.return_value = [task]
        result = collect_task_events(db, project_id=1)
        types = [e.event_type for e in result]
        assert "TASK_COMPLETED" not in types


# ── collect_cost_events ───────────────────────────────────────────────────────

class TestCollectCostEvents:
    def test_returns_empty_when_no_costs(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = collect_cost_events(db, project_id=1)
        assert result == []

    def test_creates_event_for_each_cost(self):
        db = MagicMock()
        cost = MagicMock()
        cost.id = 1
        cost.cost_name = "差旅费"
        cost.cost_type = "TRAVEL"
        cost.cost_amount = 5000
        cost.created_at = datetime(2025, 3, 15)
        db.query.return_value.filter.return_value.all.return_value = [cost]
        result = collect_cost_events(db, project_id=1)
        assert len(result) == 1
        assert result[0].event_type == "COST_RECORDED"

    def test_skips_cost_without_created_at(self):
        db = MagicMock()
        cost = MagicMock()
        cost.id = 2
        cost.cost_name = "费用"
        cost.cost_type = "OTHER"
        cost.cost_amount = 1000
        cost.created_at = None
        db.query.return_value.filter.return_value.all.return_value = [cost]
        result = collect_cost_events(db, project_id=1)
        assert len(result) == 0


# ── collect_document_events ───────────────────────────────────────────────────

class TestCollectDocumentEvents:
    def test_returns_empty_when_no_documents(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = collect_document_events(db, project_id=1)
        assert result == []

    def test_creates_event_for_each_document(self):
        db = MagicMock()
        doc = MagicMock()
        doc.id = 1
        doc.doc_name = "设计文档"
        doc.doc_type = "DESIGN"
        doc.doc_category = "TECH"
        doc.created_at = datetime(2025, 2, 20)
        db.query.return_value.filter.return_value.all.return_value = [doc]
        result = collect_document_events(db, project_id=1)
        assert len(result) == 1
        assert result[0].event_type == "DOCUMENT_UPLOADED"

    def test_title_contains_doc_name(self):
        db = MagicMock()
        doc = MagicMock()
        doc.id = 2
        doc.doc_name = "测试报告"
        doc.doc_type = "TEST"
        doc.doc_category = "QA"
        doc.created_at = datetime(2025, 5, 10)
        db.query.return_value.filter.return_value.all.return_value = [doc]
        result = collect_document_events(db, project_id=1)
        assert "测试报告" in result[0].title


# ── add_project_created_event ─────────────────────────────────────────────────

class TestAddProjectCreatedEvent:
    def test_returns_project_created_event(self):
        project = MagicMock()
        project.id = 1
        project.project_code = "PRJ001"
        project.created_at = datetime(2025, 1, 1)
        event = add_project_created_event(project)
        assert event.event_type == "PROJECT_CREATED"

    def test_event_title_is_project_created(self):
        project = MagicMock()
        project.id = 2
        project.project_code = "PRJ002"
        project.created_at = datetime(2025, 2, 1)
        event = add_project_created_event(project)
        assert event.title == "项目创建"

    def test_event_description_contains_code(self):
        project = MagicMock()
        project.id = 3
        project.project_code = "PRJ-SPECIAL-001"
        project.created_at = datetime(2025, 3, 1)
        event = add_project_created_event(project)
        assert "PRJ-SPECIAL-001" in event.description

    def test_event_related_type_is_project(self):
        project = MagicMock()
        project.id = 4
        project.project_code = "PRJ003"
        project.created_at = datetime(2025, 4, 1)
        event = add_project_created_event(project)
        assert event.related_type == "project"
