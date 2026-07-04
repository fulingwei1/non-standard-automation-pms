# -*- coding: utf-8 -*-
from decimal import Decimal
from types import SimpleNamespace
import uuid

import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.purchase.orders_refactored import create_purchase_order
from app.models.alert import AlertRule
from app.models.enums import AlertLevelEnum, AlertRuleTypeEnum
from app.models.project import Project
from app.models.purchase import PurchaseOrder
from app.models.vendor import Vendor
from app.services.budget_alert_service import BudgetAlertService


def _suffix() -> str:
    return uuid.uuid4().hex[:8]


def _project(db_session, *, budget="1000.00", actual="0.00", progress="100"):
    suffix = _suffix()
    project = Project(
        project_code=f"PJ-BUDGET-{suffix}",
        project_name="PROJ-14 预算拦截项目",
        stage="S1",
        status="ST01",
        health="H1",
        progress_pct=Decimal(progress),
        budget_amount=Decimal(budget),
        actual_cost=Decimal(actual),
    )
    db_session.add(project)
    db_session.flush()
    return project


def _vendor(db_session):
    suffix = _suffix()
    vendor = Vendor(
        supplier_code=f"SUP-BUDGET-{suffix}",
        supplier_name="PROJ-14 预算拦截供应商",
        vendor_type="MATERIAL",
        status="ACTIVE",
    )
    db_session.add(vendor)
    db_session.flush()
    return vendor


def _budget_rule(db_session, *, yellow="80", orange="90", red="100"):
    rule = AlertRule(
        rule_code="BUDGET_EXECUTION",
        rule_name="预算执行预警",
        rule_type=AlertRuleTypeEnum.COST_OVERRUN.value,
        target_type="PROJECT",
        condition_type="THRESHOLD",
        condition_operator="GT",
        threshold_value=yellow,
        threshold_min=orange,
        threshold_max=red,
        alert_level=AlertLevelEnum.WARNING.value,
        enforcement_mode="REQUIRE_APPROVAL",
        is_enabled=True,
        is_system=True,
    )
    db_session.add(rule)
    db_session.flush()
    return rule


def _purchase_payload(vendor_id: int, project_id: int, *, amount="150.00", override=False):
    payload = {
        "supplier_id": vendor_id,
        "project_id": project_id,
        "order_type": "NORMAL",
        "order_title": "PROJ-14 预算软拦截采购单",
        "items": [
            {
                "material_code": f"MAT-BUDGET-{_suffix()}",
                "material_name": "预算检查物料",
                "unit": "件",
                "quantity": 1,
                "unit_price": amount,
                "tax_rate": 13,
            }
        ],
    }
    if override:
        payload["budget_override"] = True
    return payload


def test_budget_status_uses_thresholds_from_alert_rule(db_session):
    _budget_rule(db_session, yellow="70", orange="85", red="95")
    project = _project(db_session, actual="750.00")

    status = BudgetAlertService(db_session).get_budget_status(project.id)

    assert status is not None
    assert status.execution_rate == Decimal("75.0")
    assert status.alert_level == "YELLOW"


def test_budget_soft_intercept_requires_override_at_red_threshold(db_session):
    _budget_rule(db_session)
    project = _project(db_session, actual="900.00")

    guard = BudgetAlertService(db_session).check_budget_soft_intercept(
        project.id, Decimal("150.00")
    )

    assert guard is not None
    assert guard["projected_execution_rate"] == Decimal("105.00")
    assert guard["alert_level"] == "RED"
    assert guard["requires_approval"] is True
    assert guard["allowed"] is False


def test_budget_soft_intercept_allows_explicit_override(db_session):
    project = _project(db_session, actual="900.00")

    guard = BudgetAlertService(db_session).check_budget_soft_intercept(
        project.id, Decimal("150.00"), override_approved=True
    )

    assert guard is not None
    assert guard["requires_approval"] is True
    assert guard["override_approved"] is True
    assert guard["allowed"] is True


def test_purchase_order_creation_soft_blocks_budget_red_without_override(db_session):
    project = _project(db_session, actual="900.00")
    vendor = _vendor(db_session)

    with pytest.raises(HTTPException) as exc_info:
        create_purchase_order(
            _purchase_payload(vendor.id, project.id),
            db=db_session,
            current_user=SimpleNamespace(id=1),
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["budget_guard"]["requires_approval"] is True
    assert db_session.query(PurchaseOrder).count() == 0


def test_purchase_order_creation_allows_budget_override_and_returns_guard(db_session):
    project = _project(db_session, actual="900.00")
    vendor = _vendor(db_session)

    response = create_purchase_order(
        _purchase_payload(vendor.id, project.id, override=True),
        db=db_session,
        current_user=SimpleNamespace(id=1),
    )

    assert response.data["project_id"] == project.id
    assert response.data["budget_guard"]["requires_approval"] is True
    assert response.data["budget_guard"]["allowed"] is True
    assert db_session.query(PurchaseOrder).count() == 1
