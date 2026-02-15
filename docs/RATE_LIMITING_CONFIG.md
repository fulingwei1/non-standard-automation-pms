# 速率限制配置指南

## 快速开始

### 1. 基础配置

在 `.env` 文件中添加：

```bash
# 启用速率限制
RATE_LIMIT_ENABLED=true

# Redis存储（推荐）
REDIS_URL=redis://localhost:6379/0

# 或使用独立的Redis数据库
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/1
```

### 2. 验证配置

启动应用后，检查日志：

```bash
# 成功输出
INFO: 速率限制器已启用，使用Redis存储: redis://localhost:6379/0

# 降级到内存存储
WARNING: 速率限制器使用内存存储，在分布式部署中可能不准确。
```

### 3. 测试速率限制

```bash
# 测试登录限流（5次/分钟）
for i in {1..10}; do
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}'
  echo ""
done

# 前5次应该返回正常响应（401或200）
# 第6次开始返回429 Too Many Requests
```

## 配置参数详解

### 全局配置

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `RATE_LIMIT_ENABLED` | bool | `true` | 是否启用速率限制 |
| `RATE_LIMIT_STORAGE_URL` | string | `None` | Redis存储URL |
| `RATE_LIMIT_DEFAULT` | string | `"100/minute"` | 全局默认限制 |

### 端点特定配置

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `RATE_LIMIT_LOGIN` | `"5/minute"` | 登录端点限制 |
| `RATE_LIMIT_REGISTER` | `"3/hour"` | 注册端点限制 |
| `RATE_LIMIT_REFRESH` | `"10/minute"` | Token刷新限制 |
| `RATE_LIMIT_PASSWORD_CHANGE` | `"3/hour"` | 密码修改限制 |
| `RATE_LIMIT_DELETE` | `"20/minute"` | 删除操作限制 |
| `RATE_LIMIT_BATCH` | `"10/minute"` | 批量操作限制 |

### 限制格式

支持的时间单位：
- `second` / `seconds` / `s` - 秒
- `minute` / `minutes` / `m` - 分钟
- `hour` / `hours` / `h` - 小时
- `day` / `days` / `d` - 天

示例：
```bash
RATE_LIMIT_LOGIN="5/minute"      # 每分钟5次
RATE_LIMIT_REFRESH="10/m"        # 每分钟10次（简写）
RATE_LIMIT_REGISTER="3/hour"     # 每小时3次
RATE_LIMIT_DEFAULT="1000/day"    # 每天1000次
```

## 部署场景配置

### 场景1: 单机开发环境

```bash
# .env
RATE_LIMIT_ENABLED=true
# 不设置REDIS_URL，使用内存存储
RATE_LIMIT_DEFAULT=1000/minute  # 宽松限制，方便开发
```

**特点**：
- ✅ 无需Redis依赖
- ✅ 配置简单
- ❌ 重启后计数器重置
- ❌ 不支持分布式

### 场景2: 生产环境（单实例）

```bash
# .env
RATE_LIMIT_ENABLED=true
REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_LOGIN=5/minute
RATE_LIMIT_PASSWORD_CHANGE=3/hour
```

**特点**：
- ✅ Redis持久化
- ✅ 重启后计数器保留
- ✅ 生产级限制
- ✅ 支持未来扩展到多实例

### 场景3: 生产环境（多实例/负载均衡）

```bash
# .env
RATE_LIMIT_ENABLED=true
REDIS_URL=redis://redis-cluster:6379/0  # 使用Redis集群
RATE_LIMIT_STORAGE_URL=redis://redis-cluster:6379/1  # 独立数据库
RATE_LIMIT_DEFAULT=100/minute
```

**特点**：
- ✅ 所有实例共享计数器
- ✅ 准确的分布式限流
- ✅ 独立Redis数据库，不影响其他功能
- ✅ 高可用（Redis集群）

### 场景4: 测试环境

```bash
# .env.test
RATE_LIMIT_ENABLED=false  # 禁用限流，方便测试
```

或者使用极高的限制：

```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=10000/minute
RATE_LIMIT_LOGIN=1000/minute
```

## Redis配置

### 方案1: 共享Redis数据库

```bash
REDIS_URL=redis://localhost:6379/0
# RATE_LIMIT_STORAGE_URL 不设置，自动使用 REDIS_URL
```

**优点**：配置简单，适合小型应用
**缺点**：速率限制数据和业务数据混在一起

### 方案2: 独立Redis数据库（推荐）

```bash
REDIS_URL=redis://localhost:6379/0  # 业务数据
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/1  # 速率限制专用
```

**优点**：
- 数据隔离
- 可独立调整过期策略
- 方便清理和监控

### 方案3: 独立Redis实例

```bash
REDIS_URL=redis://cache-server:6379/0  # 业务缓存
RATE_LIMIT_STORAGE_URL=redis://limiter-server:6379/0  # 限流专用
```

**优点**：
- 完全隔离
- 独立扩展
- 故障隔离

### Redis连接参数

完整URL格式：
```
redis://[:password@]host[:port][/database][?option=value]
```

