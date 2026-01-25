# 循环依赖解决方案

## 问题 #1: 状态处理器模块循环依赖

### 方案 A: 移除父引用，使用事件总线模式（推荐）

**优势**: 解耦合，易于扩展
**实施难度**: 中等

#### 重构步骤:

1. **创建事件总线** (`app/services/events/event_bus.py`):

```python
# -*- coding: utf-8 -*-
"""事件总线"""
from typing import Callable, Dict, List

class EventBus:
    """简单的事件总线实现"""

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        """订阅事件"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event_type: str, **kwargs):
        """发布事件"""
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                handler(**kwargs)

# 全局事件总线实例
event_bus = EventBus()
```

2. **修改 ContractStatusHandler** - 移除父引用:

```python
# app/services/status_handlers/contract_handler.py
from app.services.events.event_bus import event_bus

class ContractStatusHandler:
    """合同签订事件处理器"""

    def __init__(self, db: Session):  # 移除 parent 参数
        self.db = db

    def handle_contract_signed(self, contract_id: int, **kwargs):
        # ... 处理逻辑 ...

        # 发布事件而不是调用父类方法
        event_bus.publish(
            "contract.signed",
            contract_id=contract_id,
            project_id=project.id
        )

        return project
```

3. **修改 StatusTransitionService** - 订阅事件:

```python
# app/services/status_transition_service.py
from app.services.events.event_bus import event_bus

class StatusTransitionService:
    def __init__(self, db: Session):
        self.db = db
        self.contract_handler = ContractStatusHandler(db)  # 无需传入 self

        # 订阅事件
        event_bus.subscribe("contract.signed", self._on_contract_signed)

    def _on_contract_signed(self, contract_id: int, project_id: int):
        """响应合同签订事件"""
        # 执行后续逻辑
        pass
```

**优势**:
- ✅ 完全解耦，无循环依赖
- ✅ 易于添加新的事件处理器
- ✅ 符合开闭原则

**劣势**:
- ⚠️ 需要重构较多代码
- ⚠️ 事件流可能不够直观

---

### 方案 B: 延迟导入（快速修复）

**优势**: 最小改动
**实施难度**: 低

#### 实施方法:

在 `contract_handler.py` 中将导入移到方法内部:

```python
# app/services/status_handlers/contract_handler.py
class ContractStatusHandler:
    def __init__(self, db: Session, parent=None):
        self.db = db
        self._parent = parent

    def handle_contract_signed(self, contract_id: int, **kwargs):
        # 仅在需要时导入
        if self._parent:
            # 使用父服务的方法
            pass

        # ... 处理逻辑 ...
```

同时移除 `__init__.py` 中的导入，改为按需导入:

```python
# app/services/status_handlers/__init__.py

def register_all_handlers():
    """延迟导入，避免循环依赖"""
    from app.services.status_handlers.contract_handler import ContractStatusHandler
    from app.services.status_handlers.material_handler import MaterialStatusHandler
    # ... 其他导入

    # 注册逻辑
```

**优势**:
- ✅ 改动最小
- ✅ 快速修复

**劣势**:
- ❌ 治标不治本
- ❌ 代码可读性下降

---

## 问题 #2: 人工成本计算服务循环依赖

### 推荐方案: 提取共享工具模块

**问题根源**: `labor_cost_calculation_service` 既提供工具函数，又依赖 `LaborCostService`

**解决方案**: 将工具函数提取到独立模块

#### 重构步骤:

1. **创建新的工具模块** (`app/services/labor_cost/utils.py`):

```python
# -*- coding: utf-8 -*-
"""人工成本计算工具函数"""

from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from app.models.project import Project, ProjectCost
from app.models.timesheet import Timesheet


def query_approved_timesheets(
    db: Session,
    project_id: int,
    start_date: Optional[date],
    end_date: Optional[date]
) -> List[Timesheet]:
    """查询已审批的工时记录（无外部依赖）"""
    query = db.query(Timesheet).filter(
        Timesheet.project_id == project_id,
        Timesheet.status == "APPROVED"
    )

    if start_date:
        query = query.filter(Timesheet.work_date >= start_date)
    if end_date:
        query = query.filter(Timesheet.work_date <= end_date)

    return query.all()


def delete_existing_costs(
    db: Session,
    project: Project,
    project_id: int
) -> None:
    """删除现有的工时成本记录（无外部依赖）"""
    existing_costs = db.query(ProjectCost).filter(
        ProjectCost.project_id == project_id,
        ProjectCost.cost_type == "LABOR"
    ).all()

    for cost in existing_costs:
        db.delete(cost)


def group_timesheets_by_user(timesheets: List[Timesheet]) -> Dict:
    """按用户分组工时记录（纯函数）"""
    grouped = {}
    for ts in timesheets:
        if ts.user_id not in grouped:
            grouped[ts.user_id] = []
        grouped[ts.user_id].append(ts)
    return grouped


# ... 其他纯工具函数
```

