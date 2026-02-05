# 用户角色权限管理系统 - 问题分析与修改建议

> 分析日期：2026-02-05
> 范围：全系统权限架构、认证安全、API 端点权限一致性、数据范围控制

---

## 目录

1. [总体评估](#1-总体评估)
2. [严重安全漏洞](#2-严重安全漏洞)
3. [权限模型设计问题](#3-权限模型设计问题)
4. [API 端点权限一致性](#4-api-端点权限一致性)
5. [数据范围（Data Scope）执行缺失](#5-数据范围data-scope执行缺失)
6. [认证与会话安全](#6-认证与会话安全)
7. [多租户隔离缺陷](#7-多租户隔离缺陷)
8. [缓存与性能问题](#8-缓存与性能问题)
9. [测试覆盖不足](#9-测试覆盖不足)
10. [修改建议优先级清单](#10-修改建议优先级清单)

---

## 1. 总体评估

### 系统现状

| 维度 | 状态 | 评分 |
|------|------|------|
| API 级权限控制 | 约 86% 端点有权限检查 | **B** |
| 数据级权限控制 | 模型已定义，但仅项目模块实际执行 | **D** |
| 认证安全 | JWT 实现基本完整，存在若干缺陷 | **B-** |
| 多租户隔离 | 部分查询缺少 tenant 过滤 | **C** |
| 权限初始化 | 新 ApiPermission 表无种子数据 | **D** |
| 测试覆盖 | 数据范围测试仅检查实例化 | **D** |

### 架构概览

```
请求 → GlobalAuthMiddleware(JWT验证)
     → TenantContextMiddleware(租户上下文)
     → AuditMiddleware(审计日志)
     → API Endpoint
       └── require_permission("module:action")  ← API级控制
           └── check_permission()
               ├── is_superuser? → 全部放行
               ├── is_system_admin()? → 硬编码角色名匹配 ⚠️
               └── 递归查询角色权限(含继承)
       └── 数据范围过滤 ← 大部分端点缺失 ⚠️
```

---

## 2. 严重安全漏洞

### 2.1 硬编码管理员角色名导致权限提升 (P0)

**位置**: `app/core/auth.py:326-351`

```python
def is_system_admin(user: User) -> bool:
    admin_role_codes = {"admin", "super_admin", "system_admin"}  # 硬编码
    admin_role_names = {"系统管理员", "超级管理员", "管理员"}     # 硬编码
    for user_role in roles or []:
        role = getattr(user_role, "role", user_role)
        role_code = (getattr(role, "role_code", "") or "").lower()
        if role_code in admin_role_codes:
            return True  # 任何名为 "admin" 的角色自动获得全部权限
```

**问题**:
- 任何人创建 `role_code = "admin"` 的角色后，拥有该角色的用户自动获得全部系统权限
- 角色创建端点 (`POST /api/v1/roles/`) 未校验角色名是否为保留字
- `role_name` 匹配不区分大小写，但仅 `role_code` 做了 `.lower()` 处理，`role_name` 没有

**攻击路径**:
```
1. 租户管理员创建角色 role_code="admin", role_name="普通角色"
2. 将该角色分配给目标用户
3. 目标用户自动绕过所有权限检查，获得超级管理员权限
```

**修改建议**:
- 移除 `is_system_admin()` 中的硬编码字符串匹配
- 仅通过 `User.is_superuser` 和 `User.is_tenant_admin` 数据库字段判断管理员身份
- 如需保留系统角色概念，使用 `Role.is_system = True` 标志位，且禁止通过 API 创建 `is_system` 角色

---

### 2.2 未认证的 API 端点 (P0)

**位置**: `app/api/v1/endpoints/node_tasks.py`

以下端点没有任何认证或权限检查，任何人可直接访问：

| 端点 | 方法 | 风险 |
|------|------|------|
| `/node-tasks/user/{user_id}` | GET | 枚举任意用户任务 |
| `/node-tasks/{task_id}` | GET | 查看任意任务详情 |
| `/node-tasks/node/{node_instance_id}` | GET | 查看节点任务列表 |
| `/node-tasks/node/{node_instance_id}/progress` | GET | 查看节点进度 |

**修改建议**: 所有端点添加 `Depends(require_permission("task:read"))`

---

### 2.3 敏感操作缺乏权限检查 (P0)

以下关键操作仅检查用户已登录，未检查具体权限：

| 端点 | 文件 | 问题 |
|------|------|------|
| `POST /bom/headers/{id}/approve` | `bom/bom_approve.py` | BOM 审批 - 任何登录用户可审批 |
| `POST /ecns` | `ecn/core.py` | ECN 创建 - 无权限检查 |
| `PUT /ecns/{id}` | `ecn/core.py` | ECN 更新 - 无权限检查 |
| `PUT /ecns/{id}/submit` | `ecn/core.py` | ECN 提交 - 无权限检查 |

**修改建议**: 替换 `get_current_active_user` 为对应的 `require_permission()` 调用

---

### 2.4 登录接口用户名枚举 (P1)

**位置**: `app/api/v1/endpoints/auth.py:49-97`

登录失败时返回不同的错误码，允许攻击者判断用户名是否存在：

```python
# 用户不存在 → USER_NOT_FOUND
# 密码错误   → WRONG_PASSWORD
# 账号禁用   → USER_DISABLED
# 账号未激活 → USER_INACTIVE
```

**修改建议**: 统一返回 `"用户名或密码错误"` 单一错误信息，不区分失败原因

---

### 2.5 RoleApiPermission 缺少唯一约束 (P1)

**位置**: `app/models/user.py:229-244`

```python
class RoleApiPermission(Base):
    __tablename__ = "role_api_permissions"
    id = Column(Integer, primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id"))
    permission_id = Column(Integer, ForeignKey("api_permissions.id"))
    # 没有 UniqueConstraint("role_id", "permission_id") ⚠️
```

对比 `RoleMenu` 有 `UniqueConstraint("role_id", "menu_id")`，`RoleDataScope` 有 `UniqueConstraint("role_id", "resource_type")`。

**影响**: 同一权限可重复分配给同一角色，造成数据不一致

**修改建议**: 添加复合唯一约束：
```python
__table_args__ = (
    UniqueConstraint("role_id", "permission_id", name="uk_role_api_permission"),
)
```

---

## 3. 权限模型设计问题

### 3.1 权限码格式不统一 (P1)

系统中存在两种互不兼容的权限码格式：

| 格式 | 示例 | 使用位置 | 数量 |
|------|------|----------|------|
| 小写+冒号 | `project:read`, `ecn:approve` | 大部分端点 | ~92 个 |
| 大写+下划线 | `USER_VIEW`, `ROLE_VIEW` | `permissions/matrix.py`, `users/crud_refactored.py` | 6 个 |

**问题**: `check_permission()` 进行精确字符串匹配，格式不一致会导致权限检查静默失败（返回 False）

**修改建议**: 统一为 `小写:冒号` 格式 (`user:view`, `role:view`)，在权限注册时强制格式校验

### 3.2 新旧权限模型并存 (P1)

| 模型 | 表名 | 状态 |
|------|------|------|
| (旧) Permission | `permissions` | 迁移中仍有种子数据 |
| (旧) RolePermission | `role_permissions` | 迁移中仍有种子数据 |
| (新) ApiPermission | `api_permissions` | **无种子数据** |
| (新) RoleApiPermission | `role_api_permissions` | 空表 |

**问题**: 代码已切换到新 `ApiPermission` 模型，但数据库中该表为空。系统依赖 `is_superuser` 和硬编码管理员名来工作，普通用户实际上无法获取任何权限。

**修改建议**:
1. 创建 `api_permissions` 种子数据迁移文件
2. 根据所有端点使用的权限码生成完整的权限列表
3. 为默认角色（管理员、项目经理、工程师等）分配对应权限
4. 清理旧表引用

### 3.3 权限依赖链缺失 (P2)

旧系统有 `depends_on` 字段，新系统已移除。无法表达：
- "创建项目" 必须先有 "查看项目" 权限
- "审批 ECN" 必须先有 "查看 ECN" 权限

**修改建议**: 在权限分配逻辑中添加隐式依赖：分配 `project:create` 时自动包含 `project:read`

### 3.4 角色管理绕过权限系统 (P2)

**位置**: `app/api/v1/endpoints/roles.py:36-44`

```python
def require_role_management_permission(current_user):
    if current_user.is_superuser or current_user.is_tenant_admin:
        return current_user
    raise HTTPException(status_code=403, detail="需要角色管理权限")
```

这是一个硬编码的权限检查，完全绕过了数据库驱动的权限系统。

**修改建议**: 替换为 `require_permission("role:manage")` 并在 `api_permissions` 中注册该权限

---

## 4. API 端点权限一致性

### 4.1 权限检查覆盖率

```
总端点文件数:    ~578
有权限检查:      ~497 (86%)
仅认证无权限:    ~50+
完全无认证:      ~81  (14%)
```

### 4.2 缺少权限检查的关键模块

| 模块 | 文件 | 缺失检查 |
|------|------|----------|
| 销售-商机 | `sales/opportunities.py` | 无认证 |
| 销售-线索 | `sales/leads.py` | 无认证 |
| 销售-统计 | `sales/statistics.py` | 无认证 |
| 组织-员工 | `organization/employees.py` | 无认证 |
| BOM-审批 | `bom/bom_approve.py` | 仅认证无权限 |
| ECN-核心 | `ecn/core.py` | 仅认证无权限 |
| 节点任务 | `node_tasks.py` | 完全无认证 |

### 4.3 修改建议

1. 对所有端点进行权限码审计，生成完整映射表
2. 为每个模块定义标准权限集：`module:view`, `module:create`, `module:update`, `module:delete`, `module:approve`
3. 添加启动检查：扫描所有路由，警告缺少权限检查的端点

---

## 5. 数据范围（Data Scope）执行缺失

### 5.1 现状

数据范围系统定义了 7 个层级：

```
ALL(全部) → BUSINESS_UNIT(事业部) → DEPARTMENT(部门) → TEAM(团队)
→ PROJECT(项目) → OWN(个人) → CUSTOM(自定义)
```

**模型已就绪**: `DataScopeRule`、`RoleDataScope` 表已定义

**实际执行**: 仅项目模块（11 个文件）调用了数据范围过滤

### 5.2 问题影响

| 模块 | 数据范围执行 | 风险 |
|------|-------------|------|
| 项目管理 | 已实现 | 低 |
| 采购管理 | 未实现 | 高 - 可查看所有采购单 |
| 物料管理 | 未实现 | 中 - 可查看所有物料 |
| 客户管理 | 未实现 | 高 - 可查看所有客户信息 |
| 问题管理 | 未实现 | 中 - 可查看所有问题记录 |
| 工时管理 | 未实现 | 中 - 可查看其他人工时 |
| 预警管理 | 未实现 | 低 |
| 销售管理 | 未实现 | 高 - 可查看所有商机 |

### 5.3 修改建议

**方案 A: 全局中间件方式**（推荐）

创建通用数据范围过滤依赖：

```python
# app/api/deps.py
def get_data_scope_filter(resource_type: str):
    def _filter(
        current_user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> DataScopeFilter:
        scope = PermissionService.get_user_data_scope(db, current_user.id, resource_type)
        return DataScopeFilter(user=current_user, scope=scope)
    return _filter
```

**方案 B: 查询装饰器方式**

```python
@apply_data_scope("project")
def list_projects(query, scope_filter):
    return query  # 自动注入 WHERE 条件
```

---

## 6. 认证与会话安全

### 6.1 Token 黑名单不持久 (P1)

**位置**: `app/core/auth.py:32-34`

```python
_token_blacklist = set()  # 内存存储，重启丢失
```

当 Redis 不可用时，登出的 Token 在应用重启后重新生效。

**修改建议**:
- 生产环境强制要求 Redis
- 或添加数据库级 Token 版本号：用户表增加 `token_version` 字段，每次登出/改密码时递增，JWT 中携带版本号，验证时比对

### 6.2 修改密码未吊销所有 Token (P2)

**位置**: `app/api/v1/endpoints/auth.py:253`

仅吊销当前请求使用的 Token，其他设备的 Token 仍然有效。

**修改建议**: 修改密码时递增 `token_version`，使所有旧 Token 失效

### 6.3 Token Refresh 缺少速率限制 (P2)

**位置**: `app/api/v1/endpoints/auth.py:132`

`/refresh` 端点无速率限制，可被滥用进行 Token 刷新攻击。

**修改建议**: 添加 `@limiter.limit("10/minute")`

### 6.4 CSRF 保护在 DEBUG 模式下完全禁用 (P2)

**位置**: `app/core/csrf.py:75-77`

```python
if settings.DEBUG:
    return  # 完全跳过 CSRF 校验
```

**修改建议**: 使用独立的 `CSRF_ENABLED` 配置项，不绑定 DEBUG 标志

### 6.5 CSP Nonce 未实际生成 (P3)

**位置**: `app/core/security_headers.py:54-66`

CSP 头中包含 `'nonce-{nonce}'` 占位符，但实际未生成 nonce 值，导致该安全头无效。

---

## 7. 多租户隔离缺陷

### 7.1 角色查询缺少租户过滤 (P1)

**位置**: `app/api/v1/endpoints/roles.py:126-127`

```python
roles = db.query(Role).filter(Role.is_active == True).order_by(Role.sort_order).all()
# 缺少 .filter(or_(Role.tenant_id == current_tenant, Role.tenant_id.is_(None)))
```

**影响**: 一个租户可以看到其他租户的自定义角色

**相关位置**:
- `roles.py:100` - `get_role_templates()` 同样缺少租户过滤
- `roles.py:204` - `_get_parent_roles()` 递归查询无租户检查

### 7.2 缓存键碰撞风险 (P3)

**位置**: `app/services/permission_cache_service.py:49-61`

```python
tid = tenant_id if tenant_id is not None else 0  # None → 0
key = f"perm:t{tid}:user:{user_id}"
```

当 `tenant_id=None`（系统级）和 `tenant_id=0`（如果存在）时缓存键相同。

**修改建议**: 使用 `"system"` 而非 `0` 表示系统级缓存键

---

## 8. 缓存与性能问题

### 8.1 is_system_admin() 每次请求执行 (P3)

`check_permission()` 中每次都调用 `is_system_admin()`，该函数遍历用户所有角色并进行字符串匹配。对于高频 API 调用，这是不必要的开销。

**修改建议**: 在 `request.state` 中缓存 `is_admin` 结果

### 8.2 ORM 回退查询存在 N+1 问题 (P3)

当缓存和 SQL 查询都失败时，回退到 ORM 关系遍历，可能触发 N+1 查询。

**修改建议**: 添加 `joinedload` 或 `selectinload` 到回退查询

---

## 9. 测试覆盖不足

### 9.1 数据范围测试 (P1)

**位置**: `tests/unit/test_data_scope_service.py`

```python
def test_data_scope_service_instantiation(self, db_session):
    service = DataScopeService(db_session)
    assert service is not None  # 仅检查实例化！
```

**需要补充**:
- 部门级过滤：用户只能看到本部门数据
- 项目级过滤：用户只能看到参与项目的数据
- 跨租户隔离：用户不能看到其他租户数据
- 角色继承后的数据范围合并

### 9.2 权限检查测试

**需要补充**:
- 未授权用户访问受保护端点 → 403
- 权限码格式不匹配时的行为
- 角色继承链中权限的正确传递
- 缓存失效后权限的重新加载

### 9.3 安全测试

**需要补充**:
- 管理员角色名注入测试（创建 role_code="admin" 是否被拒绝）
- Token 过期后的请求处理
- 并发登录/登出的 Token 状态
- CSRF Token 验证

---

## 10. 修改建议优先级清单

### P0 - 立即修复（安全漏洞）

| # | 问题 | 建议 | 影响文件 |
|---|------|------|----------|
| 1 | 硬编码管理员角色名 | 移除 `is_system_admin()` 中的字符串匹配，改用数据库标志 | `app/core/auth.py` |
| 2 | 未认证端点 | 为 `node_tasks.py` 所有端点添加权限检查 | `app/api/v1/endpoints/node_tasks.py` |
| 3 | BOM/ECN 缺乏权限 | 添加 `require_permission()` 调用 | `bom/bom_approve.py`, `ecn/core.py` |
| 4 | 登录用户名枚举 | 统一错误信息为"用户名或密码错误" | `app/api/v1/endpoints/auth.py` |

### P1 - 短期修复（1-2 周）

| # | 问题 | 建议 | 影响文件 |
|---|------|------|----------|
| 5 | ApiPermission 无种子数据 | 创建完整的权限种子迁移文件 | `migrations/` |
| 6 | 权限码格式不统一 | 统一为小写冒号格式 | 多个端点文件 |
| 7 | RoleApiPermission 缺少唯一约束 | 添加复合唯一约束 | `app/models/user.py` |
| 8 | 角色查询缺少租户过滤 | 添加 tenant_id 过滤条件 | `app/api/v1/endpoints/roles.py` |
| 9 | Token 黑名单不持久 | 添加 token_version 机制 | `app/core/auth.py`, `app/models/user.py` |
| 10 | 角色创建未校验保留名 | 添加保留角色名校验 | `app/api/v1/endpoints/roles.py` |

### P2 - 中期改进（2-4 周）

| # | 问题 | 建议 |
|---|------|------|
| 11 | 数据范围未实际执行 | 实现全局数据范围过滤依赖 |
| 12 | 14% 端点缺少权限检查 | 审计并补全所有端点的权限检查 |
| 13 | 修改密码未吊销所有 Token | 实现 token_version 递增机制 |
| 14 | 角色管理绕过权限系统 | 替换硬编码检查为 require_permission() |
| 15 | Refresh 端点无速率限制 | 添加限流装饰器 |
| 16 | CSRF 绑定 DEBUG 模式 | 使用独立配置项 |

### P3 - 长期优化

| # | 问题 | 建议 |
|---|------|------|
| 17 | 权限依赖链缺失 | 添加隐式权限依赖 |
| 18 | CSP nonce 未生成 | 实现完整的 CSP nonce 机制 |
| 19 | 缓存键碰撞 | 修改 None → "system" |
| 20 | is_system_admin() 性能 | 请求级缓存 |
| 21 | 补充测试覆盖 | 数据范围、权限检查、安全测试 |
| 22 | 旧权限表清理 | 移除 `permissions`/`role_permissions` 表及种子数据 |

---

## 附录：关键文件清单

| 文件 | 行数 | 职责 |
|------|------|------|
| `app/core/auth.py` | ~459 | JWT 认证、权限检查、Token 管理 |
| `app/core/security.py` | ~30 | 安全功能导出层 |
| `app/services/permission_service.py` | ~479 | 权限服务（递归查询、数据范围） |
| `app/services/permission_cache_service.py` | ~200 | 权限缓存（TTL 10/30 分钟） |
| `app/models/user.py` | ~260 | User、Role、ApiPermission、RoleApiPermission |
| `app/models/permission.py` | ~150 | DataScopeRule、RoleDataScope、MenuPermission |
| `app/core/middleware/auth_middleware.py` | ~100 | 全局认证中间件 |
| `app/core/middleware/tenant_middleware.py` | ~80 | 租户上下文中间件 |
| `app/api/v1/endpoints/roles.py` | ~240 | 角色管理 API |
| `app/api/v1/endpoints/permissions/matrix.py` | ~280 | 权限矩阵视图 |
