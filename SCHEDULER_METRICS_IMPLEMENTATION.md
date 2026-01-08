# 调度器指标导出与监控仪表盘实现总结

## 概述

本次实现为调度器系统添加了完整的指标导出和监控功能，包括：
1. 增强的指标收集器（支持历史耗时记录和统计计算）
2. Prometheus 格式指标导出接口
3. 增强的 JSON 格式指标接口（包含聚合数据）
4. 前端监控仪表盘（任务运行表、失败热力图、通知链路指标）

## 实现内容

### 1. 后端实现

#### 1.1 增强指标收集器 (`app/utils/scheduler_metrics.py`)

**新增功能：**
- 历史耗时记录：使用 `deque` 存储每个任务的历史耗时数据（默认最多 1000 条）
- 统计计算：支持计算平均值、P50、P95、P99、最小值、最大值等统计指标
- 线程安全：所有操作都使用锁保护，确保并发安全

**新增方法：**
- `get_statistics(job_id)`: 获取单个任务的统计信息
- `get_all_statistics()`: 获取所有任务的统计信息
- `_calculate_statistics(history)`: 内部方法，计算统计指标

**统计指标包括：**
- `avg_duration_ms`: 平均耗时
- `p50_duration_ms`: P50 耗时（中位数）
- `p95_duration_ms`: P95 耗时
- `p99_duration_ms`: P99 耗时
- `min_duration_ms`: 最小耗时
- `max_duration_ms`: 最大耗时
- `sample_count`: 样本数量

#### 1.2 Prometheus 指标导出接口 (`/api/v1/scheduler/metrics/prometheus`)

**功能：**
- 返回 Prometheus 文本格式的指标
- 包含所有任务的计数器（success/failure）和仪表盘（duration）指标
- 包含统计指标（avg, p50, p95, p99, min, max）
- 每个指标都包含标签（job_id, job_name, owner, category）

**指标类型：**
- `scheduler_job_success_total`: 成功次数计数器
- `scheduler_job_failure_total`: 失败次数计数器
- `scheduler_job_last_duration_ms`: 最后一次执行耗时（仪表盘）
- `scheduler_job_last_run_timestamp`: 最后一次执行时间戳（仪表盘）
- `scheduler_job_duration_avg_ms`: 平均耗时（仪表盘）
- `scheduler_job_duration_p50_ms`: P50 耗时（仪表盘）
- `scheduler_job_duration_p95_ms`: P95 耗时（仪表盘）
- `scheduler_job_duration_p99_ms`: P99 耗时（仪表盘）
- `scheduler_job_duration_min_ms`: 最小耗时（仪表盘）
- `scheduler_job_duration_max_ms`: 最大耗时（仪表盘）

**使用方式：**
```bash
# 直接访问
curl http://localhost:8000/api/v1/scheduler/metrics/prometheus

# 配置 Prometheus scrape_configs
scrape_configs:
  - job_name: 'scheduler'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/scheduler/metrics/prometheus'
```

#### 1.3 增强的 JSON 指标接口 (`/api/v1/scheduler/metrics`)

**新增字段：**
- `job_name`: 任务名称（从配置中获取）
- `owner`: 负责人
- `category`: 类别
- `total_runs`: 总执行次数
- `avg_duration_ms`: 平均耗时
- `p50_duration_ms`: P50 耗时
- `p95_duration_ms`: P95 耗时
- `p99_duration_ms`: P99 耗时
- `min_duration_ms`: 最小耗时
- `max_duration_ms`: 最大耗时
- `sample_count`: 样本数量

**响应示例：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total": 32,
    "metrics": [
      {
        "job_id": "calculate_project_health",
        "job_name": "计算项目健康度",
        "owner": "Backend Platform",
        "category": "Project Health",
        "success_count": 100,
        "failure_count": 2,
        "total_runs": 102,
        "avg_duration_ms": 1250.5,
        "p95_duration_ms": 1800.0,
        "last_status": "success",
        "last_timestamp": "2026-01-15T10:00:00Z"
      }
    ]
  }
}
```

### 2. 前端实现

#### 2.1 API 服务 (`frontend/src/services/api.js`)

**新增 API：**
```javascript
export const schedulerApi = {
    status: () => api.get('/scheduler/status'),
    jobs: () => api.get('/scheduler/jobs'),
    metrics: () => api.get('/scheduler/metrics'),
    metricsPrometheus: () => api.get('/scheduler/metrics/prometheus', { responseType: 'text' }),
    triggerJob: (jobId) => api.post(`/scheduler/jobs/${jobId}/trigger`),
    listServices: () => api.get('/scheduler/services/list'),
};
```

#### 2.2 监控仪表盘页面 (`frontend/src/pages/SchedulerMonitoringDashboard.jsx`)

**功能模块：**

1. **统计卡片**
   - 总任务数
   - 成功率（成功次数/总执行次数）
   - 平均耗时
   - 失败任务数

2. **调度器状态**
   - 运行状态（运行中/已停止）
   - 已注册任务数

3. **通知链路指标**
   - 专门展示 `send_alert_notifications` 任务的执行情况
   - 成功/失败次数、平均耗时、P95 耗时
   - 最后执行时间

4. **任务运行表**
   - 表格展示所有任务的详细指标
   - 支持搜索（按任务ID、名称、负责人）
   - 支持按类别筛选
   - 显示成功率进度条
   - 显示统计指标（平均耗时、P95 耗时）

5. **失败热力图**
   - 按类别统计失败次数
   - 可视化展示失败强度（颜色深浅）
   - 列出每个类别下失败的任务

**特性：**
- 自动刷新（默认 30 秒）
- 手动刷新按钮
- Prometheus 指标导出功能
- 响应式设计，适配不同屏幕尺寸

#### 2.3 路由配置 (`frontend/src/App.jsx`)

**新增路由：**
```javascript
<Route path="/scheduler-monitoring" element={<SchedulerMonitoringDashboard />} />
```

**访问路径：**
- `/scheduler-monitoring`

## 使用指南

### 后端 API 使用

#### 1. 获取 JSON 格式指标
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/scheduler/metrics
```

