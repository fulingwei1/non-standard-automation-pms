# API速率限制文档

## 概述

本系统实现了完整的API速率限制机制，用于防止暴力破解、DDoS攻击和API滥用。

## HTTP状态码

当请求超过速率限制时，API将返回：

**HTTP 429 Too Many Requests**

```json
{
  "detail": "Rate limit exceeded: 5 per 1 minute"
}
```

### 响应头信息

所有API响应都包含以下速率限制相关的响应头：

| 响应头 | 说明 | 示例 |
|--------|------|------|
| `X-RateLimit-Limit` | 时间窗口内允许的最大请求数 | `5` |
| `X-RateLimit-Remaining` | 当前时间窗口剩余请求数 | `3` |
| `X-RateLimit-Reset` | 限制重置的Unix时间戳 | `1676543210` |
| `Retry-After` | 建议重试的秒数（仅429响应） | `60` |

### 响应示例

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1676543270
Retry-After: 60

{
  "detail": "Rate limit exceeded: 5 per 1 minute"
}
```

## 端点限制说明

### 认证端点

| 端点 | 限制 | 限制策略 | 说明 |
|------|------|----------|------|
| `POST /api/v1/auth/login` | **5次/分钟** | IP地址 | 防止暴力破解 |
| `POST /api/v1/auth/register` | **3次/小时** | IP地址 | 防止恶意注册 |
| `POST /api/v1/auth/refresh` | **10次/分钟** | 用户ID或IP | 防止Token滥用 |
| `PUT /api/v1/auth/password` | **3次/小时** | IP+用户组合 | 防止密码暴力破解 |

### 数据操作端点

| 端点类型 | 限制 | 限制策略 |
|----------|------|----------|
| 删除操作 | **20次/分钟** | 用户ID |
| 批量操作 | **10次/分钟** | 用户ID |
| 普通查询 | **100次/分钟** | IP地址 |

### 全局默认限制

所有未明确设置限制的端点默认：**100次/分钟**（基于IP地址）

## 限制策略类型

### 1. 基于IP地址
```
限制键：IP地址
适用场景：防止单个IP的暴力攻击
示例：登录、注册
```

### 2. 基于用户ID
```
限制键：用户ID（未认证时降级到IP）
适用场景：防止单个用户滥用
示例：批量操作、删除操作
```

### 3. 组合策略（IP + 用户）
```
限制键：IP地址 + 用户ID
适用场景：最严格的保护
示例：密码修改、敏感操作
```

## 错误处理指南

### 客户端处理429错误

#### 方法1: 使用Retry-After头
```javascript
async function apiRequest(url, options) {
  const response = await fetch(url, options);
  
  if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After');
    const waitSeconds = parseInt(retryAfter) || 60;
    
    console.log(`速率限制触发，${waitSeconds}秒后重试`);
    await new Promise(resolve => setTimeout(resolve, waitSeconds * 1000));
    
    // 重试请求
    return apiRequest(url, options);
  }
  
  return response;
}
```

#### 方法2: 指数退避
```javascript
async function requestWithBackoff(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    const response = await fetch(url, options);
    
    if (response.status !== 429) {
      return response;
    }
    
    // 指数退避：2^i秒
    const waitTime = Math.pow(2, i) * 1000;
    console.log(`第${i+1}次重试，等待${waitTime/1000}秒...`);
    await new Promise(resolve => setTimeout(resolve, waitTime));
  }
  
  throw new Error('超过最大重试次数');
}
```

#### 方法3: 显示友好提示
```javascript
async function handleRateLimit(response) {
  if (response.status === 429) {
    const remaining = response.headers.get('X-RateLimit-Remaining');
    const reset = response.headers.get('X-RateLimit-Reset');
    
    if (reset) {
      const resetDate = new Date(parseInt(reset) * 1000);
      const now = new Date();
      const minutes = Math.ceil((resetDate - now) / 60000);
      
      alert(`请求过于频繁，请在${minutes}分钟后重试`);
    } else {
      alert('请求过于频繁，请稍后重试');
    }
  }
}
```

### Python客户端示例

```python
import requests
import time

