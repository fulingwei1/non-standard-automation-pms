# 代码重复问题重构计划

## 概述

经过深入代码分析，发现非标自动化项目管理系统存在**严重的代码和功能重复问题**。本计划旨在系统性地解决这些问题，提高代码质量和可维护性。

## 问题分类

### 1. API 端点重复 - 严重程度：高 🔴

**问题描述**
项目从全局API迁移到项目中心API（`/projects/{id}/submodules/`）的过程中，旧的全局API端点未被删除，导致相同功能存在两套实现。

**具体影响范围**

| 模块 | 项目中心API | 全局API（应废弃） |
|------|-------------|-------------------|
| 里程碑 | `/app/api/v1/endpoints/projects/milestones/crud.py` | `/app/api/v1/endpoints/milestones/crud.py` |
| 成本 | `/app/api/v1/endpoints/projects/costs/crud.py` | `/app/api/v1/endpoints/costs/basic.py` |
| 机器 | `/app/api/v1/endpoints/projects/machines/crud.py` | `/app/api/v1/endpoints/machines/crud.py` |
| 成员 | `/app/api/v1/endpoints/projects/members/crud.py` | `/app/api/v1/endpoints/members/crud.py` |
| 采购 | `/app/api/v1/endpoints/purchase/orders.py` | 计划中的项目中心版本 |

**代码重复示例**

```python
# 项目中心版本 - 正确的实现
@router.get("/", response_model=List[MilestoneResponse])
def read_project_milestones(
    project_id: int = Path(..., description="项目ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:read")),
) -> Any:
    check_project_access_or_raise(db, current_user, project_id)
    query = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id
    )
    # ... 查询逻辑

# 全局版本 - 应该废弃
@router.get("/", response_model=List[MilestoneResponse], deprecated=True)
def read_milestones(
    db: Session = Depends(deps.get_db),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    current_user: User = Depends(security.require_permission("milestone:read")),
) -> Any:
    # 相同的查询逻辑，但增加了复杂的权限过滤
```

### 2. 服务层重复 - 严重程度：中 🟡

**问题描述**
多个服务文件包含相似的业务逻辑，缺乏统一的抽象层。

**影响范围**

| 服务类型 | 重复文件 |
|----------|----------|
| 奖金计算 | `bonus/allocation_helpers.py`, `bonus/calculator.py`, `bonus/calculation.py`, `project_bonus_service.py` |
| 采购分析 | `procurement_analysis/price_analysis.py`, `procurement_analysis/delivery_performance.py`, `procurement_analysis/quality_analysis.py` |
| 绩效服务 | `performance_integration_service.py`, `performance_stats_service.py`, `engineer_performance/engineer_performance_service.py` |

### 3. 前端组件重复 - 严重程度：中 🟡

**问题描述**
多个相似的Card组件和Dashboard布局组件在不同页面重复实现。

**影响范围**

| 组件类型 | 重复位置 |
|----------|----------|
| 统计卡片 | `StatCard.jsx`, `KeyMetricsCard.jsx`, `RecentApprovalsCard.jsx` |
| Dashboard Tab | 多个工作站都有相似的 `Overview.jsx`, `ApprovalsTab.jsx` |
| 统计卡片布局 | `StatsCards.jsx` 在多处重复 |

### 4. Schema 定义重复 - 严重程度：中 🟡

**问题描述**
分页响应模型、基础CRUD Schema模式在多处重复定义。

**影响范围**
- `PaginatedResponse` 在多个Schema中重复定义
- 基础的 Create/Update/Response Schema 模式重复

### 5. 模型定义重复 - 严重程度：低 🟢

**问题描述**
公共字段（时间戳、审计字段等）已有 TimestampMixin 解决，但部分模型仍有冗余字段。

**状态**：基本已解决，需检查是否所有模型都使用了 Mixin

---

## 重构方案

### Phase 1: API 层统一 (高优先级)

**目标**：彻底清理全局API，统一使用项目中心API

#### 1.1 创建通用CRUD基类

