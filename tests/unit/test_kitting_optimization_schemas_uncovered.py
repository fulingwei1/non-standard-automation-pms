from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.schemas.kitting_optimization import (
    AlternativeListResponse,
    AlternativeMaterialResponse,
    BottleneckMaterial,
    CommonStockMaterial,
    CriticalMaterialForecast,
    ExpediteRecordResponse,
    ExpediteRequest,
    ExpediteResult,
    ExpediteStats,
    ExpediteTarget,
    ImprovementTarget,
    KittingImprovementSuggestions,
    KittingRateSyncRequest,
    KittingRateSyncResult,
    MaterialDelayForecastResult,
    PrePurchaseMaterial,
    PriorityAdjustment,
    PriorityAutoAdjustResult,
    ProjectKittingRateResult,
    SafetyStockAlert,
    SafetyStockAlertResponse,
    SupplierDeliveryAnalysis,
)


def test_expedite_request_validation_and_defaults():
    target = ExpediteTarget(material_id=1)
    request = ExpediteRequest(targets=[target])

    assert request.targets[0].urgency_level == "NORMAL"
    assert request.notify_methods == ["SYSTEM"]
    assert request.auto_detect_high_risk is False

    with pytest.raises(ValidationError):
        ExpediteRequest(targets=[])


def test_expedite_related_response_models():
    record = ExpediteRecordResponse(
        id=1,
        material_id=10,
        material_code="MAT-001",
        material_name="物料A",
        urgency_level="HIGH",
        notify_method="EMAIL",
        notify_status="SENT",
        status="OPEN",
        required_date=date.today(),
        created_at=datetime.now(),
    )
    result = ExpediteResult(total_created=1, records=[record])
    stats = ExpediteStats(
        total_expedited=3,
        resolved_count=1,
        on_time_count=1,
        on_time_rate=50.0,
    )

    assert result.auto_detected == 0
    assert result.notify_sent == 0
    assert stats.by_urgency == {}
    assert stats.by_supplier == []


def test_alternative_material_and_list_response():
    alternative = AlternativeMaterialResponse(
        id=1,
        alternative_material_id=2,
        material_code="ALT-001",
        material_name="替代料",
        match_score=95.5,
    )
    response = AlternativeListResponse(
        original_material_id=100,
        original_material_code="MAT-001",
        original_material_name="原物料",
        alternatives=[alternative],
        total=1,
    )

    assert response.alternatives[0].current_stock == 0
    assert response.alternatives[0].supplier_count == 0
    assert response.total == 1


def test_safety_stock_models():
    alert = SafetyStockAlert(
        material_id=1,
        material_code="MAT-001",
        material_name="物料A",
        current_stock=5,
        safety_stock=10,
        gap=5,
        gap_pct=50,
        avg_daily_consumption=2,
        suggested_reorder_qty=20,
        reorder_point=8,
        alert_level="CRITICAL",
    )
    response = SafetyStockAlertResponse(
        alerts=[alert],
        total=1,
        critical_count=1,
        warning_count=0,
    )

    assert alert.is_key_material is False
    assert alert.is_high_frequency_shortage is False
    assert response.summary == {}


def test_improvement_suggestion_models():
    bottleneck = BottleneckMaterial(
        material_id=1,
        material_code="MAT-001",
        material_name="瓶颈料",
        shortage_count=3,
        total_shortage_qty=12.5,
        affected_projects=2,
        suggestion="增加备货",
    )
    supplier = SupplierDeliveryAnalysis(
        supplier_id=1,
        supplier_name="供应商A",
        total_orders=10,
        on_time_count=8,
        delayed_count=2,
        on_time_rate=80,
        avg_delay_days=1.5,
        max_delay_days=5,
        risk_level="LOW",
        suggestion="持续观察",
    )
    pre_purchase = PrePurchaseMaterial(
        material_id=2,
        material_code="MAT-002",
        material_name="提前采购料",
        lead_time_days=15,
        avg_monthly_usage=20,
        current_stock=5,
        reason="交期长",
        suggested_qty=30,
    )
    common_stock = CommonStockMaterial(
        material_id=3,
        material_code="MAT-003",
        material_name="通用料",
        usage_frequency=12,
        project_coverage=6,
        current_stock=30,
        suggested_safety_stock=50,
        reason="高频使用",
    )
    target = ImprovementTarget(
        current_rate=82,
        target_rate=95,
        gap=13,
        key_actions=["提前采购", "优化供应商"],
        estimated_timeline="30天",
    )
    suggestions = KittingImprovementSuggestions(
        bottleneck_materials=[bottleneck],
        supplier_analysis=[supplier],
        pre_purchase_materials=[pre_purchase],
        common_stock_materials=[common_stock],
        improvement_target=target,
        generated_at=datetime.now(),
    )

    assert suggestions.improvement_target.target_rate == 95
    assert suggestions.pre_purchase_materials[0].suggested_qty == 30


def test_sync_and_delay_forecast_models():
    with pytest.raises(ValidationError):
        KittingRateSyncRequest(project_ids=[])

    req = KittingRateSyncRequest(project_ids=[1, 2])
    project_result = ProjectKittingRateResult(
        project_id=1,
        old_rate=80,
        new_rate=90,
        changed=True,
    )
    sync_result = KittingRateSyncResult(
        total_synced=1,
        significant_changes=[project_result],
        significant_count=1,
        threshold=5,
    )
    material = CriticalMaterialForecast(
        material_id=1,
        material_code="MAT-001",
        material_name="关键料",
        shortage_qty=5,
        delay_days=7,
        lead_time_days=10,
        suggestions=["催料"],
    )
    forecast = MaterialDelayForecastResult(
        project_id=1,
        project_code="PJ-001",
        project_name="项目A",
        max_delay_days=7,
        critical_material_count=1,
        critical_materials=[material],
        overall_suggestions=["优先处理关键料"],
        risk_level="HIGH",
    )

    assert req.project_ids == [1, 2]
    assert sync_result.errors == []
    assert sync_result.error_count == 0
    assert forecast.critical_materials[0].is_key_item is False


def test_priority_adjustment_models():
    adjustment = PriorityAdjustment(
        project_id=1,
        project_code="PJ-001",
        project_name="项目A",
        kitting_rate=88,
        old_priority="B",
        new_priority="A",
        reason="齐套率提升",
    )
    result = PriorityAutoAdjustResult(
        total_adjusted=1,
        protected_count=0,
        adjustments=[adjustment],
        timestamp="2026-04-13T22:00:00",
    )

    assert result.adjustments[0].new_priority == "A"
    assert result.total_adjusted == 1
