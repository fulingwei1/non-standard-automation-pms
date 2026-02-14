# 安全配置快速启动指南

## 🎯 概述

本指南帮助你快速配置和理解系统的安全机制。

## ✅ 已实现的安全功能

### 1. CSRF防护 ✓
- ✅ 智能区分API和Web请求
- ✅ Origin/Referer验证
- ✅ 白名单配置
- ✅ OPTIONS预检支持
- ✅ DEBUG模式宽松验证

### 2. API认证 ✓
- ✅ JWT Bearer Token（主要）
- ✅ API Key认证（备选）
- ✅ 请求签名验证（高安全）

### 3. 安全响应头 ✓
- ✅ X-Frame-Options（防点击劫持）
- ✅ X-Content-Type-Options（防MIME混淆）
- ✅ Content-Security-Policy（内容安全策略）
- ✅ Strict-Transport-Security（强制HTTPS）
- ✅ Permissions-Policy（权限策略）
- ✅ 完整的跨域安全头

### 4. 测试覆盖 ✓
- ✅ 67+个安全测试
- ✅ CSRF防护测试（14个）
- ✅ API Key测试（11个）
- ✅ 请求签名测试（12个）
- ✅ 安全头测试（20个）
- ✅ 集成测试（10个）

## 🚀 5分钟快速启动

### 步骤1：配置环境变量

创建或编辑 `.env` 文件：

```bash
# 基本配置
DEBUG=false                    # 生产环境必须false
SECRET_KEY=your-secret-key     # 使用下方命令生成

# CORS配置（重要！）
CORS_ORIGINS='["https://your-domain.com"]'

# 数据库
DATABASE_URL=sqlite:///data/app.db
```

生成安全密钥：
```bash
python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

### 步骤2：测试CSRF防护

```bash
# 运行CSRF测试
pytest tests/security/test_csrf_protection.py -v

# 预期结果：14 passed
```

### 步骤3：测试API请求

使用curl测试：

```bash
# 1. 登录获取Token
TOKEN=$(curl -X POST 'http://localhost:8000/api/v1/auth/login' \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"admin"}' \
  | jq -r '.data.access_token')

# 2. 测试PUT请求（修复前会失败）
curl -X PUT 'http://localhost:8000/api/v1/roles/1/permissions' \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -H 'Origin: http://localhost:3000' \
  -d '{"permission_ids": [1, 2, 3]}'

# 预期结果：200 OK（如果有权限）或404（如果角色不存在）
# 不应该是403 CSRF错误
```

### 步骤4：检查安全头

```bash
# 测试安全响应头
curl -I http://localhost:8000/health

# 预期看到：
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# Content-Security-Policy: ...
# Permissions-Policy: ...
```

### 步骤5：运行所有安全测试

```bash
# 运行完整测试套件
pytest tests/security/ -v --cov=app.core

# 预期结果：67+ passed
# 覆盖率：> 85%
```

## 📋 配置检查清单

### 开发环境

- [x] `DEBUG=true`
- [x] `CORS_ORIGINS` 包含 `http://localhost:3000`
- [x] `SECRET_KEY` 可以自动生成
- [ ] 安全头宽松（允许unsafe-inline）
- [ ] CSRF验证宽松

### 生产环境（必须）

- [ ] `DEBUG=false`
- [ ] `SECRET_KEY` 从环境变量设置（强随机）
- [ ] `CORS_ORIGINS` 只包含信任的域名（移除`*`）
- [ ] 启用HTTPS
- [ ] 配置防火墙
- [ ] 启用日志和监控

## 🔒 安全机制说明

### CSRF防护工作流程

```
客户端发起PUT请求
    ↓
检查HTTP方法（GET/HEAD/OPTIONS）？
    ├─ 是 → 放行
    └─ 否 → 继续
    ↓
检查是否豁免路径（/health等）？
    ├─ 是 → 放行
    └─ 否 → 继续
    ↓
检查是否API请求（/api/v1/*）？
    ├─ 是 → 验证Bearer Token + Origin
    └─ 否 → 验证Origin/Referer
    ↓
通过验证 → 执行业务逻辑
```