```python
# app/api/v1/core/crud_base.py
from typing import Type, TypeVar, Generic, List, Optional
from fastapi import APIRouter, Path, Depends, Query
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.security import require_permission

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")
ResponseSchemaType = TypeVar("ResponseSchemaType")

class ProjectCRUDRouter(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    """项目中心CRUD路由基类"""

    def __init__(
        self,
        model: Type[ModelType],
        create_schema: Type[CreateSchemaType],
        update_schema: Type[UpdateSchemaType],
        response_schema: Type[ResponseSchemaType],
        permission_prefix: str,
        project_id_field: str = "project_id",
    ):
        self.model = model
        self.create_schema = create_schema
        self.update_schema = update_schema
        self.response_schema = response_schema
        self.permission_prefix = permission_prefix
        self.project_id_field = project_id_field
        self.router = APIRouter()
        self._register_routes()

    def _register_routes(self):
        """注册标准CRUD路由"""

        @self.router.get("/", response_model=List[self.response_schema])
        def list_items(
            project_id: int = Path(..., description="项目ID"),
            db: Session = Depends(get_db),
            skip: int = Query(0, ge=0),
            limit: int = Query(100, ge=1, le=100),
            current_user = Depends(require_permission(f"{self.permission_prefix}:read")),
        ):
            from app.services.project_service import check_project_access_or_raise
            check_project_access_or_raise(db, current_user, project_id)

            query = db.query(self.model).filter(
                getattr(self.model, self.project_id_field) == project_id
            )
            return query.offset(skip).limit(limit).all()

        @self.router.post("/", response_model=self.response_schema)
        def create_item(
            project_id: int = Path(..., description="项目ID"),
            item_in: self.create_schema = None,
            db: Session = Depends(get_db),
            current_user = Depends(require_permission(f"{self.permission_prefix}:create")),
        ):
            from app.services.project_service import check_project_access_or_raise
            check_project_access_or_raise(db, current_user, project_id)

            item_data = item_in.dict()
            item_data[self.project_id_field] = project_id
            db_item = self.model(**item_data)
            db.add(db_item)
            db.commit()
            db.refresh(db_item)
            return db_item

        @self.router.get("/{item_id}", response_model=self.response_schema)
        def get_item(
            project_id: int = Path(..., description="项目ID"),
            item_id: int = Path(..., description="项目ID"),
            db: Session = Depends(get_db),
            current_user = Depends(require_permission(f"{self.permission_prefix}:read")),
        ):
            from app.services.project_service import check_project_access_or_raise
            check_project_access_or_raise(db, current_user, project_id)

            item = db.query(self.model).filter(
                self.model.id == item_id,
                getattr(self.model, self.project_id_field) == project_id
            ).first()
            if not item:
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail="Item not found")
            return item

        @self.router.patch("/{item_id}", response_model=self.response_schema)
        def update_item(
            project_id: int = Path(..., description="项目ID"),
            item_id: int = Path(..., description="项目ID"),
            item_in: self.update_schema = None,
            db: Session = Depends(get_db),
            current_user = Depends(require_permission(f"{self.permission_prefix}:update")),
        ):
            from app.services.project_service import check_project_access_or_raise
            check_project_access_or_raise(db, current_user, project_id)

            item = db.query(self.model).filter(
                self.model.id == item_id,
                getattr(self.model, self.project_id_field) == project_id
            ).first()
            if not item:
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail="Item not found")

            update_data = item_in.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(item, field, value)
            db.commit()
            db.refresh(item)
            return item

        @self.router.delete("/{item_id}")
        def delete_item(
            project_id: int = Path(..., description="项目ID"),
            item_id: int = Path(..., description="项目ID"),
            db: Session = Depends(get_db),
            current_user = Depends(require_permission(f"{self.permission_prefix}:delete")),
        ):
            from app.services.project_service import check_project_access_or_raise
            check_project_access_or_raise(db, current_user, project_id)

            item = db.query(self.model).filter(
                self.model.id == item_id,
                getattr(self.model, self.project_id_field) == project_id
            ).first()
            if not item:
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail="Item not found")

            db.delete(item)
            db.commit()
            return {"message": "Item deleted successfully"}
```

