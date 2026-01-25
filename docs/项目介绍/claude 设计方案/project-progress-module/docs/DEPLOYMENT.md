# 项目进度管理系统 - 部署指南

## 目录
1. [环境要求](#环境要求)
2. [Docker快速部署](#docker快速部署)
3. [手动部署](#手动部署)
4. [生产环境配置](#生产环境配置)
5. [企业微信集成](#企业微信集成)
6. [常见问题](#常见问题)

---

## 环境要求

| 组件 | 最低版本 | 推荐版本 |
|------|---------|---------|
| Docker | 20.10 | 24.0 |
| Docker Compose | 2.0 | 2.20 |
| Python | 3.11 | 3.11 |
| Node.js | 18 | 20 LTS |
| MySQL | 8.0 | 8.0 |
| Redis | 7.0 | 7.2 |

### 服务器配置

| 场景 | CPU | 内存 | 存储 |
|------|-----|------|------|
| 开发测试 | 2核 | 4GB | 20GB |
| 生产(50用户) | 4核 | 8GB | 50GB SSD |
| 生产(200用户) | 8核 | 16GB | 100GB SSD |

---

## Docker快速部署

### 步骤1: 准备环境

```bash
# 解压项目
unzip project-progress-module.zip
cd project-progress-module

# 创建环境变量文件
cat > .env << EOF
MYSQL_ROOT_PASSWORD=Root@123456
MYSQL_DATABASE=project_progress
MYSQL_USER=project
MYSQL_PASSWORD=Project@123

# 企业微信(可选)
WECHAT_CORP_ID=
WECHAT_AGENT_ID=
WECHAT_SECRET=
EOF
```

### 步骤2: 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看启动状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

### 步骤3: 验证部署

```bash
# 检查API
curl http://localhost:8000/health
# 期望输出: {"status":"healthy"}

# 检查API文档
# 浏览器打开: http://localhost:8000/api/docs
```

### 步骤4: 访问系统

- **前端界面**: http://localhost
- **API文档**: http://localhost:8000/api/docs
- **数据库**: localhost:3306
- **Redis**: localhost:6379

---

## 手动部署

### 后端部署

```bash
cd backend

# 1. 创建Python虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 配置数据库
export DATABASE_URL="mysql+pymysql://project:password@localhost:3306/project_progress"
export REDIS_URL="redis://localhost:6379/0"

# 4. 初始化数据库
mysql -u root -p < ../database/ddl_script.sql

# 5. 启动服务
# 开发环境
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 生产环境
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### 前端部署

```bash
cd frontend

# 1. 安装依赖
npm install --registry=https://registry.npmmirror.com

# 2. 开发模式
npm run dev

# 3. 生产构建
npm run build

# 4. 部署静态文件
# 将 dist/ 目录部署到Nginx
```

### Nginx配置

```nginx
# /etc/nginx/conf.d/project-progress.conf
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /var/www/project-progress/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
        
        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_read_timeout 300s;
    }
}
```

---

## 生产环境配置

### 使用Systemd管理服务

```bash
# /etc/systemd/system/project-progress.service
[Unit]
Description=Project Progress API
After=network.target mysql.service redis.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/project-progress/backend
Environment="PATH=/var/www/project-progress/backend/venv/bin"
Environment="DATABASE_URL=mysql+pymysql://project:password@localhost:3306/project_progress"
Environment="REDIS_URL=redis://localhost:6379/0"
ExecStart=/var/www/project-progress/backend/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable project-progress
sudo systemctl start project-progress
sudo systemctl status project-progress
```

### SSL证书配置

```bash
# 使用Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

### 数据库备份

```bash
#!/bin/bash
# /opt/scripts/backup_db.sh
BACKUP_DIR=/data/backups
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME=project_progress

# 备份
mysqldump -u backup_user -p'password' $DB_NAME | gzip > ${BACKUP_DIR}/db_${DATE}.sql.gz

# 保留30天
find ${BACKUP_DIR} -name "db_*.sql.gz" -mtime +30 -delete
```

```bash
# 添加定时任务 (每天凌晨2点)
crontab -e
0 2 * * * /opt/scripts/backup_db.sh >> /var/log/backup.log 2>&1
```

---

## 企业微信集成

### 1. 创建企业微信应用

1. 登录 [企业微信管理后台](https://work.weixin.qq.com)
2. 进入 **应用管理** > **自建应用** > **创建应用**
3. 填写应用信息，获取:
   - 企业ID (CorpId)
   - 应用ID (AgentId)
   - 应用Secret

### 2. 配置环境变量

```bash
export WECHAT_CORP_ID=ww1234567890abcdef
export WECHAT_AGENT_ID=1000002
export WECHAT_SECRET=your_app_secret_here
```

### 3. 配置可信域名

在企业微信管理后台:
- **网页授权及JS-SDK**: 添加 `your-domain.com`
- **企业可信IP**: 添加服务器公网IP

### 4. 消息推送场景

系统自动推送以下消息:
- ✅ 任务分配通知
- ✅ 任务逾期预警
- ✅ 进度更新提醒
- ✅ 工时审批通知
- ✅ 项目周报提醒

---

## 常见问题

### Q1: Docker启动失败 - 端口冲突

```bash
# 检查端口占用
sudo netstat -tlnp | grep -E '(80|3306|6379|8000)'

# 解决方案: 修改docker-compose.yml中的端口映射
ports:
  - "8080:80"    # 改为8080
  - "3307:3306"  # 改为3307
```

### Q2: 数据库连接失败

```bash
# 检查MySQL容器状态
docker logs project-progress-mysql

# 测试连接
docker exec -it project-progress-mysql mysql -uproject -p

# 检查配置
docker exec project-progress-backend env | grep DATABASE
```

### Q3: 前端API请求失败

1. 检查后端是否正常: `curl http://localhost:8000/health`
2. 检查Nginx代理配置
3. 查看浏览器控制台错误信息
4. 检查CORS配置

### Q4: 企业微信消息发送失败

```bash
# 测试access_token获取
curl "https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid=${WECHAT_CORP_ID}&corpsecret=${WECHAT_SECRET}"

# 常见错误:
# 40001: Secret错误
# 40013: CorpId错误
# 60020: IP不在白名单
```

### Q5: 如何查看API日志

```bash
# Docker部署
docker logs -f project-progress-backend --tail 100

# Systemd部署
journalctl -u project-progress -f
```

### Q6: 如何重置数据

```bash
# 停止服务
docker-compose down

# 删除数据卷
docker volume rm project-progress-module_mysql_data

# 重新启动
docker-compose up -d
```

---

## 联系支持

如有问题，请通过以下方式联系:
- 📧 Email: support@example.com
- 📖 文档: https://docs.example.com
- 🐛 Issue: https://github.com/example/project-progress/issues
