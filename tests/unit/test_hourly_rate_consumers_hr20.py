# -*- coding: utf-8 -*-
"""HR-20: labor-cost consumers must use configured hourly rates."""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.api.v1.endpoints.cost_endpoints.labor_cost_detail import labor_cost_by_engineer
from app.models.enums import LeadOutcomeEnum
from app.models.hourly_rate import HourlyRateConfig
from app.models.production.worker import Worker
from app.models.production.work_order import WorkOrder
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User
from app.services.cost.labor_cost_service import LaborCostExpenseService
from app.services.loss_deep_analysis_service import LossDeepAnalysisService
from app.services.template_report.analysis_reports import AnalysisReportMixin


def _make_user(db: Session, suffix: str, rate: Decimal) -> User:
    user = User(
        username=f"hr20_{suffix}_{uuid4().hex[:8]}",
        password_hash="test",
        real_name=f"HR20 {suffix}",
        is_active=True,
    )
    db.add(user)
    db.flush()
    db.add(
        HourlyRateConfig(
            config_type="USER",
            user_id=user.id,
            hourly_rate=rate,
            effective_date=date(2026, 1, 1),
            is_active=True,
        )
    )
    db.flush()
    return user


def _seed_timesheet_cost_context(db: Session):
    suffix = uuid4().hex[:8]
    user_a = _make_user(db, f"a_{suffix}", Decimal("150.00"))
    user_b = _make_user(db, f"b_{suffix}", Decimal("80.00"))
    lost_project = Project(
        project_code=f"PJ-HR20-LOST-{suffix}",
        project_name="HR20 lost presale project",
        budget_amount=Decimal("3000.00"),
        status="IN_PROGRESS",
        is_active=True,
        outcome=LeadOutcomeEnum.LOST.value,
        created_at=datetime(2026, 1, 10, 9, 0, 0),
    )
    won_project = Project(
        project_code=f"PJ-HR20-WON-{suffix}",
        project_name="HR20 won presale project",
        budget_amount=Decimal("2000.00"),
        status="IN_PROGRESS",
        is_active=True,
        outcome=LeadOutcomeEnum.WON.value,
        created_at=datetime(2026, 1, 11, 9, 0, 0),
    )
    db.add_all([lost_project, won_project])
    db.flush()
    db.add_all(
        [
            Timesheet(
                user_id=user_a.id,
                project_id=lost_project.id,
                work_date=date(2026, 1, 10),
                hours=Decimal("2.00"),
                status="APPROVED",
            ),
            Timesheet(
                user_id=user_b.id,
                project_id=lost_project.id,
                work_date=date(2026, 1, 10),
                hours=Decimal("3.00"),
                status="APPROVED",
            ),
            Timesheet(
                user_id=user_a.id,
                project_id=lost_project.id,
                work_date=date(2026, 1, 10),
                hours=Decimal("10.00"),
                status="SUBMITTED",
            ),
            Timesheet(
                user_id=user_a.id,
                project_id=won_project.id,
                work_date=date(2026, 1, 11),
                hours=Decimal("4.00"),
                status="APPROVED",
            ),
        ]
    )
    db.commit()
    return lost_project


def test_template_report_cost_analysis_uses_configured_rates_and_approved_hours(
    db_session: Session,
):
    project = _seed_timesheet_cost_context(db_session)

    report = AnalysisReportMixin._generate_cost_analysis(
        db_session,
        project_id=project.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
        sections_config={},
        metrics_config={},
    )

    assert report["metrics"]["total_actual"] == 540.0
    row = report["sections"]["cost_breakdown"]["data"][0]
    assert row["actual_cost"] == 540.0
    assert row["variance"] == 2460.0




def test_labor_cost_by_engineer_uses_worker_user_configured_rate(db_session: Session):
    suffix = uuid4().hex[:8]
    user = _make_user(db_session, f"worker_{suffix}", Decimal("175.00"))
    project = Project(
        project_code=f"PJ-HR20-WO-{suffix}",
        project_name="HR20 work order project",
        status="IN_PROGRESS",
        is_active=True,
    )
    db_session.add(project)
    db_session.flush()
    worker = Worker(
        worker_no=f"W-HR20-{suffix}",
        worker_name="HR20 Worker",
        user_id=user.id,
        hourly_rate=Decimal("999.00"),
        status="ACTIVE",
        is_active=True,
    )
    db_session.add(worker)
    db_session.flush()
    db_session.add(
        WorkOrder(
            work_order_no=f"WO-HR20-{suffix}",
            task_name="HR20 configured labor cost",
            task_type="ASSEMBLY",
            project_id=project.id,
            assigned_to=worker.id,
            actual_hours=Decimal("2.00"),
            standard_hours=Decimal("5.00"),
            actual_end_time=datetime(2026, 1, 12, 18, 0, 0),
            status="COMPLETED",
        )
    )
    db_session.commit()

    response = labor_cost_by_engineer(db=db_session, current_user=user)

    assert response["summary"]["total_estimated_labor_cost"] == 350.0
    assert response["summary"]["avg_cost_per_hour"] == 175.0
    assert response["engineers"][0]["estimated_labor_cost"] == 350.0


def test_loss_deep_analysis_missing_user_uses_unified_hourly_fallback(
    db_session: Session,
):
    suffix = uuid4().hex[:8]
    project = Project(
        project_code=f"PJ-HR20-LOSS-{suffix}",
        project_name="HR20 loss fallback project",
        status="IN_PROGRESS",
        is_active=True,
    )
    db_session.add(project)
    db_session.flush()
    db_session.add(
        Timesheet(
            user_id=999999,
            project_id=project.id,
            work_date=date(2026, 1, 13),
            hours=Decimal("2.00"),
            status="APPROVED",
        )
    )
    db_session.commit()

    assert LossDeepAnalysisService(db_session)._calculate_project_cost(project.id) == Decimal(
        "200.00"
    )


def test_labor_cost_expense_missing_user_uses_unified_hourly_fallback(
    db_session: Session,
):
    suffix = uuid4().hex[:8]
    project = Project(
        project_code=f"PJ-HR20-EXP-{suffix}",
        project_name="HR20 expense fallback project",
        status="IN_PROGRESS",
        is_active=True,
    )
    db_session.add(project)
    db_session.flush()
    db_session.add(
        Timesheet(
            user_id=999998,
            project_id=project.id,
            work_date=date(2026, 1, 14),
            hours=Decimal("3.00"),
            status="APPROVED",
        )
    )
    db_session.commit()

    assert LaborCostExpenseService(db_session)._calculate_project_cost(project.id) == Decimal(
        "300.00"
    )
