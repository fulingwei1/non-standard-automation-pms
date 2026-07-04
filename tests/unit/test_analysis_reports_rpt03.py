# -*- coding: utf-8 -*-
"""RPT-03: cost analysis must use configured hourly rates."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.hourly_rate import HourlyRateConfig
from app.models.project import Project
from app.models.timesheet import Timesheet
from app.models.user import User
from app.services.report_data_generation.analysis_reports import AnalysisReportMixin
from app.services.report_framework.generators.analysis import AnalysisReportGenerator


def _seed_cost_analysis_context(db: Session) -> Project:
    suffix = uuid4().hex[:8]
    project = Project(
        project_code=f"PJ-RPT03-{suffix}",
        project_name="RPT03 cost analysis",
        budget_amount=Decimal("2000.00"),
        status="IN_PROGRESS",
        is_active=True,
    )
    user_a = User(
        username=f"rpt03_a_{suffix}",
        password_hash="test",
        real_name="RPT03 Engineer A",
        is_active=True,
    )
    user_b = User(
        username=f"rpt03_b_{suffix}",
        password_hash="test",
        real_name="RPT03 Engineer B",
        is_active=True,
    )
    db.add_all([project, user_a, user_b])
    db.flush()

    db.add_all(
        [
            HourlyRateConfig(
                config_type="USER",
                user_id=user_a.id,
                hourly_rate=Decimal("150.00"),
                effective_date=date(2026, 1, 1),
                expiry_date=date(2026, 1, 15),
                is_active=True,
            ),
            HourlyRateConfig(
                config_type="USER",
                user_id=user_a.id,
                hourly_rate=Decimal("220.00"),
                effective_date=date(2026, 1, 16),
                is_active=True,
            ),
            HourlyRateConfig(
                config_type="USER",
                user_id=user_b.id,
                hourly_rate=Decimal("80.00"),
                effective_date=date(2026, 1, 1),
                is_active=True,
            ),
            Timesheet(
                user_id=user_a.id,
                project_id=project.id,
                work_date=date(2026, 1, 10),
                hours=Decimal("2.00"),
                status="APPROVED",
            ),
            Timesheet(
                user_id=user_a.id,
                project_id=project.id,
                work_date=date(2026, 1, 20),
                hours=Decimal("1.00"),
                status="APPROVED",
            ),
            Timesheet(
                user_id=user_b.id,
                project_id=project.id,
                work_date=date(2026, 1, 20),
                hours=Decimal("3.00"),
                status="APPROVED",
            ),
            Timesheet(
                user_id=user_a.id,
                project_id=project.id,
                work_date=date(2026, 2, 1),
                hours=Decimal("5.00"),
                status="APPROVED",
            ),
        ]
    )
    db.commit()
    return project


def _assert_configured_labor_cost(report: dict):
    assert report["summary"]["total_actual"] == 760.0
    assert report["summary"]["total_variance"] == 1240.0
    assert report["project_breakdown"][0]["actual_cost"] == 760.0
    assert report["project_breakdown"][0]["variance"] == 1240.0
    assert report["project_breakdown"][0]["variance_percent"] == 62.0


def test_report_data_generation_cost_analysis_uses_configured_hourly_rates(
    db_session: Session,
):
    project = _seed_cost_analysis_context(db_session)

    report = AnalysisReportMixin.generate_cost_analysis(
        db_session,
        project_id=project.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    _assert_configured_labor_cost(report)


def test_report_framework_cost_analysis_uses_configured_hourly_rates(db_session: Session):
    project = _seed_cost_analysis_context(db_session)

    report = AnalysisReportGenerator.generate_cost_analysis(
        db_session,
        project_id=project.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    _assert_configured_labor_cost(report)
