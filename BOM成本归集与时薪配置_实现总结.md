# BOM成本归集与时薪配置功能实现总结

## 概述

本次实现了成本管理模块的两个 P1 优先级功能：
1. **BOM成本自动汇总**：从BOM自动汇总材料成本到项目成本
2. **时薪配置管理**：支持按用户、角色、部门配置时薪

## 实现内容

### 1. BOM成本自动汇总

#### 1.1 成本归集服务扩展

**文件**: `app/services/cost_collection_service.py`

新增方法：

- **`collect_from_bom`** - 从BOM归集材料成本
  - 只归集已发布的BOM（status="RELEASED"）
  - 计算BOM总成本（从明细汇总或使用表头total_amount）
  - 支持更新已存在的成本记录（幂等性）
  - 自动更新项目实际成本

#### 1.2 API集成

**文件**: `app/api/v1/endpoints/bom.py`

在BOM发布时（`release_bom`函数）自动触发成本归集：

```python
# BOM发布时自动归集材料成本
try:
    from app.services.cost_collection_service import CostCollectionService
    CostCollectionService.collect_from_bom(
        db, bom_id, created_by=current_user.id
    )
except Exception as e:
    # 成本归集失败不影响BOM发布，只记录错误
    import logging
    logging.warning(f"BOM发布后成本归集失败：{str(e)}")
```

#### 1.3 功能特性

- **自动触发**：BOM发布时自动归集，无需手动操作
- **幂等性**：如果已存在该BOM的成本记录，会更新而不是重复创建
- **成本计算**：优先使用BOM表头的total_amount，否则从明细汇总
- **错误处理**：成本归集失败不影响BOM发布流程

### 2. 时薪配置管理

#### 2.1 数据模型

**文件**: `app/models/hourly_rate.py`

- **HourlyRateConfig**（时薪配置表）
  - 配置类型：USER（用户）、ROLE（角色）、DEPT（部门）、DEFAULT（默认）
  - 支持生效日期和失效日期
  - 支持启用/禁用状态

#### 2.2 时薪配置服务

**文件**: `app/services/hourly_rate_service.py`

**HourlyRateService** 类提供以下方法：

- **`get_user_hourly_rate`** - 获取用户时薪（按优先级）
  - 优先级：用户配置 > 角色配置 > 部门配置 > 默认配置
  - 支持按工作日期判断配置是否在有效期内
  - 如果都没有配置，使用默认值100元/小时

#### 2.3 API 端点

**文件**: `app/api/v1/endpoints/hourly_rate.py`

- `GET /api/v1/hourly-rates/` - 获取时薪配置列表（支持分页、筛选）
- `POST /api/v1/hourly-rates/` - 创建时薪配置
- `GET /api/v1/hourly-rates/{config_id}` - 获取时薪配置详情
- `PUT /api/v1/hourly-rates/{config_id}` - 更新时薪配置
- `DELETE /api/v1/hourly-rates/{config_id}` - 删除时薪配置
- `GET /api/v1/hourly-rates/users/{user_id}/hourly-rate` - 获取用户时薪（按优先级）

#### 2.4 工时成本计算服务更新

**文件**: `app/services/labor_cost_service.py`

更新了 `get_user_hourly_rate` 方法，改为从时薪配置服务读取：

```python
@staticmethod
def get_user_hourly_rate(db: Session, user_id: int, work_date: Optional[date] = None) -> Decimal:
    """获取用户时薪（从时薪配置服务读取）"""
    from app.services.hourly_rate_service import HourlyRateService
    return HourlyRateService.get_user_hourly_rate(db, user_id, work_date)
```

#### 2.5 功能特性

- **多层级配置**：支持用户、角色、部门、默认四个层级
- **优先级机制**：自动按优先级查找配置
- **时间有效性**：支持按日期判断配置是否有效
- **防重复配置**：同一类型同一对象的配置不能重复

## 使用示例

### 1. BOM发布自动归集成本

