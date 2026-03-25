# Engineer Performance 数据级隔离重构方案

> 基于 `refactor/engperf-data-scope` 分支代码现状分析，面向 Sprint 3 落地

---

## 0. 核心结论（TL;DR）

**当前 engineer_performance 模块的所有 28 个接口均无数据范围控制。** 任何已登录用户可以：
- 查看全公司所有人的绩效排名、分数、趋势
- 查看任意他人收到的协作评价详情（含评语）
- 查看任意他人的知识贡献统计
- 传入任意 `department_id` 查看任意部门数据

系统已有完整的 `Role.data_scope` + `DataScopeServiceEnhanced.apply_data_scope()` 基础设施，但 **engineer_performance 模块完全没有接入**。这不是缺一个装饰器的问题，而是整个数据查询层都没有注入 scope 过滤。

---

## 1. 越权风险接口清单

### 1.1 即使补了 `require_permission` 仍会越权的接口

`require_permission` 只解决"能不能调这个接口"，**不解决"调了之后能看多大范围的数据"**。以下接口即使加了功能权限，仍然会越权：

| 风险等级 | 接口 | 文件:行号 | 越权场景 |
|---------|------|----------|---------|
| **P0-严重** | `GET /ranking` | `ranking.py:23` | 普通工程师可看全公司排名+分数+姓名 |
| **P0-严重** | `GET /ranking/by-department` | `ranking.py:83` | 可传入任意 `department_id` 查其他部门排名 |
| **P0-严重** | `GET /ranking/by-job-type` | `ranking.py:127` | 全公司同岗位排名无范围限制 |
| **P0-严重** | `GET /ranking/top` | `ranking.py:169` | Top N 工程师暴露全公司 |
| **P0-严重** | `GET /engineer/{user_id}` | `engineer.py:94` | 可查任意人绩效详情（含5维分数） |
| **P0-严重** | `GET /engineer/{user_id}/trend` | `engineer.py:156` | 可查任意人历史趋势 |
| **P0-严重** | `GET /engineer/{user_id}/comparison` | `engineer.py:170` | 可查任意人对比数据 |
| **P1-高** | `GET /engineer` (列表) | `engineer.py:243` | 可传任意 `department_id` 查他部工程师 |
| **P1-高** | `GET /summary/company` | `summary.py:23` | 公司级汇总数据，应仅限管理层 |
| **P1-高** | `GET /summary/by-job-type/{job_type}` | `summary.py:50` | 岗位类型汇总无范围控制 |
| **P1-高** | `GET /collaboration/received/{user_id}` | `collaboration.py:66` | 可查任意人收到的协作评价+评语 |
| **P1-高** | `GET /collaboration/given/{user_id}` | `collaboration.py:103` | 可查任意人给出的评价 |
| **P1-高** | `GET /collaboration/stats/{user_id}` | `collaboration.py:158` | 可查任意人协作统计 |
| **P1-高** | `GET /collaboration/matrix` | `collaboration.py:22` | 全公司协作矩阵 |
| **P1-高** | `GET /collaboration/statistics/{period_id}` | `collaboration.py:276` | 全局评价统计 |
| **P1-高** | `GET /collaboration/quality-analysis/{period_id}` | `collaboration.py:311` | 评价质量分析 |
| **P2-中** | `GET /knowledge/ranking` | `knowledge.py:487` | 知识贡献排行无范围控制 |
| **P2-中** | `GET /knowledge/rankings` | `knowledge.py:244` | 同上（兼容接口） |
| **P2-中** | `GET /knowledge/contributor/{id}/stats` | `knowledge.py:281` | 可查他人贡献统计 |
| **P2-中** | `POST /collaboration/auto-select/{id}` | `collaboration.py:172` | 可为任意人抽取评价人 |
| **P2-中** | `POST /collaboration/auto-complete/{period_id}` | `collaboration.py:327` | 自动填充评价无管理员校验 |
| **P3-低** | `GET /config/weights` | `config.py:25` | 权重配置可公开 |
| **P3-低** | `GET /config/department-configs` | `config.py:237` | 已有 `current_user.id` 过滤，风险较低 |

