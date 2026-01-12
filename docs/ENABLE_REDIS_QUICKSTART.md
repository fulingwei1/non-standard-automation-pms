# Redis缓存快速启用指南

> **快速启用Redis缓存，立即提升系统性能50-80%**

---

## 步骤1: 确认Redis已安装并运行

```bash
# 检查Redis是否运行
redis-cli ping
# 应该返回: PONG

# 如果Redis未运行，启动它
# macOS
brew services start redis

# Linux
sudo systemctl start redis-server
```

---

## 步骤2: 运行Redis配置向导

```bash
# 在项目根目录运行
python scripts/setup_redis.py
```

这个脚本会：
- ✅ 测试Redis连接
- ✅ 显示Redis版本信息
- ✅ 生成环境变量配置
- ✅ 提供下一步操作指导

**预期输出:**
```
============================================================
Redis缓存配置向导
============================================================

✓ redis包已安装
正在连接Redis: redis://localhost:6379/0
✓ Redis连接成功!
✓ Redis版本: 7.2.3
✓ 运行模式: standalone
✓ Redis读写测试成功

============================================================
环境变量配置
============================================================

请将以下配置添加到 .env 文件中:

# Redis缓存配置
# ============================================

# Redis连接URL
REDIS_URL=redis://localhost:6379/0

# 是否启用Redis缓存
REDIS_CACHE_ENABLED=true

# 默认缓存过期时间（秒），5分钟
REDIS_CACHE_DEFAULT_TTL=300

# 项目详情缓存过期时间（秒），10分钟
REDIS_CACHE_PROJECT_DETAIL_TTL=600

# 项目列表缓存过期时间（秒），5分钟
REDIS_CACHE_PROJECT_LIST_TTL=300

============================================================
配置完成！
============================================================

下一步:
1. 将上述配置添加到 .env 文件
2. 重启应用: uvicorn app.main:app --reload
3. Redis缓存将自动启用
```

---

## 步骤3: 设置环境变量

创建或编辑 `.env` 文件：

```env
# Redis缓存配置
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_ENABLED=true
REDIS_CACHE_DEFAULT_TTL=300
REDIS_CACHE_PROJECT_DETAIL_TTL=600
REDIS_CACHE_PROJECT_LIST_TTL=300
```

**其他Redis配置选项:**

```env
# 带密码的Redis连接
REDIS_URL=redis://:your-password@localhost:6379/0

# 使用特定的数据库编号
REDIS_URL=redis://localhost:6379/1

# 使用Unix socket
REDIS_URL=unix:///var/run/redis/redis.sock

# 远程Redis服务器
REDIS_URL=redis://redis.example.com:6379/0
```

---

## 步骤4: 测试Redis性能

```bash
# 运行性能测试套件
python scripts/test_redis_performance.py
```

**预期输出:**
```
============================================================
Redis性能测试套件
============================================================

Redis URL: redis://localhost:6379/0
✓ Redis连接正常

============================================================
测试1: 基本操作性能
============================================================
写入测试...
✓ 写入1000条数据: 0.2345秒 (4264.37 ops/sec)
读取测试...
✓ 读取1000条数据: 0.1234秒 (8103.73 ops/sec)
删除测试...
✓ 删除1000条数据: 0.0891秒 (11223.45 ops/sec)

测试2: JSON数据操作
============================================================
JSON写入测试...
✓ 写入100个JSON对象: 0.1234秒 (810.23 ops/sec)
  数据大小: 345 bytes
JSON读取测试...
✓ 读取并解析100个JSON对象: 0.0891秒 (1122.34 ops/sec)

测试3: 缓存管理器功能
============================================================
可用缓存前缀:
  - project:list
  - project:detail
  - project:stats
  ...

测试基本功能...
✓ 设置缓存: test:cache:basic
✓ 获取缓存成功: {'id': 1, 'name': '测试数据'}
✓ 删除缓存成功
✓ 批量删除缓存: 删除了 5 个键

测试4: 缓存装饰器
============================================================
第一次调用（未缓存）:
  结果: 5, 耗时: 0.1234秒, 调用次数: 1

第二次调用（从缓存）:
  结果: 5, 耗时: 0.0034秒, 调用次数: 1

第三次调用（不同参数）:
  结果: 7, 耗时: 0.1123秒, 调用次数: 2

✓ 缓存效果显著: 加速 36.29倍

测试5: 并发访问性能
============================================================
使用5个并发线程，每个线程执行100次读写...
✓ 完成500次读写操作: 1.2345秒 (405.03 ops/sec)
✓ 所有操作成功: True

============================================================
测试结果汇总
============================================================
基本操作性能: ✓ 通过
JSON数据操作: ✓ 通过
缓存管理器功能: ✓ 通过
缓存装饰器: ✓ 通过
并发访问性能: ✓ 通过

总计: 5/5 通过

✓ 所有测试通过！Redis缓存功能正常。
```

