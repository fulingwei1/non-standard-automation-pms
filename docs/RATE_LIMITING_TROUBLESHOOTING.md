# 速率限制故障排查指南

## 快速诊断

### 1. 检查速率限制是否启用

```bash
# 方法1: 检查环境变量
grep RATE_LIMIT .env

# 方法2: 查看启动日志
grep "速率限制" server.log

# 方法3: 发送测试请求
curl -I http://localhost:8000/api/v1/auth/login | grep X-RateLimit
```

### 2. 快速测试工具

```bash
#!/bin/bash
# test_rate_limit.sh

echo "测试速率限制..."

URL="http://localhost:8000/api/v1/auth/login"
COUNT=10

for i in $(seq 1 $COUNT); do
    echo "请求 $i:"
    curl -s -o /dev/null -w "HTTP %{http_code}\n" \
        -X POST "$URL" \
        -H "Content-Type: application/json" \
        -d '{"username":"test","password":"test"}'
    sleep 0.5
done
```

## 常见问题

### 问题1: 429错误频繁出现

**症状**：
```
HTTP/1.1 429 Too Many Requests
{"detail": "Rate limit exceeded: 5 per 1 minute"}
```

**原因**：
1. 限制设置过于严格
2. 客户端循环发送请求
3. 多个用户共享IP（NAT）
4. 测试代码未清理

**解决方案**：

#### 方案A: 调整限制（临时）
```bash
# .env
RATE_LIMIT_LOGIN=20/minute  # 从5增加到20
```

#### 方案B: 优化客户端代码
```javascript
// ❌ 错误：循环中未添加延迟
for (let i = 0; i < 100; i++) {
    await fetch('/api/v1/items');
}

// ✅ 正确：批量操作或添加延迟
const items = await fetch('/api/v1/items/batch');
```

#### 方案C: 使用基于用户的限流
```python
# 从IP限流改为用户限流
@router.get("/items")
@user_rate_limit("200/minute")  # 每个用户200次，而不是每个IP
async def get_items(...):
    pass
```

#### 方案D: 清理Redis计数器
```bash
# 手动清理某个IP的限制
redis-cli DEL "LIMITER/192.168.1.100/*"

# 清理所有限流计数器
redis-cli --scan --pattern "LIMITER/*" | xargs redis-cli DEL
```

---

### 问题2: 速率限制不生效

**症状**：
- 发送大量请求，从不返回429
- 响应头中没有 `X-RateLimit-*`

**诊断步骤**：

#### 步骤1: 检查是否启用
```bash
# .env
RATE_LIMIT_ENABLED=true  # 确保为true或未设置（默认true）
```

#### 步骤2: 检查装饰器是否应用
```python
# ❌ 错误：忘记添加装饰器
@router.post("/login")
async def login(...):
    pass

# ✅ 正确
@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):  # 注意：必须有Request参数
    pass
```

#### 步骤3: 检查Request参数
```python
# ❌ 错误：缺少Request参数
@router.post("/login")
@limiter.limit("5/minute")
async def login(username: str, password: str):  # slowapi需要Request
    pass

# ✅ 正确
@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, username: str, password: str):
    pass
```

#### 步骤4: 检查中间件注册
```python
# app/main.py
from app.core.rate_limiting import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

---

### 问题3: Redis连接失败

**症状**：
```
WARNING: 无法连接到Redis存储，降级到内存存储
```

**诊断**：

```bash
# 1. 检查Redis服务
systemctl status redis
# 或
redis-cli ping

# 2. 检查连接URL
echo $REDIS_URL
# 应该类似：redis://localhost:6379/0

# 3. 测试连接
redis-cli -u redis://localhost:6379/0 ping

# 4. 检查防火墙
telnet localhost 6379

# 5. 查看Redis日志
tail -f /var/log/redis/redis-server.log
```

**解决方案**：

#### 方案A: 修复Redis连接
```bash
# 启动Redis
systemctl start redis

# 或使用Docker
docker run -d -p 6379:6379 redis:alpine
```

#### 方案B: 修复连接URL
```bash
# .env
# ❌ 错误
REDIS_URL=localhost:6379

