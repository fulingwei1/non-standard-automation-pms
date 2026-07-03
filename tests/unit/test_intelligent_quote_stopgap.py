# -*- coding: utf-8 -*-
"""SALES-13 契约：智能报价假实现收口。

1. historical-prices 做实：按真实 WON 商机 × 已签合同返回成交参考价；
   无数据返回空列表，不得再吐"宁德时代 320 万"等演示常量。
2. 竞品价格、最优价、自动折扣、赢单率预测（单个+批量）纯常量且零真实消费，一律 501 下架。
"""
import uuid
from datetime import date
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.sales import Customer
from app.models.sales.contracts import Contract
from app.models.sales.leads import Opportunity
from tests.conftest import _get_or_create_user


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _seed_won_deal(db):
    user = _get_or_create_user(
        db,
        username=_unique("iq").lower(),
        password="test123",
        real_name="智能报价用户",
        department="销售部",
    )
    customer = Customer(
        customer_code=_unique("CUST"),
        customer_name="真实成交客户",
        customer_level="A",
        status="ACTIVE",
        sales_owner_id=user.id,
        created_by=user.id,
    )
    db.add(customer)
    db.flush()
    opp = Opportunity(
        opp_code=_unique("OPP"),
        customer_id=customer.id,
        opp_name="真实FCT测试线项目",
        equipment_type="FCT",
        stage="WON",
        owner_id=user.id,
    )
    db.add(opp)
    db.flush()
    contract = Contract(
        contract_code=_unique("CT"),
        contract_name="真实FCT合同",
        contract_type="sales",
        opportunity_id=opp.id,
        customer_id=customer.id,
        total_amount=Decimal("2600000"),
        status="signed",
        signing_date=date.today(),
    )
    db.add(contract)
    db.commit()
    return user


def test_historical_prices_uses_real_won_deals(db_session):
    from app.api.v1.endpoints.sales.intelligent_quote import get_historical_prices

    user = _seed_won_deal(db_session)
    result = get_historical_prices(
        product_category="FCT",
        estimated_amount=None,
        industry=None,
        limit=5,
        db=db_session,
        current_user=user,
    )

    items = result["items"] if isinstance(result, dict) else result
    assert items, "有真实成交却未返回参考价"
    names = [i["project_name"] for i in items]
    assert "真实FCT测试线项目" in names
    assert all("宁德时代" not in str(i) for i in items), "仍在返回演示常量"
    row = next(i for i in items if i["project_name"] == "真实FCT测试线项目")
    assert row["final_price"] == 2600000.0


def test_historical_prices_empty_when_no_match(db_session):
    from app.api.v1.endpoints.sales.intelligent_quote import get_historical_prices

    user = _seed_won_deal(db_session)
    result = get_historical_prices(
        product_category="不存在的品类XYZ",
        estimated_amount=None,
        industry=None,
        limit=5,
        db=db_session,
        current_user=user,
    )
    items = result["items"] if isinstance(result, dict) else result
    assert items == [], "查无匹配必须空列表，不得用演示数据兜底"


def test_zombie_intelligent_quote_endpoints_return_501(db_session):
    from app.api.v1.endpoints.sales import intelligent_quote as iq

    user = _seed_won_deal(db_session)
    zombies = [
        lambda: iq.add_competitor_price(data={}, db=db_session, current_user=user),
        lambda: iq.get_competitor_price_comparison(
            product_category="FCT", our_price=None, db=db_session, current_user=user
        ),
        lambda: iq.get_optimal_price_suggestion(quote_id=1, db=db_session, current_user=user),
        lambda: iq.calculate_auto_discount(quote_id=1, db=db_session, current_user=user),
        lambda: iq.predict_win_rate(opportunity_id=1, db=db_session, current_user=user),
        lambda: iq.batch_predict_win_rate(opportunity_ids=[1], db=db_session, current_user=user),
    ]
    for call in zombies:
        with pytest.raises(HTTPException) as exc:
            call()
        assert exc.value.status_code == 501