---

## 步骤5: 重启应用

```bash
# 重启FastAPI应用
uvicorn app.main:app --reload

# 或使用Python模块方式
python -m app.main
```

应用启动时，你会看到缓存模块被自动加载。

---

## 步骤6: 验证缓存是否生效

### 方式1: 查看API响应时间

使用浏览器开发者工具或curl查看响应时间：

```bash
# 第一次请求（未缓存）
time curl http://localhost:8000/api/v1/projects/list?page=1

# 第二次请求（已缓存）
time curl http://localhost:8000/api/v1/projects/list?page=1
```

**预期效果:**
- 第一次请求: 200-500ms
- 第二次请求: 20-50ms (从缓存读取)

### 方式2: 查看Redis数据

```bash
# 连接到Redis
redis-cli

# 查看所有键
KEYS project:*

# 查看具体键的内容
GET project:detail:1

# 查看键的TTL
TTL project:detail:1
```

### 方式3: 检查日志

应用日志会显示缓存命中/未命中信息（如果启用了详细日志）。

---

## 常见问题

### Q1: Redis连接失败

**错误信息:**
```
✗ Redis连接失败: Error connecting to Redis
```

**解决方案:**
```bash
# 1. 确认Redis服务运行
redis-cli ping

# 2. 检查Redis进程
ps aux | grep redis

# 3. 启动Redis服务
brew services start redis  # macOS
sudo systemctl start redis-server  # Linux

# 4. 检查防火墙
sudo ufw allow 6379  # Linux
```

### Q2: 缓存后数据不一致

**解决方案:**

确保在数据更新后使缓存失效：

```python
from app.core.cache import invalidate_cache, CACHE_PREFIXES

# 更新项目后
invalidate_cache(f"{CACHE_PREFIXES['PROJECT_DETAIL']}:{project_id}")
invalidate_cache(f"{CACHE_PREFIXES['PROJECT_LIST']}:*")
invalidate_cache(f"{CACHE_PREFIXES['PROJECT_STATS']}:*")
```

### Q3: 想要清空所有缓存

```bash
# 方式1: 通过Redis命令行
redis-cli FLUSHDB

# 方式2: 通过Python代码
from app.core.cache import cache_manager
cache_manager.clear_all()

# 方式3: 通过API（需要先创建相关端点）
DELETE /api/v1/cache/clear
```

### Q4: 想要禁用缓存

在 `.env` 文件中设置：

```env
REDIS_CACHE_ENABLED=false
```

或直接删除 `REDIS_URL` 配置。

---

## 性能提升预期

| 操作 | 优化前 | 优化后 | 提升 |
|-----|-------|-------|-----|
| 项目列表查询 | 200ms | 40ms | **80%** |
| 项目详情查询 | 500ms | 80ms | **84%** |
| 项目统计查询 | 300ms | 50ms | **83%** |
| 重复API请求 | 200ms | 20ms | **90%** |

---

## 下一步优化

### 1. 应用数据库索引

```bash
# SQLite开发环境
sqlite3 data/app.db < migrations/performance_optimization_sqlite.sql

# MySQL生产环境
mysql -u username -p database_name < migrations/performance_optimization_mysql.sql
```

### 2. 使用查询优化器

在API端点中使用优化后的查询：

```python
from app.services.query_optimizer import ProjectQueryOptimizer

# 优化后的查询
projects, pagination = ProjectQueryOptimizer.get_project_list(
    db=db,
    status='ACTIVE',
    page=1,
    page_size=20
)
```

### 3. 实施前端优化

参考 `docs/PERFORMANCE_OPTIMIZATION_GUIDE.md` 了解前端优化方法。

---

## 监控缓存效果

### 查看Redis统计信息

```bash
redis-cli INFO

# 查看缓存命中率
redis-cli INFO stats | grep keyspace

# 查看内存使用
redis-cli INFO memory | grep used_memory_human
```

### 查看慢查询日志

```bash
redis-cli SLOWLOG GET 10
```

---

## 相关文档

- **完整性能优化指南**: `docs/PERFORMANCE_OPTIMIZATION_GUIDE.md`
- **性能优化总结**: `PERFORMANCE_OPTIMIZATION_SUMMARY.md`
- **Redis官方文档**: https://redis.io/documentation

---

## 技术支持

如果遇到问题：

1. 查看 `docs/PERFORMANCE_OPTIMIZATION_GUIDE.md` 的常见问题部分
2. 运行 `python scripts/test_redis_performance.py` 进行诊断
3. 检查应用日志中的错误信息

---

**最后更新**: 2026-01-11
**文档版本**: v1.0.0
