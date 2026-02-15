# 账户锁定机制 API 文档

## 概述

账户锁定机制提供了完整的API接口，用于管理被锁定的账户、查看登录历史和管理IP黑名单。

**基础路径**: `/api/v1/admin/account-lockout`

**认证**: 所有API都需要管理员权限（Bearer Token）

## API 列表

### 1. 查看锁定账户列表

查询当前所有被锁定的账户。

**请求**:
```http
GET /api/v1/admin/account-lockout/locked-accounts
Authorization: Bearer {admin_token}
```

**响应**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "locked_accounts": [
      {
        "username": "john.doe",
        "locked_until": "2026-02-15T15:30:00",
        "attempts": 5
      },
      {
        "username": "jane.smith",
        "locked_until": "2026-02-15T15:45:00",
        "attempts": 6
      }
    ],
    "total": 2
  }
}
```

**字段说明**:
- `username`: 被锁定的用户名
- `locked_until`: 锁定截止时间（ISO 8601格式）
- `attempts`: 失败尝试次数

**错误码**:
- `403`: 需要管理员权限
- `500`: 服务器内部错误

---

### 2. 手动解锁账户

管理员可以手动解锁被锁定的账户。

**请求**:
```http
POST /api/v1/admin/account-lockout/unlock
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "username": "john.doe"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "账户 john.doe 已成功解锁"
}
```

**错误响应**:
```json
{
  "code": 400,
  "message": "解锁失败，账户可能未被锁定或Redis不可用"
}
```

**错误码**:
- `400`: 解锁失败（账户未锁定或系统错误）
- `403`: 需要管理员权限
- `500`: 服务器内部错误

**副作用**:
- 清除失败次数计数器
- 删除锁定状态
- 记录审计日志（包含管理员信息）

---

### 3. 查看登录历史

查询指定用户的登录历史记录。

**请求**:
```http
POST /api/v1/admin/account-lockout/login-history
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "username": "john.doe",
  "limit": 50
}
```

**参数**:
- `username` (必填): 要查询的用户名
- `limit` (可选): 返回记录数，默认50，范围1-500

**响应**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "history": [
      {
        "id": 12345,
        "username": "john.doe",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "success": false,
        "failure_reason": "wrong_password",
        "locked": true,
        "created_at": "2026-02-15T14:15:23"
      },
      {
        "id": 12344,
        "username": "john.doe",
        "ip_address": "192.168.1.100",
        "user_agent": "Mozilla/5.0...",
        "success": true,
        "failure_reason": null,
        "locked": false,
        "created_at": "2026-02-15T09:00:12"
      }
    ],
    "total": 2
  }
}
```

**字段说明**:
- `success`: 是否成功登录
- `failure_reason`: 失败原因
  - `wrong_password`: 密码错误
  - `user_not_found`: 用户不存在
  - `account_locked`: 账户已锁定
  - `account_inactive`: 账户未激活
- `locked`: 此次尝试后是否导致账户锁定

**错误码**:
- `403`: 需要管理员权限
- `500`: 查询失败

---

### 4. 查看IP黑名单

获取当前所有被拉黑的IP地址。

**请求**:
```http
GET /api/v1/admin/account-lockout/ip-blacklist
Authorization: Bearer {admin_token}
```

**响应**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "blacklisted_ips": [
      {
        "ip": "203.0.113.45",
        "created_at": null
      },
      {
        "ip": "198.51.100.88",
        "created_at": null
      }
    ],
    "total": 2
  }
}
```

**注意**: `created_at`字段当前为null（Redis不存储时间戳），未来版本可能改进。

**错误码**:
- `403`: 需要管理员权限
- `500`: 查询失败

---

### 5. 移除IP黑名单

从黑名单中移除指定IP地址。

**请求**:
```http
POST /api/v1/admin/account-lockout/remove-ip-blacklist
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "ip": "203.0.113.45"
}
```

**响应**:
```json
{
  "code": 200,
  "message": "IP 203.0.113.45 已从黑名单移除"
}
```

**错误响应**:
```json
{
  "code": 400,
  "message": "移除失败，Redis不可用"
}
```

**错误码**:
- `400`: 移除失败
- `403`: 需要管理员权限
- `500`: 服务器内部错误

**副作用**:
- 删除IP黑名单标记
- 清除IP失败次数计数器
- 记录审计日志（包含管理员信息）

---

### 6. 查询账户锁定状态

检查指定账户的锁定状态和失败尝试次数。

**请求**:
```http
GET /api/v1/admin/account-lockout/lockout-status/{username}
Authorization: Bearer {admin_token}
```

**示例**:
```http
GET /api/v1/admin/account-lockout/lockout-status/john.doe
```

**响应（未锁定）**:
```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "locked": false,
    "locked_until": null,
    "remaining_attempts": 3,
    "requires_captcha": true,
    "message": "剩余尝试次数: 3"
  }
}
```

**响应（已锁定）**:
```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "locked": true,
    "locked_until": "2026-02-15T15:30:00",
    "remaining_attempts": 0,
    "requires_captcha": false,
    "message": "账户已锁定，请在15:30后重试"
  }
}
```

**字段说明**:
- `locked`: 是否被锁定
- `locked_until`: 锁定截止时间（如果locked=true）
- `remaining_attempts`: 剩余尝试次数
- `requires_captcha`: 是否需要验证码（失败次数≥3）

**错误码**:
- `403`: 需要管理员权限
- `500`: 查询失败

---

## 公共错误码

所有API可能返回的公共错误：

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```
**原因**: Token缺失或无效

