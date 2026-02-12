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
    import app.models.tenant  # noqa: F401
    import app.models.permission  # noqa: F401
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


# ==================== 用户相关 Fixtures ====================


def _create_employee(db_session: Session, code: str, name: str, department: str, role: str):
    """创建员工记录"""
    from app.models.organization import Employee

    employee = db_session.query(Employee).filter(Employee.employee_code == code).first()
    if employee:
        return employee

    employee = Employee(
        employee_code=code,
        name=name,
        department=department,
        role=role,
        phone="18800000000",
        is_active=True,
        employment_status="active",
    )
    db_session.add(employee)
    db_session.flush()
    return employee


def _create_user(
    db_session: Session,
    username: str,
    real_name: str,
    department: str,
    employee_role: str = "ENGINEER",
    is_superuser: bool = False,
):
    """创建用户记录"""
    from app.core.security import get_password_hash
    from app.models.user import User

    user = db_session.query(User).filter(User.username == username).first()
    if user:
        return user

    employee = _create_employee(
        db_session,
        code=f"{username.upper()}-EMP",
        name=real_name,
        department=department,
        role=employee_role,
    )

    user = User(
        employee_id=employee.id,
        username=username,
        password_hash=get_password_hash("test123456"),
        real_name=real_name,
        department=department,
        is_active=True,
        is_superuser=is_superuser,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user(db_session: Session):
    """创建测试用户"""
    return _create_user(
        db_session,
        username="test_user",
        real_name="测试用户",
        department="技术部",
        employee_role="ENGINEER",
    )


@pytest.fixture
def test_admin(db_session: Session):
    """创建测试管理员"""
    return _create_user(
        db_session,
        username="test_admin",
        real_name="测试管理员",
        department="系统",
        employee_role="ADMIN",
        is_superuser=True,
    )


@pytest.fixture
def test_sales_user(db_session: Session):
    """创建销售用户"""
    return _create_user(
        db_session,
        username="test_sales",
        real_name="测试销售",
        department="销售部",
        employee_role="SALES",
    )


@pytest.fixture
def test_finance_user(db_session: Session):
    """创建财务用户"""
    return _create_user(
        db_session,
        username="test_finance",
        real_name="测试财务",
        department="财务部",
        employee_role="FINANCE",
    )


@pytest.fixture
def test_pm_user(db_session: Session):
    """创建项目经理用户"""
    return _create_user(
        db_session,
        username="test_pm",
        real_name="测试项目经理",
        department="项目管理部",
        employee_role="PM",
    )


# ==================== 业务数据 Fixtures ====================


@pytest.fixture
def test_customer(db_session: Session):
    """创建测试客户"""
    from app.models.project import Customer

    customer = Customer(
        customer_code="CUST-UNIT-TEST",
        customer_name="单元测试客户",
        short_name="单测客户",
        customer_type="ENTERPRISE",
        industry="电子制造",
        contact_person="测试联系人",
        contact_phone="13900000000",
        credit_level="A",
        status="ACTIVE",
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)
    return customer


@pytest.fixture
def test_supplier(db_session: Session):
    """创建测试供应商"""
    from app.models.material import Supplier

    supplier = Supplier(
        supplier_code="SUP-UNIT-TEST",
        supplier_name="单元测试供应商",
        supplier_type="STANDARD",
        contact_person="供应商联系人",
        contact_phone="13700000000",
        status="APPROVED",
    )
    db_session.add(supplier)
    db_session.commit()
    db_session.refresh(supplier)
    return supplier


@pytest.fixture
def test_material(db_session: Session):
    """创建测试物料"""
    from decimal import Decimal

    from app.models.material import Material

    material = Material(
        material_code="MAT-UNIT-TEST",
        material_name="单元测试物料",
        material_type="STANDARD",
        specification="规格A",
        unit="个",
        unit_price=Decimal("100.00"),
        is_active=True,
    )
    db_session.add(material)
    db_session.commit()
    db_session.refresh(material)
    return material


@pytest.fixture
def test_contract(db_session: Session, test_customer):
    """创建测试合同"""
    from datetime import date, timedelta
    from decimal import Decimal

    from app.models.sales import Contract

    contract = Contract(
        contract_code="CT-UNIT-TEST",
        contract_name="单元测试合同",
        contract_type="SALES",
        customer_id=test_customer.id,
        customer_name=test_customer.customer_name,
        status="EFFECTIVE",
        contract_amount=Decimal("100000.00"),
        signing_date=date.today(),
        effective_date=date.today(),
        expiry_date=date.today() + timedelta(days=365),
    )
    db_session.add(contract)
    db_session.commit()
    db_session.refresh(contract)
    return contract


@pytest.fixture
def test_lead(db_session: Session, test_sales_user):
    """创建测试销售线索"""
    from decimal import Decimal

    from app.models.sales import Lead

    lead = Lead(
        lead_code="LD-UNIT-TEST",
        lead_name="单元测试线索",
        company_name="潜在客户公司",
        contact_name="联系人",
        contact_phone="13600000000",
        source="WEBSITE",
        status="NEW",
        estimated_amount=Decimal("50000.00"),
        owner_id=test_sales_user.id,
    )
    db_session.add(lead)
    db_session.commit()
    db_session.refresh(lead)
    return lead


@pytest.fixture
def test_opportunity(db_session: Session, test_sales_user, test_customer):
    """创建测试商机"""
    from datetime import date, timedelta
    from decimal import Decimal

    from app.models.sales import Opportunity

    opportunity = Opportunity(
        opportunity_code="OP-UNIT-TEST",
        opportunity_name="单元测试商机",
        customer_id=test_customer.id,
        customer_name=test_customer.customer_name,
        stage="INITIAL",
        status="ACTIVE",
        probability=30,
        expected_amount=Decimal("200000.00"),
        expected_close_date=date.today() + timedelta(days=60),
        owner_id=test_sales_user.id,
    )
    db_session.add(opportunity)
    db_session.commit()
    db_session.refresh(opportunity)
    return opportunity