#### 1.2 迁移现有端点使用基类

```python
# app/api/v1/endpoints/projects/milestones/crud.py
from app.api.v1.core.crud_base import ProjectCRUDRouter
from app.models.project import ProjectMilestone
from app.schemas.project import MilestoneCreate, MilestoneUpdate, MilestoneResponse

# 创建路由实例
milestone_router = ProjectCRUDRouter(
    model=ProjectMilestone,
    create_schema=MilestoneCreate,
    update_schema=MilestoneUpdate,
    response_schema=MilestoneResponse,
    permission_prefix="milestone",
)

router = milestone_router.router

# 如需自定义端点，可以继续添加
@router.post("/{milestone_id}/complete")
def complete_milestone(...):
    """自定义业务逻辑"""
    pass
```

#### 1.3 废弃全局API端点

```python
# app/api/v1/endpoints/milestones/crud.py
from fastapi import APIRouter, Depends
from fastapi import status

router = APIRouter()

@router.get("/", deprecated=True)
@router.post("/", deprecated=True)
@router.get("/{item_id}", deprecated=True)
@router.patch("/{item_id}", deprecated=True)
@router.delete("/{item_id}", deprecated=True)
async def deprecated_endpoint():
    """此端点已废弃，请使用 /projects/{project_id}/milestones/"""
    raise HTTPException(
        status_code=status.HTTP_301_MOVED_PERMANENTLY,
        detail="此端点已废弃，请使用项目中心API: /projects/{project_id}/milestones/",
        headers={"Location": "/api/v1/docs"}
    )
```

#### 1.4 清理计划

| 阶段 | 操作 | 文件 |
|------|------|------|
| 1 | 创建CRUD基类 | `app/api/v1/core/crud_base.py` |
| 2 | 迁移里程碑端点 | `app/api/v1/endpoints/projects/milestones/crud.py` |
| 3 | 迁移成本端点 | `app/api/v1/endpoints/projects/costs/crud.py` |
| 4 | 迁移机器端点 | `app/api/v1/endpoints/projects/machines/crud.py` |
| 5 | 迁移成员端点 | `app/api/v1/endpoints/projects/members/crud.py` |
| 6 | 废弃全局API | `app/api/v1/endpoints/milestones/`, `costs/`, `machines/`, `members/` |
| 7 | 更新API文档 | `docs/`, API 注释 |

### Phase 2: 服务层重构 (中优先级)

**目标**：创建统一的服务抽象层，消除重复业务逻辑

#### 2.1 奖金服务统一

```python
# app/services/bonus/unified_bonus_service.py
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.project import Project, ProjectMember
from app.models.acceptance import AcceptanceOrder

class UnifiedBonusService:
    """统一的奖金计算服务"""

    def __init__(self, db: Session):
        self.db = db

    def calculate_project_bonus(
        self,
        project_id: int,
        calculation_type: str = "acceptance"
    ) -> Dict[str, float]:
        """
        计算项目奖金

        Args:
            project_id: 项目ID
            calculation_type: 计算类型 (acceptance/evaluation/completion)

        Returns:
            奖金分配字典 {member_id: bonus_amount}
        """
        if calculation_type == "acceptance":
            return self._calculate_acceptance_bonus(project_id)
        elif calculation_type == "evaluation":
            return self._calculate_evaluation_bonus(project_id)
        elif calculation_type == "completion":
            return self._calculate_completion_bonus(project_id)
        else:
            raise ValueError(f"Unknown calculation type: {calculation_type}")

    def _calculate_acceptance_bonus(self, project_id: int) -> Dict[str, float]:
        """验收奖金计算逻辑"""
        project = self.db.query(Project).get(project_id)
        if not project:
            raise ValueError("Project not found")

        # 获取验收数据
        acceptances = self.db.query(AcceptanceOrder).filter(
            AcceptanceOrder.project_id == project_id
        ).all()

        # 获取项目成员
        members = self.db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id
        ).all()

        # 计算奖金
        bonus_pool = self._calculate_bonus_pool(project, acceptances)
        return self._allocate_bonus(members, bonus_pool)

    def _calculate_bonus_pool(
        self,
        project: Project,
        acceptances: List[AcceptanceOrder]
    ) -> float:
        """计算奖金池"""
        # 奖金池计算逻辑
        pass

    def _allocate_bonus(
        self,
        members: List[ProjectMember],
        pool: float
    ) -> Dict[str, float]:
        """分配奖金"""
        # 奖金分配逻辑
        pass
```

