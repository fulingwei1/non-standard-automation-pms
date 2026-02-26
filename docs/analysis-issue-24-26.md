# Issue #26 Dashboard 重复分析 & Issue #24 Status 重复分析

## Issue #26: Dashboard 文件重复

### 发现

14个 `dashboard*.py` 文件（不含 `__pycache__`）分布如下：

**API 端点层 (10个模块 dashboard):**
| 文件 | 基类 | 业务域 |
|------|------|--------|
| `kit_rate/dashboard.py` | `BaseDashboardEndpoint` ✅ | 齐套率 |
| `shortage/analytics/dashboard.py` | `BaseDashboardEndpoint` ✅ | 缺料分析 |
| `assembly_kit/dashboard.py` | `BaseDashboardEndpoint` ✅ | 齐套分析 |
| `hr_management/dashboard.py` | `BaseDashboardEndpoint` ✅ | 人事管理 |
| `business_support/dashboard.py` | `BaseDashboardEndpoint` ✅ | 商务支持 |
| `presale_analytics/dashboard.py` | `BaseDashboardEndpoint` ✅ | 售前分析 |
| `management_rhythm/dashboard.py` | `BaseDashboardEndpoint` ✅ | 管理节律 |
| `production/dashboard.py` | `BaseDashboardEndpoint` ✅ | 生产管理 |
| `staff_matching/dashboard.py` | `BaseDashboardEndpoint` ✅ | 人员匹配 |
| `production/capacity/dashboard.py` | ❌ 原始 router | 产能分析 |

**统一/聚合层 (2个):**
- `dashboard_stats.py` — 按角色返回统计卡片（销售/工程/采购/生产/PMO/管理员）
- `dashboard_unified.py` — 统一入口，聚合各模块数据

**Schema 层 (2个):** `schemas/dashboard.py`, `schemas/business_support/dashboard.py`, `schemas/strategy/dashboard.py`

**Service 层 (2个):** `dashboard_adapter.py` (适配器注册表), `dashboard_cache_service.py` (缓存)

**已禁用:** `strategy.disabled/dashboard.py`

### 结论：**不是真正重复**

已有完善的重复消除架构：
1. `BaseDashboardEndpoint` 基类 → 统一路由注册、权限检查、响应格式
2. `DashboardAdapter` + `DashboardRegistry` → 统一聚合接口
3. `DashboardCacheService` → 统一缓存
4. 每个模块的 dashboard 包含**不同业务域的查询逻辑**，不可合并

### 唯一改进：`production/capacity/dashboard.py`

此文件是唯一未使用 `BaseDashboardEndpoint` 的端点，使用原始 router 函数式风格。
已重构为继承 `BaseDashboardEndpoint`。

---

## Issue #24: Status 文件重复

### 发现

7个 `status*.py` 端点文件：

| 文件 | 使用 StatusUpdateService | 业务域 |
|------|--------------------------|--------|
| `projects/stages/status_updates.py` | ✅ | 项目阶段状态 |
| `projects/status/status_crud.py` | ✅ | 项目状态 CRUD |
| `projects/approvals/status_new.py` | ❌ (DEPRECATED, 用 ApprovalEngine) | 审批状态 |
| `projects/status.py` | N/A (仅 re-export router) | 路由聚合 |
| `scheduler/status.py` | ❌ (完全不同：查询调度器运行状态) | 调度器 |
| `production/work_orders/status.py` | ✅ | 工单状态 |
| `service/tickets/status.py` | ✅ | 服务工单状态 |

**Service 层:**
- `StatusUpdateService` — 通用状态更新（验证、转换规则、历史、联动）✅ 已存在
- `StatusTransitionService` — 项目状态联动规则引擎（合同→项目、BOM→状态等）

### 结论：**已完成重构，不是真正重复**

1. 公共逻辑已提取到 `StatusUpdateService`（4个端点在使用）
2. `scheduler/status.py` 是查询调度器运行状态，与业务状态更新完全无关
3. `projects/approvals/status_new.py` 已标记 DEPRECATED
4. `projects/status.py` 仅做路由聚合

无需进一步重构。
