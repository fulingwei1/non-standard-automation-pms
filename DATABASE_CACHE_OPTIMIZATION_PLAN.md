# 数据库缓存与查询优化方案

## 一、现状分析

### 1.1 已有基础设施

✅ **缓存层已实现**：
- `app/services/cache_service.py` - 完整的缓存服务
- `app/utils/redis_client.py` - Redis客户端
- `app/core/config.py` - Redis配置
- `requirements.txt` - redis==5.2.0

✅ **数据库配置**：
- SQLAlchemy 2.0.36
- SQLite（开发）/ MySQL（生产）
- 连接池配置

### 1.2 存在的问题

❌ **缓存未集成**：
- API端点未使用缓存服务
- 高频查询每次都访问数据库
- 数据更新时缓存未失效

❌ **查询未优化**：
- 存在N+1查询问题
- 缺少预加载策略（joinedload/selectinload）
- 复杂查询未优化

❌ **缺少监控**：
- 无查询性能统计
- 无缓存命中率监控
- 无慢查询日志

---

## 二、优化目标

### 2.1 性能指标

| 指标 | 当前 | 目标 | 提升 |
|------|------|------|------|
| 项目列表响应时间 | ~500ms | <100ms | 80%↓ |
| 项目详情响应时间 | ~800ms | <150ms | 81%↓ |
| 缓存命中率 | 0% | >70% | - |
| 数据库QPS | 100 | <30 | 70%↓ |

### 2.2 功能目标

- [ ] 高频查询接口集成缓存
- [ ] 实现缓存失效策略
- [ ] 优化查询预加载
- [ ] 添加性能监控
- [ ] 实现缓存预热

---

## 三、优化方案

### 3.1 缓存集成策略

#### 3.1.1 缓存层级

```
┌─────────────────────────────────────┐
│         API Request                │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│    L1: Memory Cache (进程级)        │
│    - 响应时间: <1ms                 │
│    - TTL: 5分钟                    │
│    - 容量: 1000条                  │
└─────────────┬───────────────────────┘
              │ Miss
              ▼
┌─────────────────────────────────────┐
│    L2: Redis Cache (分布式)         │
│    - 响应时间: <10ms                │
│    - TTL: 可配置                   │
│    - 容量: 无限制                  │
└─────────────┬───────────────────────┘
              │ Miss
              ▼
┌─────────────────────────────────────┐
│    Database (SQLite/MySQL)          │
│    - 响应时间: 50-500ms             │
│    - 使用查询优化                   │
└─────────────────────────────────────┘
```

#### 3.1.2 缓存粒度

| 缓存类型 | 键格式 | TTL | 失效策略 |
|----------|--------|-----|----------|
| 项目列表 | `project:list:{hash(filters)}` | 300s | 项目增删改时失效 |
| 项目详情 | `project:detail:{id}` | 600s | 项目更新时失效 |
| 项目统计 | `project:statistics:{hash(filters)}` | 600s | 定时刷新 |
| 用户权限 | `user:permissions:{user_id}` | 3600s | 权限变更时失效 |
| 部门数据 | `department:tree` | 1800s | 部门变更时失效 |

### 3.2 查询优化策略

#### 3.2.1 预加载策略

```python
# 项目列表查询 - 使用selectinload
def get_project_list(db: Session, filters: dict):
    return db.query(Project)\
        .options(
            selectinload(Project.customer),           # 预加载客户
            selectinload(Project.pm_user),           # 预加载项目经理
            selectinload(Project.department),        # 预加载部门
            selectinload(Project.machines),           # 预加载设备
        )\
        .filter_by(**filters)\
        .all()

# 项目详情查询 - 使用joinedload
def get_project_detail(db: Session, project_id: int):
    return db.query(Project)\
        .options(
            joinedload(Project.customer),
            joinedload(Project.pm_user),
            joinedload(Project.department),
            joinedload(Project.members).selectinload(ProjectMember.user),
            joinedload(Project.machines).selectinload(Machine.stages),
            joinedload(Project.payment_plans),
            joinedload(Project.milestones),
        )\
        .filter(Project.id == project_id)\
        .first()
```

