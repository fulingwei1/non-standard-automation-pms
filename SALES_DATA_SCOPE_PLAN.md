# Sales Data Scope Plan — Sprint 4

## 1. 背景与目标

engineer_performance 模块已成功落地 **基于 RoleDataScope 的数据范围控制**（`engperf_scope.py`）。
Sprint 4 目标：将该模式抽象并迁移到 **销售模块核心层**，覆盖四大高风险数据对象。

## 2. 销售高风险数据对象分析

| 对象 | 模型 | Owner 字段 | 当前过滤方式 | 风险等级 |
|------|------|-----------|-------------|---------|
| **客户** | `Customer` | `sales_owner_id` | `filter_sales_data_by_scope` | 高 — 客户信息泄露 |
| **商机** | `Opportunity` | `owner_id` | `filter_sales_data_by_scope` | 高 — 含预估金额/毛利 |
| **报价** | `Quote` | `owner_id` | `filter_sales_data_by_scope` | 高 — 含成本/利润 |
| **合同** | `Contract` | `sales_owner_id` | `filter_sales_data_by_scope` | 高 — 含签约金额 |
| **线索** | `Lead` | `owner_id` | `filter_sales_data_by_scope` | 中 |
| **发票** | `Invoice` | **无 owner_id** | 注释掉了 | 高 — 财务数据无保护 |

### 现有问题

1. `sales_permissions.py` 的 `get_sales_data_scope()` 使用旧版 `DataScopeService`（全局 `Role.data_scope`），**不支持按资源类型配置**
2. DEPT scope 用 `user.department` 字符串匹配，**不走组织树**（无法覆盖子部门）
3. Invoice 过滤被注释掉，**财务数据裸奔**
4. 无 `ScopeContext` 上下文对象，每次查询重新解析 scope

## 3. 数据范围语义定义

| 层级 | 值 | 含义 | 可见数据 |
|------|---|------|---------|
| 全部 | `ALL` | 管理层/超级用户 | 所有销售数据 |
| 事业部 | `BUSINESS_UNIT` | 事业部负责人 | 本事业部 + 下属组织的数据 |
| 部门 | `DEPARTMENT` | 部门经理 | 本部门 + 子部门的数据 |
| 团队 | `TEAM` | 团队负责人 | 自己 + 直属下级的数据 |
| 个人 | `OWN` | 普通销售 | 仅自己负责的数据 |

**特殊角色：** 财务人员对 Invoice/收款拥有跨 scope 的只读权限。

## 4. 架构设计

### 4.1 新增文件

```
app/services/sales/sales_scope.py    ← 核心（已落地）
```

### 4.2 核心组件

```
┌─────────────────────────────────────────────────┐
│  resolve_sales_scope(db, user, resource_type)   │
│                                                 │
│  优先级：                                        │
│  1. RoleDataScope[resource_type]  精确资源       │
│  2. RoleDataScope["sales"]        通配降级       │
│  3. Role.data_scope               全局降级       │
│  4. 默认 → OWN                                  │
│                                                 │
│  输出：SalesScopeContext                         │
└──────────────┬──────────────────────────────────┘
               │
    ┌──────────┼──────────────┐
    ▼          ▼              ▼
apply_owner  apply_finance  can_access
  _scope       _scope       _sales_entity
```

### 4.3 SalesScopeContext 字段

```python
@dataclass
class SalesScopeContext:
    scope_type: str                          # ALL / DEPARTMENT / TEAM / OWN
    user_id: int                             # 当前用户
    resource_type: str                       # 命中的资源类型
    accessible_dept_ids: Optional[List[int]] # None=不限, []=仅自己
    accessible_user_ids: Set[int]            # TEAM: 自己+下级
    is_finance_role: bool                    # 财务特权标记
```

### 4.4 资源类型常量

```python
RT_CUSTOMER    = "customer"
RT_OPPORTUNITY = "opportunity"
RT_QUOTE       = "quote"
RT_CONTRACT    = "contract"
RT_SALES       = "sales"        # 通配 / 默认
```

与 `permission.py` 中的 `ResourceType` 常量对齐：
- `ResourceType.CUSTOMER = "customer"`
- `ResourceType.OPPORTUNITY = "opportunity"`
- `ResourceType.QUOTE = "quote"`
- `ResourceType.CONTRACT = "contract"`

### 4.5 复用的基础设施（不新造）

| 组件 | 用途 |
|------|------|
| `RoleDataScope` + `DataScopeRule` | 按角色 × 资源类型配置 scope |
| `PermissionService.get_user_data_scopes()` | 读取合并后的 {resource: scope} |
| `DataScopeServiceEnhanced.get_accessible_org_units()` | 组织树遍历（DEPT/BU scope） |
| `UserScopeService.get_subordinate_ids()` | 直属下级（TEAM scope） |
| `ScopeType` enum | 统一 scope 类型 |

## 5. 核心函数说明

### `resolve_sales_scope(db, user, resource_type="sales")`
解析用户对指定销售资源的 scope，返回 `SalesScopeContext`。

### `apply_owner_scope(query, scope, owner_column)`
为含 owner_id 的查询注入 scope 过滤。适用于 Quote/Opportunity/Lead/Customer/Contract。

### `apply_finance_scope(query, scope, owner_column=None)`
发票/收款特殊过滤：财务角色或 ALL → 不限；有 owner_column → 走 owner 过滤；无 → fail-closed。

### `can_access_sales_entity(scope, owner_id, owner_dept_id=None)`
单条记录访问判断。