### 1.2 已有保护的接口（相对安全）

| 接口 | 保护方式 |
|------|---------|
| `GET /engineer/profile` | 使用 `current_user.id`，仅查自己 |
| `POST /engineer/profile` | 创建操作（但缺管理员校验） |
| `GET /collaboration/pending` | 使用 `current_user.id` |
| `GET /knowledge/stats/me` | 使用 `current_user.id` |
| `POST /knowledge` (创建) | 使用 `current_user.id` |
| `GET /config/pending-approvals` | 有 `is_superuser` 校验 |
| `POST /config/approve/{id}` | 有 `is_superuser` 校验 |

---

## 2. 数据范围控制层选择

### 2.1 各层方案对比

| 层级 | 方案 | 优点 | 缺点 | 适用场景 |
|------|------|------|------|---------|
| **Router** | 在 endpoint 函数里硬编码过滤 | 直观 | 重复代码爆炸，容易遗漏 | 不推荐 |
| **Service** | Service 方法接受 `scope_context` 参数 | 灵活，可做业务判断 | 需要改每个 service 方法签名 | **聚合接口** |
| **Query Builder** | 在构建查询时自动注入 scope filter | 统一，不易遗漏 | 需要模型有统一的 scope 字段 | **列表/排名接口** |
| **Policy** | 独立的 policy 层做鉴权 | 解耦清晰 | 过度设计，当前规模不需要 | 未来可演进 |

### 2.2 推荐方案：Service 层 + Query Builder 双层拦截

```
Endpoint
  │
  ├─ (1) 功能权限检查: require_permission("engperf:ranking:read")
  │
  ├─ (2) 解析数据范围: scope = resolve_engperf_scope(db, current_user)
  │      返回 EngPerfScope(type=DEPARTMENT, accessible_dept_ids=[3,5])
  │
  └─ (3) Service 层注入 scope
         │
         └─ Query Builder 自动追加 WHERE 条件
              .filter(PerformanceResult.department_id.in_(scope.accessible_dept_ids))
```

**选择理由：**
1. `DataScopeServiceEnhanced.apply_data_scope()` 已实现通用 Query 过滤，但 `PerformanceResult` 用 `department_id` 而不是 `org_unit_id`，需要适配
2. 排名/列表接口适合 Query Builder 自动注入，避免遗漏
3. 单条记录接口（如 `GET /engineer/{user_id}`）适合 Service 层做 `can_access_data()` 判断
4. 汇总接口（如 company summary）需要 Service 层根据 scope 决定聚合范围

---

## 3. 数据范围模型设计

### 3.1 范围层级定义

```python
class EngPerfDataScope(str, Enum):
    """工程师绩效数据范围"""
    OWN = "OWN"               # 仅看自己的绩效数据
    TEAM = "TEAM"             # 本组成员（直属下级）
    DEPARTMENT = "DEPARTMENT" # 本部门及子部门
    ALL = "ALL"               # 全公司（管理员/HR）
    CUSTOM = "CUSTOM"         # 自定义（预留，如"指定部门列表"）
```

### 3.2 各范围对应的数据可见性

| 范围 | 排名列表 | 个人详情 | 协作评价 | 汇总统计 | 知识贡献 |
|------|---------|---------|---------|---------|---------|
| OWN | 仅看到自己的排位+同组模糊排名 | 仅自己 | 仅自己收到/发出的 | 不可见 | 仅自己的 |
| TEAM | 本组成员排名 | 本组成员 | 本组成员的 | 本组汇总 | 本组成员的 |
| DEPARTMENT | 本部门排名 | 本部门成员 | 本部门成员的 | 本部门汇总 | 本部门成员的 |
| ALL | 全公司排名 | 所有人 | 所有人的 | 公司汇总 | 所有人的 |

### 3.3 默认 scope 分配规则

| 角色类型 | 默认 scope | 说明 |
|---------|-----------|------|
| 普通工程师 | OWN | 只看自己绩效 |
| 组长/Tech Lead | TEAM | 看直属下级 |
| 部门经理 | DEPARTMENT | 看本部门 |
| HR / 绩效管理员 | ALL | 全公司 |
| 超级管理员 | ALL | 全公司 |