2. **修改 labor_cost_service.py**:

```python
# app/services/labor_cost_service.py
from app.services.labor_cost.utils import (
    query_approved_timesheets,
    delete_existing_costs,
    group_timesheets_by_user,
)

class LaborCostService:
    @staticmethod
    def calculate_project_labor_cost(db: Session, project_id: int, ...):
        # 直接使用工具函数，无需导入 labor_cost_calculation_service
        timesheets = query_approved_timesheets(db, project_id, start_date, end_date)
        # ...
```

3. **修改 labor_cost_calculation_service.py**:

```python
# app/services/labor_cost_calculation_service.py
from app.services.labor_cost.utils import (
    query_approved_timesheets,
    delete_existing_costs,
    group_timesheets_by_user,
)
from app.services.labor_cost_service import LaborCostService

# 如果需要 LaborCostService，只导入特定方法
def calculate_something(...):
    hourly_rate = LaborCostService.get_user_hourly_rate(db, user_id)
    # ...
```

4. **或者，如果只需要时薪计算，进一步拆分**:

```python
# app/services/labor_cost/rate_calculator.py
"""时薪计算器（独立模块）"""

class HourlyRateCalculator:
    @staticmethod
    def get_user_hourly_rate(db: Session, user_id: int, work_date: Optional[date] = None):
        from app.services.hourly_rate_service import HourlyRateService
        return HourlyRateService.get_user_hourly_rate(db, user_id, work_date)
```

然后两个服务都导入 `HourlyRateCalculator`，避免相互依赖。

**依赖关系**:
```
BEFORE (循环):
labor_cost_calculation_service ←→ labor_cost_service

AFTER (单向):
labor_cost_calculation_service → labor_cost.utils
labor_cost_service → labor_cost.utils
labor_cost_service → labor_cost.rate_calculator
```

---

## 实施优先级

### 立即实施（今天）:

1. ✅ **人工成本服务** - 提取工具模块
   - 风险: 低
   - 工作量: 1-2 小时
   - 收益: 高（彻底解决循环依赖）

### 短期实施（本周）:

2. 🟡 **状态处理器** - 方案 B（延迟导入）
   - 风险: 低
   - 工作量: 30 分钟
   - 收益: 中（快速修复，但不彻底）

### 中期实施（本月）:

3. 🟡 **状态处理器** - 方案 A（事件总线）
   - 风险: 中
   - 工作量: 1-2 天
   - 收益: 高（架构改进 + 彻底解决）

---

## 防止循环依赖的最佳实践

### 1. 使用依赖倒置原则（DIP）

**定义抽象接口**:
```python
# app/services/interfaces.py
from abc import ABC, abstractmethod

class IStatusHandler(ABC):
    @abstractmethod
    def handle_status_change(self, **kwargs):
        pass
```

**依赖抽象而非具体实现**:
```python
class StatusTransitionService:
    def __init__(self, db: Session, handlers: List[IStatusHandler]):
        self.handlers = handlers
```

### 2. 使用 import-linter 工具

在 CI/CD 中添加循环依赖检测:

```bash
pip install import-linter

# .import-linter
[importlinter]
root_package = app
include_external_packages = False

[importlinter:contract:1]
name = Forbid circular dependencies in services
type = forbidden
source_modules =
    app.services
forbidden_modules =
    app.services
```

### 3. 代码审查检查清单

- [ ] 新增的导入是否形成循环？
- [ ] 是否可以使用依赖注入替代直接导入？
- [ ] 工具函数是否应该提取到独立模块？
- [ ] 是否可以使用 TYPE_CHECKING 延迟导入？

### 4. 目录结构最佳实践

```
app/services/
├── core/              # 核心服务（被其他服务依赖）
│   ├── utils.py      # 通用工具函数
│   └── interfaces.py # 抽象接口
├── domain/           # 领域服务（业务逻辑）
│   ├── labor_cost/
│   │   ├── calculator.py
│   │   ├── rate_service.py
│   │   └── utils.py
│   └── status/
│       ├── handlers/
│       └── transition.py
└── integration/      # 集成服务（调用多个领域服务）
    └── project_workflow.py
```

**依赖方向**: `integration → domain → core`

---

## 验证修复效果

运行循环依赖检测:
```bash
python3 analyze_circular_deps.py
```

预期输出:
```
✅ 未发现循环依赖
```

---

## 总结

| 问题 | 严重程度 | 推荐方案 | 预计工时 |
|------|----------|----------|----------|
| 状态处理器循环 | 🟡 中等 | 事件总线（长期）<br>延迟导入（短期） | 2 天（事件总线）<br>30 分钟（延迟导入） |
| 人工成本循环 | 🔴 高 | 提取工具模块 | 1-2 小时 |

**立即行动**: 优先修复人工成本服务的循环依赖，因为实施简单且效果显著。
