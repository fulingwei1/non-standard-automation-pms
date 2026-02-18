# -*- coding: utf-8 -*-
"""OthersDashboardAdapter / StaffMatchingDashboardAdapter / KitRateDashboardAdapter 单元测试"""

import pytest
import sys
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime

from app.services.dashboard_adapters.others import (
    OthersDashboardAdapter,
    StaffMatchingDashboardAdapter,
    KitRateDashboardAdapter,
)
from app.schemas.dashboard import DashboardStatCard, DashboardWidget, DetailedDashboardResponse


# ==================== OthersDashboardAdapter ====================


class TestOthersDashboardAdapter:

    def _make(self):
        db = MagicMock()
        return OthersDashboardAdapter(db), db

    # -- get_quick_stats --

    def test_get_quick_stats_normal(self):
        adapter, db = self._make()
        # chain: db.query(Model).count() / .filter().count()
        counter = MagicMock()
        counter.count.return_value = 5
        filter_mock = MagicMock()
        filter_mock.count.return_value = 2
        counter.filter.return_value = filter_mock

        db.query.return_value = counter
        result = adapter.get_quick_stats()
        assert result["project_count"] == 5
        assert result["alert_count"] == 2

    def test_get_quick_stats_exception(self):
        adapter, db = self._make()
        db.query.side_effect = Exception("boom")
        result = adapter.get_quick_stats()
        assert result == {"project_count": 0, "user_count": 0, "alert_count": 0}

    # -- get_recent_activities --

    def test_get_recent_activities_default(self):
        adapter, db = self._make()
        chain = MagicMock()
        db.query.return_value = chain
        chain.order_by.return_value = chain
        chain.limit.return_value = chain
        chain.filter.return_value = chain
        chain.all.return_value = ["a1", "a2"]

        mock_approval = MagicMock()
        with patch.dict("sys.modules", {"app.models.approval": mock_approval}):
            mock_approval.ApprovalRecord = MagicMock()
            result = adapter.get_recent_activities()
        assert result == ["a1", "a2"]

    def test_get_recent_activities_with_user_id(self):
        adapter, db = self._make()
        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.limit.return_value = chain
        chain.all.return_value = []
        mock_approval = MagicMock()
        with patch.dict("sys.modules", {"app.models.approval": mock_approval}):
            mock_approval.ApprovalRecord = MagicMock()
            result = adapter.get_recent_activities(limit=5, user_id=42)
        assert result == []

    def test_get_recent_activities_import_fail(self):
        """When model import fails, returns empty list gracefully"""
        adapter, db = self._make()
        # Default behavior: import fails -> returns []
        assert adapter.get_recent_activities() == []

    # -- get_system_health --

    def test_get_system_health_all_healthy(self):
        adapter, db = self._make()
        db.execute.return_value = None
        with patch("app.services.dashboard_adapters.others.OthersDashboardAdapter.get_system_health") as _:
            # just call real method
            pass
        # Call directly
        result = adapter.get_system_health()
        assert result["database"] == "healthy"

    def test_get_system_health_db_fail(self):
        adapter, db = self._make()
        db.execute.side_effect = Exception("db down")
        result = adapter.get_system_health()
        assert result["database"] == "unhealthy"
        assert result["status"] == "degraded"

    # -- get_user_tasks --

    def test_get_user_tasks_basic(self):
        adapter, db = self._make()
        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.limit.return_value = chain
        chain.all.return_value = ["t1"]
        mock_mod = MagicMock()
        with patch.dict("sys.modules", {"app.models.task_center": mock_mod}):
            mock_mod.TaskItem = MagicMock()
            result = adapter.get_user_tasks(user_id=1)
        assert result == ["t1"]

    def test_get_user_tasks_with_status(self):
        adapter, db = self._make()
        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.limit.return_value = chain
        chain.all.return_value = []
        mock_mod = MagicMock()
        with patch.dict("sys.modules", {"app.models.task_center": mock_mod}):
            mock_mod.TaskItem = MagicMock()
            result = adapter.get_user_tasks(user_id=1, status="DONE")
        assert result == []

    def test_get_user_tasks_with_approvals(self):
        adapter, db = self._make()
        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.limit.return_value = chain
        chain.all.return_value = ["t1"]
        mock_task = MagicMock()
        mock_approval = MagicMock()
        with patch.dict("sys.modules", {
            "app.models.task_center": mock_task,
            "app.models.approval": mock_approval,
        }):
            mock_task.TaskItem = MagicMock()
            mock_approval.ApprovalTask = MagicMock()
            result = adapter.get_user_tasks(user_id=1, include_approvals=True)
        assert "t1" in result

    def test_get_user_tasks_import_fail(self):
        """When model import fails, returns empty list"""
        adapter, db = self._make()
        result = adapter.get_user_tasks(user_id=1)
        assert result == []

    # -- get_notifications --

    def test_get_notifications_basic(self):
        adapter, db = self._make()
        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.limit.return_value = chain
        chain.all.return_value = ["n1"]
        assert adapter.get_notifications(user_id=1) == ["n1"]

    def test_get_notifications_unread_only(self):
        adapter, db = self._make()
        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain
        chain.order_by.return_value = chain
        chain.limit.return_value = chain
        chain.all.return_value = []
        assert adapter.get_notifications(user_id=1, unread_only=True) == []

    def test_get_notifications_exception(self):
        adapter, db = self._make()
        db.query.side_effect = Exception("err")
        assert adapter.get_notifications(user_id=1) == []


# ==================== StaffMatchingDashboardAdapter ====================


