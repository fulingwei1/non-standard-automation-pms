# CLAUDE.md - AI 助手开发指南（非标自动化项目管理系统）

## 项目概述

这是一个**非标自动化项目管理系统**，专为定制自动化设备制造企业设计，适用于：

- ICT/FCT/EOL 测试设备
- 烧录设备、老化设备
- 视觉检测设备
- 自动化组装线体

系统管理从签单到售后的完整项目生命周期，是一个企业级 ERP/PMS 系统。

## 系统规模

| 组件 | 数量 |
|------|------|
| API 端点模块 | 90+ 目录 |
| 业务服务 | 240+ 服务文件 |
| 数据模型 | 65+ 主模型文件 |
| 状态机 | 11 个实现 |
| 测试文件 | 490+ 测试文件 |
| 审批适配器 | 11 个业务类型 |
| 仪表盘适配器 | 11 个数据提供器 |

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
| 缓存 | Redis (可选) |
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
│   │       └── endpoints/            # API 端点模块 (90+ 模块)
│   │           ├── acceptance/       # 验收管理
│   │           ├── admin_stats.py    # 管理统计
│   │           ├── alerts/           # 预警管理
│   │           ├── analytics/        # 数据分析
│   │           ├── approvals/        # 审批流程
│   │           ├── assembly_kit/     # 装配套件
│   │           ├── auth.py           # 认证端点
│   │           ├── bom/              # 物料清单
│   │           ├── bonus/            # 奖金管理
│   │           ├── budget/           # 预算管理
│   │           ├── culture_wall/     # 文化墙
│   │           ├── customers/        # 客户管理
│   │           ├── dashboard_unified.py  # 统一仪表盘
│   │           ├── data_import_export/   # 数据导入导出
│   │           ├── departments/      # 部门管理
│   │           ├── documents/        # 文档管理
│   │           ├── ecn/              # 工程变更通知
│   │           ├── engineer_performance/  # 工程师绩效
│   │           ├── engineers/        # 工程师管理
│   │           ├── hr_management/    # 人力资源
│   │           ├── installation_dispatch/ # 安装派遣
│   │           ├── inventory_analysis.py  # 库存分析
│   │           ├── issues/           # 问题管理
│   │           ├── itr.py            # ITR 管理
│   │           ├── kit_check/        # 套件检查
│   │           ├── kit_rate/         # 套件使用率
│   │           ├── machines/         # 机台管理
│   │           ├── management_rhythm/ # 管理节奏
│   │           ├── materials/        # 物料管理
│   │           ├── notifications/    # 通知管理
│   │           ├── organization/     # 组织架构
│   │           ├── outsourcing/      # 外协管理
│   │           ├── performance/      # 绩效管理
│   │           ├── permissions/      # 权限管理
│   │           ├── pitfalls/         # 踩坑记录
│   │           ├── pmo/              # PMO 管理
│   │           ├── presales/         # 售前管理
│   │           ├── presale_analytics.py  # 售前分析
│   │           ├── procurement_analysis.py # 采购分析
│   │           ├── production/       # 生产管理
│   │           ├── project_contributions.py # 项目贡献
│   │           ├── project_evaluation/   # 项目评价
│   │           ├── project_workspace.py  # 项目工作区
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
│   │           ├── rd_project/       # 研发项目
│   │           ├── report_center/    # 报表中心
│   │           ├── reports/          # 报表管理
│   │           ├── sales/            # 销售管理
│   │           ├── shortage/         # 短缺管理
│   │           ├── sla/              # SLA 管理
│   │           ├── solution_credits.py   # 方案积分
│   │           ├── staff_matching.py     # 人员匹配
│   │           ├── strategy/         # 战略管理 (BEM)
│   │           ├── supplier_analysis/    # 供应商分析
│   │           ├── suppliers.py      # 供应商管理
│   │           ├── technical_review/ # 技术评审
│   │           ├── technical_spec/   # 技术规格
│   │           ├── tenants.py        # 租户管理
│   │           ├── timesheet/        # 工时管理
│   │           ├── users/            # 用户管理
│   │           └── work_log/         # 工作日志 AI
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
│   │       ├── ecn_status.py         # ECN 状态辅助
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
│   │   ├── strategy/                 # 战略管理模型 (新)
│   │   ├── production/               # 生产管理模型 (新)
│   │   ├── service/                  # 服务管理模型 (新)
│   │   ├── business_support/         # 业务支持模型 (新)
│   │   ├── pmo/                      # PMO 模型 (新)
│   │   ├── rd_project/               # 研发项目模型 (新)
│   │   └── ...                       # 其他业务模型
│   ├── services/                     # 业务服务层 (240+ 服务)
│   │   ├── permission_service.py     # 权限服务 (核心)
│   │   ├── permission_cache_service.py # 权限缓存服务
│   │   ├── notification_service.py   # 通知服务
│   │   ├── unified_notification_service.py  # 统一通知服务
│   │   ├── approval_engine/          # 统一审批引擎 (详见下文)
│   │   ├── alert_rule_engine/        # 预警规则引擎 (详见下文)
│   │   ├── status_handlers/          # 状态流转处理器
│   │   ├── notification_handlers/    # 通知处理器 (Email/SMS/WeChat/System)
│   │   ├── channel_handlers/         # 渠道处理器
│   │   ├── dashboard_adapters/       # 仪表盘数据适配器 (11个)
│   │   ├── report_framework/         # 报表生成框架
│   │   ├── strategy/                 # 战略管理服务 (新)
│   │   ├── production/               # 生产管理服务 (新)
│   │   ├── staff_matching/           # AI 人员匹配服务 (新)
│   │   ├── work_log_ai/              # 工作日志 AI 服务 (新)
│   │   ├── unified_import/           # 统一导入服务 (新)
│   │   ├── ai_service.py             # AI 集成服务 (新)
│   │   ├── ai_assessment_service.py  # AI 技术评估 (新)
│   │   ├── sales_prediction_service.py    # 销售预测 (新)
│   │   ├── win_rate_prediction_service.py # 赢率预测 (新)
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
│   │   ├── scheduled_tasks/          # 定时任务处理器
│   │   ├── scheduler_config/         # 调度器配置
│   │   ├── init_data.py              # 基础数据初始化
│   │   ├── number_generator.py       # 编号生成器
│   │   ├── redis_client.py           # Redis 客户端
│   │   ├── wechat_client.py          # 微信客户端
│   │   ├── holiday_utils.py          # 节假日工具
│   │   ├── pinyin_utils.py           # 拼音转换工具
│   │   ├── cache_decorator.py        # 缓存装饰器
│   │   └── ...                       # 其他工具
│   ├── common/                       # 公共模块
│   │   ├── crud/                     # CRUD 工具
│   │   ├── dashboard/                # 仪表盘工具
│   │   ├── reports/                  # 报表工具
│   │   └── statistics/               # 统计工具
│   ├── middleware/                   # 应用中间件
│   │   └── audit.py                  # 审计日志中间件
│   ├── report_configs/               # 报表配置
│   └── templates/                    # 模板文件
├── tests/                            # 测试目录
│   ├── conftest.py                   # pytest 配置和 fixtures
│   ├── factories.py                  # 测试数据工厂
│   ├── unit/                         # 单元测试 (490+ 测试文件)
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

