# API权限配置审计报告

> 生成时间：2026-01-XX  
> 检查脚本：`scripts/check_api_permissions.py`

## 📊 执行摘要

**重要发现**：经过详细分析，并非所有API端点都需要权限检查。需要区分不同类型的端点。

### 统计数据

- **总API端点数**：1,498 个
- **实际需要权限检查**：1,054 个 (70.4%)
- **不需要权限检查**：53 个 (3.5%)
  - 公开API（登录、健康检查等）：44 个
  - 个人数据API（用户查看自己的数据）：9 个
- **需要评估**：391 个 (26.1%)
- **已配置权限**：23 个 (2.2% of 需要权限的端点)
- **未配置权限**：1,031 个 (97.8% of 需要权限的端点)

### 权限数据库状态

- **数据库中的权限总数**：67 个
- **代码中使用的权限**：13 个
- **缺失的权限**：13 个（代码中使用但数据库不存在）

---

## 📋 API端点分类说明

### 哪些端点需要权限检查？

#### ✅ 不需要权限检查的端点（53个）

1. **公开API（44个）**
   - 认证相关：`/auth/login`, `/auth/logout`, `/auth/refresh`
   - 健康检查：`/health`
   - 说明：这些API是系统基础功能，无需权限控制

2. **个人数据API（9个）**
   - 用户查看自己的数据：`/my/performance`, `/me`, `/my/bonus` 等
   - 说明：这些API只需要用户认证，不需要特定权限（用户只能查看自己的数据）

#### ⚠️ 需要评估的端点（391个）

- 简单路径的列表接口（如 `/materials`, `/projects`）
- 需要人工判断是否为公开接口或需要权限
- 建议：默认添加权限检查，除非明确为公开接口

#### 🔒 必须配置权限的端点（1,054个）

**所有业务操作API都需要权限检查**，包括：

- **CRUD操作**：创建、更新、删除
- **业务操作**：审批、提交、分配等
- **数据查询**：列表、详情（涉及他人数据）
- **管理功能**：配置、设置、导入导出等

### 各模块需要权限的端点数量

| 模块 | 需要权限的端点 | 优先级 |
|------|--------------|--------|
| 其他功能 | 316 个 | 🟢 低 |
| 销售管理 | 188 个 | 🟡 中 |
| 项目管理 | 120 个 | 🔴 高 |
| 生产管理 | 103 个 | 🟡 中 |
| 预警管理 | 83 个 | 🟢 低 |
| 工程变更 | 59 个 | 🟡 中 |
| 财务管理 | 46 个 | 🔴 高 |
| 验收管理 | 33 个 | 🟡 中 |
| 采购管理 | 28 个 | 🟡 中 |
| 绩效管理 | 25 个 | 🟡 中 |
| 物料管理 | 23 个 | 🟡 中 |
| 系统管理 | 21 个 | 🔴 高 |
| **总计** | **1,054 个** | |

---

## ❌ 问题分析

### 1. 权限编码格式不统一

**问题**：代码中使用了两种不同的权限编码格式：

#### 格式A：标准格式（推荐）
```
{module}:{resource}:{action}
```
示例：
- `project:read`
- `material:bom:manage`
- `performance:evaluation:create`

#### 格式B：旧格式（不推荐）
```
{UPPER_SNAKE_CASE}
```
示例：
- `USER_VIEW`
- `USER_CREATE`
- `ROLE_UPDATE`
- `AUDIT_VIEW`

**影响**：
- 格式不统一导致维护困难
- 旧格式不符合权限编码规范
- 需要统一迁移到标准格式

### 2. 缺失的权限定义

代码中使用了以下权限，但数据库中不存在：

| 权限编码 | 使用位置 | 建议格式 |
|---------|---------|---------|
| `USER_VIEW` | `users.py` | `system:user:read` |
| `USER_CREATE` | `users.py` | `system:user:create` |
| `USER_UPDATE` | `users.py` | `system:user:update` |
| `USER_DELETE` | `users.py` | `system:user:delete` |
| `ROLE_CREATE` | `roles.py` | `system:role:create` |
| `ROLE_UPDATE` | `roles.py` | `system:role:update` |
| `AUDIT_VIEW` | `audits.py` | `system:audit:read` |
| `performance:manage` | `performance.py` | `performance:manage` |
| `project:erp:sync` | `projects.py` | `project:erp:sync` |
| `project:erp:update` | `projects.py` | `project:erp:update` |
| `work_log:config:create` | `work_log.py` | `work_log:config:create` |
| `work_log:config:read` | `work_log.py` | `work_log:config:read` |
| `work_log:config:update` | `work_log.py` | `work_log:config:update` |

### 3. 大量业务API端点未配置权限