#### 3.2.2 索引优化

```sql
-- 项目表索引
CREATE INDEX idx_projects_stage_status ON projects(stage, status);
CREATE INDEX idx_projects_customer_id ON projects(customer_id);
CREATE INDEX idx_projects_pm_id ON projects(pm_id);
CREATE INDEX idx_projects_dates ON projects(planned_start_date, planned_end_date);
CREATE INDEX idx_projects_active_archived ON projects(is_active, is_archived);

-- 任务表索引
CREATE INDEX idx_tasks_project_status ON tasks(project_id, status);
CREATE INDEX idx_tasks_assignee ON tasks(assigned_to);

-- 物料表索引
CREATE INDEX idx_materials_code ON materials(material_code);
CREATE INDEX idx_materials_category ON materials(category_id);
```

#### 3.2.3 查询优化规则

1. **避免N+1查询**：使用joinedload/selectinload预加载关联
2. **限制返回字段**：使用`with_entities`只查询需要的列
3. **分页优化**：使用`offset().limit()`配合索引
4. **复杂查询拆分**：将大查询拆分为多个小查询并行执行
5. **使用聚合**：数据库层完成聚合，减少应用层处理

### 3.3 缓存失效策略

#### 3.3.1 主动失效

```python
# 创建/更新项目时失效相关缓存
def update_project(project_id: int, data: dict):
    # 1. 更新数据库
    project = db.query(Project).filter(Project.id == project_id).first()
    for key, value in data.items():
        setattr(project, key, value)
    db.commit()

    # 2. 失效项目详情缓存
    cache_service.invalidate_project_detail(project_id)

    # 3. 失效项目列表缓存
    cache_service.invalidate_project_list()

    # 4. 失效项目统计缓存
    cache_service.invalidate_project_statistics()
```

#### 3.3.2 定时刷新

```python
# 定时任务：刷新统计数据
@ScheduledTask(cron="0 */5 * * *")  # 每5分钟
def refresh_statistics_cache():
    """定期刷新项目统计数据缓存"""
    from app.services.project_statistics_service import get_dashboard_stats

    stats = get_dashboard_stats(db)
    cache_service.set_project_statistics(stats, expire_seconds=600)
```

### 3.4 监控与告警

#### 3.4.1 缓存监控

```python
# 缓存统计API
@router.get("/cache/stats")
def get_cache_stats():
    stats = cache_service.get_stats()
    return {
        "hits": stats["hits"],
        "misses": stats["misses"],
        "hit_rate": stats["hit_rate"],
        "cache_type": stats["cache_type"],
        "memory_cache_size": stats["memory_cache_size"],
    }
```

#### 3.4.2 慢查询监控

```python
# 查询性能装饰器
def log_query_time(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start

        if elapsed > 0.5:  # 超过500ms记录
            logger.warning(f"慢查询: {func.__name__} 耗时 {elapsed:.3f}s")

        return result
    return wrapper
```

---

## 四、实施计划

### 阶段一：核心缓存集成（Week 1）

**目标**：将高频查询接口集成缓存

- [x] 缓存服务已实现
- [ ] 在`projects.py`中集成项目列表缓存
- [ ] 在`projects.py`中集成项目详情缓存
- [ ] 实现缓存失效逻辑
- [ ] 添加缓存统计端点

**验收标准**：
- 缓存命中率达到50%以上
- 项目列表响应时间<150ms
- 项目详情响应时间<200ms

### 阶段二：查询优化（Week 2）

**目标**：优化数据库查询性能

- [ ] 添加预加载策略到所有查询
- [ ] 创建数据库索引
- [ ] 优化复杂查询
- [ ] 添加查询性能监控

**验收标准**：
- 消除N+1查询
- 查询响应时间提升50%
- 慢查询日志完整

### 阶段三：高级优化（Week 3）

**目标**：实现高级优化功能

