# -*- coding: utf-8 -*-
"""
项目管理服务测试配置
提供通用 fixtures
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.project import Customer, Project
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
def test_project(db_session: Session):
    """创建测试项目"""
    from decimal import Decimal
    from datetime import date, timedelta

    project = Project(
        project_code="PJ260307001",
        project_name="测试项目",
        stage="S3",
        status="ST05",
        health="H1",
        progress_pct=Decimal("30.0"),
        planned_start_date=date.today() - timedelta(days=30),
        planned_end_date=date.today() + timedelta(days=30),
        is_active=True,
        is_archived=False,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project
