# Dashboard 统一迁移指南

## 概述

本文档指导如何将独立的Dashboard模块迁移到统一Dashboard框架。

## 已完成迁移的模块（4个）

1. ✅ **商务支持** (`business_support`) - `app/services/dashboard_adapters/business_support.py`
2. ✅ **人事管理** (`hr_management`) - `app/services/dashboard_adapters/hr_management.py`
3. ✅ **生产管理** (`production`) - `app/services/dashboard_adapters/production.py`
4. ✅ **PMO** (`pmo`) - `app/services/dashboard_adapters/pmo.py`

## 待迁移模块（6个）

5. ⏳ 装配齐套 (`assembly_kit`)
6. ⏳ 售前分析 (`presales_integration`)
7. ⏳ 人员匹配 (`staff_matching`)
8. ⏳ 战略管理 (`strategy`)
9. ⏳ 管理节律 (`management_rhythm`)
10. ⏳ 缺料管理 (`shortage`)
11. ⏳ 齐套率 (`kit_rate`)

## 迁移步骤

### 第一步：创建适配器类

在 `app/services/dashboard_adapters/` 目录下创建新的适配器文件：

```python
# -*- coding: utf-8 -*-
"""
{模块名称} Dashboard 适配器
"""

from typing import List
from datetime import datetime

from app.schemas.dashboard import (
    DashboardStatCard,
    DashboardWidget,
    DetailedDashboardResponse,
)
from app.services.dashboard_adapter import DashboardAdapter, register_dashboard


@register_dashboard
class YourModuleDashboardAdapter(DashboardAdapter):
    """模块工作台适配器"""

    @property
    def module_id(self) -> str:
        return "your_module"  # 模块ID

    @property
    def module_name(self) -> str:
        return "模块中文名称"

    @property
    def supported_roles(self) -> List[str]:
        return ["role1", "role2", "admin"]  # 支持的角色列表

    def get_stats(self) -> List[DashboardStatCard]:
        """获取统计卡片（顶部快速统计）"""
        # 从原有dashboard代码迁移统计逻辑
        return [
            DashboardStatCard(
                key="stat_key",
                label="统计项名称",
                value=100,
                unit="个",
                icon="icon-name",
                color="blue",
            ),
            # ... 更多统计卡片
        ]

    def get_widgets(self) -> List[DashboardWidget]:
        """获取Widget列表（中间区域）"""
        # 从原有dashboard代码迁移widget逻辑
        return [
            DashboardWidget(
                widget_id="widget_id",
                widget_type="list",  # list/chart/table/stats/custom
                title="Widget标题",
                data={"key": "value"},  # 你的数据
                order=1,  # 显示顺序
                span=12,  # 占据列数（1-24）
            ),
            # ... 更多widgets
        ]

    def get_detailed_data(self) -> DetailedDashboardResponse:
        """获取详细数据（可选实现）"""
        # 如果模块需要提供详细数据接口
        stats_cards = self.get_stats()
        summary = {card.key: card.value for card in stats_cards}

        return DetailedDashboardResponse(
            module=self.module_id,
            module_name=self.module_name,
            summary=summary,
            details={},  # 你的详细数据
            generated_at=datetime.now(),
        )
```

### 第二步：注册适配器

在 `app/services/dashboard_adapters/__init__.py` 中导入新适配器：

```python
from app.services.dashboard_adapters.your_module import (  # noqa: F401
    YourModuleDashboardAdapter,
)

__all__ = [
    # ... 其他适配器
    "YourModuleDashboardAdapter",
]
```

### 第三步：测试

1. **测试统一入口**：
```bash
# 获取角色的dashboard
GET /api/v1/dashboard/unified/{role_code}

# 获取详细数据
GET /api/v1/dashboard/unified/{role_code}/detailed?module_id=your_module

# 列出所有模块
GET /api/v1/dashboard/modules
```

2. **验证数据**：
   - 统计卡片是否正确显示
   - Widget数据是否完整
   - 详细数据是否可访问

### 第四步：保留原路由（可选）

为了向后兼容，可以保留原有的dashboard路由作为别名：