BOM发布时会自动归集成本，无需手动操作：

```bash
POST /api/v1/bom/{bom_id}/release
```

系统会自动：
1. 检查BOM状态是否为RELEASED
2. 计算BOM总成本
3. 创建或更新项目成本记录
4. 更新项目实际成本

### 2. 创建用户时薪配置

```bash
POST /api/v1/hourly-rates/
{
    "config_type": "USER",
    "user_id": 1,
    "hourly_rate": 150.00,
    "effective_date": "2025-01-01",
    "remark": "高级工程师时薪"
}
```

### 3. 创建角色时薪配置

```bash
POST /api/v1/hourly-rates/
{
    "config_type": "ROLE",
    "role_id": 5,
    "hourly_rate": 120.00,
    "effective_date": "2025-01-01",
    "remark": "工程师角色默认时薪"
}
```

### 4. 创建部门时薪配置

```bash
POST /api/v1/hourly-rates/
{
    "config_type": "DEPT",
    "dept_id": 3,
    "hourly_rate": 100.00,
    "effective_date": "2025-01-01",
    "remark": "研发部门默认时薪"
}
```

### 5. 创建默认时薪配置

```bash
POST /api/v1/hourly-rates/
{
    "config_type": "DEFAULT",
    "hourly_rate": 80.00,
    "effective_date": "2025-01-01",
    "remark": "系统默认时薪"
}
```

### 6. 获取用户时薪

```bash
GET /api/v1/hourly-rates/users/1/hourly-rate
```

系统会按优先级查找：
1. 用户配置（如果存在）
2. 角色配置（如果用户有角色）
3. 部门配置（如果用户有部门）
4. 默认配置（如果存在）
5. 系统默认值（100元/小时）

## 技术要点

1. **BOM成本归集**：
   - 只归集已发布的BOM
   - 成本类型：MATERIAL
   - 成本分类：BOM
   - 来源模块：BOM
   - 来源类型：BOM_COST

2. **时薪配置优先级**：
   - 用户配置优先级最高
   - 如果用户没有配置，查找角色配置（用户可能有多个角色，取第一个有效的）
   - 如果角色没有配置，查找部门配置
   - 如果部门没有配置，查找默认配置
   - 如果都没有，使用系统默认值100元/小时

3. **时间有效性判断**：
   - 支持生效日期和失效日期
   - 如果配置有生效日期，工作日期必须 >= 生效日期
   - 如果配置有失效日期，工作日期必须 <= 失效日期
   - 如果配置没有日期限制，则始终有效

## 文件清单

### 新增文件
- `app/models/hourly_rate.py` - 时薪配置模型
- `app/schemas/hourly_rate.py` - 时薪配置 Schema
- `app/api/v1/endpoints/hourly_rate.py` - 时薪配置管理 API
- `app/services/hourly_rate_service.py` - 时薪配置服务

### 修改文件
- `app/services/cost_collection_service.py` - 添加BOM成本归集方法
- `app/services/labor_cost_service.py` - 更新时薪获取逻辑
- `app/api/v1/endpoints/bom.py` - 在BOM发布时集成成本归集
- `app/api/v1/api.py` - 注册时薪配置路由
- `app/models/__init__.py` - 导出时薪配置模型

## 完成状态

✅ **P1 优先级功能已完成**：
- ✅ BOM成本自动汇总：BOM发布时自动归集材料成本
- ✅ 时薪配置管理：支持按用户、角色、部门配置时薪，工时成本计算自动使用配置

所有代码已通过语法检查，无错误。功能已实现并可用。

## 后续优化建议

1. **BOM版本成本对比**：支持对比不同BOM版本的成本差异
2. **时薪历史记录**：记录时薪配置变更历史
3. **批量时薪配置**：支持批量导入时薪配置
4. **时薪审批流程**：时薪配置变更需要审批
5. **加班时薪配置**：区分正常工时和加班工时的时薪配置






