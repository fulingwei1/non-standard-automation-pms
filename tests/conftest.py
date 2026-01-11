import sys
from unittest.mock import MagicMock

# Mock redis module before importing app
redis_mock = MagicMock()
sys.modules["redis"] = redis_mock
sys.modules["redis.exceptions"] = MagicMock()

import uuid
from typing import Callable, Dict, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.config import settings
from app.core.security import get_password_hash
from app.models.base import SessionLocal
from app.models.organization import Employee
from app.models.user import User, Role
from app.models.project import Customer, Project, ProjectMember
from app.models.task_center import TaskUnified, TaskApprovalWorkflow

@pytest.fixture(scope="module")
def client() -> Generator:
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="module")
def admin_token(client: TestClient) -> str:
    """
    获取管理员 token
    注意：这里假设数据库中已经有了 admin 用户。
    如果是在隔离的测试环境中，应该先创建 admin 用户。
    由于目前我们没有隔离数据库，这里尝试直接登录。
    """
    login_data = {
        "username": "admin",
        "password": "admin123",  # 假设默认密码
    }
    r = client.post(f"{settings.API_V1_PREFIX}/auth/login", data=login_data)
    if r.status_code == 200:
        return r.json()["access_token"]
    else:
        # 如果登录失败，可能是因为数据库没有初始化或者密码不对
        # 这里我们可以选择跳过或者抛出错误
        # 为了健壮性，这里先返回 None，测试用例中再处理
        return None

@pytest.fixture(scope="module")
def normal_user_token(client: TestClient) -> str:
    """获取普通用户 token"""
    login_data = {
        "username": "user",
        "password": "user123",  # 假设默认密码
    }
    r = client.post(f"{settings.API_V1_PREFIX}/auth/login", data=login_data)
    if r.status_code == 200:
        return r.json()["access_token"]
    else:
        return None

@pytest.fixture(scope="module")
def sales_user_token(client: TestClient) -> str:
    """获取销售用户 token"""
    login_data = {
        "username": "sales",
        "password": "sales123",  # 假设默认密码
    }
    r = client.post(f"{settings.API_V1_PREFIX}/auth/login", data=login_data)
    if r.status_code == 200:
        return r.json()["access_token"]
    else:
        return None