#### 2. 获取 Prometheus 格式指标
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/v1/scheduler/metrics/prometheus
```

#### 3. 配置 Prometheus 抓取

在 `prometheus.yml` 中添加：
```yaml
scrape_configs:
  - job_name: 'scheduler'
    bearer_token: '<your-token>'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/api/v1/scheduler/metrics/prometheus'
    scrape_interval: 30s
```

### 前端使用

1. **访问监控仪表盘**
   - 登录系统后，访问 `/scheduler-monitoring`
   - 或通过系统管理菜单进入（如果已添加到菜单）

2. **查看任务指标**
   - 在"任务运行表"标签页查看所有任务的详细指标
   - 使用搜索框和类别筛选快速定位任务

3. **分析失败情况**
   - 在"失败热力图"标签页查看按类别统计的失败情况
   - 颜色越深表示失败次数越多

4. **监控通知链路**
   - 查看"通知链路指标"卡片，了解消息推送服务的执行情况

5. **导出 Prometheus 指标**
   - 点击"Prometheus 导出"按钮下载指标文件
   - 可用于配置 Prometheus 或进行离线分析

## 技术细节

### 统计计算算法

**百分位数计算：**
```python
def percentile(data: List[float], p: float) -> float:
    """Calculate percentile value."""
    if not data:
        return 0.0
    k = (len(data) - 1) * p
    f = int(k)
    c = k - f
    if f + 1 < len(data):
        return data[f] + c * (data[f + 1] - data[f])
    return data[f]
```

使用线性插值方法计算百分位数，确保结果的准确性。

### 内存管理

- 使用 `deque` 的 `maxlen` 参数限制历史记录数量（默认 1000）
- 当记录超过限制时，自动删除最旧的记录
- 避免内存无限增长

### 性能考虑

- 统计计算在锁外进行，避免长时间持有锁
- 使用深拷贝确保数据快照的一致性
- 前端自动刷新间隔可配置（默认 30 秒）

## 与 SCHEDULER_MONITORING_GUIDE.md 的对应关系

本次实现完全符合 `docs/SCHEDULER_MONITORING_GUIDE.md` 中的蓝图：

1. ✅ **任务运行表**：展示 job_id、owner、最近运行状态、耗时 P95
2. ✅ **告警热力图**：统计一天内失败次数，阈值报警（通过颜色深浅表示）
3. ✅ **通知链路监控**：展示 `send_alert_notifications` 成功率与外部网关响应时间
4. ✅ **实时指标卡片**：消费 `/scheduler/metrics` 接口的 snapshot，快速查看成功/失败次数、最近耗时

## 后续优化建议

1. **持久化存储**
   - 考虑将指标数据持久化到数据库，支持历史查询
   - 可以定期清理旧数据，只保留最近 N 天的数据

2. **告警规则**
   - 基于指标数据设置告警规则（如失败率超过阈值、耗时超过阈值）
   - 集成到现有的告警系统中

3. **趋势分析**
   - 添加时间序列图表，展示任务执行趋势
   - 支持按时间段对比分析

4. **任务详情页**
   - 点击任务可以查看详细的历史执行记录
   - 显示每次执行的耗时、状态、错误信息等

5. **批量操作**
   - 支持批量启用/禁用任务
   - 支持批量触发任务执行

## 测试建议

1. **后端测试**
   - 测试指标收集的准确性
   - 测试统计计算的正确性
   - 测试 Prometheus 格式输出的有效性

2. **前端测试**
   - 测试页面加载和数据显示
   - 测试搜索和筛选功能
   - 测试自动刷新功能
   - 测试 Prometheus 导出功能

3. **集成测试**
   - 测试 Prometheus 抓取配置
   - 测试在 Grafana 中创建仪表盘
   - 测试告警规则配置

## 总结

本次实现为调度器系统提供了完整的监控和指标导出能力，满足了运维和开发团队对任务执行情况的监控需求。通过 Prometheus 格式的指标导出，可以轻松集成到现有的监控体系中，实现统一的监控和告警。



