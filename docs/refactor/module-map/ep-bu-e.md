已收到基准信息（api.py 为唯一生效聚合器）。我在中断前已完成全部核查，直接输出最终结果。

| 路径 | 域 | 文件数 | 总行数 | 跨域依赖 | 死代码嫌疑 | 备注 |
|---|---|---|---|---|---|---|
| `endpoints/budget/` | cost-finance | 5 | 847 | project | 无 | 项目预算 CRUD/提交/审批/明细/成本分摊规则；经 api.py `/budgets` 挂载 |
| `endpoints/business_support/` | sales | 7 | 1708 | sales | 无 | 商务支持：投标、合同审核/盖章、回款催收、档案、工作台；`/business-support` 挂载 |
| `endpoints/business_support_orders/` | sales | 22 | 4010 | sales, acceptance, production, project | 无 | 销售订单/交付单/开票申请/对账/验收跟踪/各类报表；含 delivery_orders(3)、sales_orders(4) 两子包；`/business-support-orders` 挂载 |
| `endpoints/change_impact.py` | ecn | 1 | 34 | 无 | 疑似(禁用兼容 shim，全部方法返回 501，且未被 api.py 挂载) | 旧 `/change-impact` 占位，明确指向 `/project-change-impacts`；顶层文件未注册，activ 的是 `projects.change_impact` |
| `endpoints/competitor_analysis.py` | sales | 1 | 578 | 无 | 疑似(整模块 501 下架，硬编码演示数据未接真实源) | 竞品赢单率分析；经 `sales/__init__.py` 挂载到 `/competitor` 但已止血 |
| `endpoints/cost_collection.py` | cost-finance | 1 | 9 | 无 | 无 | 兼容 re-export，仅 `from .cost_endpoints.collection import router`；`/cost-collection` 挂载 |
| `endpoints/cost_endpoints/` | cost-finance | 5 | 1026 | bom-material, production, procurement, project, performance-hr | 无 | 成本归集/偏差分析/人工成本明细/报价实际对比的真实实现；由多个顶层兼容文件 re-export |
| `endpoints/cost_variance_analysis.py` | cost-finance | 1 | 9 | 无 | 无 | 兼容 re-export → `cost_endpoints.variance_analysis`；`/cost-variance` 挂载 |
| `endpoints/costs.py` | cost-finance | 1 | 448 | project | 疑似(未被 api.py 或任何位置挂载/引用) | 旧 `/costs/` 兼容层，转发到项目成本服务；活实现为 448 行但无引用者 |
| `endpoints/culture_wall/` | performance-hr | 4 | 558 | 无 | 无 | 文化墙汇总/内容/个人目标；`/culture-wall` 挂载 |
| `endpoints/culture_wall_config.py` | performance-hr | 1 | 187 | 无 | 无 | 文化墙配置 CRUD；`/culture-wall-config` 挂载 |
| `endpoints/customer_360.py` | sales | 1 | 675 | project | 无 | 客户 360 画像（交互史/决策链/健康度），对接真实库；经 `sales/__init__.py` 挂载 `/customer-360` |
| `endpoints/customers/` | sales | 4 | 517 | project | 无 | 客户 CRUD/关联数据/360 视图；Customer 模型在 project 包内；api.py 作为"关键模块"直接 `/customers` 挂载 |
| `endpoints/dashboard/` | analytics | 5 | 1214 | sales, ecn, production, procurement, project, performance-hr | 疑似(仅 `layout.py` 未被任何 include，dead) | `__init__` 仅挂 cost_dashboard(`/dashboard/cost`)；stats/unified 经同名兼容文件另行挂载；layout.py 无引用者 |
| `endpoints/dashboard_stats.py` | analytics | 1 | 9 | 无 | 无 | 兼容 re-export → `dashboard/stats`（按角色的工作台统计）；api.py 关键模块挂载 |
| `endpoints/dashboard_unified.py` | analytics | 1 | 9 | 无 | 无 | 兼容 re-export → `dashboard/unified`（统一工作台聚合入口）；api.py 关键模块挂载 |
| `endpoints/data_import_export/` | platform-file | 10 | 1326 | project, bom-material, performance-hr, strategy-pmo, analytics | 无 | 通用导入导出引擎（模板/预览/校验/上传/项目·任务·工时·工作量导出）；`/data-import-export` 挂载 |
| `endpoints/departments/` | platform-auth | 1 | 93 | project | 无 | 部门维度视图（部门项目/工作量/工时），复用 ProjectCore/Resource 服务；`/departments` 挂载 |
| `endpoints/documents/` | project | 3 | 533 | project | 无 | 项目文档 CRUD/下载/版本/删除（ProjectDocument、Machine）；`/documents` 挂载；实体属 project，通用能力借 platform-file 的 FileUploadService |
| `endpoints/ecn/` | ecn | 21 | 4852 | bom-material, procurement, production | 无 | 工程变更全套：核心 CRUD/评估/审批/任务/状态机/类型/影响(BOM/物料/成本)/RCA/知识库/责任分摊/统计/集成；`analysis.py` 二次聚合 bom_impact 等 5 文件；全部经 `ecn/__init__` 挂载 |
| `endpoints/ecn_bom.py` | ecn | 1 | 21 | 无 | 疑似(三个 import 目标 `.ecnbom`/`.common.ecn_bom`/`.admin.ecn_bom` 均不存在，回退为空 APIRouter) | 兼容 shim，被 api.py 挂载但 router 为空 no-op |

