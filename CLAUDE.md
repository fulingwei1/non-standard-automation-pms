# CLAUDE.md - AI 助手开发指南（非标自动化项目管理系统）

## 项目概述

这是一个**非标自动化项目管理系统**，专为定制自动化设备制造企业设计，适用于：

- ICT/FCT/EOL 测试设备
- 烧录设备、老化设备
- 视觉检测设备
- 自动化组装线体

系统管理从签单到售后的完整项目生命周期。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI |
| ORM | SQLAlchemy 2.0 |
| 数据库 | SQLite（开发环境）/ MySQL（生产环境）|
| 数据验证 | Pydantic 2.x / pydantic-settings |
| 身份认证 | JWT (python-jose) |
| 密码加密 | passlib + bcrypt |
| 速率限制 | slowapi |
| 任务调度 | APScheduler |
| 文档处理 | python-docx, PyPDF2, reportlab |
| HTTP 客户端 | httpx |
| ASGI 服务器 | Uvicorn |

## 项目结构

```
non-standard-automation-pms/
├── app/                              # 主应用程序包
│   ├── __init__.py
│   ├── main.py                       # FastAPI 应用入口
│   ├── scheduler_progress.py         # 进度追踪定时任务
│   ├── api/                          # API 路由层
│   │   ├── deps.py                   # 依赖注入 (get_db, get_current_user)
│   │   └── v1/
│   │       ├── api.py                # API 路由聚合
│   │       ├── core/                 # 核心 CRUD 基类
│   │       └── endpoints/            # API 端点模块 (50+ 模块)
│   │           ├── acceptance/       # 验收管理
│   │           ├── alerts/           # 预警管理
│   │           ├── approvals/        # 审批流程
│   │           ├── assembly_kit/     # 装配套件
│   │           ├── auth.py           # 认证端点
│   │           ├── bom/              # 物料清单
│   │           ├── bonus/            # 奖金管理
│   │           ├── budget/           # 预算管理
│   │           ├── customers/        # 客户管理
│   │           ├── documents/        # 文档管理
│   │           ├── ecn/              # 工程变更通知
│   │           ├── engineer_performance/  # 工程师绩效
│   │           ├── issues/           # 问题管理
│   │           ├── machines/         # 机台管理
│   │           ├── management_rhythm/ # 管理节奏
│   │           ├── materials/        # 物料管理
│   │           ├── notifications/    # 通知管理
│   │           ├── organization/     # 组织架构
│   │           ├── outsourcing/      # 外协管理
│   │           ├── performance/      # 绩效管理
│   │           ├── permissions/      # 权限管理
│   │           ├── pitfalls/         # 踩坑记录
│   │           ├── presales/         # 售前管理
│   │           ├── projects/         # 项目管理（核心模块）
│   │           │   ├── core.py       # 项目 CRUD
│   │           │   ├── stages/       # 阶段管理
│   │           │   ├── milestones/   # 里程碑管理
│   │           │   ├── machines/     # 机台管理
│   │           │   ├── members/      # 团队成员
│   │           │   ├── roles/        # 项目角色
│   │           │   ├── costs/        # 成本管理
│   │           │   ├── progress/     # 进度管理
│   │           │   ├── work_logs/    # 工作日志
│   │           │   ├── evaluations/  # 项目评价
│   │           │   ├── timesheet/    # 工时管理
│   │           │   ├── workload/     # 工作量管理
│   │           │   └── resource_plan/ # 资源计划
│   │           ├── purchase/         # 采购管理
│   │           ├── qualifications/   # 资质管理
│   │           ├── reports/          # 报表管理
│   │           ├── sales/            # 销售管理
│   │           ├── shortage/         # 短缺管理
│   │           ├── timesheet/        # 工时管理
│   │           └── users/            # 用户管理
│   ├── core/                         # 核心配置
│   │   ├── config.py                 # 应用配置 (pydantic-settings)
│   │   ├── auth.py                   # JWT 认证、权限检查
│   │   ├── security.py               # 安全导出层
│   │   ├── csrf.py                   # CSRF 防护
│   │   ├── rate_limit.py             # 速率限制
│   │   ├── security_headers.py       # 安全 HTTP 头
│   │   ├── logging_config.py         # 日志配置
│   │   ├── exception_handlers.py     # 异常处理器
│   │   ├── middleware/               # 中间件
│   │   │   ├── auth_middleware.py    # 全局认证中间件
│   │   │   └── tenant_middleware.py  # 租户上下文中间件
│   │   ├── permissions/              # 权限相关
│   │   │   └── timesheet.py          # 工时审批业务逻辑
│   │   ├── schemas/                  # 核心数据模式
│   │   └── state_machine/            # 状态机引擎
│   │       ├── base.py               # 基础状态机类
│   │       ├── decorators.py         # 状态机装饰器
│   │       ├── exceptions.py         # 状态机异常
│   │       ├── notifications.py      # 状态变更通知
│   │       ├── permissions.py        # 状态机权限检查
│   │       ├── acceptance.py         # 验收状态机
│   │       ├── ecn.py                # ECN 状态机
│   │       ├── issue.py              # 问题状态机
│   │       ├── milestone.py          # 里程碑状态机
│   │       ├── opportunity.py        # 商机状态机
│   │       ├── quote.py              # 报价状态机
│   │       └── installation_dispatch.py  # 安装派遣状态机
│   ├── models/                       # SQLAlchemy ORM 模型
│   │   ├── base.py                   # 基础模型、引擎、会话管理
│   │   ├── __init__.py               # 模型导出（重要！）
│   │   ├── enums.py                  # 基础枚举定义
│   │   ├── enums/                    # 分类枚举目录
│   │   ├── user.py                   # 用户、角色模型
│   │   ├── permission.py             # 权限模型 (ApiPermission, RoleApiPermission)
│   │   ├── project.py                # 项目模型导出
│   │   ├── project/                  # 项目相关模型目录
│   │   ├── material.py               # 物料、BOM、供应商模型
│   │   ├── purchase.py               # 采购订单模型
│   │   ├── ecn/                      # ECN 相关模型目录
│   │   ├── acceptance.py             # 验收管理模型
│   │   ├── outsourcing.py            # 外协供应商/订单模型
│   │   ├── alert.py                  # 预警和异常模型
│   │   ├── organization.py           # 部门组织模型
│   │   ├── approval/                 # 审批相关模型
│   │   ├── bonus.py                  # 奖金模型
│   │   ├── budget.py                 # 预算模型
│   │   ├── finance.py                # 财务模型
│   │   ├── presale.py                # 售前模型
│   │   ├── sales/                    # 销售相关模型
│   │   ├── timesheet.py              # 工时模型
│   │   ├── task_center.py            # 任务中心模型
│   │   └── ...                       # 其他业务模型
│   ├── services/                     # 业务服务层 (150+ 服务)
│   │   ├── permission_service.py     # 权限服务 (核心)
│   │   ├── permission_cache_service.py # 权限缓存服务
│   │   ├── notification_service.py   # 通知服务
│   │   ├── unified_notification_service.py  # 统一通知服务
│   │   ├── approval_engine/          # 统一审批引擎
│   │   ├── alert_rule_engine/        # 预警规则引擎
│   │   ├── status_handlers/          # 状态流转处理器
│   │   ├── health_calculator.py      # 项目健康度计算
│   │   ├── progress_aggregation_service.py  # 进度聚合服务
│   │   ├── stage_advance_service.py  # 阶段推进服务
│   │   └── ...                       # 其他业务服务
│   ├── schemas/                      # Pydantic 数据模式
│   │   ├── common.py                 # 通用响应模式
│   │   ├── auth.py                   # 认证模式
│   │   ├── project.py                # 项目模式
│   │   └── ...                       # 其他业务模式
│   ├── utils/                        # 工具函数
│   │   ├── scheduler.py              # 定时任务调度器
│   │   ├── init_data.py              # 基础数据初始化
│   │   ├── number_generator.py       # 编号生成器
│   │   └── ...                       # 其他工具
│   ├── common/                       # 公共模块
│   ├── middleware/                   # 应用中间件
│   │   └── audit.py                  # 审计日志中间件
│   ├── report_configs/               # 报表配置
│   └── templates/                    # 模板文件
├── tests/                            # 测试目录
│   ├── conftest.py                   # pytest 配置和 fixtures
│   ├── factories.py                  # 测试数据工厂
│   ├── unit/                         # 单元测试 (280+ 测试文件)
│   ├── integration/                  # 集成测试
│   ├── api/                          # API 测试
│   ├── e2e/                          # 端到端测试
│   ├── performance/                  # 性能测试
│   └── scripts/                      # 测试脚本
├── scripts/                          # 运维脚本
│   ├── create_admin.py               # 创建管理员
│   ├── create_demo_data.py           # 创建演示数据
│   ├── init_db.py                    # 数据库初始化
│   ├── coverage_analysis.py          # 覆盖率分析
│   └── ...                           # 其他脚本
├── migrations/                       # SQL 迁移文件
├── data/                             # SQLite 数据库存储
├── docs/                             # 项目文档
├── frontend/                         # 前端代码
├── templates/                        # HTML 模板
├── reports/                          # 生成的报告
├── monitoring/                       # 监控配置
├── requirements.txt                  # Python 依赖
├── pytest.ini                        # pytest 配置
├── Dockerfile                        # Docker 配置
├── docker-compose.yml                # Docker Compose 配置
└── *.md                              # 各类文档和报告
```