**影响范围**：
- **1,054个需要权限的端点中，只有23个已配置权限**
- **未配置权限比例：97.8%**
- 包括敏感操作（创建、更新、删除）也未受保护
- 存在严重的安全风险

**主要未配置权限的模块**（按优先级排序）：

**🔴 高优先级（立即处理）**：
- 系统管理 (`users.py`, `roles.py`) - 21个端点
- 财务管理 (`budget.py`, `costs.py`, `bonus.py`) - 46个端点
- 项目管理 (`projects.py`) - 120个端点

**🟡 中优先级（1-2周内）**：
- 销售管理 (`sales.py`) - 188个端点
- 生产管理 (`production.py`) - 103个端点
- 工程变更 (`ecn.py`) - 59个端点
- 验收管理 (`acceptance.py`) - 33个端点
- 采购管理 (`purchase.py`) - 28个端点
- 物料管理 (`materials.py`) - 23个端点

**🟢 低优先级（逐步完善）**：
- 预警管理 (`alerts.py`) - 83个端点
- 其他辅助功能 - 316个端点

---

## ✅ 解决方案

### 阶段1：补充缺失的权限定义（立即执行）

创建迁移脚本，添加代码中已使用但数据库中不存在的权限：

**文件**：`migrations/202601XX_missing_permissions_sqlite.sql`

```sql
-- 补充缺失的权限定义 (SQLite)
BEGIN;

-- 系统管理模块权限（统一格式）
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('system:user:read', '用户查看', 'system', 'user', 'read'),
('system:user:create', '用户创建', 'system', 'user', 'create'),
('system:user:update', '用户更新', 'system', 'user', 'update'),
('system:user:delete', '用户删除', 'system', 'user', 'delete'),
('system:role:create', '角色创建', 'system', 'role', 'create'),
('system:role:update', '角色更新', 'system', 'role', 'update'),
('system:audit:read', '审计查看', 'system', 'audit', 'read');

-- 绩效管理模块权限
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('performance:manage', '绩效管理', 'performance', 'performance', 'manage'),
('performance:evaluation:read', '绩效评估查看', 'performance', 'evaluation', 'read'),
('performance:evaluation:create', '绩效评估创建', 'performance', 'evaluation', 'create'),
('performance:evaluation:update', '绩效评估更新', 'performance', 'evaluation', 'update');

-- 项目管理模块扩展权限
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('project:erp:sync', 'ERP同步', 'project', 'erp', 'sync'),
('project:erp:update', 'ERP更新', 'project', 'erp', 'update');

-- 工作日志模块权限
INSERT OR IGNORE INTO permissions (perm_code, perm_name, module, resource, action) VALUES
('work_log:config:read', '工作日志配置查看', 'work_log', 'config', 'read'),
('work_log:config:create', '工作日志配置创建', 'work_log', 'config', 'create'),
('work_log:config:update', '工作日志配置更新', 'work_log', 'config', 'update');

COMMIT;
```

### 阶段2：统一权限编码格式（短期）

将旧格式的权限编码迁移到标准格式：

1. **更新代码中的权限编码**
   - `USER_VIEW` → `system:user:read`
   - `USER_CREATE` → `system:user:create`
   - `USER_UPDATE` → `system:user:update`
   - `USER_DELETE` → `system:user:delete`
   - `ROLE_CREATE` → `system:role:create`
   - `ROLE_UPDATE` → `system:role:update`
   - `AUDIT_VIEW` → `system:audit:read`

2. **创建数据迁移脚本**
   - 在数据库中创建新格式的权限
   - 将角色权限关联从旧格式迁移到新格式
   - 删除旧格式的权限（可选）

### 阶段3：为业务API端点添加权限检查（长期）

**注意**：只需要为 **1,054个业务API端点** 添加权限检查，不需要为公开API和个人数据API添加。

**优先级排序**：

#### 🔴 高优先级（立即处理，约187个端点）
1. **系统管理** (`users.py`, `roles.py`, `audits.py`) - 21个端点
   - 系统安全核心，必须立即处理
2. **财务管理** (`budget.py`, `costs.py`, `bonus.py`) - 46个端点
   - 涉及资金安全，必须立即处理
3. **项目管理** (`projects.py`) - 120个端点
   - 核心业务模块，必须立即处理

#### 🟡 中优先级（1-2周内，约440个端点）
4. **销售管理** (`sales.py`, `presale.py`) - 188个端点
5. **生产管理** (`production.py`, `assembly_kit.py`) - 103个端点
6. **工程变更** (`ecn.py`) - 59个端点
7. **验收管理** (`acceptance.py`) - 33个端点
8. **采购管理** (`purchase.py`, `outsourcing.py`) - 28个端点
9. **物料管理** (`materials.py`, `bom.py`) - 23个端点
10. **绩效管理** (`performance.py`) - 25个端点