def api_request_with_retry(url, max_retries=3):
    """带重试的API请求"""
    for attempt in range(max_retries):
        response = requests.post(url, json={...})
        
        if response.status_code != 429:
            return response
        
        # 获取Retry-After
        retry_after = int(response.headers.get('Retry-After', 60))
        print(f"速率限制触发，等待{retry_after}秒后重试...")
        time.sleep(retry_after)
    
    raise Exception(f"超过最大重试次数: {max_retries}")

# 使用示例
try:
    response = api_request_with_retry('http://api.example.com/login')
    print(response.json())
except Exception as e:
    print(f"请求失败: {e}")
```

## 最佳实践

### 1. 监控速率限制状态
```javascript
// 在每次请求后检查剩余次数
const response = await fetch(url);
const remaining = response.headers.get('X-RateLimit-Remaining');

if (remaining && parseInt(remaining) < 5) {
  console.warn(`警告：剩余请求次数不足 ${remaining}`);
}
```

### 2. 实现请求队列
```javascript
class RateLimitedQueue {
  constructor(limit = 100, windowMs = 60000) {
    this.limit = limit;
    this.windowMs = windowMs;
    this.queue = [];
    this.requests = [];
  }
  
  async enqueue(fn) {
    // 清理过期的请求记录
    const now = Date.now();
    this.requests = this.requests.filter(t => now - t < this.windowMs);
    
    // 如果达到限制，等待
    if (this.requests.length >= this.limit) {
      const oldestRequest = this.requests[0];
      const waitTime = this.windowMs - (now - oldestRequest);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
    
    // 执行请求
    this.requests.push(Date.now());
    return fn();
  }
}

// 使用
const queue = new RateLimitedQueue(100, 60000);
await queue.enqueue(() => fetch('/api/v1/projects'));
```

### 3. 批量操作优化
```javascript
// ❌ 不好：逐个请求
for (const item of items) {
  await deleteItem(item.id);  // 可能触发限流
}

// ✅ 好：使用批量端点
await batchDelete(items.map(i => i.id));
```

## 常见问题

### Q1: 为什么会收到429错误？
A: 您在短时间内发送了过多请求。请检查：
- 是否有代码循环发送请求
- 是否多个客户端使用同一IP
- 是否需要优化为批量操作

### Q2: 如何提高限制？
A: 速率限制是系统级配置，无法针对单个用户提高。如果有特殊需求，请联系系统管理员。

### Q3: 测试环境是否有速率限制？
A: 是的，但可以通过环境变量 `RATE_LIMIT_ENABLED=false` 禁用。

### Q4: 限制是基于什么计算的？
A: 根据端点不同，可能基于：
- IP地址
- 用户ID
- IP + 用户组合

### Q5: 可以看到自己的限流状态吗？
A: 可以，通过响应头：
- `X-RateLimit-Remaining`: 剩余次数
- `X-RateLimit-Reset`: 重置时间

## 技术细节

### 时间窗口算法

系统使用**滑动窗口**算法计算速率限制：

```
时间窗口：1分钟
限制：5次

请求时间轴：
|-----|-----|-----|-----|-----|-----|
0s    10s   20s   30s   40s   50s   60s
 ✓     ✓     ✓     ✓     ✓     ✗

第6次请求（55s）被拒绝，因为在过去60秒内已有5次请求
第7次请求需要等到第1次请求过期（60s后）
```

### 存储机制

- **生产环境**：使用Redis存储（支持分布式部署）
- **开发环境**：使用内存存储（单机部署）

### 性能影响

- **延迟增加**：< 1ms（Redis存储）
- **内存占用**：每个IP/用户约100字节
- **吞吐量影响**：可忽略（异步检查）

## 相关文档

- [速率限制配置指南](./RATE_LIMITING_CONFIG.md)
- [故障排查文档](./RATE_LIMITING_TROUBLESHOOTING.md)
- [API完整文档](./API_REFERENCE.md)
