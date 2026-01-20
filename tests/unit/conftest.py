"""
Unit tests fixtures - 不依赖完整应用程序
使用独立的测试数据库引擎，避免与 tests/conftest.py 的 fixture 冲突
"""

import os
import tempfile

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="function")
def db_engine():
    """
    为单元测试提供隔离的 SQLite 引擎：
    - 创建内存数据库或临时文件数据库
    - 导入所有模型以确保表结构被注册
    - 每个测试函数独享数据库，互不影响
    """
    # 创建临时数据库文件
    tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)

    engine = create_engine(
        f"sqlite:///{tmp_db.name}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # 导入所有模型以确保表结构被注册
    import app.models  # noqa: F401
    from app.models.base import Base

    Base.metadata.create_all(bind=engine)

    # 清理测试数据
    with engine.begin() as conn:
        conn.execute(text("PRAGMA foreign_keys=OFF"))
        try:
            conn.execute(text("DELETE FROM task_unified"))
        except Exception:
            pass
        try:
            conn.execute(text("DELETE FROM project_stages"))
        except Exception:
            pass
        try:
            conn.execute(text("DELETE FROM projects"))
        except Exception:
            pass
        try:
            conn.execute(text("DELETE FROM employees"))
        except Exception:
            pass
        try:
            conn.execute(text("DELETE FROM customers"))
        except Exception:
            pass
        conn.execute(text("PRAGMA foreign_keys=ON"))

    yield engine

    engine.dispose()
    tmp_db.close()
    try:
        os.unlink(tmp_db.name)
    except Exception:
        pass


@pytest.fixture(scope="function")
def db_session(db_engine) -> Session:
    """创建测试数据库会话"""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ==================== 常用测试 Fixture ====================


@pytest.fixture
def mock_project(db_session: Session):
    """创建测试项目"""
    from app.models import Project, Customer

    # 创建测试客户
    customer = Customer(
        customer_code="CUST-TEST-001",
        customer_name="测试客户",
        contact_person="测试联系人",
        contact_phone="13800000000",
        status="ACTIVE",
    )
    db_session.add(customer)
    db_session.flush()

    project = Project(
        project_code="PJ-TEST-001",
        project_name="测试项目",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def mock_machine(db_session: Session, mock_project):
    """创建测试机台"""
    from app.models import Machine

    machine = Machine(
        project_id=mock_project.id,
        machine_code="M-TEST-001",
        machine_name="测试设备",
        machine_type="TEST",
        status="DESIGN",
    )
    db_session.add(machine)
    db_session.commit()
    db_session.refresh(machine)
    return machine