### PUT请求修复说明

**修复前的问题：**
```
PUT /api/v1/roles/1/permissions
→ 403 Forbidden（CSRF验证失败）
```

**修复后：**
```
PUT /api/v1/roles/1/permissions
Headers:
  - Authorization: Bearer {token}  ✓
  - Origin: https://allowed.com     ✓
→ 200 OK（CSRF验证通过）
```

**关键改进：**
1. 区分API请求和Web请求
2. API请求使用JWT认证（CSRF风险低）
3. 验证Origin而非强制CSRF Token
4. 支持CORS预检请求

## 📚 常见场景

### 场景1：前端调用API

```javascript
// Axios配置
const api = axios.create({
  baseURL: 'https://api.example.com/api/v1',
  headers: {
    'Authorization': `Bearer ${token}`,
  },
  withCredentials: true,  // 发送Cookie
});

// PUT请求
await api.put('/roles/1/permissions', {
  permission_ids: [1, 2, 3]
});
```

### 场景2：服务间调用（使用API Key）

```python
import requests

headers = {
    'X-API-Key': 'pms_your_api_key_here',
    'Content-Type': 'application/json',
}

response = requests.get(
    'https://api.example.com/api/v1/projects',
    headers=headers
)
```

### 场景3：高安全场景（使用请求签名）

```python
from app.core.request_signature import generate_client_signature

method = 'POST'
url = 'https://api.example.com/api/v1/projects'
body = b'{"name":"test"}'
secret = 'your-secret-key'

signature, timestamp = generate_client_signature(
    method, url, body, secret
)

headers = {
    'X-Signature': signature,
    'X-Timestamp': timestamp,
    'Content-Type': 'application/json',
}

response = requests.post(url, data=body, headers=headers)
```

## ⚠️ 常见错误和解决方案

### 错误1：403 CSRF验证失败

```
{
  "detail": "CSRF验证失败：缺少Origin或Referer头"
}
```

**解决方案：**
- 确保请求包含 `Origin` 或 `Referer` 头
- 确认Origin在 `CORS_ORIGINS` 白名单中
- 检查是否设置了 `DEBUG=false`

### 错误2：401 需要JWT认证

```
{
  "detail": "需要JWT认证"
}
```

**解决方案：**
- 添加 `Authorization: Bearer {token}` 头
- 确保token未过期
- 检查SECRET_KEY是否正确

### 错误3：OPTIONS预检失败

```
Access to XMLHttpRequest has been blocked by CORS policy
```

**解决方案：**
- 确认`CORS_ORIGINS`包含前端域名
- 检查main.py中的CORS配置
- 确保服务器支持OPTIONS方法

## 📊 安全测试报告

运行测试并生成报告：

```bash
# HTML覆盖率报告
pytest tests/security/ -v \
  --cov=app.core \
  --cov-report=html

# 查看报告
open htmlcov/index.html
```

**预期覆盖率：**
- `app/core/csrf.py`: > 90%
- `app/core/api_key_auth.py`: > 85%
- `app/core/request_signature.py`: > 90%
- `app/core/security_headers.py`: > 95%

## 🔧 维护和监控

### 日常检查

```bash
# 1. 检查依赖漏洞
pip install safety
safety check

# 2. 代码安全扫描
pip install bandit
bandit -r app/core/ -ll

# 3. 运行安全测试
pytest tests/security/ -v
```

### 监控指标

在生产环境监控以下指标：

- CSRF验证失败次数
- 401/403错误率
- API Key使用统计
- 异常请求模式
- 响应头合规性

### 日志记录

安全相关日志会记录在：
- `logs/security.log` - 安全事件
- `logs/audit.log` - 审计日志
- `logs/app.log` - 应用日志

## 📖 进一步阅读

- [完整安全配置文档](./SECURITY.md)
- [安全测试指南](../tests/security/README.md)
- [API文档](./API.md)
- [OWASP CSRF防护指南](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)

## 🆘 获取帮助

- GitHub Issues: [项目地址]/issues
- 安全问题: security@example.com
- 技术支持: support@example.com

---

**最后更新**: 2026-02-14  
**版本**: 1.0.0
