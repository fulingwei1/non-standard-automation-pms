# -*- coding: utf-8 -*-
"""
Finance Models 测试的 Fixtures
"""

import pytest
from datetime import date
from decimal import Decimal


@pytest.fixture
def sample_invoice(db_session, sample_customer):
    """创建示例发票"""
    from app.models.sales.invoices import Invoice
    
    invoice = Invoice(
        invoice_code="INV001",
        amount=Decimal("10000.00"),
        customer_id=sample_customer.id,
        invoice_date=date.today()
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
        payment_date=date.today()
    )
    db_session.add(payment)
    db_session.commit()
    db_session.refresh(payment)
    return payment
