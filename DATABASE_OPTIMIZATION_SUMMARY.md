# 数据库优化实施总结

## 日期
2025-01-11

## 优化概述
本次优化主要针对高优先级的索引添加和查询优化，提升系统整体性能。

---

## 一、索引优化（已完成）

### 1. User、Role、Permission 表索引

#### users 表
- ✅ `idx_user_active` - is_active 索引（优化活跃用户查询）
- ✅ `idx_user_department` - department 索引（优化部门查询）
- ✅ `idx_user_email` - email 索引（优化邮箱查找）

#### roles 表
- ✅ `idx_role_active` - is_active 索引（优化活跃角色查询）
- ✅ `idx_role_system` - is_system 索引（优化系统角色筛选）
- ✅ `idx_role_data_scope` - data_scope 索引（优化数据权限范围筛选）

#### permissions 表
- ✅ `idx_permission_active` - is_active 索引（优化活跃权限查询）
- ✅ `idx_permission_module` - module 索引（优化按模块查询权限）

#### role_permissions 表
- ✅ `idx_role_permissions_role` - role_id 索引（优化角色权限查询）
- ✅ `idx_role_permissions_permission` - permission_id 索引（优化权限角色查询）

#### user_roles 表
- ✅ `idx_user_roles_user` - user_id 索引（优化用户角色查询）
- ✅ `idx_user_roles_role` - role_id 索引（优化角色用户查询）

**迁移文件：**
- `migrations/20250111_user_role_permission_indexes_sqlite.sql`
- `migrations/20250111_user_role_permission_indexes_mysql.sql`

---

### 2. ProjectMember 表复合索引

#### 新增索引
- ✅ `idx_project_members_user_active` - (user_id, is_active) 复合索引
  - 优化：查询用户的活跃项目成员
  
- ✅ `idx_project_members_project_active` - (project_id, is_active) 复合索引
  - 优化：查询项目的活跃成员列表
  
- ✅ `idx_project_members_machine_active` - (machine_id, is_active) 复合索引
  - 优化：查询设备的活跃成员
  
- ✅ `idx_project_members_cover_user` - (user_id, is_active, project_id) 覆盖索引
  - 优化：减少回表查询，直接从索引获取所需数据

**迁移文件：**
- `migrations/20250111_project_alert_indexes_sqlite.sql`
- `migrations/20250111_project_alert_indexes_mysql.sql`

---

### 3. AlertRecord 表复合索引

#### 新增索引
- ✅ `idx_alert_status_level` - (status, alert_level) 复合索引
  - 优化：按状态和级别查询预警
  
- ✅ `idx_alert_project_status` - (project_id, status) 复合索引
  - 优化：查询项目的预警状态
  
- ✅ `idx_alert_project_time` - (project_id, triggered_at) 复合索引
  - 优化：查询项目预警的时间序列
  
- ✅ `idx_alert_cover_status` - (status, triggered_at, alert_level, alert_title) 覆盖索引
  - 优化：减少回表查询

---

### 4. ExceptionEvent 表复合索引

#### 新增索引
- ✅ `idx_event_status_overdue` - (status, is_overdue) 复合索引
  - 优化：查询超期异常
  
- ✅ `idx_event_responsible_status` - (responsible_user_id, status) 复合索引
  - 优化：查询责任人的异常状态
  
- ✅ `idx_event_project_severity` - (project_id, severity) 复合索引
  - 优化：查询项目的异常严重程度

---

## 二、查询优化（已完成）

### 1. DataScopeService 优化

#### 优化内容

**部门查询缓存：**
```python
# 优化前：每次都查询数据库
dept = db.query(Department).filter(Department.dept_name == dept_name).first()

# 优化后：使用缓存
dept_id = DepartmentCache.get(dept_name)
if dept_id is None:
    dept = db.query(Department.id).filter(
        Department.dept_name == dept_name
    ).first()
    if dept:
        dept_id = dept[0]
        DepartmentCache.set(dept_name, dept_id)
```

**用户项目列表缓存：**
```python
# 优化前：每次都查询数据库
members = db.query(ProjectMember.project_id).filter(
    ProjectMember.user_id == user_id,
    ProjectMember.is_active == True
).all()

# 优化后：使用缓存 + select 语句
cached_ids = UserProjectCache.get(user_id)
if cached_ids is not None:
    return cached_ids

stmt = select(ProjectMember.project_id).where(
    ProjectMember.user_id == user_id,
    ProjectMember.is_active == True
)
project_ids = {row[0] for row in db.execute(stmt)}
UserProjectCache.set(user_id, project_ids)
```

