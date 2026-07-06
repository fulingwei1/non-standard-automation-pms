# 归域清单：app/api/v1/endpoints（rd_project/ 到 workload_compat.py，不含 sales/）

活跃路由聚合文件：`app/api/v1/api.py`（main.py 中 `from app.api.v1.api import api_router` 并挂载）。auth 在 main.py 优先注册；sessions/2fa 在 api.py 注册。

| 路径 | 域 | 文件数 | 总行数 | 跨域依赖 | 死代码嫌疑 | 备注 |
|---|---|---|---|---|---|---|
| rd_project/ | engineering | 9 | 1410 | project, cost-finance, performance-hr | 无 | 研发项目 API 模块化包：分类/立项(CRUD/审批/结项)/费用类型/费用归集/分摊规则/工作日志/文档；挂 /rd-projects |
| rd_project_aliases.py | engineering | 1 | 17 | (同域 rd_project) | 无 | 给前端无重定向别名路由，复用 rd_project.initiation.get_rd_projects；已挂载 |
| relationship_maturity.py | sales | 1 | 589 | sales | 无 | 客户关系成熟度评分接口(Customer/Opportunity/relationship_scoring_service)；经 sales/__init__ 挂 /sales/relationship（非未挂载）|
| report.py | analytics | 1 | 605 | performance-hr | 无 | 报表模板管理(ReportService/ReportExcelService/models.report)，HR/Admin 权限；挂 /report |
| report_center/ | analytics | 12 | 2198 | procurement(outsourcing/vendor), project, sales, performance-hr(timesheet) | 无 | 报表中心：BI/配置/生成/模板/研发费用报表/项目自动报表/统一报告引擎(report_framework)；挂 /report-center |
| reports/ | analytics | 2 | 67 | 无 | 无 | 仅 re-export unified.py，基于 _shared.unified_reports 的统一报告路由；api.py 直挂 reports.unified |
| requirement_extraction.py | presale | 1 | 190 | project | 无 | 项目需求提取兼容路由(ProjectRequirement/EngineerRecommendation)；挂 /requirement-extraction |
| resource_overview.py | performance-hr | 1 | 23 | 无 | 疑似(已禁用 shim，501，未挂载，指向 /pmo/resource-overview) | 遗留资源总览占位，全部方法返回 501 |
| resource_scheduling.py | performance-hr | 1 | 33 | 无 | 疑似(已禁用 shim，501，未挂载，指向 /engineer-scheduling) | 遗留资源调度占位，返回 501 |
| roles.py | platform-auth | 1 | 692 | 无 | 无 | 角色管理 API(RoleManagementService/RoleService)；挂 /roles |
| sales_regions.py | sales | 1 | 27 | (回退 .sales) | 疑似(兼容 shim，api.py 中已注释掉未挂载) | try 导入链回退到 sales 包 router；重复挂载已废弃 |
| sales_targets.py | sales | 1 | 27 | (回退 .sales) | 疑似(兼容 shim，api.py 中已注释掉未挂载) | 同上，销售目标兼容 shim，未挂载 |
| sales_teams.py | sales | 1 | 27 | (回退 .sales) | 疑似(兼容 shim，api.py 中已注释掉未挂载) | 同上，销售团队兼容 shim，未挂载 |
| schedule_generation.py | project | 1 | 234 | 无 | 无 | 排程生成兼容路由(ScheduleGenerationService)；挂 /schedule-generation |
| schedule_optimization.py | project | 1 | 67 | 无 | 疑似(所有 try 导入失败，实际只提供 placeholder 返回空数据) | 排程优化 shim，挂 /schedule-optimization 但只返回占位/空 BOM/空采购 |
| sessions.py | platform-auth | 1 | 125 | 无 | 无 | 会话管理(SessionService)，列出/撤销会话；api.py 挂 /auth |
| settlements.py | cost-finance | 1 | 298 | sales(Contract), project | 无 | 项目结算兼容接口(ProjectCost/Contract/cost_basis)；挂载(prefix="") |
| stage_templates.py | project | 1 | 111 | 无 | 疑似(所有 try 导入失败，回退 placeholder 返回硬编码假模板数据) | 阶段模板 shim，挂 /stage-templates 但返回样例假数据 |
| stub_endpoints.py | platform-infra | 1 | 83 | 无 | 无 | 通配兜底 stub handler，未实现前端 API 的 404/501 兜底；受 ENABLE_STUB_ENDPOINTS 条件挂载 |
| suppliers.py | procurement | 1 | 213 | bom-material(material) | 无 | 供应商 CRUD(VendorService/MaterialSupplier)；挂 /suppliers |
| team_generation.py | project | 1 | 240 | project | 无 | AI 自动组队兼容路由(ProjectTeamPlan/TeamGenerationService)；挂 /team-generation |
| tenants.py | platform-auth | 1 | 172 | 无 | 无 | 租户管理(TenantService)，超管专用；挂 /tenants |
| timesheet_reminders.py | performance-hr | 1 | 27 | 无 | 疑似(兼容 shim：try 回退 `from .timesheet import router`，实际把整个 timesheet 包 router 重挂到 /timesheet-reminders) | 工时提醒 shim，已挂载但路由内容=timesheet 全量，命名误导 |
| two_factor.py | platform-auth | 1 | 384 | 无 | 无 | 2FA 设置/校验/恢复码；api.py 挂 /auth/2fa |
| win_rate_prediction.py | sales | 1 | 704 | sales | 无 | 赢单率预测模型接口(仅 deps/security/User，无 service 层)；经 sales/__init__ 挂 /sales/win-rate（非未挂载）|
| workload_compat.py | performance-hr | 1 | 202 | project(Task) | 无 | 资源负荷看板兼容接口(Timesheet/Task/Department)；挂 /workload |
| scheduler/ | platform-infra | 4 | 748 | 无 | 无 | 调度器管理(scheduler_config)：状态/手动触发/指标(JSON+Prometheus)/定时任务配置；挂 /scheduler |
| service/ | aftersales | 22 | 3767 | ecn, project | 无 | 客服服务：工单/记录/沟通/满意度调查/调查模板/知识库/知识特性/统计(sla_service/ticket_assignment)；挂 /service |
| shortage/ | inventory-kitting | 13 | 3202 | bom-material(material), procurement(purchase/vendor), project | 无 | 缺料管理三层：detection(预警)/handling(处理)/analytics(统计)+smart_alerts(智能预警)；挂 /shortage(+/shortage/smart-alerts) |
| sla/ | aftersales | 4 | 565 | 无 | 无 | SLA 管理：策略/监控记录/统计；挂 /sla |
| solution_credits/ | presale | 5 | 545 | 无 | 无 | 方案生成积分：用户端查询/管理员配置/内部扣退(solution_credit_service，模型在 models.user)；挂 /solution-credits |
| staff_matching/ | performance-hr | 8 | 1327 | project | 无 | AI 人员智能匹配：标签/评估/画像/绩效/用人需求/匹配/看板；挂 /staff-matching |
| standard_costs/ | cost-finance | 5 | 1028 | project | 无 | 标准成本库：CRUD/项目集成/批量导入/历史(budget/standard_cost)；挂 /standard-costs |
| strategy/ | strategy-pmo | 9 | 2060 | 无 | 无 | 战略管理：战略/CSF/KPI/年度重点工作/目标分解/审视/同比分析；挂 /strategy |
| task_center/ | project | 15 | 1971 | sales(sales_reminder) | 无 | 任务中心：概览/我的任务/详情/增改/完成/转派/驳回/评论/批量(task_progress_service)；挂 /task-center |
| technical_review/ | engineering | 7 | 1248 | project | 无 | 技术评审：评审主表/参与人/材料/检查项/问题(design_review_sync)；挂载(prefix="") |
| technical_spec/ | engineering | 5 | 503 | bom-material(material), procurement(purchase), project | 无 | 技术规格：要求 CRUD/匹配检查/提取(spec_match_service)；挂 /technical-spec 与 /technical-specs(重复双挂) |
| template_configs/ | project | 3 | 533 | 无 | 无 | 项目模板配置：configs CRUD + apply(preset_stage_templates)；挂 /template-configs |
| timesheet/ | performance-hr | 12 | 2540 | project | 疑似(analytics.py 因 Pydantic 递归错误被 __init__ 注释禁用) | 工时管理：记录/待办/周月/统计/质量/报表/同步/工作流；挂 /timesheet |
| users/ | platform-auth | 7 | 1404 | project, engineering(rd_project), performance-hr(timesheet) | 无 | 用户管理：CRUD(重构版)/同步/工时分配/批量导入(tenant_service)；挂 /users |
| warehouse/ | inventory-kitting | 5 | 1118 | 无 | 无 | 仓储管理：出入库/库位/预警/盘点；挂 /warehouse |

