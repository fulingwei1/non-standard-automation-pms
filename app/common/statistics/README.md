# 统一统计服务使用指南

## 快速开始

### 步骤1: 创建统计服务（只需2行代码！）

```python
from app.common.statistics.base import BaseStatisticsService
from app.models.projects import Project

class ProjectStatisticsService(BaseStatisticsService):
    def __init__(self, db: AsyncSession):
        super().__init__(Project, db)
```

### 步骤2: 使用统计功能

```python
service = ProjectStatisticsService(db)

# 按状态统计
by_status = await service.count_by_status()

# 按字段统计
by_stage = await service.count_by_field("stage")

# 获取趋势
trends = await service.get_trend("created_at", days=30)

# 获取分布
distribution = await service.get_distribution("status")
```

### 步骤3: 创建Dashboard服务

```python
from app.common.statistics.dashboard import BaseDashboardService

class ProjectDashboardService(BaseDashboardService):
    def __init__(self, db: AsyncSession):
        stats = BaseStatisticsService(Project, db)
        super().__init__(stats, db)
```

---

## 核心功能

### 1. 按状态统计

```python
by_status = await service.count_by_status()
# 返回: {"ACTIVE": 10, "COMPLETED": 5, "CANCELLED": 2}
```

### 2. 按字段统计

```python
by_stage = await service.count_by_field("stage")
# 返回: {"S1": 3, "S2": 5, "S3": 7}
```

### 3. 趋势分析

```python
trends = await service.get_trend(
    date_field="created_at",
    days=30,
    period="day"  # day, week, month
)
# 返回: [{"date": "2026-01-01", "count": 10}, ...]
```

### 4. 分布分析

```python
distribution = await service.get_distribution("status")
# 返回: {
#     "distribution": {"ACTIVE": 10, "COMPLETED": 5},
#     "total": 15,
#     "percentages": {"ACTIVE": 66.67, "COMPLETED": 33.33}
# }
```

### 5. 汇总统计

```python
summary = await service.get_summary_stats(
    numeric_fields=["total_cost", "progress"],
    date_field="created_at"
)
# 返回: {
#     "total": 15,
#     "sums": {"total_cost": 1000000, "progress": 1200},
#     "averages": {"total_cost": 66666.67, "progress": 80},
#     "latest_date": "2026-01-23",
#     "earliest_date": "2026-01-01"
# }
```

---

## Dashboard服务

### 基础使用

```python
dashboard = ProjectDashboardService(db)

# 获取完整Dashboard数据
data = await dashboard.get_dashboard_data()
```

### 自定义Dashboard

```python
class ProjectDashboardService(BaseDashboardService):
    async def get_overview(self, filters=None):
        # 调用基类方法
        base = await super().get_overview(filters)
        
        # 添加自定义统计
        base["custom_stat"] = await self._get_custom_stat()
        
        return base
```

---

## 更多示例

查看 `example_usage.py` 获取更多使用示例。