# ✅ 正确
REDIS_URL=redis://localhost:6379/0
```

#### 方案C: 临时使用内存存储
```bash
# .env
# 注释掉Redis URL，使用内存存储
# REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_STORAGE_URL=  # 清空，使用内存
```

---

### 问题4: 分布式环境计数不准

**症状**：
- 多实例部署时，限流不准确
- 同一IP可以发送超过限制的请求

**原因**：使用了内存存储，每个实例独立计数

**解决**：

```bash
# 必须使用共享Redis
RATE_LIMIT_STORAGE_URL=redis://shared-redis:6379/0
```

验证：
```bash
# 在Redis中查看键
redis-cli
> KEYS LIMITER/*
> GET LIMITER/192.168.1.100/api/v1/auth/login
```

---

### 问题5: 重启后限制立即重置

**症状**：
- 应用重启后，所有限流计数器归零
- 用户可以再次发送请求

**原因**：使用了内存存储

**解决**：
```bash
# 使用Redis持久化
REDIS_URL=redis://localhost:6379/0
```

Redis持久化配置：
```conf
# redis.conf
save 900 1      # 15分钟内至少1个键变化，保存
save 300 10     # 5分钟内至少10个键变化，保存
save 60 10000   # 1分钟内至少10000个键变化，保存
```

---

### 问题6: 测试环境限流干扰测试

**症状**：
- 运行测试时频繁遇到429
- 测试不稳定

**解决方案**：

#### 方案A: 禁用限流（推荐）
```bash
# .env.test
RATE_LIMIT_ENABLED=false
```

#### 方案B: 提高限制
```bash
# .env.test
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=10000/minute
RATE_LIMIT_LOGIN=1000/minute
```

#### 方案C: 测试前清理
```python
# conftest.py
import pytest

@pytest.fixture(autouse=True)
def clear_rate_limits():
    """每个测试前清理速率限制"""
    from app.core.rate_limiting import limiter
    if hasattr(limiter, 'reset'):
        limiter.reset()
    yield
```

---

### 问题7: 响应头缺失

**症状**：
- 响应中没有 `X-RateLimit-*` 头

**原因**：
1. 限流未启用
2. `headers_enabled=False`
3. CORS中间件过滤了头

**解决**：

```python
# app/core/rate_limiting.py
limiter = Limiter(
    key_func=get_remote_address,
    headers_enabled=True,  # 确保启用
)

# app/main.py - CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_headers=["*"],
    expose_headers=[  # 重要：暴露限流头
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ],
)
```

---

## 调试工具

### 1. 查看限流状态

```python
# 添加调试端点
@router.get("/debug/rate-limit-status")
async def get_rate_limit_status(request: Request):
    """查看当前请求的限流状态"""
    from app.core.rate_limiting import get_rate_limit_status
    return get_rate_limit_status(request)
```

### 2. Redis监控脚本

```bash
#!/bin/bash
# monitor_rate_limits.sh

while true; do
    clear
    echo "=== 速率限制监控 ==="
    echo "当前时间: $(date)"
    echo ""
    
    echo "活跃限流键数量:"
    redis-cli --scan --pattern "LIMITER/*" | wc -l
    echo ""
    
    echo "最近的限流键:"
    redis-cli --scan --pattern "LIMITER/*" | head -10
    echo ""
    
    sleep 5
done
```

### 3. 日志分析

```bash
# 统计429错误
grep "429" server.log | wc -l

# 按端点统计
grep "速率限制触发" server.log | awk '{print $(NF-1)}' | sort | uniq -c | sort -nr

# 按IP统计
grep "速率限制触发" server.log | grep -oP '\d+\.\d+\.\d+\.\d+' | sort | uniq -c | sort -nr

# 时间分布
grep "429" server.log | awk '{print $1, $2}' | uniq -c
```

### 4. Python调试脚本

```python
# debug_rate_limit.py
import requests
import time

def test_rate_limit(url, max_requests=20):
    """测试速率限制"""
    print(f"测试 {url}")
    print("=" * 60)
    
    for i in range(1, max_requests + 1):
        response = requests.post(url, json={"username": "test", "password": "test"})
        
        limit = response.headers.get('X-RateLimit-Limit')
        remaining = response.headers.get('X-RateLimit-Remaining')
        reset = response.headers.get('X-RateLimit-Reset')
        
        print(f"请求 {i:2d}: "
              f"HTTP {response.status_code} | "
              f"Limit: {limit} | "
              f"Remaining: {remaining} | "
              f"Reset: {reset}")
        
        if response.status_code == 429:
            print(f"  ⚠️  触发限流！")
            break
        
        time.sleep(0.5)

if __name__ == "__main__":
    test_rate_limit("http://localhost:8000/api/v1/auth/login")
```

---

## 性能问题

### 问题: 速率限制导致延迟增加

**症状**：
- API响应时间明显增加
- 限流检查耗时过长

**诊断**：

```python
import time

@router.post("/test")
async def test_endpoint(request: Request):
    start = time.time()
    # 业务逻辑
    duration = time.time() - start
    return {"duration": duration}
```

**优化**：

#### 1. 使用本地Redis
```bash
# ❌ 远程Redis（高延迟）
REDIS_URL=redis://remote-server:6379/0

# ✅ 本地Redis
REDIS_URL=redis://127.0.0.1:6379/0
```

#### 2. 优化Redis连接池
```bash
REDIS_URL=redis://localhost:6379/0?max_connections=100&socket_timeout=1
```

#### 3. 减少限流检查
```python
# 仅对敏感端点启用严格限流
@router.get("/public-data")
# 不添加限流装饰器，使用全局默认限制
async def get_public_data(...):
    pass
```

---

## 紧急措施

### 临时禁用速率限制

```bash
# 1. 环境变量（需重启）
RATE_LIMIT_ENABLED=false

# 2. Redis清空（立即生效）
redis-cli FLUSHDB

# 3. 代码热修复（不推荐）
# app/core/config.py
RATE_LIMIT_ENABLED = False
```

### 临时提高限制

```bash
# 快速提高所有限制
RATE_LIMIT_DEFAULT=10000/minute
RATE_LIMIT_LOGIN=1000/minute
RATE_LIMIT_REFRESH=1000/minute
```

---

## 获取帮助

### 1. 收集诊断信息

```bash
# 生成诊断报告
cat > rate_limit_diagnostic.txt << EOF
=== 环境配置 ===
$(grep RATE_LIMIT .env)

=== Redis状态 ===
$(redis-cli ping 2>&1)

=== 限流键数量 ===
$(redis-cli --scan --pattern "LIMITER/*" | wc -l)

=== 最近日志 ===
$(tail -100 server.log | grep "速率限制")

=== 429错误统计 ===
$(grep "429" server.log | wc -l)
EOF
```

### 2. 联系支持

提供以下信息：
- 诊断报告
- 具体错误信息
- 复现步骤
- 环境信息（单机/分布式）

---

## 相关文档

- [速率限制配置指南](./RATE_LIMITING_CONFIG.md)
- [API速率限制文档](./API_RATE_LIMITING.md)
- [系统架构文档](./ARCHITECTURE.md)
