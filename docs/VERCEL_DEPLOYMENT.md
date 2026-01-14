# Vercel 部署方案对比

## 方案一：全部署到 Vercel（推荐）

```
┌─────────────────┐
│  Vercel (前端)  │  ← frontend/
│    React SPA    │
└─────────────────┘
         │
         ↓ 内部调用
┌─────────────────┐
│  Vercel (后端)  │  ← app/ (Serverless Functions)
│   FastAPI       │
└─────────────────┘
         │
         ↓
┌─────────────────┐
│  Vercel Postgres │  ← 数据库
└─────────────────┘
```

**优点：**
- 全在一个平台，管理简单
- Vercel 免费额度充足
- 自动 HTTPS
- 边缘网络加速

**缺点：**
- Serverless 有冷启动延迟
- 无状态，不适合 WebSocket
- 单次请求最长 60 秒

---

## 方案二：Vercel + Railway

**优点：**
- 后端可长运行
- 数据库独立
- 更适合复杂业务

---

## 方案一配置（全 Vercel）
