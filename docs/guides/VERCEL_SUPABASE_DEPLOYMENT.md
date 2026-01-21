# 🚀 Vercel + Supabase 免费部署指南

完全免费的云端部署方案，适合个人项目和小团队使用。

## 📋 方案优势

✅ **完全免费**
- Vercel: 免费托管前端 + Serverless API
- Supabase: 免费 PostgreSQL 数据库（500MB + 无限 API 请求）

✅ **性能优秀**
- 全球 CDN 加速
- 自动 HTTPS
- 秒级部署

✅ **易于维护**
- Git 自动部署
- 零配置服务器
- 在线管理面板

## 🎯 部署架构

```
用户浏览器
    ↓
Vercel CDN (前端 React)
    ↓
Vercel Serverless Functions (FastAPI)
    ↓
Supabase PostgreSQL (数据库)
```

---

## 第一步：Supabase 数据库设置

### 1.1 创建 Supabase 项目

1. 访问 https://supabase.com
2. 点击 **"Start your project"** 注册/登录（支持 GitHub 登录）
3. 点击 **"New Project"**
4. 填写项目信息：
   - **Name**: `non-standard-pm`
   - **Database Password**: 设置一个强密码（记住它！）
   - **Region**: 选择 `Northeast Asia (Tokyo)` 或最近的区域
   - **Pricing Plan**: Free（免费版）
5. 点击 **"Create new project"**（需要等待 1-2 分钟）

### 1.2 获取数据库连接信息

1. 项目创建完成后，点击左侧 **"Settings"** → **"Database"**
2. 找到 **"Connection string"** 部分
3. 选择 **"URI"** 格式
4. 复制连接字符串，格式如下：
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres
   ```
5. 将 `[YOUR-PASSWORD]` 替换为你刚才设置的数据库密码

### 1.3 初始化数据库

1. 在 Supabase Dashboard 中，点击左侧 **"SQL Editor"**
2. 点击 **"New query"**
3. 打开项目中的 `supabase-setup.sql` 文件
4. 复制全部内容，粘贴到 SQL Editor
5. 点击 **"Run"** 执行脚本
6. 看到成功提示后，点击 **"Table Editor"** 验证表已创建

**验证数据库**：
- 应该能看到 `users`, `roles`, `projects` 等表
- `users` 表中有一个 `admin` 用户

---

## 第二步：Vercel 部署

### 2.1 准备 Vercel 账号

1. 访问 https://vercel.com
2. 点击 **"Sign Up"**，使用 GitHub 账号登录
3. 授权 Vercel 访问你的 GitHub 仓库

### 2.2 推送代码到 GitHub

```bash
# 如果还没有 Git 仓库，初始化
cd /Users/flw/non-standard-automation-pm
git init
git add .
git commit -m "Initial commit for Vercel deployment"

# 创建 GitHub 仓库后推送
git remote add origin https://github.com/YOUR-USERNAME/non-standard-pm.git
git branch -M main
git push -u origin main
```

### 2.3 在 Vercel 中导入项目

1. 在 Vercel Dashboard，点击 **"Add New..."** → **"Project"**
2. 找到你的 GitHub 仓库 `non-standard-pm`，点击 **"Import"**
3. **不要急着点 Deploy！** 先配置环境变量

### 2.4 配置环境变量

在 Vercel 项目配置页面，点击 **"Environment Variables"**，添加以下变量：

#### 必需的环境变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `DATABASE_URL` | `postgresql://postgres:your-password@db.xxx.supabase.co:5432/postgres` | 从 Supabase 复制的连接字符串 |
| `SECRET_KEY` | 运行 `openssl rand -base64 32` 生成 | JWT 加密密钥 |

#### 可选的环境变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `DEBUG` | `false` | 生产环境必须为 false |
| `CORS_ORIGINS` | `https://your-app.vercel.app` | 跨域配置（部署后更新） |

**生成 SECRET_KEY**：
```bash
# 在终端运行
openssl rand -base64 32
```

### 2.5 部署项目

1. 添加完环境变量后，点击 **"Deploy"**
2. 等待构建完成（约 2-3 分钟）
3. 看到 🎉 **Congratulations!** 表示部署成功

---

## 第三步：访问和测试

### 3.1 获取部署 URL

部署成功后，Vercel 会提供一个 URL，格式如下：
```
https://non-standard-pm.vercel.app
```

### 3.2 测试应用

1. **测试前端**：
   - 访问 `https://your-app.vercel.app`
   - 应该能看到登录页面

2. **测试 API**：
   - 访问 `https://your-app.vercel.app/health`
   - 应该返回 `{"status":"ok"}`
   
3. **测试 API 文档**：
   - 访问 `https://your-app.vercel.app/docs`
   - 应该能看到 Swagger UI 文档

### 3.3 登录系统

使用默认管理员账号登录：
- **用户名**: `admin`
- **密码**: `admin123`

⚠️ **重要**：首次登录后立即修改密码！

---

## 第四步：配置自定义域名（可选）

### 4.1 在 Vercel 添加域名

1. 在 Vercel 项目页面，点击 **"Settings"** → **"Domains"**
2. 输入你的域名（如 `pm.yourdomain.com`）
3. 点击 **"Add"**

### 4.2 配置 DNS

在你的域名提供商（如 Cloudflare、阿里云）添加 DNS 记录：

- **类型**: CNAME
- **名称**: `pm`（或 `@` 如果是根域名）
- **值**: `cname.vercel-dns.com`

等待 DNS 生效（几分钟到几小时）。

### 4.3 更新 CORS 配置

