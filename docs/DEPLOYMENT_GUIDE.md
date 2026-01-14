# Vercel 部署完整指南

## 方案架构

```
┌─────────────────┐
│  Vercel (前端)  │  ← frontend/
│    React SPA    │
└────────┬────────┘
         │ HTTPS
         ↓
┌─────────────────┐
│   Railway       │  ← app/ (后端 API)
│  FastAPI        │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   Railway       │  ← MySQL/PostgreSQL
│   Database      │
└─────────────────┘
```

---

## 第一步：配置前端环境变量

1. 打开 `.env` 文件：
   ```bash
   vim frontend/.env
   ```

2. 添加后端 API 地址（部署后更新）：
   ```env
   VITE_API_BASE_URL=https://your-backend.railway.app
   ```

3. 确保 `frontend/vite.config.js` 代理已配置（本地开发用）：
   ```js
   server: {
     proxy: {
       '/api': {
         target: 'http://localhost:8000',
         changeOrigin: true
       }
     }
   }
   ```

---

## 第二步：部署后端到 Railway

### 2.1 安装 Railway CLI
```bash
npm install -g @railway/cli
railway login
```

### 2.2 创建 Railway 项目
```bash
cd /Users/flw/non-standard-automation-pm
railway init
# 输入项目名称: non-standard-automation-pms
```

### 2.3 添加 MySQL 数据库
```bash
railway add mysql
# Railway 会自动生成 DATABASE_URL 环境变量
```

### 2.4 配置后端服务
创建 `railway.toml`：
```toml
[build]
builder = "nixpacks"

[build.env]
PYTHON_VERSION = "3.9"

[[services]]
name = "api"
command = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"

[[services.ports]]
port = 8000
```

### 2.5 设置环境变量
```bash
railway variables set SECRET_KEY="your-secret-key-here"
railway variables set ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

### 2.6 初始化数据库
```bash
railway run python3 init_db.py
```

### 2.7 部署
```bash
railway up
```

### 2.8 获取后端 URL
```bash
railway domain
# 输出示例: https://non-standard-automation-pms-production.up.railway.app
```

---

## 第三步：更新前端环境变量

1. 更新 `frontend/.env`：
   ```env
   VITE_API_BASE_URL=https://your-backend-url.railway.app
   ```

2. 重新构建前端：
   ```bash
   cd frontend
   npm run build
   ```

---

## 第四步：部署前端到 Vercel

### 4.1 安装 Vercel CLI
```bash
npm install -g vercel
vercel login
```

### 4.2 部署到预览环境
```bash
vercel
# 按提示操作：
# - Set up and deploy: Yes
# - Which scope: 选择你的账号
# - Link to existing project: No
# - Project name: non-standard-automation-pms
# - In which directory: frontend
# - Override settings: Yes
```

### 4.3 配置 Vercel 项目
部署后访问 https://vercel.com/dashboard，进入项目设置：

**Settings → Environment Variables** 添加：
```
VITE_API_BASE_URL = https://your-backend-url.railway.app
```

**Settings → Build & Development** 配置：
```
Framework Preset: Vite
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

### 4.4 部署到生产环境
```bash
vercel --prod
```

---

## 第五步：验证部署

### 5.1 检查后端健康
```bash
curl https://your-backend.railway.app/health
# 期望输出: {"status": "healthy"}
```

### 5.2 检查前端
访问 Vercel 提供的 URL，确认：
- 页面正常加载
- API 请求成功
- 可以登录（需要后端有数据）

---

## 故障排查

### 后端无法连接数据库
```bash
# 检查 Railway 变量
railway variables

# 查看日志
railway logs
```

### 前端 API 请求失败
1. 检查 `VITE_API_BASE_URL` 是否正确
2. 检查后端 CORS 配置 (`app/core/config.py`):
   ```python
   CORS_ORIGINS=["https://your-vercel-domain.vercel.app"]
   ```

### 数据库未初始化
```bash
# 在 Railway 环境中运行
railway run python3 init_db.py
```

---

## 本地开发命令

```bash
# 后端
uvicorn app.main:app --reload

# 前端
cd frontend && npm run dev
```

---

## 目录结构总结

| 组件 | 目录 | 部署平台 |
|------|------|---------|
| 前端 | `frontend/` | Vercel |
| 后端 | `app/` | Railway |
| 数据库 | - (由 Railway 托管) | Railway MySQL |
