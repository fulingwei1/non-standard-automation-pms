# -*- coding: utf-8 -*-
import os
import sys
from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

redis_mock = MagicMock()
sys.modules.setdefault("redis", redis_mock)
sys.modules.setdefault("redis.exceptions", MagicMock())

os.environ.setdefault("SQLITE_DB_PATH", ":memory:")
os.environ.setdefault("REDIS_URL", "")
os.environ.setdefault("ENABLE_SCHEDULER", "false")

from app.api.v1.endpoints.production.work_reports import _resolve_report_worker
from app.schemas.production import (
    ProductionPlanCalendarResponse,
    WorkOrderAssignRequest,
    WorkReportCompleteRequest,
    WorkReportProgressRequest,
    WorkReportStartRequest,
)
from app.services.production.plan_service import ProductionPlanService
from tests.unit.test_api_p6_coverage import make_client, make_mock_db


class TestWorkOrderAssignCompat:
    def test_accepts_worker_id_as_assigned_to_alias(self):
        req = WorkOrderAssignRequest(worker_id=12, workstation_id=3)

        assert req.assigned_to == 12
        assert req.worker_id == 12
        assert req.workstation_id == 3

    def test_keeps_assigned_to_when_provided(self):
        req = WorkOrderAssignRequest(assigned_to=21)

        assert req.assigned_to == 21
        assert req.worker_id == 21


@pytest.mark.parametrize(
    "schema_cls,payload",
    [
        (WorkReportStartRequest, {"work_order_id": 1, "report_note": "start"}),
        (
            WorkReportProgressRequest,
            {"work_order_id": 1, "progress_percent": 50, "report_note": "progress"},
        ),
        (
            WorkReportCompleteRequest,
            {"work_order_id": 1, "completed_qty": 10, "qualified_qty": 9},
        ),
    ],
)
def test_work_report_requests_allow_missing_worker_id(schema_cls, payload):
    req = schema_cls(**payload)

    assert req.worker_id is None


@pytest.mark.parametrize(
    "schema_cls,extra_payload",
    [
        (WorkReportStartRequest, {}),
        (WorkReportProgressRequest, {"progress_percent": 30}),
        (WorkReportCompleteRequest, {"completed_qty": 10, "qualified_qty": 10}),
    ],
)
def test_work_report_requests_accept_assigned_to_alias(schema_cls, extra_payload):
    req = schema_cls(work_order_id=1, assigned_to=8, **extra_payload)

    assert req.worker_id == 8


class TestResolveReportWorker:
    def test_prefers_current_user_bound_worker(self):
        db = MagicMock()
        current_user = SimpleNamespace(id=100)
        work_order = SimpleNamespace(assigned_to=9)
        current_worker = SimpleNamespace(id=5, worker_name="张三")

        db.query.return_value.filter.return_value.first.return_value = current_worker

        worker = _resolve_report_worker(db, current_user, work_order, request_worker_id=12)

        assert worker is current_worker

    def test_falls_back_to_assigned_worker_when_user_not_bound(self):
        db = MagicMock()
        current_user = SimpleNamespace(id=100)
        work_order = SimpleNamespace(assigned_to=9)
        assigned_worker = SimpleNamespace(id=9, worker_name="李四")

        db.query.return_value.filter.return_value.first.return_value = None

        with patch(
            "app.api.v1.endpoints.production.work_reports.get_or_404",
            return_value=assigned_worker,
        ) as mock_get:
            worker = _resolve_report_worker(db, current_user, work_order, request_worker_id=None)

        assert worker is assigned_worker
        mock_get.assert_called_once()

    def test_uses_request_worker_id_when_order_has_no_assignee(self):
        db = MagicMock()
        current_user = SimpleNamespace(id=100)
        work_order = SimpleNamespace(assigned_to=None)
        request_worker = SimpleNamespace(id=12, worker_name="王五")

        db.query.return_value.filter.return_value.first.return_value = None

        with patch(
            "app.api.v1.endpoints.production.work_reports.get_or_404",
            return_value=request_worker,
        ) as mock_get:
            worker = _resolve_report_worker(db, current_user, work_order, request_worker_id=12)

        assert worker is request_worker
        mock_get.assert_called_once()


class TestProductionPlanCalendar:
    def test_build_calendar_response_contains_plan_and_work_order(self):
        db = MagicMock()
        service = ProductionPlanService(db)

        plan = SimpleNamespace(
            id=1,
            plan_no="PP000001",
            plan_name="三月计划",
            plan_type="MASTER",
            status="PUBLISHED",
            project_id=None,
            workshop_id=None,
            plan_start_date=date(2026, 3, 10),
            plan_end_date=date(2026, 3, 11),
        )
        order = SimpleNamespace(
            id=2,
            work_order_no="WO000001",
            task_name="装配任务",
            status="ASSIGNED",
            project_id=None,
            workshop_id=None,
            workstation_id=3,
            assigned_to=7,
            progress=20,
            plan_start_date=date(2026, 3, 11),
            plan_end_date=date(2026, 3, 12),
        )

        result = service._build_calendar_response(
            plans=[plan],
            work_orders=[order],
            start_date=date(2026, 3, 10),
            end_date=date(2026, 3, 12),
        )

        assert isinstance(result, ProductionPlanCalendarResponse)
        assert len(result.calendar) == 3
        assert result.calendar[0].plans[0].plan_name == "三月计划"
        assert result.calendar[1].work_orders[0].order_no == "WO000001"
        assert result.calendar[2].work_orders[0].task_name == "装配任务"

    def test_calendar_route_hits_static_endpoint_not_plan_id_route(self):
        from app.api.v1.endpoints.production.plans import router

        client = make_client(router, "/api/v1/production", mock_db=make_mock_db())

        with patch(
            "app.api.v1.endpoints.production.plans.ProductionPlanService.get_calendar",
            return_value={"calendar": []},
        ) as mock_get_calendar:
            response = client.get(
                "/api/v1/production/production-plans/calendar",
                params={"start_date": "2026-03-01", "end_date": "2026-03-31"},
            )

        assert response.status_code == 200
        mock_get_calendar.assert_called_once()
