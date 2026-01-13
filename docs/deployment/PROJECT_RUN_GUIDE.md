# 项目运行指南

> **运行日期**: 2026-01-12  
> **运行状态**: ✅ 后端和前端都已运行

---

## 一、当前运行状态

### 1.1 后端服务

| 指标 | 状态 | 说明 |
|-----|:----:|------|
| **端口** | 8000 | ✅ 正常监听 |
| **进程** | ✅ | uvicorn已启动 |
| **配置** | ✅ | DEBUG模式已启用 |
| **SECRET_KEY** | ✅ | 已自动生成 |
| **日志** | ✅ | 输出到backend.log |

**启动命令**:
```bash
cd /Users/flw/non-standard-automation-pm
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
```

**验证命令**:
```bash
# 检查端口
lsof -i :8000

# 查看日志
tail -f backend.log

# 健康检查
curl http://localhost:8000/health
```

### 1.2 前端服务

| 指标 | 状态 | 说明 |
|-----|:----:|------|
| **端口** | 3000 | ✅ 正常监听 |
| **进程** | ✅ | Node.js已启动 |
| **页面** | ✅ | 前端页面已加载 |

**启动命令**:
```bash
cd /Users/flw/non-standard-automation-pm/frontend
npm start
```

**验证命令**:
```bash
# 检查端口
lsof -i :3000

# 访问前端
http://localhost:3000
```

---

## 二、访问地址

### 2.1 前端访问

**基础地址**:
```
http://localhost:3000
```

**主要页面**:
- 🏠 **首页/仪表盘**: `http://localhost:3000`
- 📊 **项目看板**: `http://localhost:3000/board`
- 📋 **项目列表**: `http://localhost:3000/projects`
- ⏰ **排期看板**: `http://localhost:3000/schedule`
- 📝 **任务中心**: `http://localhost:3000/tasks`

### 2.2 后端API

**基础地址**:
```
http://localhost:8000
```

**API前缀**:
```
/api/v1
```

**API文档**:
```
http://localhost:8000/docs
```

**主要API端点**:
- 登录: `POST /api/v1/auth/login`
- 项目列表: `GET /api/v1/projects`
- 项目详情: `GET /api/v1/projects/{id}`
- 进度预测: `GET /api/v1/progress/projects/{id}/progress-forecast`
- 依赖检查: `GET /api/v1/progress/projects/{id}/dependency-check`
- 自动处理: `POST /api/v1/progress/projects/{id}/auto-process-complete`

---

## 三、新功能访问

### 3.1 进度预测看板

**访问方式1**: 直接URL
```
http://localhost:3000/projects/1/progress-forecast
```

**访问方式2**: 从项目详情页
1. 进入项目详情页: `http://localhost:3000/projects/1`
2. 点击"进度计划"标签页
3. 点击"智能化进度管理"卡片中的"查看进度预测"按钮

**访问方式3**: 从项目详情页标签页
1. 进入项目详情页: `http://localhost:3000/projects/1`
2. 点击"进度预测"标签页

**权限要求**: 只有以下角色能访问
- ✅ ADMIN - 系统管理员
- ✅ GM - 总经理
- ✅ PM - 项目经理
- ✅ PMC - 计划管理
- ✅ PROJECT_MANAGER - 项目经理

### 3.2 依赖巡检结果

**访问方式1**: 直接URL
```
http://localhost:3000/projects/1/dependency-check
```

**访问方式2**: 从项目详情页
1. 进入项目详情页: `http://localhost:3000/projects/1`
2. 点击"进度计划"标签页
3. 点击"智能化进度管理"卡片中的"检查依赖关系"按钮

**访问方式3**: 从项目详情页标签页
1. 进入项目详情页: `http://localhost:3000/projects/1`
2. 点击"依赖巡检"标签页

**权限要求**: 只有以下角色能访问
- ✅ ADMIN - 系统管理员
- ✅ GM - 总经理
- ✅ PM - 项目经理
- ✅ PMC - 计划管理
- ✅ PROJECT_MANAGER - 项目经理

---

## 四、演示账号

### 4.1 可用的角色

**管理员账号**:
- **用户名**: `admin`
- **密码**: `admin123`
- **角色**: 系统管理员
- **权限**: 所有功能

**管理层账号**:
- **用户名**: `gm`
- **密码**: `gm123`
- **角色**: 总经理
- **权限**: 监控所有项目和功能

**项目经理账号**:
- **用户名**: `pm`
- **密码**: `pm123`
- **角色**: 项目经理
- **权限**: 管理负责的项目

**普通用户账号**:
- **用户名**: `engineer`
- **密码**: `engineer123`
- **角色**: 工程师
- **权限**: 查看自己参与的项目