#### 2.2 分析服务基类

```python
# app/services/analysis/base_analysis_service.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

class BaseAnalysisService(ABC):
    """分析服务基类"""

    def __init__(self, db: Session):
        self.db = db

    def analyze(
        self,
        filters: Dict[str, Any],
        group_by: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        执行分析

        Args:
            filters: 筛选条件
            group_by: 分组字段

        Returns:
            分析结果
        """
        data = self._fetch_data(filters)
        processed_data = self._preprocess(data)
        result = self._calculate(processed_data, group_by)
        return self._postprocess(result)

    @abstractmethod
    def _fetch_data(self, filters: Dict[str, Any]) -> List[Any]:
        """获取原始数据"""
        pass

    def _preprocess(self, data: List[Any]) -> List[Any]:
        """预处理数据"""
        return data

    @abstractmethod
    def _calculate(
        self,
        data: List[Any],
        group_by: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """计算分析结果"""
        pass

    def _postprocess(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """后处理结果"""
        return result
```

```python
# app/services/procurement_analysis/price_analysis.py
from app.services.analysis.base_analysis_service import BaseAnalysisService

class PriceAnalysisService(BaseAnalysisService):
    """价格分析服务"""

    def _fetch_data(self, filters: Dict[str, Any]) -> List[Any]:
        """获取采购价格数据"""
        from app.models.purchase import PurchaseOrder, PurchaseOrderItem
        from app.models.material import Material

        query = self.db.query(
            Material,
            PurchaseOrderItem,
            PurchaseOrder
        ).join(
            PurchaseOrderItem,
            Material.id == PurchaseOrderItem.material_id
        ).join(
            PurchaseOrder,
            PurchaseOrderItem.order_id == PurchaseOrder.id
        )

        # 应用筛选条件
        if 'material_id' in filters:
            query = query.filter(Material.id == filters['material_id'])
        if 'supplier_id' in filters:
            query = query.filter(PurchaseOrder.supplier_id == filters['supplier_id'])
        if 'date_from' in filters:
            query = query.filter(PurchaseOrder.order_date >= filters['date_from'])
        if 'date_to' in filters:
            query = query.filter(PurchaseOrder.order_date <= filters['date_to'])

        return query.all()

    def _calculate(
        self,
        data: List[Any],
        group_by: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """计算价格统计"""
        if not data:
            return {
                "count": 0,
                "avg_price": 0,
                "min_price": 0,
                "max_price": 0,
                "price_trend": []
            }

        prices = [float(item[1].unit_price) for item in data]

        return {
            "count": len(prices),
            "avg_price": sum(prices) / len(prices),
            "min_price": min(prices),
            "max_price": max(prices),
            "price_trend": self._calculate_trend(data)
        }

    def _calculate_trend(self, data: List[Any]) -> List[Dict[str, Any]]:
        """计算价格趋势"""
        # 按日期分组计算平均价格
        pass
```

#### 2.3 绩效服务统一