## 异常发现

- **兼容 shim 群（“猜测导入位置+占位回退”老模式）**：`sales_regions.py` / `sales_targets.py` / `sales_teams.py` / `stage_templates.py` / `schedule_optimization.py` / `timesheet_reminders.py`。均为 try 多路径导入失败后回退 placeholder 的历史产物：
  - sales_regions/targets/teams：api.py 中挂载代码已注释（去重，回退到 sales 包），实为死代码 shim。
  - stage_templates：已挂 /stage-templates 但所有导入失败，实际返回**硬编码假模板数据**（STD_9_STAGE 样例），生产隐患。
  - schedule_optimization：已挂 /schedule-optimization，实际只返回占位/空结果。
  - timesheet_reminders：已挂 /timesheet-reminders，但 `from .timesheet import router` 成功 → **把整个 timesheet 包 router 重复挂载**到该前缀，命名与内容不符。
- **已禁用的遗留 shim**：`resource_overview.py`（→ /pmo/resource-overview）、`resource_scheduling.py`（→ /engineer-scheduling），全部方法返回 501，未在 api.py 挂载。可安全删除。
- **“未挂载”误判澄清**：`relationship_maturity.py`、`win_rate_prediction.py` 在 api.py 中查不到注册，但均由 `sales/__init__.py`（本次扫描范围外的 sales 子包）import 并分别挂到 `/sales/relationship`、`/sales/win-rate`，属**活代码**，非死代码。
- **报表实现三处并存**：`report.py`(/report, ReportService+Excel)、`reports/`(/reports, _shared.unified_reports)、`report_center/`(/report-center, report_framework/YAML 引擎)——三套报表入口/引擎并存，重构时需收敛，注意 report_center/unified.py 与 reports/unified.py 都基于同一 `_shared.unified_reports` 工厂。
- **重复双挂载**：`technical_spec` 在 api.py 同时挂 `/technical-spec` 和 `/technical-specs`（同一 router 两个前缀）。
- **被禁用的子模块**：`timesheet/analytics.py` 因 Pydantic 递归错误在 `timesheet/__init__.py` 中被注释掉，未注册（存在但不生效）。
- **平台层反向依赖业务域**：`users/`(platform-auth) import 了 project / rd_project / timesheet 模型（time_allocation 统计）；`report.py`(analytics) 依赖 performance-hr 的 ReportService/HR 权限——重构拆分时需处理平台层→业务域的反向耦合。
- **win_rate_prediction.py**（704 行）无任何 service 层，全部逻辑内联在 endpoint（仅依赖 deps/security/User），疑似含内联 mock/硬编码，建议核查数据真实性（未逐行核实）。
- 多租户 tenant_id 检查：本次为 endpoints 扫描，未逐表核查表结构，此项交 models 扫描 agent。
