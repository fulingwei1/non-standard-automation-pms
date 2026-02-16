# Rate Limiter 使用指南

本指南说明如何使用系统的速率限制功能。

---

## 🎯 概述

系统现在具备**双层安全保护机制**：

### 第一层: IP级别速率限制 (slowapi)
- **防护目标**: DDoS攻击、分布式暴力破解
- **限制范围**: 所有来自同一IP的请求
- **存储方式**: Redis（分布式） 或 内存（单机）

### 第二层: 账户级别锁定 (AccountLockoutService)
- **防护目标**: 针对特定账户的暴力破解
- **限制范围**: 同一用户名
- **存储方式**: 数据库

---

## 📋 限制清单

| Endpoint | 限制 | 说明 |
|----------|------|------|
| `POST /api/v1/auth/login` | 5次/分钟 | 防止暴力破解 |
| `POST /api/v1/auth/refresh` | 10次/分钟 | 防止token刷新滥用 |
| `PUT /api/v1/auth/password` | 5次/小时 | 严格限制密码修改 |
| 其他endpoints | 100次/分钟 | 全局默认限制 |

---

## ⚙️ 配置

### 环境变量

```bash
# .env

# 启用/禁用速率限制
RATE_LIMIT_ENABLED=true

# Redis存储（推荐生产环境）
REDIS_URL=redis://localhost:6379/0

# 或使用内存存储（开发环境）
# RATE_LIMIT_STORAGE_URL=  # 留空使用内存

# 自定义限制
RATE_LIMIT_DEFAULT=100/minute     # 全局默认
RATE_LIMIT_LOGIN=5/minute         # 登录
RATE_LIMIT_REFRESH=10/minute      # 刷新token
RATE_LIMIT_PASSWORD_CHANGE=5/hour # 密码修改
```

### 推荐配置

**开发环境**:
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_STORAGE_URL=  # 内存模式，无需Redis
```

**生产环境（单实例）**:
```bash
RATE_LIMIT_ENABLED=true
REDIS_URL=redis://127.0.0.1:6379/0  # 本地Redis
```

**生产环境（多实例/负载均衡）**:
```bash
RATE_LIMIT_ENABLED=true
REDIS_URL=redis://shared-redis:6379/0  # 共享Redis
```

**测试环境**:
```bash
RATE_LIMIT_ENABLED=false  # 禁用，避免干扰测试
```

---

## 🚀 使用示例

### 客户端处理429错误

**JavaScript (axios)**:
```javascript
import axios from 'axios';

async function login(username, password) {
  try {
    const response = await axios.post('/api/v1/auth/login', {
      username,
      password
    });
    return response.data;
  } catch (error) {
    if (error.response?.status === 429) {
      // 速率限制触发
      const retryAfter = error.response.headers['retry-after'] || 60;
      const remaining = error.response.headers['x-ratelimit-remaining'] || 0;
      
      alert(`请求过于频繁，请 ${retryAfter} 秒后再试`);
      
      // 或者自动重试
      await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
      return login(username, password);  // 递归重试
    }
    throw error;
  }
}
```

**Python (requests)**:
```python
import requests
import time

def login(username, password):
    url = "http://localhost:8000/api/v1/auth/login"
    
    while True:
        response = requests.post(url, json={
            "username": username,
            "password": password
        })
        
        if response.status_code == 429:
            # 速率限制触发
            retry_after = int(response.headers.get('Retry-After', 60))
            print(f"速率限制，等待 {retry_after} 秒...")
            time.sleep(retry_after)
            continue  # 重试
        
        return response.json()
```

---

## 📊 监控

### 查看响应头

所有受限制的请求都会返回速率限制信息：

```bash
curl -I http://localhost:8000/api/v1/auth/login

# 响应头:
X-RateLimit-Limit: 5           # 限制总数
X-RateLimit-Remaining: 3       # 剩余次数
X-RateLimit-Reset: 1708070460  # 重置时间（Unix时间戳）
```

### 查看日志

```bash
# 查看限流触发记录
grep "429\|Rate limit exceeded" server.log

# 按IP统计
grep "速率限制触发" server.log | \
  grep -oP '\d+\.\d+\.\d+\.\d+' | \
  sort | uniq -c | sort -nr

# 按endpoint统计
grep "速率限制触发" server.log | \
  awk '{print $(NF-1)}' | \
  sort | uniq -c | sort -nr
```

### Redis监控 (如果使用Redis)

```bash
# 连接Redis
redis-cli

