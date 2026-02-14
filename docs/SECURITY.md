# 安全配置文档

## 目录
- [概述](#概述)
- [CSRF防护](#csrf防护)
- [API认证机制](#api认证机制)
- [请求签名验证](#请求签名验证)
- [安全响应头](#安全响应头)
- [配置指南](#配置指南)
- [安全最佳实践](#安全最佳实践)

---

## 概述

本系统实现了多层安全防护机制，包括：

- **CSRF防护**：区分Web和API请求的智能CSRF防护
- **多种认证方式**：JWT、API Key、请求签名
- **安全响应头**：完善的HTTP安全头配置
- **速率限制**：防止暴力攻击和滥用
- **审计日志**：记录所有安全相关事件

---

## CSRF防护

### 原理

CSRF（跨站请求伪造）攻击利用用户已认证的会话执行非预期操作。本系统采用以下策略：

1. **API请求**（`/api/v1/*`）
   - 要求JWT Bearer Token认证
   - 验证Origin/Referer头
   - 支持CORS预检请求

2. **Web请求**（非API路径）
   - 验证Origin/Referer头
   - 可选的CSRF Token机制（未来扩展）

### 配置

#### 环境变量

```bash
# .env
DEBUG=false  # 生产环境必须设为false
CORS_ORIGINS='["https://your-domain.com","https://app.your-domain.com"]'
```

#### CSRF白名单

编辑 `app/core/csrf.py`：

```python
# 豁免CSRF检查的路径
EXEMPT_PATHS: Set[str] = {
    "/",
    "/health",
    "/docs",
    "/api/v1/auth/login",
}
```

### 工作流程

```
客户端请求
    │
    ├─ 是安全方法（GET/HEAD/OPTIONS）？
    │   └─ 是 → 放行
    │
    ├─ 是豁免路径？
    │   └─ 是 → 放行
    │
    ├─ 是API请求（/api/v1/*）？
    │   │
    │   ├─ 检查Bearer Token → 无 → 401
    │   ├─ 检查Origin/Referer → 无 → 403
    │   └─ 验证Origin是否在白名单 → 否 → 403
    │
    └─ 是Web请求
        └─ 验证Origin/Referer → 通过 → 放行
```

### API调用示例

#### JavaScript（Axios）

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://api.example.com/api/v1',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // 发送Cookie
});

// PUT请求示例
await api.put('/roles/1/permissions', {
  permission_ids: [1, 2, 3]
});
```

#### cURL

```bash
curl -X PUT 'https://api.example.com/api/v1/roles/1/permissions' \
  -H 'Authorization: Bearer eyJ0eXAiOiJKV1QiLC...' \
  -H 'Content-Type: application/json' \
  -H 'Origin: https://app.example.com' \
  -d '{"permission_ids": [1, 2, 3]}'
```

#### Python（Requests）

```python
import requests

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
    'Origin': 'https://app.example.com',
}

response = requests.put(
    'https://api.example.com/api/v1/roles/1/permissions',
    json={'permission_ids': [1, 2, 3]},
    headers=headers
)
```

---

## API认证机制

### 认证方式对比

| 方式 | 适用场景 | 安全性 | 实现复杂度 |
|------|----------|--------|------------|
| JWT | Web应用、移动应用 | 高 | 中 |
| API Key | 服务间调用、脚本 | 中 | 低 |
| 请求签名 | 高安全要求场景 | 极高 | 高 |

### 1. JWT认证（主要方式）

#### 登录获取Token

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}

# 响应
{
  "code": 200,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLC...",
    "token_type": "bearer"
  }
}
```

#### 使用Token

```bash
GET /api/v1/users/me
Authorization: Bearer eyJ0eXAiOiJKV1QiLC...
```

### 2. API Key认证（备选方案）

#### 生成API Key

```bash
POST /api/v1/api-keys
Authorization: Bearer {jwt_token}
Content-Type: application/json

{
  "name": "Production API Key",
  "scopes": ["projects:read", "projects:write"],
  "allowed_ips": ["192.168.1.100"],
  "expires_at": "2025-12-31T23:59:59Z"
}

# 响应
{
  "code": 201,
  "data": {
    "api_key": "pms_AbCdEf123456...",  # 只显示一次，请保存
    "id": 1,
    "name": "Production API Key"
  }
}
```

#### 使用API Key

```bash
GET /api/v1/projects
X-API-Key: pms_AbCdEf123456...
```

#### 权限范围（Scopes）

- `admin`: 完全权限
- `projects:read`: 读取项目
- `projects:write`: 创建/更新项目
- `users:read`: 读取用户
- `users:write`: 创建/更新用户

#### 安全特性

- **哈希存储**：API Key使用SHA256哈希存储，数据库泄露也无法恢复原始值
- **IP白名单**：限制允许的客户端IP
- **过期时间**：自动失效
- **速率限制**：防止滥用
- **审计日志**：记录所有使用

---

## 请求签名验证

### 原理

使用HMAC-SHA256签名请求，防止篡改和重放攻击。

### 签名算法

```
1. 构建签名字符串：
   signature_string = "{method}\n{path}\n{timestamp}\n{body_hash}"
   
2. 计算HMAC-SHA256：
   signature = HMAC-SHA256(secret_key, signature_string)
   
3. Base64编码：
   encoded_signature = Base64(signature)
```

### Python客户端示例

```python
import hashlib
import hmac
import base64
import time
import requests

def sign_request(method, url, body, secret):
    """生成请求签名"""
    from urllib.parse import urlparse
    
    # 解析URL
    parsed = urlparse(url)
    path = parsed.path
    if parsed.query:
        path += f"?{parsed.query}"
    
    # 生成时间戳（毫秒）
    timestamp = str(int(time.time() * 1000))
    
    # 计算body哈希
    body_hash = hashlib.sha256(body).hexdigest()
    
    # 构建签名字符串
    signature_string = f"{method}\n{path}\n{timestamp}\n{body_hash}"
    
    # 计算HMAC-SHA256签名
    signature_bytes = hmac.new(
        secret.encode('utf-8'),
        signature_string.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    # Base64编码
    signature = base64.b64encode(signature_bytes).decode('utf-8')
    
    return signature, timestamp

# 使用示例
secret_key = "your-secret-key"
method = "POST"
url = "https://api.example.com/api/v1/projects"
body = b'{"name":"Test Project"}'

signature, timestamp = sign_request(method, url, body, secret_key)

headers = {
    'X-Signature': signature,
    'X-Timestamp': timestamp,
    'Content-Type': 'application/json',
}

response = requests.post(url, data=body, headers=headers)
```

### JavaScript客户端示例

```javascript
const crypto = require('crypto');

async function signRequest(method, url, body, secret) {
  // 解析URL
  const urlObj = new URL(url);
  let path = urlObj.pathname;
  if (urlObj.search) {
    path += urlObj.search;
  }
  
  // 生成时间戳（毫秒）
  const timestamp = Date.now().toString();
  
  // 计算body哈希
  const bodyHash = crypto
    .createHash('sha256')
    .update(body)
    .digest('hex');
  
  // 构建签名字符串
  const signatureString = `${method}\n${path}\n${timestamp}\n${bodyHash}`;
  
  // 计算HMAC-SHA256签名
  const signature = crypto
    .createHmac('sha256', secret)
    .update(signatureString)
    .digest('base64');
  
  return { signature, timestamp };
}

// 使用示例
const secretKey = 'your-secret-key';
const method = 'POST';
const url = 'https://api.example.com/api/v1/projects';
const body = JSON.stringify({ name: 'Test Project' });

const { signature, timestamp } = await signRequest(method, url, body, secretKey);

const response = await fetch(url, {
  method: method,
  headers: {
    'X-Signature': signature,
    'X-Timestamp': timestamp,
    'Content-Type': 'application/json',
  },
  body: body,
});
```

### 安全特性

- **时间窗口验证**：签名有效期5分钟，防止重放攻击
- **请求完整性**：body哈希确保请求未被篡改
- **恒定时间比较**：防止时序攻击

---

## 安全响应头

### 完整头部列表

| 响应头 | 值 | 作用 |
|--------|-----|------|
| X-Frame-Options | DENY | 防止点击劫持 |
| X-Content-Type-Options | nosniff | 防止MIME类型混淆 |
| X-XSS-Protection | 1; mode=block | 启用XSS过滤器 |
| Content-Security-Policy | (见下文) | 内容安全策略 |
| Referrer-Policy | strict-origin-when-cross-origin | 限制Referer泄露 |
| Permissions-Policy | (见下文) | 禁用不必要的浏览器功能 |
| Strict-Transport-Security | max-age=31536000; includeSubDomains; preload | 强制HTTPS（生产） |
| Server | PMS | 隐藏服务器信息 |

### Content-Security-Policy（CSP）

#### 生产环境（严格）

```
default-src 'self';
script-src 'self' 'nonce-{random}';
style-src 'self' 'nonce-{random}';
img-src 'self' data: https:;
font-src 'self' data:;
connect-src 'self' {cors_origins};
frame-ancestors 'none';
form-action 'self';
base-uri 'self';
object-src 'none';
upgrade-insecure-requests;
```

#### 开发环境（宽松）

```
default-src 'self';
script-src 'self' 'unsafe-inline' 'unsafe-eval';
style-src 'self' 'unsafe-inline';
img-src 'self' data: https: blob:;
connect-src 'self' ws://localhost:* wss://localhost:*;
```

### Permissions-Policy

禁用的浏览器功能：
- 地理位置 (geolocation)
- 麦克风 (microphone)
- 摄像头 (camera)
- 支付 (payment)
- USB设备 (usb)
- 传感器 (magnetometer, gyroscope, accelerometer)

---

## 配置指南

### 1. 环境变量配置

创建 `.env` 文件：

```bash
# 应用配置
APP_NAME="非标自动化项目管理系统"
DEBUG=false

# 数据库
DATABASE_URL=sqlite:///data/app.db

# 安全配置
SECRET_KEY=your-secret-key-here  # 使用: python -c 'import secrets; print(secrets.token_urlsafe(32))'
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24小时

# CORS配置（重要！）
CORS_ORIGINS='["https://app.example.com","https://admin.example.com"]'

# Redis（可选，用于缓存和速率限制）
REDIS_URL=redis://localhost:6379/0
```

### 2. 生产环境部署检查清单

#### 必须配置项

- [ ] `DEBUG=false` - 禁用调试模式
- [ ] `SECRET_KEY` - 设置强随机密钥
- [ ] `CORS_ORIGINS` - 严格限制允许的来源
- [ ] 配置HTTPS（Nginx/Caddy）
- [ ] 启用防火墙，只开放必要端口

#### 推荐配置项

- [ ] 配置Redis（速率限制和缓存）
- [ ] 设置日志轮转
- [ ] 配置备份策略
- [ ] 监控和告警
- [ ] WAF（Web Application Firewall）

### 3. Nginx配置示例

```nginx
server {
    listen 443 ssl http2;
    server_name api.example.com;

    # SSL证书
    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 安全头（备份，应用已设置）
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # 限制请求大小
    client_max_body_size 10M;

    # 速率限制
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 安全最佳实践

### 1. 密钥管理

```bash
# 生成强随机密钥
python -c 'import secrets; print(secrets.token_urlsafe(32))'

# 存储在环境变量或密钥管理服务（如AWS Secrets Manager）
export SECRET_KEY="your-generated-key"
```

### 2. API Key管理

- 使用有意义的名称标识API Key
- 设置合理的过期时间
- 定期轮换API Key
- 限制权限范围（最小权限原则）
- 监控使用情况

### 3. CORS配置

```python
# ❌ 不安全（生产环境禁止）
CORS_ORIGINS = ["*"]

# ✅ 安全（明确列出允许的域名）
CORS_ORIGINS = [
    "https://app.example.com",
    "https://admin.example.com"
]
```

### 4. 错误处理

- 不在错误消息中泄露敏感信息
- 使用统一的错误响应格式
- 记录详细错误到日志（不返回给客户端）

```python
# ❌ 不安全
raise HTTPException(detail=f"Database error: {str(db_error)}")

# ✅ 安全
logger.error(f"Database error: {str(db_error)}")
raise HTTPException(detail="Internal server error")
```

### 5. 日志和监控

- 记录所有认证失败
- 记录所有CSRF验证失败
- 记录异常的API使用模式
- 设置告警阈值

### 6. 定期安全审计

- [ ] 每月检查依赖包更新
- [ ] 每季度进行安全扫描
- [ ] 每年进行渗透测试
- [ ] 定期审查访问日志

---

## 故障排查

### CSRF验证失败

#### 问题：403 Forbidden - CSRF验证失败

**可能原因：**

1. 缺少Origin/Referer头
2. Origin不在CORS_ORIGINS白名单中
3. 缺少Authorization头

**解决方案：**

```bash
# 1. 检查请求头
curl -v https://api.example.com/api/v1/roles/1/permissions

# 2. 添加必要的头
curl -X PUT 'https://api.example.com/api/v1/roles/1/permissions' \
  -H 'Authorization: Bearer your-token' \
  -H 'Origin: https://app.example.com' \
  -H 'Content-Type: application/json' \
  -d '{"permission_ids": [1, 2, 3]}'

# 3. 检查CORS配置
# 编辑 .env
CORS_ORIGINS='["https://app.example.com"]'
```

### API Key认证失败

#### 问题：401 Unauthorized - Invalid API Key

**可能原因：**

1. API Key已过期
2. API Key已被删除或禁用
3. IP不在白名单中
4. API Key格式错误

**解决方案：**

```python
# 检查API Key详情
GET /api/v1/api-keys/{id}
Authorization: Bearer {jwt_token}

# 重新生成API Key
POST /api/v1/api-keys
Authorization: Bearer {jwt_token}
```

---

## 附录

### 相关RFC和标准

- [RFC 6265](https://tools.ietf.org/html/rfc6265) - HTTP Cookie
- [RFC 6750](https://tools.ietf.org/html/rfc6750) - OAuth 2.0 Bearer Token
- [RFC 7519](https://tools.ietf.org/html/rfc7519) - JSON Web Token (JWT)
- [OWASP CSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP Secure Headers Project](https://owasp.org/www-project-secure-headers/)

### 工具推荐

- [OWASP ZAP](https://www.zaproxy.org/) - 安全扫描工具
- [Burp Suite](https://portswigger.net/burp) - 渗透测试工具
- [Mozilla Observatory](https://observatory.mozilla.org/) - HTTP安全头检查
- [SSL Labs](https://www.ssllabs.com/ssltest/) - SSL/TLS配置检查

---

**更新日期**: 2026-02-14  
**版本**: 1.0.0  
**维护者**: Security Team
