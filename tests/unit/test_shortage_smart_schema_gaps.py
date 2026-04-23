from decimal import Decimal

from app.schemas.shortage_smart import ShortageAlertResponse


def test_shortage_alert_response_normalizes_none_fields():
    alert = ShortageAlertResponse(
        id=1,
        alert_no="ALT-001",
        project_id=1,
        material_id=2,
        material_code="M001",
        material_name="传感器",
        material_spec=None,
        required_qty=Decimal("5"),
        available_qty=None,
        shortage_qty=None,
        in_transit_qty=None,
        days_to_shortage=None,
        estimated_delay_days=None,
        is_critical_path=None,
        alert_level=None,
        status=None,
        estimated_cost_impact=None,
        risk_score=None,
        auto_handled=None,
        required_date=None,
        expected_arrival_date=None,
        impact_projects=None,
        handling_plan_id=None,
        notified_at=None,
        handled_at=None,
        resolved_at=None,
        resolution_type=None,
        resolution_note=None,
    )

    assert alert.available_qty == Decimal("0")
    assert alert.shortage_qty == Decimal("0")
    assert alert.in_transit_qty == Decimal("0")
    assert alert.days_to_shortage == 0
    assert alert.estimated_delay_days == 0
    assert alert.is_critical_path is False
    assert alert.alert_level == "WARNING"
    assert alert.status == "PENDING"
    assert alert.estimated_cost_impact == Decimal("0")
    assert alert.risk_score == Decimal("0")
    assert alert.auto_handled is False
