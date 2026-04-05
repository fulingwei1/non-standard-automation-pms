# -*- coding: utf-8 -*-
"""
知识库服务测试配置文件
"""
import pytest
from datetime import date, datetime
from decimal import Decimal
from unittest.mock import Mock, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.models.base import Base
from app.models.user import User
from app.models.project.core import Project
from app.models.knowledge_base import (
    KnowledgeEntry,
    KnowledgeTypeEnum,
    KnowledgeSourceEnum,
    KnowledgeStatusEnum,
)
from app.models.project_risk import ProjectRisk
from app.models.issue import Issue
from app.models.ecn.core import Ecn
from app.models.project.lifecycle import ProjectStage


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
def test_project(db_session: Session, test_user: User):
    """创建测试项目"""
    project = Project(
        project_code="PJ260406001",
        project_name="测试知识库项目",
        stage="S5",
        status="ST05",
        health="H1",
        progress_pct=Decimal("60.0"),
        planned_start_date=date(2025, 1, 1),
        planned_end_date=date(2025, 6, 30),
        actual_start_date=date(2025, 1, 1),
        budget_amount=Decimal("200000"),
        actual_cost=Decimal("120000"),
        created_by=test_user.id,
        pm_id=test_user.id,
        is_active=True,
        is_archived=False,
        project_type="非标设备",
        product_category="ICT测试设备",
        industry="汽车电子",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def test_risk(db_session: Session, test_project: Project, test_user: User):
    """创建测试风险记录"""
    risk = ProjectRisk(
        project_id=test_project.id,
        risk_name="原材料供应延迟",
        risk_type="SUPPLY",
        risk_level="HIGH",
        description="关键原材料供应商产能不足，可能导致项目延期",
        mitigation_plan="提前储备安全库存，引入备选供应商",
        contingency_plan="启动备选供应商应急采购",
        is_occurred=True,
        actual_impact="延期15天，增加成本20000元",
        created_by=test_user.id,
    )
    db_session.add(risk)
    db_session.commit()
    db_session.refresh(risk)
    return risk


@pytest.fixture
def test_issue(db_session: Session, test_project: Project, test_user: User):
    """创建测试问题记录"""
    issue = Issue(
        project_id=test_project.id,
        title="测试夹具精度不足",
        description="测试夹具重复定位精度达不到要求",
        category="技术问题",
        severity="HIGH",
        status="RESOLVED",
        solution="更换高精密定位元件，调整夹具结构",
        root_cause="定位元件磨损，间隙过大",
        impact_scope="影响测试效率30%",
        created_by=test_user.id,
    )
    db_session.add(issue)
    db_session.commit()
    db_session.refresh(issue)
    return issue


@pytest.fixture
def test_ecn(db_session: Session, test_project: Project, test_user: User):
    """创建测试变更单"""
    ecn = Ecn(
        project_id=test_project.id,
        ecn_no="ECN-001",
        ecn_type="设计变更",
        change_reason="客户需求变更",
        solution="重新设计PCB布局",
        root_cause_analysis="前期需求调研不充分",
        status="CLOSED",
        cost_impact=Decimal("15000"),
        schedule_impact_days=10,
        created_by=test_user.id,
    )
    db_session.add(ecn)
    db_session.commit()
    db_session.refresh(ecn)
    return ecn


@pytest.fixture
def test_stage(db_session: Session, test_project: Project):
    """创建测试阶段记录"""
    stage = ProjectStage(
        project_id=test_project.id,
        stage_code="S5",
        stage_name="设计阶段",
        planned_end_date=date(2025, 3, 31),
        actual_end_date=date(2025, 4, 15),
    )
    db_session.add(stage)
    db_session.commit()
    db_session.refresh(stage)
    return stage