示例：
```bash
# 无密码
REDIS_URL=redis://localhost:6379/0

# 有密码
REDIS_URL=redis://:mypassword@localhost:6379/0

# 使用用户名和密码（Redis 6+）
REDIS_URL=redis://username:password@localhost:6379/0

# 自定义连接池
REDIS_URL=redis://localhost:6379/0?max_connections=50&socket_timeout=5
```

## 自定义端点限流

### 方法1: 使用预定义装饰器

```python
from app.utils.rate_limit_decorator import (
    login_rate_limit,
    delete_rate_limit,
    batch_operation_rate_limit,
)

@router.post("/login")
@login_rate_limit()  # 自动应用配置的限制
async def login(...):
    pass

@router.delete("/items/{item_id}")
@delete_rate_limit()
async def delete_item(...):
    pass
```

### 方法2: 自定义限制

```python
from app.utils.rate_limit_decorator import rate_limit

@router.post("/heavy-operation")
@rate_limit("3/minute")  # 自定义为3次/分钟
async def heavy_operation(...):
    pass
```

### 方法3: 基于用户限流

```python
from app.utils.rate_limit_decorator import user_rate_limit

@router.post("/user-action")
@user_rate_limit("50/hour")  # 每个用户每小时50次
async def user_action(...):
    pass
```

### 方法4: 严格限流（IP + 用户）

```python
from app.utils.rate_limit_decorator import strict_rate_limit

@router.post("/critical-action")
@strict_rate_limit("1/hour")  # IP和用户都限制
async def critical_action(...):
    pass
```

## 监控和调优

### 1. 日志监控

启用详细日志：

```bash
# .env
DEBUG=true
```

查看限流日志：
```bash
tail -f server.log | grep "速率限制"
```

输出示例：
```
WARNING: 速率限制触发: POST /api/v1/auth/login from 192.168.1.100
```

### 2. Redis监控

查看限流键：
```bash
redis-cli
> KEYS LIMITER/*
> TTL LIMITER/192.168.1.100/api/v1/auth/login
> GET LIMITER/192.168.1.100/api/v1/auth/login
```

### 3. 性能指标

关键指标：
- **429响应率**：429错误 / 总请求数
- **平均延迟**：限流检查增加的延迟
- **Redis连接数**：活跃连接数

Prometheus指标（如果启用）：
```
# 429错误数
rate_limit_exceeded_total

# 限流检查延迟
rate_limit_check_duration_seconds
```

### 4. 调优建议

#### 过于严格（429频繁）
```bash
# 增加限制
RATE_LIMIT_DEFAULT=200/minute  # 从100增加到200
RATE_LIMIT_LOGIN=10/minute     # 从5增加到10
```

#### 过于宽松（安全风险）
```bash
# 减少限制
RATE_LIMIT_DEFAULT=50/minute   # 从100减少到50
RATE_LIMIT_LOGIN=3/minute      # 从5减少到3
```

#### 优化Redis性能
```bash
# 使用独立Redis实例
RATE_LIMIT_STORAGE_URL=redis://fast-redis:6379/0

# 优化连接池
RATE_LIMIT_STORAGE_URL=redis://localhost:6379/0?max_connections=100

# 使用本地Redis（减少网络延迟）
RATE_LIMIT_STORAGE_URL=redis://127.0.0.1:6379/0
```

## 常见配置错误

### 错误1: Redis连接失败

**症状**：
```
WARNING: 无法连接到Redis存储，降级到内存存储
```

**解决**：
```bash
# 检查Redis是否运行
redis-cli ping

# 检查连接URL
REDIS_URL=redis://localhost:6379/0  # 确保主机和端口正确

# 检查防火墙
telnet localhost 6379
```

### 错误2: 多实例计数不准

**症状**：分布式部署时，限流不生效或不准确

**原因**：使用了内存存储

**解决**：
```bash
# 必须使用Redis
RATE_LIMIT_STORAGE_URL=redis://shared-redis:6379/0
```

### 错误3: 限制格式错误

**症状**：
```
ValueError: Invalid rate limit format: "5/min"
```

**解决**：
```bash
# ❌ 错误
RATE_LIMIT_LOGIN="5/min"

# ✅ 正确
RATE_LIMIT_LOGIN="5/minute"
```

## 安全建议

### 1. 生产环境必须启用

```bash
RATE_LIMIT_ENABLED=true  # 永远不要在生产环境禁用
```

### 2. 使用严格的登录限制

```bash
RATE_LIMIT_LOGIN=5/minute         # 防止暴力破解
RATE_LIMIT_PASSWORD_CHANGE=3/hour # 防止密码猜测
```

### 3. 保护敏感操作

```python
@router.delete("/user/{user_id}")
@strict_rate_limit("5/hour")  # 严格限制删除操作
async def delete_user(...):
    pass
```

### 4. 定期审计

```bash
# 每周查看429错误日志
grep "429" server.log | wc -l

# 识别异常IP
grep "速率限制触发" server.log | awk '{print $NF}' | sort | uniq -c | sort -nr
```

## 下一步

- [API速率限制文档](./API_RATE_LIMITING.md) - 了解API响应格式
- [故障排查文档](./RATE_LIMITING_TROUBLESHOOTING.md) - 解决常见问题
- [安全最佳实践](./SECURITY_BEST_PRACTICES.md) - 提升系统安全
