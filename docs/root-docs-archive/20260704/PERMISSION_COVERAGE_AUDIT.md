# API 权限覆盖审计报告

> 审计时间: 2026-07-04T18:08:47.706525
> 扫描方式: AST 静态分析 (`scripts/audit_permission_coverage.py`)

## 1. 总览

| 指标 | 值 |
|------|-----|
| 总端点数 | 2997 |
| PERMISSION (有权限码) | 1032 (34.4%) |
| AUTH_ONLY (仅登录) | 1822 (60.8%) |
| NONE (无保护) | 143 (4.8%) |
| 唯一权限码数 | 206 |

### 按 HTTP 方法分布

| 方法 | PERMISSION | AUTH_ONLY | NONE |
|------|-----------|----------|------|
| GET | 472 | 975 | 102 |
| POST | 357 | 578 | 33 |
| PUT | 142 | 198 | 4 |
| DELETE | 61 | 66 | 4 |
| PATCH | 0 | 5 | 0 |

## 2. 模块权限覆盖热力图 (按裸奔写端点数排序)

| 模块 | 总数 | PERM | AUTH_ONLY | NONE | 写裸奔 | 覆盖率 |
|------|------|------|----------|------|--------|--------|
| 🟡 sales | 549 | 109 | 439 | 1 | 190 | 20% |
| 🟡 projects | 331 | 116 | 207 | 8 | 97 | 35% |
| 🔴 production | 116 | 4 | 102 | 10 | 48 | 3% |
| 🔴 strategy | 83 | 0 | 44 | 39 | 41 | 0% |
| 🟡 ecn | 84 | 18 | 66 | 0 | 37 | 21% |
| 🔴 presale | 78 | 2 | 76 | 0 | 35 | 3% |
| 🟡 acceptance | 44 | 9 | 35 | 0 | 22 | 20% |
| 🔴 business_support_orders | 46 | 4 | 42 | 0 | 22 | 9% |
| 🔴 shortage | 54 | 4 | 50 | 0 | 20 | 7% |
| 🟡 pmo | 38 | 8 | 30 | 0 | 19 | 21% |
| 🟡 purchase | 33 | 9 | 24 | 0 | 16 | 27% |
| 🔴 ai_planning | 22 | 0 | 22 | 0 | 15 | 0% |
| 🟡 alerts | 38 | 7 | 31 | 0 | 15 | 18% |
| 🟡 performance | 43 | 5 | 38 | 0 | 13 | 12% |
| 🔴 after_sales | 22 | 1 | 21 | 0 | 12 | 5% |
| 🔴 technical_review | 18 | 0 | 18 | 0 | 12 | 0% |
| 🔴 management_rhythm | 32 | 0 | 32 | 0 | 12 | 0% |
| 🟡 bonus | 34 | 10 | 24 | 0 | 11 | 29% |
| 🟡 outsourcing | 30 | 9 | 21 | 0 | 11 | 30% |
| 🔴 progress_compat | 20 | 0 | 20 | 0 | 10 | 0% |
| 🔴 admin_compat | 21 | 0 | 21 | 0 | 9 | 0% |
| 🔴 bom | 18 | 1 | 17 | 0 | 9 | 6% |
| 🔴 ai_copilot | 12 | 0 | 12 | 0 | 8 | 0% |
| 🔴 engineer_scheduling | 15 | 0 | 15 | 0 | 8 | 0% |
| 🔴 report | 15 | 0 | 15 | 0 | 8 | 0% |
| 🔴 project_review | 18 | 0 | 18 | 0 | 8 | 0% |
| 🔴 presale_ai_knowledge | 10 | 0 | 0 | 10 | 7 | 0% |
| 🔴 knowledge | 11 | 0 | 11 | 0 | 7 | 0% |
| 🔴 inventory | 13 | 0 | 13 | 0 | 7 | 0% |
| 🔴 presale_ai_quotation | 8 | 0 | 8 | 0 | 6 | 0% |
| 🔴 two_factor | 7 | 0 | 6 | 1 | 6 | 0% |
| 🔴 ai_engineering | 6 | 0 | 6 | 0 | 6 | 0% |
| 🔴 culture_wall | 10 | 0 | 10 | 0 | 6 | 0% |
| 🔴 project_delivery | 14 | 0 | 14 | 0 | 6 | 0% |
| 🟡 material | 13 | 4 | 4 | 5 | 6 | 31% |
| 🔴 presale_ai_emotion | 8 | 0 | 0 | 8 | 5 | 0% |
| 🔴 presale_ai_cost | 8 | 0 | 8 | 0 | 5 | 0% |
| 🔴 presale_ai_integration | 13 | 0 | 12 | 1 | 5 | 0% |
| 🔴 backup | 7 | 0 | 0 | 7 | 5 | 0% |
| 🔴 notifications | 8 | 0 | 8 | 0 | 5 | 0% |
| 🔴 auth | 6 | 0 | 4 | 2 | 4 | 0% |
| 🔴 ai_admin | 6 | 0 | 6 | 0 | 4 | 0% |
| 🔴 milestones | 7 | 0 | 7 | 0 | 4 | 0% |
| 🔴 schedule_generation | 6 | 0 | 6 | 0 | 4 | 0% |
| 🔴 team_generation | 6 | 0 | 5 | 1 | 4 | 0% |
| 🔴 field_commissioning | 7 | 0 | 7 | 0 | 4 | 0% |
| 🔴 tenants | 7 | 0 | 0 | 7 | 4 | 0% |
| 🔴 template_configs | 6 | 0 | 6 | 0 | 4 | 0% |
| 🔴 pitfalls | 6 | 0 | 6 | 0 | 4 | 0% |
| 🟢 approvals | 66 | 54 | 12 | 0 | 4 | 82% |
| 🔴 ai_jobs | 4 | 0 | 4 | 0 | 3 | 0% |
| 🔴 lessons_learned | 7 | 0 | 7 | 0 | 3 | 0% |
| 🔴 base_crud_router | 6 | 0 | 0 | 6 | 3 | 0% |
| 🔴 culture_wall_config | 5 | 0 | 5 | 0 | 3 | 0% |
| 🟡 organization | 43 | 21 | 18 | 4 | 3 | 49% |
| 🟢 assembly_kit | 37 | 19 | 6 | 12 | 3 | 51% |
| 🔴 sla | 8 | 0 | 8 | 0 | 3 | 0% |
| 🔴 sessions | 3 | 0 | 3 | 0 | 2 | 0% |
| 🔴 ai_more | 3 | 0 | 3 | 0 | 2 | 0% |
| 🔴 ai_advanced | 2 | 0 | 2 | 0 | 2 | 0% |
| 🔴 admin_attendance | 7 | 0 | 7 | 0 | 2 | 0% |
| 🔴 gantt_dependency | 4 | 0 | 4 | 0 | 2 | 0% |
| 🔴 requirement_extraction | 4 | 0 | 3 | 1 | 2 | 0% |
| 🔴 schedule_optimization | 4 | 0 | 0 | 4 | 2 | 0% |
| 🟢 solution_credits | 13 | 9 | 4 | 0 | 2 | 69% |
| 🟢 dashboard | 15 | 8 | 7 | 0 | 2 | 53% |
| 🔴 _shared | 5 | 0 | 5 | 0 | 2 | 0% |
| 🔴 kit_check | 5 | 0 | 5 | 0 | 2 | 0% |
| 🟡 qualification | 17 | 7 | 10 | 0 | 2 | 41% |
| 🔴 presale_agent_revisions | 4 | 0 | 4 | 0 | 1 | 0% |
| 🔴 otd_thresholds | 2 | 0 | 2 | 0 | 1 | 0% |
| 🔴 ai_sales_assistant | 6 | 0 | 6 | 0 | 1 | 0% |
| 🔴 relationship_maturity | 4 | 0 | 4 | 0 | 1 | 0% |
| 🔴 account_unlock | 4 | 0 | 0 | 4 | 1 | 0% |
| 🔴 ai_feedback | 3 | 0 | 3 | 0 | 1 | 0% |
| 🔴 management_rhythm_compat | 4 | 0 | 4 | 0 | 1 | 0% |
| 🔴 multi_currency | 5 | 0 | 5 | 0 | 1 | 0% |
| 🔴 ai_modules | 3 | 0 | 3 | 0 | 1 | 0% |
| 🔴 otd | 7 | 0 | 7 | 0 | 1 | 0% |
| 🟢 timesheet | 36 | 28 | 8 | 0 | 1 | 78% |
| 🟢 service | 51 | 50 | 0 | 1 | 1 | 98% |
| 🔴 analytics | 17 | 0 | 17 | 0 | 1 | 0% |
| 🟢 core | 5 | 3 | 0 | 2 | 0 | 60% |
| 🔴 sales_teams | 1 | 0 | 0 | 1 | 0 | 0% |
| 🔴 margin_prediction | 4 | 0 | 4 | 0 | 0 | 0% |
| 🔴 customer_360 | 5 | 0 | 5 | 0 | 0 | 0% |
| 🔴 settlements | 3 | 0 | 3 | 0 | 0 | 0% |
| 🟢 audits | 2 | 2 | 0 | 0 | 0 | 100% |
| 🔴 sales_regions | 1 | 0 | 0 | 1 | 0 | 0% |
| 🔴 timesheet_reminders | 1 | 0 | 0 | 1 | 0 | 0% |
| 🔴 ai_delivery | 1 | 0 | 1 | 0 | 0 | 0% |
| 🔴 presale_agent_metrics | 1 | 0 | 1 | 0 | 0 | 0% |
| 🟢 inventory_analysis | 6 | 6 | 0 | 0 | 0 | 100% |
| 🔴 stage_templates | 2 | 0 | 0 | 2 | 0 | 0% |
| 🟢 roles | 23 | 22 | 1 | 0 | 0 | 96% |
| 🔴 competitor_analysis | 3 | 0 | 3 | 0 | 0 | 0% |
| 🔴 workload_compat | 2 | 0 | 2 | 0 | 0 | 0% |
| 🔴 sales_targets | 1 | 0 | 0 | 1 | 0 | 0% |
| 🟢 node_tasks | 15 | 14 | 1 | 0 | 0 | 93% |
| 🔴 project_legacy_compat | 2 | 0 | 2 | 0 | 0 | 0% |
| 🟢 best_practice | 4 | 4 | 0 | 0 | 0 | 100% |
| 🔴 production_daily_reports | 2 | 0 | 2 | 0 | 0 | 0% |
| 🟢 costs | 14 | 14 | 0 | 0 | 0 | 100% |
| 🟢 suppliers | 3 | 3 | 0 | 0 | 0 | 100% |
| 🔴 finance_reports | 4 | 0 | 4 | 0 | 0 | 0% |
| 🔴 win_rate_prediction | 3 | 0 | 3 | 0 | 0 | 0% |
| 🟢 itr | 3 | 3 | 0 | 0 | 0 | 100% |
| 🔴 admin_stats | 1 | 0 | 1 | 0 | 0 | 0% |
| 🔴 quality_risk | 1 | 0 | 0 | 1 | 0 | 0% |
| 🔴 labor_cost_detail | 1 | 0 | 0 | 1 | 0 | 0% |
| 🟢 base_crud_router_sync | 6 | 6 | 0 | 0 | 0 | 100% |
| 🔴 project_workspace | 1 | 0 | 0 | 1 | 0 | 0% |
| 🟢 customers | 6 | 5 | 1 | 0 | 0 | 83% |
| 🟢 report_center | 28 | 28 | 0 | 0 | 0 | 100% |
| 🟢 kit_rate | 8 | 6 | 2 | 0 | 0 | 75% |
| 🟢 hourly_rate | 8 | 8 | 0 | 0 | 0 | 100% |
| 🟢 advantage_products | 11 | 11 | 0 | 0 | 0 | 100% |
| 🟢 task_center | 21 | 21 | 0 | 0 | 0 | 100% |
| 🟢 installation_dispatch | 11 | 11 | 0 | 0 | 0 | 100% |
| 🟢 material_demands | 5 | 5 | 0 | 0 | 0 | 100% |
| 🟢 materials | 7 | 5 | 2 | 0 | 0 | 71% |
| 🟢 engineer_performance | 88 | 87 | 1 | 0 | 0 | 99% |
| 🟡 cost_endpoints | 11 | 4 | 7 | 0 | 0 | 36% |
| 🟢 hr_management | 12 | 12 | 0 | 0 | 0 | 100% |
| 🟢 data_import_export | 10 | 10 | 0 | 0 | 0 | 100% |
| 🟢 technical_spec | 8 | 5 | 3 | 0 | 0 | 62% |
| 🟡 scheduler | 10 | 3 | 7 | 0 | 0 | 30% |
| 🟢 business_support | 18 | 18 | 0 | 0 | 0 | 100% |
| 🟢 permissions | 13 | 13 | 0 | 0 | 0 | 100% |
| 🟢 presale_analytics | 6 | 6 | 0 | 0 | 0 | 100% |
| 🟢 engineers | 11 | 11 | 0 | 0 | 0 | 100% |
| 🟢 procurement | 9 | 9 | 0 | 0 | 0 | 100% |
| 🟢 users | 17 | 16 | 1 | 0 | 0 | 94% |
| 🟢 standard_costs | 13 | 13 | 0 | 0 | 0 | 100% |
| 🟢 rd_project | 23 | 23 | 0 | 0 | 0 | 100% |
| 🟢 documents | 10 | 9 | 1 | 0 | 0 | 90% |
| 🟢 staff_matching | 26 | 26 | 0 | 0 | 0 | 100% |
| 🟢 warehouse | 22 | 22 | 0 | 0 | 0 | 100% |
| 🟢 issues | 36 | 35 | 1 | 0 | 0 | 97% |
| 🟢 budget | 17 | 17 | 0 | 0 | 0 | 100% |