```python
# app/services/performance/unified_performance_service.py
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

class UnifiedPerformanceService:
    """统一的绩效服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_engineer_performance(
        self,
        engineer_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取工程师绩效

        Args:
            engineer_id: 工程师ID
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            绩效数据字典
        """
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()

        return {
            "summary": self._get_summary(engineer_id, start_date, end_date),
            "projects": self._get_projects(engineer_id, start_date, end_date),
            "tasks": self._get_tasks(engineer_id, start_date, end_date),
            "trend": self._get_trend(engineer_id, start_date, end_date),
        }

    def _get_summary(
        self,
        engineer_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """获取绩效摘要"""
        # 实现摘要逻辑
        pass

    def _get_projects(
        self,
        engineer_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """获取项目绩效"""
        # 实现项目逻辑
        pass

    def _get_tasks(
        self,
        engineer_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """获取任务绩效"""
        # 实现任务逻辑
        pass

    def _get_trend(
        self,
        engineer_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """获取绩效趋势"""
        # 实现趋势逻辑
        pass
```

### Phase 3: 前端组件重构 (中优先级)

**目标**：创建可复用的通用组件

#### 3.1 通用统计卡片组件

```jsx
// frontend/src/components/common/StatCard.jsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

const formatValue = (value, format = 'number') => {
  switch (format) {
    case 'currency':
      return new Intl.NumberFormat('zh-CN', {
        style: 'currency',
        currency: 'CNY'
      }).format(value);
    case 'percentage':
      return `${value.toFixed(1)}%`;
    case 'number':
    default:
      return new Intl.NumberFormat('zh-CN').format(value);
  }
};

const TrendIcon = ({ value, className }) => {
  if (value > 0) return <TrendingUp className={cn("text-green-500", className)} />;
  if (value < 0) return <TrendingDown className={cn("text-red-500", className)} />;
  return <Minus className={cn("text-gray-500", className)} />;
};

export function StatCard({
  title,
  value,
  subtitle,
  trend,
  icon: Icon,
  valueFormat = 'number',
  trendFormat = 'percentage',
  className,
  ...props
}) {
  const formattedValue = formatValue(value, valueFormat);

  const trendDisplay = trend !== undefined ? (
    <div className="flex items-center gap-1">
      <TrendIcon value={trend} className="w-4 h-4" />
      <span className={cn(
        "text-sm",
        trend > 0 ? "text-green-500" : trend < 0 ? "text-red-500" : "text-gray-500"
      )}>
        {trendFormat === 'percentage' ? `${Math.abs(trend).toFixed(1)}%` : Math.abs(trend)}
      </span>
    </div>
  ) : null;

  return (
    <Card className={cn("transition-all duration-300 hover:shadow-lg", className)} {...props}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-slate-600">
          {title}
        </CardTitle>
        {Icon && <Icon className="h-4 w-4 text-slate-500" />}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{formattedValue}</div>
        {subtitle && (
          <p className="text-xs text-slate-500 mt-1">{subtitle}</p>
        )}
        {trendDisplay && (
          <div className="mt-2">{trendDisplay}</div>
        )}
      </CardContent>
    </Card>
  );
}

// 使用示例
export function StatCardExample() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <StatCard
        title="总销售额"
        value={1234567.89}
        valueFormat="currency"
        trend={12.5}
        subtitle="较上月"
        icon={TrendingUp}
      />
      <StatCard
        title="项目完成率"
        value={85.7}
        valueFormat="percentage"
        trend={5.3}
        subtitle="较上月"
      />
    </div>
  );
}
```

#### 3.2 通用Dashboard布局模板

