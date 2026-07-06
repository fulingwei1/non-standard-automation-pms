| 路径 | 域 | 文件数 | 总行数 | 跨域依赖 | 死代码嫌疑 | 备注 |
|------|----|-------|-------|---------|-----------|------|
| app/api/v1/endpoints/_shared/ | analytics | 2 | 253 | 依赖 report_framework | 无 | unified_reports.py 提供统一报表路由工厂 create_unified_report_router，被 report_center/unified.py 与 reports/unified.py 复用（生成 json/pdf/excel/word 报告） |
| app/api/v1/endpoints/acceptance/ | acceptance | 21 | 3286 | performance-hr(services.bonus BonusCalculator，见 bonus_trigger.py)、analytics(report_framework)、platform-auth(data_scope) | 无 | 验收管理主域：验收模板/验收单CRUD/检查项/流程/问题/签字/报告/客户文件上传；bonus_trigger.py 手动触发验收关联奖金计算。api.py 去前缀裸挂 |
| app/api/v1/endpoints/account_unlock.py | platform-auth | 1 | 96 | 无 | 无 | 账号锁定管理端点（查询/解锁被锁账号），挂 /account-unlock |
| app/api/v1/endpoints/admin_attendance.py | performance-hr | 1 | 129 | 无 | 无 | /admin/attendance 兼容路由；尚无生产考勤域，显式返回空态而非合成考勤/请假/打卡数据 |
| app/api/v1/endpoints/admin_compat.py | 待定 | 1 | 517 | 无 | 无 | 行政管理（用品申领/车辆/资产/费用）真库 CRUD+审批扣库存；属行政办公，不在价值链业务域，暂归待定（勉强近 performance-hr 的HR/行政） |
| app/api/v1/endpoints/admin_stats.py | analytics | 1 | 188 | 无 | 无 | 管理端统计路由 + runtime 采集器（含系统运行时指标收集，该部分偏 platform-infra 监控），挂 /admin |
| app/api/v1/endpoints/advantage_products/ | presale | 5 | 643 | platform-file(import_export_engine) | 无 | 优势产品目录：类别/产品CRUD、Excel导入、产品匹配检查（售前方案匹配用），挂 /advantage-products |
| app/api/v1/endpoints/after_sales.py | aftersales | 1 | 1294 | 无 | 无 | 售后服务：客户反馈/维修保养/技术支持工单管理，挂 /after-sales |
| app/api/v1/endpoints/ai_admin.py | platform-ai | 1 | 210 | 无 | 无 | 管理员可视化配置AI接入(Key/BaseURL/模型/超时)+测试连接，挂 /admin/ai-config |
| app/api/v1/endpoints/ai_advanced.py | platform-ai | 1 | 95 | 无 | 无 | 差异化AI：多模态图纸/照片理解(qwen视觉)+对内RAG知识问答，挂 /ai-advanced |
| app/api/v1/endpoints/ai_copilot.py | platform-ai | 1 | 263 | 无 | 无 | 通用AI Copilot：命令栏/语义搜索/日周报/摘要/翻译/邮件代写等11项提效能力，挂 /ai-copilot |
| app/api/v1/endpoints/ai_delivery.py | project | 1 | 80 | 无 | 无 | B3交付风险预警：扫执行中项目按进度/工期/缺料预测延期+AI归因（业务专属AI归 project），挂 /ai-delivery |
| app/api/v1/endpoints/ai_engineering.py | engineering | 1 | 378 | 无 | 无 | 工程/售后类AI：BOM智能选型/售后故障诊断/配置式设计（业务专属AI），挂 /ai-eng |
| app/api/v1/endpoints/ai_feedback.py | platform-ai | 1 | 69 | 无 | 无 | AI产出反馈闭环：采纳/驳回记录+采纳率统计，挂 /ai-feedback |
| app/api/v1/endpoints/ai_jobs.py | platform-ai | 1 | 134 | 无 | 无 | AI后台任务：提交重AI生成+轮询状态/结果，挂 /ai-jobs |
| app/api/v1/endpoints/ai_modules.py | engineering | 1 | 144 | 无 | 无 | M1标准模块库：AI从历史BOM挖可复用模块（支撑配置式设计/模块级报价），挂 /ai-modules |
| app/api/v1/endpoints/ai_more.py | 待定 | 1 | 86 | ecn、sales | 无 | 跨多域AI：ECN影响预测(ecn)+回款催收(sales)+投标智能(presale/sales)，跨域难单归，挂 /ai-more |
| app/api/v1/endpoints/ai_planning.py | 待定 | 1 | 172 | production、engineering、strategy-pmo、presale | 无 | 跨多域AI收尾批：排产工时/质量异常/行业分析/战略规划/经营计划分解/工程师匹配/售前ROI/产能/竞品，挂 /ai-planning |
| app/api/v1/endpoints/ai_sales_assistant.py | sales | 1 | 102 | 无 | 无 | AI销售助手：话术推荐/方案生成/竞品分析/谈判建议/流失预警；经 sales/__init__.py 挂 /sales/ai（非 api.py 顶层注册） |
| app/api/v1/endpoints/ai_strategy.py | strategy-pmo | 1 | 23 | 无 | 疑似(legacy shim，全仓零引用且未被 api.py 挂载) | Legacy AI strategy route shim，死代码 |
| app/api/v1/endpoints/alerts/ | platform-notify | 11 | 2303 | project | 无 | 预警/异常管理：规则/记录/通知/异常事件/统计/订阅/导出（services.alert.* + notification），api.py 裸挂 |
| app/api/v1/endpoints/analytics/ | analytics | 4 | 1480 | project(ProjectAnalyticsService/models.project)、performance-hr(staff_matching)、platform-auth(organization) | 无 | 组织/PMO维度分析：项目健康/跨项目进度/工作量概览/成本汇总/资源冲突/技能矩阵，挂 /analytics |
| app/api/v1/endpoints/approval_submit_guard.py | platform-approval | 1 | 21 | 无 | 无 | 审批提交守卫 reject_all_failed_submit（批量提交无成功实例即拒绝），被 sales/acceptance/purchase/outsourcing workflow 复用；非路由，helper |
| app/api/v1/endpoints/approvals/ | platform-approval | 7 | 2232 | 无 | 无 | 统一审批系统：模板/实例/任务/待办(pending_refactored)/代理人/legacy兼容，挂 /approvals |
| app/api/v1/endpoints/assembly_kit/ | inventory-kitting | 16 | 2317 | bom-material(bom_attributes)、procurement(purchase.in_transit)、platform-notify(wechat_alert) | 无 | 装配套件/齐套分析：阶段/物料映射/BOM属性/齐套分析/缺料预警/排产/看板/成套率，api.py 裸挂 |
| app/api/v1/endpoints/audit_pack.py | presale | 1 | 148 | 无 | 无 | 验厂资料：销售上传客户验厂清单→总监审批→AI自动准备资料包，挂 /audit-packs（api.py 于 presale-ai 段注册） |
| app/api/v1/endpoints/audits.py | platform-auth | 1 | 109 | 无 | 无 | 权限审计日志查询API，挂 /audits |
| app/api/v1/endpoints/auth.py | platform-auth | 1 | 588 | 无 | 无 | 认证核心（登录/令牌等）；在 main.py 优先注册 /api/v1/auth，先于 stub 兜底 |
| app/api/v1/endpoints/backup.py | platform-infra | 1 | 102 | 无 | 无 | 备份管理API（BackupService），挂 /backup |
| app/api/v1/endpoints/base_crud_router.py | platform-infra | 1 | 224 | 无 | 疑似(全仓无 importer，仅 _sync 版被使用) | 通用CRUD路由工厂(async版)，被 base_crud_router_sync.py 取代，死代码 |
| app/api/v1/endpoints/base_crud_router_sync.py | platform-infra | 1 | 305 | 无 | 无 | 通用CRUD路由工厂 create_crud_router_sync(sync版)，被 customers/suppliers/materials 复用；非路由，helper |
| app/api/v1/endpoints/best_practice.py | 待定 | 1 | 170 | bom-material、procurement、inventory-kitting | 疑似(3个router均未被任何 api*.py 挂载，全仓无 importer) | 行业最佳实践P0：ABC物料分级/供应商升降级/缺料升级/齐套目标配置；未挂载死代码 |
| app/api/v1/endpoints/bom/ | bom-material | 12 | 1767 | procurement(purchase.utils generate_request_no)、cost-finance(cost_collection_service)、platform-file(import_export_engine)、platform-auth(data_scope) | 无 | BOM管理：机器BOM/明细/条目/版本/发布/审批/导出/生成PR/导入/模板/列表，挂 /bom |
| app/api/v1/endpoints/bom_cost_check.py | cost-finance | 1 | 52 | bom-material | 无 | BOM成本检查清单(手册Sheet3)，GET /projects/{id}/bom-cost-check，挂 /projects（api.py 于 presale-ai 段注册） |
| app/api/v1/endpoints/bonus/ | performance-hr | 17 | 2089 | presale(PresaleSupportTicket)、project(Project/ProjectMilestone)、sales(Contract) | 无 | 奖金管理：规则/计算/销售奖金核算/发放/团队/我的奖金/统计/分配表(allocation_sheets)，api.py 裸挂 |