## 核心业务模块

### 1. 项目管理

- **模型**: `Project`, `Machine`, `ProjectStage`, `ProjectStatus`, `ProjectMilestone`, `ProjectMember`, `ProjectCost`, `ProjectDocument`
- 项目遵循 9 阶段生命周期 (S1-S9)：
  - S1: 需求进入
  - S2: 方案设计
  - S3: 采购备料
  - S4: 加工制造
  - S5: 装配调试
  - S6: 出厂验收 (FAT)
  - S7: 包装发运
  - S8: 现场安装 (SAT)
  - S9: 质保结项

### 2. 健康度状态

- H1: 正常（绿色）
- H2: 有风险（黄色）
- H3: 阻塞（红色）
- H4: 已完结（灰色）

### 3. 采购与物料

- **模型**: `Material`, `MaterialCategory`, `Supplier`, `BomHeader`, `BomItem`, `PurchaseOrder`, `PurchaseOrderItem`, `GoodsReceipt`
- 物料类型：标准件、机械件、电气件、气动件等

### 4. 工程变更通知 (ECN)

- **模型**: `Ecn`, `EcnEvaluation`, `EcnApproval`, `EcnTask`, `EcnAffectedMaterial`
- 变更类型：设计变更、物料变更、工艺变更、规格变更、计划变更
- 使用状态机管理流程 (`app/core/state_machine/ecn.py`)