```jsx
// frontend/src/components/common/DashboardLayout.jsx
import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function DashboardLayout({
  title,
  stats,
  tabs,
  children
}) {
  const [activeTab, setActiveTab] = useState(tabs[0]?.value);

  return (
    <div className="space-y-6">
      {/* 标题 */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
      </div>

      {/* 统计卡片 */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {stats.map((stat, index) => (
            <StatCard key={index} {...stat} />
          ))}
        </div>
      )}

      {/* 标签页 */}
      {tabs && tabs.length > 0 && (
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList>
            {tabs.map((tab) => (
              <TabsTrigger key={tab.value} value={tab.value}>
                {tab.label}
              </TabsTrigger>
            ))}
          </TabsList>
          {tabs.map((tab) => (
            <TabsContent key={tab.value} value={tab.value} className="space-y-4">
              {tab.content}
            </TabsContent>
          ))}
        </Tabs>
      )}

      {/* 自定义内容 */}
      {children}
    </div>
  );
}

// 使用示例
export function DashboardLayoutExample() {
  const stats = [
    {
      title: "总项目数",
      value: 42,
      trend: 3,
      subtitle: "较上月"
    },
    // ... 更多统计
  ];

  const tabs = [
    {
      value: "overview",
      label: "概览",
      content: <div>概览内容</div>
    },
    {
      value: "approvals",
      label: "审批",
      content: <div>审批内容</div>
    }
  ];

  return (
    <DashboardLayout
      title="项目经理工作台"
      stats={stats}
      tabs={tabs}
    />
  );
}
```

### Phase 4: Schema层重构 (中优先级)

**目标**：创建通用的Schema工厂和共享Schema

#### 4.1 Schema工厂

```python
# app/schemas/factory.py
from typing import Type, TypeVar, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic import ConfigDict

T = TypeVar("T", bound=BaseModel)

def create_crud_schemas(
    name: str,
    fields: Dict[str, tuple],
    include_timestamps: bool = True
) -> tuple[Type[BaseModel], Type[BaseModel], Type[BaseModel]]:
    """
    动态创建CRUD相关的Schema

    Args:
        name: Schema名称前缀
        fields: 字段定义 {field_name: (type, description, required)}
        include_timestamps: 是否包含时间戳字段

    Returns:
        (CreateSchema, UpdateSchema, ResponseSchema)
    """

    # 构建字段定义
    create_fields = {}
    update_fields = {}
    response_fields = {}

    for field_name, (field_type, description, required) in fields.items():
        if required:
            create_fields[field_name] = (field_type, Field(..., description=description))
            update_fields[field_name] = (Optional[field_type], Field(None, description=description))
        else:
            create_fields[field_name] = (Optional[field_type], Field(None, description=description))
            update_fields[field_name] = (Optional[field_type], Field(None, description=description))
        response_fields[field_name] = (field_type, Field(description=description))

    # 创建CreateSchema
    create_schema_dict = {"__annotations__": {}}
    for field_name, (field_type, field) in create_fields.items():
        create_schema_dict[field_name] = field
        create_schema_dict["__annotations__"][field_name] = field_type

    CreateSchema = type(f"{name}Create", (BaseModel,), create_schema_dict)

    # 创建UpdateSchema
    update_schema_dict = {"__annotations__": {}}
    for field_name, (field_type, field) in update_fields.items():
        update_schema_dict[field_name] = field
        update_schema_dict["__annotations__"][field_name] = field_type

    class Config:
        from_attributes = True

    UpdateSchema = type(f"{name}Update", (BaseModel,), update_schema_dict)
    UpdateSchema.Config = Config

    # 创建ResponseSchema
    response_schema_dict = {
        "__annotations__": {
            "id": int,
            **{field_name: field_type for field_name, (field_type, _, _) in fields.items()}
        },
        "id": Field(description="ID"),
        "model_config": ConfigDict(from_attributes=True)
    }

    for field_name, (field_type, field) in response_fields.items():
        response_schema_dict[field_name] = field

    if include_timestamps:
        response_schema_dict["__annotations__"]["created_at"] = datetime
        response_schema_dict["__annotations__"]["updated_at"] = datetime
        response_schema_dict["created_at"] = Field(description="创建时间")
        response_schema_dict["updated_at"] = Field(description="更新时间")

    ResponseSchema = type(f"{name}Response", (BaseModel,), response_schema_dict)

    return CreateSchema, UpdateSchema, ResponseSchema

# 使用示例
if __name__ == "__main__":
    MilestoneCreate, MilestoneUpdate, MilestoneResponse = create_crud_schemas(
        name="Milestone",
        fields={
            "name": (str, "里程碑名称", True),
            "description": (Optional[str], "里程碑描述", False),
            "target_date": (datetime, "目标日期", True),
        }
    )
```

