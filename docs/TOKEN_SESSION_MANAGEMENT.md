# Token刷新和会话管理系统

## 概述

本系统实现了完善的Token刷新和会话管理机制，支持：

- **双Token机制**：Access Token（短期）+ Refresh Token（长期）
- **会话管理**：多设备登录追踪、会话查看、强制下线
- **安全增强**：设备绑定、异地登录检测、Token黑名单
- **滑动窗口刷新**：防止Token重放攻击

## 架构设计

### Token类型

#### Access Token
- **有效期**：24小时
- **用途**：访问API资源
- **包含字段**：
  - `sub`: 用户ID
  - `exp`: 过期时间
  - `iat`: 签发时间
  - `jti`: JWT ID（唯一标识）
  - `token_type`: "access"

#### Refresh Token
- **有效期**：7天
- **用途**：刷新Access Token
- **包含字段**：
  - `sub`: 用户ID
  - `exp`: 过期时间
  - `iat`: 签发时间
  - `jti`: JWT ID（唯一标识）
  - `token_type`: "refresh"

### 会话模型

```python
class UserSession:
    - user_id: 用户ID
    - access_token_jti: Access Token JTI
    - refresh_token_jti: Refresh Token JTI
    - device_id: 设备唯一标识
    - device_name: 设备名称
    - device_type: 设备类型
    - ip_address: 登录IP
    - location: 地理位置
    - user_agent: 浏览器User-Agent
    - is_active: 会话是否活跃
    - login_at: 登录时间
    - last_activity_at: 最后活动时间
    - expires_at: 会话过期时间
    - is_suspicious: 是否可疑登录
    - risk_score: 风险评分（0-100）
```

## API接口

### 1. 登录

**请求**
```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

**响应**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400,
  "refresh_expires_in": 604800
}
```

### 2. 刷新Token

**请求**
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJ...",
  "device_info": {
    "device_id": "uuid-here",
    "device_name": "Chrome on Windows",
    "device_type": "desktop"
  }
}
```

**响应**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

### 3. 登出

**单设备登出**
```http
POST /api/v1/auth/logout
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "logout_all": false
}
```

**所有设备登出**
```http
POST /api/v1/auth/logout
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "logout_all": true
}
```

### 4. 查看会话列表

**请求**
```http
GET /api/v1/auth/sessions
Authorization: Bearer {access_token}
```

**响应**
```json
{
  "sessions": [
    {
      "id": 1,
      "device_name": "Chrome on Windows",
      "device_type": "desktop",
      "ip_address": "192.168.1.100",
      "location": "北京",
      "browser": "Chrome 91.0",
      "os": "Windows 10",
      "login_at": "2026-02-14T10:00:00",
      "last_activity_at": "2026-02-14T12:00:00",
      "is_active": true,
      "is_current": true,
      "is_suspicious": false,
      "risk_score": 0
    }
  ],
  "total": 1,
  "active_count": 1
}
```

### 5. 强制下线指定设备

**请求**
```http
POST /api/v1/auth/sessions/revoke
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "session_id": 123
}
```

### 6. 强制下线所有其他设备

**请求**
```http
POST /api/v1/auth/sessions/revoke-all
Authorization: Bearer {access_token}
```

## 安全特性

### 1. Token黑名单

- **存储方式**：优先使用Redis，降级到内存
- **键格式**：`jwt:blacklist:{jti}`
- **过期时间**：与原Token相同
- **触发场景**：
  - 用户登出
  - 密码修改
  - 会话撤销
  - Token刷新（旧Access Token）

### 2. 会话限制

- **最大会话数**：每用户5个活跃会话
- **自动清理**：超过限制时关闭最旧的会话
- **会话过期**：7天无活动自动失效

### 3. 异地登录检测

系统会根据以下因素评估登录风险：

| 检测项 | 风险分值 | 说明 |
|--------|---------|------|
| 新IP地址 | +30 | 历史未使用过的IP |
| 新设备 | +20 | 历史未使用过的设备ID |
| 异地登录 | +25 | 与历史位置不同 |
| 频繁登录 | +25 | 1小时内超过5次 |

**风险阈值**：≥50分标记为可疑登录（`is_suspicious=true`）

### 4. 滑动窗口刷新策略

```
登录时刻     刷新时刻1    刷新时刻2
  │             │            │
  ├─ Access1 ───┤            │
  ├─ Refresh ───┼─ Access2 ──┤
                 └──────── Refresh ───── Access3 ──→