### 4.2 登录步骤

1. 打开浏览器，访问: `http://localhost:3000`
2. 输入用户名和密码
3. 点击"登录"按钮
4. 登录成功后会自动跳转到对应的工作台

### 4.3 权限测试

**测试1**: 使用管理员账号访问
1. 使用 `admin/admin123` 登录
2. 访问: `http://localhost:3000/projects/1/progress-forecast`
3. **预期**: 能正常访问，显示进度预测看板

**测试2**: 使用项目经理账号访问
1. 使用 `pm/pm123` 登录
2. 访问: `http://localhost:3000/projects/1/progress-forecast`
3. **预期**: 能正常访问，显示进度预测看板

**测试3**: 使用工程师账号访问
1. 使用 `engineer/engineer123` 登录
2. 访问: `http://localhost:3000/projects/1/progress-forecast`
3. **预期**: 显示"权限不足"提示页面

---

## 五、新功能使用指南

### 5.1 进度预测看板

**核心功能**:
1. ✅ 进度预测概览（当前进度、预测完成日期、预测延期天数）
2. ✅ 未来进度预期（未来7天和14天的预期增长）
3. ✅ 延迟任务列表（显示所有延迟任务）
4. ✅ 自动处理选项配置（自动阻塞开关、延迟阈值设置）
5. ✅ 预览自动处理结果
6. ✅ 执行自动处理流程

**使用流程**:
1. 进入项目详情页
2. 点击"进度计划"标签页
3. 点击"智能化进度管理"卡片中的"查看进度预测"按钮
4. 查看预测数据和延迟任务
5. 配置自动处理选项（可选）
6. 点击"预览自动处理"查看将要执行的操作
7. 点击"执行自动处理"应用预测结果

**自动处理功能**:
- 🚫 **自动阻塞延迟任务**: 超过阈值的任务会被阻塞
- 🚫 **延迟阈值设置**: 1-30天可配置
- 📧 **发送通知**: 自动发送进度预警通知

### 5.2 依赖巡检结果

**核心功能**:
1. ✅ 依赖问题概览（循环依赖、时序冲突、缺失依赖）
2. ✅ 循环依赖详情（显示所有循环依赖链）
3. ✅ 时序冲突详情（显示所有时序冲突）
4. ✅ 缺失依赖详情（显示所有缺失的依赖关系）
5. ✅ 自动修复选项配置（自动修复时序冲突、自动移除缺失依赖）
6. ✅ 预览修复操作
7. ✅ 执行依赖修复

**使用流程**:
1. 进入项目详情页
2. 点击"进度计划"标签页
3. 点击"智能化进度管理"卡片中的"检查依赖关系"按钮
4. 查看依赖问题分类和详情
5. 配置自动修复选项（可选）
6. 点击"预览修复"查看将要执行的修复操作
7. 点击"执行修复"修复依赖问题

**自动修复功能**:
- ⚠️ **自动修复时序冲突**: 自动调整任务计划时间
- ⚠️ **自动移除缺失依赖**: 自动删除指向不存在任务的依赖
- 🚫 **循环依赖**: 无法自动修复，需要手动处理

---

## 六、常见问题

### 6.1 后端无法启动

**问题**: 端口8000已被占用

**解决方案**:
```bash
# 杀掉占用8000端口的进程
lsof -ti :8000 | xargs kill -9

# 重新启动后端
cd /Users/flw/non-standard-automation-pm
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
```

### 6.2 前端无法启动

**问题**: 端口3000已被占用

**解决方案**:
```bash
# 杀掉占用3000端口的进程
lsof -ti :3000 | xargs kill -9

# 重新启动前端
cd /Users/flw/non-standard-automation-pm/frontend
npm start
```

### 6.3 权限不足提示

**问题**: 访问进度预测或依赖检查页面时显示"权限不足"

**解决方案**:
1. 使用有权限的角色账号登录（admin、gm、pm、pmc）
2. 或者联系管理员分配相应的权限
3. 或者使用超级管理员账号绕过权限检查

### 6.4 数据库连接错误

**问题**: 后端启动时报数据库连接错误

**解决方案**:
```bash
# 检查数据库文件是否存在
ls -la data/app.db

# 如果数据库文件不存在，初始化数据库
python3 init_db.py

# 重新启动后端
cd /Users/flw/non-standard-automation-pm
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &
```

---

## 七、启动和停止脚本

### 7.1 启动后端