### `can_access_finance_entity(scope, owner_id=None, owner_dept_id=None)`
财务实体单条记录访问判断。

## 6. 迁移计划（端点改造）

### Phase 1：核心层落地 ✅（本 Sprint）

- [x] `sales_scope.py` — scope 解析 + 过滤 + 访问判断
- [x] 不改任何 endpoint，不新建数据表

### Phase 2：端点迁移（下一 Sprint）

逐步将端点从 `filter_sales_data_by_scope` 迁移到 `sales_scope`：

```python
# BEFORE（旧）
query = filter_sales_data_by_scope(query, user, db, Quote, "owner_id")

# AFTER（新）
scope = resolve_sales_scope(db, user, RT_QUOTE)
query = apply_owner_scope(query, scope, Quote.owner_id)
```

**迁移顺序（按风险排序）：**

| 优先级 | 端点文件 | 资源 | Owner字段 | 改造点 |
|--------|---------|------|----------|--------|
| P0 | `invoices/basic.py` | Invoice | 无 | `apply_finance_scope` 替换注释掉的代码 |
| P0 | `customers.py` | Customer | `sales_owner_id` | `apply_owner_scope` |
| P1 | `opportunities/*.py` | Opportunity | `owner_id` | `apply_owner_scope` |
| P1 | `quotes.py` | Quote | `owner_id` | `apply_owner_scope` |
| P1 | `contracts/*.py` | Contract | `sales_owner_id` | `apply_owner_scope` |
| P2 | `leads/crud.py` | Lead | `owner_id` | `apply_owner_scope` |
| P2 | `payments/*.py` | Payment | 无 | `apply_finance_scope` |

### Phase 3：SalesQueryBuilder 集成

```python
# SalesQueryBuilder.with_scope_filter 改造为使用 sales_scope
def with_scope_filter(self, user, resource_type=RT_SALES):
    scope = resolve_sales_scope(self._db, user, resource_type)
    owner_col = getattr(self._model, self._config.owner_field, None)
    self._query = apply_owner_scope(self._query, scope, owner_col)
    return self
```

## 7. 数据库配置示例

无需新表。在 `role_data_scopes` + `data_scope_rules` 中配置：

```sql
-- 示例：销售经理对商机有部门级权限
INSERT INTO data_scope_rules (rule_code, rule_name, scope_type, is_active)
VALUES ('SALES_DEPT', '销售部门范围', 'DEPARTMENT', true);

INSERT INTO role_data_scopes (role_id, resource_type, scope_rule_id, is_active)
VALUES (
  (SELECT id FROM roles WHERE role_code = 'SALES_MANAGER'),
  'opportunity',
  (SELECT id FROM data_scope_rules WHERE rule_code = 'SALES_DEPT'),
  true
);

-- 通配：未单独配置的销售资源用 "sales" 通配
INSERT INTO role_data_scopes (role_id, resource_type, scope_rule_id, is_active)
VALUES (
  (SELECT id FROM roles WHERE role_code = 'SALES_REP'),
  'sales',
  (SELECT id FROM data_scope_rules WHERE rule_code = 'SCOPE_OWN'),
  true
);
```

## 8. 风险点

| 风险 | 影响 | 缓解 |
|------|------|------|
| DEPT scope 的 JOIN User 性能 | 大量数据时变慢 | 建议 owner 表加 `department_id` 冗余列（长期） |
| Invoice 无 owner_id | 迁移时需走 Contract → sales_owner_id 间接过滤 | Phase 2 可 JOIN Contract |
| RoleDataScope 未配置 | 降级到 Role.data_scope 或 OWN | fail-closed 安全，但可能过严 |
| 旧 `sales_permissions.py` 并行期 | 两套过滤逻辑共存 | Phase 2 统一后废弃旧模块 |
| `SalesQueryBuilder` 硬编码 `filter_sales_data_by_scope` | 改造前无法受益 | Phase 3 改造 |

## 9. 验证方式

### 单元测试要点

```python
# test_sales_scope.py 核心场景
def test_superuser_gets_all(): ...
def test_role_data_scope_precise_resource(): ...
def test_fallback_to_sales_wildcard(): ...
def test_fallback_to_role_data_scope(): ...
def test_default_own(): ...
def test_department_scope_uses_org_tree(): ...
def test_team_scope_includes_subordinates(): ...
def test_empty_dept_ids_downgrade_to_own(): ...
def test_finance_role_flag(): ...
def test_apply_owner_scope_all(): ...
def test_apply_owner_scope_own(): ...
def test_apply_owner_scope_team(): ...
def test_apply_owner_scope_department(): ...
def test_apply_finance_scope_no_owner(): ...
def test_can_access_sales_entity(): ...
def test_fail_closed_on_exception(): ...
```

### 集成验证

1. 配置 `RoleDataScope` 为销售经理设置 DEPARTMENT scope
2. 以该用户登录 → 查询报价列表 → 仅看到本部门的报价
3. 以普通销售登录 → 查询客户列表 → 仅看到自己的客户
4. 以财务角色登录 → 查询发票列表 → 可看到所有发票

## 10. 改动文件清单

| 文件 | 状态 | 说明 |
|------|------|------|
| `app/services/sales/sales_scope.py` | **新增** | Sales scope 核心 |
| `SALES_DATA_SCOPE_PLAN.md` | **新增** | 本方案文档 |
| `app/core/sales_permissions.py` | 不改 | Phase 2 迁移后废弃 |
| `app/common/crud/sales_query_builder.py` | 不改 | Phase 3 集成 |
| 端点文件 | 不改 | Phase 2 逐步迁移 |
