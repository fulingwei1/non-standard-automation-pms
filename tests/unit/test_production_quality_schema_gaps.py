from datetime import datetime

from app.schemas.production.quality import (
    QualityAlertRuleResponse,
    QualityInspectionResponse,
    ReworkOrderResponse,
)


NOW = datetime(2026, 4, 14, 8, 0, 0)


def test_quality_inspection_response_normalizes_none_fields():
    schema = QualityInspectionResponse(
        id=1,
        inspection_no="IQC-001",
        inspection_type="IQC",
        inspection_date=NOW,
        inspector_id=1,
        inspection_qty=100,
        qualified_qty=None,
        defect_qty=None,
        inspection_result=None,
        defect_rate=None,
    )

    assert schema.qualified_qty == 0
    assert schema.defect_qty == 0
    assert schema.inspection_result == "PENDING"
    assert schema.defect_rate == 0.0


def test_quality_alert_rule_response_normalizes_none_fields():
    schema = QualityAlertRuleResponse(
        id=1,
        rule_no="RULE-001",
        rule_name="不良率预警",
        alert_type="DEFECT_RATE",
        threshold_value=None,
        threshold_operator=None,
        time_window_hours=None,
        min_sample_size=None,
        alert_level=None,
        enabled=None,
        trigger_count=None,
    )

    assert schema.threshold_value == 0.0
    assert schema.threshold_operator == "GT"
    assert schema.time_window_hours == 0
    assert schema.min_sample_size == 0
    assert schema.alert_level == "WARNING"
    assert schema.enabled == 0
    assert schema.trigger_count == 0


def test_rework_order_response_normalizes_none_fields():
    schema = ReworkOrderResponse(
        id=1,
        rework_order_no="RW-001",
        original_work_order_id=1,
        rework_qty=10,
        rework_reason="尺寸超差",
        completed_qty=None,
        qualified_qty=None,
        scrap_qty=None,
        actual_hours=None,
        rework_cost=None,
        status=None,
    )

    assert schema.completed_qty == 0
    assert schema.qualified_qty == 0
    assert schema.scrap_qty == 0
    assert schema.actual_hours == 0.0
    assert schema.rework_cost == 0.0
    assert schema.status == "PENDING"
