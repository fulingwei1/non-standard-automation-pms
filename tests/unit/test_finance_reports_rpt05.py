# -*- coding: utf-8 -*-
"""RPT-05 / SALES-17: financial reports must keep tax basis explicit."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.api.v1.endpoints.finance_reports import (
    get_cash_flow,
    get_cost_analysis,
    get_monthly_trend,
    get_project_profitability,
)
from app.api.v1.endpoints.sales.contracts.basic import (
    ContractFromQuoteRequest,
    create_contract_from_quote,
)
from app.api.v1.endpoints.sales.quotes import create_quote
from app.models.project import Customer, FinancialProjectCost, Project, ProjectCost
from app.models.sales import Contract, Invoice, Opportunity, Quote, QuoteVersion
from app.models.user import User


def _money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _create_user(db: Session) -> User:
    suffix = uuid4().hex[:8]
    user = User(
        username=f"rpt05-{suffix}",
        password_hash="test",
        real_name="RPT05 Tester",
        is_active=True,
        is_superuser=True,
    )
    db.add(user)
    db.flush()
    return user


def _create_customer_and_opportunity(db: Session, user: User) -> tuple[Customer, Opportunity]:
    suffix = uuid4().hex[:8]
    customer = Customer(
        customer_code=f"CUST-RPT05-{suffix}",
        customer_name=f"RPT05 客户 {suffix}",
        status="ACTIVE",
        created_by=user.id,
        sales_owner_id=user.id,
    )
    db.add(customer)
    db.flush()

    opportunity = Opportunity(
        opp_code=f"OPP-RPT05-{suffix[:6]}",
        customer_id=customer.id,
        opp_name=f"RPT05 商机 {suffix}",
        stage="QUOTATION",
        probability=80,
        owner_id=user.id,
        updated_by=user.id,
    )
    db.add(opportunity)
    db.flush()
    return customer, opportunity


def test_quote_creation_persists_explicit_tax_breakdown(db_session: Session):
    user = _create_user(db_session)
    customer, opportunity = _create_customer_and_opportunity(db_session, user)

    response = create_quote(
        quote_data={
            "quote_code": f"QT-RPT05-{uuid4().hex[:6]}",
            "opportunity_id": opportunity.id,
            "customer_id": customer.id,
            "version": {
                "version_no": "V1",
                "amount_without_tax": 1000,
                "tax_rate": 13,
                "tax_amount": 130,
                "amount_with_tax": 1130,
                "total_price": 1130,
                "cost_total": 700,
                "items": [],
            },
        },
        db=db_session,
        current_user=user,
    )

    version = db_session.get(QuoteVersion, response["current_version_id"])
    assert version is not None
    assert _money(version.amount_without_tax) == Decimal("1000.00")
    assert _money(version.tax_rate) == Decimal("13.00")
    assert _money(version.tax_amount) == Decimal("130.00")
    assert _money(version.amount_with_tax) == Decimal("1130.00")
    assert _money(version.total_price) == Decimal("1130.00")


def test_contract_from_quote_inherits_quote_tax_breakdown(db_session: Session):
    user = _create_user(db_session)
    customer, opportunity = _create_customer_and_opportunity(db_session, user)
    quote = Quote(
        quote_code=f"QT-RPT05-{uuid4().hex[:6]}",
        opportunity_id=opportunity.id,
        customer_id=customer.id,
        status="APPROVED",
        owner_id=user.id,
    )
    db_session.add(quote)
    db_session.flush()
    version = QuoteVersion(
        quote_id=quote.id,
        version_no="V1",
        amount_without_tax=Decimal("1000.00"),
        tax_rate=Decimal("13.00"),
        tax_amount=Decimal("130.00"),
        amount_with_tax=Decimal("1130.00"),
        total_price=Decimal("1130.00"),
        cost_total=Decimal("700.00"),
        gross_margin=Decimal("38.05"),
        created_by=user.id,
    )
    db_session.add(version)
    db_session.flush()
    quote.current_version_id = version.id
    db_session.commit()

    contract = create_contract_from_quote(
        db=db_session,
        request=ContractFromQuoteRequest(quote_id=quote.id),
        skip_g3_validation=True,
        current_user=user,
    )

    stored = db_session.get(Contract, contract.id)
    assert stored is not None
    assert _money(stored.amount_without_tax) == Decimal("1000.00")
    assert _money(stored.tax_rate) == Decimal("13.00")
    assert _money(stored.tax_amount) == Decimal("130.00")
    assert _money(stored.amount_with_tax) == Decimal("1130.00")
    assert _money(stored.total_amount) == Decimal("1130.00")


def test_finance_reports_return_net_tax_and_gross_amounts(db_session: Session):
    user = _create_user(db_session)
    customer, opportunity = _create_customer_and_opportunity(db_session, user)
    project = Project(
        project_code=f"PJ-RPT05-{uuid4().hex[:6]}",
        project_name="RPT05 finance tax basis",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        status="IN_PROGRESS",
        is_active=True,
        contract_amount=Decimal("0"),
    )
    db_session.add(project)
    db_session.flush()

    contract = Contract(
        contract_code=f"CT-RPT05-{uuid4().hex[:6]}",
        contract_name="RPT05 tax contract",
        contract_type="sales",
        opportunity_id=opportunity.id,
        customer_id=customer.id,
        project_id=project.id,
        amount_without_tax=Decimal("1000.00"),
        tax_rate=Decimal("13.00"),
        tax_amount=Decimal("130.00"),
        amount_with_tax=Decimal("1130.00"),
        total_amount=Decimal("1130.00"),
        received_amount=Decimal("0"),
        signing_date=date(2026, 1, 8),
        status="signed",
        sales_owner_id=user.id,
    )
    db_session.add(contract)
    db_session.flush()

    db_session.add_all(
        [
            Invoice(
                invoice_code=f"INV-RPT05-{uuid4().hex[:6]}",
                contract_id=contract.id,
                project_id=project.id,
                amount=Decimal("500.00"),
                tax_rate=Decimal("13.00"),
                tax_amount=Decimal("65.00"),
                total_amount=Decimal("565.00"),
                paid_amount=Decimal("565.00"),
                paid_date=date(2026, 1, 20),
                issue_date=date(2026, 1, 18),
                status="PAID",
                buyer_name=customer.customer_name,
            ),
            ProjectCost(
                project_id=project.id,
                cost_type="MATERIAL",
                cost_category="材料成本",
                amount=Decimal("200.00"),
                tax_amount=Decimal("26.00"),
                cost_date=date(2026, 1, 22),
                cost_basis="ACTUAL",
            ),
            FinancialProjectCost(
                project_id=project.id,
                project_code=project.project_code,
                project_name=project.project_name,
                cost_type="TRAVEL",
                cost_category="差旅费",
                amount=Decimal("100.00"),
                tax_amount=Decimal("13.00"),
                cost_date=date(2026, 1, 23),
                cost_month="2026-01",
                uploaded_by=user.id,
            ),
        ]
    )
    db_session.commit()

    monthly = get_monthly_trend(year=2026, db=db_session, current_user=user)
    january = next(row for row in monthly if row["month"] == "2026-01")
    assert january["revenueWithoutTax"] == 1000.0
    assert january["revenueTaxAmount"] == 130.0
    assert january["revenueWithTax"] == 1130.0
    assert january["cost"] == 300.0
    assert january["costTaxAmount"] == 39.0
    assert january["costWithTax"] == 339.0
    assert january["cashInflowWithoutTax"] == 500.0
    assert january["cashInflowTaxAmount"] == 65.0
    assert january["cashInflowWithTax"] == 565.0
    assert january["cashFlowWithTax"] == 226.0

    cost_rows = get_cost_analysis(period="month", db=db_session, current_user=user)
    material = next(row for row in cost_rows if row["category"] == "材料成本")
    travel = next(row for row in cost_rows if row["category"] == "差旅费")
    assert material["amount"] == 200.0
    assert material["taxAmount"] == 26.0
    assert material["amountWithTax"] == 226.0
    assert travel["amount"] == 100.0
    assert travel["taxAmount"] == 13.0
    assert travel["amountWithTax"] == 113.0

    profitability = get_project_profitability(limit=10, db=db_session, current_user=user)
    project_row = next(row for row in profitability if row["project"] == project.project_name)
    assert project_row["revenueWithoutTax"] == 1000.0
    assert project_row["revenueTaxAmount"] == 130.0
    assert project_row["revenueWithTax"] == 1130.0
    assert project_row["cost"] == 300.0
    assert project_row["costWithTax"] == 339.0
    assert project_row["profitWithoutTax"] == 700.0
    assert project_row["profitWithTax"] == 791.0

    cash_flow = get_cash_flow(period="month", year=2026, db=db_session, current_user=user)
    cash_january = next(row for row in cash_flow if row["month"] == "2026-01")
    assert cash_january["inflowWithoutTax"] == 500.0
    assert cash_january["inflowTaxAmount"] == 65.0
    assert cash_january["inflowWithTax"] == 565.0
    assert cash_january["outflow"] == 300.0
    assert cash_january["outflowTaxAmount"] == 39.0
    assert cash_january["outflowWithTax"] == 339.0
    assert cash_january["netWithTax"] == 226.0
