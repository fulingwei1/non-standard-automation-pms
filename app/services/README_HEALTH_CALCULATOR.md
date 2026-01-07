# 健康度自动计算服务使用说明

## 概述

健康度自动计算服务 (`HealthCalculator`) 用于根据项目状态、里程碑、问题、缺料、预警等多维度指标自动计算项目健康度。

## 健康度等级

- **H1**: 正常(绿色) - On Track
- **H2**: 有风险(黄色) - At Risk  
- **H3**: 阻塞(红色) - Blocked
- **H4**: 已完结(灰色) - Closed

## 计算规则

### H4: 已完结
- 项目状态为 `ST30`(已结项) 或 `ST99`(项目取消)

### H3: 阻塞
满足以下任一条件：
1. 项目状态为 `ST14`(缺料阻塞) 或 `ST19`(技术阻塞)
2. 有关键任务阻塞
3. 有严重阻塞问题未解决
4. 有严重缺料预警

### H2: 有风险
满足以下任一条件：
1. 项目状态为 `ST22`(FAT整改中) 或 `ST26`(SAT整改中)
2. 交期临近（7天内）
3. 有逾期里程碑
4. 有缺料预警（非严重）
5. 有未解决的高优先级问题
6. 进度偏差超过阈值（10%）

### H1: 正常
- 不满足以上条件的情况

## 使用方法

### 1. 单个项目健康度计算

```python
from app.services.health_calculator import HealthCalculator
from app.models.base import get_db_session

with get_db_session() as db:
    project = db.query(Project).filter(Project.id == 1).first()
    calculator = HealthCalculator(db)
    
    # 计算并更新健康度
    result = calculator.calculate_and_update(project, auto_save=True)
    print(f"健康度: {result['old_health']} -> {result['new_health']}")
```

### 2. 批量计算健康度

```python
from app.services.health_calculator import HealthCalculator
from app.models.base import get_db_session

with get_db_session() as db:
    calculator = HealthCalculator(db)
    
    # 计算所有活跃项目
    result = calculator.batch_calculate()
    print(f"总计: {result['total']}, 更新: {result['updated']}, 未变化: {result['unchanged']}")
    
    # 计算指定项目
    result = calculator.batch_calculate(project_ids=[1, 2, 3])
```

### 3. 获取健康度详细信息（诊断）

```python
from app.services.health_calculator import HealthCalculator
from app.models.base import get_db_session

with get_db_session() as db:
    project = db.query(Project).filter(Project.id == 1).first()
    calculator = HealthCalculator(db)
    
    # 获取详细信息
    details = calculator.get_health_details(project)
    print(f"当前健康度: {details['current_health']}")
    print(f"计算健康度: {details['calculated_health']}")
    print(f"检查结果: {details['checks']}")
    print(f"统计信息: {details['statistics']}")
```

## 定时任务配置

### 使用 APScheduler

在 `app/main.py` 或启动脚本中添加：

```python
from apscheduler.schedulers.background import BackgroundScheduler
from app.utils.scheduled_tasks import calculate_project_health, daily_health_snapshot

scheduler = BackgroundScheduler()

# 每小时计算健康度
scheduler.add_job(calculate_project_health, 'cron', minute=0)

# 每天凌晨2点生成健康度快照
scheduler.add_job(daily_health_snapshot, 'cron', hour=2, minute=0)

scheduler.start()
```

### 使用 Celery

在 Celery 任务文件中添加：

```python
from celery import Celery
from app.utils.scheduled_tasks import calculate_project_health, daily_health_snapshot

app = Celery('tasks')

@app.task
def calculate_health_task():
    return calculate_project_health()

@app.task
def health_snapshot_task():
    return daily_health_snapshot()

# 配置定时任务
app.conf.beat_schedule = {
    'calculate-health-every-hour': {
        'task': 'calculate_health_task',
        'schedule': crontab(minute=0),  # 每小时
    },
    'health-snapshot-daily': {
        'task': 'health_snapshot_task',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨2点
    },
}
```

## API 端点集成

可以在项目状态更新时自动触发健康度计算：

```python
from app.services.health_calculator import HealthCalculator

@router.put("/{project_id}/status")
def update_project_status(...):
    # ... 更新项目状态 ...
    
    # 自动计算健康度
    calculator = HealthCalculator(db)
    calculator.calculate_and_update(project, auto_save=True)
    
    return project
```

## 注意事项

1. **性能考虑**: 批量计算时建议分批处理，避免一次性处理过多项目
2. **事务管理**: 确保在数据库事务中正确使用，避免数据不一致
3. **错误处理**: 建议添加异常处理和日志记录
4. **缓存策略**: 可以考虑对健康度计算结果进行缓存，减少数据库查询

## 扩展开发

如需自定义健康度计算规则，可以：

1. 继承 `HealthCalculator` 类
2. 重写 `_is_blocked()` 或 `_has_risks()` 方法
3. 添加新的检查条件

示例：

```python
class CustomHealthCalculator(HealthCalculator):
    def _has_risks(self, project: Project) -> bool:
        # 调用父类方法
        if super()._has_risks(project):
            return True
        
        # 添加自定义检查
        if self._custom_risk_check(project):
            return True
        
        return False
```