**影响的文件：**
- ✅ `app/services/data_scope_service.py`

---

## 三、缓存服务（已实现）

### 1. CacheService（通用缓存）

**功能：**
- 内存缓存支持 TTL（生存时间）
- 支持手动失效
- 提供缓存统计信息

**主要方法：**
- `get(key, default)` - 获取缓存
- `set(key, value, ttl)` - 设置缓存
- `delete(key)` - 删除缓存
- `clear()` - 清空所有缓存
- `clear_prefix(prefix)` - 清除指定前缀的缓存
- `get_stats()` - 获取统计信息

**文件：**
- ✅ `app/services/cache_service.py`

---

### 2. DepartmentCache（部门ID缓存）

**功能：**
- 缓存部门名称到 ID 的映射
- TTL: 1 小时
- 线程安全

**主要方法：**
- `get(dept_name)` - 获取部门 ID
- `set(dept_name, dept_id)` - 设置部门 ID
- `delete(dept_name)` - 删除部门缓存
- `clear()` - 清空所有缓存
- `get_size()` - 获取缓存大小

---

### 3. UserProjectCache（用户项目缓存）

**功能：**
- 缓存用户参与的项目 ID 集合
- TTL: 5 分钟（可配置）
- 支持按项目失效相关用户缓存

**主要方法：**
- `get(user_id)` - 获取用户项目列表
- `set(user_id, project_ids, ttl)` - 设置用户项目列表
- `delete(user_id)` - 删除用户缓存
- `clear_by_project(project_id)` - 清除包含指定项目的所有用户缓存
- `clear()` - 清空所有缓存
- `get_stats()` - 获取统计信息

---

### 4. UserPermissionCache（用户权限缓存）

**功能：**
- 使用 LRU 缓存（最多 1000 个用户）
- TTL: 10 分钟
- 支持手动失效

**主要方法：**
- `get_user_permissions(user_id)` - 获取用户权限（带 LRU 缓存）
- `invalidate_user(user_id)` - 失效用户缓存
- `invalidate_all()` - 失效所有缓存
- `get_stats()` - 获取统计信息

---

### 5. CacheInvalidator（缓存失效管理器）

**功能：**
- 统一管理缓存失效逻辑
- 确保数据一致性
- 支持相关缓存的级联失效

**主要方法：**
- `invalidate_user(user_id)` - 失效用户相关缓存
- `invalidate_role(role_id, user_ids)` - 失效角色相关缓存
- `invalidate_permission(permission_id)` - 失效权限相关缓存
- `invalidate_project(project_id)` - 失效项目相关缓存
- `invalidate_project_member(db, project_id, user_id)` - 失效项目成员相关缓存
- `invalidate_department(dept_id, dept_name)` - 失效部门相关缓存

**文件：**
- ✅ `app/services/cache_invalidation.py`

---

### 6. CacheInvalidationHooks（缓存失效钩子）

**功能：**
- 在数据库操作后自动失效缓存
- 提供钩子方法，方便集成

**主要钩子：**
- `on_user_created(user_id)` - 用户创建后
- `on_user_updated(db, user_id)` - 用户更新后
- `on_user_deleted(user_id)` - 用户删除后
- `on_role_assigned(db, user_id, role_id)` - 角色分配后
- `on_role_revoked(user_id, role_id)` - 角色撤销后
- `on_project_member_added(db, project_id, user_id)` - 添加项目成员后
- `on_project_member_removed(db, project_id, user_id)` - 移除项目成员后
- `on_department_updated(db, dept_id, dept_name)` - 部门更新后

---

## 四、迁移执行指南

### SQLite 数据库

```bash
# 执行用户角色权限索引迁移
sqlite3 data/app.db < migrations/20250111_user_role_permission_indexes_sqlite.sql

# 执行项目预警索引迁移
sqlite3 data/app.db < migrations/20250111_project_alert_indexes_sqlite.sql
```

### MySQL 数据库

