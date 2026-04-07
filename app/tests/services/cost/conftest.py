# -*- coding: utf-8 -*-
"""
成本服务测试配置
提供通用 fixtures
"""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.project import Customer, Project, ProjectCost
from app.models.sales import Contract, Invoice
from app.models.user import User


@pytest.fixture(scope="function")
def db_session():
    """创建测试数据库会话"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_customer(db_session: Session):
    """创建测试客户"""
    customer = Customer(
        customer_code="CUST001",
        customer_name="测试客户",
        contact_person="张三",
        contact_phone="13800138000",
        address="测试地址",
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def test_user(db_session: Session):
    """创建测试用户"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
        full_name="测试用户",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_project(db_session: Session, test_customer):
    """创建测试项目"""
    project = Project(
        project_code="PJ260307001",
        project_name="测试项目",
        stage="S3",
        status="ST05",
        health="H1",
        progress_pct=Decimal("30.0"),
        planned_start_date=date.today() - timedelta(days=30),
        planned_end_date=date.today() + timedelta(days=30),
        contract_amount=Decimal("100000"),
        budget_amount=Decimal("80000"),
        actual_cost=Decimal("50000"),
        is_active=True,
        is_archived=False,
        customer_id=test_customer.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_project_with_costs(db_session: Session, test_project):
    """创建带成本记录的测试项目"""
    # 添加成本记录
    costs = [
        ProjectCost(
            project_id=test_project.id,
            cost_type="材料费",
            cost_category="BOM",
            amount=Decimal("20000"),
            cost_date=date.today() - timedelta(days=15),
            source_module="bom",
            source_type="bom_header",
            source_id=1,
            source_no="BOM001",
        ),
        ProjectCost(
            project_id=test_project.id,
            cost_type="人工费",
            cost_category="人工",
            amount=Decimal("15000"),
            cost_date=date.today() - timedelta(days=10),
            source_module="timesheet",
            source_type="timesheet",
            source_id=1,
            source_no="TS001",
        ),
        ProjectCost(
            project_id=test_project.id,
            cost_type="外协费",
            cost_category="外协",
            amount=Decimal("10000"),
            cost_date=date.today() - timedelta(days=5),
            source_module="outsourcing",
            source_type="outsourcing_order",
            source_id=1,
            source_no="OUT001",
        ),
        ProjectCost(
            project_id=test_project.id,
            cost_type="差旅费",
            cost_category="其他",
            amount=Decimal("5000"),
            cost_date=date.today(),
            source_module="expense",
            source_type="expense_record",
            source_id=1,
            source_no="EXP001",
        ),
    ]
    for cost in costs:
        db_session.add(cost)
    db_session.commit()
    
    for cost in costs:
        db_session.refresh(cost)
    
    return test_project


@pytest.fixture
def test_project_no_costs(db_session: Session, test_customer):
    """创建没有成本记录的测试项目"""
    project = Project(
        project_code="PJ260307002",
        project_name="无成本项目",
        stage="S1",
        status="ST01",
        health="H1",
        progress_pct=Decimal("10.0"),
        planned_start_date=date.today(),
        planned_end_date=date.today() + timedelta(days=60),
        contract_amount=Decimal("50000"),
        budget_amount=Decimal("40000"),
        actual_cost=Decimal("0"),
        is_active=True,
        is_archived=False,
        customer_id=test_customer.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_invoice(db_session: Session, test_project):
    """创建测试发票"""
    # 需要先创建一个合同
    contract = Contract(
        contract_code="CONTRACT001",
        contract_name="测试合同",
        project_id=test_project.id,
        customer_id=test_project.customer_id,
        contract_amount=Decimal("100000"),
        total_amount=Decimal("100000"),
        status="SIGNED",
    )
    db_session.add(contract)
    db_session.commit()
    db_session.refresh(contract)
    
    invoice = Invoice(
        contract_id=contract.id,
        project_id=test_project.id,
        invoice_code="INV001",
        invoice_type="增值税专用发票",
        amount=Decimal("100000"),
        tax_amount=Decimal("13000"),
        status="PAID",
        paid_amount=Decimal("100000"),
        issue_date=date.today() - timedelta(days=30),
    )
    db_session.add(invoice)
    db_session.commit()
    db_session.refresh(invoice)
    return invoice