### 5. 验收管理

- **模型**: `AcceptanceTemplate`, `AcceptanceOrder`, `AcceptanceOrderItem`, `AcceptanceIssue`
- 类型：FAT（出厂验收）、SAT（现场验收）、终验收
- 使用状态机管理流程 (`app/core/state_machine/acceptance.py`)

### 6. 外协管理

- **模型**: `OutsourcingVendor`, `OutsourcingOrder`, `OutsourcingDelivery`, `OutsourcingInspection`

### 7. 预警与异常

- **模型**: `AlertRule`, `AlertRecord`, `ExceptionEvent`, `AlertStatistics`, `ProjectHealthSnapshot`
- 预警级别：提示、警告、严重、紧急
- 规则引擎：`app/services/alert_rule_engine/`

### 8. 统一审批引擎

- **位置**: `app/services/approval_engine/`
- 支持多种业务类型的审批流程
- 适配器模式实现业务解耦

## 状态机架构

系统使用统一的状态机框架管理业务流程：

### 核心组件 (`app/core/state_machine/`)

| 文件 | 描述 |
|------|------|
| `base.py` | 基础状态机类，定义状态、转换、钩子 |
| `decorators.py` | 状态机装饰器 |
| `exceptions.py` | 状态机异常定义 |
| `notifications.py` | 状态变更通知 |
| `permissions.py` | 状态机权限检查 |

