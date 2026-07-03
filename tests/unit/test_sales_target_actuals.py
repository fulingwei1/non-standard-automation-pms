# -*- coding: utf-8 -*-
"""SALES-08 契约：销售目标 actual_value 必须自动回填，达成率口径统一。

目标列表接口不得再返回恒 0 的 actual_value——个人目标按
SalesTeamService.calculate_target_performance 口径实时计算：
LEAD_COUNT/OPPORTUNITY_COUNT 按 owner 计数，CONTRACT_AMOUNT 按合同负责人
金额求和，COLLECTION_AMOUNT 按发票实收；达成率 = actual/target*100。
"""
import uuid
from datetime import datetime
from decimal import Decimal

from app.common.pagination import PaginationParams
from app.models.sales import Customer, SalesTarget
from app.models.sales.contracts import Contract
from tests.conftest import _get_or_create_user


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def test_target_list_backfills_actual_value(db_session):
    from app.api.v1.endpoints.sales.targets import get_sales_targets

    user = _get_or_create_user(
        db_session,
        username=_unique("tgt").lower(),
        password="test123",
        real_name="目标回填用户",
        department="销售部",
        employee_role="SALES",
    )
    customer = Customer(
        customer_code=_unique("CUST"),
        customer_name="目标客户",
        customer_level="A",
        status="ACTIVE",
        sales_owner_id=user.id,
        created_by=user.id,
    )
    db_session.add(customer)
    db_session.flush()

    now = datetime.now()
    month_value = now.strftime("%Y-%m")
    target = SalesTarget(
        target_scope="PERSONAL",
        user_id=user.id,
        target_type="CONTRACT_AMOUNT",
        target_period="MONTHLY",
        period_value=month_value,
        target_value=Decimal("2000000"),
        status="ACTIVE",
        created_by=user.id,
    )
    contract = Contract(
        contract_code=_unique("CT"),
        contract_name="目标回填合同",
        contract_type="sales",
        customer_id=customer.id,
        sales_owner_id=user.id,
        total_amount=Decimal("1000000"),
        status="signed",
    )
    db_session.add_all([target, contract])
    db_session.commit()

    pagination = PaginationParams(page=1, page_size=20, offset=0, limit=20)
    result = get_sales_targets(
        db=db_session,
        pagination=pagination,
        target_scope=None,
        target_type=None,
        target_period=None,
        period_value=month_value,
        user_id=user.id,
        department_id=None,
        status=None,
        current_user=user,
    )

    rows = [r for r in result.items if r["user_id"] == user.id]
    assert rows, "个人目标未出现在列表中"
    row = rows[0]
    assert row["actual_value"] == 1000000.0, "actual_value 未按合同真实数据回填（仍恒 0）"
    assert abs(row["completion_rate"] - 50.0) < 0.01, "达成率口径应为 actual/target*100"