### 1. 项目管理（核心模块）

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
- 支持缺料预警、紧急采购生成

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

### 8. 战略管理 (BEM 框架) - 新模块

- **位置**: `app/services/strategy/`, `app/models/strategy/`
- **模型**: `Strategy`, `CSF`, `KPI`, `KPIHistory`, `KPIDataSource`, `AnnualKeyWork`, `DepartmentObjective`, `PersonalKPI`, `StrategyReview`, `StrategyComparison`
- **服务**:
  - `strategy_service.py` - 战略管理
  - `csf_service.py` - 关键成功因素
  - `kpi_service/` - KPI 管理
  - `annual_work_service/` - 年度重点工作
  - `decomposition/` - 目标分解
  - `comparison_service.py` - 战略对比
  - `review/` - 战略评审
  - `health_calculator.py` - 战略健康度

### 9. 生产管理 - 新模块

- **位置**: `app/services/production/`, `app/models/production/`
- **模型**:
  - `Workshop`, `Workstation`, `Worker`, `WorkerSkill` - 车间/工位/工人
  - `ProcessDict`, `Equipment`, `EquipmentMaintenance` - 工艺/设备
  - `ProductionPlan`, `WorkOrder`, `WorkReport` - 生产计划/工单
  - `ProductionException`, `ProductionDailyReport` - 异常/日报
  - `MaterialRequisition`, `MaterialRequisitionItem` - 领料单

### 10. 服务管理 - 新模块

