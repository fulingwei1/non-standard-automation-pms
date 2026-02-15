# 售前AI系统 - 系统管理员手册

## 📚 目录

1. [系统架构](#系统架构)
2. [部署指南](#部署指南)
3. [配置管理](#配置管理)
4. [监控与维护](#监控与维护)
5. [故障排查](#故障排查)
6. [安全管理](#安全管理)
7. [性能优化](#性能优化)
8. [备份与恢复](#备份与恢复)

---

## 🏗️ 系统架构

### 技术栈

**前端**:
- React 19 + TypeScript
- Vite 构建工具
- Tailwind CSS + shadcn/ui
- Zustand 状态管理
- Recharts 图表库

**后端**:
- FastAPI (Python 3.9+)
- SQLAlchemy ORM
- MySQL 8.0+
- Redis (可选，用于缓存)

**AI服务**:
- OpenAI GPT-4 (或其他LLM)
- 自定义AI微服务

### 系统架构图

```
┌─────────────────────────────────────────────────┐
│                   前端应用                       │
│         (React + Vite + Tailwind)               │
└─────────────┬───────────────────────────────────┘
              │ HTTP/HTTPS
              ▼
┌─────────────────────────────────────────────────┐
│                FastAPI应用                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ API路由  │  │  服务层  │  │  模型层  │      │
│  └──────────┘  └──────────┘  └──────────┘      │
└─────────────┬───────────────────────────────────┘
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
┌────────┐ ┌────────┐ ┌────────┐
│ MySQL  │ │ Redis  │ │ AI API │
└────────┘ └────────┘ └────────┘
```

---

## 🚀 部署指南

### 前置要求

- Python 3.9+
- Node.js 18+
- MySQL 8.0+
- Redis 6.0+ (可选)
- 2GB+ RAM
- 10GB+ 磁盘空间

### 数据库初始化

1. **创建数据库**:
```sql
CREATE DATABASE presale_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'presale_user'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON presale_ai.* TO 'presale_user'@'localhost';
FLUSH PRIVILEGES;
```

2. **运行迁移**:
```bash
cd /path/to/project
alembic upgrade head
```

3. **初始化AI配置**:
```bash
python scripts/init_ai_config.py
```

### 后端部署

1. **安装依赖**:
```bash
cd backend
pip install -r requirements.txt
```

2. **配置环境变量**:
```bash
cp .env.example .env
# 编辑.env文件，设置：
# - DATABASE_URL
# - SECRET_KEY
# - OPENAI_API_KEY
# - REDIS_URL (可选)
```

3. **启动服务**:
```bash
# 开发环境
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产环境
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile access.log \
  --error-logfile error.log
```

### 前端部署

1. **安装依赖**:
```bash
cd frontend
npm install
```

2. **构建生产版本**:
```bash
npm run build
```

3. **部署到Nginx**:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    root /path/to/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker部署

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## ⚙️ 配置管理

### AI功能配置

**位置**: 系统管理 → AI配置

可配置参数：

| 参数 | 说明 | 默认值 | 范围 |
|------|------|--------|------|
| enabled | 是否启用 | true | true/false |
| model_name | 模型名称 | gpt-4 | - |
| temperature | 温度参数 | 0.7 | 0.0-2.0 |
| max_tokens | 最大tokens | 2000 | 1-8000 |
| timeout_seconds | 超时时间 | 30 | 1-300 |

**通过API配置**:
```bash
curl -X POST "http://localhost:8000/api/v1/presale/ai/config/update?ai_function=requirement" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "temperature": 0.7,
    "max_tokens": 2000
  }'
```

**通过数据库配置**:
```sql
UPDATE presale_ai_config 
SET temperature = 0.8, max_tokens = 3000 
WHERE ai_function = 'requirement';
```

### 系统参数配置

**文件**: `app/core/config.py`

```python
class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "售前AI系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 数据库配置
    DATABASE_URL: str
    
    # AI配置
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4"
    OPENAI_TIMEOUT: int = 30
    
    # Redis配置
    REDIS_URL: Optional[str] = None
    
    # 安全配置
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
```

---

## 📊 监控与维护

### 健康检查

**手动检查**:
```bash
curl http://localhost:8000/api/v1/presale/ai/health-check
```

**响应示例**:
```json
{
  "status": "healthy",
  "services": {
    "database": {"status": "healthy"},
    "ai_functions": {"status": "healthy", "enabled_count": 9},
    "recent_activity": {"status": "healthy", "usage_count_24h": 145}
  }
}
```

**自动监控脚本**:
```bash
#!/bin/bash
# health_monitor.sh

while true; do
    STATUS=$(curl -s http://localhost:8000/api/v1/presale/ai/health-check | jq -r '.status')
    
    if [ "$STATUS" != "healthy" ]; then
        echo "$(date): System unhealthy!" | tee -a health.log
        # 发送告警邮件/短信
    fi
    
    sleep 60
done
```

### 日志管理

**日志位置**:
- 应用日志: `/var/log/presale-ai/app.log`
- 访问日志: `/var/log/presale-ai/access.log`
- 错误日志: `/var/log/presale-ai/error.log`
- AI调用日志: `/var/log/presale-ai/ai.log`

**日志轮转配置** (`/etc/logrotate.d/presale-ai`):
```
/var/log/presale-ai/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0644 www-data www-data
    sharedscripts
    postrotate
        systemctl reload presale-ai
    endscript
}
```

**查看实时日志**:
```bash
tail -f /var/log/presale-ai/app.log
```

**搜索错误**:
```bash
grep "ERROR" /var/log/presale-ai/app.log | tail -n 50
```

### 性能指标

**关键指标**:
- API响应时间 (目标: <500ms)
- AI处理时间 (目标: <30s)
- 数据库查询时间 (目标: <100ms)
- 系统可用性 (目标: >99.9%)

**监控工具**:
- Prometheus + Grafana
- New Relic
- Datadog

**自定义指标**:
```python
# app/utils/metrics.py
from prometheus_client import Counter, Histogram

ai_requests_total = Counter('ai_requests_total', 'Total AI requests', ['function'])
ai_request_duration = Histogram('ai_request_duration_seconds', 'AI request duration', ['function'])
```

---

## 🔧 故障排查

### 常见问题

#### 1. AI处理失败

**症状**: AI功能返回错误

**排查步骤**:
1. 检查AI配置是否正确
2. 查看错误日志
3. 测试API连接
4. 检查配额和限制

**解决方案**:
```bash
# 检查AI配置
curl http://localhost:8000/api/v1/presale/ai/config

# 测试OpenAI连接
python scripts/test_ai_connection.py

# 查看错误详情
grep "OpenAI" /var/log/presale-ai/error.log
```

#### 2. 数据库连接失败

**症状**: 应用无法启动或查询失败

**排查步骤**:
1. 检查MySQL是否运行
2. 验证数据库凭据
3. 测试网络连接
4. 检查连接池配置

**解决方案**:
```bash
# 检查MySQL状态
systemctl status mysql

# 测试连接
mysql -u presale_user -p -h localhost presale_ai

# 检查连接数
mysql> SHOW PROCESSLIST;
```

#### 3. 性能问题

**症状**: 响应缓慢

**排查步骤**:
1. 检查系统资源使用
2. 分析慢查询
3. 查看并发连接数
4. 检查缓存命中率

**解决方案**:
```bash
# 查看系统资源
htop

# 启用MySQL慢查询日志
mysql> SET GLOBAL slow_query_log = 'ON';
mysql> SET GLOBAL long_query_time = 1;

# 分析慢查询
mysqldumpslow /var/log/mysql/slow.log
```

### 调试模式

**启用调试日志**:
```bash
# .env文件
DEBUG=true
LOG_LEVEL=DEBUG
```

**Python调试器**:
```python
# 在代码中添加断点
import pdb; pdb.set_trace()
```

---

## 🔐 安全管理

### 访问控制

**用户权限管理**:
```sql
-- 查看用户权限
SELECT u.username, r.name as role, p.name as permission
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE u.username = 'admin';

-- 授予AI管理权限
INSERT INTO user_permissions (user_id, permission_id)
SELECT u.id, p.id
FROM users u, permissions p
WHERE u.username = 'admin' 
  AND p.name = 'ai:manage';
```

### API密钥管理

**生成API密钥**:
```bash
python scripts/generate_api_key.py
```

**轮换密钥**:
```bash
# 更新.env文件
SECRET_KEY=$(openssl rand -hex 32)
OPENAI_API_KEY=sk-new-key-here

# 重启服务
systemctl restart presale-ai
```

### 审计日志

**查看审计日志**:
```sql
SELECT * FROM presale_ai_audit_log
WHERE created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
ORDER BY created_at DESC;
```

**导出审计日志**:
```bash
mysql -u root -p presale_ai -e "
SELECT * FROM presale_ai_audit_log 
WHERE created_at >= '2026-02-01'
" > audit_export.csv
```

---

## ⚡ 性能优化

### 数据库优化

**添加索引**:
```sql
-- AI使用统计索引
CREATE INDEX idx_usage_stats_lookup 
ON presale_ai_usage_stats(user_id, ai_function, date);

-- 工作流日志索引
CREATE INDEX idx_workflow_ticket 
ON presale_ai_workflow_log(presale_ticket_id, workflow_step);
```

**查询优化**:
```sql
-- 使用EXPLAIN分析查询
EXPLAIN SELECT * FROM presale_ai_usage_stats 
WHERE user_id = 10 AND date >= '2026-02-01';
```

### 应用优化

**启用缓存**:
```python
# app/core/cache.py
from functools import lru_cache

@lru_cache(maxsize=128)
def get_ai_config(ai_function: str):
    # 缓存AI配置
    pass
```

**异步处理**:
```python
# app/services/ai_async.py
import asyncio

async def process_workflow_async(ticket_id: int):
    # 异步处理工作流
    pass
```

### 负载均衡

**Nginx配置**:
```nginx
upstream presale_ai {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    location /api {
        proxy_pass http://presale_ai;
    }
}
```

---

## 💾 备份与恢复

### 数据库备份

**自动备份脚本**:
```bash
#!/bin/bash
# backup_db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/presale-ai"
MYSQL_USER="root"
MYSQL_PASS="password"
DATABASE="presale_ai"

mysqldump -u $MYSQL_USER -p$MYSQL_PASS $DATABASE | \
  gzip > $BACKUP_DIR/presale_ai_$DATE.sql.gz

# 保留最近30天的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete
```

**定时任务** (`crontab -e`):
```cron
# 每天凌晨2点备份
0 2 * * * /path/to/backup_db.sh
```

### 数据恢复

**恢复数据库**:
```bash
# 解压备份
gunzip presale_ai_20260215.sql.gz

# 恢复数据
mysql -u root -p presale_ai < presale_ai_20260215.sql
```

### 文件备份

**备份上传文件**:
```bash
# 使用rsync同步
rsync -avz /var/www/presale-ai/uploads/ \
  backup-server:/backups/uploads/
```

---

## 📞 技术支持

### 联系方式
- 📧 技术支持: tech-support@example.com
- 🚨 紧急热线: 400-XXX-XXXX (24/7)
- 💬 Slack频道: #presale-ai-support

### 升级说明
- 系统升级请提前备份
- 遵循语义化版本号
- 查看CHANGELOG了解变更

---

**最后更新**: 2026-02-15  
**版本**: v1.0.0
