# Sales 模块数据范围控制 Endpoint 优先级矩阵

> 分析日期: 2026-03-25
> 范围: `app/api/v1/endpoints/sales/`

---

## 一、核心发现

### 关键漏洞：`check_sales_data_permission()` 未定义

该函数在 **customers.py**（3处）、**contacts.py**（6处）、**customer_tags.py**（5处）被调用，但 **在整个代码库中不存在定义**。

- `security.py` 的 `__all__` 和 import 列表中均无此函数
- `sales_permissions.py` 中未定义
- 调用时会触发 `AttributeError`，导致 500 错误

**影响**：所有依赖此函数的 detail/update/delete 端点在运行时直接崩溃，无法正常提供服务。

---

## 二、Endpoint 优先级矩阵

### P0 — 严重（运行时崩溃 + 数据泄露，必须立即修复）

| Endpoint | 文件 | 问题 | 风险 |
|----------|------|------|------|
| `GET /customers/{id}` | customers.py:175 | 调用不存在的 `check_sales_data_permission()`，500 崩溃 | 详情接口不可用 |
| `PUT /customers/{id}` | customers.py:262 | 同上 | 更新接口不可用 |
| `DELETE /customers/{id}` | customers.py:304 | 同上 | 删除接口不可用 |
| `GET /customers/{id}/contacts` | contacts.py:28 | 同上 | 联系人列表不可用 |
| `GET /contacts/{id}` | contacts.py:121 | 同上 | 联系人详情不可用 |
| `POST /customers/{id}/contacts` | contacts.py:154 | 同上 | 创建联系人不可用 |
| `PUT /contacts/{id}` | contacts.py:195 | 同上 | 更新联系人不可用 |
| `DELETE /contacts/{id}` | contacts.py:243 | 同上 | 删除联系人不可用 |
| `POST /contacts/{id}/set-primary` | contacts.py:265 | 同上 | 设主联系人不可用 |
| `GET/POST/PUT/DELETE customer_tags` | customer_tags.py（5处） | 同上 | 标签操作不可用 |

**修复方案**：实现 `check_sales_data_permission()` 函数，复用 `get_sales_data_scope()` + `DataScopeService` 已有逻辑。**不依赖新 sales_scope 核心，可立即修复。**

---

### P0 — 严重（数据越权，无任何 scope 检查）

| Endpoint | 文件 | 问题 | 风险 |
|----------|------|------|------|
| `GET /opportunities/{id}` | opportunity_crud.py:169 | 无任何权限/scope 检查，任意登录用户可读取任意商机详情 | **数据泄露** |
| `GET /contracts/{id}` | contracts/basic.py:260 | 仅有 `require_permission("contract:view")` 动作权限，无数据 scope 过滤 | **数据泄露** |
| `GET /quotes/{id}` | quote_quotes_crud.py:48 | 无任何权限/scope 检查 | **数据泄露** |
| `PUT /quotes/{id}` | quote_quotes_crud.py:137 | 无权限检查，任意用户可更新任意报价 | **越权修改** |
| `DELETE /quotes/{id}` | quote_quotes_crud.py:172 | 无权限检查，任意用户可删除报价 | **越权删除** |

**修复方案**：在详情/修改/删除接口中加入 `check_sales_data_permission()` 检查。商机和合同已有 `check_sales_edit_permission()` 可复用。

---

### ~~P1 — 高（数据泄露，缺少 scope 过滤但影响范围较窄）~~ ✅ 已修复 (Sprint 5)

