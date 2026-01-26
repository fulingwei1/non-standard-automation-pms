# 统一Dashboard基类使用指南

## 概述

`BaseDashboardService` 提供了所有Dashboard服务的统一基类，简化Dashboard服务的开发，确保接口一致性。

## 特性

- ✅ 支持同步数据库会话（Session）
- ✅ 提供通用的统计方法（count、sum、avg等）
- ✅ 支持趋势分析、分布统计
- ✅ 灵活的筛选条件支持
- ✅ 可扩展的接口设计

## 快速开始

### 1. 创建Dashboard服务

```python
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.common.dashboard import BaseDashboardService
from app.models.project import Project

class ProjectDashboardService(BaseDashboardService):
    """项目Dashboard服务"""
    
    def __init__(self, db: Session):
        super().__init__(db)
        # 可以在这里初始化其他服务或模型
    
    def get_overview(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取项目概览数据（必须实现）"""
        total = self.count_total(Project, filters)
        active = self.count_total(Project, {**filters or {}, "status": "ACTIVE"})
        
        return {
            "total": total,
            "active": active,
            "pending": self.count_total(Project, {**filters or {}, "status": "PENDING"}),
            "completed": self.count_total(Project, {**filters or {}, "status": "COMPLETED"}),
        }
    
    def get_stats(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取统计数据（可选）"""
        # 使用基类提供的工具方法
        by_status = self.count_by_status(Project, "status", filters)
        by_stage = self.count_by_field(Project, "stage", filters)
        
        return {
            "by_status": by_status,
            "by_stage": by_stage,
        }
    
    def get_trends(
        self,
        date_field: str = "created_at",
        days: int = 30,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """获取趋势数据（可选）"""
        return self.get_trend_by_date(Project, date_field, days=days, filters=filters)
```

### 2. 在API端点中使用

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.common.dashboard import ProjectDashboardService
from app.schemas.common import ResponseModel

router = APIRouter()

@router.get("/dashboard", response_model=ResponseModel[Dict])
def get_project_dashboard(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """获取项目Dashboard数据"""
    service = ProjectDashboardService(db)
    dashboard_data = service.get_dashboard_data()
    
    return ResponseModel(
        code=200,
        message="获取Dashboard数据成功",
        data=dashboard_data
    )
```

## API参考

### 必须实现的方法

#### `get_overview(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`

获取概览数据，子类必须实现此方法。

**参数：**
- `filters`: 筛选条件字典

**返回：**
- 概览数据字典，通常包含 `total`、`active`、`pending`、`completed` 等字段

### 可选重写的方法

#### `get_stats(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`

获取统计数据，默认返回空字典。

#### `get_trends(date_field: str = "created_at", days: int = 30, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]`

获取趋势数据，默认返回空列表。

#### `get_distribution(field: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`

获取分布数据，默认返回空分布。

#### `get_recent_items(limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]`

获取最近项目/记录列表，默认返回空列表。

#### `get_alerts(filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]`

获取预警/提醒列表，默认返回空列表。

#### `get_dashboard_data(filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`

获取完整的Dashboard数据，默认组合所有标准方法的结果。

### 通用工具方法

#### `count_by_status(model, status_field: str = "status", filters: Optional[Dict[str, Any]] = None) -> Dict[str, int]`

按状态统计。

#### `count_by_field(model, field: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, int]`

按字段统计。

#### `count_total(model, filters: Optional[Dict[str, Any]] = None) -> int`

统计总数。

#### `calculate_sum(model, field: str, filters: Optional[Dict[str, Any]] = None) -> float`

计算字段总和。

#### `calculate_avg(model, field: str, filters: Optional[Dict[str, Any]] = None) -> float`

计算字段平均值。

#### `get_trend_by_date(model, date_field: str, value_field: Optional[str] = None, days: int = 30, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]`

获取按日期的趋势数据。

## 筛选条件格式

筛选条件支持以下格式：

```python
# 简单等值查询
filters = {"status": "ACTIVE"}

# 列表查询（IN查询）
filters = {"status": ["ACTIVE", "PENDING"]}

# 范围查询
filters = {
    "created_at": {
        "gte": "2026-01-01",  # 大于等于
        "lte": "2026-01-31"   # 小于等于
    }
}

# 组合查询
filters = {
    "status": "ACTIVE",
    "stage": ["S1", "S2"],
    "created_at": {"gte": "2026-01-01"}
}
```

## 最佳实践

1. **保持方法职责单一**：每个方法只负责一个特定的数据获取任务
2. **使用基类工具方法**：优先使用基类提供的工具方法，减少重复代码
3. **合理使用缓存**：对于计算量大的统计，考虑在服务层添加缓存
4. **错误处理**：在方法中添加适当的错误处理，避免因数据问题导致整个Dashboard失败
5. **性能优化**：对于大量数据的统计，考虑使用数据库聚合函数而不是在应用层计算

## 示例：完整的Dashboard服务

```python
from typing import Dict, Any, Optional, List
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.common.dashboard import BaseDashboardService
from app.models.project import Project, ProjectCost

class ProjectDashboardService(BaseDashboardService):
    """项目Dashboard服务"""
    
    def __init__(self, db: Session):
        super().__init__(db)
    
    def get_overview(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取项目概览"""
        total = self.count_total(Project, filters)
        
        # 使用状态统计
        by_status = self.count_by_status(Project, "status", filters)
        
        return {
            "total": total,
            "active": by_status.get("ACTIVE", 0),
            "pending": by_status.get("PENDING", 0),
            "completed": by_status.get("COMPLETED", 0),
            "by_status": by_status,
        }
    
    def get_stats(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取统计数据"""
        # 按阶段统计
        by_stage = self.count_by_field(Project, "stage", filters)
        
        # 计算总成本
        total_cost = self.calculate_sum(ProjectCost, "amount", filters)
        avg_cost = self.calculate_avg(ProjectCost, "amount", filters)
        
        return {
            "by_stage": by_stage,
            "total_cost": total_cost,
            "avg_cost": avg_cost,
        }
    
    def get_trends(
        self,
        date_field: str = "created_at",
        days: int = 30,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """获取项目创建趋势"""
        return self.get_trend_by_date(Project, date_field, days=days, filters=filters)
    
    def get_recent_items(
        self,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """获取最近项目"""
        query = self.db.query(Project)
        
        if filters:
            query = self._apply_filters(query, Project, filters)
        
        projects = query.order_by(desc(Project.created_at)).limit(limit).all()
        
        return [
            {
                "id": p.id,
                "code": p.project_code,
                "name": p.project_name,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in projects
        ]
    
    def get_dashboard_data(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取完整Dashboard数据"""
        return {
            "overview": self.get_overview(filters),
            "stats": self.get_stats(filters),
            "trends": self.get_trends(filters=filters),
            "recent_projects": self.get_recent_items(filters=filters),
            "timestamp": datetime.now().isoformat()
        }
```