- **位置**: `app/models/service/`
- **模型**: `ServiceTicket`, `ServiceTicketProject`, `ServiceRecord`, `CustomerCommunication`, `CustomerSatisfaction`, `KnowledgeBase`
- 完整的售后服务管理，包含工单、沟通记录、满意度调查、知识库

### 11. 业务支持管理 - 新模块

- **位置**: `app/models/business_support/`
- **模型**:
  - `SalesOrder`, `SalesOrderItem`, `DeliveryOrder` - 销售订单/发货
  - `AcceptanceTracking`, `Reconciliation` - 验收跟踪/对账
  - `InvoiceRequest`, `PaymentReminder` - 开票/付款提醒
  - `CustomerSupplierRegistration` - 客户供应商注册
  - `BiddingProject`, `BiddingDocument` - 招投标

### 12. PMO 管理 - 新模块

- **位置**: `app/models/pmo/`
- **模型**: `PmoProjectInitiation`, `PmoProjectPhase`, `PmoChangeRequest`, `PmoProjectRisk`, `PmoProjectCost`, `PmoMeeting`, `PmoResourceAllocation`, `PmoProjectClosure`

### 13. 研发项目管理 - 新模块

- **位置**: `app/models/rd_project/`
- **模型**: `RdProjectCategory`, `RdProject`, `RdCostType`, `RdCost`, `RdCostAllocationRule`, `RdReportRecord`

## 统一审批引擎

系统使用统一的审批引擎处理所有业务审批流程。

### 架构 (`app/services/approval_engine/`)

```
approval_engine/
├── adapters/                    # 业务适配器 (11个)
│   ├── base.py                  # 基础适配器
│   ├── acceptance_adapter.py    # 验收审批
│   ├── contract_adapter.py      # 合同审批
│   ├── ecn_adapter.py           # ECN 审批
│   ├── invoice_adapter.py       # 发票审批
│   ├── outsourcing_adapter.py   # 外协审批
│   ├── project_adapter.py       # 项目审批
│   ├── purchase_adapter.py      # 采购审批
│   ├── quote_adapter.py         # 报价审批
│   └── timesheet_adapter.py     # 工时审批
├── engine/                      # 引擎核心
│   ├── core.py                  # 核心逻辑
│   ├── submit.py                # 提交处理
│   ├── approve.py               # 审批处理
│   ├── actions.py               # 审批动作
│   └── query.py                 # 查询服务
├── notifications/               # 通知系统
│   ├── basic.py                 # 基础通知
│   ├── flow.py                  # 流程通知
│   ├── comment.py               # 评论通知
│   ├── reminder.py              # 提醒通知
│   ├── external_channel.py      # 外部渠道
│   └── batch.py                 # 批量通知
└── workflow/                    # 工作流
    ├── engine.py                # 工作流引擎
    ├── delegate.py              # 委托管理
    ├── execution_log.py         # 执行日志
    └── condition_parser.py      # 条件解析
```

### 审批模型 (`app/models/approval/`)

- `ApprovalTemplate` - 审批模板
- `ApprovalWorkflow` - 审批工作流
- `ApprovalInstance` - 审批实例
- `ApprovalTask` - 审批任务
- `ApprovalRecord` - 审批记录
- `ApprovalHistory` - 审批历史
- `ApprovalDelegate` - 审批委托
- `ApprovalComment` - 审批评论
- `ApprovalCarbonCopy` - 抄送
- `ApprovalCountersignResult` - 会签结果

## 预警规则引擎

### 架构 (`app/services/alert_rule_engine/`)

```
alert_rule_engine/
├── base.py              # 基础引擎实现
├── rule_manager.py      # 规则生命周期管理
├── condition_evaluator.py  # 复杂条件评估
├── alert_creator.py     # 预警创建
├── alert_generator.py   # 预警生成
├── alert_upgrader.py    # 预警升级逻辑
└── level_determiner.py  # 预警级别判定
```

### 预警类型

| 类型 | 说明 |
|------|------|
| 进度预警 | 项目进度滞后 |
| 成本预警 | 成本超支 |
| 缺料预警 | 物料短缺 |
| 质量预警 | 质量问题 |
| 交付预警 | 交付风险 |

## 通知系统

### 通知处理器 (`app/services/notification_handlers/`)

| 处理器 | 渠道 |
|--------|------|
| `email_handler.py` | 邮件通知 |
| `sms_handler.py` | 短信通知 |
| `system_handler.py` | 系统内通知 |
| `wechat_handler.py` | 企业微信通知 |