```python
# 在原有dashboard文件中
@router.get("/your-module/dashboard")
async def get_your_module_dashboard_legacy(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    【已废弃】请使用统一Dashboard接口:
    GET /dashboard/unified/{role_code}/detailed?module_id=your_module
    """
    from app.services.dashboard_adapter import dashboard_registry

    adapter = dashboard_registry.get_adapter("your_module", db, current_user)
    if not adapter:
        raise HTTPException(status_code=404, detail="Dashboard not found")

    return ResponseModel(data=adapter.get_detailed_data())
```

## 迁移示例

### 示例1：商务支持Dashboard迁移

**原代码**（`business_support/dashboard.py`）：
```python
@router.get("/dashboard")
async def get_business_support_dashboard(db: Session, current_user: User):
    active_contracts = count_active_contracts(db)
    pending_amount = calculate_pending_amount(db, today)
    # ... 其他统计

    return ResponseModel(data={
        "active_contracts_count": active_contracts,
        "pending_amount": pending_amount,
        # ...
    })
```

**新代码**（适配器）：
```python
@register_dashboard
class BusinessSupportDashboardAdapter(DashboardAdapter):
    def get_stats(self) -> List[DashboardStatCard]:
        active_contracts = count_active_contracts(self.db)
        pending_amount = calculate_pending_amount(self.db, date.today())

        return [
            DashboardStatCard(
                key="active_contracts",
                label="进行中合同",
                value=active_contracts,
                unit="个",
            ),
            DashboardStatCard(
                key="pending_amount",
                label="待回款金额",
                value=f"¥{pending_amount:,.2f}",
            ),
            # ...
        ]
```

## 统一接口说明

### 1. 简化模式（推荐用于首页）

```http
GET /api/v1/dashboard/unified/pmo
```

**响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "role_code": "pmo",
    "role_name": "项目管理办公室",
    "stats": [
      {
        "key": "active_projects",
        "label": "活跃项目",
        "value": 42,
        "unit": "个",
        "icon": "project",
        "color": "blue"
      }
    ],
    "widgets": [
      {
        "widget_id": "risk_projects",
        "widget_type": "list",
        "title": "风险项目",
        "data": [...],
        "order": 1,
        "span": 24
      }
    ],
    "last_updated": "2026-01-25T10:30:00",
    "refresh_interval": 300
  }
}
```

### 2. 详细模式（用于专属页面）

```http
GET /api/v1/dashboard/unified/pmo/detailed?module_id=business_support
```

**响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "module": "business_support",
      "module_name": "商务支持",
      "summary": {
        "active_contracts_count": 15,
        "pending_amount": 1250000.00
      },
      "details": {
        "urgent_tasks": [...],
        "today_todos": [...]
      },
      "generated_at": "2026-01-25T10:30:00"
    }
  ]
}
```

### 3. 模块列表

```http
GET /api/v1/dashboard/modules?role_code=pmo
```

**响应**：
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "module_id": "business_support",
      "module_name": "商务支持",
      "roles": ["business_support", "admin"],
      "endpoint": "/dashboard/unified/{role_code}/detailed?module_id=business_support",
      "is_active": true
    }
  ]
}
```

## 注意事项

1. **权限检查**：适配器中可以访问 `self.current_user`，请根据需要进行权限过滤
2. **数据权限**：对于项目类数据，务必使用 `DataScopeService.filter_projects_by_scope`
3. **错误处理**：单个适配器失败不应影响整体，框架会自动捕获异常
4. **性能优化**：避免在 `get_stats()` 中执行复杂查询，可以使用缓存
5. **向后兼容**：迁移后保留原路由30天，添加废弃警告

## 迁移优先级

**高优先级**（核心业务）：
1. PMO ✅
2. 商务支持 ✅
3. 生产管理 ✅

**中优先级**（常用功能）：
4. 人事管理 ✅
5. 装配齐套
6. 缺料管理

**低优先级**（专项功能）：
7. 售前分析
8. 战略管理
9. 管理节律
10. 人员匹配
11. 齐套率

## 后续计划

1. **第一阶段**（已完成）：核心架构 + 4个模块
2. **第二阶段**（本周）：迁移剩余6个模块
3. **第三阶段**（下周）：前端对接 + 测试
4. **第四阶段**（下下周）：废弃独立路由

## 技术支持

如有问题，请参考：
- 适配器基类：`app/services/dashboard_adapter.py`
- Schema定义：`app/schemas/dashboard.py`
- 已完成示例：`app/services/dashboard_adapters/business_support.py`
