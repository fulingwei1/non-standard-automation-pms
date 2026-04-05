# -*- coding: utf-8 -*-
"""
统一导入服务测试配置
提供通用 fixtures
"""

import pytest
from datetime import date
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.material import Material, BomHeader, BomItem
from app.models.project import Project
from app.models.user import User
from app.models.vendor import Vendor


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
def test_user(db_session: Session):
    """创建测试用户"""
    user = User(
        id=1,
        username="testuser",
        email="test@example.com",
        password_hash="hashed",
        real_name="测试用户",
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
    project = Project(
        id=1,
        project_code="PJ260307001",
        project_name="测试项目",
        stage="S3",
        status="ST05",
        health="H1",
        progress_pct=Decimal("30.0"),
        planned_start_date=date.today(),
        planned_end_date=date.today(),
        is_active=True,
        is_archived=False,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_material(db_session: Session):
    """创建测试物料"""
    material = Material(
        id=1,
        material_code="MAT001",
        material_name="测试物料",
        specification="规格A",
        unit="件",
        material_type="原材料",
        standard_price=Decimal("100.00"),
        safety_stock=Decimal("10"),
        is_active=True,
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)
    return material


@pytest.fixture
def test_vendor(db_session: Session):
    """创建测试供应商"""
    vendor = Vendor(
        id=1,
        supplier_code="SUP001",
        supplier_name="测试供应商",
        vendor_type="MATERIAL",
        status="ACTIVE",
    )
    db_session.add(vendor)
    db_session.commit()
    db_session.refresh(vendor)
    return vendor


@pytest.fixture
def test_bom_header(db_session: Session, test_project):
    """创建测试BOM头"""
    bom_header = BomHeader(
        id=1,
        bom_no="BOM001",
        bom_name="测试BOM",
        project_id=test_project.id,
        version="1.0",
        status="DRAFT",
        created_by=1,
    )
    db_session.add(bom_header)
    db_session.commit()
    db_session.refresh(bom_header)
    return bom_header