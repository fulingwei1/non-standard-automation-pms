# 性能优化指南

> **最后更新**: 2026-01-11
> **适用版本**: v1.0.0+

本文档介绍项目性能优化的配置和使用方法。

---

## 目录

1. [Redis缓存配置](#redis缓存配置)
2. [数据库索引优化](#数据库索引优化)
3. [API响应压缩](#api响应压缩)
4. [前端性能优化](#前端性能优化)
5. [查询优化技巧](#查询优化技巧)
6. [性能监控](#性能监控)

---

## Redis缓存配置

### 1. 安装和配置Redis

#### 步骤1: 安装Redis

**macOS (使用Homebrew):**
```bash
brew install redis
brew services start redis
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Windows:**
下载并安装 [Redis for Windows](https://github.com/microsoftarchive/redis/releases)

#### 步骤2: 配置Redis

运行配置向导：
```bash
python scripts/setup_redis.py
```

脚本会自动：
- 测试Redis连接
- 生成环境变量配置
- 验证Redis功能

#### 步骤3: 设置环境变量

在 `.env` 文件中添加：
```env
# Redis配置
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_ENABLED=true
REDIS_CACHE_DEFAULT_TTL=300
REDIS_CACHE_PROJECT_DETAIL_TTL=600
REDIS_CACHE_PROJECT_LIST_TTL=300
```

**带密码的Redis连接:**
```env
REDIS_URL=redis://:your-password@localhost:6379/0
```

**使用Unix socket:**
```env
REDIS_URL=unix:///var/run/redis/redis.sock
```

#### 步骤4: 验证配置

运行性能测试：
```bash
python scripts/test_redis_performance.py
```

测试包括：
- 基本操作性能
- JSON数据操作
- 缓存管理器功能
- 缓存装饰器
- 并发访问性能

### 2. 使用Redis缓存

#### 方式1: 使用缓存装饰器

```python
from app.core.cache import cached, CACHE_PREFIXES

@cached(prefix=CACHE_PREFIXES['PROJECT_DETAIL'], ttl=600)
def get_project_detail(project_id: int, db: Session):
    return db.query(Project).filter(Project.id == project_id).first()
```

#### 方式2: 手动缓存管理

```python
from app.core.cache import cache_manager, CACHE_PREFIXES

# 设置缓存
cache_key = f"{CACHE_PREFIXES['PROJECT_DETAIL']}:{project_id}"
cache_manager.set(cache_key, project_data, ttl=600)

# 获取缓存
cached_data = cache_manager.get(cache_key)

# 删除缓存
cache_manager.delete(cache_key)

# 批量删除
cache_manager.delete_pattern("project:*")
```

#### 方式3: 缓存失效策略

**主动失效（推荐）:**
```python
from app.core.cache import invalidate_cache

@router.put("/{project_id}")
async def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    # 更新数据库
    project = db.query(Project).filter(Project.id == project_id).first()
    # ... 更新逻辑 ...

    # 使缓存失效
    invalidate_cache(f"{CACHE_PREFIXES['PROJECT_DETAIL']}:{project_id}")
    invalidate_cache(f"{CACHE_PREFIXES['PROJECT_LIST']}:*")

    return project
```

**被动失效（TTL）:**
```python
@cached(prefix="project:detail", ttl=600)  # 10分钟后自动失效
def get_project_detail(project_id: int, db: Session):
    ...
```

### 3. 缓存最佳实践

✅ **推荐做法:**
- 对读多写少的数据使用缓存
- 设置合理的TTL（建议5-10分钟）
- 更新数据后主动使缓存失效
- 使用有意义的缓存键前缀
- 对列表查询进行分页缓存

❌ **避免做法:**
- 对实时性要求高的数据使用缓存
- 缓存过大的对象（>1MB）
- 设置过长的TTL（超过1小时）
- 缓存敏感数据（密码、密钥等）
- 忽略缓存失效逻辑

---

## 数据库索引优化

### 1. 应用索引优化脚本

#### SQLite开发环境:
```bash
sqlite3 data/app.db < migrations/performance_optimization_sqlite.sql
```

#### MySQL生产环境:
```bash
mysql -u username -p database_name < migrations/performance_optimization_mysql.sql
```

### 2. 索引优化范围

已优化的索引包括：

**项目相关:**
- 项目编码、名称、状态、阶段、健康度
- 项目经理、客户
- 创建时间

**物料相关:**
- 物料编码、名称、分类、类型
- 供应商

**采购相关:**
- 采购订单编号、供应商、状态
- 收货单

**任务相关:**
- 项目、状态、负责人、优先级
- 截止日期

**复合索引:**
- 项目状态+阶段
- 项目健康度+状态
- 任务状态+负责人

### 3. 索引使用建议

**查询优化示例:**

```python
# ❌ 低效查询（全表扫描）
projects = db.query(Project).filter(
    Project.status == 'ACTIVE',
    Project.stage == 'S2'
).all()

# ✅ 高效查询（使用复合索引）
projects = db.query(Project).filter(
    Project.status == 'ACTIVE',
    Project.stage == 'S2'
).all()  # 使用 idx_projects_status_stage 索引
```

**避免N+1查询:**

```python
# ❌ 低效（N+1查询）
projects = db.query(Project).all()
for project in projects:
    print(project.customer.name)  # 每次都查询客户表

# ✅ 高效（预加载关联）
from sqlalchemy.orm import joinedload

projects = db.query(Project).options(
    joinedload(Project.customer)
).all()
for project in projects:
    print(project.customer.name)  # 已经加载，不会额外查询
```

### 4. 使用查询优化器

```python
from app.services.query_optimizer import ProjectQueryOptimizer

# 获取项目列表（优化版本）
projects, pagination = ProjectQueryOptimizer.get_project_list(
    db=db,
    status='ACTIVE',
    stage='S2',
    page=1,
    page_size=20,
    sort_by='created_at',
    sort_order='desc'
)

# 获取项目详情（优化版本）
project = ProjectQueryOptimizer.get_project_detail(
    db=db,
    project_id=project_id,
    include_members=True,
    include_stages=True,
    include_milestones=True
)
```

---

## API响应压缩

### 1. 已启用Gzip压缩

在 `app/main.py` 中已配置：
```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 2. 压缩效果

- **响应大小 > 1KB**: 自动压缩
- **压缩率**: 通常60-80%
- **CPU开销**: 极小
- **兼容性**: 所有现代浏览器

### 3. 监控压缩效果

查看响应头：
```
Content-Encoding: gzip
Content-Type: application/json
```

---

## 前端性能优化

### 1. 虚拟滚动（大数据列表）

**适用场景:**
- 项目列表（>100条）
- 物料列表（>1000条）
- 采购订单列表（>500条）

**使用方法:**

```jsx
import { VirtualScroll } from '../components/VirtualScroll';

function ProjectList({ projects }) {
  return (
    <VirtualScroll
      items={projects}
      itemHeight={60}
      height={600}
      renderItem={(project, index) => (
        <div key={project.id} className="p-4 border-b">
          {project.name}
        </div>
      )}
    />
  );
}
```

### 2. API请求缓存

```jsx
import { cachedRequest, debounce, throttle } from '../lib/api-utils';

// 带缓存的请求
const fetchProjects = async () => {
  const { data, fromCache } = await cachedRequest(
    '/api/v1/projects/list',
    { params: { page: 1, page_size: 20 } },
    { enabled: true, ttl: 300000 }  // 5分钟缓存
  );

  if (fromCache) {
    console.log('数据来自缓存');
  }
  return data;
};

// 防抖（避免频繁请求）
const handleSearch = debounce((keyword) => {
  searchProjects(keyword);
}, 300);

// 节流（限制请求频率）
const handleScroll = throttle(() => {
  loadMoreData();
}, 1000);
```

### 3. 图片优化

```jsx
import { OptimizedImage, Avatar } from '../components/OptimizedImage';

// 懒加载图片
<OptimizedImage
  src="/path/to/image.jpg"
  alt="描述"
  loading="lazy"
  width={400}
  height={300}
/>

// 头像组件
<Avatar
  src="/avatar.jpg"
  name="张三"
  size="md"
  onClick={() => console.log('clicked')}
/>
```

### 4. 代码分割

```jsx
// 懒加载路由组件
const ProjectList = lazy(() => import('./pages/ProjectList'));
const ProjectDetail = lazy(() => import('./pages/ProjectDetail'));

function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/projects" element={<ProjectList />} />
        <Route path="/projects/:id" element={<ProjectDetail />} />
      </Routes>
    </Suspense>
  );
}
```

---

## 查询优化技巧

### 1. 只查询需要的字段

```python
# ❌ 查询所有字段
projects = db.query(Project).all()

# ✅ 只查询需要的字段
projects = db.query(
    Project.id,
    Project.code,
    Project.name,
    Project.status
).all()
```

### 2. 使用聚合函数减少数据传输

```python
# ❌ 先获取所有数据再统计
projects = db.query(Project).all()
total = len(projects)
active_count = sum(1 for p in projects if p.status == 'ACTIVE')

# ✅ 直接使用聚合函数
from sqlalchemy import func

total = db.query(func.count(Project.id)).scalar()
active_count = db.query(func.count(Project.id)).filter(
    Project.status == 'ACTIVE'
).scalar()
```

### 3. 分页查询大数据集

```python
from app.services.query_optimizer import QueryOptimizer

# ❌ 一次性加载所有数据
all_projects = db.query(Project).all()

# ✅ 分页加载
query = db.query(Project)
query = QueryOptimizer.paginate(query, page=1, page_size=20)
projects = query.all()
```

### 4. 使用索引提示

```python
# 强制使用特定索引（谨慎使用）
from sqlalchemy import Index

# 在模型定义时指定索引
class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        Index('idx_projects_status_stage', 'status', 'stage'),
    )
```

---

## 性能监控

### 1. 日志监控

在 `.env` 中启用SQL日志：
```env
# 设置数据库echo为True
```

### 2. 慢查询日志

```python
# 在app/main.py中添加中间件
from time import time

@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time()
    response = await call_next(request)
    process_time = time() - start_time

    # 记录慢请求（>1秒）
    if process_time > 1.0:
        print(f"慢请求: {request.url.path} 耗时: {process_time:.2f}秒")

    response.headers["X-Process-Time"] = str(process_time)
    return response
```

### 3. Redis监控

```bash
# Redis命令行监控
redis-cli

# 查看信息
INFO

# 查看慢查询日志
SLOWLOG GET 10

# 查看内存使用
MEMORY STATS
```

### 4. 性能测试脚本

```bash
# 测试Redis性能
python scripts/test_redis_performance.py

# 测试API性能
ab -n 1000 -c 10 http://localhost:8000/api/v1/projects/list
```

---

## 性能优化检查清单

### 后端优化

- [ ] 启用Redis缓存
- [ ] 应用数据库索引
- [ ] 启用Gzip压缩
- [ ] 使用查询优化器
- [ ] 避免N+1查询
- [ ] 实现缓存失效策略
- [ ] 配置慢查询日志
- [ ] 监控Redis性能

### 前端优化

- [ ] 实现虚拟滚动
- [ ] 添加请求缓存
- [ ] 使用防抖/节流
- [ ] 优化图片加载
- [ ] 实现代码分割
- [ ] 懒加载路由
- [ ] 优化包大小

### 数据库优化

- [ ] 创建必要的索引
- [ ] 优化慢查询
- [ ] 使用连接池
- [ ] 配置合理的超时时间
- [ ] 定期维护数据库

---

## 常见问题

### Q1: Redis连接失败怎么办？

**A:** 检查以下几点：
1. Redis服务是否启动
2. 连接URL是否正确
3. 防火墙是否允许连接
4. 运行 `python scripts/setup_redis.py` 测试连接

### Q2: 缓存后数据不一致怎么办？

**A:** 确保在数据更新后调用缓存失效：
```python
invalidate_cache(f"project:detail:{project_id}")
invalidate_cache("project:list:*")
```

### Q3: 如何优化慢查询？

**A:** 使用以下步骤：
1. 启用SQL日志
2. 识别慢查询
3. 使用EXPLAIN分析查询计划
4. 添加或优化索引
5. 重构查询逻辑

### Q4: 虚拟滚动不生效怎么办？

**A:** 检查以下几点：
1. 确保 `itemHeight` 参数正确
2. 容器必须有固定高度
3. `items` 数组不为空
4. `renderItem` 函数返回有效的JSX

---

## 参考资源

- [Redis官方文档](https://redis.io/documentation)
- [FastAPI性能优化](https://fastapi.tiangolo.com/advanced/)
- [SQLAlchemy性能优化](https://docs.sqlalchemy.org/en/14/core/performance.html)
- [React性能优化](https://react.dev/learn/render-and-commit)
- [Web性能优化](https://web.dev/fast/)

---

**最后更新**: 2026-01-11
**文档版本**: v1.0.0