---

## 4. 与现有模型的对接关系

### 4.1 与 `Role.data_scope` 的关系

`Role` 模型已有 `data_scope` 字段（默认 `"OWN"`），`RoleDataScope` 关联表支持按 `resource_type` 配置不同资源的范围。

**对接方案：**

```python
# 新增 resource_type = "engineer_performance" 的 RoleDataScope 记录
# 如果未配置，降级读取 Role.data_scope 字段

def resolve_engperf_scope(db: Session, user: User) -> EngPerfScopeContext:
    """解析用户的工程师绩效数据范围"""
    if user.is_superuser:
        return EngPerfScopeContext(scope_type="ALL")

    # 1. 优先从 RoleDataScope 读取 resource_type="engineer_performance"
    scopes = PermissionService.get_user_data_scopes(db, user.id)
    scope_type = scopes.get("engineer_performance")

    # 2. 降级到 Role.data_scope
    if not scope_type:
        for user_role in user.roles:
            if user_role.role and user_role.role.is_active:
                scope_type = user_role.role.data_scope
                break

    scope_type = scope_type or "OWN"

    # 3. 解析可访问的部门ID列表
    if scope_type in ("DEPARTMENT", "BUSINESS_UNIT", "TEAM"):
        accessible_dept_ids = DataScopeServiceEnhanced.get_accessible_org_units(
            db, user.id, scope_type
        )
    elif scope_type == "ALL":
        accessible_dept_ids = None  # None 表示不限
    else:
        accessible_dept_ids = []  # OWN: 空列表，由 user_id 过滤

    return EngPerfScopeContext(
        scope_type=scope_type,
        user_id=user.id,
        accessible_dept_ids=accessible_dept_ids,
    )
```

### 4.2 与 Tenant 的关系

`PerformanceResult` 表目前没有 `tenant_id` 字段。由于当前是单租户部署，**Phase A 暂不处理 tenant 隔离**。但 Phase C 应补齐。

### 4.3 与 Department / Team / OrganizationUnit 的关系

| 现有字段 | 位置 | 是否可用 |
|---------|------|---------|
| `PerformanceResult.department_id` | 绩效结果表 | **可用**，核心 scope 过滤字段 |
| `User.department_id` | 用户表 | 可用于关联查询 |
| `User.reporting_to` | 用户表 | 可用于 TEAM scope（查直属下级） |
| `EngineerProfile.user_id` → `User.department_id` | 间接关联 | 列表查询需 JOIN |
| `CollaborationRating.rater_id` / `ratee_id` | 协作评价表 | 需通过 user_id JOIN 到 department |
| `KnowledgeContribution.contributor_id` | 知识贡献表 | 同上 |
| `OrganizationUnit.path` | 组织树 | **已可用于高效子树查询** |

**关键问题：** `PerformanceResult.department_id` 是直接字段，可直接过滤。但 `CollaborationRating` 和 `KnowledgeContribution` 没有 `department_id`，需要 JOIN `User` 表。

---

## 5. 最小可落地方案（Phase A）

### 5.1 实现范围

Phase A 目标：**用最小改动堵住 P0 越权漏洞**，覆盖排名和个人详情接口。

#### 5.1.1 新增文件

```
app/services/engineer_performance/engperf_scope.py   # scope 解析 + 过滤
```

核心代码骨架：