# 查看所有限流键
> KEYS LIMITER/*

# 查看特定IP的计数
> GET LIMITER/192.168.1.100/api/v1/auth/login

# 查看过期时间
> TTL LIMITER/192.168.1.100/api/v1/auth/login

# 手动清理（如需）
> DEL LIMITER/192.168.1.100/*
```

---

## 🔧 自定义限流

### 方法1: 使用装饰器

```python
from fastapi import APIRouter, Request
from app.core.rate_limiting import limiter

router = APIRouter()

@router.post("/my-endpoint")
@limiter.limit("20/minute")  # 自定义限制
async def my_endpoint(request: Request):
    return {"status": "ok"}
```

### 方法2: 使用预定义装饰器

```python
from app.utils.rate_limit_decorator import (
    login_rate_limit,
    register_rate_limit,
    delete_rate_limit,
    batch_operation_rate_limit,
)

@router.post("/register")
@register_rate_limit()  # 3次/小时
async def register(request: Request, ...):
    pass

@router.delete("/items/{id}")
@delete_rate_limit()  # 20次/分钟
async def delete_item(request: Request, id: int):
    pass
```

### 方法3: 基于用户限流

```python
from app.core.rate_limiting import user_limiter

@router.get("/my-items")
@user_limiter.limit("200/minute")  # 每个用户200次，而不是每个IP
async def get_my_items(request: Request, current_user: User = Depends(...)):
    pass
```

### 方法4: 严格限流（IP+用户）

```python
from app.core.rate_limiting import strict_limiter

@router.post("/transfer")
@strict_limiter.limit("5/hour")  # IP和用户都要满足限制
async def transfer(request: Request, current_user: User = Depends(...)):
    pass
```

---

## 🛠️ 故障排除

### 问题1: 限流不生效

**检查清单**:
1. ✅ `RATE_LIMIT_ENABLED=true`
2. ✅ endpoint有 `@limiter.limit()` 装饰器
3. ✅ endpoint函数有 `request: Request` 参数
4. ✅ `app.state.limiter` 已注册
5. ✅ `RateLimitExceeded` 异常处理器已添加

### 问题2: 429频繁出现

**解决方案**:
1. 调整限制：增加 `RATE_LIMIT_LOGIN` 值
2. 优化客户端：减少请求频率或使用批量接口
3. 使用用户级限流：替代IP限流
4. 手动清理：`redis-cli DEL LIMITER/192.168.1.100/*`

### 问题3: Redis连接失败

**系统会自动降级到内存存储**，无需担心。

如需修复Redis连接：
```bash
# 检查Redis服务
systemctl status redis

# 或启动Docker Redis
docker run -d -p 6379:6379 redis:alpine

# 检查连接
redis-cli -u redis://localhost:6379/0 ping
```

### 问题4: 测试时被限流

**测试环境禁用限流**:
```bash
# .env.test
RATE_LIMIT_ENABLED=false
```

**或清理Redis**:
```bash
redis-cli FLUSHDB
```

---

## 📚 相关文档

- [API速率限制文档](docs/API_RATE_LIMITING.md) - 完整的API文档
- [配置指南](docs/RATE_LIMITING_CONFIG.md) - 详细配置说明
- [故障排查](docs/RATE_LIMITING_TROUBLESHOOTING.md) - 常见问题解决
- [分析报告](team5_rate_limiter_analysis_report.md) - 技术分析和决策依据

---

## ❓ 常见问题

**Q: 为什么需要双层保护？**

A: 
- IP限流防止DDoS和分布式攻击
- 账户锁定防止针对特定账户的暴力破解
- 两者互补，缺一不可

**Q: Redis必须吗？**

A:
- 单机部署：可选，使用内存存储也可以
- 多实例部署：必须，否则限流不准确

**Q: 性能影响多大？**

A:
- 内存模式：<1ms per request
- Redis本地：~3ms per request
- Redis远程：取决于网络延迟

**Q: 如何临时禁用限流？**

A:
```bash
# 方法1: 环境变量（需重启）
RATE_LIMIT_ENABLED=false

# 方法2: Redis清空（立即生效）
redis-cli FLUSHDB

# 方法3: 提高限制（推荐）
RATE_LIMIT_DEFAULT=10000/minute
```

**Q: 能否针对特定IP白名单？**

A: 当前版本不支持，建议后续版本实现。临时方案：
```bash
# 手动清理特定IP的限制
redis-cli DEL "LIMITER/192.168.1.100/*"
```

---

**文档版本**: 1.0  
**更新日期**: 2026-02-16  
**负责团队**: Subagent Team 5
