# 权限缓存配置指南

本文档详细说明如何配置和使用权限缓存系统。

---

## 📋 目录

1. [快速开始](#快速开始)
2. [架构概览](#架构概览)
3. [配置说明](#配置说明)
4. [使用方式](#使用方式)
5. [缓存失效机制](#缓存失效机制)
6. [监控与调优](#监控与调优)
7. [故障排查](#故障排查)
8. [最佳实践](#最佳实践)

---

## 🚀 快速开始

### 1. 安装 Redis（可选，推荐）

权限缓存支持两种模式：
- **Redis 缓存**（推荐生产环境）
- **内存缓存**（开发/测试环境降级方案）

#### macOS 安装 Redis

```bash
brew install redis
brew services start redis
```

#### Ubuntu/Debian 安装 Redis

```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

#### Docker 运行 Redis

```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

### 2. 配置环境变量

在 `.env` 文件中添加：

```bash
# Redis 配置（可选）
REDIS_URL=redis://localhost:6379/0

# 缓存开关（默认启用）
REDIS_CACHE_ENABLED=true

# 缓存过期时间（秒）
PERMISSION_CACHE_TTL=600        # 用户权限缓存: 10 分钟
ROLE_CACHE_TTL=1800             # 角色权限缓存: 30 分钟
```

### 3. 验证缓存功能

```bash
# 启动应用
uvicorn app.main:app --reload

# 测试权限查询（第一次会查询数据库）
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/users/me/permissions

# 再次查询（应从缓存返回，响应更快）
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/users/me/permissions
```

---

## 🏗️ 架构概览

### 缓存分层结构

```
┌─────────────────────────────────────────────────┐
│              应用层 (API Endpoints)             │
└─────────────────┬───────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────┐
│          权限服务 (PermissionService)           │
│  - 集成缓存读取                                  │
│  - 缓存未命中时查询数据库                        │
│  - 自动写入缓存                                  │
└─────────────────┬───────────────────────────────┘
                  │
                  ├─────────────────────────┐
                  ▼                         ▼
    ┌─────────────────────────┐   ┌──────────────────┐
    │ PermissionCacheService  │   │  Database        │
    │ - 多租户隔离            │   │  - 权限查询      │
    │ - 自动失效机制          │   │  - 角色关联      │
    │ - 统计信息              │   └──────────────────┘
    └─────────────┬───────────┘
                  │
                  ▼
    ┌─────────────────────────┐
    │    CacheService         │
    │  - Redis 主缓存         │
    │  - 内存缓存降级         │
    │  - 性能统计             │
    └─────────────────────────┘
```

### 缓存键结构（多租户隔离）

```
权限缓存键设计:

perm:t{tenant_id}:user:{user_id}           # 用户权限缓存
perm:t{tenant_id}:role:{role_id}           # 角色权限缓存
perm:t{tenant_id}:user_roles:{user_id}     # 用户-角色关联
perm:t{tenant_id}:role_users:{role_id}     # 角色-用户关联

示例:
perm:t1:user:123                           # 租户1的用户123的权限
perm:t2:role:5                             # 租户2的角色5的权限
perm:tsystem:user:1                        # 系统级用户（超级管理员）
```

---

## ⚙️ 配置说明

### app/core/config.py

完整配置项：

```python
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ========== Redis 缓存配置 ==========
    
    # Redis 连接 URL
    # 格式: redis://[username:password@]host:port/database
    # 示例:
    #   - redis://localhost:6379/0              (本地无密码)
    #   - redis://:mypassword@localhost:6379/0  (本地有密码)
    #   - redis://user:pass@redis.example.com:6379/0  (远程)
    REDIS_URL: Optional[str] = None
    
    # 是否启用 Redis 缓存
    # True: 启用缓存（推荐）
    # False: 禁用缓存（仅用于调试）
    REDIS_CACHE_ENABLED: bool = True
    
    # ========== 权限缓存 TTL 配置 ==========
    
    # 用户权限缓存过期时间（秒）
    # 建议: 300-1800（5分钟-30分钟）
    # 默认: 600（10分钟）
    PERMISSION_CACHE_TTL: int = 600
    
    # 角色权限缓存过期时间（秒）
    # 建议: 600-3600（10分钟-1小时）
    # 默认: 1800（30分钟）
    ROLE_CACHE_TTL: int = 1800
    
    class Config:
        env_file = ".env"
        case_sensitive = True
```

### 环境变量配置（.env）

#### 生产环境推荐配置

```bash
# Redis URL（必填）
REDIS_URL=redis://production-redis.example.com:6379/0

# 启用缓存（推荐）
REDIS_CACHE_ENABLED=true

# 较长的 TTL，减少数据库压力
PERMISSION_CACHE_TTL=1200      # 20 分钟
ROLE_CACHE_TTL=3600            # 1 小时
```

#### 开发环境配置

```bash
# 使用本地 Redis 或不配置（自动降级到内存缓存）
REDIS_URL=redis://localhost:6379/0

# 启用缓存
REDIS_CACHE_ENABLED=true

# 较短的 TTL，便于测试
PERMISSION_CACHE_TTL=60        # 1 分钟
ROLE_CACHE_TTL=300             # 5 分钟
```

#### 测试环境配置（不使用 Redis）

```bash
# 不配置 REDIS_URL，自动使用内存缓存
# REDIS_URL=

# 启用缓存（内存模式）
REDIS_CACHE_ENABLED=true

# 短 TTL
PERMISSION_CACHE_TTL=30
ROLE_CACHE_TTL=60
```

---

## 💡 使用方式

### 1. 权限查询（自动使用缓存）

```python
from sqlalchemy.orm import Session
from app.services.permission_service import PermissionService

# 获取用户权限（自动从缓存读取或查询数据库）
permissions = PermissionService.get_user_permissions(
    db=db,
    user_id=user.id,
    tenant_id=user.tenant_id  # 可选，用于多租户隔离
)

# permissions = ["project:read", "project:write", "user:read", ...]
```

### 2. 权限检查（自动使用缓存）

```python
# 检查单个权限
has_permission = PermissionService.check_permission(
    db=db,
    user_id=user.id,
    permission_code="project:write",
    user=user,
    tenant_id=user.tenant_id
)

# 检查任意权限
has_any = PermissionService.check_any_permission(
    db=db,
    user_id=user.id,
    permission_codes=["project:read", "project:write"],
    user=user
)

# 检查所有权限
has_all = PermissionService.check_all_permissions(
    db=db,
    user_id=user.id,
    permission_codes=["project:read", "project:write"],
    user=user
)
```

### 3. 手动失效缓存（高级用法）

```python
from app.services.permission_cache_service import get_permission_cache_service

cache_service = get_permission_cache_service()

# 1. 用户权限失效
cache_service.invalidate_user_permissions(user_id=123, tenant_id=1)

# 2. 角色权限失效
cache_service.invalidate_role_permissions(role_id=5, tenant_id=1)

# 3. 角色权限变更时，同时失效角色和相关用户
cache_service.invalidate_role_and_users(
    role_id=5,
    user_ids=[10, 20, 30],  # 可选，如果不提供会自动查询
    tenant_id=1
)

# 4. 用户角色变更时
cache_service.invalidate_user_role_change(
    user_id=123,
    old_role_ids=[1, 2],
    new_role_ids=[2, 3],
    tenant_id=1
)

# 5. 失效整个租户的缓存
cache_service.invalidate_tenant(tenant_id=1)

# 6. 失效所有缓存（谨慎使用！）
cache_service.invalidate_all()
```

### 4. 查看缓存统计

```python
from app.services.permission_cache_service import get_permission_cache_service

cache_service = get_permission_cache_service()
stats = cache_service.get_stats()

print(stats)
# 输出示例:
# {
#   "hits": 1250,
#   "misses": 50,
#   "total_requests": 1300,
#   "hit_rate": 96.15,
#   "cache_type": "redis",
#   "memory_cache_size": 0,
#   "tenant_isolation": True,
#   "ttl_user": 600,
#   "ttl_role": 1800
# }
```

---

## 🔄 缓存失效机制

### 自动失效触发点

权限缓存在以下场景会**自动失效**，确保数据一致性：

#### 1. 用户角色变更

**触发位置**: `app/api/v1/endpoints/users/utils.py`

```python
def replace_user_roles(db: Session, user_id: int, role_ids: List[int]):
    """替换用户角色"""
    # ... 更新数据库 ...
    
    # 自动失效缓存
    cache_service.invalidate_user_role_change(
        user_id, old_role_ids, new_role_ids
    )
```

**失效范围**:
- 用户权限缓存: `perm:t{tenant_id}:user:{user_id}`
- 用户-角色关联: `perm:t{tenant_id}:user_roles:{user_id}`
- 变更的角色-用户关联: `perm:t{tenant_id}:role_users:{role_id}`

#### 2. 角色权限变更

**触发位置**: `app/api/v1/endpoints/roles.py`

```python
@router.put("/{role_id}/permissions")
def update_role_permissions(role_id: int, permission_ids: List[int], ...):
    """更新角色权限"""
    # ... 更新数据库 ...
    
    # 自动失效角色和相关用户缓存
    cache_service.invalidate_role_and_users(
        role_id=role_id,
        tenant_id=current_user.tenant_id
    )
```

**失效范围**:
- 角色权限缓存: `perm:t{tenant_id}:role:{role_id}`
- 所有拥有该角色的用户权限: `perm:t{tenant_id}:user:{user_id}`
- 角色-用户关联: `perm:t{tenant_id}:role_users:{role_id}`

#### 3. 租户配置变更

```python
# 批量权限更新时
cache_service.invalidate_tenant(tenant_id=1)
```

**失效范围**:
- 租户下所有权限缓存: `perm:t{tenant_id}:*`

#### 4. TTL 自动过期

即使自动失效机制失败，缓存也会在 TTL 到期后自动刷新。

---

## 📊 监控与调优

### 缓存性能监控

#### 1. 获取缓存统计（API 接口）

创建监控接口（建议仅管理员可访问）：

```python
# app/api/v1/endpoints/admin.py

@router.get("/cache/stats")
def get_cache_stats(
    current_user: User = Depends(require_permission("system:admin"))
):
    """获取缓存统计信息"""
    from app.services.permission_cache_service import get_permission_cache_service
    
    cache_service = get_permission_cache_service()
    stats = cache_service.get_stats()
    
    return ResponseModel(code=200, message="获取成功", data=stats)
```

#### 2. 日志监控

权限服务会自动记录缓存相关日志：

```python
# 日志示例
2026-02-14 10:30:15 - app.services.permission_service - DEBUG - 缓存命中: user_id=123, tenant_id=1, permissions_count=25
2026-02-14 10:31:20 - app.services.permission_service - DEBUG - 缓存未命中，查询数据库: user_id=456, tenant_id=1
2026-02-14 10:31:21 - app.services.permission_service - DEBUG - 权限已缓存: user_id=456, tenant_id=1, permissions_count=18
2026-02-14 10:32:10 - app.services.permission_cache_service - INFO - Invalidating role and user caches: tenant_id=1, role_id=5, affected_users=42
```

#### 3. 性能指标建议

| 指标 | 目标值 | 监控方式 |
|------|--------|---------|
| 缓存命中率 | > 90% | `stats["hit_rate"]` |
| 平均响应时间 | < 10 ms | API 响应时间监控 |
| 缓存失效频率 | 每天 < 100 次 | 日志统计 |
| Redis 连接状态 | 正常 | `stats["cache_type"] == "redis"` |

### 调优建议

#### 1. TTL 调优

根据业务特点调整 TTL：

| 场景 | 推荐 TTL | 说明 |
|------|---------|------|
| 权限变更频繁 | 300-600 秒 | 缩短 TTL，更快反映变更 |
| 权限变更较少 | 1800-3600 秒 | 延长 TTL，减少数据库压力 |
| 开发/测试 | 30-120 秒 | 便于快速测试 |

#### 2. Redis 连接池配置

```python
# app/utils/redis_client.py

def get_redis_client():
    """获取 Redis 客户端（连接池）"""
    from redis import ConnectionPool, Redis
    from app.core.config import settings
    
    if not settings.REDIS_URL:
        return None
    
    pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=50,      # 最大连接数
        socket_timeout=5,        # 超时时间
        socket_connect_timeout=5,
        retry_on_timeout=True,
        health_check_interval=30 # 健康检查间隔
    )
    
    return Redis(connection_pool=pool)
```

#### 3. 缓存预热（可选）

系统启动时预加载常用用户权限：

```python
# app/main.py

@app.on_event("startup")
async def warmup_cache():
    """缓存预热"""
    from app.services.permission_service import PermissionService
    from app.db.session import SessionLocal
    
    db = SessionLocal()
    try:
        # 预加载活跃用户权限
        active_users = db.query(User).filter(User.is_active == True).limit(100).all()
        for user in active_users:
            PermissionService.get_user_permissions(db, user.id, user.tenant_id)
        
        logger.info(f"缓存预热完成: {len(active_users)} 个用户")
    finally:
        db.close()
```

---

## 🔧 故障排查

### 问题 1: 缓存未生效（响应时间未改善）

**现象**: 权限查询仍然很慢，缓存命中率为 0%

**排查步骤**:

1. 检查配置:
```python
from app.core.config import settings
print(settings.REDIS_CACHE_ENABLED)  # 应该是 True
print(settings.REDIS_URL)            # 应该有值或为 None（内存缓存）
```

2. 检查 Redis 连接:
```python
from app.utils.redis_client import get_redis_client
client = get_redis_client()
if client:
    client.ping()  # 应该返回 True
```

3. 查看日志:
```bash
grep "缓存命中\|缓存未命中" app.log
```

**解决方案**:
- 确认 `REDIS_CACHE_ENABLED=true`
- 检查 Redis 服务是否运行: `redis-cli ping`
- 检查防火墙/网络配置

---

### 问题 2: 权限变更后未立即生效

**现象**: 更新角色权限后，用户仍有旧权限

**排查步骤**:

1. 检查自动失效是否执行:
```bash
grep "Invalidating" app.log
```

2. 检查缓存键是否正确:
```python
from app.services.permission_cache_service import get_permission_cache_service
cache = get_permission_cache_service()

# 查看用户权限是否存在
permissions = cache.get_user_permissions(user_id=123, tenant_id=1)
print(permissions)  # 应该是 None（如果已失效）
```

**解决方案**:
- 手动失效缓存: `cache.invalidate_user_permissions(user_id, tenant_id)`
- 检查代码是否调用了失效函数
- 等待 TTL 过期（最多 10-30 分钟）

---

### 问题 3: Redis 连接失败，系统无响应

**现象**: Redis 不可用时，系统挂起或报错

**排查步骤**:

1. 检查降级机制:
```python
from app.services.cache_service import CacheService
cache = CacheService()
print(cache.use_redis)  # 应该是 False（降级到内存）
```

**解决方案**:
- 系统会自动降级到内存缓存
- 检查 Redis 连接超时配置
- 修复 Redis 服务后系统自动恢复

---

### 问题 4: 内存占用过高

**现象**: 使用内存缓存时，应用内存占用持续增长

**排查步骤**:

1. 检查缓存大小:
```python
from app.services.permission_cache_service import get_permission_cache_service
stats = get_permission_cache_service().get_stats()
print(stats["memory_cache_size"])  # 缓存条目数
```

2. 检查是否有缓存清理:
```bash
grep "delete\|invalidate" app.log
```

**解决方案**:
- 使用 Redis 替代内存缓存
- 缩短 TTL 值
- 定期清理缓存: `cache.invalidate_all()`

---

## 🎯 最佳实践

### 1. 生产环境必须使用 Redis

**原因**:
- 内存缓存在多进程/多服务器部署时数据不一致
- Redis 支持持久化、集群、高可用

**配置**:
```bash
REDIS_URL=redis://production-redis:6379/0
REDIS_CACHE_ENABLED=true
```

---

### 2. 合理设置 TTL

**建议**:
- **用户权限**: 600-1200 秒（10-20 分钟）
- **角色权限**: 1800-3600 秒（30-60 分钟）

**原则**:
- 权限变更频繁 → 缩短 TTL
- 系统压力大 → 延长 TTL
- 安全要求高 → 缩短 TTL

---

### 3. 监控缓存命中率

**目标**: 缓存命中率 > 90%

**监控方式**:
```python
# 定期检查
stats = cache_service.get_stats()
if stats["hit_rate"] < 90:
    logger.warning(f"缓存命中率过低: {stats['hit_rate']}%")
```

---

### 4. 缓存失效要及时

**在以下操作后必须失效缓存**:
- 用户角色变更
- 角色权限变更
- 批量权限导入
- 租户配置变更

**示例**:
```python
# 更新角色权限后
cache_service.invalidate_role_and_users(role_id, tenant_id=tenant_id)
```

---

### 5. 多租户隔离

**确保缓存键包含 tenant_id**:
```python
# ✅ 正确
cache_service.get_user_permissions(user_id=123, tenant_id=1)

# ❌ 错误（可能跨租户泄露）
cache_service.get_user_permissions(user_id=123, tenant_id=None)
```

---

### 6. 日志级别配置

**生产环境**:
```python
# 设置为 INFO，避免大量 DEBUG 日志
logging.getLogger("app.services.permission_service").setLevel(logging.INFO)
```

**开发环境**:
```python
# 设置为 DEBUG，便于调试
logging.getLogger("app.services.permission_service").setLevel(logging.DEBUG)
```

---

## 📚 参考资料

- [Redis 官方文档](https://redis.io/documentation)
- [SQLAlchemy 缓存策略](https://docs.sqlalchemy.org/en/14/orm/caching.html)
- [多租户缓存隔离最佳实践](https://www.infoq.com/articles/multi-tenant-caching/)

---

**文档版本**: v1.0  
**最后更新**: 2026-02-14  
**维护者**: 开发团队
