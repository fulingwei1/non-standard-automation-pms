# -*- coding: utf-8 -*-
"""ADMIN-07 契约：行政管理四件套做实，不再返回硬编码演示数据。

1. 用品：真库为空时列表为空（"A4 复印纸"等演示数据消失）；申领→审批扣库存、驳回不扣。
2. 车辆：申请→批准后车辆置 IN_USE；可用车辆列表排除占用。
3. 资产：真实 CRUD + 统计按真数据聚合。
4. 费用统计按真实记录聚合，不再返回写死的 24.6 万。
"""
import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.admin_office import (
    AdminAsset,
    AdminExpense,
    AdminSupply,
    AdminVehicle,
)
from tests.conftest import _get_or_create_user


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:6].upper()}"


def _user(db):
    return _get_or_create_user(
        db,
        username=_unique("adm").lower(),
        password="test123",
        real_name="行政用户",
        department="行政部",
    )


def test_supplies_list_is_real_data(db_session):
    from app.api.v1.endpoints import admin_compat

    user = _user(db_session)
    result = admin_compat.list_supplies(db=db_session, current_user=user)
    names = [s["name"] for s in (result.get("items") if isinstance(result, dict) else result)]
    assert "A4 复印纸" not in names, "仍在返回硬编码演示数据"

    supply = AdminSupply(name="真实测试用品", category="办公耗材", unit="盒", current_stock=10, min_stock=2)
    db_session.add(supply)
    db_session.commit()

    result = admin_compat.list_supplies(db=db_session, current_user=user)
    items = result.get("items") if isinstance(result, dict) else result
    assert any(s["name"] == "真实测试用品" for s in items)


def test_supply_request_approve_deducts_stock(db_session):
    from app.api.v1.endpoints import admin_compat

    user = _user(db_session)
    approver = _user(db_session)
    supply = AdminSupply(name=_unique("用品"), unit="件", current_stock=10, min_stock=1)
    db_session.add(supply)
    db_session.commit()

    req = admin_compat.create_supply_request(
        payload={"supply_id": supply.id, "quantity": 3, "reason": "部门领用"},
        db=db_session,
        current_user=user,
    )
    request_id = req["id"]

    admin_compat.approve_supply_request(
        request_id=request_id, payload={"comment": "同意"}, db=db_session, current_user=approver
    )

    db_session.expire_all()
    assert db_session.get(AdminSupply, supply.id).current_stock == 7, "审批通过未扣减库存"

    # 库存不足必须拒绝
    with pytest.raises(HTTPException) as exc:
        req2 = admin_compat.create_supply_request(
            payload={"supply_id": supply.id, "quantity": 999, "reason": "超量"},
            db=db_session,
            current_user=user,
        )
        admin_compat.approve_supply_request(
            request_id=req2["id"], payload={}, db=db_session, current_user=approver
        )
    assert exc.value.status_code == 400


def test_supply_request_reject_keeps_stock(db_session):
    from app.api.v1.endpoints import admin_compat

    user = _user(db_session)
    supply = AdminSupply(name=_unique("用品"), unit="件", current_stock=5)
    db_session.add(supply)
    db_session.commit()

    req = admin_compat.create_supply_request(
        payload={"supply_id": supply.id, "quantity": 2},
        db=db_session,
        current_user=user,
    )
    admin_compat.reject_supply_request(
        request_id=req["id"], payload={"comment": "近期缩减"}, db=db_session, current_user=user
    )
    db_session.expire_all()
    assert db_session.get(AdminSupply, supply.id).current_stock == 5


def test_vehicle_request_approve_marks_in_use(db_session):
    from app.api.v1.endpoints import admin_compat

    user = _user(db_session)
    vehicle = AdminVehicle(plate_no=_unique("粤B"), model="别克GL8", status="AVAILABLE")
    db_session.add(vehicle)
    db_session.commit()

    req = admin_compat.create_vehicle_request(
        payload={"vehicle_id": vehicle.id, "use_date": date.today().isoformat(), "purpose": "客户拜访"},
        db=db_session,
        current_user=user,
    )
    admin_compat.approve_vehicle_request(
        request_id=req["id"], payload={}, db=db_session, current_user=user
    )

    db_session.expire_all()
    assert db_session.get(AdminVehicle, vehicle.id).status == "IN_USE"

    available = admin_compat.list_available_vehicles(
        date=None, db=db_session, current_user=user
    )
    items = available.get("items") if isinstance(available, dict) else available
    assert all(v["id"] != vehicle.id for v in items), "已占用车辆不应出现在可用列表"


def test_asset_crud_and_statistics(db_session):
    from app.api.v1.endpoints import admin_compat

    user = _user(db_session)
    created = admin_compat.create_asset(
        payload={"name": "测试服务器", "category": "IT设备", "value": 45000, "custodian": "IT部"},
        db=db_session,
        current_user=user,
    )
    asset_id = created["id"]
    assert created["asset_no"], "资产编号应自动生成"

    admin_compat.update_asset(
        asset_id=asset_id, payload={"status": "REPAIRING"}, db=db_session, current_user=user
    )
    db_session.expire_all()
    assert db_session.get(AdminAsset, asset_id).status == "REPAIRING"

    stats = admin_compat.get_asset_statistics(db=db_session, current_user=user)
    assert stats["total_count"] >= 1
    assert stats["total_value"] >= 45000

    admin_compat.delete_asset(asset_id=asset_id, db=db_session, current_user=user)
    assert db_session.get(AdminAsset, asset_id) is None


def test_expense_statistics_uses_real_records(db_session):
    from app.api.v1.endpoints import admin_compat

    user = _user(db_session)
    db_session.add(
        AdminExpense(
            expense_no=_unique("EXP"),
            category="办公耗材",
            amount=Decimal("1234.56"),
            expense_date=date.today(),
        )
    )
    db_session.commit()

    stats = admin_compat.get_expense_statistics(period="month", db=db_session, current_user=user)
    assert stats["total_amount"] != 246000, "仍在返回写死的费用统计"
    assert any(c["category"] == "办公耗材" for c in stats["by_category"])