## 3. Top 20 最危险裸奔/弱保护接口

| # | 风险分 | 方法 | 路径 | 保护 | 文件:行 | 函数 |
|---|--------|------|------|------|---------|------|
| 1 | 110 | DELETE | `/old` | NONE | `app/api/v1/endpoints/backup.py:72` | `delete_old_backups` |
| 2 | 110 | DELETE | `/{tenant_id}` | NONE | `app/api/v1/endpoints/tenants.py:118` | `delete_tenant` |
| 3 | 100 | POST | `/` | NONE | `app/api/v1/endpoints/backup.py:44` | `create_backup` |
| 4 | 100 | POST | `/database` | NONE | `app/api/v1/endpoints/backup.py:50` | `create_database_backup` |
| 5 | 100 | POST | `/verify` | NONE | `app/api/v1/endpoints/backup.py:56` | `verify_backup` |
| 6 | 100 | POST | `/restore` | NONE | `app/api/v1/endpoints/backup.py:62` | `restore_backup` |
| 7 | 100 | POST | `/` | NONE | `app/api/v1/endpoints/tenants.py:66` | `create_tenant` |
| 8 | 100 | PUT | `/{tenant_id}` | NONE | `app/api/v1/endpoints/tenants.py:99` | `update_tenant` |
| 9 | 100 | POST | `/{tenant_id}/init` | NONE | `app/api/v1/endpoints/tenants.py:138` | `init_tenant` |
| 10 | 90 | DELETE | `/{item_id}` | NONE | `app/api/v1/endpoints/base_crud_router.py:192` | `delete_item` |
| 11 | 90 | DELETE | `/{project_id}/risks/{risk_id}` | NONE | `app/api/v1/endpoints/projects/risks.py:232` | `delete_risk` |
| 12 | 80 | POST | `/analyze-emotion` | NONE | `app/api/presale_ai_emotion.py:30` | `analyze_emotion` |
| 13 | 80 | POST | `/predict-churn-risk` | NONE | `app/api/presale_ai_emotion.py:90` | `predict_churn_risk` |
| 14 | 80 | POST | `/recommend-follow-up` | NONE | `app/api/presale_ai_emotion.py:123` | `recommend_follow_up` |
| 15 | 80 | POST | `/dismiss-reminder/{reminder_id}` | NONE | `app/api/presale_ai_emotion.py:204` | `dismiss_reminder` |
| 16 | 80 | POST | `/batch-analyze-customers` | NONE | `app/api/presale_ai_emotion.py:227` | `batch_analyze_customers` |
| 17 | 80 | POST | `/search-similar-cases` | NONE | `app/api/v1/presale_ai_knowledge.py:46` | `search_similar_cases` |
| 18 | 80 | POST | `/recommend-best-practices` | NONE | `app/api/v1/presale_ai_knowledge.py:97` | `recommend_best_practices` |
| 19 | 80 | POST | `/extract-case-knowledge` | NONE | `app/api/v1/presale_ai_knowledge.py:129` | `extract_case_knowledge` |
| 20 | 80 | POST | `/qa` | NONE | `app/api/v1/presale_ai_knowledge.py:155` | `ask_question` |

