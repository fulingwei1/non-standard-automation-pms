# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.models.project import Customer, Project, ProjectCost
from app.models.purchase import PurchaseOrder
from app.models.user import User
from app.models.vendor import Vendor


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_cost_collection_collect_endpoint_uses_project_costs(
    client: TestClient, admin_token: str, db_session
):
    if not admin_token:
        pytest.skip("Admin token not available")

    suffix = uuid.uuid4().hex[:8]
    admin = db_session.query(User).filter(User.username == "admin").first()

    customer = Customer(
        customer_code=f"CUST-COLLECT-{suffix}",
        customer_name="归集接口测试客户",
        status="ACTIVE",
        created_by=admin.id,
    )
    vendor = Vendor(
        supplier_code=f"SUP-COLLECT-{suffix}",
        supplier_name="归集接口测试供应商",
        vendor_type="MATERIAL",
        status="ACTIVE",
        created_by=admin.id,
    )
    db_session.add_all([customer, vendor])
    db_session.flush()

    project = Project(
        project_code=f"PJ-COLLECT-{suffix}",
        project_name="归集接口测试项目",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        actual_cost=Decimal("0"),
        created_by=admin.id,
    )
    db_session.add(project)
    db_session.flush()

    purchase_order = PurchaseOrder(
        order_no=f"PO-COLLECT-{suffix}",
        supplier_id=vendor.id,
        project_id=project.id,
        order_title="接口触发采购归集",
        total_amount=Decimal("1234.00"),
        tax_amount=Decimal("160.42"),
        order_date=date(2026, 6, 5),
        status="RECEIVED",
        created_by=admin.id,
    )
    db_session.add(purchase_order)
    db_session.commit()
    project_id = project.id
    order_id = purchase_order.id

    with patch(
        "app.services.cost.cost_collection_service.CostAlertService.check_budget_execution",
        return_value=None,
    ):
        response = client.post(
            f"{settings.API_V1_PREFIX}/cost-collection/collect",
            params={"project_id": project_id},
            headers=_headers(admin_token),
        )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["total_collected"] >= 1

    cost = (
        db_session.query(ProjectCost)
        .filter(
            ProjectCost.project_id == project_id,
            ProjectCost.source_type == "PURCHASE_ORDER",
            ProjectCost.source_id == order_id,
        )
        .first()
    )
    assert cost is not None
    assert cost.source_module == "PURCHASE"
    assert cost.amount == Decimal("1234.00")