```python
@dataclass
class EngPerfScopeContext:
    scope_type: str           # OWN / TEAM / DEPARTMENT / ALL
    user_id: int
    accessible_dept_ids: Optional[List[int]]  # None=不限, []=仅自己
    accessible_user_ids: Optional[List[int]]  # TEAM scope 用

def resolve_engperf_scope(db: Session, user: User) -> EngPerfScopeContext:
    """解析 scope（见 4.1 节）"""

def apply_ranking_scope(
    query: Query, scope: EngPerfScopeContext
) -> Query:
    """排名查询注入 scope 过滤"""
    if scope.scope_type == "ALL":
        return query
    if scope.scope_type == "OWN":
        return query.filter(PerformanceResult.user_id == scope.user_id)
    if scope.accessible_dept_ids is not None:
        return query.filter(
            PerformanceResult.department_id.in_(scope.accessible_dept_ids)
        )
    return query.filter(False)  # fail-closed

def can_view_engineer(scope: EngPerfScopeContext, target_user_id: int,
                       target_dept_id: Optional[int]) -> bool:
    """单条记录访问判断"""
    if scope.scope_type == "ALL":
        return True
    if scope.scope_type == "OWN":
        return target_user_id == scope.user_id
    if scope.accessible_dept_ids and target_dept_id:
        return target_dept_id in scope.accessible_dept_ids
    if scope.accessible_user_ids:
        return target_user_id in scope.accessible_user_ids
    return False
```

#### 5.1.2 需改动的文件（6个）

| 文件 | 改动内容 | 改动量 |
|------|---------|-------|
| `ranking_service.py` | `get_ranking()` 接收 `scope` 参数，注入过滤 | ~10 行 |
| `ranking.py` (endpoint) | 调用 `resolve_engperf_scope`，传入 service | ~15 行/接口 |
| `engineer.py` (endpoint) | `/{user_id}` 系列接口加 `can_view_engineer` 校验 | ~8 行/接口 |
| `summary.py` (endpoint) | company summary 加 scope 过滤或限权 | ~10 行 |
| `ranking_service.py` | `get_company_summary()` 接收 scope | ~8 行 |
| `engineer_performance_service.py` | 透传 scope 到 ranking_service | ~5 行 |

#### 5.1.3 优先改造顺序

```
1. GET /ranking            → 注入 dept scope 过滤（堵最大漏洞）
2. GET /ranking/by-department → 验证 department_id 在 scope 内
3. GET /ranking/by-job-type   → 同 1
4. GET /ranking/top          → 同 1
5. GET /engineer/{user_id}   → can_view_engineer 校验
6. GET /engineer/{user_id}/trend → 同 5
7. GET /engineer/{user_id}/comparison → 同 5
8. GET /summary/company      → 限 ALL scope 或改为 scope 内汇总
```

### 5.2 Phase A 不做的事

- 不改 `CollaborationRating` / `KnowledgeContribution` 的查询（P1/P2，Phase B）
- 不加 `tenant_id`（Phase C）
- 不改前端（Phase A 只做后端拦截，前端自然看不到无权数据）
- 不新建数据库表或加列（复用现有 `Role.data_scope` + `RoleDataScope`）

---

## 6. Phase B / C 计划

### Phase B：协作评价 + 知识贡献 scope 覆盖（Sprint 3 后半）

| 任务 | 复杂度 | 说明 |
|------|--------|------|
| `collaboration.py` 接口加 scope | 中 | `CollaborationRating` 无 `department_id`，需 JOIN User |
| `knowledge.py` 接口加 scope | 中 | 同上，`KnowledgeContribution` 需 JOIN |
| 管理操作加功能权限 | 低 | `auto-complete`、`auto-select` 加 `require_permission` |
| 前端接入 `dataScopes["engineer_performance"]` | 中 | `usePermission().getDataScope("engineer_performance")` 过滤UI |

### Phase C：多租户 + 审计（Sprint 4）

| 任务 | 复杂度 | 说明 |
|------|--------|------|
| `PerformanceResult` 加 `tenant_id` | 高 | 需 migration + 数据回填 |
| `EngineerProfile` 加 `tenant_id` | 高 | 同上 |
| 接入 `@require_tenant_isolation` | 低 | 已有装饰器 |
| 数据访问审计日志 | 中 | 敏感数据（绩效分数）应记录谁看了谁的 |

---

## 7. 修改难度与风险评估

### 7.1 Phase A 评估

