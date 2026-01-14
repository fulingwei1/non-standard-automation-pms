# 非标自动化项目管理系统 - Docker Compose 部署指南

## 前置要求

1. **Docker Desktop** 
   - macOS: 从 [Docker官网](https://www.docker.com/products/docker-desktop/) 下载安装
   - 确保 Docker Desktop 正在运行（菜单栏有 Docker 图标）

2. **系统要求**
   - 至少 4GB 可用内存
   - 至少 10GB 可用磁盘空间

## 快速部署

### 方式一：一键部署（推荐）

```bash
# 确保 Docker Desktop 正在运行
./deploy.sh
```

### 方式二：手动部署

#### 1. 启动 Docker Desktop
确保 Docker Desktop 正在运行

#### 2. 构建前端
```bash
cd frontend
npm ci
npm run build
cd ..
```

#### 3. 启动服务
```bash
docker compose -f docker-compose.production.yml --env-file .env.production up -d --build
```

#### 4. 查看状态
```bash
docker compose -f docker-compose.production.yml ps
```

## 访问系统

部署成功后，可以通过以下地址访问：

- **前端界面**: http://localhost
- **API文档**: http://localhost/docs
- **API ReDoc**: http://localhost/redoc
- **健康检查**: http://localhost/health

## 默认账号

首次部署后，使用以下账号登录：

- **用户名**: `admin`
- **密码**: `admin123`

⚠️ **重要**: 首次登录后请立即修改密码！

## 服务管理

### 查看日志
```bash
# 查看所有服务日志
docker compose -f docker-compose.production.yml logs -f

# 查看指定服务日志
docker compose -f docker-compose.production.yml logs -f app
docker compose -f docker-compose.production.yml logs -f mysql
docker compose -f docker-compose.production.yml logs -f redis
```

### 停止服务
```bash
docker compose -f docker-compose.production.yml down
```

### 重启服务
```bash
# 重启所有服务
docker compose -f docker-compose.production.yml restart

# 重启指定服务
docker compose -f docker-compose.production.yml restart app
```

### 查看服务状态
```bash
docker compose -f docker-compose.production.yml ps
```

### 进入容器
```bash
# 进入应用容器
docker compose -f docker-compose.production.yml exec app bash

# 进入数据库容器
docker compose -f docker-compose.production.yml exec mysql bash
```

## 数据备份

### 备份 MySQL 数据库
```bash
docker compose -f docker-compose.production.yml exec mysql \
  mysqldump -u root -p'RootPass2026!SecureDB' pms > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 恢复数据库
```bash
docker compose -f docker-compose.production.yml exec -T mysql \
  mysql -u root -p'RootPass2026!SecureDB' pms < backup_20260110_120000.sql
```

### 备份上传文件
```bash
tar -czf uploads_backup_$(date +%Y%m%d_%H%M%S).tar.gz uploads/
```

## 配置说明

### 环境变量（.env.production）

```env
# 数据库密码（请修改为强密码）
DB_ROOT_PASSWORD=RootPass2026!SecureDB
DB_PASSWORD=PMSPass2026!AppDB

# JWT 密钥（自动生成，请勿修改）
SECRET_KEY=Nb+cWzRHBeCbboAsAeaEeYn216fNvQknCsbvKWimDJ0=

# 调试模式（生产环境必须为 false）
DEBUG=false

# CORS 配置（根据实际域名修改）
CORS_ORIGINS=http://localhost,http://yourdomain.com
```

### 端口配置

默认端口映射：
- **80**: 前端 Nginx（可访问前端界面和 API）
- **3306**: MySQL 数据库
- **6379**: Redis 缓存
- **8000**: 后端 API（内部）

如需修改端口，编辑 `docker-compose.production.yml` 文件的 `ports` 部分。

## 常见问题

### 1. Docker 命令报错 "Cannot connect to the Docker daemon"

**原因**: Docker Desktop 未运行

**解决**: 
- 启动 Docker Desktop 应用
- 等待 Docker 图标显示为绿色
- 重新运行部署命令

### 2. 端口被占用

**错误信息**: "port is already allocated"

**解决**:
```bash
# 查看占用端口的进程
lsof -i :80
lsof -i :3306

# 停止占用端口的服务或修改 docker-compose.production.yml 中的端口映射
```

### 3. 前端无法访问后端 API

**检查项**:
1. 确认所有服务都在运行: `docker compose -f docker-compose.production.yml ps`
2. 查看应用日志: `docker compose -f docker-compose.production.yml logs app`
3. 测试健康检查: `curl http://localhost/health`

### 4. 数据库连接失败

**检查项**:
```bash
# 查看 MySQL 日志
docker compose -f docker-compose.production.yml logs mysql

# 测试数据库连接
docker compose -f docker-compose.production.yml exec mysql \
  mysql -u pms -p'PMSPass2026!AppDB' -e "SELECT 1"
```

### 5. 内存不足

**症状**: 容器频繁重启或无法启动

**解决**:
1. 增加 Docker Desktop 的内存限制（设置 → Resources → Memory）
2. 减少工作进程数量（编辑 Dockerfile.fullstack，修改 `--workers 4` 为 `--workers 2`）

### 6. 构建失败

**解决**:
```bash
# 清理缓存重新构建
docker compose -f docker-compose.production.yml build --no-cache

# 如果还是失败，尝试清理所有 Docker 缓存
docker system prune -a
```

## 生产环境优化

### 1. 使用外部数据库

修改 `.env.production`:
```env
DATABASE_URL=mysql+pymysql://user:password@your-mysql-host:3306/pms
```

然后注释掉 `docker-compose.production.yml` 中的 mysql 服务。

### 2. 配置 HTTPS

1. 准备 SSL 证书（cert.pem 和 key.pem）
2. 修改 `Dockerfile.fullstack` 中的 Nginx 配置，添加 SSL 支持
3. 修改端口映射为 `443:443`

### 3. 配置域名

修改 `.env.production`:
```env
CORS_ORIGINS=https://yourdomain.com
```

### 4. 邮件通知

修改 `.env.production`:
```env
EMAIL_ENABLED=true
EMAIL_SMTP_SERVER=smtp.example.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=noreply@example.com
EMAIL_PASSWORD=your_smtp_password
```

### 5. 监控和日志

添加日志收集和监控服务（Prometheus + Grafana）:
```bash
docker compose -f docker-compose.production.yml --profile monitoring up -d
```

## 更新部署

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建和部署
./deploy.sh

# 或手动执行
cd frontend && npm run build && cd ..
docker compose -f docker-compose.production.yml up -d --build
```

## 完全卸载

```bash
# 停止并删除所有容器、网络
docker compose -f docker-compose.production.yml down

# 删除数据卷（⚠️ 会删除所有数据）
docker compose -f docker-compose.production.yml down -v

# 删除镜像
docker rmi $(docker images -q 'non-standard-automation-pm*')
```

## 技术支持

如遇问题，请提供以下信息：

```bash
# 系统信息
docker --version
docker compose version

# 服务状态
docker compose -f docker-compose.production.yml ps

# 最近日志
docker compose -f docker-compose.production.yml logs --tail=100

# 资源使用
docker stats --no-stream
```

## 架构说明

```
┌─────────────────────────────────────────┐
│           前端用户访问 :80               │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│         Nginx (静态文件 + 反向代理)      │
├─────────────────────────────────────────┤
│  /          → 前端静态文件               │
│  /api/*     → 后端 FastAPI (8000)      │
│  /docs      → API 文档                  │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌──────────────┐        ┌──────────────┐
│   FastAPI    │        │    Redis     │
│   Backend    │◄──────►│   Cache      │
│   (8000)     │        │   (6379)     │
└──────┬───────┘        └──────────────┘
       │
       ▼
┌──────────────┐
│    MySQL     │
│   Database   │
│   (3306)     │
└──────────────┘
```

## 许可证

[待添加]