| Endpoint | 文件 | 修复方式 | 状态 |
|----------|------|----------|------|
| `GET /opportunities/funnel` | opportunity_analytics.py | `filter_sales_data_by_scope()` 应用于主查询和金额聚合查询 | ✅ 已修复 |
| `GET /opportunities/export` | opportunity_analytics.py | `filter_sales_data_by_scope()` 应用于导出查询 | ✅ 已修复 |
| `GET /opportunities/{id}/win-probability` | opportunity_analytics.py | `check_sales_data_permission()` 检查商机所有权 | ✅ 已修复 |
| `GET /quotes/{id}/versions` | quote_versions.py | `_check_quote_scope()` 通过父 Quote 检查 | ✅ 已修复 |
| `GET /quotes/{id}/versions/{vid}` | quote_versions.py | `_check_quote_scope()` 通过父 Quote 检查 | ✅ 已修复 |
| `POST /quotes/{id}/versions` | quote_versions.py | `_check_quote_scope()` 通过父 Quote 检查 | ✅ 已修复 |
| `GET /quotes/{id}/versions/compare` | quote_versions.py | `_check_quote_scope()` 通过父 Quote 检查 | ✅ 已修复 |
| `GET /quotes/{vid}/items` | quote_items.py | `_check_version_scope()` 通过 Version→Quote 检查 | ✅ 已修复 |
| `POST /quotes/{vid}/items` | quote_items.py | `_check_version_scope()` 通过 Version→Quote 检查 | ✅ 已修复 |
| `PUT /quotes/items/{id}` | quote_items.py | `_check_item_scope()` 通过 Item→Version→Quote 检查 | ✅ 已修复 |
| `DELETE /quotes/items/{id}` | quote_items.py | `_check_item_scope()` 通过 Item→Version→Quote 检查 | ✅ 已修复 |
| `GET /contracts/{id}/deliverables` | contracts/deliverables.py | `_check_contract_scope()` 通过父 Contract 检查 | ✅ 已修复 |
| `GET /contracts/{id}/amendments` | contracts/deliverables.py | `_check_contract_scope()` 通过父 Contract 检查 | ✅ 已修复 |
| `POST /contracts/{id}/amendments` | contracts/deliverables.py | `_check_contract_scope()` 通过父 Contract 检查 | ✅ 已修复 |
| `GET /contracts/export` | contracts/export.py | `filter_sales_data_by_scope()` 应用于导出查询 | ✅ 已修复 |
| `GET /contracts/{id}/pdf` | contracts/export.py | `check_sales_data_permission()` 检查合同所有权 | ✅ 已修复 |

---

### P1 — 高（工作流操作缺少 scope 检查）

| Endpoint | 文件 | 问题 | 风险 |
|----------|------|------|------|
| `PUT /opportunities/{id}/stage` | opportunity_workflow.py:78 | 无 scope/管理权限检查 | 越权变更阶段 |
| `PUT /opportunities/{id}/score` | opportunity_workflow.py:122 | 无 scope 检查 | 越权评分 |
| `PUT /opportunities/{id}/win` | opportunity_workflow.py:171 | 无 scope 检查 | 越权赢单 |
| `PUT /opportunities/{id}/lose` | opportunity_workflow.py:210 | 无 scope 检查 | 越权输单 |
| `POST /quotes/{id}/approve` | quotes.py:216 | 无审批权限检查（直接改状态） | 越权审批 |

> 注意: `POST /opportunities/{id}/gate` 已正确使用 `can_set_opportunity_gate()` 检查。

---

### P2 — 中（审批流/列表端点，风险有限或已有部分保护）

| Endpoint | 文件 | 问题 | 风险 |
|----------|------|------|------|
| `GET /contacts` (全局列表) | contacts.py:69 | 非 admin 用 `sales_owner_id == current_user.id` 硬编码过滤，不走 scope 体系 | DEPT/TEAM 用户看不到下属数据 |
| `POST /contracts/{id}/sign` | contracts/sign_project.py:42 | 有 `contract:sign` 权限检查，但不验证 scope | 低风险（签约权限本身就很高） |
| `POST /contracts/{id}/project` | contracts/sign_project.py:122 | 有 `contract:create` 权限检查，无 scope | 低风险 |
| 报价审批工作流 | quote_approval.py | 使用 `require_permission` + Service 层 user_id 过滤 | 基本安全 |
| 合同审批工作流 | contracts/approval.py | 使用 `require_permission` + Service 层 user_id 过滤 | 基本安全 |

