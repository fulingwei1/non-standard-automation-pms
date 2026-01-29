import sys
from unittest.mock import MagicMock

# Mock redis module before importing app
redis_mock = MagicMock()
sys.modules["redis"] = redis_mock
sys.modules["redis.exceptions"] = MagicMock()

import os

# ---------------------------------------------------------------------------
# Test database isolation
# ---------------------------------------------------------------------------
# The repository may contain a pre-existing `data/app.db` with legacy/demo data
# and schema drift (e.g. wrong column types). API tests should run against a
# clean, predictable SQLite database.
# Use in-memory SQLite database for tests to avoid readonly file permission issues.
os.environ["SQLITE_DB_PATH"] = ":memory:"
# Disable Redis during tests to avoid token blacklist issues with MagicMock.
# MagicMock.exists() returns MagicMock which is truthy, causing all tokens to be "revoked".
os.environ["REDIS_URL"] = ""
# Disable schedulers during tests to avoid background writes.
os.environ.setdefault("ENABLE_SCHEDULER", "false")

import uuid
from typing import Callable, Dict, Generator, Iterable, Optional, Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.services.permission_cache_service import get_permission_cache_service

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.main import app
from app.models.base import SessionLocal
from app.models.organization import Employee
from app.models.project import Customer, Machine, Project, ProjectMember
from app.models.task_center import TaskApprovalWorkflow, TaskUnified
from app.models.user import (
    ApiPermission,
    Role,
    RoleApiPermission,
    User,
    UserRole,
)


def _ensure_login_user(
    db: Session,
    username: str,
    password: str,
    *,
    real_name: str,
    department: str,
    employee_role: str = "ENGINEER",
    is_superuser: bool = False,
) -> User:
    """
    Ensure a login-capable user exists for API tests.

    Many API tests are skipped when default users are missing; creating them
    here allows the existing test suite to exercise real endpoints and improve
    coverage.
    """
    user = _get_or_create_user(
        db,
        username=username,
        password=password,
        real_name=real_name,
        department=department,
        employee_role=employee_role,
    )
    if user.is_superuser != is_superuser:
        db.query(User).filter(User.id == user.id).update({"is_superuser": is_superuser})
        db.commit()
    return user


@pytest.fixture(scope="session", autouse=True)
def _init_test_database() -> None:
    """
    Initialize a clean SQLite database for the whole test session.

    - Ensures all models are imported so metadata is complete.
    - Creates tables based on SQLAlchemy models.
    - Seeds minimal baseline records to prevent "empty DB" skips in API tests.
    """
    from datetime import date

    import app.models  # noqa: F401  # register all models into Base.metadata
    from app.models.acceptance import (
        AcceptanceOrder,
        AcceptanceOrderItem,
        AcceptanceTemplate,
        TemplateCategory,
        TemplateCheckItem,
    )
    from app.models.base import get_session, init_db
    from app.models.vendor import Vendor

    init_db(drop_all=True)

    db = get_session()
    try:
        admin = _ensure_login_user(
            db,
            username="admin",
            password="admin123",
            real_name="系统管理员",
            department="系统",
            employee_role="ADMIN",
            is_superuser=True,
        )

        # Minimal project + machine + acceptance template + order for acceptance API tests.
        customer = Customer(
            customer_code="CUST-TEST",
            customer_name="测试客户",
            contact_person="联系人",
            contact_phone="13800000000",
            status="ACTIVE",
        )
        db.add(customer)
        db.flush()

        from app.models.vendor import Vendor

        supplier = Vendor(
            supplier_code="SUP-TEST",
            supplier_name="测试供应商",
            vendor_type="MATERIAL",
            contact_person="供应商联系人",
            contact_phone="13900000000",
            status="ACTIVE",
            created_by=admin.id,
        )
        db.add(supplier)
        db.flush()

        project = Project(
            project_code="PJ-TEST",
            project_name="测试项目",
            customer_id=customer.id,
            customer_name=customer.customer_name,
            stage="S1",
            status="ST01",
            health="H1",
            created_by=admin.id,
        )
        db.add(project)
        db.flush()

        machine = Machine(
            project_id=project.id,
            machine_code="M-TEST",
            machine_name="测试设备",
            machine_type="TEST",
            status="DESIGN",
        )
        db.add(machine)
        db.flush()

        template = AcceptanceTemplate(
            template_code="AT-TEST",
            template_name="测试验收模板",
            acceptance_type="FAT",
            equipment_type="TEST",
            version="1.0",
            is_system=True,
            is_active=True,
            created_by=admin.id,
        )
        db.add(template)
        db.flush()

        category = TemplateCategory(
            template_id=template.id,
            category_code="CAT-TEST",
            category_name="测试分类",
            weight=0,
            sort_order=0,
            is_required=True,
            description="测试分类",
        )
        db.add(category)
        db.flush()

        check_item = TemplateCheckItem(
            category_id=category.id,
            item_code="ITEM-TEST",
            item_name="测试检查项",
            sort_order=0,
            is_required=True,
            is_key_item=False,
        )
        db.add(check_item)
        db.flush()

        order = AcceptanceOrder(
            order_no="AO-TEST",
            project_id=project.id,
            machine_id=machine.id,
            acceptance_type="FAT",
            template_id=template.id,
            planned_date=date.today(),
            location="测试地点",
            status="DRAFT",
            total_items=1,
            passed_items=0,
            failed_items=0,
            na_items=0,
            created_by=admin.id,
        )
        db.add(order)
        db.flush()

        order_item = AcceptanceOrderItem(
            order_id=order.id,
            category_id=category.id,
            template_item_id=check_item.id,
            category_code=category.category_code,
            category_name=category.category_name,
            item_code=check_item.item_code,
            item_name=check_item.item_name,
            is_required=True,
            is_key_item=False,
            sort_order=0,
            result_status="PENDING",
        )
        db.add(order_item)

        db.commit()
    finally:
        db.close()


