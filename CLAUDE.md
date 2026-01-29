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
| ORM | SQLAlchemy |
| 数据库 | SQLite（开发环境）/ MySQL（生产环境）|
| 数据验证 | Pydantic / pydantic-settings |
| 身份认证 | JWT (python-jose) |
| 密码加密 | passlib + bcrypt |
| ASGI 服务器 | Uvicorn |

## 项目结构

```
non-standard-automation-pms/
├── app/                          # 主应用程序包
│   ├── __init__.py
│   ├── main.py                   # FastAPI 应用入口
│   ├── api/                      # API 路由
│   │   ├── deps.py               # 依赖注入 (get_db)
│   │   └── v1/
│   │       ├── api.py            # API 路由聚合
│   │       └── endpoints/        # API 端点模块
│   │           └── projects/     # 项目模块（已整合）
│   │               ├── core.py           # 核心CRUD
│   │               ├── stages/           # 阶段管理
│   │               ├── milestones/       # 里程碑管理
│   │               ├── machines/         # 机台管理
│   │               ├── members/          # 团队成员
│   │               ├── roles/            # 项目角色
│   │               ├── costs/            # 成本管理
│   │               ├── progress/         # 进度管理
│   │               ├── work_logs/        # 工作日志
│   │               ├── evaluations/      # 项目评价
│   │               ├── timesheet/        # 工时管理
│   │               ├── workload/         # 工作量管理
│   │               └── resource_plan/    # 资源计划
│   ├── core/                     # 核心配置
│   │   ├── config.py             # 应用配置 (pydantic-settings)
│   │   └── security.py           # JWT 认证、密码加密、权限控制
│   ├── models/                   # SQLAlchemy ORM 模型
│   │   ├── base.py               # 基础模型、引擎、会话管理
│   │   ├── enums.py              # 所有枚举定义
│   │   ├── user.py               # 用户、角色、权限模型
│   │   ├── project.py            # 项目、设备、阶段、里程碑模型
│   │   ├── material.py           # 物料、BOM、供应商模型
│   │   ├── purchase.py           # 采购订单模型
│   │   ├── ecn.py                # 工程变更通知模型
│   │   ├── acceptance.py         # 验收管理模型
│   │   ├── outsourcing.py        # 外协供应商/订单模型
│   │   ├── alert.py              # 预警和异常模型
│   │   └── organization.py       # 部门组织模型
│   ├── services/                 # 业务服务层
│   │   ├── project_execution_service.py   # 项目执行服务
│   │   ├── project_resource_service.py    # 项目资源服务
│   │   ├── project_finance_service.py     # 项目财务服务
│   │   └── project_analytics_service.py   # 项目分析服务
│   └── schemas/                  # Pydantic 数据模式（API 验证）
│       ├── common.py             # 通用响应模式
│       ├── auth.py               # 认证模式
│       ├── project.py            # 项目请求/响应模式
│       ├── material.py           # 物料模式
│       ├── purchase.py           # 采购模式
│       ├── ecn.py                # ECN 模式
│       ├── acceptance.py         # 验收模式
│       ├── outsourcing.py        # 外协模式
│       └── alert.py              # 预警模式
├── migrations/                   # SQL 迁移文件
│   ├── *_sqlite.sql              # SQLite 专用迁移
│   └── *_mysql.sql               # MySQL 专用迁移
├── data/                         # SQLite 数据库存储
│   └── app.db                    # SQLite 数据库文件
├── templates/                    # HTML 模板
├── docs/                         # 附加文档
├── attachments/                  # 图表和附件
├── claude 设计方案/              # 设计文档和规格说明
├── init_db.py                    # 数据库初始化脚本
├── requirements.txt              # Python 依赖
└── *.md                          # 模块详细设计文档
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

### 5. 验收管理

- **模型**: `AcceptanceTemplate`, `AcceptanceOrder`, `AcceptanceOrderItem`, `AcceptanceIssue`
- 类型：FAT（出厂验收）、SAT（现场验收）、终验收

### 6. 外协管理

- **模型**: `OutsourcingVendor`, `OutsourcingOrder`, `OutsourcingDelivery`, `OutsourcingInspection`

### 7. 预警与异常

- **模型**: `AlertRule`, `AlertRecord`, `ExceptionEvent`, `AlertStatistics`, `ProjectHealthSnapshot`
- 预警级别：提示、警告、严重、紧急

## 项目中心 API 结构

系统采用项目中心 API 设计，所有项目相关操作均通过 `/projects/{project_id}/` 访问：

### 项目子模块路由

| 路由 | 描述 | 主要功能 |
|------|------|----------|
| `/projects/{id}/milestones/` | 里程碑管理 | 列表、创建、完成、删除 |
| `/projects/{id}/machines/` | 机台管理 | CRUD、批量操作 |
| `/projects/{id}/members/` | 团队成员 | 添加、移除、角色管理 |
| `/projects/{id}/roles/` | 项目角色 | 负责人、团队成员、配置 |
| `/projects/{id}/costs/` | 成本管理 | 成本记录、统计、审批 |
| `/projects/{id}/progress/` | 进度管理 | 汇总、甘特图、看板 |
| `/projects/{id}/stages/` | 阶段管理 | 初始化、推进、门禁检查 |
| `/projects/{id}/work-logs/` | 工作日志 | 查看、汇总 |
| `/projects/{id}/evaluations/` | 项目评价 | 创建、确认、统计 |
| `/projects/{id}/timesheet/` | 工时管理 | 记录、汇总、统计 |
| `/projects/{id}/workload/` | 工作量管理 | 团队负荷、甘特图、摘要 |
| `/projects/{id}/resource-plan/` | 资源计划 | 资源分配、需求 |

### 服务层

项目业务逻辑通过服务层统一管理：

| 服务 | 职责 |
|------|------|
| `ProjectExecutionService` | 阶段管理、门禁检查、进度聚合 |
| `ProjectResourceService` | 团队管理、资源负荷、贡献度 |
| `ProjectFinanceService` | 成本统计、人工成本、奖金 |
| `ProjectAnalyticsService` | 仪表盘、统计分析、趋势 |

## 开发命令

### 环境搭建

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库（创建 data/app.db）
python3 init_db.py
```