---

### 已安全（有 scope 过滤）

| Endpoint | 文件 | 保护方式 |
|----------|------|----------|
| `GET /customers` | customers.py:53 | `filter_sales_data_by_scope()` ✅ |
| `GET /customers/stats` | customers.py:126 | `filter_sales_data_by_scope()` ✅ |
| `GET /opportunities` | opportunity_crud.py:44 | `SalesQueryBuilder.with_scope_filter()` ✅ |
| `PUT /opportunities/{id}` | opportunity_crud.py:210 | `check_sales_edit_permission()` ✅ |
| `GET /contracts` | contracts/basic.py:105 | `SalesQueryBuilder.with_scope_filter()` ✅ |
| `PUT /contracts/{id}` | contracts/basic.py:290 | `check_sales_edit_permission()` ✅ |
| `POST /opportunities/{id}/gate` | opportunity_workflow.py:35 | `can_set_opportunity_gate()` ✅ |
| `GET /quotes` (列表) | quotes.py:97 | Service 层集成数据权限 ✅ |

---

## 三、修复分类

### 可立即修复（不依赖 sales_scope 核心）

1. **实现 `check_sales_data_permission()` 函数** — 解决全部 P0 崩溃问题
   - 复用已有的 `get_sales_data_scope()` + `DataScopeService.get_subordinate_ids()`
   - 对单个实体进行 owner 字段检查
   - 影响文件：`app/core/sales_permissions.py`（加函数）+ `app/core/security.py`（加 export）

2. **商机详情 scope 检查** — `GET /opportunities/{id}` 加入 `check_sales_data_permission()`
3. **合同详情 scope 检查** — `GET /contracts/{id}` 加入 `check_sales_data_permission()`
4. **报价 CRUD scope 检查** — `GET/PUT/DELETE /quotes/{id}` 加入权限检查

### ✅ Sprint 5 已完成

1. ~~**报价子资源全面 scope**~~ — ✅ 通过 `_check_quote_scope()` / `_check_version_scope()` / `_check_item_scope()` 链路回溯
2. ~~**商机分析接口 scope**~~ — ✅ funnel/export 已集成 `filter_sales_data_by_scope()`
3. ~~**合同子资源 scope**~~ — ✅ 通过 `_check_contract_scope()` 回溯到 `sales_owner_id`
4. ~~**合同导出 scope**~~ — ✅ export 已集成 `filter_sales_data_by_scope()`，PDF 已加 `check_sales_data_permission()`

### 剩余高风险（P1-workflow，下一批修复）

1. **联系人全局列表 scope 升级** — 从硬编码 `sales_owner_id == current_user.id` 迁移到 `filter_sales_data_by_scope()` 体系
2. **商机工作流 scope** — stage/score/win/lose 需要统一的 `can_manage_sales_opportunity()` 守卫
3. **报价审批 scope** — `POST /quotes/{id}/approve` 无审批权限检查

---

## 四、风险总结

| 优先级 | 数量 | 类型 |
|--------|------|------|
| P0 (崩溃) | ~14 endpoint | `check_sales_data_permission` 未定义导致 500 |
| P0 (越权) | 5 endpoint | 详情/修改/删除完全无 scope 检查 |
| ~~P1~~ | ~~16 endpoint~~ | ✅ Sprint 5 已全部修复 |
| P2 | ~5 endpoint | 有部分保护，scope 不完整 |
| 安全 | ~8 endpoint | 已正确集成 scope |

**最危险接口 TOP 5:**
1. `GET /opportunities/{id}` — 零检查，完全裸露
2. `GET /quotes/{id}` — 零检查，含成本/毛利等敏感数据
3. `GET /contracts/{id}` — 仅动作权限，可查看任意合同金额
4. `PUT/DELETE /quotes/{id}` — 零检查，可越权修改/删除
5. `GET /opportunities/export` — 无 scope，可批量导出全公司商机
