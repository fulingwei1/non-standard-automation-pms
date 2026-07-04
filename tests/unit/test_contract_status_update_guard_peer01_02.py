# -*- coding: utf-8 -*-
"""
PEER-01/02: 合同通用 PUT 不得直接修改状态，避免绕过审批/状态机。
"""

from decimal import Decimal
import uuid

import pytest
from fastapi import HTTPException


def _code(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:8].upper()}"


def _seed_contract(db_session, *, status: str):
    from app.models.project import Customer
    from app.models.sales import Contract
    from app.models.user import User

    user = User(
        username=_code("contract_guard").lower(),
        password_hash="not-used",
        real_name="合同状态守卫测试",
        is_active=True,
        is_superuser=True,
    )
    customer = Customer(
        customer_code=_code("CUST"),
        customer_name="合同状态守卫客户",
    )
    db_session.add_all([user, customer])
    db_session.flush()

    contract = Contract(
        contract_code=_code("CT"),
        contract_name="合同状态守卫合同",
        contract_type="sales",
        customer_id=customer.id,
        total_amount=Decimal("100000"),
        status=status,
        sales_owner_id=user.id,
    )
    db_session.add(contract)
    db_session.commit()
    return user, contract


@pytest.mark.parametrize("original_status", ["CANCELLED", "pending_approval"])
def test_generic_contract_update_rejects_status_changes(db_session, original_status):
    from app.api.v1.endpoints.sales.contracts.basic import update_contract
    from app.models.sales import Contract
    from app.schemas.sales import ContractUpdate

    user, contract = _seed_contract(db_session, status=original_status)

    with pytest.raises(HTTPException) as exc:
        update_contract(
            db=db_session,
            contract_id=contract.id,
            contract_in=ContractUpdate(status="SIGNED"),
            current_user=user,
        )

    assert exc.value.status_code == 400
    db_session.expire_all()
    assert db_session.get(Contract, contract.id).status == original_status


def test_generic_contract_update_still_allows_non_status_fields(db_session):
    from app.api.v1.endpoints.sales.contracts.basic import update_contract
    from app.schemas.sales import ContractUpdate

    user, contract = _seed_contract(db_session, status="draft")

    response = update_contract(
        db=db_session,
        contract_id=contract.id,
        contract_in=ContractUpdate(contract_name="更新后的合同名称"),
        current_user=user,
    )

    assert response.contract_name == "更新后的合同名称"
    assert response.status == "draft"