### 渠道处理器 (`app/services/channel_handlers/`)

- `base.py` - 基础渠道处理器
- `webhook.py` - Webhook 处理器
- 扩展其他渠道

### 统一通知服务

- `notification_service.py` - 基础通知服务
- `unified_notification_service.py` - 统一通知调度
- `notification_dispatcher.py` - 通知分发

## 仪表盘适配器

系统提供 11 个仪表盘数据适配器 (`app/services/dashboard_adapters/`)：

| 适配器 | 数据领域 |
|--------|----------|
| 项目仪表盘 | 项目概览、进度、健康度 |
| 采购仪表盘 | 采购统计、订单状态 |
| 生产仪表盘 | 生产计划、产能 |
| 质量仪表盘 | 质量指标、问题统计 |
| 财务仪表盘 | 成本、收入、利润 |
| 人力仪表盘 | 工时、绩效 |
| 销售仪表盘 | 销售漏斗、业绩 |
| 库存仪表盘 | 库存状态、周转率 |
| 服务仪表盘 | 工单、满意度 |
| 预警仪表盘 | 预警统计、趋势 |
| 综合仪表盘 | 全局概览 |

## 报表框架

### 架构 (`app/services/report_framework/`)

```
report_framework/
├── data_sources/        # 数据源定义
├── adapters/            # 数据适配器
├── expressions/         # 表达式引擎
├── formatters/          # 数据格式化
├── renderers/           # 报表渲染器
└── cache/               # 缓存管理
```

### 报表中心模型

- `ReportTemplate` - 报表模板
- `ReportDefinition` - 报表定义
- `ReportGenerationRecord` - 生成记录
- `ReportSubscription` - 报表订阅

## AI/ML 服务

系统集成了多个 AI/ML 服务用于智能化辅助：

| 服务 | 功能 |
|------|------|
| `ai_service.py` | 通用 AI 集成 |
| `ai_assessment_service.py` | 技术方案 AI 评估 |
| `sales_prediction_service.py` | 销售预测 |
| `win_rate_prediction_service.py` | 商机赢率预测 |
| `knowledge_extraction_service.py` | 知识提取 |
| `knowledge_auto_identification_service.py` | 知识自动识别 |
| `staff_matching/` | AI 人员匹配（技能、经验匹配） |
| `work_log_ai/` | 工作日志自动生成和分析 |

## 成本管理服务

| 服务 | 功能 |
|------|------|
| `cost_collection_service.py` | 多源成本采集 |
| `cost_overrun_analysis_service.py` | 超支分析 |
| `cost_match_suggestion_service.py` | 成本匹配建议 |
| `labor_cost_calculation_service.py` | 人工成本计算 |
| `labor_cost_expense_service.py` | 人工费用管理 |
| `issue_cost_service.py` | 问题成本追踪 |

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

### 业务状态机 (11个)

| 状态机 | 业务 | 关键状态 |
|--------|------|----------|
| `ecn.py` | ECN 变更 | draft → pending_evaluation → evaluating → pending_approval → approved/rejected |
| `ecn_status.py` | ECN 状态辅助 | 状态转换辅助函数 |
| `acceptance.py` | 验收 | draft → submitted → testing → passed/failed |
| `issue.py` | 问题 | open → in_progress → resolved → closed |
| `milestone.py` | 里程碑 | pending → in_progress → completed |
| `opportunity.py` | 商机 | lead → qualified → proposal → negotiation → won/lost |
| `quote.py` | 报价 | draft → submitted → reviewing → approved/rejected |
| `installation_dispatch.py` | 安装派遣 | pending → dispatched → in_progress → completed |

### 状态处理器 (`app/services/status_handlers/`)

- ECN 状态处理器
- 验收状态处理器
- 合同状态处理器
- 里程碑状态处理器
- 物料状态处理器

## 组织与权限系统 (V2)

### 组织架构模型

- `OrganizationUnit` - 组织单元
- `Position` - 职位
- `JobLevel` - 职级
- `EmployeeOrgAssignment` - 员工组织分配
- `PositionRole` - 职位角色

### 权限模型

- `ApiPermission` - API 权限
- `RoleApiPermission` - 角色 API 权限关联
- `DataScopeRule` - 数据范围规则
- `RoleDataScope` - 角色数据范围
- `PermissionGroup` - 权限组
- `MenuPermission` - 菜单权限
- `RoleMenu` - 角色菜单

