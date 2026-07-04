# -*- coding: utf-8 -*-
"""
APPR-14: 合同签订创建/更新项目时，交付日期必须带入项目计划完工日期。
"""

from datetime import date
from decimal import Decimal
import uuid


def _code(prefix: str) -> str:
    return f"{prefix}{uuid.uuid4().hex[:8].upper()}"


def _seed_contract_with_quote_delivery(db_session, delivery_date: date):
    from app.models.project import Customer
    from app.models.sales import Contract, Opportunity, Quote, QuoteVersion

    customer = Customer(
        customer_code=_code("CUST"),
        customer_name="APPR14客户",
        industry="非标自动化",
    )
    db_session.add(customer)
    db_session.flush()

    opportunity = Opportunity(
        opp_code=_code("OPP"),
        customer_id=customer.id,
        opp_name="APPR14商机",
        project_type="automation",
        equipment_type="tester",
        stage="QUOTATION",
        probability=80,
        est_amount=Decimal("500000"),
    )
    db_session.add(opportunity)
    db_session.flush()

    quote = Quote(
        quote_code=_code("Q"),
        opportunity_id=opportunity.id,
        customer_id=customer.id,
        status="APPROVED",
    )
    db_session.add(quote)
    db_session.flush()

    quote_version = QuoteVersion(
        quote_id=quote.id,
        version_no="V1",
        status="APPROVED",
        total_price=Decimal("500000"),
        cost_total=Decimal("300000"),
        delivery_date=delivery_date,
    )
    db_session.add(quote_version)
    db_session.flush()
    quote.current_version_id = quote_version.id

    contract = Contract(
        contract_code=_code("CT"),
        contract_name="APPR14合同",
        contract_type="sales",
        customer_id=customer.id,
        opportunity_id=opportunity.id,
        quote_id=quote_version.id,
        total_amount=Decimal("500000"),
        signing_date=date(2026, 7, 1),
        status="signed",
    )
    db_session.add(contract)
    db_session.commit()
    return contract, quote_version


def test_signed_contract_auto_created_project_uses_quote_delivery_date(db_session):
    from app.services.status_handlers.contract_handler import ContractStatusHandler

    contract, quote_version = _seed_contract_with_quote_delivery(
        db_session,
        delivery_date=date(2026, 10, 31),
    )

    project = ContractStatusHandler(db_session).handle_contract_signed(contract.id)

    assert project is not None
    assert project.planned_end_date == quote_version.delivery_date


def test_signed_contract_updates_existing_project_delivery_date(db_session):
    from app.models.project import Project
    from app.services.status_handlers.contract_handler import ContractStatusHandler

    contract, quote_version = _seed_contract_with_quote_delivery(
        db_session,
        delivery_date=date(2026, 11, 30),
    )
    project = Project(
        project_code=_code("PJ"),
        project_name="APPR14已有项目",
        customer_id=contract.customer_id,
        contract_no=contract.contract_code,
        stage="S2",
        status="ST05",
        health="H1",
        planned_end_date=None,
    )
    db_session.add(project)
    db_session.flush()
    contract.project_id = project.id
    db_session.commit()

    updated = ContractStatusHandler(db_session).handle_contract_signed(contract.id)

    assert updated.id == project.id
    assert updated.planned_end_date == quote_version.delivery_date