## 异常发现

**死代码群（未被生效路由 api.py 挂载 / 无引用）：**
- `ai_strategy.py` — Legacy AI strategy route shim，全仓零引用，未在任何 api*.py 挂载。确认死代码。
- `best_practice.py` — 定义 material_router/supplier_router/project_router（ABC物料分级、供应商升降级、缺料升级、齐套目标），三者均未在任何 api*.py 注册，全仓无 importer。确认死代码。
- `base_crud_router.py`（async 版）— 无任何 importer；实际在用的是 `base_crud_router_sync.py`（被 customers/suppliers/materials 引用）。async 版为并存尸体。

**重复/并存实现：**
- `base_crud_router.py`（async，尸体）vs `base_crud_router_sync.py`（sync，活）— 同一通用CRUD路由工厂的两个版本，仅 sync 版存活。

**放错位置 / 归域存疑：**
- `admin_compat.py` — 行政办公资产管理（用品/车辆/资产/费用 CRUD+审批），不属非标自动化价值链任一业务域，暂归待定。
- `ai_more.py`、`ai_planning.py` — 业务专属AI但单文件横跨多个业务域（ECN/回款/投标 及 排产/质量/战略/售前/竞品等），无法干净归入单一域，暂归待定；重构时建议按功能点拆分到各业务域。
- `admin_stats.py` — 混合了经营统计（analytics）与 runtime 指标采集器（platform-infra 监控）两种职责。
- `audit_pack.py` / `bom_cost_check.py` — 业务上属 presale/成本，但 api.py 中被塞进「预售AI」try 块内注册（与 presale-ai 强耦合，任一 import 失败会整块失活，STRICT 模式下会启动报错）。

**非顶层但值得注意：**
- `ai_sales_assistant.py` 不由 api.py 顶层注册，而是经 `sales/__init__.py` 挂到 `/sales/ai`——归 sales 域，重构时随 sales 走。
- `approval_submit_guard.py`、`base_crud_router_sync.py`、`_shared/unified_reports.py` 均为被跨模块复用的 helper（非独立挂载路由），拆分时应作为共享工具随对应平台层下沉。

**多租户（tenant_id）检查：** 本范围为 endpoints，未逐表核验 models，tenant_id 情况未核实（应由 models 扫描 agent 覆盖）。
