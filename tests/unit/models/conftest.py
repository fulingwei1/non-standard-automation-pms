# -*- coding: utf-8 -*-
"""
Models 测试的 Fixtures
"""

import pytest
from datetime import datetime, date, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.base import Base


@pytest.fixture(scope="function")
def db_session():
    """为每个测试函数创建独立的数据库会话"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def sample_user(db_session):
    """创建示例用户"""
    from app.models.user import User
    from app.core.security import get_password_hash
    
    user = User(
        username="testuser",
        password_hash=get_password_hash("password123"),
        email="test@example.com",
        real_name="测试用户",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_department(db_session):
    """创建示例部门"""
    from app.models.organization import Department
    
    dept = Department(
        dept_name="技术部",
        dept_code="TECH001",
        manager_id=None
    )
    db_session.add(dept)
    db_session.commit()
    db_session.refresh(dept)
    return dept


@pytest.fixture
def sample_customer(db_session):
    """创建示例客户"""
    from app.models.project.customer import Customer
    
    customer = Customer(
        customer_name="测试客户",
        customer_code="CUST001",
        contact_person="张三",
        contact_phone="13800138000",
        customer_type="企业"
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def sample_project(db_session, sample_customer, sample_user):
    """创建示例项目"""
    from app.models.project.core import Project
    
    project = Project(
        project_code="PRJ001",
        project_name="测试项目",
        customer_id=sample_customer.id,
        pm_id=sample_user.id,
        contract_amount=Decimal("100000.00"),
        planned_start_date=date.today(),
        planned_end_date=date.today() + timedelta(days=90)
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project
