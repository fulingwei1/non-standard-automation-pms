# Docker 配置文件

本目录包含所有 Docker 相关的配置文件。

---

## 📦 Dockerfile

### [Dockerfile](Dockerfile)
- **用途**: 标准后端 API 服务镜像
- **基础镜像**: Python 3.11
- **暴露端口**: 8000

### [Dockerfile.fullstack](Dockerfile.fullstack)
- **用途**: 全栈应用镜像（前端+后端）
- **包含**: FastAPI后端 + React前端
- **适用**: 单容器部署场景

### [Dockerfile.nginx](Dockerfile.nginx)
- **用途**: Nginx + WAF 镜像
- **功能**: 反向代理 + ModSecurity WAF
- **配置**: 见 `nginx/` 目录

---

## 🐳 Docker Compose 配置

### [docker-compose.yml](docker-compose.yml)
- **用途**: 开发环境标准配置
- **服务**: 
  - backend (FastAPI)
  - frontend (React开发服务器)
  - db (MySQL)
  - redis
- **网络**: 内部网络隔离

### [docker-compose.production.yml](docker-compose.production.yml)
- **用途**: 生产环境配置
- **特点**:
  - 生产级优化
  - 资源限制
  - 健康检查
  - 日志配置

### [docker-compose.waf.yml](docker-compose.waf.yml)
- **用途**: WAF（Web应用防火墙）部署
- **服务**:
  - nginx-waf (Nginx + ModSecurity)
  - backend
  - db
- **安全**: OWASP CRS 规则集

### [docker-compose.secrets.yml](docker-compose.secrets.yml)
- **用途**: 密钥管理增强配置
- **功能**: Docker Secrets / AWS Secrets Manager 集成
- **适用**: 敏感信息管理

---

## 📁 nginx/ 目录

包含 Nginx 相关配置：

```
nginx/
├── conf.d/          - 站点配置
├── modsecurity/     - ModSecurity WAF 规则
├── ssl/             - SSL 证书
└── nginx.conf       - 主配置文件
```

---

## 🚀 快速开始

### 开发环境

```bash
# 启动开发环境
cd docker/
docker-compose up -d

# 查看日志
docker-compose logs -f backend

# 停止
docker-compose down
```

### 生产环境

```bash
# 使用生产配置启动
cd docker/
docker-compose -f docker-compose.production.yml up -d

# 健康检查
docker-compose -f docker-compose.production.yml ps
```

### WAF 部署

```bash
# 启动 WAF
cd docker/
docker-compose -f docker-compose.waf.yml up -d

# 查看 WAF 日志
docker-compose -f docker-compose.waf.yml logs -f nginx-waf
```

---

## 🔧 自定义配置

### 环境变量

在项目根目录创建 `.env` 文件：

```env
# 数据库
DATABASE_URL=mysql://user:password@db:3306/pms
REDIS_URL=redis://redis:6379/0

# 密钥
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret

# API
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### 端口映射

默认端口：
- **后端 API**: 8000
- **前端**: 3000
- **Nginx (WAF)**: 80, 443
- **MySQL**: 3306
- **Redis**: 6379

可在 docker-compose*.yml 中修改。

---

## 📊 资源要求

### 最低配置
- **CPU**: 2核
- **内存**: 4GB
- **磁盘**: 20GB

### 推荐配置（生产）
- **CPU**: 4核+
- **内存**: 8GB+
- **磁盘**: 50GB+

---

## 🔗 相关文档

- [WAF 部署指南](../docs/modules/README_WAF.md)
- [安全最佳实践](../docs/security/)
- [API 文档](../docs/)

---

**最后更新**: 2026-02-25