#### 4.2 共享分页Schema

```python
# app/schemas/common.py
from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field

T = TypeVar("T")

class PaginatedResponse(BaseModel, Generic[T]):
    """通用分页响应"""

    items: List[T] = Field(description="数据列表")
    total: int = Field(description="总数量")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    total_pages: int = Field(description="总页数")

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse[T]":
        """创建分页响应"""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )

class ResponseModel(BaseModel, Generic[T]):
    """通用API响应"""

    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="消息")
    data: Optional[T] = Field(default=None, description="数据")

    @classmethod
    def success(cls, data: T = None, message: str = "success") -> "ResponseModel[T]":
        """成功响应"""
        return cls(code=200, message=message, data=data)

    @classmethod
    def error(cls, message: str, code: int = 400) -> "ResponseModel[T]":
        """错误响应"""
        return cls(code=code, message=message, data=None)
```

---

## 实施计划

### 优先级排序

| 优先级 | 阶段 | 预计工作量 | 风险等级 |
|--------|------|------------|----------|
| 1 | Phase 1: API层统一 | 3-5天 | 中 |
| 2 | Phase 2: 服务层重构 | 5-7天 | 高 |
| 3 | Phase 3: 前端组件重构 | 3-4天 | 低 |
| 4 | Phase 4: Schema层重构 | 2-3天 | 低 |

### 实施步骤

#### 第一步：API层统一 (第1-2周)

1. **Day 1-2**: 创建 `ProjectCRUDRouter` 基类
2. **Day 3**: 迁移里程碑端点
3. **Day 4**: 迁移成本端点
4. **Day 5**: 迁移机器和成员端点
5. **Day 6**: 废弃全局API，添加重定向
6. **Day 7**: 测试和文档更新

#### 第二步：服务层重构 (第3-4周)

1. **Day 1-2**: 创建分析服务基类
2. **Day 3**: 统一奖金计算服务
3. **Day 4**: 统一绩效服务
4. **Day 5**: 重构采购分析服务
5. **Day 6-7**: 测试和验证

#### 第三步：前端组件重构 (第5周)

1. **Day 1-2**: 创建通用StatCard组件
2. **Day 3**: 创建DashboardLayout模板
3. **Day 4**: 迁移现有页面使用新组件

#### 第四步：Schema层重构 (第6周)

1. **Day 1**: 创建Schema工厂
2. **Day 2**: 创建共享分页Schema
3. **Day 3**: 迁移现有Schema

---

## 验证标准

### API层验证

- [ ] 全局API端点已标记为废弃并返回301重定向
- [ ] 所有CRUD操作统一使用 `ProjectCRUDRouter` 基类
- [ ] API文档已更新
- [ ] 前端调用已更新到项目中心API
- [ ] 测试覆盖率达到80%以上

### 服务层验证

- [ ] 奖金计算服务统一为单一入口
- [ ] 分析服务使用统一基类
- [ ] 服务代码重复率降低50%以上
- [ ] 业务逻辑单元测试覆盖

### 前端组件验证

- [ ] StatCard组件在至少3个页面使用
- [ ] DashboardLayout模板在至少2个工作台使用
- [ ] 组件代码重复率降低40%以上
- [ ] UI一致性验证

### Schema层验证

- [ ] 所有CRUD Schema使用工厂创建
- [ ] 分页响应统一使用 `PaginatedResponse`
- [ ] Schema定义代码减少30%以上

---

## 回滚计划

如果重构过程中出现重大问题：

1. **保留原代码**：在废弃旧代码前，使用Git分支保留
2. **特性开关**：可以使用环境变量控制新旧实现切换
3. **渐进式迁移**：先迁移部分模块验证，再全面推广

---

## 相关文档

- [设计：通过CRUD基类完整实现](../design/通过CRUD基类完整实现.md)
- [系统重构建议_完全重写方案](./系统重构建议_完全重写方案.md)
- [项目模块详细设计文档](../项目管理模块_详细设计文档.md)