```bash
#!/bin/bash
# start_backend.sh

cd /Users/flw/non-standard-automation-pm

# 检查端口是否被占用
if lsof -i :8000 > /dev/null; then
    echo "端口8000已被占用，正在杀掉占用进程..."
    lsof -ti :8000 | xargs kill -9
    sleep 2
fi

# 启动后端
echo "启动后端服务..."
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > backend.log 2>&1 &

# 等待后端启动
sleep 5

# 检查后端状态
if lsof -i :8000 > /dev/null; then
    echo "✅ 后端服务已启动，监听端口8000"
    echo "📋 日志文件: backend.log"
else
    echo "❌ 后端服务启动失败，请查看日志"
fi
```

### 7.2 停止后端

```bash
#!/bin/bash
# stop_backend.sh

echo "停止后端服务..."
lsof -ti :8000 | xargs kill -9 2>/dev/null

sleep 2

if lsof -i :8000 > /dev/null; then
    echo "❌ 后端服务停止失败"
else
    echo "✅ 后端服务已停止"
fi
```

### 7.3 启动前端

```bash
#!/bin/bash
# start_frontend.sh

cd /Users/flw/non-standard-automation-pm/frontend

# 检查端口是否被占用
if lsof -i :3000 > /dev/null; then
    echo "端口3000已被占用，正在杀掉占用进程..."
    lsof -ti :3000 | xargs kill -9
    sleep 2
fi

# 启动前端
echo "启动前端服务..."
npm start &

# 等待前端启动
sleep 5

# 检查前端状态
if lsof -i :3000 > /dev/null; then
    echo "✅ 前端服务已启动，监听端口3000"
    echo "🌐 访问地址: http://localhost:3000"
else
    echo "❌ 前端服务启动失败"
fi
```

### 7.4 停止前端

```bash
#!/bin/bash
# stop_frontend.sh

echo "停止前端服务..."
lsof -ti :3000 | xargs kill -9 2>/dev/null

sleep 2

if lsof -i :3000 > /dev/null; then
    echo "❌ 前端服务停止失败"
else
    echo "✅ 前端服务已停止"
fi
```

---

## 八、测试新功能

### 8.1 测试进度预测

**步骤**:
1. 使用管理员账号登录（admin/admin123）
2. 访问项目详情页
3. 点击"进度预测"标签页
4. 查看预测数据和延迟任务
5. 配置自动处理选项
6. 点击"预览自动处理"
7. 查看预览对话框
8. 点击"执行自动处理"

**预期结果**:
- ✅ 能正常访问进度预测看板
- ✅ 能查看预测数据和延迟任务
- ✅ 能配置自动处理选项
- ✅ 能预览自动处理结果
- ✅ 能执行自动处理

### 8.2 测试依赖巡检

**步骤**:
1. 使用管理员账号登录（admin/admin123）
2. 访问项目详情页
3. 点击"依赖巡检"标签页
4. 查看依赖问题分类和详情
5. 配置自动修复选项
6. 点击"预览修复"
7. 查看预览对话框
8. 点击"执行修复"

**预期结果**:
- ✅ 能正常访问依赖巡检结果页面
- ✅ 能查看依赖问题分类和详情
- ✅ 能配置自动修复选项
- ✅ 能预览修复操作
- ✅ 能执行依赖修复

---

## 九、系统要求

### 9.1 后端要求

**Python版本**: 3.14+
**依赖包**:
- fastapi==0.128.0
- uvicorn==0.40.0
- pydantic==2.12.0
- pydantic-settings==2.8.0
- sqlalchemy==2.0+
- sqlite3 (内置)

**数据库**: SQLite (无需额外安装)

### 9.2 前端要求

**Node.js版本**: 18+
**依赖包**: 通过npm安装
**浏览器**: Chrome、Firefox、Safari最新版本

### 9.3 环境要求

**操作系统**: macOS、Linux、Windows
**网络**: 本地开发需要能访问localhost
**内存**: 至少4GB RAM
**磁盘**: 至少2GB可用空间

---

## 十、总结

### 10.1 当前运行状态

| 服务 | 状态 | 端口 | 访问地址 |
|-----|:----:|:----:|---------|
| **后端** | ✅ 运行中 | 8000 | http://localhost:8000 |
| **前端** | ✅ 运行中 | 3000 | http://localhost:3000 |
| **数据库** | ✅ 就绪 | - | data/app.db |

### 10.2 新功能状态

| 功能 | 状态 | 权限 | 访问地址 |
|-----|:----:|------|---------|
| **进度预测看板** | ✅ 可用 | 5个角色 | /projects/:id/progress-forecast |
| **依赖巡检结果** | ✅ 可用 | 5个角色 | /projects/:id/dependency-check |

### 10.3 快速访问

**前端**: http://localhost:3000
**后端API**: http://localhost:8000
**API文档**: http://localhost:8000/docs

---

**最后更新**: 2026-01-12
