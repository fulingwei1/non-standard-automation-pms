I have enough information. Producing the final output now.

| 路径 | 域 | 文件数 | 总行数 | 跨域依赖 | 死代码嫌疑 | 备注 |
|---|---|---|---|---|---|---|
| app/main.py | platform-infra | 1 | 370 | project(status_handlers/ai_job_service), presale等经api_router | 无 | FastAPI 入口；装配中间件链、健康检查/metrics、startup初始化。**唯一加载 `app.api.v1.api.api_router`（第11、103行）** |
| app/dependencies.py | platform-infra | 1 | 50 | 无 | 无 | DB 会话依赖 `get_db` / `get_db_session`，从 models.base 拆出以断循环导入 |
| app/scheduler_progress.py | platform-infra | 1 | 180 | project(progress_service, project_status_normalization) | 无 | 进度预测/依赖巡检每日定时任务，start/stop 被 main.py 调用 |
| app/api/deps.py | platform-auth | 1 | 142 | 无 | 无 | API 依赖：租户ID/管理员/超管校验，re-export get_db 与 security 认证依赖 |
| app/api/response_helpers.py | platform-infra | 1 | 237 | 无 | 疑似(全仓无 import) | 统一响应工厂 success/error/paginated/ApiResponse；无任何引用者 |
| app/api/presale_ai_emotion.py | presale | 1 | 276 | 无(依赖 ai_emotion_service) | 无 | AI 客户情绪分析路由，经 api.py 第272/280行挂载 |
| app/api/v1/api.py | platform-infra(入口) | 1 | 1302 | 全域(集中 include_router) | 无 | **实际生效的路由聚合文件**；模块级 `api_router = create_api_router()`，逐模块 try/import，STRICT_API_ROUTER 控制失败是否抛错 |
| app/api/v1/api_lazy.py | platform-infra(入口) | 1 | 341 | — | 疑似(无引用) | 路由聚合旧版；仅被 api.py 注释提及，无代码引用 |
| app/api/v1/api_medium.py | platform-infra(入口) | 1 | 191 | — | 疑似(无引用) | 路由聚合中间版；无引用 |
| app/api/v1/api_minimal.py | platform-infra(入口) | 1 | 50 | — | 疑似(无引用) | 最小路由聚合；无引用 |
| app/api/v1/api_minimal_backup.py | platform-infra(入口) | 1 | 50 | — | 疑似(_backup 且无引用) | minimal 的备份副本 |
| app/api/v1/ai_planning.py | project | 1 | 486 | 无 | 疑似(无引用;活的是 endpoints/ai_planning.py) | 根级 AI 项目规划(WBS/资源分配)路由；api.py 第320行导入的是 `endpoints.ai_planning`，此根文件无人引用 |
| app/api/v1/company_certifications.py | 待定(sales/presale) | 1 | 116 | 无 | 无 | 公司资质证书 CRUD；api.py 第294行挂载。资质证书归属待业务确认 |
| app/api/v1/presale_ai_cost.py | presale | 1 | 372 | 无(models.sales.presale_ai_cost) | 无 | 售前 AI 成本估算路由，api.py 第273/278行挂载 |
| app/api/v1/presale_ai_integration.py | presale | 1 | 574 | 无 | 无 | 售前 AI 系统集成路由，api.py 第275/277行挂载 |
| app/api/v1/presale_ai_knowledge.py | presale | 1 | 327 | 无 | 无 | 售前 AI 知识库路由，api.py 第274/279行挂载 |
| app/api/v1/presale_ai_quotation.py | presale | 1 | 389 | 无 | 无 | AI 报价单生成路由，api.py 第276/281行挂载（api_lazy/medium 也引用但那两个是死的） |
| app/api/v1/core/project_crud_base.py | project | 1 | 370 | 无 | 无 | 项目子模块 CRUD 路由工厂 `create_project_crud_router`，被 projects/* 多处使用 |
| app/core/auth.py | platform-auth | 1 | 953 | 无 | 无 | 认证核心：密码/JWT/用户获取/权限加载 |
| app/core/security.py | platform-auth | 1 | 91 | 无 | 无 | 简化认证壳，`require_permission("module:action")` |
| app/core/api_key_auth.py | platform-auth | 1 | 206 | 无 | 未核实 | API Key 认证机制（JWT 备选） |
| app/core/permission_engine.py | platform-auth | 1 | 292 | 无 | 无 | 统一权限引擎，收敛 auth/permission_service 权限加载 |
| app/core/permission_codes.py | platform-auth | 1 | 44 | 无 | 无 | 权限编码收口 `*:read`/`*:view` 兼容 |
| app/core/sales_permissions.py | **sales** | 1 | 586 | 无 | 无 | 销售数据范围过滤/增删改权限；被 sales/customers 多端点用（业务逻辑混入 core） |
| app/core/scoring_config.py | **sales** | 1 | 225 | 无 | 疑似(无引用) | 销售评分阈值集中配置；全仓无 import（业务配置混入 core） |
| app/core/production_config.py | **production** | 1 | 16 | 无 | 无 | 生产管理可配参数；被 production_schedule_service 用（业务配置混入 core） |
| app/core/config.py | platform-infra | 1 | 325 | 无 | 无 | 全局 Settings |
| app/core/config.py.secure | platform-infra | 1 | — | — | 疑似(非 .py 备份文件) | config 的 .secure 副本 |
| app/core/csrf.py | platform-infra | 1 | 316 | 无 | 无 | CSRF 中间件，main.py 使用 |
| app/core/encryption.py | platform-infra | 1 | 151 | 无 | 未核实 | AES-256-GCM 字段加密 |
| app/core/secret_manager.py | platform-infra | 1 | 305 | 无 | 未核实 | 密钥管理/轮转 |
| app/core/request_signature.py | platform-infra | 1 | 222 | 无 | 未核实 | HMAC 请求签名防篡改 |
| app/core/exception_handlers.py | platform-infra | 1 | 328 | 无 | 无 | 统一异常处理器，main.py 使用 |
| app/core/exceptions.py | platform-infra | 1 | 18 | 无 | 无 | 临时业务异常定义(FIXME 桩) |
| app/core/logging_config.py | platform-infra | 1 | 333 | 无 | 无 | 统一日志配置，main.py 使用 |
| app/core/rate_limit.py | platform-infra | 1 | 25 | 无 | 疑似(仅 compat 壳) | 从 rate_limiting re-export，仅 endpoints/auth.py 用 |
| app/core/rate_limiting.py | platform-infra | 1 | 158 | 无 | 无 | slowapi limiter 核心，main.py/多处使用 |
| app/core/security_headers.py | platform-infra | 1 | 240 | 无 | 无 | 安全响应头中间件，main.py 使用 |
| app/core/scoring_config? | — | — | — | — | — | (见上) |
| app/core/database/ | platform-infra | 3 | 776 | 无 | 未核实 | partition(分区)/tenant_scope(租户过滤) |
| app/core/decorators/ | platform-infra | 1 | 8 | 无 | 疑似(仅 __init__ 8行,空壳) | 装饰器占位包 |
| app/core/middleware/ | platform-infra | 4 | 476 | 无 | 无 | auth_middleware/tenant_middleware/rate_limiting(in-memory)，均被 main.py 装配 |
| app/core/permissions/ | **performance-hr** | 2 | 290 | 无 | 未核实 | 仅 timesheet.py（工时权限）——应归 performance-hr |
| app/core/schemas/ | platform-infra | 3 | 845 | 无 | 未核实 | 通用响应 schema/validators |
| app/core/state_machine/ (引擎部分) | platform-infra | base/decorators/exceptions/permissions/notifications | 1057 | 无 | 无 | 状态机引擎+通用通知/权限，被各 workflow 端点用 |
| ├─ acceptance.py | acceptance | 1 | 322 | — | 无 | 验收状态机(混入引擎包) |
| ├─ ecn.py, ecn_status.py | ecn | 2 | 515 | — | 无 | ECN 变更状态机 |
| ├─ installation_dispatch.py | production | 1 | 235 | — | 无 | 安装派工状态机 |
| ├─ issue.py | 待定(aftersales/质量) | 1 | 240 | — | 无 | 问题工单状态机 |
| ├─ milestone.py | project | 1 | 230 | — | 无 | 里程碑状态机 |
| ├─ opportunity.py | sales | 1 | 298 | — | 无 | 商机状态机 |
| ├─ quote.py | presale/sales | 1 | 420 | — | 无 | 报价状态机 |
| app/common/context.py | platform-infra | 1 | 73 | 无 | 无 | ContextVar 请求上下文(用户/IP/租户) |
| app/common/date_range.py | platform-infra | 1 | 92 | 无 | 无 | 通用时间范围工具 |
| app/common/pagination.py | platform-infra | 1 | 132 | 无 | 无 | 通用分页 |
| app/common/query_filters.py | platform-infra | 1 | 189 | 无 | 无 | 通用查询过滤 |
| app/common/tree_builder.py | platform-infra | 1 | 113 | 无 | 无 | 扁平转树 |
| app/common/crud/ (通用部分) | platform-infra | 11 | ~2189 | 无 | 无 | 同步/异步 CRUD 基类/repository/service/filters |
| ├─ crud/sales_query_builder.py | **sales** | 1 | 575 | 无 | 无 | 销售链式查询构建器(业务逻辑混入 common) |
| app/common/dashboard/ | analytics | 2 | 306 | 无 | 无 | Dashboard 端点基类 |
| app/common/reports/ | platform-file/analytics | 2 | 341 | 无 | 无 | 报表基类+PDF/Excel/Word 渲染器 |
| app/common/statistics/ | analytics | 5 | 769 | 无 | 无 | 统一统计服务基类/聚合器 |
| app/common/workflow/ | platform-infra | 1 | 80 | 无 | 未核实 | 状态流转 workflow 引擎(仅 engine.py，无 __init__) |
| app/middleware/audit.py | platform-infra | 1 | 31 | 无 | 无 | 审计中间件(IP/UA→上下文)，main.py 使用 |
| app/middleware/rate_limit_middleware.py | platform-infra | 1 | 96 | 无 | 疑似(无引用;main 用的是 core.middleware.rate_limiting) | 独立限流中间件，无人 add_middleware |
| app/plugins/core.py | platform-infra | 1 | 476 | 无 | 疑似(全仓无引用) | 插件框架 Plugin/PluginManager，未被 main.py 加载 |
| app/plugins/hooks.py | platform-infra | 1 | 488 | 无 | 疑似(全仓无引用) | 事件钩子 HookManager + Sales 预定义事件常量，无使用者 |
| app/plugins/installed/ | platform-infra | 1 | 13 | 无 | 疑似(空目录,仅说明) | 无任何实际插件 |
| app/utils/scheduler.py | platform-infra | 1 | 255 | 无 | 无 | APScheduler 调度器，main.py init_scheduler 调用 |
| app/utils/scheduler_config.py | platform-infra | 1 | 17 | 无 | 疑似(compat 壳) | 兼容层，转发到 scheduler_config/ 包 |
| app/utils/scheduler_config/ | 多业务(见备注) | 14 | 1303 | 各业务 | 无 | 各域定时任务元数据(finance/production/timesheet/otd/risk/shortage…)——按业务域拆分 |
| app/utils/scheduled_tasks.py | platform-infra | 1 | 150 | 各业务 | 疑似(compat 壳) | 兼容层，被 ai_admin/多 service 引用 |
| app/utils/scheduled_tasks_new.py | platform-infra | 1 | 33 | — | 疑似(无引用,重构半成品) | 重构版调度中心，无人 import |
| app/utils/scheduled_tasks/ | 多业务(见备注) | 24 | 5526 | 各业务 | 无 | 各域定时任务实现(sales/hr/production/otd/margin/timesheet/risk/kit_rate/issue…)——应各归业务域 |
| app/utils/scheduler_metrics.py | platform-infra | 1 | 234 | 无 | 无 | 内存调度指标，main.py metrics 使用 |
| app/utils/alert_escalation_task.py | platform-notify | 1 | 153 | 无 | 未核实 | 预警自动升级定时任务 |
| app/utils/batch_operations.py | platform-infra | 1 | 366 | 无 | 未核实 | 通用批量操作框架 |
| app/utils/cache_decorator.py | platform-infra | 1 | 253 | 无 | 未核实 | 缓存装饰器 |
| app/utils/redis_client.py | platform-infra | 1 | 63 | 无 | 无 | Redis 客户端，main.py 探针使用 |
| app/utils/rate_limit_decorator.py | platform-infra | 1 | 148 | 无 | 未核实 | 限流装饰器 |
| app/utils/business_code_generator.py | platform-infra | 1 | 139 | 无 | 未核实 | 业务编号生成器 |
| app/utils/number_generator.py | platform-infra | 1 | 499 | 无 | 未核实 | 编号生成 |
| app/utils/domain_codes.py | platform-infra | 1 | 420 | 无 | 未核实 | 领域编码生成 |
| app/utils/code_config.py | platform-infra | 1 | 83 | 无 | 未核实 | 主数据编码配置 |
| app/utils/common.py | platform-infra | 1 | 102 | 无 | 未核实 | 通用工具 |
| app/utils/db_helpers.py | platform-infra | 1 | 128 | 无 | 未核实 | DB 辅助 |
| app/utils/decimal_helpers.py | platform-infra | 1 | 174 | 无 | 未核实 | Decimal 工具 |
| app/utils/numerical_utils.py | platform-infra | 1 | 412 | 无 | 未核实 | 数值计算+业务规则 |
| app/utils/json_helpers.py | platform-infra | 1 | 75 | 无 | 未核实 | JSON 安全解析 |
| app/utils/logging_helpers.py | platform-infra | 1 | 209 | 无 | 未核实 | 日志工具 |
| app/utils/pagination.py | platform-infra | 1 | 154 | 无 | 疑似(与 common/pagination 重复,待核实) | 分页工具(另有 common/pagination.py) |
| app/utils/tree.py | platform-infra | 1 | 12 | 无 | 疑似(12行,与 common/tree_builder 重复) | 树构建(壳) |
| app/utils/status_helpers.py | platform-infra | 1 | 250 | 无 | 未核实 | 状态工具 |
| app/utils/pinyin_utils.py | platform-infra | 1 | 163 | 无 | 未核实 | 拼音工具 |
| app/utils/holiday_utils.py | platform-infra | 1 | 236 | 无 | 未核实 | 节假日/工作日计算 |
| app/utils/permission_helpers.py | platform-auth | 1 | 141 | 无 | 无 | 权限/项目访问校验，被 project_crud_base 等用 |
| app/utils/role_inheritance_utils.py | platform-auth | 1 | 375 | 无 | 未核实 | 角色继承 |
| app/utils/init_data.py | platform-infra | 1 | 140 | 各业务 | 无 | 启动数据初始化，main.py startup 调用 |
| app/utils/init_permissions_data.py | platform-auth | 1 | 631 | 无 | 未核实 | 权限数据初始化(内嵌) |
| app/utils/init_approval_data.py | platform-approval | 1 | 426 | 无 | 未核实 | 审批基础数据初始化 |
| app/utils/wechat_client.py | platform-notify | 1 | 225 | 无 | 未核实 | 企业微信 API 客户端 |
| app/utils/risk_calculator.py | **project** | 1 | 139 | 无 | 未核实 | 风险计算(业务逻辑混入 utils) |
| app/utils/project_utils.py | **project** | 1 | 164 | 无 | 未核实 | 项目工具(业务逻辑混入 utils) |
| app/utils/spec_matcher.py | **presale** | 1 | 251 | 无 | 无 | 规格匹配器，被 spec 定时任务/技术规格端点用(业务混入 utils) |
| app/utils/spec_match_service.py | **presale** | 1 | 272 | 无 | 疑似(疑与 services/spec_match_service.py 重复,未核实) | 规格匹配服务(业务混入 utils) |
| app/utils/spec_extractor/ | **presale** | 5 | 649 | 无 | 未核实 | 规格提取(base/extraction/formats)——需求提取，业务混入 utils |
| app/utils/exports/ | **project** | 2 | 211 | 无 | 未核实 | project_delivery_export 交付导出(业务混入 utils) |
| app/utils/text_similarity.py | platform-infra | 1 | 52 | 无 | 未核实 | 文本相似度 |

## 异常发现

**1. main.py 实际加载的路由聚合文件（最重要结论）**
- `app/main.py` 第 11 行 `from app.api.v1.api import api_router`，第 103 行 `app.include_router(api_router, prefix=settings.API_V1_PREFIX)`。
- **无任何环境变量条件分支**：`api.py` 是唯一被导入并生效的路由聚合文件。`STRICT_API_ROUTER`/`ENABLE_STUB_ENDPOINTS` 只控制 api.py 内部加载失败是否抛错、是否挂 stub，不影响选哪个聚合文件。
- 全仓仅此一处 `from app.api.v1.api import`；`api_lazy.py`、`api_medium.py`、`api_minimal.py`、`api_minimal_backup.py` 均无任何代码引用（只在 api.py 注释和一处 smart_alerts.py 注释中被提及）→ **这 4 个变体全部是死代码**。此外 auth 路由在 main.py 第 91-96 行先于 api_router 单独注册。
- 死活判断基准：**只有被 `app/api/v1/api.py::create_api_router()` 内 try/import 成功挂载的 endpoint 才是活的**。

**2. 插件骨架现状（platform 插件机制）**
- `app/plugins/` 有完整框架：`core.py`(Plugin 基类 + PluginManager，从 `installed/` 动态发现子目录插件) 和 `hooks.py`(HookManager 事件发布/订阅 + emit/emit_async/filter + `SalesEvents`/`SalesFilters` 预定义常量)。
- `installed/` 目录**只有一个纯说明性 `__init__.py`，没有任何实际插件**。
- `get_plugin_manager()`/`get_hook_manager()` 及整个 `app.plugins` 包**全仓（app/ 内）无任何 import**，main.py 也未加载 → **整个插件系统是未接线的死骨架**（约 1000 行）。设计上是为 sales 域合同/商机/报价/发票事件预留，但从未启用。

**3. 死代码群 / 并存版本**
- 路由聚合：api_lazy / api_medium / api_minimal / api_minimal_backup（见第1点）。
- `app/api/v1/ai_planning.py`(根,486行,WBS/资源分配) 死代码 —— 活的是内容完全不同的 `app/api/v1/endpoints/ai_planning.py`(172行)，api.py 第320行导入的是后者。
- `app/api/response_helpers.py` 全仓无引用。
- `app/core/scoring_config.py` 全仓无引用。
- `app/utils/scheduled_tasks_new.py`（重构版调度中心）无引用；`scheduled_tasks.py`/`scheduler_config.py` 是仍在用的 compat 兼容壳（转发到同名子包）。
- `app/middleware/rate_limit_middleware.py` 无人装配（main.py 用的是 `app/core/middleware/rate_limiting.py`）。
- **限流实现四处并存**：`core/rate_limit.py`(re-export壳) + `core/rate_limiting.py`(slowapi,活) + `core/middleware/rate_limiting.py`(in-memory,main.py活) + `app/middleware/rate_limit_middleware.py`(死)。
- **分页/树工具重复**：`utils/pagination.py` vs `common/pagination.py`；`utils/tree.py`(12行壳) vs `common/tree_builder.py`。
- `app/utils/spec_match_service.py` 与 `app/services/spec_match_service.py` 同名疑似重复（未核实哪个活）。
- `app/core/config.py.secure`（非 .py 备份文件）、`app/core/decorators/`（仅 8 行空 __init__）。

**4. 放错位置的文件（业务逻辑混入平台层，重构时应移出）**
- 混入 `app/core/`：`sales_permissions.py`→sales、`scoring_config.py`→sales、`production_config.py`→production、`permissions/timesheet.py`→performance-hr；`state_machine/` 内 acceptance/ecn/ecn_status→ecn、installation_dispatch→production、issue→aftersales、milestone→project、opportunity→sales、quote→presale/sales（引擎 base/decorators/exceptions/permissions/notifications 才是 platform-infra）。
- 混入 `app/common/`：`crud/sales_query_builder.py`→sales。
- 混入 `app/utils/`：`risk_calculator.py`/`project_utils.py`/`exports/`→project、`spec_matcher.py`/`spec_match_service.py`/`spec_extractor/`→presale；`scheduled_tasks/`(24文件5526行) 与 `scheduler_config/`(14文件1303行) 内绝大多数按业务域拆分(sales/hr/production/otd/margin/timesheet/risk/kit_rate/issue/finance…)，仅调度框架部分属 platform-infra。

**5. 多租户检查**：本范围为平台层/入口，几乎无业务表模型；仅注意 `app/core/database/tenant_scope.py`、`app/core/middleware/tenant_middleware.py`、`app/api/deps.py` 提供租户隔离基础设施（tenant_id 过滤），未发现缺 tenant_id 的表定义（本范围内无表模型）。

**未核实项**：受连接中断限制，utils 下多个 platform-infra 工具文件（cache/batch/number/domain_codes 等）的具体引用计数、core/encryption·secret_manager·request_signature·api_key_auth 的挂载情况、`common/workflow/engine.py` 与 `utils/spec_match_service.py` 的活跃度未逐一 grep 核实，已在表中标注"未核实"。