### 运行应用

```bash
# 使用 uvicorn 直接运行
uvicorn app.main:app --reload

# 或使用 Python 模块方式
python3 -m app.main
```

### API 访问

- API 基础地址: `http://127.0.0.1:8000`
- OpenAPI 文档: `http://127.0.0.1:8000/docs`
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

### 枚举

- 所有枚举定义在 `app/models/enums.py`
- 同时继承 `str` 和 `Enum` 以支持 JSON 序列化
- 使用英文键名，中文注释

### API 端点

- 使用 FastAPI 的 `APIRouter`
- 通过 `Depends(deps.get_db)` 注入数据库会话
- 返回 Pydantic 响应模型
- 正确使用 HTTP 状态码

### 数据模式（Schemas）

- 使用 `from_attributes = True`（原 `orm_mode`）兼容 ORM
- 分离 Create、Update 和 Response 模式
- 可空字段使用 `Optional`

## 身份认证与授权

### JWT 令牌流程

1. 通过 `/api/v1/auth/login` 登录（待实现）
2. 令牌存储在请求头: `Authorization: Bearer <token>`
3. 通过 `get_current_user` 依赖解码令牌

### 权限检查

```python
from app.core.security import require_permission

@router.get("/protected")
async def protected_route(user = Depends(require_permission("project:read"))):
    pass
```

## 配置说明

环境变量可在 `.env` 文件中设置：

```
DEBUG=true
DATABASE_URL=mysql://user:pass@host:3306/dbname
SECRET_KEY=your-secret-key
CORS_ORIGINS=["http://localhost:3000"]
```

`app/core/config.py` 中的关键配置：

- `API_V1_PREFIX`: `/api/v1`
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 1440（24小时）
- `DEFAULT_PAGE_SIZE`: 20
- `MAX_PAGE_SIZE`: 100
- `MAX_UPLOAD_SIZE`: 10MB

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

## 设计文档

详细设计文档（中文）：

