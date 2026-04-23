from datetime import datetime
from decimal import Decimal

from app.schemas.production.work_report import (
    WorkReportCompleteRequest,
    WorkReportListResponse,
    WorkReportProgressRequest,
    WorkReportResponse,
    WorkReportStartRequest,
)


def test_work_report_request_normalizes_assigned_to():
    start = WorkReportStartRequest(work_order_id=1, assigned_to=11, report_note="开工")
    progress = WorkReportProgressRequest(
        work_order_id=1,
        assigned_to=12,
        progress_percent=60,
        work_hours=Decimal("2.5"),
    )
    complete = WorkReportCompleteRequest(
        work_order_id=1,
        assigned_to=13,
        completed_qty=20,
        qualified_qty=19,
        defect_qty=1,
        work_hours=Decimal("8.0"),
    )

    assert start.worker_id == 11
    assert progress.worker_id == 12
    assert progress.work_hours == Decimal("2.5")
    assert complete.worker_id == 13
    assert complete.defect_qty == 1

    sentinel = object()
    assert WorkReportStartRequest._normalize_worker_id(sentinel) is sentinel
    assert WorkReportProgressRequest._normalize_worker_id(sentinel) is sentinel
    assert WorkReportCompleteRequest._normalize_worker_id(sentinel) is sentinel


def test_work_report_response_and_list_models():
    item = WorkReportResponse(
        id=1,
        report_no="WR-001",
        work_order_id=100,
        work_order_no="WO-001",
        worker_id=11,
        worker_name="张三",
        report_type="START",
        report_time=datetime.now(),
        progress_percent=60,
        work_hours=2.5,
        completed_qty=20,
        qualified_qty=19,
        defect_qty=1,
        status="APPROVED",
        report_note="正常",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    response = WorkReportListResponse(items=[item], total=1, skip=0, limit=20)

    assert response.total == 1
    assert response.items[0].report_no == "WR-001"
    assert response.items[0].approved_by is None