```

- 每次刷新生成新的Access Token
- Refresh Token保持不变（直到过期或撤销）
- 旧Access Token立即加入黑名单

### 5. 防重放攻击

- **JTI唯一性**：每个Token都有唯一的JTI
- **一次性使用**：刷新后旧Token立即失效
- **时间窗口**：Token包含签发时间和过期时间
- **会话绑定**：Token与会话记录关联

## 使用场景

### 场景1：移动端长期登录

```python
# 1. 登录获取tokens
response = login(username, password)
access_token = response['access_token']
refresh_token = response['refresh_token']

# 2. 保存refresh_token到安全存储
SecureStorage.save('refresh_token', refresh_token)

# 3. Access Token过期前刷新
if access_token_expired():
    refresh_token = SecureStorage.get('refresh_token')
    new_tokens = refresh(refresh_token)
    access_token = new_tokens['access_token']
```

### 场景2：多设备管理

```python
# 1. 查看所有登录设备
sessions = get_sessions()

# 2. 识别可疑会话
suspicious_sessions = [s for s in sessions if s['is_suspicious']]

# 3. 强制下线可疑设备
for session in suspicious_sessions:
    revoke_session(session['id'])

# 4. 下线所有其他设备
revoke_all_sessions()
```

### 场景3：修改密码后强制重新登录

```python
# 1. 修改密码
change_password(old_password, new_password)

# 2. 系统自动撤销所有会话
# 3. 用户需要在所有设备重新登录
```

## 配置项

### 环境变量

```bash
# JWT密钥（必须）
SECRET_KEY=your-secret-key-here

# Access Token有效期（分钟）
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24小时

# Redis连接（可选，用于分布式部署）
REDIS_URL=redis://localhost:6379/0
```

### 服务配置

```python
# app/services/session_service.py

class SessionService:
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时
    REFRESH_TOKEN_EXPIRE_DAYS = 7  # 7天
    SESSION_EXPIRE_DAYS = 7  # 会话7天过期
    MAX_SESSIONS_PER_USER = 5  # 每用户最多5个会话
    RISK_SCORE_THRESHOLD = 50  # 风险分数阈值
```

## 数据库Schema

### user_sessions表

```sql
CREATE TABLE user_sessions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    access_token_jti VARCHAR(64) NOT NULL UNIQUE,
    refresh_token_jti VARCHAR(64) NOT NULL UNIQUE,
    device_id VARCHAR(128),
    device_name VARCHAR(100),
    device_type VARCHAR(50),
    ip_address VARCHAR(50),
    location VARCHAR(200),
    user_agent TEXT,
    browser VARCHAR(50),
    os VARCHAR(50),
    is_active BOOLEAN DEFAULT 1,
    login_at TIMESTAMP,
    last_activity_at TIMESTAMP,
    expires_at TIMESTAMP,
    logout_at TIMESTAMP,
    is_suspicious BOOLEAN DEFAULT 0,
    risk_score INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

## 性能优化

### Redis缓存策略

```python
# 会话缓存
session:{session_id} -> {user_id, is_active, jti}
TTL: 7天

# Token黑名单
jwt:blacklist:{jti} -> 1
TTL: Token剩余有效期

# IP地理位置缓存
ip:location:{ip} -> "北京"
TTL: 30天
```

### 数据库索引

```sql
CREATE INDEX idx_user_sessions_user_active ON user_sessions(user_id, is_active);
CREATE INDEX idx_user_sessions_access_jti ON user_sessions(access_token_jti);
CREATE INDEX idx_user_sessions_refresh_jti ON user_sessions(refresh_token_jti);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
```

## 定时任务

### 清理过期会话

```python
# 每小时执行一次
@scheduler.scheduled_job('interval', hours=1)
def cleanup_expired_sessions():
    """清理过期会话"""
    count = SessionService.cleanup_expired_sessions(db)
    logger.info(f"清理过期会话: {count}个")
```

## 错误处理

### 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|---------|
| 401 | Refresh Token无效或已过期 | 重新登录 |
| 403 | 会话已被撤销 | 重新登录 |
| 404 | 会话不存在 | 检查session_id |
| 423 | 账号已被锁定 | 等待锁定时间结束 |

## 最佳实践

### 1. 客户端实现

