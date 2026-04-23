# -*- coding: utf-8 -*-
"""
Finance Models 测试的 Fixtures
"""

from datetime import date
from decimal import Decimal

import pytest


@pytest.fixture
def sample_contract(db_session, sample_customer, sample_user):
    """创建示例合同"""
    from app.models.sales.contracts import Contract

    contract = Contract(
        contract_code="FIN-CONTRACT-001",
        contract_name="财务测试合同",
        customer_id=sample_customer.id,
        contract_type="sales",
        total_amount=Decimal("300000.00"),
        signing_date=date.today(),
        sales_owner_id=sample_user.id,
        status="SIGNED",
    )
    db_session.add(contract)
    db_session.commit()
    db_session.refresh(contract)
    return contract


@pytest.fixture
def sample_invoice(db_session, sample_contract):
    """创建示例发票"""
    from app.models.sales.invoices import Invoice

    invoice = Invoice(
        invoice_code="INV001",
        amount=Decimal("10000.00"),
        contract_id=sample_contract.id,
        issue_date=date.today(),
    )
    db_session.add(invoice)
    db_session.commit()
    db_session.refresh(invoice)
    return invoice


@pytest.fixture
def sample_payment(db_session, sample_project):
    """创建示例付款"""
    from app.models.finance import Payment

    payment = Payment(
        payment_code="PAY001",
        payment_amount=Decimal("5000.00"),
        project_id=sample_project.id,
        payment_date=date.today(),
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment
