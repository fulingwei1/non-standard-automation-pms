# Performance Optimization Guide

## 数据库优化

### 1. 索引优化

```sql
-- 项目表索引
CREATE INDEX idx_project_stage ON projects(stage);
CREATE INDEX idx_project_health ON projects(health);
CREATE INDEX idx_project_pm ON projects(pm_id);
CREATE INDEX idx_project_customer ON projects(customer_id);
CREATE INDEX idx_project_created_at ON projects(created_at DESC);

-- 任务表索引
CREATE INDEX idx_task_project ON task_unified(project_id);
CREATE INDEX idx_task_assignee ON task_unified(assignee_id);
CREATE INDEX idx_task_status ON task_unified(status);
CREATE INDEX idx_task_deadline ON task_unified(deadline);
CREATE INDEX idx_task_importance ON task_unified(task_importance);

-- 工时表索引
CREATE INDEX idx_timesheet_user ON timesheets(user_id);
CREATE INDEX idx_timesheet_project ON timesheets(project_id);
CREATE INDEX idx_timesheet_date ON timesheets(work_date);
CREATE INDEX idx_timesheet_status ON timesheets(approval_status);

-- 预警表索引
CREATE INDEX idx_alert_project ON alert_records(project_id);
CREATE INDEX idx_alert_level ON alert_records(alert_level);
CREATE INDEX idx_alert_created ON alert_records(created_at DESC);
CREATE INDEX idx_alert_resolved ON alert_records(resolved_at);
```

### 2. 查询优化策略

**使用批量操作替代单条操作：**
```python
# 差：循环单条插入
for item in items:
    db.add(item)
    db.commit()

# 好：批量插入
db.bulk_save_objects(items)
db.commit()
```

**使用 selectinload/joinedload 预加载关联：**
```python
from sqlalchemy.orm import selectinload, joinedload

# 项目列表加载关联数据
projects = (
    session.query(Project)
    .options(
        selectinload(Project.members),
        selectinload(Project.milestones),
        joinedload(Project.customer)
    )
    .all()
)
```

**分页查询使用游标：**
```python
# 传统分页（深度分页性能差）
page = session.query(Project).offset(1000).limit(20).all()

# 游标分页（性能更好）
last_id = last_project_id if last_project_id else 0
projects = (
    session.query(Project)
    .filter(Project.id > last_id)
    .order_by(Project.id)
    .limit(20)
    .all()
)
```

### 3. 连接池配置

```python
# MySQL 连接池优化
engine = create_engine(
    DATABASE_URL,
    pool_size=20,          # 连接池大小
    max_overflow=40,       # 最大溢出连接数
    pool_pre_ping=True,    # 连接健康检查
    pool_recycle=3600,     # 连接回收时间（秒）
    echo=False             # 生产环境关闭 SQL 日志
)
```

## 缓存优化

### 1. Redis 缓存策略

```python
# 缓存键命名规范
CACHE_KEY_PREFIX = "pms"
CACHE_PROJECT_DETAIL = f"{CACHE_KEY_PREFIX}:project:detail"
CACHE_PROJECT_LIST = f"{CACHE_KEY_PREFIX}:project:list"
CACHE_USER_PERMISSIONS = f"{CACHE_KEY_PREFIX}:user:permissions"

# 缓存过期时间配置
CACHE_TTL_SHORT = 300      # 5分钟
CACHE_TTL_MEDIUM = 600     # 10分钟
CACHE_TTL_LONG = 3600      # 1小时
CACHE_TTL_VERY_LONG = 86400  # 24小时
```

### 2. 缓存穿透防护

```python
def get_project_with_cache(project_id: int):
    cache_key = f"{CACHE_PROJECT_DETAIL}:{project_id}"

    # 尝试从缓存获取
    cached = redis_client.get(cache_key)
    if cached is not None:
        if cached == "NULL":
            return None
        return json.loads(cached)

    # 查询数据库
    project = db.query(Project).filter(Project.id == project_id).first()

    # 写入缓存（空值也缓存，防止穿透）
    value = json.dumps(project.to_dict()) if project else "NULL"
    redis_client.setex(cache_key, CACHE_TTL_MEDIUM, value)

    return project
```

### 3. 缓存雪崩防护

