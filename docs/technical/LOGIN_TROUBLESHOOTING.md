# 登录问题排查指南

## 问题现象
点击登录按钮后一直转圈，无法进入系统。

## 排查步骤

### 1. 检查后端服务是否启动

```bash
# 检查后端服务是否在运行
curl http://127.0.0.1:8000/health

# 如果返回 {"status": "ok", "version": "1.0.0"} 说明后端正常
# 如果没有响应，需要启动后端服务
```

**启动后端服务：**
```bash
cd /Users/flw/非标自动化项目管理系统
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. 检查前端服务是否启动

```bash
# 检查前端服务是否在运行
# 通常运行在 http://localhost:5173
```

**启动前端服务：**
```bash
cd frontend
npm run dev
```

### 3. 检查浏览器控制台

打开浏览器开发者工具（F12），查看：
- **Console标签**：是否有JavaScript错误
- **Network标签**：查看登录请求的状态
  - 如果请求失败（红色），查看错误信息
  - 如果请求pending（一直转圈），可能是后端未响应

### 4. 检查数据库是否有用户

```bash
# 使用SQLite命令行工具检查
sqlite3 data/app.db "SELECT id, username, is_active FROM users LIMIT 5;"
```

如果没有用户，需要初始化数据库：
```bash
python3 init_db.py
```

### 5. 检查CORS配置

如果看到CORS错误，检查：
- 后端 `app/core/config.py` 中的 `CORS_ORIGINS` 配置
- 前端运行端口是否在允许列表中
- 开发模式下 `DEBUG=True` 时会允许所有来源

### 6. 使用演示账户测试

如果后端服务未启动，可以使用演示账户登录：
- 用户名：从演示账号列表中选择（如 `chu_procurement`）
- 密码：`admin123`

系统会自动fallback到演示模式。

### 7. 检查API响应格式

如果API调用成功但登录失败，检查响应格式：
- 后端返回：`{"access_token": "...", "token_type": "bearer", "expires_in": 86400}`
- 前端期望：`response.data.access_token`

## 常见错误及解决方案

### 错误1：无法连接到服务器
**原因：** 后端服务未启动
**解决：** 启动后端服务（见步骤1）

### 错误2：CORS错误
**原因：** 前端端口不在CORS允许列表中
**解决：** 
- 开发模式：设置 `DEBUG=True` 在 `.env` 文件中
- 或更新 `CORS_ORIGINS` 配置

### 错误3：用户名或密码错误
**原因：** 数据库中没有该用户或密码不匹配
**解决：** 
- 使用演示账户测试
- 或检查数据库用户表

### 错误4：用户未激活
**原因：** 用户 `is_active=False`
**解决：** 更新数据库：`UPDATE users SET is_active=1 WHERE username='xxx';`

## 快速测试命令

```bash
# 测试后端健康检查
curl http://127.0.0.1:8000/health

# 测试登录API（需要替换用户名和密码）
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=test"

# 检查数据库用户
sqlite3 data/app.db "SELECT username, is_active FROM users;"
```

## 调试模式

在前端代码中，已添加了 `console.error` 和 `console.log` 来帮助调试：
- 打开浏览器控制台查看详细错误信息
- 查看网络请求的完整响应

