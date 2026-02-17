# 系统管理员操作手册

> 非标自动化测试设备项目管理系统 — 超级管理员操作指南  
> 版本: 1.0 | 更新时间: 2026-02-17 | 读者对象: 平台运维管理员

---

## 目录

1. [超级管理员概述](#1-超级管理员概述)
2. [管理员登录与鉴权](#2-管理员登录与鉴权)
3. [租户 CRUD 操作](#3-租户-crud-操作)
4. [用户管理](#4-用户管理)
5. [监控与统计](#5-监控与统计)
6. [故障排查](#6-故障排查)
7. [安全操作规范](#7-安全操作规范)

---

## 1. 超级管理员概述

### 1.1 超级管理员身份特征

超级管理员（Superuser）是系统的最高权限账号，具有以下特征：

```python
# 判断标准（同时满足两个条件）
user.is_superuser == True
user.tenant_id is None   # 不属于任何租户
```

> ⚠️ **重要**：超级管理员账号不属于任何租户，它可以**跨租户访问所有数据**。

### 1.2 超级管理员权限范围

| 权限 | 描述 |
|------|------|
| 租户管理 | 创建、修改、禁用、删除所有租户 |
| 用户管理 | 查看所有租户的用户，重置任意用户密码 |
| 数据访问 | 查看任意租户的全部业务数据 |
| 系统配置 | 修改系统级配置、角色模板 |
| 监控运维 | 查看各租户使用量、系统健康状态 |

### 1.3 超级管理员账号安全原则

- 🔐 使用强密码（至少 16 位，含大小写字母、数字、特殊字符）
- 🔑 定期轮换密码（建议每季度一次）
- 📝 所有超级管理员操作均记录审计日志
- 👥 生产环境建议设置 2 个超级管理员账号（互为备份）
- 🚫 禁止将超级管理员凭据用于日常业务操作

---

## 2. 管理员登录与鉴权

### 2.1 登录获取 Token

```bash
# 超级管理员登录
curl -X POST http://yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=superadmin&password=YourPassword@2026"

# 响应示例
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 28800
  }
}
```

### 2.2 设置环境变量（推荐用于脚本操作）

```bash
# 设置 Token 到环境变量，避免每次重复输入
export PMS_BASE_URL="http://yourdomain.com"
export PMS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# 通用请求头函数
pms_get()  { curl -s -X GET  "${PMS_BASE_URL}$1" -H "Authorization: Bearer $PMS_TOKEN"; }
pms_post() { curl -s -X POST "${PMS_BASE_URL}$1" -H "Authorization: Bearer $PMS_TOKEN" \
             -H "Content-Type: application/json" -d "$2"; }
pms_put()  { curl -s -X PUT  "${PMS_BASE_URL}$1" -H "Authorization: Bearer $PMS_TOKEN" \
             -H "Content-Type: application/json" -d "$2"; }
pms_del()  { curl -s -X DELETE "${PMS_BASE_URL}$1" -H "Authorization: Bearer $PMS_TOKEN"; }
```

---

## 3. 租户 CRUD 操作

### 3.1 查看租户列表

```bash
# 获取所有租户列表（分页）
pms_get "/api/v1/tenants/?page=1&page_size=20"

# 按状态筛选
pms_get "/api/v1/tenants/?status=ACTIVE"
pms_get "/api/v1/tenants/?status=SUSPENDED"

# 关键词搜索
pms_get "/api/v1/tenants/?keyword=上海"

# 响应格式
{
  "code": 200,
  "data": {
    "items": [
      {
        "id": 1,
        "tenant_code": "SH-PRECISION-001",
        "tenant_name": "上海精密制造有限公司",
        "status": "ACTIVE",
        "plan_type": "STANDARD",
        "max_users": 50,
        "user_count": 23,
        "contact_name": "张三",
        "expired_at": "2027-12-31T00:00:00",
        "created_at": "2026-01-15T09:00:00"
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 20,
    "pages": 1
  }
}
```

### 3.2 创建新租户

```bash
# 创建租户
pms_post "/api/v1/tenants/" '{
  "tenant_name": "苏州智能装备有限公司",
  "tenant_code": "SZ-INTELLIGENT-001",
  "plan_type": "ENTERPRISE",
  "contact_name": "李四",
  "contact_email": "lisi@sz-intelligent.com",
  "contact_phone": "0512-87654321",
  "max_users": 200,
  "max_roles": 50,
  "expired_at": "2028-12-31T00:00:00",
  "settings": {
    "timezone": "Asia/Shanghai",
    "language": "zh-CN",
    "logo_url": "https://cdn.example.com/logos/sz.png"
  }
}'
```

### 3.3 初始化租户数据

```bash
# 初始化租户（创建默认角色和管理员账号）
# ⚠️ 注意：此操作只能执行一次，重复执行会报错
TENANT_ID=2

pms_post "/api/v1/tenants/${TENANT_ID}/init" '{
  "admin_username": "sz_admin",
  "admin_password": "Admin@Sz2026!",
  "admin_email": "admin@sz-intelligent.com",
  "admin_real_name": "李四",
  "copy_role_templates": true
}'

# 初始化完成后，该租户会包含以下默认数据：
# - 角色：系统管理员、项目经理、销售工程师、生产工程师、财务专员、访客
# - 用户：1 个管理员账号
# - 权限：根据角色模板配置
```

### 3.4 更新租户信息

```bash
TENANT_ID=1

# 更新联系信息
pms_put "/api/v1/tenants/${TENANT_ID}" '{
  "contact_name": "王五",
  "contact_email": "wangwu@sh-precision.com",
  "contact_phone": "021-99887766"
}'

# 升级套餐
pms_put "/api/v1/tenants/${TENANT_ID}" '{
  "plan_type": "ENTERPRISE",
  "max_users": 200,
  "expired_at": "2028-12-31T00:00:00"
}'

# 暂停租户（租户用户将无法登录）
pms_put "/api/v1/tenants/${TENANT_ID}" '{"status": "SUSPENDED"}'

# 恢复租户
pms_put "/api/v1/tenants/${TENANT_ID}" '{"status": "ACTIVE"}'
```

### 3.5 删除租户

```bash
TENANT_ID=3

# 软删除租户（数据保留，仅标记为 DELETED 状态）
pms_del "/api/v1/tenants/${TENANT_ID}"

# ⚠️ 警告：
# 1. 软删除后该租户的用户无法登录
# 2. 数据不会被物理删除（可以恢复）
# 3. 如需物理删除，需要直接操作数据库（需要 DBA 权限）

# 恢复已删除的租户（通过 API 更新状态）
pms_put "/api/v1/tenants/${TENANT_ID}" '{"status": "ACTIVE"}'
```

---

## 4. 用户管理

### 4.1 查看指定租户的用户

```bash
# 超级管理员可以查看任意租户的用户
# 通过查询参数指定 tenant_id
pms_get "/api/v1/users/?tenant_id=1&page=1&page_size=20"
```

### 4.2 重置租户用户密码

```bash
USER_ID=42

# 重置用户密码（超级管理员权限）
pms_post "/api/v1/users/${USER_ID}/reset-password" '{
  "new_password": "TempPass@2026!",
  "force_change_on_login": true
}'
```

### 4.3 禁用/启用用户

```bash
USER_ID=42

# 禁用用户
pms_put "/api/v1/users/${USER_ID}" '{"is_active": false}'

# 启用用户
pms_put "/api/v1/users/${USER_ID}" '{"is_active": true}'
```

---

## 5. 监控与统计

### 5.1 查看租户使用量

```bash
# 获取指定租户的统计数据
TENANT_ID=1
pms_get "/api/v1/tenants/${TENANT_ID}/stats"

# 响应示例
{
  "code": 200,
  "data": {
    "tenant_id": 1,
    "tenant_code": "SH-PRECISION-001",
    "user_count": 23,
    "role_count": 6,
    "project_count": 47,
    "storage_used_mb": 234.5,
    "plan_limits": {
      "users": 50,
      "roles": 20,
      "storage_gb": 10
    }
  }
}
```

### 5.2 数据库层面统计

```sql
-- 各租户数据量统计
SELECT
    t.tenant_code,
    t.tenant_name,
    t.status,
    COUNT(DISTINCT u.id)  AS user_count,
    COUNT(DISTINCT p.id)  AS project_count,
    COUNT(DISTINCT q.id)  AS quotation_count
FROM tenants t
LEFT JOIN users       u ON u.tenant_id = t.id
LEFT JOIN projects    p ON p.tenant_id = t.id
LEFT JOIN quotations  q ON q.tenant_id = t.id
GROUP BY t.id, t.tenant_code, t.tenant_name, t.status
ORDER BY t.id;

-- 查找数据量最大的租户（用于容量规划）
SELECT
    t.tenant_name,
    COUNT(*) AS total_records
FROM (
    SELECT tenant_id FROM projects
    UNION ALL
    SELECT tenant_id FROM tasks
    UNION ALL
    SELECT tenant_id FROM quotations
    UNION ALL
    SELECT tenant_id FROM production_orders
) combined
JOIN tenants t ON t.id = combined.tenant_id
GROUP BY combined.tenant_id, t.tenant_name
ORDER BY total_records DESC
LIMIT 10;
```

### 5.3 系统健康检查

```bash
# 检查系统整体状态
pms_get "/api/v1/health/"

# 检查多租户功能状态
pms_get "/api/v1/health/tenant"

# 检查数据库连接
pms_get "/api/v1/health/db"
```

### 5.4 租户登录活跃度统计

```sql
-- 最近 7 天各租户活跃用户数
SELECT
    t.tenant_name,
    COUNT(DISTINCT al.user_id) AS active_users,
    COUNT(*) AS total_logins
FROM audit_logs al
JOIN users u ON u.id = al.user_id
JOIN tenants t ON t.id = u.tenant_id
WHERE al.action = 'LOGIN'
  AND al.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
GROUP BY u.tenant_id, t.tenant_name
ORDER BY active_users DESC;
```

---

## 6. 故障排查

### 6.1 租户用户无法登录

**症状：** 租户用户登录报错 `403 Forbidden` 或 `账号已禁用`

**排查步骤：**

```bash
# 1. 检查租户状态
mysql -u pms_user -p automation_pms \
  -e "SELECT id, tenant_code, tenant_name, status, expired_at FROM tenants WHERE id = 1;"

# 2. 检查用户状态
mysql -u pms_user -p automation_pms \
  -e "SELECT id, username, is_active, tenant_id FROM users WHERE username = 'sh_admin';"

# 3. 检查租户是否过期
mysql -u pms_user -p automation_pms \
  -e "SELECT tenant_name, expired_at, NOW() > expired_at AS is_expired
      FROM tenants WHERE id = 1;"

# 4. 如果租户过期，延长有效期
pms_put "/api/v1/tenants/1" '{"expired_at": "2028-12-31T00:00:00"}'

# 5. 如果租户被暂停，重新启用
pms_put "/api/v1/tenants/1" '{"status": "ACTIVE"}'
```

### 6.2 数据隔离验证失败

**症状：** 某用户可以看到其他租户的数据

**排查步骤：**

```bash
# 1. 检查用户的 tenant_id 是否正确
mysql -u pms_user -p automation_pms \
  -e "SELECT id, username, tenant_id, is_superuser FROM users WHERE id = 42;"

# 2. 检查问题数据的 tenant_id
mysql -u pms_user -p automation_pms \
  -e "SELECT id, tenant_id, name FROM projects WHERE id = 100;"

# 3. 检查 TenantContextMiddleware 是否正常工作
# 查看应用日志中的 "Tenant context set" 日志
sudo journalctl -u automation-pms | grep "Tenant context set" | tail -20

# 4. 检查是否有代码绕过了 TenantQuery
# 搜索使用了 _skip_tenant_filter 的代码
grep -r "_skip_tenant_filter" app/ --include="*.py"
```

### 6.3 超级管理员权限不生效

**症状：** 超级管理员调用 API 返回 `403 Forbidden`

**排查步骤：**

```bash
# 1. 验证超级管理员账号的 is_superuser 和 tenant_id
mysql -u pms_user -p automation_pms \
  -e "SELECT username, is_superuser, tenant_id FROM users WHERE username = 'superadmin';"

# 预期结果：is_superuser=1, tenant_id=NULL

# 2. 检查约束是否满足
# is_superuser=1 且 tenant_id NOT NULL 是非法状态，需要修复
mysql -u pms_user -p automation_pms \
  -e "UPDATE users SET tenant_id = NULL WHERE username='superadmin' AND is_superuser=1;"

# 3. 检查 Token 是否包含正确的 is_superuser 字段
# 解码 JWT Token（仅用于调试）
python3 -c "
import base64, json
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
payload = token.split('.')[1]
# 补齐 padding
payload += '=' * (4 - len(payload) % 4)
print(json.dumps(json.loads(base64.b64decode(payload)), indent=2))
"
```

### 6.4 租户数据迁移问题

**症状：** 某些数据没有 `tenant_id`，导致查询结果缺失

```sql
-- 检查各表中 tenant_id 为 NULL 的记录数
SELECT 'projects' AS table_name, COUNT(*) AS null_tenant_count
FROM projects WHERE tenant_id IS NULL
UNION ALL
SELECT 'tasks', COUNT(*) FROM tasks WHERE tenant_id IS NULL
UNION ALL
SELECT 'users', COUNT(*) FROM users WHERE tenant_id IS NULL AND is_superuser = 0;

-- 如果发现历史数据缺少 tenant_id，需要手动补填
-- （需要确认这些数据属于哪个租户）
UPDATE projects
SET tenant_id = 1  -- 替换为正确的租户ID
WHERE tenant_id IS NULL;
```

### 6.5 常见错误代码说明

| 错误代码 | 说明 | 解决方法 |
|---------|------|---------|
| `403 需要超级管理员权限` | 用户不是超级管理员 | 确认用户 is_superuser=True 且 tenant_id=NULL |
| `404 租户不存在` | 租户ID不正确或已被删除 | 检查租户状态 |
| `400 租户已初始化` | 重复执行初始化 | 此错误可忽略，初始化只需执行一次 |
| `Invalid user: tenant_id=None but is_superuser=False` | 数据不一致 | 修复用户数据（参考 6.3） |

---

## 7. 安全操作规范

### 7.1 操作前必做检查

```bash
# 在执行任何写操作前，先备份相关数据
mysqldump -u pms_user -p automation_pms tenants users > \
  /tmp/backup_before_ops_$(date +%Y%m%d_%H%M%S).sql
```

### 7.2 操作审计

所有超级管理员操作都会记录到审计日志：

```sql
-- 查看超级管理员最近的操作记录
SELECT
    al.created_at,
    u.username,
    al.action,
    al.resource_type,
    al.resource_id,
    al.details
FROM audit_logs al
JOIN users u ON u.id = al.user_id
WHERE u.is_superuser = TRUE
ORDER BY al.created_at DESC
LIMIT 50;
```

### 7.3 敏感操作二次确认

以下操作建议在执行前进行二次确认：

1. **删除租户** - 确认是否需要先备份数据
2. **重置用户密码** - 确认用户身份
3. **修改套餐限制** - 确认与客户合同一致
4. **批量操作** - 先在测试环境验证脚本

---

## 相关文档

- [README.md](./README.md) — 多租户架构总览
- [DEPLOYMENT.md](./DEPLOYMENT.md) — 生产部署指南
- [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) — 开发者指南
- [../超级管理员设计规范.md](../超级管理员设计规范.md) — 超级管理员规范详情