在 Vercel 环境变量中更新 `CORS_ORIGINS`：
```
https://pm.yourdomain.com
```

---

## 📊 监控和维护

### 查看部署日志

1. 在 Vercel Dashboard，点击你的项目
2. 选择 **"Deployments"** 标签
3. 点击任意部署查看日志

### 查看数据库

1. 登录 Supabase Dashboard
2. 点击 **"Table Editor"** 查看数据
3. 点击 **"SQL Editor"** 执行 SQL 查询

### 查看应用日志

1. 在 Vercel，点击 **"Logs"** 标签
2. 实时查看函数执行日志

---

## 🔄 自动部署

配置完成后，每次推送代码到 GitHub 的 `main` 分支，Vercel 会自动：
1. 拉取最新代码
2. 构建前端和后端
3. 部署到生产环境

```bash
# 更新代码并自动部署
git add .
git commit -m "Update feature"
git push origin main
```

---

## 💾 数据备份

### 备份 Supabase 数据库

1. 在 Supabase Dashboard，点击 **"Database"** → **"Backups"**
2. 免费版提供 7 天自动备份
3. 可以手动导出数据：
   ```bash
   # 使用 pg_dump
   pg_dump "postgresql://postgres:password@db.xxx.supabase.co:5432/postgres" > backup.sql
   ```

### 恢复数据

1. 在 Supabase SQL Editor 中执行备份的 SQL 文件
2. 或使用命令行：
   ```bash
   psql "postgresql://postgres:password@db.xxx.supabase.co:5432/postgres" < backup.sql
   ```

---

## ⚠️ 限制说明

### Vercel 免费版限制

- ✅ 100 GB 带宽/月
- ✅ 无限部署次数
- ✅ Serverless Function: 10s 超时，1024MB 内存
- ⚠️ 不支持 WebSocket 长连接
- ⚠️ 不支持后台任务（定时任务需要使用外部服务）

### Supabase 免费版限制

- ✅ 500 MB 数据库存储
- ✅ 1 GB 文件存储
- ✅ 无限 API 请求
- ✅ 50,000 每月活跃用户
- ⚠️ 7 天不活跃会暂停（访问一次即可恢复）

---

## 🚨 常见问题

### 1. 部署失败："Module not found"

**原因**：依赖安装失败

**解决**：
1. 检查 `api/requirements.txt` 是否包含所有依赖
2. 在 Vercel 日志中查看具体错误
3. 尝试重新部署

### 2. 数据库连接失败

**检查项**：
1. DATABASE_URL 环境变量是否正确
2. 密码是否包含特殊字符（需要 URL 编码）
3. Supabase 项目是否处于活跃状态

**测试连接**：
```python
import psycopg2
conn = psycopg2.connect("postgresql://postgres:password@db.xxx.supabase.co:5432/postgres")
print("Connected!")
```

### 3. API 响应 500 错误

1. 在 Vercel 查看函数日志
2. 检查数据库表是否正确创建
3. 验证环境变量配置

### 4. CORS 错误

在 Vercel 环境变量中更新 `CORS_ORIGINS`：
```
https://your-app.vercel.app,https://pm.yourdomain.com
```

### 5. 前端无法调用 API

检查 `frontend/src/services/api.js` 中的 baseURL：
```javascript
const baseURL = import.meta.env.PROD 
  ? '/api/v1'  // 生产环境
  : 'http://localhost:8000/api/v1';  // 开发环境
```

### 6. Supabase 项目暂停

**现象**：7 天未访问，数据库自动暂停

**解决**：
1. 访问 Supabase Dashboard
2. 点击 **"Restore"** 恢复项目
3. 或设置定时任务每周访问一次应用

---

## 🎯 优化建议

### 1. 启用 Vercel Analytics

```bash
# 安装分析工具
npm install @vercel/analytics
```

在 `frontend/src/main.jsx` 添加：
```javascript
import { inject } from '@vercel/analytics';
inject();
```

### 2. 配置 Upstash Redis（可选）

如需缓存功能：
1. 访问 https://upstash.com
2. 创建免费 Redis 数据库
3. 在 Vercel 添加 `REDIS_URL` 环境变量

### 3. 设置告警通知

在 Supabase 中配置：
- 数据库使用率告警
- API 错误率监控

---

## 📱 移动端支持

前端自动适配移动设备，可以：
1. 添加到主屏幕（PWA）
2. 使用原生分享功能
3. 支持触摸手势

---

## 🔐 安全建议

1. **修改默认密码**：首次登录后立即修改 admin 密码
2. **定期更新密钥**：每 3-6 个月更新 SECRET_KEY
3. **启用 Row Level Security**：在 Supabase 启用 RLS
4. **限制 API 访问**：配置正确的 CORS_ORIGINS
5. **定期备份数据**：建议每周备份一次

---

## 📚 相关文档

- [Vercel 文档](https://vercel.com/docs)
- [Supabase 文档](https://supabase.com/docs)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [React 文档](https://react.dev/)

---

## ✅ 部署检查清单

- [ ] Supabase 项目已创建
- [ ] 数据库初始化脚本已执行
- [ ] Vercel 项目已创建
- [ ] 环境变量已配置（DATABASE_URL, SECRET_KEY）
- [ ] 项目已成功部署
- [ ] 前端可访问（https://your-app.vercel.app）
- [ ] API 健康检查通过（/health）
- [ ] 可以使用 admin 账号登录
- [ ] 已修改默认密码
- [ ] （可选）自定义域名已配置

---

## 🎉 恭喜！

你的项目现在已经成功部署到云端，完全免费且可随时访问！

有任何问题，请参考文档或查看部署日志。
