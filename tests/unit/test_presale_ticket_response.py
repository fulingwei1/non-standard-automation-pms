from datetime import datetime
from types import SimpleNamespace

from app.api.v1.endpoints.presale.tickets.utils import build_ticket_response


def _ticket_with_progress(progress_records):
    return SimpleNamespace(
        id=42,
        ticket_no="TICKET-260607-001",
        title="方案评审申请",
        ticket_type="SOLUTION_REVIEW",
        urgency="NORMAL",
        description="商机编号：OPP-001",
        customer_id=101,
        customer_name="某大型企业",
        opportunity_id=1,
        project_id=None,
        applicant_id=7,
        applicant_name="张三",
        applicant_dept="销售部",
        apply_time=datetime(2026, 6, 7, 9, 0, 0),
        assignee_id=8,
        assignee_name="李工",
        accept_time=datetime(2026, 6, 7, 10, 0, 0),
        expected_date=None,
        deadline=None,
        status="IN_PROGRESS",
        complete_time=None,
        actual_hours=None,
        satisfaction_score=None,
        feedback=None,
        created_at=datetime(2026, 6, 7, 9, 0, 0),
        updated_at=datetime(2026, 6, 7, 10, 0, 0),
        progress_records=progress_records,
        deliverables=[],
    )


def test_build_ticket_response_exposes_latest_progress_percent():
    ticket = _ticket_with_progress(
        [
            SimpleNamespace(id=1, progress_percent=20, progress_note="已接单", created_at=datetime(2026, 6, 7, 10, 0, 0)),
            SimpleNamespace(id=2, progress_percent=65, progress_note="方案初稿完成", created_at=datetime(2026, 6, 7, 11, 0, 0)),
        ]
    )

    response = build_ticket_response(ticket)

    assert response.progress_percent == 65
    assert response.progress_note == "方案初稿完成"


def test_build_ticket_response_exposes_ticket_deliverables():
    ticket = _ticket_with_progress([])
    ticket.deliverables = [
        SimpleNamespace(
            id=3,
            ticket_id=42,
            name="初版技术方案",
            file_type="SOLUTION",
            file_path="/files/solution-v1.pdf",
            status="SUBMITTED",
            created_at=datetime(2026, 6, 7, 11, 0, 0),
            updated_at=datetime(2026, 6, 7, 11, 5, 0),
        )
    ]

    response = build_ticket_response(ticket)

    assert response.deliverables == [
        {
            "id": 3,
            "ticket_id": 42,
            "deliverable_name": "初版技术方案",
            "deliverable_type": "SOLUTION",
            "file_path": "/files/solution-v1.pdf",
            "file_url": "/files/solution-v1.pdf",
            "status": "SUBMITTED",
            "created_at": datetime(2026, 6, 7, 11, 0, 0),
            "updated_at": datetime(2026, 6, 7, 11, 5, 0),
        }
    ]
