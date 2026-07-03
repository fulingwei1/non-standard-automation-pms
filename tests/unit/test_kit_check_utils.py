# -*- coding: utf-8 -*-
"""齐套检查工具函数测试"""

from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.api.v1.endpoints.kit_check.utils import calculate_work_order_kit_rate
from app.api.v1.endpoints.kit_check.work_orders import get_work_order_kit_detail


@pytest.mark.unit
def test_work_order_kit_rate_does_not_count_in_transit_as_fulfilled():
    db = MagicMock()

    work_order = SimpleNamespace(machine_id=1, plan_qty=1)
    machine = SimpleNamespace(bom_id=7)
    bom_header = SimpleNamespace(id=7)
    material = SimpleNamespace(
        id=5,
        material_code="MAT-005",
        material_name="在途未到物料",
        current_stock=0,
    )
    bom_item = SimpleNamespace(
        material=material,
        material_id=5,
        quantity=10,
    )

    call_count = [0]

    def query_side_effect(model):
        query = MagicMock()
        query.filter.return_value = query
        if call_count[0] == 0:
            query.first.return_value = machine
        elif call_count[0] == 1:
            query.first.return_value = bom_header
        else:
            query.all.return_value = [bom_item]
        call_count[0] += 1
        return query

    db.query.side_effect = query_side_effect

    with patch(
        "app.api.v1.endpoints.kit_check.utils.get_purchase_in_transit_qty",
        return_value=Decimal("10"),
    ):
        result = calculate_work_order_kit_rate(db, work_order)

    assert result["fulfilled_items"] == 0
    assert result["shortage_items"] == 1
    assert result["in_transit_items"] == 1
    assert result["kit_rate"] == 0.0
    assert result["is_kit_complete"] is False
    assert result["shortage_details"][0]["shortage_qty"] == 10.0


@pytest.mark.unit
def test_work_order_kit_detail_does_not_count_in_transit_as_available():
    db = MagicMock()

    work_order = SimpleNamespace(
        id=1,
        work_order_no="WO-001",
        task_name="装配",
        project_id=1,
        machine_id=1,
        workshop_id=None,
        plan_start_date=None,
        plan_qty=1,
        status="PENDING",
    )
    machine = SimpleNamespace(id=1, bom_id=7, machine_name="机台1")
    project = SimpleNamespace(project_name="项目1")
    bom_header = SimpleNamespace(id=7)
    material = SimpleNamespace(
        id=5,
        material_code="MAT-005",
        material_name="在途未到物料",
        specification="SPEC",
        unit="件",
        current_stock=0,
    )
    bom_item = SimpleNamespace(
        material=material,
        material_id=5,
        quantity=10,
        is_critical=False,
    )

    call_count = [0]

    def query_side_effect(model):
        query = MagicMock()
        query.filter.return_value = query
        if call_count[0] == 0:
            query.first.return_value = work_order
        elif call_count[0] == 1:
            query.first.return_value = machine
        elif call_count[0] == 2:
            query.first.return_value = bom_header
        elif call_count[0] == 3:
            query.all.return_value = [bom_item]
        elif call_count[0] == 4:
            query.first.return_value = project
        else:
            query.first.return_value = machine
        call_count[0] += 1
        return query

    db.query.side_effect = query_side_effect

    with patch(
        "app.api.v1.endpoints.kit_check.work_orders.calculate_work_order_kit_rate",
        return_value={
            "total_items": 1,
            "fulfilled_items": 0,
            "shortage_items": 1,
            "in_transit_items": 1,
            "kit_rate": 0.0,
            "kit_status": "shortage",
            "is_kit_complete": False,
            "shortage_details": [],
        },
    ), patch(
        "app.services.purchase.in_transit.get_purchase_in_transit_qty",
        return_value=Decimal("10"),
    ):
        response = get_work_order_kit_detail(db=db, work_order_id=1, current_user=SimpleNamespace(id=1))

    detail = response.data["bom_items"][0]
    assert detail["available_qty"] == 0.0
    assert detail["in_transit_qty"] == 10.0
    assert detail["total_available"] == 0.0
    assert detail["shortage_qty"] == 10.0
    assert detail["status"] == "shortage"