#### 🟢 低优先级（逐步完善，约427个端点）
11. **预警管理** (`alerts.py`, `shortage.py`) - 83个端点
12. **其他辅助功能** - 316个端点
    - 报表、统计、通知等
    - 可以逐步完善

**实施步骤**：

1. **为每个模块定义权限**
   ```sql
   -- 示例：物料管理模块
   INSERT INTO permissions (perm_code, perm_name, module, resource, action) VALUES
   ('material:material:read', '物料查看', 'material', 'material', 'read'),
   ('material:material:create', '物料创建', 'material', 'material', 'create'),
   ('material:material:update', '物料更新', 'material', 'material', 'update'),
   ('material:material:delete', '物料删除', 'material', 'material', 'delete'),
   ('material:bom:read', 'BOM查看', 'material', 'bom', 'read'),
   ('material:bom:manage', 'BOM管理', 'material', 'bom', 'manage');
   ```

2. **在API端点中添加权限检查**
   ```python
   @router.get("/materials", response_model=List[MaterialResponse])
   async def list_materials(
       current_user: User = Depends(require_permission("material:material:read")),
       db: Session = Depends(get_db),
   ):
       # ...
   ```

3. **分配权限给角色**
   ```sql
   -- 为项目经理角色分配物料查看权限
   INSERT INTO role_permissions (role_id, permission_id)
   SELECT r.id, p.id
   FROM roles r, permissions p
   WHERE r.role_code = 'PM' AND p.perm_code = 'material:material:read';
   ```

---

## 📋 权限编码规范

### 标准格式

```
{module}:{resource}:{action}
```

### 模块划分

| 模块 | 说明 | 示例 |
|------|------|------|
| `system` | 系统管理 | `system:user:read` |
| `project` | 项目管理 | `project:project:read` |
| `material` | 物料管理 | `material:bom:manage` |
| `purchase` | 采购管理 | `purchase:order:create` |
| `sales` | 销售管理 | `sales:order:read` |
| `production` | 生产管理 | `production:plan:manage` |
| `finance` | 财务管理 | `finance:payment:approve` |
| `ecn` | 工程变更 | `ecn:ecn:create` |
| `performance` | 绩效管理 | `performance:evaluation:read` |
| `work_log` | 工作日志 | `work_log:config:read` |

### 操作类型（action）

| Action | 说明 | 示例 |
|--------|------|------|
| `read` | 查看 | `project:read` |
| `create` | 创建 | `project:create` |
| `update` | 更新 | `project:update` |
| `delete` | 删除 | `project:delete` |
| `manage` | 管理（包含所有操作） | `project:manage` |
| `approve` | 审批 | `project:approve` |
| `submit` | 提交 | `project:submit` |

---

## 🔍 检查工具

使用 `scripts/check_api_permissions.py` 定期检查：

```bash
python3 scripts/check_api_permissions.py
```

**输出内容**：
- 未配置权限的API端点列表
- 代码中使用的权限编码
- 数据库中缺失的权限
- 数据库中的权限列表（按模块分组）

---

## 📝 实施检查清单

### 阶段1：补充缺失权限
- [ ] 创建迁移脚本 `migrations/202601XX_missing_permissions_sqlite.sql`
- [ ] 创建迁移脚本 `migrations/202601XX_missing_permissions_mysql.sql`
- [ ] 执行迁移脚本
- [ ] 验证权限已创建

### 阶段2：统一权限格式
- [ ] 更新 `users.py` 中的权限编码
- [ ] 更新 `roles.py` 中的权限编码
- [ ] 更新 `audits.py` 中的权限编码
- [ ] 创建数据迁移脚本（旧格式 → 新格式）
- [ ] 执行迁移并验证

### 阶段3：为API端点添加权限
- [ ] 用户管理模块（高优先级）
- [ ] 角色管理模块（高优先级）
- [ ] 项目管理模块（高优先级）
- [ ] 物料管理模块（中优先级）
- [ ] 采购管理模块（中优先级）
- [ ] 其他模块（逐步完善）

---

## ⚠️ 注意事项

1. **向后兼容**：在迁移权限编码时，需要确保现有角色权限关联不受影响
2. **测试验证**：每次添加权限后，需要测试API端点的权限检查是否正常工作
3. **文档更新**：更新API文档，说明每个端点所需的权限
4. **角色分配**：添加新权限后，需要为相应角色分配权限

---

## 📚 参考文档

- [权限系统完整指南](./PERMISSION_SYSTEM_COMPLETE_GUIDE.md)
- [系统功能与权限指南](./SYSTEM_FUNCTIONS_AND_PERMISSIONS_GUIDE.md)
- [权限机制说明](./PERMISSION_MECHANISM_EXPLANATION.md)
