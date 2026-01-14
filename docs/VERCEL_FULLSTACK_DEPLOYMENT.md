# Vercel 全栈部署指南（推荐）

## 架构

```
┌─────────────────┐
│  Vercel (前端)  │  ← frontend/ (React)
│    React SPA    │
└────────┬────────┘
         │ 相对路径 /api/v1
         ↓
┌─────────────────┐
│  Vercel (后端)  │  ← api/ (Serverless Functions)
│   FastAPI       │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Vercel Postgres │  ← 托管数据库
└─────────────────┘
```

---

## 前置要求

1. Vercel 账号
2. GitHub 仓库（已连接）
3. Vercel Postgres 数据库

---

## 第一步：配置数据库

### 1.1 创建 Vercel Postgres

访问 https://vercel.com/dashboard，进入项目：

1. **Storage** → **Create Database** → **Postgres**
2. 选择免费或付费计划
3. 记录连接信息

### 1.2 获取连接信息

在 Vercel Dashboard → Storage → Database → **Connect**：

复制 `.env.local` 内容：
```env
POSTGRES_URL="postgres://user:pass@host:5432/dbname"
POSTGRES_PRISMA_URL="..."
POSTGRES_URL_NON_POOLING="..."
```

---

## 第二步：更新后端配置

### 2.1 修改 `app/core/config.py`

```python
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    
    # 数据库配置 - 优先使用 Vercel Postgres
    DATABASE_URL: str = os.getenv(
        "POSTGRES_URL",
        "sqlite:///./data/app.db"
    )
    
    # CORS 配置
    CORS_ORIGINS: list = ["*"]  # 生产环境请限制

    class Config:
        env_file = ".env"


settings = Settings()
```

### 2.2 修改 `app/models/base.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# 根据数据库类型选择引擎
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    # PostgreSQL（Vercel Postgres）
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

### 2.3 确保依赖完整

检查 `api/requirements.txt` 包含：
```txt
# ... 其他依赖
mangum==0.17.0
psycopg2-binary==2.9.9  # PostgreSQL 驱动
```

---

## 第三步：配置 Vercel

### 3.1 设置环境变量

在 Vercel Dashboard → Settings → Environment Variables：

| 变量名 | 值 | 环境 |
|--------|-----|------|
| `SECRET_KEY` | `your-random-secret-key` | All |
| `POSTGRES_URL` | 从 Vercel Postgres 复制 | All |
| `POSTGRES_PRISMA_URL` | 从 Vercel Postgres 复制 | All |

### 3.2 验证配置

检查 `vercel.json`：
```json
{
  "version": 2,
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "installCommand": "cd frontend && npm install",
  "framework": "vite",
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.9",
      "maxDuration": 60
    }
  },
  "rewrites": [
    { "source": "/api/:path*", "destination": "/api/index.py" },
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

---

## 第四步：初始化数据库

### 4.1 本地运行初始化脚本

```bash
# 设置环境变量（使用 Vercel Postgres）
export POSTGRES_URL="postgres://user:pass@host:5432/dbname"

# 运行初始化
python3 init_db.py
```

### 4.2 或通过 Vercel CLI

```bash
vercel env pull .env.local
python3 init_db.py
```

---

## 第五步：部署

### 5.1 安装 Vercel CLI

```bash
npm install -g vercel
vercel login
```

### 5.2 部署到预览环境

```bash
vercel
# 按提示操作
```

### 5.3 部署到生产环境

```bash
vercel --prod
```

---

## 第六步：验证部署

### 6.1 检查后端

```bash
curl https://your-app.vercel.app/api/v1/health
# 期望: {"status":"healthy"}
```

### 6.2 检查前端

访问 https://your-app.vercel.app，确认：
- 页面加载
- 可以登录
- API 请求成功

---

## 故障排查

### 后端返回 500 错误

查看 Vercel Logs：
```bash
vercel logs
```

常见问题：
- 数据库连接失败 → 检查 `POSTGRES_URL`
- 缺少依赖 → 检查 `api/requirements.txt`

### CORS 错误

在 `vercel.json` 中已配置，确保：
- 前端使用相对路径 `/api/v1`
- 后端 `CORS_ORIGINS` 包含前端域名

### 冷启动延迟

Vercel Serverless 首次请求有 1-3 秒延迟，正常现象。

---

## 本地开发

```bash
# 后端（使用本地 SQLite）
uvicorn app.main:app --reload

# 前端
cd frontend && npm run dev
```

---

## 费用

| 服务 | 免费额度 | 付费计划 |
|------|---------|---------|
| Vercel 部署 | 100GB 带宽/月 | $20/月 起 |
| Vercel Postgres | 512MB 存储 | $0.04/GB + $0.125/小时 |
| Serverless Functions | 100GB-hrs/月 | $0.60/百万请求 |