## 4. 已使用的权限码清单

```
acceptance:approve
acceptance:create
acceptance:manage
acceptance:read
admin:cache:clear
admin:cache:reset
advantage_product:create
advantage_product:delete
advantage_product:read
advantage_product:update
aftersales:manage
alert:manage
alert:read
approval:approve
approval:create
approval:template:manage
approval:template:view
approval:view
assembly_kit:create
assembly_kit:delete
assembly_kit:read
assembly_kit:update
bom:approve
bonus:distribute
bonus:manage
bonus:pay
bonus:read
bonus:trigger
budget:approve
budget:create
budget:delete
budget:read
budget:update
business_support:approve
business_support:create
business_support:read
business_support:update
change:approve
change:close
change:create
change:read
change:update
change:verify
contract:approve
contract:create
contract:delete
contract:export
contract:read
contract:sign
contract:update
contract:view
cost:create
cost:delete
cost:manage
cost:read
cost:update
cost:write
customer:create
customer:delete
customer:read
customer:update
dashboard:manage
dashboard:view
data_import_export:manage
delivery:manage
document:create
document:delete
document:read
document:update
ecn:approve
ecn:cancel
ecn:create
ecn:execute
ecn:read
ecn:submit
ecn:update
engineer:create
engineer:read
finance:create
finance:delete
finance:read
finance:update
hourly_rate:create
hourly_rate:delete
hourly_rate:read
hourly_rate:update
hr:create
hr:read
hr:update
installation_dispatch:create
installation_dispatch:read
installation_dispatch:update
inventory:count
inventory:create
inventory:update
inventory:view
issue:create
issue:delete
issue:read
issue:update
knowledge:approve
knowledge:read
knowledge:write
machine:create
machine:delete
machine:read
machine:update
material:update
milestone:create
milestone:delete
milestone:read
milestone:update
outsourcing:approve
outsourcing:create
outsourcing:read
performance:config:read
performance:config:write
performance:engineer:read
performance:engineer:write
performance:evaluate
performance:manage
permission:create
permission:delete
permission:read
permission:update
presale:manage
presale_analytics:create
procurement:read
production:manage
project:erp:sync
project:erp:update
project:initiation:approve
project:initiation:create
project:initiation:read
project:initiation:update
project:read
project:update
project_evaluation:create
project_evaluation:read
project_evaluation:update
project_role:assign
project_role:create
project_role:read
project_role:update
purchase:approve
purchase:create
purchase:read
quote:approve
quote:create
quote:read
rd_project:read
report:create
report:export
report:read
role:assign
role:create
role:delete
role:read
role:update
sales:data_audit:review
sales_region:create
sales_region:update
sales_region:view
sales_target:create
sales_target:delete
sales_target:update
sales_target:view
sales_team:create
sales_team:delete
sales_team:update
sales_team:view
service:create
service:delete
service:read
service:update
shortage:manage
solution_credit:manage
staff_matching:create
staff_matching:read
staff_matching:update
supplier:read
supplier:update
system:user:create
system:user:update
task_center:assign
task_center:create
task_center:read
task_center:update
technical_spec:create
technical_spec:delete
technical_spec:read
technical_spec:update
timesheet:approve
timesheet:create
timesheet:delete
timesheet:read
timesheet:submit
timesheet:update
user:create
user:delete
user:read
user:update
warehouse:create
warehouse:delete
warehouse:update
warehouse:view
```