### 枚举类型

- `ScopeType` - 范围类型
- `MenuType` - 菜单类型
- `PermissionType` - 权限类型
- `ResourceType` - 资源类型

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

### 服务层规范

- 复杂业务逻辑封装在 `app/services/` 中
- 服务类接收 `db: Session` 作为构造参数
- API 端点保持简洁，调用服务层方法
- 使用依赖注入获取服务实例

```python
class ProjectService:
    def __init__(self, db: Session):
        self.db = db

    def create_project(self, data: ProjectCreate) -> Project:
        project = Project(**data.dict())
        self.db.add(project)
        self.db.commit()
        return project
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
- `app/services/permission_crud_service.py` - 权限 CRUD 服务
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
REDIS_URL=redis://localhost:6379/0
WECHAT_CORP_ID=your-corp-id
WECHAT_AGENT_ID=your-agent-id
WECHAT_SECRET=your-secret
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
| BEM | 战略管理 | Balanced Enterprise Management |
| CSF | 关键成功因素 | Critical Success Factor |
| KPI | 关键绩效指标 | Key Performance Indicator |
| PMO | 项目管理办公室 | Project Management Office |
| SLA | 服务级别协议 | Service Level Agreement |
| ITR | 即时修复 | In-Time Repair |
| R&D | 研发 | Research & Development |
| Workshop | 车间 | 生产车间 |
| Workstation | 工位 | 生产工位 |
| WorkOrder | 工单 | 生产/服务工单 |

## 测试架构

### 测试目录结构

```
tests/
├── conftest.py          # 全局 fixtures（数据库会话、测试用户等）
├── factories.py         # 测试数据工厂
├── unit/                # 单元测试（490+ 文件）
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
11. **审批流程**: 需要审批的业务应接入 `approval_engine`，创建对应适配器
12. **通知发送**: 使用 `unified_notification_service` 统一发送通知
13. **仪表盘数据**: 新增仪表盘应创建对应的 dashboard adapter
14. **AI 服务**: 需要 AI 辅助的功能可参考现有 AI 服务实现

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

### 审批流程问题

```bash
# 检查审批实例状态
python3 -c "
from app.models.base import get_db_session
from app.models.approval import ApprovalInstance
with get_db_session() as db:
    instance = db.query(ApprovalInstance).filter_by(id=1).first()
    print(instance.status, instance.current_node)
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

### 技术报告

- `PERMISSION_MIGRATION_REPORT.md` - 权限系统迁移报告
- `APPROVAL_ADAPTERS_COMPLETION_REPORT.md` - 审批适配器完成报告
- `CIRCULAR_DEPS_FINAL_REPORT.md` - 循环依赖解决报告
- `APPROVAL_ENGINE_NOTIFICATION_UNIFICATION_COMPLETE.md` - 审批通知统一报告
- `ECN_NOTIFICATION_UNIFICATION_COMPLETE.md` - ECN 通知统一报告
- `IMPLEMENTATION_REPORT_AUTH_MIDDLEWARE.md` - 全局认证中间件报告
- `DEPLOYMENT_GUIDE.md` - 部署指南

## 最近更新

### 综合测试覆盖提升 (2026-01-30)

- 新增 72 个综合测试文件
- 覆盖所有主要服务（告警、成本、审批、验收等）
- 测试文件总数达到 490+

### 权限系统重构 (2026-01-27)

- 使用新的 `ApiPermission` 模型替代旧的 `Permission` 模型
- `PermissionService` 通过 `RoleApiPermission` 表查询权限
- 权限缓存服务简化至约 200 行代码
- 删除了硬编码权限文件（保留 `timesheet.py` 业务逻辑）
- 所有 API 端点通过统一的 `require_permission()` 检查权限

### 代码重构 (2026-01)

- 移除 10 个废弃/未使用的 CRUD 端点文件
- 移除未使用的示例和内部文档
- 解决了 50+ 文件的循环依赖问题

### 状态机框架 (2026-01)

- 实现了统一的状态机基类
- 支持状态转换钩子、权限检查、通知
- 已应用于 ECN、验收、问题、里程碑、商机、报价等业务

### 全局认证中间件 (2026-01)

- 实现默认拒绝策略的全局认证
- 租户上下文隔离
- 审计日志记录

### 审批引擎完善 (2026-01)

- 完成 11 个业务类型的审批适配器
- 统一通知系统集成
- 工作流委托管理

---

**最后更新**: 2026-01-31
