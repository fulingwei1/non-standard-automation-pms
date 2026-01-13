# API 测试指南

本文档提供了多种测试API的方法。

## 快速开始

### 方法1: 使用Python测试脚本（推荐）

```bash
cd 非标自动化项目管理系统
python3 test_auth_apis.py
```

### 方法2: 使用Bash测试脚本

```bash
cd 非标自动化项目管理系统
bash test_auth_apis.sh
```

### 方法3: 使用快速测试脚本

```bash
cd 非标自动化项目管理系统
bash quick_test.sh
```

### 方法4: 运行验收模块端到端脚本

```bash
cd 非标自动化项目管理系统
python3 test_acceptance_workflow.py
```

该脚本会自动创建项目/机台/验收模板/验收单，串联“创建 → 启动 → 更新检查项 → 完成验收”全流程，并在结束时清理数据，可多次重复执行验证验收模块。
脚本还会检测失败项，自动创建/更新/关闭验收问题，并在验收完成后补充 QA/客户签字与验收报告生成（含下载接口校验），覆盖验收问题、签字与报告相关接口。

## 前置条件

### 1. 启动服务器

```bash
cd 非标自动化项目管理系统
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 2. 初始化数据库（如果还没有用户）

```bash
python3 init_db.py
```

### 3. 检查服务器状态

```bash
curl http://127.0.0.1:8000/health
```

应该返回：
```json
{"status": "ok", "version": "1.0.0"}
```

## 手动测试（curl）

### 1. 登录获取Token

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

保存Token：
```bash
TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

### 2. 使用Token测试其他API

```bash
# 获取当前用户信息
curl -X GET "http://127.0.0.1:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"

# 获取用户列表
curl -X GET "http://127.0.0.1:8000/api/v1/users?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"

# 获取角色列表
curl -X GET "http://127.0.0.1:8000/api/v1/roles?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

## Postman测试

### 1. 导入环境

创建新的Environment：
- `base_url`: `http://127.0.0.1:8000/api/v1`
- `token`: (登录后自动设置)

### 2. 设置Pre-request Script

在Collection的Pre-request Script中添加：
```javascript
if (pm.environment.get("token")) {
    pm.request.headers.add({
        key: "Authorization",
        value: "Bearer " + pm.environment.get("token")
    });
}
```

### 3. 登录并保存Token

在登录请求的Tests中添加：
```javascript
var jsonData = pm.response.json();
pm.environment.set("token", jsonData.access_token);
```

## API文档

访问以下地址查看完整的API文档：

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 测试文件说明

- `test_auth_apis.py` - Python测试脚本（推荐）
- `test_auth_apis.sh` - Bash完整测试脚本
- `quick_test.sh` - 快速测试脚本（只测试登录和基本信息）
- `test_auth_apis.md` - 详细的测试文档

## 常见问题

### 问题1: 服务器未运行
**错误**: `Connection refused` 或 `无法连接到服务器`

**解决**: 
```bash
cd 非标自动化项目管理系统
uvicorn app.main:app --reload
```

### 问题2: 登录失败
**错误**: `401 Unauthorized` 或 `用户名或密码错误`

**解决**: 
1. 检查数据库是否有用户
2. 运行 `python3 init_db.py` 初始化数据库
3. 确认用户名和密码正确

### 问题3: 权限不足
**错误**: `403 Forbidden` 或 `没有执行此操作的权限`

**解决**: 
1. 检查用户是否有相应权限
2. 确认用户角色已正确分配
3. 使用超级管理员账户测试

### 问题4: Token过期
**错误**: `401 Unauthorized` 或 `Token已失效`

**解决**: 
1. 重新登录获取新Token
2. 使用 `/auth/refresh` 刷新Token

## 测试检查清单

- [ ] 服务器已启动
- [ ] 数据库已初始化
- [ ] 有测试用户（默认: admin/admin123）
- [ ] 可以成功登录
- [ ] 可以获取当前用户信息
- [ ] 可以刷新Token
- [ ] 可以修改密码
- [ ] 可以获取用户列表
- [ ] 可以创建用户
- [ ] 可以更新用户
- [ ] 可以获取角色列表
- [ ] 可以创建角色
- [ ] 可以分配权限

## 下一步

测试完成后，可以：
1. 继续实现第二步：主数据管理API（客户、供应商、部门）
2. 集成到前端：实现登录页面和用户管理界面
3. 完善权限系统：初始化系统权限数据


