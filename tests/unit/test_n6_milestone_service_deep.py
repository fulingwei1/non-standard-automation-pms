# -*- coding: utf-8 -*-
"""
N6组 - 深度覆盖测试：里程碑服务
Coverage target: app/services/milestone_service.py

测试分支：
1. get_by_project — 正常、空、排序
2. complete_milestone — 指定日期、默认今天
3. complete_milestone — 已有 actual_date 时使用原日期
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch, call

from app.models.project import ProjectMilestone
from app.services.milestone_service import MilestoneService
from app.schemas.project import MilestoneUpdate


class TestMilestoneServiceInit:

    def test_init_sets_model_and_resource_name(self):
        db = MagicMock()
        svc = MilestoneService(db)
        assert svc.model == ProjectMilestone
        assert svc.resource_name == "里程碑"
        assert svc.db is db


class TestGetByProject:

    def setup_method(self):
        self.db = MagicMock()
        self.svc = MilestoneService(self.db)

    def test_returns_milestones_in_order(self):
        m1 = MagicMock(id=1, planned_date=date(2026, 1, 1))
        m2 = MagicMock(id=2, planned_date=date(2026, 2, 1))
        q = self.db.query.return_value
        q.filter.return_value.order_by.return_value.all.return_value = [m1, m2]

        result = self.svc.get_by_project(10)

        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2
        self.db.query.assert_called_with(ProjectMilestone)

    def test_returns_empty_list_for_nonexistent_project(self):
        q = self.db.query.return_value
        q.filter.return_value.order_by.return_value.all.return_value = []
        result = self.svc.get_by_project(9999)
        assert result == []

    def test_query_filters_by_project_id(self):
        q = self.db.query.return_value
        q.filter.return_value.order_by.return_value.all.return_value = []
        self.svc.get_by_project(42)
        self.db.query.assert_called_with(ProjectMilestone)

    def test_returns_single_milestone(self):
        m = MagicMock(id=5, planned_date=date(2026, 3, 15))
        q = self.db.query.return_value
        q.filter.return_value.order_by.return_value.all.return_value = [m]
        result = self.svc.get_by_project(1)
        assert len(result) == 1
        assert result[0].id == 5

    def test_handles_many_milestones(self):
        milestones = [MagicMock(id=i) for i in range(1, 51)]
        q = self.db.query.return_value
        q.filter.return_value.order_by.return_value.all.return_value = milestones
        result = self.svc.get_by_project(1)
        assert len(result) == 50


class TestCompleteMilestone:

    def setup_method(self):
        self.db = MagicMock()
        self.svc = MilestoneService(self.db)

    def _setup_milestone(self, actual_date=None, has_db_query=True):
        mock_milestone = MagicMock(
            id=1,
            status="IN_PROGRESS",
            actual_date=actual_date,
        )
        if has_db_query:
            q = self.db.query.return_value
            q.filter.return_value.first.return_value = mock_milestone
        return mock_milestone

    def test_complete_with_explicit_date(self):
        milestone = self._setup_milestone()
        explicit_date = date(2026, 3, 1)

        with patch.object(self.svc, 'get', return_value=milestone), \
             patch.object(self.svc, 'update') as mock_update:
            self.svc.complete_milestone(1, actual_date=explicit_date)

        mock_update.assert_called_once()
        call_args = mock_update.call_args
        update_data = call_args[0][1]  # second positional arg
        assert update_data.status == "COMPLETED"
        assert update_data.actual_date == explicit_date

    def test_complete_with_no_date_uses_today(self):
        milestone = self._setup_milestone(actual_date=None)

        with patch.object(self.svc, 'get', return_value=milestone), \
             patch.object(self.svc, 'update') as mock_update:
            self.svc.complete_milestone(1, actual_date=None)

        call_args = mock_update.call_args
        update_data = call_args[0][1]
        assert update_data.actual_date == date.today()

    def test_complete_preserves_existing_actual_date_when_no_explicit(self):
        """如果 milestone 已有 actual_date 且未传 actual_date，使用 milestone.actual_date"""
        existing = date(2026, 2, 10)
        milestone = self._setup_milestone(actual_date=existing)

        with patch.object(self.svc, 'get', return_value=milestone), \
             patch.object(self.svc, 'update') as mock_update:
            self.svc.complete_milestone(1)

        call_args = mock_update.call_args
        update_data = call_args[0][1]
        # 优先 milestone.actual_date
        assert update_data.actual_date == existing

    def test_complete_returns_milestone_model(self):
        milestone = self._setup_milestone()

        with patch.object(self.svc, 'get', return_value=milestone), \
             patch.object(self.svc, 'update'), \
             patch.object(self.db.query.return_value.filter.return_value, 'first', return_value=milestone):
            result = self.svc.complete_milestone(1)

        assert result is not None

    def test_complete_calls_update_with_completed_status(self):
        milestone = self._setup_milestone()

        with patch.object(self.svc, 'get', return_value=milestone), \
             patch.object(self.svc, 'update') as mock_update:
            self.svc.complete_milestone(1)

        mock_update.assert_called_once()
        args = mock_update.call_args[0]
        assert args[0] == 1  # milestone_id
        assert args[1].status == "COMPLETED"

    def test_complete_calls_get_to_retrieve_milestone(self):
        milestone = self._setup_milestone()

        with patch.object(self.svc, 'get', return_value=milestone) as mock_get, \
             patch.object(self.svc, 'update'):
            self.svc.complete_milestone(7)

        mock_get.assert_called_once_with(7)

    def test_complete_triggers_db_refetch(self):
        """complete_milestone 最后用 db.query().filter().first() 重新获取模型"""
        milestone = self._setup_milestone()
        fresh_milestone = MagicMock(id=1)
        q = self.db.query.return_value
        q.filter.return_value.first.return_value = fresh_milestone

        with patch.object(self.svc, 'get', return_value=milestone), \
             patch.object(self.svc, 'update'):
            result = self.svc.complete_milestone(1)

        self.db.query.assert_called_with(ProjectMilestone)

    def test_complete_no_date_no_existing_uses_today(self):
        """milestone.actual_date = None, no explicit date → date.today()"""
        milestone = MagicMock(id=1, status="NOT_STARTED", actual_date=None)
        q = self.db.query.return_value
        q.filter.return_value.first.return_value = milestone

        with patch.object(self.svc, 'get', return_value=milestone), \
             patch.object(self.svc, 'update') as mock_update:
            self.svc.complete_milestone(1)

        update_data = mock_update.call_args[0][1]
        assert update_data.actual_date == date.today()