```python
import random

def set_cache_with_jitter(key: str, value: str, ttl: int):
    """添加随机过期时间，防止缓存雪崩"""
    jitter = random.randint(0, int(ttl * 0.1))  # 10% 的随机偏移
    redis_client.setex(key, ttl + jitter, value)
```

## API 性能优化

### 1. 响应压缩

```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 2. 异步端点

```python
@router.get("/projects/{project_id}")
async def get_project(project_id: int, db: Session = Depends(get_db)):
    # 使用异步数据库驱动（如 asyncpg）
    project = await db.execute(
        select(Project).where(Project.id == project_id)
    )
    return project
```

### 3. 分页限制

```python
# app/core/config.py
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# 强制执行分页限制
page_size = min(request.page_size, MAX_PAGE_SIZE)
```

## 前端性能优化

### 1. 代码分割

```javascript
// React Router 懒加载
const ProjectList = lazy(() => import('./pages/ProjectList'));
const ProjectDetail = lazy(() => import('./pages/ProjectDetail'));

<Suspense fallback={<Loading />}>
  <Route path="/projects" element={<ProjectList />} />
  <Route path="/projects/:id" element={<ProjectDetail />} />
</Suspense>
```

### 2. 虚拟滚动

```javascript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={projects.length}
  itemSize={50}
>
  {({ index, style }) => (
    <div style={style}>
      <ProjectItem project={projects[index]} />
    </div>
  )}
</FixedSizeList>
```

### 3. 请求优化

```javascript
// 请求防抖
import { debounce } from 'lodash';

const handleSearch = debounce((keyword) => {
  searchProjects(keyword);
}, 300);

// 请求节流
import { throttle } from 'lodash';

const handleScroll = throttle(() => {
  loadMoreProjects();
}, 1000);
```

## 监控和日志

### 1. 性能指标采集

```python
import time
from functools import wraps

def measure_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start

        # 记录慢查询
        if duration > 1.0:
            logger.warning(f"Slow function {func.__name__}: {duration:.2f}s")

        # 发送到监控系统
        send_metric(f"function.{func.__name__}.duration", duration)

        return result
    return wrapper
```

### 2. 结构化日志

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "project_created",
    project_id=project.id,
    user_id=user.id,
    duration_ms=duration
)
```

## 扩展性考虑

### 1. 微服务拆分

建议按业务模块拆分：

```
┌─────────────────────────────────────┐
│         API Gateway                  │
└──────────────┬──────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌───────┐ ┌────────┐ ┌────────┐
│ Sales │ │Project │ │Procure │
│Service│ │Service │ │Service │
└───────┘ └────────┘ └────────┘
    │          │          │
    └──────────┼──────────┘
               ▼
         ┌───────────┐
         │  Message  │
         │   Queue   │
         └───────────┘
```

### 2. 消息队列集成

```python
# 使用 Celery 处理异步任务
from celery import Celery

celery_app = Celery('pms', broker='redis://localhost:6379/0')

@celery_app.task
def send_notification_async(user_id: int, message: str):
    """异步发送通知"""
    send_notification(user_id, message)
```

### 3. 读写分离

```python
# 配置主从数据库
MASTER_DB_URL = "mysql+pymysql://user:pass@master:3306/pms"
SLAVE_DB_URL = "mysql+pymysql://user:pass@slave:3306/pms"

# 读操作使用从库
read_engine = create_engine(SLAVE_DB_URL)

# 写操作使用主库
write_engine = create_engine(MASTER_DB_URL)
```

### 4. 水平扩展

```python
# 使用一致性哈希进行分片
from hashlib import sha256

def get_shard_key(project_id: int, shard_count: int = 4):
    hash_value = sha256(str(project_id).encode()).hexdigest()
    return int(hash_value, 16) % shard_count

# 根据分片键路由到不同的数据库
shard_index = get_shard_key(project.id, 4)
engine = engines[shard_index]
```

## 性能测试脚本

```python
# tests/performance/load_test.py
import locust
from locust import HttpUser, task, between

class PMSUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def get_projects(self):
        self.client.get("/api/v1/projects")

    @task(2)
    def get_project_detail(self):
        project_id = random.randint(1, 100)
        self.client.get(f"/api/v1/projects/{project_id}")

    @task(1)
    def create_project(self):
        self.client.post("/api/v1/projects", json={
            "project_name": "测试项目",
            "customer_id": 1
        })
```