### 业务状态机

| 状态机 | 业务 | 状态 |
|--------|------|------|
| `ecn.py` | ECN 变更 | draft → pending_evaluation → evaluating → pending_approval → ... |
| `acceptance.py` | 验收 | draft → submitted → testing → ... |
| `issue.py` | 问题 | open → in_progress → resolved → closed |
| `milestone.py` | 里程碑 | pending → in_progress → completed |
| `opportunity.py` | 商机 | lead → qualified → proposal → ... |
| `quote.py` | 报价 | draft → submitted → approved → ... |

## 开发命令

### 环境搭建

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python3 init_db.py

# 或使用脚本
python3 scripts/init_db.py
```

### 运行应用

```bash
# 使用 uvicorn 直接运行（开发模式）
uvicorn app.main:app --reload

# 或使用 Python 模块方式
python3 -m app.main

# 使用启动脚本
./start.sh

# 禁用调度器启动
ENABLE_SCHEDULER=false uvicorn app.main:app --reload
```

### 测试命令

```bash
# 运行所有测试（带覆盖率）
pytest

# 运行单元测试
pytest tests/unit/

# 运行特定测试文件
pytest tests/unit/test_auth.py

# 运行特定测试
pytest tests/unit/test_auth.py::test_login -v

# 跳过慢测试
pytest -m "not slow"

# 运行 API 测试
pytest -m api

# 不带覆盖率运行（更快）
pytest -c pytest_no_cov.ini

# 查看覆盖率报告
open htmlcov/index.html
```

### 常用脚本

```bash
# 创建管理员账户
python3 scripts/create_admin.py

# 创建演示数据
python3 scripts/create_demo_data.py

# 覆盖率分析
python3 scripts/coverage_analysis.py

# 重置管理员密码
python3 reset_admin_password.py

# 快速启动检查
./quick_start.sh
```

### API 访问

- API 基础地址: `http://127.0.0.1:8000`
- OpenAPI 文档: `http://127.0.0.1:8000/docs`（仅开发环境）
- ReDoc 文档: `http://127.0.0.1:8000/redoc`（仅开发环境）
- 健康检查: `GET /health`
- API 前缀: `/api/v1`

## 数据库管理

### 引擎配置 (`app/models/base.py`)

- 开发环境使用 SQLite，配置 `check_same_thread=False` 和 `StaticPool`
- 生产环境支持 MySQL，带连接池
- SQLite 通过 PRAGMA 启用外键约束

### 会话管理

```python
from app.models.base import get_db_session

with get_db_session() as session:
    # 数据库操作
    session.query(Project).all()
```

### 迁移文件命名规范

- 格式: `YYYYMMDD_模块名_{mysql|sqlite}.sql`
- 示例: `20250712_project_management_sqlite.sql`

## 编码规范

### 模型

- 所有模型继承 `Base`，可选继承 `TimestampMixin`
- 使用 `Column` 的 `comment` 参数添加中文说明
- 使用 `back_populates` 明确定义关系
- 通过 `__table_args__` 添加数据库索引

```python
class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, comment="项目编码")
    name = Column(String(100), comment="项目名称")

    # 关系定义
    machines = relationship("Machine", back_populates="project")

    __table_args__ = (
        Index("ix_projects_code", "code"),
    )
```

### 枚举

- 所有枚举定义在 `app/models/enums.py` 或 `app/models/enums/` 目录
- 同时继承 `str` 和 `Enum` 以支持 JSON 序列化
- 使用英文键名，中文注释

```python
class ProjectStage(str, Enum):
    S1_REQUIREMENT = "S1"  # 需求进入
    S2_DESIGN = "S2"       # 方案设计
    # ...
```

### API 端点