- `非标自动化项目管理系统_设计文档.md` - 系统概述
- `项目管理模块_详细设计文档.md` - 项目管理模块
- `采购与物料管理模块_详细设计文档.md` - 采购模块
- `变更管理模块_详细设计文档.md` - ECN 模块
- `验收管理模块_详细设计文档.md` - 验收模块
- `外协管理模块_详细设计文档.md` - 外协模块
- `预警与异常管理模块_详细设计文档.md` - 预警模块
- `权限管理模块_详细设计文档.md` - 权限模块
- `角色管理模块_详细设计文档.md` - 角色管理

## AI 助手注意事项

1. **语言**: 代码使用英文标识符，注释和文档使用中文
2. **日期格式**: 统一使用 `YYYY-MM-DD` 格式
3. **金额精度**: 货币值使用 `Numeric(14, 2)`
4. **软删除**: 多数模型使用 `is_active` 布尔值而非硬删除
5. **时间戳**: 所有使用 `TimestampMixin` 的模型都有 `created_at` 和 `updated_at`
6. **项目编码**: 格式为 `PJyymmddxxx`（例如 `PJ250708001`）
7. **机台编码**: 格式为 `PNxxx`（例如 `PN001`）

## 测试

目前未配置测试套件。添加测试时：

- 使用 pytest 作为测试框架
- 创建 `tests/` 目录，结构与 `app/` 保持一致
- 使用 `app/models/base.py` 中的 `reset_engine()` 实现测试隔离

## 未来开发方向

根据设计文档，计划实现的功能包括：

- 销售管理（从线索到回款流程）
- 进度跟踪模块
- 绩效管理
- 成本管理
- 所有模块的完整 API 实现

- 测试：`pnpm test`（不是 npm test）
- 构建：`pnpm build`
- Lint：`pnpm lint`

## 权限系统重构完成 (2026-01-27)

### 重构内容

#### 1. PermissionService 重构完成
- 文件：`app/services/permission_service.py`
- 变更：
  - 使用新的 `ApiPermission` 模型替代旧的 `Permission` 模型
  - `get_user_permissions()` 方法现在通过 `RoleApiPermission` 表查询 `api_permissions`
  - 所有权限检查方法 (`check_permission`, `check_any_permission`, `check_all_permissions`) 使用统一的 PermissionService

#### 2. PermissionCacheService 压缩简化完成
- 文件：`app/services/permission_cache_service.py`
- 变更：
  - 从 328 行压缩到约 200 行
  - 移除了不必要的方法，保留核心缓存功能
  - 简化了代码结构

#### 3. 硬编码权限文件删除完成
- 删除目录：`app/core/permissions/`（部分保留）
- 删除的文件：
  - `finance.py`
  - `hr.py`
  - `machine.py`
  - `procurement.py`
  - `production.py`
  - `project.py`
  - `rd_project.py`
  - `scheduler.py`
  - `sales.py`
- **保留的文件**：
  - `timesheet.py` - 包含工时审批业务逻辑函数（非简单权限检查）
    - `apply_timesheet_access_filter()` - 工时数据访问过滤
    - `get_user_manageable_dimensions()` - 获取用户可管理维度
    - `is_timesheet_admin()` - 检查工时管理员
    - `check_timesheet_approval_permission()` - 工时审批权限检查

#### 4. Security.py 兼容层清理完成
- 文件：`app/core/security.py`
- 变更：
  - 删除了 `permissions/` 目录的导入
  - 简化为仅导出认证相关功能
  - 保留 `check_permission()` 和 `require_permission()` 从 `auth.py`

#### 5. API 端点保持不变
- 155 个文件中的 470 处 `require_permission()` 调用保持不变
- 所有 API 端点现在通过 `auth.py` 的 `check_permission()` 使用统一的 PermissionService

#### 6. 权限系统架构

**核心组件：**
- `app/services/permission_service.py` - 权限服务（使用 ApiPermission）
- `app/services/permission_cache_service.py` - 权限缓存服务（简化版）
- `app/core/auth.py` - 认证和权限检查功能
- `app/core/security.py` - 简化的导出层

**数据模型：**
- `ApiPermission` - API 权限表（新）
- `RoleApiPermission` - 角色 API 权限关联表（新）
- `Permission` - 旧权限表（保留用于兼容性）

**API 端点使用模式：**
```python
from app.core.security import require_permission

@router.get("/projects/")
async def list_projects(
    current_user: User = Depends(require_permission("project:read")),
    db: Session = Depends(get_db)
):
    ...
```

