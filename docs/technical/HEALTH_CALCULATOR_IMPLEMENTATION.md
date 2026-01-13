# 健康度自动计算服务实现总结

## 已完成的工作

### 1. 核心服务实现 ✅

**文件**: `app/services/health_calculator.py`

- ✅ `HealthCalculator` 类：完整的健康度计算逻辑
- ✅ 支持单个项目计算
- ✅ 支持批量计算
- ✅ 支持健康度详情诊断
- ✅ 自动记录状态变更历史

### 2. 定时任务框架 ✅

**文件**: `app/utils/scheduler.py`

- ✅ APScheduler 调度器配置
- ✅ 任务监听和错误处理
- ✅ 三个定时任务：
  - 每小时计算健康度（整点）
  - 每天凌晨2点生成健康度快照
  - 每天上午9点执行规格匹配检查

**文件**: `app/utils/scheduled_tasks.py`

- ✅ `calculate_project_health()`: 健康度计算任务
- ✅ `daily_health_snapshot()`: 健康度快照任务
- ✅ 错误处理和日志记录

### 3. 应用集成 ✅

**文件**: `app/main.py`

- ✅ 应用启动时自动初始化调度器
- ✅ 应用关闭时优雅关闭调度器
- ✅ 可通过环境变量 `ENABLE_SCHEDULER` 控制是否启用

### 4. API 端点集成 ✅

**文件**: `app/api/v1/endpoints/projects.py`

- ✅ 项目状态更新时自动触发健康度计算
- ✅ `POST /projects/{project_id}/health/calculate`: 手动触发健康度计算
- ✅ `GET /projects/{project_id}/health/details`: 获取健康度详细信息
- ✅ `POST /projects/health/batch-calculate`: 批量计算健康度

### 5. Schema 定义 ✅

**文件**: `app/schemas/project.py`

- ✅ `ProjectHealthDetailsResponse`: 健康度详情响应模型

### 6. 依赖更新 ✅

**文件**: `requirements.txt`

- ✅ 添加 `apscheduler` 依赖

## 健康度计算规则

### H4: 已完结（灰色）
- 项目状态为 `ST30`(已结项) 或 `ST99`(项目取消)

### H3: 阻塞（红色）
满足以下任一条件：
1. 项目状态为 `ST14`(缺料阻塞) 或 `ST19`(技术阻塞)
2. 有关键任务阻塞
3. 有严重阻塞问题未解决
4. 有严重缺料预警

### H2: 有风险（黄色）
满足以下任一条件：
1. 项目状态为 `ST22`(FAT整改中) 或 `ST26`(SAT整改中)
2. 交期临近（7天内）
3. 有逾期里程碑
4. 有缺料预警（非严重）
5. 有未解决的高优先级问题
6. 进度偏差超过阈值（10%）

### H1: 正常（绿色）
- 不满足以上条件的情况

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量（可选）

```bash
# .env 文件
ENABLE_SCHEDULER=true  # 是否启用定时任务，默认true
```

### 3. 启动应用

```bash
uvicorn app.main:app --reload
```

定时任务会在应用启动时自动开始运行。

### 4. API 使用示例

#### 手动触发健康度计算

```bash
POST /api/v1/projects/1/health/calculate
```

#### 获取健康度详情

```bash
GET /api/v1/projects/1/health/details
```

响应示例：
```json
{
  "project_id": 1,
  "project_code": "PJ250101001",
  "current_health": "H1",
  "calculated_health": "H2",
  "status": "ST12",
  "stage": "S5",
  "checks": {
    "is_closed": false,
    "is_blocked": false,
    "has_risks": true,
    "has_overdue_milestones": true,
    ...
  },
  "statistics": {
    "blocked_tasks": 0,
    "blocking_issues": 0,
    "overdue_milestones": 1,
    "active_alerts": 2
  }
}
```

#### 批量计算健康度

```bash
POST /api/v1/projects/health/batch-calculate
Content-Type: application/json

{
  "project_ids": [1, 2, 3]  // 可选，为空则计算所有活跃项目
}
```

## 定时任务说明

### 1. 健康度计算任务
- **执行频率**: 每小时（整点）
- **功能**: 自动计算所有活跃项目的健康度
- **日志**: 输出计算统计信息

### 2. 健康度快照任务
- **执行频率**: 每天凌晨2点
- **功能**: 生成所有项目的健康度快照，用于趋势分析
- **存储**: `project_health_snapshots` 表

### 3. 规格匹配检查任务
- **执行频率**: 每天上午9点
- **功能**: 检查采购订单和BOM的规格匹配情况

## 注意事项

1. **性能考虑**
   - 批量计算时建议分批处理大量项目
   - 定时任务在后台线程执行，不会阻塞API请求

2. **错误处理**
   - 所有定时任务都有异常捕获和日志记录
   - 健康度计算失败不会影响项目状态更新

3. **数据一致性**
   - 健康度计算在数据库事务中执行
   - 状态变更历史自动记录

4. **扩展性**
   - 可以继承 `HealthCalculator` 类自定义计算规则
   - 可以添加新的定时任务到 `scheduler.py`

## 下一步优化建议

1. **缓存机制**: 对健康度计算结果进行缓存，减少重复计算
2. **异步处理**: 使用 Celery 替代 APScheduler，支持分布式任务
3. **健康度趋势**: 基于快照数据生成健康度趋势图表
4. **预警集成**: 健康度变化时自动生成预警通知
5. **性能监控**: 添加任务执行时间监控和性能分析

## 测试建议

1. **单元测试**: 测试健康度计算逻辑的各种场景
2. **集成测试**: 测试API端点和定时任务
3. **性能测试**: 测试批量计算的性能
4. **压力测试**: 测试大量项目同时计算的情况

## 相关文档

- `app/services/README_HEALTH_CALCULATOR.md`: 详细使用文档
- `app/services/health_calculator.py`: 核心服务代码
- `app/utils/scheduler.py`: 定时任务配置
- `app/utils/scheduled_tasks.py`: 定时任务实现



