# 500错误排查指南

## 问题现象
前端访问权限管理或角色管理页面时，出现 "Request failed with status code 500" 错误。

## 快速检查清单

### 1. 后端服务状态
```bash
# 检查后端服务是否运行
curl http://localhost:8000/health

# 或访问API文档
open http://localhost:8000/docs
```

### 2. 后端日志
查看运行 `uvicorn app.main:app --reload` 的终端，查找：
- `ERROR` 级别的日志
- `获取权限列表失败` 或 `获取角色列表失败` 的错误信息
- 完整的错误堆栈

### 3. 数据库状态
```bash
# 运行诊断脚本
python3 scripts/diagnose_permissions_api.py
```

### 4. 前端请求
打开浏览器开发者工具（F12）：
- Network 标签 → 找到失败的请求
- 检查请求URL、请求头（特别是Authorization）
- 查看响应内容（Response标签）

## 常见原因和解决方案

### 原因1: 后端服务未重启
**症状**: 修改了代码但错误仍然存在

**解决**:
```bash
# 停止当前服务（Ctrl+C）
# 重新启动
uvicorn app.main:app --reload
```

### 原因2: 认证失败
**症状**: 后端日志显示 "无效的认证凭据" 或 "Token已失效"

**解决**:
1. 重新登录获取新token
2. 检查浏览器localStorage中的token是否过期
3. 清除浏览器缓存和localStorage，重新登录

### 原因3: 数据库连接问题
**症状**: 后端日志显示数据库连接错误

**解决**:
```bash
# 检查数据库文件是否存在
ls -la data/app.db

# 检查数据库权限
chmod 644 data/app.db
```

### 原因4: 其他模型关系错误
**症状**: 后端日志显示 "Could not determine join condition"

**解决**:
- 当前已使用SQL查询绕过此问题
- 如需使用ORM，需要修复相关模型的关系定义

### 原因5: 字段类型不匹配
**症状**: 后端日志显示序列化错误

**解决**:
- 已修复datetime字段转换
- 如果仍有问题，检查数据库中的实际数据类型

## 诊断命令

### 完整诊断
```bash
python3 scripts/diagnose_permissions_api.py
```

### 测试权限查询
```bash
python3 scripts/test_permissions_api_endpoint.py
```

### 测试认证流程
```bash
python3 scripts/test_permissions_endpoint_with_auth.py
```

## 获取详细错误信息

### 方法1: 查看后端日志
后端已添加详细日志，所有错误都会记录：
- `logger.info()` - 正常流程日志
- `logger.error()` - 错误日志（包含堆栈信息）

### 方法2: 使用curl测试API
```bash
# 1. 先登录获取token
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}' \
  | jq -r '.access_token')

# 2. 使用token访问权限列表
curl -X GET "http://localhost:8000/api/v1/roles/permissions" \
  -H "Authorization: Bearer $TOKEN" \
  -v
```

### 方法3: 使用Postman或类似工具
1. 先调用 `/api/v1/auth/login` 获取token
2. 使用token访问 `/api/v1/roles/permissions`
3. 查看响应状态码和错误信息

## 已修复的问题

✅ 数据库表结构已统一
✅ DateTime字段序列化已修复
✅ 认证流程已修复（JWT sub字段处理）
✅ ORM查询失败降级机制已添加
✅ 所有API端点已改用SQL查询

## 如果问题仍然存在

请提供以下信息：

1. **后端日志**（完整的错误堆栈）
2. **浏览器控制台错误**（Network标签中的请求详情）
3. **诊断脚本输出**（运行 `python3 scripts/diagnose_permissions_api.py` 的结果）
4. **后端服务状态**（是否正常运行，端口是否正确）

## 相关文件

- API端点: `app/api/v1/endpoints/roles.py`
- 认证逻辑: `app/core/security.py`
- 诊断脚本: `scripts/diagnose_permissions_api.py`
- 修复文档: `docs/ROLES_PERMISSIONS_API_FIX_SUMMARY.md`