- [ ] 实现缓存预热
- [ ] 实现查询结果分页缓存
- [ ] 添加缓存监控面板
- [ ] 实现自动缓存过期清理

**验收标准**：
- 缓存命中率达到70%以上
- 系统启动后缓存命中率快速提升
- 监控面板实时显示缓存状态

---

## 五、风险评估

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|----------|
| Redis单点故障 | 高 | 低 | 使用Redis哨兵/集群 |
| 缓存雪崩 | 中 | 低 | 设置随机TTL偏移 |
| 缓存穿透 | 中 | 低 | 使用布隆过滤器 |
| 数据一致性 | 高 | 中 | 实现缓存失效补偿 |
| 内存溢出 | 低 | 低 | 限制缓存大小 |

---

## 六、配置说明

### 6.1 环境变量

```bash
# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_ENABLED=true
REDIS_CACHE_DEFAULT_TTL=300
REDIS_CACHE_PROJECT_DETAIL_TTL=600
REDIS_CACHE_PROJECT_LIST_TTL=300

# 数据库配置
DATABASE_URL=mysql://user:pass@localhost:3306/dbname
SQLITE_DB_PATH=data/app.db
```

### 6.2 缓存配置

```python
# app/core/config.py

# Redis配置
REDIS_URL: Optional[str] = None
REDIS_CACHE_ENABLED: bool = True
REDIS_CACHE_DEFAULT_TTL: int = 300  # 5分钟
REDIS_CACHE_PROJECT_DETAIL_TTL: int = 600  # 10分钟
REDIS_CACHE_PROJECT_LIST_TTL: int = 300  # 5分钟
```

---

## 七、测试方案

### 7.1 性能测试

```bash
# 使用Locust进行压力测试
locust -f tests/performance/cache_performance_test.py

# 目标：
# - 并发100用户
# - 响应时间<200ms
# - 错误率<0.1%
```

### 7.2 缓存测试

```python
def test_cache_hit_rate():
    """测试缓存命中率"""
    # 第一次请求（缓存未命中）
    resp1 = client.get("/api/v1/projects/")
    assert resp1.json()["from_cache"] == False

    # 第二次请求（缓存命中）
    resp2 = client.get("/api/v1/projects/")
    assert resp2.json()["from_cache"] == True

    # 获取缓存统计
    stats = cache_service.get_stats()
    assert stats["hit_rate"] > 50
```

### 7.3 数据一致性测试

```python
def test_cache_invalidation():
    """测试缓存失效"""
    # 获取项目详情
    resp1 = client.get(f"/api/v1/projects/{project_id}")
    old_name = resp1.json()["project_name"]

    # 更新项目
    client.put(f"/api/v1/projects/{project_id}", json={"project_name": "新名称"})

    # 再次获取（应该返回新数据）
    resp2 = client.get(f"/api/v1/projects/{project_id}")
    assert resp2.json()["project_name"] == "新名称"
    assert resp2.json()["project_name"] != old_name
```

---

## 八、运维指南

### 8.1 监控指标

| 指标 | 告警阈值 | 处理方式 |
|------|----------|----------|
| 缓存命中率 | <50% | 检查TTL配置 |
| Redis内存使用率 | >80% | 扩容或清理 |
| 数据库连接数 | >80% | 检查连接泄漏 |
| 慢查询数 | >10/min | 优化查询 |

### 8.2 故障处理

**Redis故障**：
1. 自动降级到内存缓存
2. 监控告警
3. 重启或扩容Redis

**缓存雪崩**：
1. 设置TTL随机偏移
2. 使用互斥锁重建缓存
3. 限流保护

**数据不一致**：
1. 实现缓存版本号
2. 定期全量刷新
3. 手动清除缓存

---

## 九、参考资料

- [Redis官方文档](https://redis.io/documentation)
- [SQLAlchemy性能优化](https://docs.sqlalchemy.org/en/20/orm/persistence_techniques.html)
- [FastAPI缓存最佳实践](https://fastapi.tiangolo.com/advanced/async-sql-databases/)

---

## 十、联系方式

如有问题，请联系开发团队。
