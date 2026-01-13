# 权限表结构升级迁移总结

## 迁移日期
2025-01-20

## 迁移目的
统一权限表结构，添加缺失的字段，使其与模型定义完全匹配。

## 迁移内容

### 1. 添加的字段

| 字段名 | 类型 | 说明 | 默认值 |
|--------|------|------|--------|
| `resource` | VARCHAR(50) | 资源类型 | NULL |
| `description` | TEXT | 权限描述 | NULL |
| `is_active` | BOOLEAN | 是否启用 | TRUE (1) |
| `created_at` | DATETIME | 创建时间 | CURRENT_TIMESTAMP |
| `updated_at` | DATETIME | 更新时间 | CURRENT_TIMESTAMP |

### 2. 字段映射关系

**数据库字段名** → **模型属性名**
- `perm_code` → `permission_code` (通过 Column 映射)
- `perm_name` → `permission_name` (通过 Column 映射)
- `module` → `module` (直接映射)
- `resource` → `resource` (直接映射)
- `action` → `action` (直接映射)
- `description` → `description` (直接映射)
- `is_active` → `is_active` (直接映射)
- `created_at` → `created_at` (直接映射)
- `updated_at` → `updated_at` (直接映射)

### 3. 数据更新

迁移脚本自动完成以下数据更新：

1. **设置 is_active 默认值**
   - 所有现有权限的 `is_active` 字段设置为 `1` (启用)

2. **设置时间戳**
   - 所有现有权限的 `created_at` 和 `updated_at` 设置为当前时间

3. **推断 resource 字段值**
   - 从 `permission_code` 中提取 resource（格式：`module:resource:action`）
   - 例如：`project:project:read` → `resource = 'project'`
   - 例如：`ecn:ecn:create` → `resource = 'ecn'`
   - 如果提取失败，使用 `module` 作为 `resource` 的回退值

## 迁移文件

### SQLite 迁移脚本
- **文件**: `migrations/20250120_permissions_table_upgrade_sqlite.sql`
- **说明**: SQLite 数据库迁移脚本

### MySQL 迁移脚本
- **文件**: `migrations/20250120_permissions_table_upgrade_mysql.sql`
- **说明**: MySQL 数据库迁移脚本

### Python 自动化脚本
- **文件**: `scripts/apply_permissions_migration.py`
- **说明**: 自动检测数据库类型并应用迁移，安全地添加字段（避免重复添加）

## 使用方法

### 方法1：使用 Python 脚本（推荐）

```bash
python3 scripts/apply_permissions_migration.py
```

脚本会自动：
- 检测数据库类型（SQLite/MySQL）
- 检查字段是否存在
- 安全地添加缺失字段
- 更新现有数据
- 验证迁移结果

### 方法2：手动执行 SQL 脚本

**SQLite:**
```bash
sqlite3 data/app.db < migrations/20250120_permissions_table_upgrade_sqlite.sql
```

**MySQL:**
```bash
mysql -u username -p database_name < migrations/20250120_permissions_table_upgrade_mysql.sql
```

## 迁移结果验证

### 验证表结构

**SQLite:**
```sql
PRAGMA table_info(permissions);
```

**MySQL:**
```sql
DESCRIBE permissions;
```

### 验证数据

```sql
SELECT 
    id, 
    perm_code, 
    perm_name, 
    module, 
    resource, 
    action, 
    description, 
    is_active, 
    created_at, 
    updated_at 
FROM permissions 
LIMIT 5;
```

### 验证统计

```sql
-- 总权限数
SELECT COUNT(*) FROM permissions;

-- 启用权限数
SELECT COUNT(*) FROM permissions WHERE is_active = 1;

-- 有 resource 的权限数
SELECT COUNT(*) FROM permissions WHERE resource IS NOT NULL AND resource != '';

-- 按模块统计
SELECT module, COUNT(*) as count 
FROM permissions 
GROUP BY module 
ORDER BY count DESC;
```

## 迁移后的表结构

### 完整字段列表

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| `id` | INTEGER | PRIMARY KEY, AUTO_INCREMENT | 主键ID |
| `perm_code` | VARCHAR(100) | UNIQUE, NOT NULL | 权限编码 |
| `perm_name` | VARCHAR(200) | | 权限名称 |
| `module` | VARCHAR(50) | | 所属模块 |
| `resource` | VARCHAR(50) | | 资源类型 |
| `action` | VARCHAR(20) | | 操作类型 |
| `description` | TEXT | | 权限描述 |
| `is_active` | BOOLEAN | DEFAULT TRUE | 是否启用 |
| `created_at` | DATETIME | | 创建时间 |
| `updated_at` | DATETIME | | 更新时间 |

## 注意事项

1. **字段名保持兼容**
   - 数据库字段名保持为 `perm_code` 和 `perm_name`
   - 通过 SQLAlchemy 的 `Column` 映射到模型的 `permission_code` 和 `permission_name`
   - 这样既保持了数据库兼容性，又符合模型的命名规范

2. **SQLite 限制**
   - SQLite 不支持在 `ALTER TABLE ADD COLUMN` 时使用 `CURRENT_TIMESTAMP` 作为默认值
   - 迁移脚本先添加字段，然后通过 `UPDATE` 语句设置时间戳

3. **向后兼容**
   - 所有新字段都设置为可空（NULL），确保不会影响现有数据
   - `is_active` 字段默认为 `TRUE`，所有现有权限自动启用

4. **API 兼容性**
   - API 端点已更新，使用 SQL 查询以确保稳定性
   - 响应模型 (`PermissionResponse`) 已更新，包含所有新字段

## 后续工作

1. **修复其他模型的关系定义错误**
   - 当前存在 `ProjectDocument.rd_project` 关系定义错误
   - 修复后可以改用 ORM 查询

2. **统一字段命名（可选）**
   - 如果需要，可以创建迁移脚本将 `perm_code` 重命名为 `permission_code`
   - 将 `perm_name` 重命名为 `permission_name`
   - 但这不是必需的，因为模型映射已经处理了这个问题

## 相关文件

- 模型定义: `app/models/user.py` (Permission 类)
- API 端点: `app/api/v1/endpoints/roles.py` (read_permissions)
- 响应模型: `app/schemas/auth.py` (PermissionResponse)
- 迁移脚本: `migrations/20250120_permissions_table_upgrade_*.sql`
- 自动化脚本: `scripts/apply_permissions_migration.py`
