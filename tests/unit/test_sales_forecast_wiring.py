# -*- coding: utf-8 -*-
"""SALES-06 契约：销售预测接线真算法，僵尸假端点下架。

1. 真服务修模型漂移后能算出真数据：已签合同计入 actual_revenue（现行小写状态），
   漏斗按 est_amount 聚合、只统计非终态阶段。
2. company-overview 端点消费真服务，不再返回硬编码 2026-Q1/52800000。
3. 其余 8 个零消费假端点统一 501 下架。
"""
import uuid
from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi import HTTPException

from app.models.sales import Customer
from app.models.sales.contracts import Contract
from app.models.sales.leads import Opportunity
from tests.conftest import _get_or_create_user


def _unique(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _seed(db):
    user = _get_or_create_user(
        db,
        username=_unique("fcst").lower(),
        password="test123",
        real_name="预测用户",
        department="销售部",
    )
    customer = Customer(
        customer_code=_unique("CUST"),
        customer_name="预测客户",
        customer_level="A",
        status="ACTIVE",
        sales_owner_id=user.id,
        created_by=user.id,
    )
    db.add(customer)
    db.flush()
    contract = Contract(
        contract_code=_unique("CT"),
        contract_name="预测合同",
        contract_type="sales",
        customer_id=customer.id,
        total_amount=Decimal("3000000"),
        status="signed",
        signing_date=date.today(),
    )
    opp = Opportunity(
        opp_code=_unique("OPP"),
        customer_id=customer.id,
        opp_name="漏斗商机",
        stage="PROPOSAL",
        est_amount=Decimal("1000000"),
        owner_id=user.id,
    )
    db.add_all([contract, opp])
    db.commit()
    return user


def test_forecast_service_computes_from_real_data(db_session):
    from app.services.sales_forecast_service import SalesForecastService

    _seed(db_session)
    forecast = SalesForecastService(db_session).get_company_forecast("quarterly")

    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    assert forecast["period"] == f"{now.year}-Q{quarter}", "周期必须是当前真实周期"
    assert forecast["targets"]["actual_revenue"] >= 3000000, "已签合同未计入实际业绩"
    funnel = forecast["funnel_contribution"]
    assert funnel["PROPOSAL"]["total_amount"] >= 1000000, "漏斗未按 est_amount 聚合"
    assert "WON" not in funnel and "LOST" not in funnel, "终态阶段不应进漏斗"


def test_company_overview_endpoint_uses_real_service(db_session):
    from app.api.v1.endpoints.sales.sales_forecast import get_company_forecast

    user = _seed(db_session)
    result = get_company_forecast(period="quarterly", db=db_session, current_user=user)

    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    assert result["period"] == f"{now.year}-Q{quarter}", "端点仍在返回硬编码周期"
    assert result["prediction"]["predicted_revenue"] != 52800000, "端点仍在返回硬编码预测值"


def test_zombie_forecast_endpoints_return_501(db_session):
    from app.api.v1.endpoints.sales import sales_forecast as sf

    user = _seed(db_session)
    zombies = [
        lambda: sf.get_team_forecast(period="quarterly", db=db_session, current_user=user),
        lambda: sf.get_sales_rep_forecast(team_id=None, period="quarterly", db=db_session, current_user=user),
        lambda: sf.get_forecast_accuracy(db=db_session, current_user=user),
        lambda: sf.get_executive_dashboard(db=db_session, current_user=user),
        lambda: sf.get_enhanced_prediction(db=db_session, current_user=user),
        lambda: sf.get_data_quality_score(db=db_session, current_user=user),
        lambda: sf.get_activity_tracking(db=db_session, current_user=user),
        lambda: sf.get_accuracy_comparison(db=db_session, current_user=user),
    ]
    for call in zombies:
        with pytest.raises(HTTPException) as exc:
            call()
        assert exc.value.status_code == 501, "零消费假端点必须 501 下架"