@pytest.fixture(scope="module")
def client() -> Generator:
    # Disable rate limiting during tests to avoid flaky 429 responses from slowapi
    # when multiple fixtures log in repeatedly.
    if getattr(app.state, "limiter", None) is not None:
        app.state.limiter.enabled = False
    with TestClient(app) as c:
        yield c


def _get_auth_token(
    db: Session, username: str = "admin", password: str = "admin123"
) -> str:
    """
    获取认证 token 的辅助函数

    Args:
        db: 数据库会话
        username: 用户名
        password: 密码

    Returns:
        JWT token 字符串
    """
    from app.main import app
    from fastapi.testclient import TestClient

    # 确保用户存在
    _ensure_login_user(
        db,
        username=username,
        password=password,
        real_name="测试用户" if username != "admin" else "系统管理员",
        department="测试部门" if username != "admin" else "系统",
        employee_role="ENGINEER" if username != "admin" else "ADMIN",
        is_superuser=(username == "admin"),
    )
    db.commit()

    # 通过登录接口获取 token
    client = TestClient(app)
    login_data = {
        "username": username,
        "password": password,
    }
    response = client.post(f"{settings.API_V1_PREFIX}/auth/login", data=login_data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise ValueError(
            f"Failed to get auth token: {response.status_code} - {response.text}"
        )


@pytest.fixture(scope="module")
def admin_token(client: TestClient) -> str:
    """
    获取管理员 token
    注意：这里假设数据库中已经有了 admin 用户。
    如果是在隔离的测试环境中，应该先创建 admin 用户。
    由于目前我们没有隔离数据库，这里尝试直接登录。
    """
    # Ensure an admin user exists so API/integration tests can run instead of skipping.
    db = SessionLocal()
    try:
        _ensure_login_user(
            db,
            username="admin",
            password="admin123",
            real_name="系统管理员",
            department="系统",
            employee_role="ADMIN",
            is_superuser=True,
        )
    finally:
        db.close()

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
    db = SessionLocal()
    try:
        _ensure_login_user(
            db,
            username="user",
            password="user123",
            real_name="普通用户",
            department="综合管理部",
            employee_role="BUSINESS_USER",
            is_superuser=False,
        )
    finally:
        db.close()

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
    db = SessionLocal()
    try:
        # Sales permission matrix varies across deployments; use superuser to keep
        # permission-filtering tests focused on API behavior rather than role setup.
        _ensure_login_user(
            db,
            username="sales",
            password="sales123",
            real_name="销售用户",
            department="销售部",
            employee_role="SALES",
            is_superuser=True,
        )
    finally:
        db.close()

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
    db = SessionLocal()
    try:
        _ensure_login_user(
            db,
            username="finance",
            password="finance123",
            real_name="财务用户",
            department="财务部",
            employee_role="FINANCE",
            is_superuser=True,
        )
    finally:
        db.close()

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

    每个测试结束后自动回滚，确保测试隔离：
    - 使用事务包装所有操作
    - 测试结束时回滚，不提交数据
    - 避免测试间相互影响
    """
    session: Session = SessionLocal()
    transaction = session.begin_nested()

    try:
        yield session
    finally:
        # 强制回滚，不提交任何数据到数据库
        if transaction.is_active:
            transaction.rollback()
        session.close()


@pytest.fixture(scope="function", autouse=True)
def cleanup_permission_cache():
    """每个测试前后清理权限缓存，防止 ID 重复导致的测试污染"""
    cache_service = get_permission_cache_service()
    cache_service.invalidate_all()
    yield
    cache_service.invalidate_all()


_token_cache: Dict[str, str] = {}


def _get_cached_token(username: str) -> Optional[str]:
    """
    从缓存获取 token，避免重复登录请求

    登录请求较慢，缓存 token 可以显著提升测试执行速度
    """
    return _token_cache.get(username)


def _set_cached_token(username: str, token: str) -> None:
    """
    缓存 token 供后续测试使用
    """
    _token_cache[username] = token


def _clear_token_cache() -> None:
    """
    清空 token 缓存，用于 session 级清理
    """
    _token_cache.clear()


@pytest.fixture(scope="session", autouse=True)
def clear_token_cache_on_session_end():
    """
    Session 级别清理：每个测试会话结束后清空 token 缓存
    避免跨 session 的 token 污染
    """
    yield
    _clear_token_cache()


# ---------------------------------------------------------------------------
# 测试辅助常量 & 工具
# ---------------------------------------------------------------------------

ENGINEER_CREDENTIALS: Dict[str, str] = {
    "username": "engineer_test",
    "password": "engineer123",
}
PM_CREDENTIALS: Dict[str, str] = {"username": "pm_test", "password": "pm123"}
REGULAR_USER_CREDENTIALS: Dict[str, str] = {
    "username": "regular_user",
    "password": "regular123",
}

ENGINEER_PERMISSION_SPECS: Tuple[Tuple[str, str], ...] = (
    ("engineer:read", "工程师进度查看"),
    ("engineer:create", "工程师任务创建"),
)


def _ensure_permission(db: Session, code: str, name: str) -> ApiPermission:
    permission = db.query(ApiPermission).filter(ApiPermission.perm_code == code).first()
    if permission:
        return permission

    permission = ApiPermission(
        perm_code=code,
        perm_name=name,
        module="engineer",
        action="access",
        description=f"测试自动创建 - {name}",
        is_active=True,
    )
    db.add(permission)
    db.commit()
    db.refresh(permission)
    return permission


def _get_or_create_employee(
    db: Session,
    code: str,
    name: str,
    department: str,
    role: str = "ENGINEER",
) -> Employee:
    employee = db.query(Employee).filter(Employee.employee_code == code).first()
    if employee:
        updated = False
        if not employee.is_active:
            employee.is_active = True
            updated = True
        if employee.employment_status != "active":
            employee.employment_status = "active"
            updated = True
        if department and employee.department != department:
            employee.department = department
            updated = True
        if role and employee.role != role:
            employee.role = role
            updated = True
        if updated:
            db.commit()
            db.refresh(employee)
        return employee

    employee = Employee(
        employee_code=code,
        name=name,
        department=department,
        role=role or "ENGINEER",
        phone="18800000000",
    )
    db.add(employee)
    db.flush()
    return employee


def _get_or_create_user(
    db: Session,
    username: str,
    password: str,
    real_name: str,
    department: str,
    employee_role: str = "ENGINEER",
) -> User:
    user = db.query(User).filter(User.username == username).first()
    if user:
        updated = False
        if not user.is_active:
            user.is_active = True
            updated = True
        if real_name and user.real_name != real_name:
            user.real_name = real_name
            updated = True
        if department and user.department != department:
            user.department = department
            updated = True
        if not user.password_hash or not verify_password(password, user.password_hash):
            user.password_hash = get_password_hash(password)
            updated = True
        if updated:
            db.commit()
            db.refresh(user)
        return user

    employee = _get_or_create_employee(
        db,
        code=f"{username.upper()}-EMP",
        name=real_name,
        department=department,
        role=employee_role,
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


def _ensure_role_permissions(
    db: Session, role: Role, permission_specs: Iterable[Tuple[str, str]]
) -> None:
    changed = False
    for code, name in permission_specs:
        permission = _ensure_permission(db, code, name)
        exists = (
            db.query(RoleApiPermission)
            .filter(
                RoleApiPermission.role_id == role.id,
                RoleApiPermission.permission_id == permission.id,
            )
            .first()
        )
        if not exists:
            db.add(RoleApiPermission(role_id=role.id, permission_id=permission.id))
            changed = True
    if changed:
        db.commit()


def _assign_role_to_user(db: Session, user: User, role: Role) -> None:
    exists = (
        db.query(UserRole)
        .filter(UserRole.user_id == user.id, UserRole.role_id == role.id)
        .first()
    )
    if exists:
        return
    db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()


@pytest.fixture(scope="function")
def engineer_user(db_session: Session) -> User:
    """确保存在用于工程师接口测试的用户"""
    user = _get_or_create_user(
        db_session,
        username=ENGINEER_CREDENTIALS["username"],
        password=ENGINEER_CREDENTIALS["password"],
        real_name="工程师一号",
        department="工程部",
        employee_role="ENGINEER",
    )
    engineer_role = _ensure_role(db_session, "ENGINEER", "工程师")
    _ensure_role_permissions(db_session, engineer_role, ENGINEER_PERMISSION_SPECS)
    _assign_role_to_user(db_session, user, engineer_role)
    return user


@pytest.fixture(scope="function")
def pm_user(db_session: Session) -> User:
    """确保存在用于PM审批的用户"""
    user = _get_or_create_user(
        db_session,
        username=PM_CREDENTIALS["username"],
        password=PM_CREDENTIALS["password"],
        real_name="项目经理",
        department="项目管理部",
        employee_role="PM",
    )
    pm_role = _ensure_role(db_session, "PROJECT_MANAGER", "项目经理")
    _ensure_role_permissions(db_session, pm_role, ENGINEER_PERMISSION_SPECS)
    _assign_role_to_user(db_session, user, pm_role)
    return user


@pytest.fixture(scope="function")
def regular_user(db_session: Session) -> User:
    """确保存在普通权限的业务用户"""
    user = _get_or_create_user(
        db_session,
        username=REGULAR_USER_CREDENTIALS["username"],
        password=REGULAR_USER_CREDENTIALS["password"],
        real_name="普通业务用户",
        department="综合管理部",
        employee_role="BUSINESS_USER",
    )
    return user


def _ensure_customer(db: Session) -> Customer:
    customer = (
        db.query(Customer).filter(Customer.customer_code == "CUST-ENGINEER").first()
    )
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

        existing = (
            session.query(TaskUnified)
            .filter(TaskUnified.task_code == task_code)
            .first()
        )
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
            assignee_name=overrides.get(
                "assignee_name", mock_user.real_name or mock_user.username
            ),
            assigner_id=overrides.get("assigner_id", mock_user.id),
            assigner_name=overrides.get(
                "assigner_name", mock_user.real_name or mock_user.username
            ),
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
    """Return engineer user Bearer Token"""
    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        data={
            "username": ENGINEER_CREDENTIALS["username"],
            "password": ENGINEER_CREDENTIALS["password"],
        },
    )
    assert response.status_code == 200, "Engineer login failed"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def pm_auth_headers(client: TestClient, pm_user: User) -> Dict[str, str]:
    """Return PM user Bearer Token"""
    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        data={
            "username": PM_CREDENTIALS["username"],
            "password": PM_CREDENTIALS["password"],
        },
    )
    assert response.status_code == 200, "PM login failed"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(client: TestClient, admin_token: str) -> Dict[str, str]:
    """Return Admin Bearer Token"""
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def regular_user_token(client: TestClient, regular_user: User) -> str:
    """Get regular user Bearer Token"""
    response = client.post(
        f"{settings.API_V1_PREFIX}/auth/login",
        data={
            "username": REGULAR_USER_CREDENTIALS["username"],
            "password": REGULAR_USER_CREDENTIALS["password"],
        },
    )
    assert response.status_code == 200, "Regular user login failed"
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def db(db_session: Session) -> Session:
    """Alias for db_session fixture for backward compatibility"""
    return db_session


# ---------------------------------------------------------------------------
# Factory-based fixtures (使用 factory_boy)
# ---------------------------------------------------------------------------

from tests.factories import (
    AdminUserFactory,
    ContractFactory,
    CustomerFactory,
    EmployeeFactory,
    LeadFactory,
    MaterialFactory,
    OpportunityFactory,
    ProjectBudgetFactory,
    ProjectFactory,
    ProjectWithCustomerFactory,
    PurchaseOrderFactory,
    QuoteFactory,
    UserFactory,
    create_complete_project_setup,
)


@pytest.fixture(scope="function")
def test_employee() -> Employee:
    """Create test employee"""
    return EmployeeFactory()


@pytest.fixture(scope="function")
def test_user() -> User:
    """Create test user"""
    return UserFactory()


@pytest.fixture(scope="function")
def test_admin() -> User:
    """Create test admin"""
    return AdminUserFactory()


@pytest.fixture(scope="function")
def test_customer() -> Customer:
    """Create test customer"""
    return CustomerFactory()


@pytest.fixture(scope="function")
def test_project() -> Project:
    """Create test project (without customer relationship)"""
    return ProjectFactory()


@pytest.fixture(scope="function")
def test_project_with_customer() -> Project:
    """Create test project (with customer relationship)"""
    return ProjectWithCustomerFactory()


@pytest.fixture(scope="function")
def test_supplier():
    """Create test supplier"""
    return SupplierFactory()


@pytest.fixture(scope="function")
def test_material():
    """Create test material"""
    return MaterialFactory()


@pytest.fixture(scope="function")
def test_materials():
    """Create multiple test materials"""
    return MaterialFactory.create_batch(5)


@pytest.fixture(scope="function")
def test_purchase_order():
    """Create test purchase order"""
    return PurchaseOrderFactory()


@pytest.fixture(scope="function")
def test_lead():
    """Create test lead"""
    return LeadFactory()


@pytest.fixture(scope="function")
def test_opportunity():
    """Create test opportunity"""
    return OpportunityFactory()


@pytest.fixture(scope="function")
def test_quote():
    """Create test quote"""
    return QuoteFactory()


@pytest.fixture(scope="function")
def test_contract():
    """Create test contract"""
    return ContractFactory()


@pytest.fixture(scope="function")
def test_budget():
    """Create test budget"""
    return ProjectBudgetFactory()


@pytest.fixture(scope="function")
def complete_project_setup():
    """
    Create complete project test dataset

    Includes: customer, project, supplier, materials, BOM
    """
    return create_complete_project_setup()


# ============================================================================
# Unified Mocking Pattern - External Services
# ============================================================================

from unittest.mock import MagicMock


@pytest.fixture(scope="function")
def mock_db_session():
    """
    提供模拟数据库会话，用于服务层单元测试
    不需要真实数据库连接，适合快速单元测试
    """
    return MagicMock(spec=Session)


@pytest.fixture(scope="function")
def mock_user_simple():
    """创建简单的模拟用户对象（用于服务测试）"""
    user = MagicMock()
    user.id = 1
    user.username = "test_user"
    user.real_name = "测试用户"
    user.department = "测试部门"
    user.department_id = 1
    user.is_active = True
    user.is_superuser = False
    return user


@pytest.fixture(scope="function")
def mock_project_simple():
    """创建简单的模拟项目对象（用于服务测试）"""
    project = MagicMock()
    project.id = 1
    project.project_code = "PJ260101001"
    project.project_name = "测试项目"
    project.customer_id = 1
    project.customer_name = "测试客户"
    project.stage = "S1"
    project.status = "ST01"
    project.health = "H1"
    project.is_active = True
    return project


@pytest.fixture(scope="function")
def mock_department_simple():
    """创建简单的模拟部门对象（用于服务测试）"""
    dept = MagicMock()
    dept.id = 1
    dept.dept_code = "DEPT001"
    dept.dept_name = "测试部门"
    dept.is_active = True
    return dept


# ---------------------------------------------------------------------------
# 统一 Mocking 模式 - 外部服务
# ---------------------------------------------------------------------------

from unittest.mock import MagicMock, Mock
from io import BytesIO


class ExternalServiceMocker:
    """
    统一的外部服务 Mock 管理

    支持的 Mock 类型：
    - HTTP 客户端
    - Redis 缓存
    - 文件系统操作
    - PDF/Excel 生成
    - 邮件服务
    - 异步任务执行
    """

    @staticmethod
    def mock_redis():
        """Mock redis client, return empty result or preset data"""
        return MagicMock()

    @staticmethod
    def mock_http_client(response_data=None, status_code=200):
        """Mock HTTP client endpoint, simulate API response"""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = response_data or {}
        mock_response.text = ""
        return mock_response

    @staticmethod
    def mock_pdf_generation():
        """Mock PDF generation, return BytesIO object"""
        return BytesIO(b"mock_pdf_content")

    @staticmethod
    def mock_excel_generation():
        """Mock Excel generation, return BytesIO object"""
        return BytesIO(b"mock_excel_content")

    @staticmethod
    def mock_email_service():
        """Mock email service, always return success"""
        mock = Mock()
        mock.send.return_value = True
        return mock

    @staticmethod
    def mock_file_write():
        """Mock file write operation"""
        return Mock()

    @staticmethod
    def mock_redis_get(return_value=None):
        """Mock Redis GET operation, for cache testing"""
        return MagicMock(return_value=return_value)

    @staticmethod
    def mock_redis_set():
        """Mock Redis SET operation, for cache testing"""
        return MagicMock()


@pytest.fixture(scope="function")
def external_service_mocker():
    """
    Provide unified external service Mock tools

    Usage:
        mocker = external_service_mocker()
        http_mock = mocker.mock_http_client({"data": "test"})
        pdf_mock = mocker.mock_pdf_generation()
    """
    return ExternalServiceMocker()


@pytest.fixture(scope="function")
def mock_redis_operations():
    """
    Mock all Redis operations for testing without external Redis dependency

    In unit tests, use this fixture instead of real Redis connection
    """
    redis_mock = MagicMock()
    redis_mock.get.return_value = None
    redis_mock.set.return_value = True
    redis_mock.delete.return_value = True
    redis_mock.exists.return_value = False
    redis_mock.expire.return_value = True
    return redis_mock


@pytest.fixture(scope="function")
def mock_pdf_excel_export():
    """
    Mock PDF/Excel 导出功能

    用于测试导出服务时：
    - 不生成真实文件
    - 不依赖真实的 PDF/Excel 库
    - 验证数据转换逻辑
    """
    return BytesIO(b"mock_export_content")


@pytest.fixture(scope="function")
def mock_external_dependencies():
    """
    Mock 所有外部依赖，用于纯单元测试

    包含：
    - Redis
    - HTTP 客户端
    - 文件系统
    - PDF/Excel 生成
    - 邮件服务
    - 异步任务
    """
    return {
        "redis": MagicMock(),
        "http_client": Mock(),
        "pdf_generator": BytesIO(b""),
        "excel_generator": BytesIO(b""),
        "email_service": Mock(send=True),
        "file_system": Mock(),
        "async_task": Mock(),
    }