- 使用 FastAPI 的 `APIRouter`
- 通过 `Depends(deps.get_db)` 注入数据库会话
- 使用 `require_permission()` 进行权限检查
- 返回 Pydantic 响应模型
- 正确使用 HTTP 状态码

```python
from app.core.security import require_permission
from app.api.deps import get_db

@router.get("/projects/")
async def list_projects(
    current_user: User = Depends(require_permission("project:read")),
    db: Session = Depends(get_db)
):
    return db.query(Project).all()
```

### 数据模式（Schemas）

- 使用 `from_attributes = True` 兼容 ORM
- 分离 Create、Update 和 Response 模式
- 可空字段使用 `Optional`

```python
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)
```

## 身份认证与授权

### JWT 令牌流程

1. 通过 `POST /api/v1/auth/login` 登录
2. 令牌存储在请求头: `Authorization: Bearer <token>`
3. 通过 `get_current_user` 依赖解码令牌

### 权限检查

```python
from app.core.security import require_permission

# 单个权限
@router.get("/protected")
async def protected_route(
    user = Depends(require_permission("project:read"))
):
    pass

# 权限在服务层检查
from app.services.permission_service import PermissionService

service = PermissionService(db)
if service.check_permission(user_id, "project:write"):
    # 执行操作
```

### 权限系统架构

**核心组件：**
- `app/services/permission_service.py` - 权限服务（使用 ApiPermission）
- `app/services/permission_cache_service.py` - 权限缓存服务
- `app/core/auth.py` - 认证和权限检查功能
- `app/core/security.py` - 简化的导出层

**数据模型：**
- `ApiPermission` - API 权限表
- `RoleApiPermission` - 角色 API 权限关联表

## 中间件架构

FastAPI 中间件执行顺序（后进先出）：

1. `GlobalAuthMiddleware` - 全局认证（最先执行）
2. `TenantContextMiddleware` - 租户上下文
3. `AuditMiddleware` - 审计日志
4. `CSRFMiddleware` - CSRF 防护
5. 安全 HTTP 响应头
6. CORS 配置

## 配置说明

环境变量可在 `.env` 文件中设置：

```bash
DEBUG=true
DATABASE_URL=mysql://user:pass@host:3306/dbname
SECRET_KEY=your-secret-key
CORS_ORIGINS=["http://localhost:3000"]
ENABLE_SCHEDULER=true
```

`app/core/config.py` 中的关键配置：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `API_V1_PREFIX` | `/api/v1` | API 前缀 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 1440 | Token 有效期（24小时）|
| `DEFAULT_PAGE_SIZE` | 20 | 默认分页大小 |
| `MAX_PAGE_SIZE` | 100 | 最大分页大小 |
| `MAX_UPLOAD_SIZE` | 10MB | 最大上传文件大小 |

## 专业术语对照表

| 英文 | 中文 | 说明 |
|------|------|------|
| Project | 项目 | 主要工作单元 |
| Machine | 设备/机台 | 正在制造的设备 |
| BOM | 物料清单 | Bill of Materials |
| FAT | 出厂验收 | Factory Acceptance Test |
| SAT | 现场验收 | Site Acceptance Test |
| ECN | 工程变更通知 | Engineering Change Notice |
| PMC | 生产物料控制 | Production Material Control |
| Outsourcing | 外协 | 外部加工 |
| Milestone | 里程碑 | 关键项目节点 |
| Health | 健康度 | 项目状态指示器 |
| Presale | 售前 | 项目立项前阶段 |
| Timesheet | 工时 | 工作时间记录 |

## 测试架构

### 测试目录结构

```
tests/
├── conftest.py          # 全局 fixtures（数据库会话、测试用户等）
├── factories.py         # 测试数据工厂
├── unit/                # 单元测试（280+ 文件）
│   ├── conftest.py      # 单元测试专用 fixtures
│   ├── test_*.py        # 服务层、工具函数测试
│   └── test_alert_rule_engine/  # 子目录组织的测试
├── integration/         # 集成测试
├── api/                 # API 端点测试
├── e2e/                 # 端到端测试
└── performance/         # 性能测试
```

### 测试标记