class TestStaffMatchingDashboardAdapter:

    def _make(self):
        db = MagicMock()
        user = MagicMock()
        adapter = StaffMatchingDashboardAdapter(db, user)
        return adapter, db

    def test_properties(self):
        adapter, _ = self._make()
        assert adapter.module_id == "staff_matching"
        assert adapter.module_name == "人员匹配"
        assert "hr" in adapter.supported_roles

    @patch("app.services.dashboard_adapters.others.MesProjectStaffingNeed")
    @patch("app.services.dashboard_adapters.others.HrAIMatchingLog")
    def test_get_stats(self, MockLog, MockNeed):
        adapter, db = self._make()
        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain
        chain.scalar.return_value = 3

        stats = adapter.get_stats()
        assert isinstance(stats, list)
        assert len(stats) == 6
        assert all(isinstance(s, DashboardStatCard) for s in stats)
        keys = [s.key for s in stats]
        assert "open_needs" in keys
        assert "success_rate" in keys

    @patch("app.services.dashboard_adapters.others.MesProjectStaffingNeed")
    @patch("app.services.dashboard_adapters.others.HrAIMatchingLog")
    def test_get_stats_zero_matched(self, MockLog, MockNeed):
        """success_rate should be 0 when total_matched=0"""
        adapter, db = self._make()
        chain = MagicMock()
        db.query.return_value = chain
        chain.filter.return_value = chain
        chain.scalar.return_value = 0

        stats = adapter.get_stats()
        rate_card = [s for s in stats if s.title == "匹配成功率"][0]
        assert rate_card.value == 0.0

    @patch("app.services.dashboard_adapters.others.MesProjectStaffingNeed")
    @patch("app.services.dashboard_adapters.others.HrAIMatchingLog")
    def test_get_widgets(self, MockLog, MockNeed):
        adapter, db = self._make()
        chain = MagicMock()
        db.query.return_value = chain
        chain.order_by.return_value = chain
        chain.limit.return_value = chain
        chain.filter.return_value = chain
        chain.group_by.return_value = chain
        chain.all.return_value = []

        widgets = adapter.get_widgets()
        assert isinstance(widgets, list)
        assert len(widgets) == 2
        assert all(isinstance(w, DashboardWidget) for w in widgets)

    @patch("app.services.dashboard_adapters.others.MesProjectStaffingNeed")
    @patch("app.services.dashboard_adapters.others.HrAIMatchingLog")
    def test_get_widgets_with_logs(self, MockLog, MockNeed):
        adapter, db = self._make()
        log = MagicMock()
        log.id = 1
        log.request_id = "req1"
        log.project_id = 10
        log.total_score = 85.0
        log.is_accepted = True
        log.matching_time = datetime.now()
        log.project.name = "Proj"
        log.candidate.name = "John"

        chain = MagicMock()
        db.query.return_value = chain
        chain.order_by.return_value = chain
        chain.limit.return_value = chain
        chain.filter.return_value = chain
        chain.group_by.return_value = chain
        chain.all.side_effect = [[log], [("HIGH", 2), ("LOW", 5)]]

        widgets = adapter.get_widgets()
        assert len(widgets) == 2
        assert widgets[0].data["items"][0]["employee_name"] == "John"

    @patch("app.services.dashboard_adapters.others.MesProjectStaffingNeed")
    @patch("app.services.dashboard_adapters.others.HrAIMatchingLog")
    def test_get_detailed_data(self, MockLog, MockNeed):
        adapter, db = self._make()
        chain = MagicMock()
        chain.scalar.return_value = 1
        chain.filter.return_value = chain
        chain.count.return_value = 2
        db.query.return_value = chain

        result = adapter.get_detailed_data()
        assert isinstance(result, DetailedDashboardResponse)
        assert result.module_id == "staff_matching"
        assert "by_status" in result.data.get("details", result.data)


# ==================== KitRateDashboardAdapter ====================


class TestKitRateDashboardAdapter:

    def _make(self):
        db = MagicMock()
        user = MagicMock()
        adapter = KitRateDashboardAdapter(db, user)
        return adapter, db

    def test_properties(self):
        adapter, _ = self._make()
        assert adapter.module_id == "kit_rate"
        assert adapter.module_name == "齐套率"
        assert "procurement" in adapter.supported_roles

    @patch("app.services.kit_rate.KitRateService")
    def test_get_stats(self, MockKitRateService):
        adapter, db = self._make()
        svc = MagicMock()
        MockKitRateService.return_value = svc
        svc.get_dashboard.return_value = {
            "data": {
                "overall_stats": {
                    "total_projects": 10,
                    "avg_kit_rate": 85.5,
                    "can_start_count": 7,
                    "shortage_count": 3,
                },
                "project_list": [],
            }
        }
        stats = adapter.get_stats()
        assert len(stats) == 4
        assert stats[0].value == 10

    @patch("app.services.kit_rate.KitRateService")
    def test_get_widgets(self, MockKitRateService):
        adapter, db = self._make()
        svc = MagicMock()
        MockKitRateService.return_value = svc
        svc.get_dashboard.return_value = {
            "data": {"project_list": [{"id": 1}, {"id": 2}]}
        }
        widgets = adapter.get_widgets()
        assert len(widgets) == 1
        assert widgets[0].widget_type == "table"

    @patch("app.services.kit_rate.KitRateService")
    def test_get_detailed_data(self, MockKitRateService):
        adapter, db = self._make()
        svc = MagicMock()
        MockKitRateService.return_value = svc
        svc.get_dashboard.return_value = {
            "data": {
                "overall_stats": {"total_projects": 5},
                "project_list": [{"id": 1}],
            }
        }
        result = adapter.get_detailed_data()
        assert isinstance(result, DetailedDashboardResponse)
        assert result.module_id == "kit_rate"