```javascript
// Token管理类
class TokenManager {
  constructor() {
    this.accessToken = null;
    this.refreshToken = null;
    this.refreshTimer = null;
  }
  
  async login(username, password) {
    const response = await api.post('/auth/login', {
      username, password
    });
    
    this.accessToken = response.access_token;
    this.refreshToken = response.refresh_token;
    
    // 设置自动刷新（提前5分钟）
    const refreshTime = (response.expires_in - 300) * 1000;
    this.refreshTimer = setTimeout(() => this.refresh(), refreshTime);
    
    return response;
  }
  
  async refresh() {
    try {
      const response = await api.post('/auth/refresh', {
        refresh_token: this.refreshToken
      });
      
      this.accessToken = response.access_token;
      
      // 重新设置定时器
      const refreshTime = (response.expires_in - 300) * 1000;
      this.refreshTimer = setTimeout(() => this.refresh(), refreshTime);
    } catch (error) {
      // Refresh失败，跳转到登录页
      this.logout();
      window.location.href = '/login';
    }
  }
  
  async logout() {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer);
    }
    
    await api.post('/auth/logout', { logout_all: false });
    
    this.accessToken = null;
    this.refreshToken = null;
  }
}
```

### 2. API请求拦截器

```javascript
// Axios拦截器
axios.interceptors.request.use(config => {
  const token = tokenManager.accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      // Token过期，尝试刷新
      try {
        await tokenManager.refresh();
        // 重试原请求
        return axios.request(error.config);
      } catch (refreshError) {
        // 刷新失败，跳转登录
        tokenManager.logout();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
```

### 3. 移动端安全存储

```swift
// iOS Keychain
func saveRefreshToken(_ token: String) {
    let query: [String: Any] = [
        kSecClass as String: kSecClassGenericPassword,
        kSecAttrAccount as String: "refresh_token",
        kSecValueData as String: token.data(using: .utf8)!
    ]
    SecItemAdd(query as CFDictionary, nil)
}
```

## 监控指标

### 关键指标

- **Token刷新率**：每小时刷新次数
- **异地登录检测率**：可疑登录占比
- **会话数量**：平均每用户会话数
- **强制下线次数**：安全操作频率
- **Token黑名单命中率**：撤销Token被使用次数

### 日志示例

```log
2026-02-14 10:00:00 INFO 创建会话成功: user_id=123, session_id=456, ip=192.168.1.100, suspicious=false, risk=0
2026-02-14 10:30:00 INFO 刷新Token成功: user_id=123, session_id=456
2026-02-14 11:00:00 WARNING 检测到新IP登录: user_id=123, ip=10.0.0.1
2026-02-14 11:00:01 WARNING 检测到异地登录: user_id=123, location=上海
2026-02-14 11:05:00 INFO 撤销会话成功: session_id=456, user_id=123
```

## 安全建议

1. **生产环境必须配置SECRET_KEY**
2. **启用HTTPS**：防止Token在传输中被窃取
3. **定期轮换SECRET_KEY**：建议每季度更换
4. **监控异常登录**：设置告警规则
5. **限制登录尝试**：防止暴力破解
6. **设备指纹增强**：结合Canvas、WebGL等技术
7. **IP地理位置**：接入专业GeoIP服务
8. **会话通知**：新设备登录时发送邮件/短信

## 故障排查

### 问题1：Token刷新失败

**症状**：`401 Unauthorized`

**排查步骤**：
1. 检查Refresh Token是否过期
2. 检查Token格式是否正确
3. 查看会话是否被撤销
4. 检查Redis连接状态

### 问题2：会话未创建

**症状**：登录成功但会话列表为空

**排查步骤**：
1. 检查数据库连接
2. 查看SessionService日志
3. 验证user_sessions表是否存在
4. 检查数据库写入权限

### 问题3：黑名单未生效

**症状**：撤销的Token仍可使用

**排查步骤**：
1. 检查Redis连接
2. 验证JTI提取逻辑
3. 检查黑名单键格式
4. 查看Token过期时间

## 更新日志

### v1.0.0 (2026-02-14)

- ✅ 实现双Token机制（Access + Refresh）
- ✅ 支持会话管理和多设备追踪
- ✅ Token黑名单（Redis + 内存降级）
- ✅ 设备绑定和User-Agent解析
- ✅ 异地登录检测和风险评分
- ✅ 滑动窗口刷新策略
- ✅ 强制下线功能
- ✅ 完整的API文档和测试

## 参考资料

- [RFC 7519 - JSON Web Token (JWT)](https://tools.ietf.org/html/rfc7519)
- [RFC 6749 - OAuth 2.0](https://tools.ietf.org/html/rfc6749)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
