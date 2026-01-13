# "Not authenticated" 错误修复指南

## 问题描述

访问权限管理页面时出现 "加载权限列表失败: Not authenticated" 错误。

## 错误原因

"Not authenticated" 错误来自 FastAPI 的 `OAuth2PasswordBearer`，当请求中**没有 Authorization header** 时会抛出此错误。

## 可能的原因

1. **localStorage 中没有 token**
   - 用户未登录或 token 已过期
   - token 被意外清除

2. **前端没有正确发送 token**
   - 请求拦截器未正确添加 Authorization header
   - token 格式不正确

3. **token 是演示账号 token**
   - 演示账号 token（`demo_token_*`）不会发送到后端

## 诊断步骤

### 1. 检查浏览器 localStorage

打开浏览器开发者工具（F12）：
```javascript
// 在 Console 中执行
console.log('Token:', localStorage.getItem('token'));
console.log('User:', localStorage.getItem('user'));
```

**如果 token 不存在**：
- 需要重新登录
- 检查登录流程是否正常

**如果 token 存在但以 `demo_token_` 开头**：
- 这是演示账号 token，不会发送到后端
- 需要使用真实账号登录

### 2. 检查网络请求

在浏览器开发者工具的 Network 标签中：
1. 找到失败的请求（通常是 `/api/v1/roles/permissions`）
2. 查看 Request Headers
3. 检查是否有 `Authorization: Bearer <token>` header

**如果没有 Authorization header**：
- 检查前端请求拦截器是否正常工作
- 检查 token 是否被正确读取

### 3. 检查后端日志

查看后端服务终端日志：
- 查找 "收到认证请求" 的日志
- 如果没有任何日志，说明请求根本没有到达后端认证逻辑

## 已实施的修复

### 1. 前端增强错误处理

在 `PermissionManagement.jsx` 中：
- 添加了 token 存在性检查
- 改进了错误提示信息
- 认证失败时自动跳转到登录页

### 2. 前端请求拦截器增强

在 `api.js` 中：
- 添加了调试日志（开发环境）
- 添加了 token 缺失警告

### 3. 后端认证日志

在 `security.py` 中：
- 添加了认证请求的调试日志

## 解决方案

### 方案1: 重新登录

如果 token 不存在或已过期：
1. 清除浏览器 localStorage
2. 重新登录获取新 token

### 方案2: 检查 token 格式

确保 token 是有效的 JWT token：
```javascript
// 在浏览器 Console 中检查
const token = localStorage.getItem('token');
if (token && !token.startsWith('demo_token_')) {
  console.log('Token 格式:', token.substring(0, 50) + '...');
  // JWT token 通常包含三个部分，用 . 分隔
  const parts = token.split('.');
  console.log('Token 部分数:', parts.length); // 应该是 3
}
```

### 方案3: 手动测试 API

使用 curl 或 Postman 测试：
```bash
# 1. 先登录获取 token
TOKEN=$(curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=your_password" \
  | jq -r '.access_token')

# 2. 使用 token 访问权限列表
curl -X GET "http://localhost:8000/api/v1/roles/permissions" \
  -H "Authorization: Bearer $TOKEN"
```

## 常见问题

### Q: 为什么演示账号会显示 "Not authenticated"？

A: 演示账号的 token（`demo_token_*`）不会发送到后端，这是设计如此。演示账号应该使用 mock 数据。

### Q: 登录后立即访问权限管理页面还是失败？

A: 可能的原因：
1. 登录响应格式不正确，token 没有正确保存
2. 请求拦截器在 token 保存之前就执行了
3. 需要刷新页面或等待 token 保存完成

### Q: 如何确认 token 是否正确发送？

A: 在浏览器开发者工具的 Network 标签中：
1. 找到权限列表的请求
2. 查看 Request Headers
3. 确认有 `Authorization: Bearer <token>` header

## 调试工具

运行诊断脚本：
```bash
python3 scripts/test_auth_token.py
```

这个脚本会：
1. 尝试登录
2. 使用获取的 token 访问权限列表
3. 显示详细的错误信息

## 相关文件

- 前端权限管理页面: `frontend/src/pages/PermissionManagement.jsx`
- 前端 API 服务: `frontend/src/services/api.js`
- 后端认证逻辑: `app/core/security.py`
- 后端权限 API: `app/api/v1/endpoints/roles.py`