## 异常发现

- **禁用/止血 stub（挂载但无实际功能）**：
  - `change_impact.py`：顶层文件为禁用 shim（全 501），且**未被 api.py 挂载**；活的是 `endpoints/projects/change_impact.py`（api.py 1065-1066 行注册 `/project-change-impacts`）。两者同名易混淆。
  - `competitor_analysis.py`：578 行但整模块 501 下架（自述"硬编码演示数据未接真实源"），经 sales 包仍挂载在 `/competitor`。
  - `ecn_bom.py`：三处 fallback import 路径全部不存在（`ecnbom.py`/`common/ecn_bom.py`/`admin/ecn_bom.py` 均无此文件），最终 router 为空；被 api.py 挂载但无任何路由。

- **死代码（未挂载/无引用）**：
  - `costs.py`（448 行）：旧 `/costs/` 兼容转发层，全项目搜索无 `endpoints.costs` 的 import/include，未进入 api.py 生效路由链。
  - `dashboard/layout.py`（172 行，用户仪表盘布局自定义）：`dashboard/__init__.py` 只 include 了 cost_dashboard，全项目无 `dashboard.layout` 引用者，路由从未被挂载。

- **兼容 re-export 文件群（活着但是薄壳，重构时可合并回子包）**：`cost_collection.py`、`cost_variance_analysis.py`、`labor_cost_detail.py`、`quote_actual_compare.py` 均只做 `from .cost_endpoints.* import router`；`dashboard_stats.py`、`dashboard_unified.py` 只做 `from .dashboard.* import router`。真实实现全在 `cost_endpoints/`、`dashboard/` 子包内，顶层同名 .py 仅为 api.py 提供导入锚点。

- **重复挂载（同一 router 挂多前缀，非死代码但需留意）**：`business_support/__init__.py` 将 `contract_review.router` 同时挂到 `/contract-review` 和 `/contracts`，`payment_reminders.router` 同时挂到 `/payment-reminder` 和 `/payment-reminders`。

- **放错位置/域归属存疑**：
  - `documents/`：实体是 project 域的 ProjectDocument/Machine，但目录平铺在 endpoints 顶层且复用 platform-file 的 FileUploadService；建议归 project。
  - `departments/`：目录名像 platform-auth（组织架构），但实现完全是"部门维度的项目/工时/工作量视图"，重度依赖 project 服务；重构时需决定归 platform-auth 还是 project 的部门视图。
  - `customers/` 与 `customer_360.py`：客户属 sales/CRM 语义，但 Customer 模型物理上在 `app/models/project` 包内——models 层与 endpoints 层的域划分不一致。

- **api.py 中的注释掉的死注册**：`sales_regions`/`sales_targets`/`sales_teams`（1206/1217/1228 行）在 api.py 中被注释，属历史遗留（不在本范围内，附带记录）。

- 多租户（tenant_id）检查：本范围为 endpoints，不含建表定义，未做 tenant 字段核查（属 models 扫描范围）。