```python
@pytest.mark.unit          # 单元测试
@pytest.mark.api           # API 测试
@pytest.mark.integration   # 集成测试
@pytest.mark.e2e           # 端到端测试
@pytest.mark.slow          # 慢速测试
@pytest.mark.security      # 安全测试
@pytest.mark.database      # 需要数据库的测试
@pytest.mark.asyncio       # 异步测试
```

### 编写测试示例

```python
import pytest
from unittest.mock import Mock, patch
from app.services.project_service import ProjectService

class TestProjectService:
    @pytest.fixture
    def service(self, db_session):
        return ProjectService(db_session)

    def test_create_project(self, service):
        result = service.create_project({"name": "Test"})
        assert result.name == "Test"

    @pytest.mark.asyncio
    async def test_async_operation(self, service):
        result = await service.async_method()
        assert result is not None
```

## AI 助手注意事项

1. **语言**: 代码使用英文标识符，注释和文档使用中文
2. **日期格式**: 统一使用 `YYYY-MM-DD` 格式
3. **金额精度**: 货币值使用 `Numeric(14, 2)`
4. **软删除**: 多数模型使用 `is_active` 布尔值而非硬删除
5. **时间戳**: 所有使用 `TimestampMixin` 的模型都有 `created_at` 和 `updated_at`
6. **项目编码**: 格式为 `PJyymmddxxx`（例如 `PJ250708001`）
7. **机台编码**: 格式为 `PNxxx`（例如 `PN001`）
8. **权限格式**: 使用 `模块:操作` 格式（例如 `project:read`, `ecn:approve`）
9. **状态机**: 新增需要状态流转的业务时，应使用 `app/core/state_machine/` 框架
10. **服务层**: 复杂业务逻辑应封装在 `app/services/` 中，API 端点保持简洁

## 常见问题排查

### 启动失败

```bash
# 检查数据库连接
python3 -c "from app.models.base import engine; print(engine.url)"

# 检查环境变量
python3 -c "from app.core.config import settings; print(settings.dict())"

# 验证依赖
pip check
```

### 测试失败

```bash
# 查看详细错误
pytest tests/unit/test_xxx.py -v --tb=long

# 单独运行失败的测试
pytest tests/unit/test_xxx.py::test_function -v

# 跳过依赖数据库的测试
pytest -m "not database"
```

### 权限问题

```bash
# 检查用户权限
python3 -c "
from app.models.base import get_db_session
from app.services.permission_service import PermissionService
with get_db_session() as db:
    svc = PermissionService(db)
    print(svc.get_user_permissions(user_id=1))
"
```

## 设计文档

详细设计文档（中文）位于项目根目录：

- `非标自动化项目管理系统_设计文档.md` - 系统概述
- `项目管理模块_详细设计文档.md` - 项目管理模块
- `采购与物料管理模块_详细设计文档.md` - 采购模块
- `变更管理模块_详细设计文档.md` - ECN 模块
- `验收管理模块_详细设计文档.md` - 验收模块
- `外协管理模块_详细设计文档.md` - 外协模块
- `预警与异常管理模块_详细设计文档.md` - 预警模块
- `权限管理模块_详细设计文档.md` - 权限模块
- `角色管理模块_详细设计文档.md` - 角色管理

## 最近更新

### 权限系统重构 (2026-01-27)

- 使用新的 `ApiPermission` 模型替代旧的 `Permission` 模型
- `PermissionService` 通过 `RoleApiPermission` 表查询权限
- 权限缓存服务简化至约 200 行代码
- 删除了硬编码权限文件（保留 `timesheet.py` 业务逻辑）
- 所有 API 端点通过统一的 `require_permission()` 检查权限

### 状态机框架 (2026-01)

- 实现了统一的状态机基类
- 支持状态转换钩子、权限检查、通知
- 已应用于 ECN、验收、问题、里程碑、商机、报价等业务

### 全局认证中间件 (2026-01)

- 实现默认拒绝策略的全局认证
- 租户上下文隔离
- 审计日志记录

---

**最后更新**: 2026-01-30
