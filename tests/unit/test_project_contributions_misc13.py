from decimal import Decimal
from types import SimpleNamespace

from app.services.project_contribution_service import ProjectContributionService


def test_contribution_report_keeps_each_row_period_when_showing_all_periods():
    service = ProjectContributionService.__new__(ProjectContributionService)
    service.get_project_contributions = lambda project_id, period=None: [
        SimpleNamespace(
            user_id=7,
            user=SimpleNamespace(employee=None, real_name="Alice", username="alice"),
            period="pr30222",
            task_count=3,
            actual_hours=Decimal("12.5"),
            deliverable_count=2,
            issue_resolved=1,
            bonus_amount=Decimal("1000"),
            contribution_score=Decimal("8.5"),
            pm_rating=4,
        )
    ]

    report = ProjectContributionService.generate_contribution_report(service, 42, None)

    assert report["period"] is None
    assert report["contributions"][0]["period"] == "pr30222"
    assert report["top_contributors"][0]["period"] == "pr30222"