| 维度 | 评估 |
|------|------|
| **代码改动量** | ~150 行新增，~50 行修改，1 个新文件 |
| **改动范围** | 6 个文件，均在 `engineer_performance` 目录内 |
| **数据库变更** | 无。复用现有 `RoleDataScope` 表，需插入 `resource_type="engineer_performance"` 的配置数据 |
| **接口兼容性** | 100% 向后兼容。返回数据减少（看到的数据变少），不影响接口签名 |
| **测试策略** | 需覆盖 OWN/TEAM/DEPT/ALL 四种 scope × 8 个接口 = 32 个用例 |
| **回滚方案** | 删除 `engperf_scope.py`，恢复 endpoint 改动即可 |
| **风险点** | 1. `PerformanceResult.department_id` 可能有 NULL 值（需 fallback 处理） |
| | 2. 用户未关联 `EmployeeOrgAssignment` 时 `get_accessible_org_units` 返回空 |
| | 3. TEAM scope 依赖 `User.reporting_to`，需确认数据完整性 |

### 7.2 风险缓解

| 风险 | 缓解措施 |
|------|---------|
| `department_id` 为 NULL | Scope 过滤时 NULL 记录默认不可见（fail-closed），管理员 scope=ALL 不受影响 |
| 用户无组织关联 | `resolve_engperf_scope` 降级为 OWN，日志告警 |
| TEAM scope 数据缺失 | Phase A 可暂时将 TEAM 等效为 OWN，Phase B 补齐 `reporting_to` 查询 |
| 前端因数据减少出现空白页 | Phase A 不改前端，但需通知前端同事做空状态处理 |

---

## 8. 实施检查清单

### Phase A（建议工期：3 天）

- [ ] 创建 `app/services/engineer_performance/engperf_scope.py`
- [ ] 实现 `resolve_engperf_scope()` 对接 `RoleDataScope` + `Role.data_scope`
- [ ] 实现 `apply_ranking_scope()` 查询过滤器
- [ ] 实现 `can_view_engineer()` 单条记录校验
- [ ] 改造 `ranking.py` 4 个接口注入 scope
- [ ] 改造 `engineer.py` 的 `/{user_id}` 系列接口（3个）
- [ ] 改造 `summary.py` 的 company summary 接口
- [ ] 准备 seed data：为现有角色插入 `engineer_performance` 的 `RoleDataScope` 记录
- [ ] 编写单元测试（32 个用例）
- [ ] 编写集成测试：不同角色访问同一排名接口的返回差异

### Phase B（建议工期：3 天）

- [ ] 协作评价接口 scope 改造（需 JOIN User 获取 department）
- [ ] 知识贡献接口 scope 改造（同上）
- [ ] 管理操作加 `require_permission` 装饰器
- [ ] 前端 `useModuleAccess` 接入 `engineer_performance` scope
- [ ] 补充 `MODULE_PERMISSIONS` 中的 `engineer_performance` 条目

### Phase C（建议工期：5 天）

- [ ] 设计 migration：`PerformanceResult` / `EngineerProfile` 加 `tenant_id`
- [ ] 数据回填脚本
- [ ] 接入 `@require_tenant_isolation`
- [ ] 敏感数据访问审计日志

---

## 附录：现有基础设施可复用清单

| 组件 | 文件 | 复用方式 |
|------|------|---------|
| Role.data_scope | `app/models/user.py:155` | 读取默认 scope |
| RoleDataScope | `app/models/permission.py` | 读取 `resource_type="engineer_performance"` |
| ScopeType 枚举 | `app/models/permission.py` | ALL/DEPARTMENT/TEAM/OWN/CUSTOM |
| DataScopeServiceEnhanced | `app/services/data_scope_service_enhanced.py` | `get_accessible_org_units()`, `apply_data_scope()` |
| PermissionService | `app/services/permission_service.py` | `get_user_data_scopes()` |
| sales_permissions 参考实现 | `app/core/sales_permissions.py` | `filter_sales_data_by_scope()` 是最佳参照 |
| 前端 usePermission | `frontend/src/hooks/usePermission.js` | `getDataScope("engineer_performance")` |
| 前端 PermissionContext | `frontend/src/context/PermissionContext.jsx` | 已支持 `dataScopes` 下发 |