### 403 Forbidden
```json
{
  "detail": "需要管理员权限"
}
```
**原因**: 当前用户不是管理员

### 429 Too Many Requests
```json
{
  "detail": "请求过于频繁，请稍后再试"
}
```
**原因**: 触发速率限制

### 500 Internal Server Error
```json
{
  "code": 500,
  "message": "服务器内部错误"
}
```
**原因**: 服务器异常

---

## 使用示例

### Python (requests)

```python
import requests

API_BASE = "http://your-domain/api/v1/admin/account-lockout"
ADMIN_TOKEN = "your_admin_token"

headers = {
    "Authorization": f"Bearer {ADMIN_TOKEN}",
    "Content-Type": "application/json"
}

# 1. 查看锁定账户
response = requests.get(f"{API_BASE}/locked-accounts", headers=headers)
print(response.json())

# 2. 解锁账户
response = requests.post(
    f"{API_BASE}/unlock",
    headers=headers,
    json={"username": "john.doe"}
)
print(response.json())

# 3. 查看登录历史
response = requests.post(
    f"{API_BASE}/login-history",
    headers=headers,
    json={"username": "john.doe", "limit": 20}
)
print(response.json())
```

### cURL

```bash
# 设置变量
API_BASE="http://your-domain/api/v1/admin/account-lockout"
TOKEN="your_admin_token"

# 1. 查看锁定账户
curl -X GET "${API_BASE}/locked-accounts" \
  -H "Authorization: Bearer ${TOKEN}"

# 2. 解锁账户
curl -X POST "${API_BASE}/unlock" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"username": "john.doe"}'

# 3. 查看IP黑名单
curl -X GET "${API_BASE}/ip-blacklist" \
  -H "Authorization: Bearer ${TOKEN}"

# 4. 移除IP黑名单
curl -X POST "${API_BASE}/remove-ip-blacklist" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"ip": "203.0.113.45"}'

# 5. 查询锁定状态
curl -X GET "${API_BASE}/lockout-status/john.doe" \
  -H "Authorization: Bearer ${TOKEN}"
```

### JavaScript (Fetch)

```javascript
const API_BASE = 'http://your-domain/api/v1/admin/account-lockout';
const ADMIN_TOKEN = 'your_admin_token';

const headers = {
  'Authorization': `Bearer ${ADMIN_TOKEN}`,
  'Content-Type': 'application/json'
};

// 1. 查看锁定账户
fetch(`${API_BASE}/locked-accounts`, { headers })
  .then(res => res.json())
  .then(data => console.log(data));

// 2. 解锁账户
fetch(`${API_BASE}/unlock`, {
  method: 'POST',
  headers,
  body: JSON.stringify({ username: 'john.doe' })
})
  .then(res => res.json())
  .then(data => console.log(data));
```

---

## 速率限制

为防止API滥用，管理接口有以下速率限制：

- **查询接口** (GET): 60次/分钟
- **操作接口** (POST): 20次/分钟

超过限制会返回 `429 Too Many Requests`。

---

## 变更日志

### v1.0 (2026-02-15)
- 初始版本
- 支持基本的锁定/解锁操作
- 支持IP黑名单管理
- 支持登录历史查询

### 计划功能 (v1.1)
- [ ] 验证码集成
- [ ] 白名单IP配置
- [ ] 批量操作接口
- [ ] WebSocket实时通知
- [ ] 更详细的统计报表

---

**最后更新**: 2026年2月15日  
**版本**: v1.0  
**维护者**: 系统安全团队