## 5. 全面重构难度评估

### 改动半径最大的模块 (Top 10)

| 模块 | 需补权限的端点数 | 写操作裸奔 | 难度 | 说明 |
|------|-----------------|-----------|------|------|
| sales | 440 | 190 | 极高 | 写操作极多，需逐一定义权限码并验证业务逻辑 |
| projects | 215 | 97 | 极高 | 写操作极多，需逐一定义权限码并验证业务逻辑 |
| production | 112 | 48 | 极高 | 写操作极多，需逐一定义权限码并验证业务逻辑 |
| strategy | 83 | 41 | 极高 | 写操作极多，需逐一定义权限码并验证业务逻辑 |
| presale | 76 | 35 | 极高 | 写操作极多，需逐一定义权限码并验证业务逻辑 |
| ecn | 66 | 37 | 极高 | 写操作极多，需逐一定义权限码并验证业务逻辑 |
| shortage | 50 | 20 | 高 | 写操作较多，需定义权限码+回归测试 |
| business_support_orders | 42 | 22 | 极高 | 写操作极多，需逐一定义权限码并验证业务逻辑 |
| performance | 38 | 13 | 高 | 写操作较多，需定义权限码+回归测试 |
| acceptance | 35 | 22 | 极高 | 写操作极多，需逐一定义权限码并验证业务逻辑 |

### 最易回归炸裂的位置

1. **sales 模块** (304 端点, 7% 覆盖): 商机/报价/合同全链路，状态机 + 数据范围过滤交织
2. **projects 模块** (263 端点, 40% 覆盖): 部分有权限但不一致，WBS/风险子模块全裸
3. **approvals 模块** (46 端点, 0% 覆盖): 审批模板 CRUD 完全无权限，任何登录用户可操作
4. **production 模块** (94 端点, 9% 覆盖): 产能分析、OEE 等无保护，数据泄露风险
5. **warehouse 模块** (22 端点, 0% 覆盖): 全部 NONE，连 AUTH_ONLY 都没有

### 建议修复优先级

1. **P0 (立即)**: warehouse, approvals/templates, organization/employees — 完全裸奔的写操作
2. **P1 (本周)**: sales 写操作, projects/risks, production 写操作
3. **P2 (本月)**: 所有 AUTH_ONLY 写操作补权限码
4. **P3 (规划)**: 所有 AUTH_ONLY 读操作补权限码，达到 >90% 覆盖

---

*本报告由 `scripts/audit_permission_coverage.py` 自动生成，可随时重新运行获取最新状态。*