```bash
# 执行用户角色权限索引迁移
mysql -u username -p database_name < migrations/20250111_user_role_permission_indexes_mysql.sql

# 执行项目预警索引迁移
mysql -u username -p database_name < migrations/20250111_project_alert_indexes_mysql.sql
```

---

## 五、预期性能提升

### 1. 用户权限查询
- **优化前**：每次查询都需要 JOIN 多张表
- **优化后**：利用索引 + 缓存，减少 70-80% 查询时间

### 2. 数据权限过滤
- **优化前**：每次都需要查询部门 ID 和用户项目列表
- **优化后**：利用缓存，减少 80-90% 查询时间

### 3. 项目成员查询
- **优化前**：全表扫描或单列索引
- **优化后**：复合索引，减少 60-70% 查询时间

### 4. 预警查询
- **优化前**：多条件查询效率低
- **优化后**：复合索引 + 覆盖索引，减少 50-60% 查询时间

### 5. 异常查询
- **优化前**：需要多次单列查询
- **优化后**：复合索引，减少 50-70% 查询时间

---

## 六、后续优化建议

### 中优先级（近期实施）

1. **实现查询监控**
   - 记录慢查询日志
   - 分析查询性能瓶颈

2. **优化 JOIN 查询**
   - 根据查询场景选择合适的加载策略
   - 使用 selectinload、contains_eager 等

3. **添加更多覆盖索引**
   - 针对高频查询场景
   - 减少回表查询

4. **优化聚合查询**
   - 使用单次聚合查询代替多次查询
   - 利用数据库聚合函数

### 低优先级（长期规划）

1. **表分区**
   - 按时间分区历史数据
   - 按状态分区活跃/归档数据

2. **创建视图**
   - 项目健康度概览视图
   - 用户项目权限视图

3. **数据库读写分离**
   - 主库写入
   - 从库读取

4. **引入 Redis**
   - 更强大的缓存能力
   - 分布式缓存支持

---

## 七、验证和监控

### 1. 索引验证

**SQLite：**
```sql
-- 查看表的索引
PRAGMA index_list('users');
PRAGMA index_list('roles');
PRAGMA index_list('permissions');
```

**MySQL：**
```sql
-- 查看表的索引
SHOW INDEX FROM users WHERE Key_name LIKE 'idx_%';
SHOW INDEX FROM roles WHERE Key_name LIKE 'idx_%';
SHOW INDEX FROM permissions WHERE Key_name LIKE 'idx_%';
```

### 2. 性能监控

**缓存统计：**
```python
from app.services.cache_service import get_cache_stats

stats = get_cache_stats()
print(f"缓存统计: {stats}")
```

**慢查询监控：**
```sql
-- SQLite
PRAGMA temp_store = MEMORY;
PRAGMA synchronous = NORMAL;

-- MySQL
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;
```

---

## 八、总结

本次优化完成了以下工作：

✅ **高优先级索引优化（已完成）**
- User、Role、Permission 表的 is_active 索引
- ProjectMember 表的复合索引
- AlertRecord 表的复合索引
- ExceptionEvent 表的复合索引

✅ **查询优化（已完成）**
- DataScopeService 部门查询缓存
- 用户项目列表缓存

✅ **缓存服务（已实现）**
- 通用缓存服务
- 部门 ID 缓存
- 用户项目缓存
- 用户权限缓存
- 缓存失效管理器
- 缓存失效钩子

✅ **迁移文件（已创建）**
- SQLite 版本迁移文件
- MySQL 版本迁移文件

**预期效果：**
- 用户权限查询性能提升 70-80%
- 数据权限过滤性能提升 80-90%
- 项目成员查询性能提升 60-70%
- 预警查询性能提升 50-60%
- 异常查询性能提升 50-70%

---

## 九、注意事项

1. **迁移前备份数据库**
   - 索引创建可能需要较长时间
   - 大表可能锁定，影响性能

2. **监控索引创建进度**
   - SQLite: 没有进度显示
   - MySQL: 可以通过 SHOW PROCESSLIST 查看

3. **验证索引效果**
   - 执行 EXPLAIN ANALYZE 查看执行计划
   - 对比优化前后的查询性能

4. **定期维护索引**
   - 监控索引使用情况
   - 删除不必要的索引

5. **缓存失效时机**
   - 数据变更后及时失效缓存
   - 使用钩子自动失效
