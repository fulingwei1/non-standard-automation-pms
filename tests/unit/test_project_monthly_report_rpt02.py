# -*- coding: utf-8 -*-
"""RPT-02: project monthly report must use real project costs."""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.project import FinancialProjectCost, Project, ProjectCost
from app.services.report_data_generation.project_reports import ProjectReportMixin


def test_project_monthly_report_cost_summary_uses_period_cost_records(db_session: Session):
    project = Project(
        project_code="PJ-RPT02-001",
        project_name="RPT02项目月报成本测试",
        budget_amount=Decimal("1000.00"),
        progress_pct=Decimal("50"),
        stage="S3",
        status="ST05",
        health="H1",
        is_active=True,
    )
    db_session.add(project)
    db_session.flush()

    db_session.add_all(
        [
            ProjectCost(
                project_id=project.id,
                cost_type="MATERIAL",
                cost_category="材料费",
                amount=Decimal("200.00"),
                cost_date=date(2026, 1, 10),
                cost_basis="ACTUAL",
            ),
            FinancialProjectCost(
                project_id=project.id,
                project_code=project.project_code,
                project_name=project.project_name,
                cost_type="LABOR",
                cost_category="人工费",
                amount=Decimal("150.00"),
                cost_date=date(2026, 1, 15),
                cost_month="2026-01",
                uploaded_by=1,
            ),
            ProjectCost(
                project_id=project.id,
                cost_type="MATERIAL",
                cost_category="材料费",
                amount=Decimal("900.00"),
                cost_date=date(2026, 2, 1),
                cost_basis="ACTUAL",
            ),
        ]
    )
    db_session.commit()

    report = ProjectReportMixin.generate_project_monthly_report(
        db_session,
        project_id=project.id,
        start_date=date(2026, 1, 1),
        end_date=date(2026, 1, 31),
    )

    assert report["cost"]["actual_cost"] == 350.0
    assert report["cost"]["cost_variance"] == 650.0
    assert report["cost"]["cost_variance_percent"] == 65.0
