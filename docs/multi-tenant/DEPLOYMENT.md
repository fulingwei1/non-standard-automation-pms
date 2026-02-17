# 生产部署指南

> 非标自动化测试设备项目管理系统 — 多租户生产部署文档  
> 版本: 1.0 | 更新时间: 2026-02-17 | 适用阶段: 单服务器部署

---

## 目录

1. [部署架构说明](#1-部署架构说明)
2. [环境准备](#2-环境准备)
3. [多租户配置](#3-多租户配置)
4. [数据库初始化](#4-数据库初始化)
5. [租户管理命令](#5-租户管理命令)
6. [数据备份策略](#6-数据备份策略)
7. [性能优化](#7-性能优化)
8. [服务启动与维护](#8-服务启动与维护)

---

## 1. 部署架构说明

### 1.1 当前阶段：单服务器部署

```
┌──────────────────────────────────────────┐
│             单台服务器                    │
│                                          │
│  ┌────────────────┐  ┌────────────────┐  │
│  │   Nginx (80)   │  │  FastAPI App   │  │
│  │   反向代理      │→ │  (8000)        │  │
│  └────────────────┘  └───────┬────────┘  │
│                              │           │
│  ┌───────────────────────────▼────────┐  │
│  │         MySQL 8.0                  │  │
│  │  所有租户共享同一数据库实例           │  │
│  │  通过 tenant_id 行级隔离            │  │
│  └────────────────────────────────────┘  │
│                                          │
│  ┌────────────────┐                      │
│  │  Redis (6379)  │  Token 黑名单/缓存   │
│  └────────────────┘                      │
└──────────────────────────────────────────┘
```

### 1.2 服务器最低配置

| 资源 | 最低要求 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核 |
| 内存 | 4 GB | 8 GB |
| 磁盘 | 50 GB SSD | 100 GB SSD |
| 操作系统 | Ubuntu 20.04+ | Ubuntu 22.04 LTS |

---

## 2. 环境准备

### 2.1 安装系统依赖

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip \
    mysql-server-8.0 redis-server nginx git

# 启动服务
sudo systemctl enable mysql redis-server nginx
sudo systemctl start mysql redis-server nginx
```

### 2.2 克隆代码并安装依赖

```bash
# 克隆仓库
git clone <repository_url> /opt/automation-pms
cd /opt/automation-pms

# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2.3 创建 MySQL 数据库

```sql
-- 以 root 登录 MySQL
mysql -u root -p

-- 创建数据库
CREATE DATABASE automation_pms CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建应用专用账号
CREATE USER 'pms_user'@'localhost' IDENTIFIED BY 'your_strong_password';
GRANT ALL PRIVILEGES ON automation_pms.* TO 'pms_user'@'localhost';
FLUSH PRIVILEGES;
```

---

## 3. 多租户配置

### 3.1 环境变量文件

创建 `/opt/automation-pms/.env` 文件：

```bash
# ============================================================
# 数据库配置
# ============================================================
DATABASE_URL=mysql+pymysql://pms_user:your_strong_password@localhost:3306/automation_pms

# ============================================================
# 安全配置
# ============================================================
SECRET_KEY=your-256-bit-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=480
REFRESH_TOKEN_EXPIRE_DAYS=7

# ============================================================
# 多租户配置
# ============================================================
# 超级管理员初始账号（首次部署时使用）
SUPER_ADMIN_USERNAME=superadmin
SUPER_ADMIN_PASSWORD=SuperAdmin@2026!
SUPER_ADMIN_EMAIL=admin@yourdomain.com

# 租户功能开关
MULTI_TENANT_ENABLED=true
TENANT_ISOLATION_STRICT=true   # 严格模式：非法状态直接抛异常

# ============================================================
# Redis 配置（Token 黑名单）
# ============================================================
REDIS_URL=redis://localhost:6379/0

# ============================================================
# 应用配置
# ============================================================
APP_ENV=production
DEBUG=false
API_V1_PREFIX=/api/v1
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### 3.2 关键配置说明

| 配置项 | 说明 | 默认值 |
|-------|------|-------|
| `MULTI_TENANT_ENABLED` | 是否启用多租户功能 | `true` |
| `TENANT_ISOLATION_STRICT` | 严格模式（非法状态抛异常而非静默失败） | `true` |
| `SECRET_KEY` | JWT 签名密钥，**生产环境必须更换** | 无 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access Token 有效期（分钟） | 480 |

### 3.3 Nginx 配置

```nginx
# /etc/nginx/sites-available/automation-pms
server {
    listen 80;
    server_name yourdomain.com;

    # 重定向到 HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/ssl/certs/yourdomain.crt;
    ssl_certificate_key /etc/ssl/private/yourdomain.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## 4. 数据库初始化

### 4.1 执行数据库迁移

```bash
cd /opt/automation-pms
source venv/bin/activate

# 方式一：使用 Alembic 迁移（推荐）
alembic upgrade head

# 方式二：直接执行 SQL 脚本
mysql -u pms_user -p automation_pms < migrations/add_tenant_id_to_all_tables.sql
```

### 4.2 创建超级管理员

```bash
# 运行初始化脚本
python scripts/init_superadmin.py

# 或使用环境变量指定账号信息
SUPER_ADMIN_USERNAME=superadmin \
SUPER_ADMIN_PASSWORD=SuperAdmin@2026! \
python scripts/init_superadmin.py
```

### 4.3 验证数据库结构

```sql
-- 验证租户表
SHOW TABLES LIKE 'tenants';
DESCRIBE tenants;

-- 验证 tenant_id 字段已添加到业务表
SHOW COLUMNS FROM projects LIKE 'tenant_id';
SHOW COLUMNS FROM users LIKE 'tenant_id';
SHOW COLUMNS FROM quotations LIKE 'tenant_id';

-- 验证超级管理员约束
SHOW CREATE TABLE users\G
```

---

## 5. 租户管理命令

### 5.1 通过 API 创建租户

```bash
# 1. 超级管理员登录获取 Token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=superadmin&password=SuperAdmin@2026!" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['access_token'])")

echo "Token: $TOKEN"

# 2. 创建租户
curl -X POST http://localhost:8000/api/v1/tenants/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "上海精密制造有限公司",
    "tenant_code": "SH-PRECISION-001",
    "plan_type": "STANDARD",
    "contact_name": "张三",
    "contact_email": "zhangsan@sh-precision.com",
    "contact_phone": "021-12345678",
    "max_users": 50,
    "expired_at": "2027-12-31T00:00:00"
  }'
```

### 5.2 初始化租户数据

```bash
# 3. 初始化租户（创建默认角色和管理员账号）
TENANT_ID=1

curl -X POST http://localhost:8000/api/v1/tenants/${TENANT_ID}/init \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "admin_username": "sh_admin",
    "admin_password": "Admin@Sh2026!",
    "admin_email": "admin@sh-precision.com",
    "admin_real_name": "张三",
    "copy_role_templates": true
  }'
```

### 5.3 禁用/启用租户

```bash
# 禁用租户（暂停服务）
curl -X PUT http://localhost:8000/api/v1/tenants/${TENANT_ID} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "SUSPENDED"}'

# 重新启用租户
curl -X PUT http://localhost:8000/api/v1/tenants/${TENANT_ID} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "ACTIVE"}'

# 软删除租户
curl -X DELETE http://localhost:8000/api/v1/tenants/${TENANT_ID} \
  -H "Authorization: Bearer $TOKEN"
```

### 5.4 通过脚本管理租户

```bash
# 使用管理脚本（批量操作）
cd /opt/automation-pms
source venv/bin/activate

# 列出所有租户
python scripts/tenant_admin.py list

# 创建租户
python scripts/tenant_admin.py create \
  --name "苏州工厂" \
  --code "SZ-FACTORY-001" \
  --plan STANDARD \
  --admin-user sz_admin \
  --admin-email admin@sz-factory.com

# 禁用租户
python scripts/tenant_admin.py suspend --tenant-id 2

# 查看租户统计
python scripts/tenant_admin.py stats --tenant-id 1
```

---

## 6. 数据备份策略

### 6.1 全量备份（每日）

```bash
#!/bin/bash
# /opt/scripts/backup_all.sh

BACKUP_DIR="/data/backups/$(date +%Y%m%d)"
DB_USER="pms_user"
DB_PASS="your_strong_password"
DB_NAME="automation_pms"

mkdir -p "$BACKUP_DIR"

# 全量备份
mysqldump \
  -u "$DB_USER" \
  -p"$DB_PASS" \
  --single-transaction \
  --routines \
  --triggers \
  "$DB_NAME" | gzip > "$BACKUP_DIR/full_backup.sql.gz"

echo "全量备份完成: $BACKUP_DIR/full_backup.sql.gz"

# 保留最近 30 天的备份
find /data/backups/ -type d -mtime +30 -exec rm -rf {} + 2>/dev/null
```

### 6.2 按租户备份

```bash
#!/bin/bash
# /opt/scripts/backup_tenant.sh <tenant_id>
# 备份指定租户的所有数据

TENANT_ID=$1
if [ -z "$TENANT_ID" ]; then
  echo "Usage: $0 <tenant_id>"
  exit 1
fi

BACKUP_DIR="/data/backups/tenant_${TENANT_ID}/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# 获取租户信息
TENANT_CODE=$(mysql -u pms_user -pyour_password automation_pms \
  -se "SELECT tenant_code FROM tenants WHERE id = ${TENANT_ID};")

echo "备份租户: ${TENANT_CODE} (ID: ${TENANT_ID})"

# 核心业务表列表
TABLES=(projects tasks users roles quotations contracts
        production_orders purchase_orders inventory quality_inspections)

for TABLE in "${TABLES[@]}"; do
  # 检查表是否有 tenant_id 字段
  HAS_TENANT=$(mysql -u pms_user -pyour_password automation_pms \
    -se "SELECT COUNT(*) FROM information_schema.columns
         WHERE table_name='${TABLE}' AND column_name='tenant_id'
         AND table_schema='automation_pms';")

  if [ "$HAS_TENANT" -gt "0" ]; then
    mysqldump \
      -u pms_user \
      -pyour_password \
      --single-transaction \
      --where="tenant_id=${TENANT_ID}" \
      automation_pms "$TABLE" \
      > "${BACKUP_DIR}/${TABLE}.sql"
    echo "  ✅ 已备份: ${TABLE}"
  fi
done

# 打包压缩
tar -czf "${BACKUP_DIR}.tar.gz" -C "$(dirname $BACKUP_DIR)" "$(basename $BACKUP_DIR)"
rm -rf "$BACKUP_DIR"

echo "备份完成: ${BACKUP_DIR}.tar.gz"
```

### 6.3 配置定时备份

```bash
# 编辑 crontab
crontab -e

# 每天凌晨 2:00 全量备份
0 2 * * * /opt/scripts/backup_all.sh >> /var/log/pms-backup.log 2>&1

# 每周日凌晨 3:00 按租户备份所有租户
0 3 * * 0 /opt/scripts/backup_all_tenants.sh >> /var/log/pms-tenant-backup.log 2>&1
```

### 6.4 数据恢复

```bash
# 恢复全量备份
gunzip -c /data/backups/20260217/full_backup.sql.gz | \
  mysql -u pms_user -p automation_pms

# 恢复指定租户数据（谨慎操作！）
# 先清空该租户数据
mysql -u pms_user -p automation_pms \
  -e "DELETE FROM projects WHERE tenant_id = 1;"

# 再导入备份
mysql -u pms_user -p automation_pms < /data/backups/tenant_1/20260217_020000/projects.sql
```

---

## 7. 性能优化

### 7.1 租户查询索引

所有包含 `tenant_id` 的业务表**必须建立索引**：

```sql
-- 单列索引（适合简单查询）
CREATE INDEX idx_projects_tenant_id ON projects(tenant_id);
CREATE INDEX idx_tasks_tenant_id ON tasks(tenant_id);
CREATE INDEX idx_users_tenant_id ON users(tenant_id);

-- 复合索引（适合常用查询条件组合）
-- 按租户+状态查询项目
CREATE INDEX idx_projects_tenant_status
    ON projects(tenant_id, status);

-- 按租户+创建时间查询（分页场景）
CREATE INDEX idx_projects_tenant_created
    ON projects(tenant_id, created_at DESC);

-- 按租户+负责人查询任务
CREATE INDEX idx_tasks_tenant_assignee
    ON tasks(tenant_id, assignee_id);
```

### 7.2 批量添加索引脚本

```sql
-- 为所有主要业务表批量添加 tenant_id 索引
-- 注意：生产环境添加索引会锁表，建议在业务低峰期执行
-- MySQL 8.0+ 支持在线 DDL（ALGORITHM=INPLACE, LOCK=NONE）

ALTER TABLE projects
    ADD INDEX idx_tenant_id (tenant_id)
    ALGORITHM=INPLACE, LOCK=NONE;

ALTER TABLE tasks
    ADD INDEX idx_tenant_id (tenant_id)
    ALGORITHM=INPLACE, LOCK=NONE;

ALTER TABLE quotations
    ADD INDEX idx_tenant_id (tenant_id)
    ALGORITHM=INPLACE, LOCK=NONE;

-- 批量执行（生成 SQL）
SELECT CONCAT(
    'ALTER TABLE ', table_name,
    ' ADD INDEX idx_tenant_id (tenant_id) ALGORITHM=INPLACE, LOCK=NONE;'
)
FROM information_schema.columns
WHERE table_schema = 'automation_pms'
  AND column_name = 'tenant_id'
  AND table_name NOT IN (
    SELECT table_name
    FROM information_schema.statistics
    WHERE table_schema = 'automation_pms'
      AND index_name = 'idx_tenant_id'
  );
```

### 7.3 MySQL 配置优化

```ini
# /etc/mysql/mysql.conf.d/mysqld.cnf

[mysqld]
# 缓冲池大小（建议为物理内存的 70-80%）
innodb_buffer_pool_size = 4G

# 查询缓存（已在 MySQL 8.0 移除，使用 Redis 代替）

# 连接池
max_connections = 200
thread_cache_size = 16

# 慢查询日志（用于发现未过滤 tenant_id 的慢查询）
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 1

# 索引统计
innodb_stats_on_metadata = 0
```

---

## 8. 服务启动与维护

### 8.1 使用 systemd 管理服务

```ini
# /etc/systemd/system/automation-pms.service

[Unit]
Description=Non-Standard Automation PMS
After=network.target mysql.service redis.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/automation-pms
Environment="PATH=/opt/automation-pms/venv/bin"
EnvironmentFile=/opt/automation-pms/.env
ExecStart=/opt/automation-pms/venv/bin/uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --access-log \
    --log-level info
ExecReload=/bin/kill -s HUP $MAINPID
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable automation-pms
sudo systemctl start automation-pms

# 查看状态
sudo systemctl status automation-pms

# 查看日志
sudo journalctl -u automation-pms -f --since "1 hour ago"
```

### 8.2 健康检查

```bash
# 检查应用是否正常运行
curl http://localhost:8000/health

# 检查多租户功能是否正常
curl http://localhost:8000/api/v1/health/tenant

# 预期响应
# {"status": "ok", "multi_tenant": "enabled", "tenant_count": 5}
```

### 8.3 版本升级流程

```bash
# 1. 备份数据库
/opt/scripts/backup_all.sh

# 2. 拉取新代码
cd /opt/automation-pms
git pull origin main

# 3. 安装新依赖
source venv/bin/activate
pip install -r requirements.txt

# 4. 执行数据库迁移
alembic upgrade head

# 5. 重启服务
sudo systemctl restart automation-pms

# 6. 验证服务正常
sudo systemctl status automation-pms
curl http://localhost:8000/health
```

---

## 相关文档

- [README.md](./README.md) — 多租户架构总览
- [ADMIN_GUIDE.md](./ADMIN_GUIDE.md) — 系统管理员操作手册
- [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) — 开发者指南
- [../multi-tenant/01_数据库迁移指南.md](./01_数据库迁移指南.md) — 数据库迁移详细指南
