# 开发者指南

> 非标自动化测试设备项目管理系统 — 多租户开发规范  
> 版本: 1.0 | 更新时间: 2026-02-17 | 读者对象: 后端开发工程师

---

## 目录

1. [开发规范](#1-开发规范)
2. [中间件工作原理](#2-中间件工作原理)
3. [装饰器使用指南](#3-装饰器使用指南)
4. [测试多租户场景](#4-测试多租户场景)
5. [常见错误与避坑指南](#5-常见错误与避坑指南)
6. [代码审查检查清单](#6-代码审查检查清单)

---

## 1. 开发规范

### 1.1 核心原则：所有查询必须过滤 tenant_id

在多租户系统中，**最重要的开发规范**是：
> 任何读取业务数据的查询，都必须确保 `tenant_id` 被正确过滤。

系统通过 `TenantQuery` 自动处理绝大多数情况，但开发者仍需理解并遵守以下规范。

### 1.2 ✅ 正确的查询写法

**方式一：标准 ORM 查询（推荐，自动过滤）**

```python
# app/api/v1/endpoints/projects.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.security import get_current_active_user
from app.models.project import Project
from app.models.user import User

router = APIRouter()

@router.get("/projects")
async def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # ✅ TenantQuery 会自动添加 WHERE tenant_id = ? 条件
    projects = db.query(Project).filter(Project.status == "ACTIVE").all()
    return projects
```

**方式二：使用 TenantAwareQuery 工具类**

```python
from app.core.middleware.tenant_middleware import TenantAwareQuery

@router.get("/projects")
async def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # 显式指定租户感知查询
    tenant_query = TenantAwareQuery(db)
    projects = tenant_query.query(Project).filter(
        Project.status == "ACTIVE"
    ).all()
    return projects
```

**方式三：在服务层使用（标准分层架构）**

```python
# app/services/project_service.py
from sqlalchemy.orm import Session
from app.models.project import Project

class ProjectService:
    def __init__(self, db: Session):
        self.db = db  # TenantQuery 在查询时自动生效

    def get_active_projects(self, page: int = 1, page_size: int = 20):
        """获取当前租户的活跃项目（自动过滤）"""
        offset = (page - 1) * page_size
        return (
            self.db.query(Project)
            .filter(Project.status == "ACTIVE")
            .offset(offset)
            .limit(page_size)
            .all()
        )

    def get_project_by_id(self, project_id: int) -> Project | None:
        """获取项目详情（自动确保只返回本租户数据）"""
        return (
            self.db.query(Project)
            .filter(Project.id == project_id)
            .first()
        )
```

### 1.3 ❌ 禁止的写法

**禁止手动执行原始 SQL（容易遗漏 tenant_id 过滤）：**

```python
# ❌ 错误：直接执行原始 SQL，没有租户过滤
result = db.execute("SELECT * FROM projects WHERE status = 'ACTIVE'")

# ✅ 正确：如果必须用 SQL，一定要加 tenant_id 过滤
from app.core.middleware.tenant_middleware import get_current_tenant_id
tenant_id = get_current_tenant_id()
result = db.execute(
    "SELECT * FROM projects WHERE status = 'ACTIVE' AND tenant_id = :tid",
    {"tid": tenant_id}
)
```

**禁止跳过租户过滤（除非明确有权限）：**

```python
# ❌ 危险：跳过租户过滤，返回所有租户的数据
query = db.query(Project)
query._skip_tenant_filter = True  # 只允许超级管理员相关逻辑使用
all_projects = query.all()

# ✅ 正确：如果需要跨租户查询，必须先验证超级管理员身份
from app.core.auth import is_superuser

if not is_superuser(current_user):
    raise HTTPException(status_code=403, detail="需要超级管理员权限")

query = db.query(Project)
query._skip_tenant_filter = True
all_projects = query.all()
```

### 1.4 新建模型的规范

**所有新建的业务模型，都必须包含 `tenant_id` 字段：**

```python
# app/models/custom_module.py
from sqlalchemy import Column, Integer, String, ForeignKey
from app.models.base import Base, TimestampMixin

class EquipmentRecord(Base, TimestampMixin):
    """设备记录表 - 多租户业务模型示例"""
    __tablename__ = "equipment_records"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # ✅ 必须包含 tenant_id 字段
    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id"),
        nullable=False,              # 不允许为空
        index=True,                  # 必须建索引
        comment="租户ID"
    )

    # 业务字段
    equipment_name = Column(String(200), nullable=False, comment="设备名称")
    serial_number  = Column(String(100), comment="序列号")
    status         = Column(String(20), default="NORMAL", comment="状态")
```

**对应的 Alembic 迁移文件示例：**

```python
# migrations/versions/xxxx_add_equipment_records.py
def upgrade():
    op.create_table(
        'equipment_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),  # 必须
        sa.Column('equipment_name', sa.String(200), nullable=False),
        sa.Column('serial_number', sa.String(100)),
        sa.Column('status', sa.String(20), server_default='NORMAL'),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    # ✅ 必须为 tenant_id 建索引
    op.create_index('idx_equipment_records_tenant_id',
                    'equipment_records', ['tenant_id'])
```

---

## 2. 中间件工作原理

### 2.1 完整请求处理链路

```
HTTP Request（含 Authorization: Bearer <token>）
        │
        ▼
GlobalAuthMiddleware（认证中间件）
        │  1. 解析 JWT Token
        │  2. 查询数据库验证用户
        │  3. request.state.user = User(id=42, tenant_id=1)
        │
        ▼
TenantContextMiddleware（租户上下文中间件）
        │  4. 从 request.state.user 提取 tenant_id
        │  5. 调用 set_current_tenant_id(1)
        │  6. 存入 ContextVar[current_tenant_id] = 1
        │
        ▼
FastAPI 路由处理（API Endpoint）
        │  7. 执行业务逻辑
        │  8. db.query(Project).filter(...)
        │
        ▼
TenantQuery.__iter__()（查询拦截）
        │  9.  调用 get_current_tenant_id() → 1
        │  10. 检查 Project 模型是否有 tenant_id 字段 → 是
        │  11. 自动添加 filter(Project.tenant_id == 1)
        │  12. 执行最终 SQL: SELECT * FROM projects WHERE tenant_id=1 AND ...
        │
        ▼
Response（返回租户 1 的数据）
        │
finally: TenantContextMiddleware 清理上下文
        set_current_tenant_id(None)
```

### 2.2 ContextVar 实现细节

`ContextVar` 是 Python 3.7+ 内置模块，天然支持 asyncio 异步并发，每个异步任务（协程）都有独立的上下文，不会相互干扰：

```python
# app/core/middleware/tenant_middleware.py
from contextvars import ContextVar
from typing import Optional

# 每个异步请求有独立的 context，不会混串
_current_tenant_id: ContextVar[Optional[int]] = ContextVar(
    "current_tenant_id",
    default=None
)

# 请求处理期间：ContextVar = 1（租户A的请求）
# 并发请求B：ContextVar = 2（租户B的请求，独立不干扰）
```

### 2.3 TenantQuery 核心逻辑

```python
# app/core/database/tenant_query.py
class TenantQuery(Query):
    """继承 SQLAlchemy Query，在迭代时自动注入租户过滤"""

    def __iter__(self):
        """所有遍历操作（.all(), .first(), .count() 等）都会触发此方法"""
        if getattr(self, '_skip_tenant_filter', False):
            return super().__iter__()
        return self._apply_tenant_filter().__iter__()

    def _apply_tenant_filter(self):
        tenant_id = get_current_tenant_id()
        model = self.column_descriptions[0].get('type')

        if not hasattr(model, 'tenant_id'):
            # 系统级表（如 tenants, role_templates）不需要过滤
            return self

        if tenant_id is None:
            # tenant_id=None 的情况：只有超级管理员合法
            # 验证逻辑在 auth.py 的 is_superuser() 中处理
            return self

        # 普通租户用户：自动添加过滤
        return self.filter(model.tenant_id == tenant_id)
```

### 2.4 Session 配置

需要确认 `get_session_factory()` 使用了 `TenantQuery` 类：

```python
# app/models/base.py
from sqlalchemy.orm import sessionmaker
from app.core.database.tenant_query import TenantQuery

def get_session_factory(engine):
    return sessionmaker(
        bind=engine,
        query_cls=TenantQuery,   # ✅ 关键：使用自定义 Query 类
        autocommit=False,
        autoflush=False,
    )
```

---

## 3. 装饰器使用指南

### 3.1 @require_tenant_isolation

用于**普通业务 API**，强制执行租户隔离：

```python
# app/api/v1/endpoints/projects.py
from app.core.decorators.tenant_isolation import require_tenant_isolation

@router.get("/projects/{project_id}")
@require_tenant_isolation
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """装饰器确保：
    1. 用户已认证
    2. db.info['tenant_id'] 已设置
    3. 后续查询自动过滤 tenant_id
    """
    service = ProjectService(db)
    project = service.get_project_by_id(project_id)

    if project is None:
        raise HTTPException(status_code=404, detail="项目不存在或无权访问")

    return project
```

### 3.2 @allow_cross_tenant

用于**系统管理 API**（仅超级管理员可用），允许跨租户访问：

```python
# app/api/v1/endpoints/tenants.py
from app.core.decorators.tenant_isolation import allow_cross_tenant

@router.get("/tenants/{tenant_id}/stats")
@allow_cross_tenant
async def get_tenant_stats(
    tenant_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)  # 超级管理员专用依赖
):
    """
    超级管理员查看任意租户的统计数据
    装饰器允许跨租户访问，不添加 tenant_id 过滤
    """
    pass
```

### 3.3 tenant_resource_check

在访问具体资源时，验证资源是否属于当前租户：

```python
# app/services/project_service.py
from app.core.permissions.tenant_access import check_tenant_access
from app.core.auth import is_superuser

def update_project(
    self,
    project_id: int,
    update_data: dict,
    current_user: User
) -> Project:
    """更新项目（带租户权限检查）"""
    # 获取原始数据（此处 TenantQuery 已自动过滤，找不到就是不存在）
    project = self.db.query(Project).filter(Project.id == project_id).first()

    if project is None:
        raise ValueError("项目不存在或无权访问")

    # 额外的权限检查（双重保障）
    if not is_superuser(current_user):
        if project.tenant_id != current_user.tenant_id:
            # 这种情况在 TenantQuery 正常工作时不应该发生
            # 但作为防御性编程，明确抛出异常
            raise PermissionError("无权修改其他租户的项目")

    # 执行更新
    for key, value in update_data.items():
        setattr(project, key, value)
    self.db.commit()
    return project
```

---

## 4. 测试多租户场景

### 4.1 测试环境配置

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.core.database.tenant_query import TenantQuery

@pytest.fixture(scope="function")
def db_session():
    """创建测试用数据库会话（使用内存 SQLite）"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(engine)

    # ✅ 测试也必须使用 TenantQuery
    TestSessionLocal = sessionmaker(
        bind=engine,
        query_cls=TenantQuery,
        autocommit=False,
        autoflush=False,
    )
    session = TestSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(engine)
```

### 4.2 创建测试租户和用户

```python
# tests/fixtures/tenant_fixtures.py
from app.models.tenant import Tenant, TenantStatus
from app.models.user import User

def create_test_tenant(db, tenant_id: int, tenant_name: str) -> Tenant:
    """创建测试租户"""
    tenant = Tenant(
        id=tenant_id,
        tenant_code=f"TEST-{tenant_id:03d}",
        tenant_name=tenant_name,
        status=TenantStatus.ACTIVE.value,
        plan_type="STANDARD",
        max_users=50,
    )
    db.add(tenant)
    db.commit()
    return tenant

def create_test_user(
    db,
    user_id: int,
    tenant_id: int,
    username: str = None,
    is_superuser: bool = False
) -> User:
    """创建测试用户"""
    user = User(
        id=user_id,
        username=username or f"user_{user_id}",
        tenant_id=None if is_superuser else tenant_id,  # 超级管理员 tenant_id=None
        is_superuser=is_superuser,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user
```

### 4.3 模拟租户上下文

```python
# tests/security/test_tenant_isolation.py
import pytest
from unittest.mock import patch
from app.core.middleware.tenant_middleware import set_current_tenant_id
from app.models.project import Project

class TestTenantIsolation:
    """测试租户数据隔离"""

    def setup_method(self):
        """每个测试前的准备工作"""
        # 重置租户上下文
        set_current_tenant_id(None)

    def test_user_cannot_access_other_tenant_project(self, db_session):
        """验证用户无法访问其他租户的项目"""
        # 创建两个租户
        tenant_a = create_test_tenant(db_session, 1, "租户A")
        tenant_b = create_test_tenant(db_session, 2, "租户B")

        # 在租户B下创建项目（绕过自动过滤，直接插入）
        set_current_tenant_id(None)  # 暂时清空
        project_b = Project(
            tenant_id=2,
            name="租户B的项目",
            status="ACTIVE"
        )
        db_session.add(project_b)
        db_session.commit()

        # 模拟租户A的用户在查询
        set_current_tenant_id(1)  # 设置为租户A

        # 查询所有项目
        projects = db_session.query(Project).all()

        # 验证：不应该看到租户B的项目
        project_names = [p.name for p in projects]
        assert "租户B的项目" not in project_names, "租户隔离失败：看到了其他租户的数据"

    def test_user_can_only_see_own_tenant_data(self, db_session):
        """验证用户只能看到自己租户的数据"""
        # 为租户1和租户2各创建项目
        for tenant_id in [1, 2]:
            set_current_tenant_id(None)  # 直接插入，绕过过滤
            project = Project(
                tenant_id=tenant_id,
                name=f"租户{tenant_id}的项目",
                status="ACTIVE"
            )
            db_session.add(project)
        db_session.commit()

        # 切换到租户1查询
        set_current_tenant_id(1)
        projects = db_session.query(Project).all()

        # 验证：只看到租户1的项目
        assert len(projects) == 1
        assert projects[0].tenant_id == 1

    def test_superuser_can_see_all_tenant_data(self, db_session):
        """验证超级管理员可以看到所有租户数据"""
        # 为不同租户插入数据
        for tenant_id in [1, 2, 3]:
            set_current_tenant_id(None)
            project = Project(
                tenant_id=tenant_id,
                name=f"租户{tenant_id}的项目"
            )
            db_session.add(project)
        db_session.commit()

        # 超级管理员：tenant_id=None
        set_current_tenant_id(None)

        # 跳过过滤查询所有数据（超级管理员特权）
        query = db_session.query(Project)
        query._skip_tenant_filter = True
        all_projects = query.all()

        # 验证：可以看到所有租户的数据
        assert len(all_projects) == 3
```

### 4.4 API 级别的集成测试

```python
# tests/api/test_tenant_api.py
from fastapi.testclient import TestClient
from unittest.mock import patch

def test_list_projects_only_returns_own_tenant(client: TestClient, auth_headers: dict):
    """
    集成测试：通过 API 验证租户隔离
    auth_headers 包含租户A用户的 JWT Token
    """
    # 调用项目列表 API
    response = client.get("/api/v1/projects/", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()["data"]

    # 验证所有返回的项目都属于当前租户
    for project in data["items"]:
        assert project["tenant_id"] == 1, f"项目 {project['id']} 不属于当前租户"
```

### 4.5 测试运行命令

```bash
# 运行所有租户隔离测试
pytest tests/security/ -v --tb=short

# 运行特定测试
pytest tests/security/test_tenant_isolation.py -v

# 带覆盖率报告
pytest tests/security/ --cov=app/core/middleware --cov=app/core/database \
    --cov-report=html:coverage_report

# 并发测试（验证 ContextVar 线程安全）
pytest tests/security/ -n 4  # 4 个并发进程
```

---

## 5. 常见错误与避坑指南

### 5.1 ❌ 错误1：忘记过滤 tenant_id 的后果

```python
# ❌ 危险：如果 TenantQuery 因配置问题未生效，此代码会泄露所有租户数据
projects = db.execute("SELECT * FROM projects").fetchall()

# 后果：
# - 租户A的用户可以看到租户B的商业数据
# - 可能涉及商业机密泄露，面临法律风险
# - 严重情况下导致客户流失和声誉损害
```

**如何检测：** 在代码审查阶段，使用以下脚本扫描潜在风险：

```bash
# 查找所有直接执行 SQL 字符串的地方
grep -rn "db.execute.*SELECT" app/ --include="*.py" | \
  grep -v "tenant_id"  # 过滤掉已包含 tenant_id 的安全查询
```

### 5.2 ❌ 错误2：在后台任务中忘记设置租户上下文

```python
# ❌ 错误：后台任务中没有请求上下文，ContextVar 默认为 None
from fastapi import BackgroundTasks

@router.post("/projects/{id}/export")
async def export_project(
    project_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    # 启动后台任务
    background_tasks.add_task(do_export, project_id)  # ❌ 没有传递 tenant_id

async def do_export(project_id: int):
    # 此时 ContextVar 已被清理，get_current_tenant_id() 返回 None
    # 如果用户不是超级管理员，TenantQuery 会报错
    project = db.query(Project).filter(Project.id == project_id).first()
```

```python
# ✅ 正确：显式传递 tenant_id 给后台任务
@router.post("/projects/{id}/export")
async def export_project(
    project_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user)
):
    tenant_id = current_user.tenant_id  # 在请求上下文中捕获

    # 将 tenant_id 作为参数传递
    background_tasks.add_task(do_export, project_id, tenant_id)

async def do_export(project_id: int, tenant_id: int):
    # 在后台任务中手动设置租户上下文
    set_current_tenant_id(tenant_id)
    try:
        async with get_db_session() as db:
            project = db.query(Project).filter(Project.id == project_id).first()
            # 执行导出逻辑
    finally:
        set_current_tenant_id(None)  # 清理
```

### 5.3 ❌ 错误3：在新租户创建数据时没有设置 tenant_id

```python
# ❌ 错误：创建数据时没有设置 tenant_id
def create_project(self, project_data: dict) -> Project:
    project = Project(**project_data)  # 如果 project_data 没有 tenant_id
    self.db.add(project)
    self.db.commit()
    return project
```

```python
# ✅ 正确：确保 tenant_id 从当前用户或上下文获取
def create_project(
    self,
    project_data: dict,
    current_user: User
) -> Project:
    # 显式设置 tenant_id，不依赖调用方传入
    project = Project(
        **project_data,
        tenant_id=current_user.tenant_id  # 从当前登录用户获取
    )
    self.db.add(project)
    self.db.commit()
    return project
```

### 5.4 ❌ 错误4：跨租户关联查询

```python
# ❌ 错误：JOIN 查询时没有考虑租户过滤
def get_project_with_tasks(self, project_id: int):
    # 如果 Task 也有 tenant_id，JOIN 后需要两个表都过滤
    result = self.db.query(Project, Task).join(
        Task, Task.project_id == Project.id
    ).filter(Project.id == project_id).all()
    # ⚠️ 此处 TenantQuery 只对第一个实体（Project）过滤
    # Task 的 tenant_id 没有被自动过滤
```

```python
# ✅ 正确：JOIN 查询时显式过滤所有涉及的租户表
def get_project_with_tasks(self, project_id: int):
    tenant_id = get_current_tenant_id()

    result = self.db.query(Project, Task).join(
        Task, Task.project_id == Project.id
    ).filter(
        Project.id == project_id,
        Task.tenant_id == tenant_id  # 显式过滤 Task 的租户
    ).all()
    return result
```

### 5.5 ❌ 错误5：超级管理员误操作影响所有租户

```python
# ❌ 危险：超级管理员在没有指定租户的情况下批量更新
@router.put("/admin/projects/bulk-update")
async def bulk_update_projects(
    update_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    # 超级管理员的 TenantQuery 不过滤，会更新所有租户的项目！
    db.query(Project).filter(
        Project.status == "DRAFT"
    ).update(update_data)
    db.commit()
```

```python
# ✅ 正确：超级管理员操作时必须明确指定 tenant_id
@router.put("/admin/projects/bulk-update")
async def bulk_update_projects(
    tenant_id: int,      # 必须明确指定要操作的租户
    update_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_super_admin)
):
    db.query(Project).filter(
        Project.tenant_id == tenant_id,  # 明确指定租户
        Project.status == "DRAFT"
    ).update(update_data)
    db.commit()
```

---

## 6. 代码审查检查清单

在提交涉及数据查询的代码时，请逐项确认：

### 新增模型

- [ ] 模型包含 `tenant_id` 字段（`Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)`）
- [ ] Alembic 迁移文件包含 `idx_tenant_id` 索引

### 新增查询

- [ ] 使用 `db.query(Model)` ORM 方式（优先，自动过滤）
- [ ] 如果使用原始 SQL，已手动添加 `AND tenant_id = :tid`
- [ ] JOIN 查询中，所有含 `tenant_id` 的关联表都已过滤

### 新增 API

- [ ] 业务 API 使用了 `@require_tenant_isolation` 或 `Depends(get_current_active_user)`
- [ ] 管理员 API 使用了 `Depends(require_super_admin)`
- [ ] 创建资源时，从 `current_user.tenant_id` 获取租户ID

### 后台任务/异步代码

- [ ] 已将 `tenant_id` 作为参数传入任务函数
- [ ] 任务函数内调用了 `set_current_tenant_id(tenant_id)` 并在 `finally` 清理

### 测试

- [ ] 新功能包含多租户隔离测试（至少验证 A 租户无法读到 B 租户数据）
- [ ] 测试使用了 `TenantQuery` 配置的 Session

---

## 相关文档

- [README.md](./README.md) — 多租户架构总览
- [DEPLOYMENT.md](./DEPLOYMENT.md) — 生产部署指南
- [ADMIN_GUIDE.md](./ADMIN_GUIDE.md) — 系统管理员操作手册
- [../租户过滤实现原理.md](../租户过滤实现原理.md) — TenantQuery 技术细节
- [../租户隔离测试指南.md](../租户隔离测试指南.md) — 测试用例完整说明
