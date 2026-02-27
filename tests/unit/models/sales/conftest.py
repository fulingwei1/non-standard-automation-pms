# -*- coding: utf-8 -*-
"""
Sales Models 测试的 Fixtures
"""

import pytest
from datetime import date, datetime, timedelta
from decimal import Decimal


@pytest.fixture
def sample_lead(db_session, sample_user):
    """创建示例线索"""
    from app.models.sales.leads import Lead
    
    lead = Lead(
        lead_code="LEAD001",
        customer_name="潜在客户A",
        industry="制造业",
        contact_name="李四",
        contact_phone="13900139000",
        owner_id=sample_user.id,
        status="NEW"
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)
    return lead


@pytest.fixture
def sample_opportunity(db_session, sample_user, sample_customer):
    """创建示例商机"""
    from app.models.sales.leads import Opportunity
    
    opp = Opportunity(
        opp_code="OPP001",
        opp_name="测试商机",
        customer_id=sample_customer.id,
        owner_id=sample_user.id,
        stage="需求分析",
        probability=Decimal("60.00"),
        est_amount=Decimal("500000.00"),
        expected_close_date=date.today() + timedelta(days=60)
    )
    db_session.add(opp)
    db_session.commit()
    db_session.refresh(opp)
    return opp


@pytest.fixture
def sample_contract(db_session, sample_customer, sample_user):
    """创建示例合同"""
    from app.models.sales.contracts import Contract
    
    contract = Contract(
        contract_code="CONTRACT001",
        contract_name="测试合同",
        customer_id=sample_customer.id,
        contract_type="销售合同",
        contract_amount=Decimal("300000.00"),
        signing_date=date.today(),
        owner_id=sample_user.id,
        status="SIGNED"
    )
    db_session.add(contract)
    db_session.commit()
    db_session.refresh(contract)
    return contract


@pytest.fixture
def sample_quote(db_session, sample_customer, sample_user):
    """创建示例报价单"""
    from app.models.sales.quotes import Quote
    
    quote = Quote(
        quote_code="QUOTE001",
        quote_name="测试报价单",
        customer_id=sample_customer.id,
        quote_amount=Decimal("150000.00"),
        valid_until=date.today() + timedelta(days=30),
        created_by=sample_user.id,
        status="DRAFT"
    )
    db_session.add(quote)
    db_session.commit()
    db_session.refresh(quote)
    return quote