@pytest.fixture(scope="module")
def finance_user_token(client: TestClient) -> str:
    """获取财务用户 token"""
    login_data = {
        "username": "finance",
        "password": "finance123",  # 假设默认密码
    }
    r = client.post(f"{settings.API_V1_PREFIX}/auth/login", data=login_data)
    if r.status_code == 200:
        return r.json()["access_token"]
    else:
        return None


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    提供与应用相同的数据库会话，供测试直接操作数据库数据
    """
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ---------------------------------------------------------------------------
# 测试辅助常量 & 工具
# ---------------------------------------------------------------------------

ENGINEER_CREDENTIALS: Dict[str, str] = {"username": "engineer_test", "password": "engineer123"}
PM_CREDENTIALS: Dict[str, str] = {"username": "pm_test", "password": "pm123"}
REGULAR_USER_CREDENTIALS: Dict[str, str] = {"username": "regular_user", "password": "regular123"}


def _get_or_create_employee(db: Session, code: str, name: str, department: str) -> Employee:
    employee = db.query(Employee).filter(Employee.employee_code == code).first()
    if not employee:
        employee = Employee(
            employee_code=code,
            name=name,
            department=department,
            role="ENGINEER",
            phone="18800000000",
        )
        db.add(employee)
        db.flush()
    return employee


def _get_or_create_user(db: Session, username: str, password: str, real_name: str, department: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if user:
        return user

    employee = _get_or_create_employee(
        db,
        code=f"{username.upper()}-EMP",
        name=real_name,
        department=department,
    )

    user = User(
        employee_id=employee.id,
        username=username,
        password_hash=get_password_hash(password),
        real_name=real_name,
        department=department,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _ensure_role(db: Session, role_code: str, role_name: str) -> Role:
    """确保角色字典中存在指定角色编码"""
    role = db.query(Role).filter(Role.role_code == role_code).first()
    if role:
        return role
    role = Role(
        role_code=role_code,
        role_name=role_name,
        description=f"{role_name}（测试自动创建）",
        is_system=True,
        is_active=True,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


@pytest.fixture(scope="function")
def engineer_user(db_session: Session) -> User:
    """确保存在用于工程师接口测试的用户"""
    return _get_or_create_user(
        db_session,
        username=ENGINEER_CREDENTIALS["username"],
        password=ENGINEER_CREDENTIALS["password"],
        real_name="工程师一号",
        department="工程部",
    )


@pytest.fixture(scope="function")
def pm_user(db_session: Session) -> User:
    """确保存在用于PM审批的用户"""
    return _get_or_create_user(
        db_session,
        username=PM_CREDENTIALS["username"],
        password=PM_CREDENTIALS["password"],
        real_name="项目经理",
        department="项目管理部",
    )


@pytest.fixture(scope="function")
def regular_user(db_session: Session) -> User:
    """确保存在普通权限的业务用户"""
    return _get_or_create_user(
        db_session,
        username=REGULAR_USER_CREDENTIALS["username"],
        password=REGULAR_USER_CREDENTIALS["password"],
        real_name="普通业务用户",
        department="综合管理部",
    )


def _ensure_customer(db: Session) -> Customer:
    customer = db.query(Customer).filter(Customer.customer_code == "CUST-ENGINEER").first()
    if not customer:
        customer = Customer(
            customer_code="CUST-ENGINEER",
            customer_name="工程师测试客户",
            contact_person="张三",
            contact_phone="13800000000",
            status="ACTIVE",
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
    return customer


@pytest.fixture(scope="function")
def mock_project(db_session: Session, engineer_user: User, pm_user: User) -> Project:
    """创建用于工程师端测试的项目及成员关系"""
    _ensure_role(db_session, "PM", "项目经理")
    _ensure_role(db_session, "ENGINEER", "工程师")
    customer = _ensure_customer(db_session)
    project = Project(
        project_code=f"PJT-{uuid.uuid4().hex[:8].upper()}",
        project_name="工程师测试项目",
        customer_id=customer.id,
        customer_name=customer.customer_name,
        stage="S1",
        status="ST01",
        health="H1",
        pm_id=pm_user.id,
        pm_name=pm_user.real_name or pm_user.username,
        priority="NORMAL",
        created_by=pm_user.id,
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    # 创建项目成员：项目经理 + 工程师
    members = [
        ProjectMember(
            project_id=project.id,
            user_id=pm_user.id,
            role_code="PM",
            is_lead=True,
            allocation_pct=100,
            created_by=pm_user.id,
        ),
        ProjectMember(
            project_id=project.id,
            user_id=engineer_user.id,
            role_code="ENGINEER",
            allocation_pct=100,
            created_by=pm_user.id,
        ),
    ]
    db_session.add_all(members)
    db_session.commit()
    return project


@pytest.fixture(scope="function")
def mock_user(engineer_user: User) -> User:
    """返回工程师用户供其他fixtures使用"""
    return engineer_user


@pytest.fixture(scope="function")
def create_test_task(
    db_session: Session, mock_project: Project, mock_user: User
) -> Callable[..., TaskUnified]:
    """工厂方法：便捷创建 TaskUnified 记录"""

    def _create_task(**overrides) -> TaskUnified:
        session: Session = overrides.pop("db", db_session)
        task_code = overrides.get("task_code", f"TASK-{uuid.uuid4().hex[:10].upper()}")

        existing = session.query(TaskUnified).filter(TaskUnified.task_code == task_code).first()
        if existing:
            session.delete(existing)
            session.commit()

        task = TaskUnified(
            task_code=task_code,
            title=overrides.get("title", "测试任务"),
            description=overrides.get("description"),
            task_type="PROJECT_WBS",
            source_type="MANUAL",
            project_id=overrides.get("project_id", mock_project.id),
            project_code=overrides.get("project_code", mock_project.project_code),
            project_name=overrides.get("project_name", mock_project.project_name),
            assignee_id=overrides.get("assignee_id", mock_user.id),
            assignee_name=overrides.get("assignee_name", mock_user.real_name or mock_user.username),
            assigner_id=overrides.get("assigner_id", mock_user.id),
            assigner_name=overrides.get("assigner_name", mock_user.real_name or mock_user.username),
            plan_start_date=overrides.get("plan_start_date"),
            plan_end_date=overrides.get("plan_end_date"),
            deadline=overrides.get("deadline"),
            estimated_hours=overrides.get("estimated_hours", 8.0),
            actual_hours=overrides.get("actual_hours", 0),
            status=overrides.get("status", "IN_PROGRESS"),
            progress=overrides.get("progress", 0),
            priority=overrides.get("priority", "MEDIUM"),
            approval_required=overrides.get("approval_required", False),
            approval_status=overrides.get("approval_status"),
            task_importance=overrides.get("task_importance", "GENERAL"),
            created_by=overrides.get("created_by", mock_user.id),
            updated_by=overrides.get("updated_by", mock_user.id),
            is_delayed=overrides.get("is_delayed", False),
            is_active=overrides.get("is_active", True),
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

    return _create_task


@pytest.fixture(scope="function")
def mock_task(create_test_task: Callable[..., TaskUnified]) -> TaskUnified:
    """默认工程师任务"""
    return create_test_task(status="ACCEPTED", progress=0, task_importance="GENERAL")


@pytest.fixture(scope="function")
def mock_important_task(
    db_session: Session,
    create_test_task: Callable[..., TaskUnified],
    mock_user: User,
    pm_user: User,
) -> TaskUnified:
    """生成一个待审批的重要任务及审批工作流"""
    task = create_test_task(
        title="重要任务",
        task_importance="IMPORTANT",
        approval_required=True,
        approval_status="PENDING_APPROVAL",
        status="PENDING_APPROVAL",
    )
    workflow = TaskApprovalWorkflow(
        task_id=task.id,
        submitted_by=mock_user.id,
        submit_note="测试任务必要性",
        approver_id=pm_user.id,
        approval_status="PENDING",
    )
    db_session.add(workflow)
    db_session.commit()
    return task


# ---------------------------------------------------------------------------
# 认证头部 fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def auth_headers(client: TestClient, engineer_user: User) -> Dict[str, str]:
    """返回普通工程师的Bearer Token"""
    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        data={
            "username": ENGINEER_CREDENTIALS["username"],
            "password": ENGINEER_CREDENTIALS["password"],
        },
    )
    assert response.status_code == 200, "工程师账号登录失败"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def pm_auth_headers(client: TestClient, pm_user: User) -> Dict[str, str]:
    """返回PM账号的Bearer Token"""
    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        data={
            "username": PM_CREDENTIALS["username"],
            "password": PM_CREDENTIALS["password"],
        },
    )
    assert response.status_code == 200, "PM账号登录失败"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def regular_user_token(client: TestClient, regular_user: User) -> str:
    """返回普通业务用户的Bearer Token"""
    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        data={
            "username": REGULAR_USER_CREDENTIALS["username"],
            "password": REGULAR_USER_CREDENTIALS["password"],
        },
    )
    assert response.status_code == 200, "普通业务账号登录失败"
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def db(db_session: Session) -> Session:
    """兼容旧测试中引用的 db fixture"""
    return db_session


# ---------------------------------------------------------------------------
# Factory-based fixtures (使用 factory_boy)
# ---------------------------------------------------------------------------

from tests.factories import (
    UserFactory,
    AdminUserFactory,
    EmployeeFactory,
    CustomerFactory,
    ProjectFactory,
    ProjectWithCustomerFactory,
    SupplierFactory,
    MaterialFactory,
    BomHeaderFactory,
    PurchaseOrderFactory,
    LeadFactory,
    OpportunityFactory,
    QuoteFactory,
    ContractFactory,
    ProjectBudgetFactory,
    create_test_user,
    create_test_project,
    create_complete_project_setup,
)


@pytest.fixture(scope="function")
def test_employee() -> Employee:
    """创建测试员工"""
    return EmployeeFactory()


@pytest.fixture(scope="function")
def test_user() -> User:
    """创建测试用户"""
    return UserFactory()


@pytest.fixture(scope="function")
def test_admin() -> User:
    """创建测试管理员"""
    return AdminUserFactory()


@pytest.fixture(scope="function")
def test_customer() -> Customer:
    """创建测试客户"""
    return CustomerFactory()


@pytest.fixture(scope="function")
def test_project() -> Project:
    """创建测试项目（不带客户关联）"""
    return ProjectFactory()


@pytest.fixture(scope="function")
def test_project_with_customer() -> Project:
    """创建测试项目（带客户关联）"""
    return ProjectWithCustomerFactory()


@pytest.fixture(scope="function")
def test_supplier():
    """创建测试供应商"""
    return SupplierFactory()


@pytest.fixture(scope="function")
def test_material():
    """创建测试物料"""
    return MaterialFactory()


@pytest.fixture(scope="function")
def test_materials():
    """创建多个测试物料"""
    return MaterialFactory.create_batch(5)


@pytest.fixture(scope="function")
def test_purchase_order():
    """创建测试采购订单"""
    return PurchaseOrderFactory()


@pytest.fixture(scope="function")
def test_lead():
    """创建测试销售线索"""
    return LeadFactory()


@pytest.fixture(scope="function")
def test_opportunity():
    """创建测试商机"""
    return OpportunityFactory()


@pytest.fixture(scope="function")
def test_quote():
    """创建测试报价单"""
    return QuoteFactory()


@pytest.fixture(scope="function")
def test_contract():
    """创建测试合同"""
    return ContractFactory()


@pytest.fixture(scope="function")
def test_budget():
    """创建测试预算"""
    return ProjectBudgetFactory()


@pytest.fixture(scope="function")
def complete_project_setup():
    """
    创建完整的项目测试数据集

    包含：客户、项目、供应商、物料、BOM
    """
    return create_complete_project_setup()
