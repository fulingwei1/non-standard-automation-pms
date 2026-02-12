# 代码库全面审查报告

**项目**: 非标自动化项目管理系统 (Non-Standard Automation PMS)
**审查日期**: 2026-02-11
**审查范围**: 全部代码库 (1631 个 Python 文件, 587,000+ 行代码)

---

## 目录

1. [审查概要](#1-审查概要)
2. [严重问题 (CRITICAL)](#2-严重问题-critical)
3. [高危问题 (HIGH)](#3-高危问题-high)
4. [中等问题 (MEDIUM)](#4-中等问题-medium)
5. [低危问题 (LOW)](#5-低危问题-low)
6. [正面发现](#6-正面发现)
7. [修复建议优先级](#7-修复建议优先级)

---

## 1. 审查概要

| 审查项 | 结果 |
|--------|------|
| Python 语法检查 | 1631 文件中 **1 个语法错误** |
| 安全漏洞 | **1 个严重** + **5 个中等** |
| 缺失认证保护的端点 | **30+ 个文件** |
| 数据库操作无错误处理 | **20+ 个文件** |
| 未分页的列表查询 | **20+ 个端点** |
| Pydantic v1 旧模式 | **82 个 Schema 类** (57 文件) |
| 生产代码中的 print() | **9 个文件** |
| 不规范的分页实现 | **9+ 个端点** |
| 手写 .like() 过滤 | **20+ 个文件** |
| 缺少 `__init__.py` | **15 个 app/ 目录** |
| 缺少 TimestampMixin 的模型 | **23 个模型** |
| 数据库外键缺失 | **2 个关键模型** |

---

## 2. 严重问题 (CRITICAL)

### 2.1 SQL 注入风险 - QueryOptimizer

**文件**: `app/services/database/query_optimizer.py:357,386`

`optimize_query()` 和 `analyze_query()` 方法使用 `text(f"...")` 进行字符串插值构建 SQL：

```python
# 第 357 行 - 存在风险
query = query.filter(text(f"{field} = :val").params(val=value))

# 第 386 行 - 存在风险
explain_result = self.db.execute(text(f"EXPLAIN QUERY PLAN {sql_str}")).fetchall()
```

**影响**: 如果 `field` 参数未经验证，攻击者可以注入 SQL。虽然目前该类未被任何端点引用，但一旦启用将造成严重安全隐患。

**建议**: 删除未使用的代码，或对 field 名称进行白名单校验。

### 2.2 误提交的开发脚本 (语法错误)

**文件**: `app/api/v1/endpoints/_fix_import.py`

该文件是开发者遗留的一次性修复脚本，存在以下问题：
- **IndentationError** (第 37 行): 缩进不一致导致语法错误
- 硬编码了开发者 macOS 路径: `/Users/flw/non-standard-automation-pm/...`
- 不是有效的 API 端点，不应存在于 endpoints 目录中

**建议**: 立即删除此文件。

---

## 3. 高危问题 (HIGH)

### 3.1 30+ 个端点文件缺少认证/权限检查

以下文件的路由未使用 `require_permission()` 或 `get_current_active_user`：

| 文件 | 无保护路由数 | 严重性 |
|------|------------|--------|
| `app/api/v1/endpoints/strategy/decomposition.py` | 17 | 高 |
| `app/api/v1/endpoints/strategy/review.py` | 15 | 高 |
| `app/api/v1/endpoints/approvals/templates.py` | 16 | 高 |
| `app/api/v1/endpoints/strategy/kpi.py` | 13 | 高 |
| `app/api/v1/endpoints/strategy/annual_work.py` | 11 | 高 |
| `app/api/v1/endpoints/approvals/tasks.py` | 11 | 高 |
| `app/api/v1/endpoints/strategy/strategy.py` | 9 | 高 |
| `app/api/v1/endpoints/strategy/comparison.py` | 7 | 高 |
| `app/api/v1/endpoints/strategy/csf.py` | 7 | 高 |
| `app/api/v1/endpoints/approvals/instances.py` | 7 | 高 |
| `app/api/v1/endpoints/organization/employees.py` | 5 | 高 |
| `app/api/v1/endpoints/business_support_orders/*` | 多个 | 高 |

> **注意**: 全局 `GlobalAuthMiddleware` 会拦截未认证请求，但缺少细粒度的权限检查意味着任何已认证用户都可以访问这些端点。

### 3.2 20+ 个端点数据库操作无错误处理

以下文件的 `db.add()`/`db.commit()` 操作缺少 try/except 保护：

- `app/api/v1/endpoints/culture_wall/goals.py` (第 94-96 行)
- `app/api/v1/endpoints/audits.py`
- `app/api/v1/endpoints/culture_wall_config.py`
- `app/api/v1/endpoints/staff_matching/tags.py` (第 100, 120, 137 行)
- `app/api/v1/endpoints/management_rhythm/` 多个文件

数据库异常会直接抛出 500 错误，暴露内部信息。

### 3.3 20+ 个列表端点缺少分页

以下端点使用 `.all()` 查询但未实施分页限制：

- `app/api/v1/endpoints/culture_wall/goals.py`
- `app/api/v1/endpoints/management_rhythm/meeting_map.py`
- `app/api/v1/endpoints/management_rhythm/action_items.py`
- `app/api/v1/endpoints/management_rhythm/metrics.py`
- `app/api/v1/endpoints/staff_matching/evaluations.py`
- `app/api/v1/endpoints/staff_matching/matching.py`
- `app/api/v1/endpoints/staff_matching/profiles.py`
- `app/api/v1/endpoints/kit_rate/unified.py`
- `app/api/v1/endpoints/sla/statistics.py`
- `app/api/v1/endpoints/pmo/cockpit.py`
- `app/api/v1/endpoints/pmo/phases.py`

**风险**: 大数据量时可能导致内存溢出或响应超时。

### 3.4 生产代码中的 print() 语句 (9 个文件)

生产代码应使用 `logging` 模块，而非 `print()`：

| 文件 | 问题 |
|------|------|
| `app/utils/scheduled_tasks/performance_data_auto_tasks.py` | 多处 print() (第 28-192 行) |
| `app/services/report_framework/data_resolver.py` | print 调试输出 |
| `app/services/report_framework/config_loader.py` | print 调试输出 |
| `app/services/preset_stage_templates/__init__.py` | print 调试输出 |
| `app/services/ppt_generator/generator.py` | print 调试输出 |
| `app/api/v1/endpoints/technical_review/reviews.py:249` | `print(f"设计评审同步失败: {e}")` |
| `app/api/v1/endpoints/dashboard_unified.py:67` | `print(f"Error loading dashboard...")` |

### 3.5 .env.example 中的占位凭据

**文件**: `.env.example`

包含类似 `root_password_change_me` 的占位密码，如果未更改直接用于生产将造成安全隐患。建议改为空值或文档引用。

---

## 4. 中等问题 (MEDIUM)

### 4.1 82 个 Pydantic Schema 类使用旧版 v1 模式

**57 个文件** 中的 82 个类仍在使用已弃用的 `class Config:` 模式：

```python
# 当前 (Pydantic v1 旧模式)
class Config:
    from_attributes = True

# 应改为 (Pydantic v2 新模式)
model_config = ConfigDict(from_attributes=True)
```

**受影响文件**:
- `app/schemas/bonus.py` (5 个类)
- `app/schemas/organization.py` (11 个类)
- `app/schemas/technical_review.py` (15 个类)
- `app/schemas/performance.py` (10 个类)
- `app/schemas/budget.py`, `staff_matching.py`, `strategy/strategy.py`, `presales.py` 等

### 4.2 不规范的分页实现 (违反项目标准)

以下文件使用手写 `offset = (page - 1) * page_size` 而非标准的 `get_pagination_query`：

- `app/api/v1/endpoints/tenants.py`
- `app/api/v1/endpoints/base_crud_router_sync.py`
- `app/api/v1/endpoints/roles.py`
- `app/services/shortage/shortage_management_service.py:78`
- `app/services/project/core_service.py:48`

### 4.3 手写 .like() 过滤 (违反项目标准)

**20+ 个文件** 使用 `.ilike(f"%{keyword}%")` 而非标准的 `apply_keyword_filter()`：

- `app/utils/scheduled_tasks/risk_tasks.py`
- `app/utils/scheduled_tasks/milestone_tasks.py`
- `app/services/sales/payment_plan_service.py`
- `app/services/cost_match_suggestion_service.py`
- `app/services/shortage/shortage_management_service.py`
- `app/api/v1/endpoints/service/statistics.py`
- `app/api/v1/endpoints/sales/cost_matching.py`
- 等 13+ 个文件

### 4.4 alert_rule_engine 表达式求值安全风险

**文件**: `app/services/alert_rule_engine/condition_evaluator.py:222`

使用 `simple_eval()` 执行用户自定义表达式：

```python
result = simple_eval(rule.condition_expr, names=eval_context, safe=True)
```

虽然 `simpleeval` 比 `eval()` 安全，但管理员创建的恶意表达式仍存在风险。建议添加表达式白名单验证。

### 4.5 CSRF 保护在 DEBUG 模式下完全关闭

**文件**: `app/core/csrf.py:75-77`

```python
if settings.DEBUG:
    return  # 完全跳过 CSRF 验证
```

如果生产环境意外启用 DEBUG=True，CSRF 保护将失效。

### 4.6 文件上传仅检查扩展名

**文件**: `app/api/v1/endpoints/bonus/allocation_sheets/upload.py:58`

只检查 `.xlsx`/`.xls` 扩展名，不验证 MIME 类型。攻击者可以重命名恶意文件绕过检查。

### 4.7 23 个数据库模型缺少 TimestampMixin

以下审计/日志相关模型缺少 `created_at`/`updated_at` 字段：

| 文件 | 模型 |
|------|------|
| `app/models/progress.py` | WbsTemplateTask, TaskDependency, ProgressLog, BaselineTask |
| `app/models/staff_matching.py` | HrAIMatchingLog |
| `app/models/timesheet.py` | TimesheetApprovalLog |
| `app/models/technical_review.py` | ReviewParticipant, ReviewChecklistRecord |
| `app/models/presale.py` | PresaleTicketProgress |
| `app/models/sales/quotes.py` | QuoteItem, QuoteCostHistory |
| `app/models/permission.py` | RoleDataScope, RoleMenu |
| `app/models/user.py` | RoleApiPermission, UserRole, SolutionCreditTransaction |
| `app/models/organization.py` | PositionRole |

### 4.8 数据库模型外键约束缺失

**文件**: `app/models/issue.py`
- `task_id`, `project_id`, `machine_id`, `acceptance_order_id` 等字段未定义 ForeignKey 约束
- 缺少这些字段的索引

**文件**: `app/models/presale.py`
- `customer_id` (第 102 行), `opportunity_id` (第 104 行) 未定义 ForeignKey 约束

### 4.9 15 个 app/ 目录缺少 `__init__.py`

| 目录 | Python 文件数 |
|------|-------------|
| `app/utils/` | 22 |
| `app/api/v1/endpoints/` | 19 |
| `app/services/alert/` | 5 |
| `app/services/sales/` | 3 |
| `app/services/shortage/` | 3 |
| `app/services/cache/` | 2 |
| `app/services/service/` | 2 |
| `app/middleware/` | 1 |
| `app/common/workflow/` | 1 |
| `app/services/database/` | 1 |
| `app/services/material/` | 1 |
| `app/services/purchase/` | 1 |
| 其他 3 个目录 | 各 1-8 |

虽然 Python 3 支持隐式命名空间包，但这与项目其他 191 个目录有 `__init__.py` 的惯例不一致。

### 4.10 超过 100 行的函数 (5 个)

| 文件 | 函数 | 行数 |
|------|------|------|
| `app/services/progress_service.py` | `run_auto_processing()` | 132 行 (848-979) |
| `app/services/progress_service.py` | `aggregate_task_progress()` | 107 行 (159-265) |
| `app/services/progress_service.py` | `aggregate_project_progress()` | 105 行 (456-560) |
| `app/services/notification_service.py` | `send_alert_notification()` | 105 行 (295-399) |
| `app/services/approval_engine/adapters/ecn.py` | `submit_for_approval()` | 102 行 (173-274) |

### 4.11 返回原始字典而非 Pydantic 模型的端点

以下端点返回未经 Pydantic 验证的原始字典：

- `app/api/v1/endpoints/project_contributions.py` (`response_model=dict`)
- `app/api/v1/endpoints/project_workspace.py` (原始字典返回)
- `app/api/v1/endpoints/staff_matching/tags.py`
- `app/api/v1/endpoints/staff_matching/evaluations.py`
- `app/api/v1/endpoints/kit_rate/project.py`
- `app/api/v1/endpoints/kit_rate/unified.py`

---

## 5. 低危问题 (LOW)

### 5.1 Token 撤销依赖 Redis 可用性

**文件**: `app/core/auth.py:84-138`

Token 黑名单在 Redis 不可用时回退到内存存储，服务重启后已撤销的 Token 可以被重新使用。

### 5.2 time.sleep() 阻塞调用

**文件**: `app/utils/wechat_client.py:194`

在 HTTP 处理过程中使用 `time.sleep(1)` 进行重试，应改为 `asyncio.sleep()`。

### 5.3 RuntimePatchedSession 线程安全

**文件**: `app/models/base.py:56-72`

类级别标志 `_sqlite_patches_applied` 在多线程环境下可能出现竞态条件。

### 5.4 表名命名不一致

- `presale_support_ticket` (单数) - 应为 `presale_support_tickets` (复数)
- `hr_ai_matching_log` (单数) - 应为 `hr_ai_matching_logs` (复数)

### 5.5 未完成的 TODO 项 (3 个)

| 文件 | 描述 |
|------|------|
| `app/api/v1/endpoints/dashboard_stats.py:48` | 多租户隔离 - 业务模型缺少 tenant_id |
| `app/api/v1/endpoints/dashboard_stats.py:323` | 需要系统错误日志表来统计错误数 |
| `app/models/material.py:89` | Supplier 信息迁移到 Vendor 模型 |

---

## 6. 正面发现

该项目在多个方面表现出色：

| 方面 | 评价 |
|------|------|
| **架构设计** | 清晰的分层架构 (API → Service → Model)，统一的审批引擎、状态机框架 |
| **安全基础** | JWT 认证、bcrypt 密码哈希、速率限制、CSRF 防护、全局认证中间件 |
| **代码组织** | 163 个模型文件按业务域组织，537 个服务文件覆盖 40+ 业务领域 |
| **测试覆盖** | 517+ 测试文件，覆盖单元、API、集成、E2E、性能测试 |
| **文档** | 24+ 设计文档，44KB 的 AI 助手指南 |
| **通用工具** | 统一的分页、过滤、日期范围工具（虽然未完全应用到所有端点） |
| **无裸 except** | 未发现 `except:` 裸异常捕获 |
| **无通配符 import** | 除模型导出外，未发现 `from x import *` 滥用 |
| **权限系统** | 完整的 RBAC，API 级权限控制，数据范围规则 |
| **状态机** | 统一的状态机框架，11 个业务实现，支持钩子和通知 |

---

## 7. 修复建议优先级

### P0 - 立即修复

1. **删除** `app/api/v1/endpoints/_fix_import.py`
2. **修复或删除** `app/services/database/query_optimizer.py` 中的 SQL 注入风险

### P1 - 尽快修复

3. **为 30+ 个端点文件添加** `require_permission()` 权限检查（特别是 strategy/* 和 approvals/*）
4. **为 20+ 个端点的数据库操作添加** try/except 错误处理
5. **为 20+ 个列表端点添加分页** (使用 `get_pagination_query`)
6. **将 9 个文件中的 print() 替换为** logging

### P2 - 计划修复

7. **迁移 82 个 Pydantic Schema** 从 `class Config:` 到 `model_config = ConfigDict(...)`
8. **统一分页实现** 使用 `get_pagination_query` 和 `apply_pagination`
9. **统一关键词过滤** 使用 `apply_keyword_filter()`
10. **为 23 个模型添加** TimestampMixin
11. **补充 15 个目录的** `__init__.py`
12. **为 Issue/Presale 模型添加** ForeignKey 约束和索引

### P3 - 持续改进

13. **重构 5 个超长函数** (> 100 行)
14. **将端点的原始字典返回改为** Pydantic 响应模型
15. **修复表名命名不一致** (单数 → 复数)
16. **添加 CSRF 保护的生产环境强制检查** (不依赖 DEBUG 标志)
17. **增强文件上传验证** (MIME 类型检查)
18. **解决 3 个未完成的 TODO 项**

---

*本报告基于静态代码分析。建议额外进行运行时安全测试和渗透测试。*
