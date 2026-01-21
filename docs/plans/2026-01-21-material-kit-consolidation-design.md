# 物料/齐套模块整合设计方案

## 一、问题总结

### 1.1 当前模块清单

| 模块 | 文件数 | 功能 | 问题 |
|------|--------|------|------|
| `materials/` | 5 | 物料主数据CRUD | ✅ 无重复 |
| `material_demands/` | 5 | 物料需求计划(MRP) | ✅ 无重复 |
| `kit_rate/` | 4 | 简单齐套率统计 | 🟡 与assembly_kit功能交叉 |
| `kit_check/` | 4 | 工单齐套检查 | 🟡 与assembly_kit功能交叉 |
| `assembly_kit/` | 12 | 工艺阶段齐套分析 | ✅ 最完整实现 |
| `shortage/` | 12 | 缺料管理 | 🔴 与shortage_alerts完全重复 |
| `shortage_alerts/` | 8 | 缺料预警 | 🔴 与shortage完全重复 |

### 1.2 确认的重复代码

#### 🔴 高优先级：shortage vs shortage_alerts（完全重复）

两个模块实现了几乎相同的功能：

| 子功能 | shortage/ | shortage_alerts/ | 重复程度 |
|--------|-----------|------------------|----------|
| 到货跟踪 | `arrival_crud.py` (412行) | `arrivals.py` (326行) | 90%相同 |
| 缺料报告 | `reports/` | `reports.py` | 高度相似 |
| 统计分析 | `statistics*.py` (6个文件) | `statistics.py` | 高度相似 |
| 物料替代 | `substitution*.py` | `substitutions.py` | 高度相似 |
| 物料调拨 | `transfers/` | `transfers/` | 高度相似 |

服务层也有重复：
- `app/services/shortage_report_service.py`
- `app/services/shortage/shortage_reports_service.py`

#### 🟡 中优先级：齐套模块功能交叉

三个模块都计算"齐套率"，但方式不同：

| 模块 | 计算方法 | 核心函数 | 特点 |
|------|----------|----------|------|
| kit_rate | 按数量/金额比例 | `calculate_kit_rate()` | 简单统计 |
| kit_check | 按项数(二元) | `calculate_work_order_kit_rate()` | 工单级 |
| assembly_kit | 按工艺阶段 | `calculate_stage_kit_rates()` | 最完整，支持阻塞性判断 |

### 1.3 齐套率的两个定义

1. **简单齐套率**：已满足数量 / 总需求数量 × 100
2. **工艺齐套率**：按装配阶段分别计算，阻塞性物料100%齐套才能开工

---

## 二、整合方案

### 2.1 目标架构

```
整合后的模块结构：

app/api/v1/endpoints/
├── materials/              # 保留：物料主数据
│   ├── crud.py
│   ├── categories.py
│   ├── suppliers.py
│   └── statistics.py
│
├── material_demands/       # 保留：物料需求计划
│   ├── demands.py
│   ├── forecast.py
│   ├── generate.py
│   └── schedule.py
│
├── kit_management/         # 新建：齐套管理（整合3个模块）
│   ├── __init__.py
│   ├── # --- 齐套率计算 ---
│   ├── rate/
│   │   ├── simple.py       # 简单齐套率（原kit_rate）
│   │   ├── stage_based.py  # 工艺阶段齐套率（原assembly_kit/kit_analysis）
│   │   └── utils.py        # 统一计算工具
│   ├── # --- 齐套检查 ---
│   ├── check/
│   │   ├── work_order.py   # 工单齐套检查（原kit_check）
│   │   ├── project.py      # 项目齐套检查
│   │   └── history.py      # 检查历史
│   ├── # --- 装配配置 ---
│   ├── assembly/
│   │   ├── stages.py       # 装配阶段定义
│   │   ├── templates.py    # 装配模板
│   │   ├── mapping.py      # 物料阶段映射
│   │   └── attributes.py   # BOM装配属性
│   ├── # --- 看板与统计 ---
│   ├── dashboard.py        # 统一看板
│   ├── statistics.py       # 统一统计
│   └── scheduling.py       # 排产建议
│
├── shortage_management/    # 新建：缺料管理（整合2个模块）
│   ├── __init__.py
│   ├── # --- 缺料上报与处理 ---
│   ├── reports/
│   │   ├── crud.py         # 缺料上报CRUD
│   │   └── workflow.py     # 处理流程
│   ├── # --- 到货跟踪 ---
│   ├── arrivals/
│   │   ├── crud.py         # 到货记录CRUD
│   │   ├── follow_up.py    # 跟催记录
│   │   └── receive.py      # 收货确认
│   ├── # --- 解决方案 ---
│   ├── solutions/
│   │   ├── substitution.py # 物料替代
│   │   └── transfer.py     # 物料调拨
│   ├── # --- 预警 ---
│   ├── alerts/
│   │   ├── rules.py        # 预警规则
│   │   ├── triggers.py     # 预警触发
│   │   └── notifications.py # 通知发送
│   ├── # --- 统计 ---
│   ├── statistics/
│   │   ├── dashboard.py    # 统计看板
│   │   ├── supplier.py     # 供应商统计
│   │   └── daily.py        # 日报
│   └── utils.py
```

### 2.2 服务层整合

```
整合后的服务结构：

app/services/
├── kit_management/                 # 新建
│   ├── __init__.py
│   ├── kit_rate_service.py         # 统一齐套率计算
│   ├── kit_check_service.py        # 齐套检查服务
│   ├── assembly_config_service.py  # 装配配置服务
│   ├── kit_optimizer_service.py    # 齐套优化建议
│   └── kit_snapshot_service.py     # 历史快照服务
│
├── shortage_management/            # 新建
│   ├── __init__.py
│   ├── shortage_service.py         # 缺料主服务（整合原有2个）
│   ├── arrival_service.py          # 到货跟踪服务
│   ├── alert_service.py            # 预警服务
│   └── solution_service.py         # 解决方案服务

# 删除：
# - assembly_kit_service.py → 移入 kit_management/
# - assembly_kit_optimizer.py → 移入 kit_management/
# - assembly_attr_recommender.py → 移入 kit_management/
# - kit_rate_statistics_service.py → 移入 kit_management/
# - shortage_report_service.py → 移入 shortage_management/
# - shortage/shortage_reports_service.py → 删除（重复）
# - shortage/shortage_alerts_service.py → 移入 shortage_management/
# - shortage/shortage_management_service.py → 移入 shortage_management/
```

### 2.3 API路由整合

```python
# app/api/v1/api.py 中的路由变更

# 删除：
# - kit_rate.router
# - kit_check.router
# - assembly_kit (从包导入)
# - shortage.router
# - shortage_alerts.router

# 新增：
from app.api.v1.endpoints.kit_management import router as kit_management_router
from app.api.v1.endpoints.shortage_management import router as shortage_management_router

api_router.include_router(kit_management_router, prefix="/kit", tags=["kit-management"])
api_router.include_router(shortage_management_router, prefix="/shortage", tags=["shortage-management"])
```

### 2.4 新API端点设计

#### 齐套管理 `/api/v1/kit/`

```
# 齐套率查询
GET  /kit/rate/project/{project_id}          # 项目齐套率
GET  /kit/rate/machine/{machine_id}          # 机台齐套率
GET  /kit/rate/work-order/{work_order_id}    # 工单齐套率
GET  /kit/rate/stage-analysis                # 工艺阶段齐套分析

# 齐套检查
POST /kit/check/execute                       # 执行齐套检查
GET  /kit/check/history                       # 检查历史
POST /kit/check/confirm-start                 # 确认开工

# 装配配置
GET  /kit/assembly/stages                     # 装配阶段列表
POST /kit/assembly/stages                     # 创建阶段
GET  /kit/assembly/templates                  # 装配模板
POST /kit/assembly/mapping                    # 物料阶段映射
PUT  /kit/assembly/bom-attrs/{bom_item_id}   # BOM装配属性

# 看板统计
GET  /kit/dashboard                           # 齐套看板
GET  /kit/statistics                          # 统计数据
GET  /kit/trend                               # 趋势分析

# 排产建议
GET  /kit/scheduling/suggestions              # 排产建议
POST /kit/scheduling/accept                   # 接受建议
```

#### 缺料管理 `/api/v1/shortage/`

```
# 缺料上报
POST /shortage/reports                        # 创建缺料上报
GET  /shortage/reports                        # 缺料列表
GET  /shortage/reports/{id}                   # 缺料详情
PUT  /shortage/reports/{id}/status            # 更新状态

# 到货跟踪
POST /shortage/arrivals                       # 创建到货记录
GET  /shortage/arrivals                       # 到货列表
PUT  /shortage/arrivals/{id}/receive          # 确认收货
POST /shortage/arrivals/{id}/follow-up        # 添加跟催
GET  /shortage/arrivals/delayed               # 延迟列表

# 解决方案
POST /shortage/solutions/substitute           # 物料替代
POST /shortage/solutions/transfer             # 物料调拨
GET  /shortage/solutions/suggestions          # 解决建议

# 预警
GET  /shortage/alerts                         # 预警列表
GET  /shortage/alerts/rules                   # 预警规则
POST /shortage/alerts/rules                   # 创建规则
PUT  /shortage/alerts/{id}/acknowledge        # 确认预警

# 统计
GET  /shortage/statistics/dashboard           # 统计看板
GET  /shortage/statistics/supplier            # 供应商统计
GET  /shortage/statistics/daily               # 日报
```

---

## 三、实施步骤

### Phase 1：缺料模块整合（高优先级）

**目标**：消除 shortage 和 shortage_alerts 的重复

1. 创建 `shortage_management/` 新模块结构
2. 将 `shortage/` 的实现迁移到新结构（代码更完整）
3. 整合 `shortage_alerts/` 的预警功能
4. 合并服务层代码
5. 更新路由配置
6. 添加旧路由到新路由的重定向（兼容期）
7. 更新测试用例
8. 删除旧模块

### Phase 2：齐套模块整合（中优先级）

**目标**：统一齐套率计算，消除功能交叉

1. 创建 `kit_management/` 新模块结构
2. 将 `assembly_kit/` 作为核心实现迁入
3. 将 `kit_rate/` 的简单计算作为一种计算模式
4. 将 `kit_check/` 的工单检查集成
5. 统一看板和统计接口
6. 更新路由配置
7. 更新测试用例
8. 删除旧模块

### Phase 3：清理与优化

1. 删除所有旧模块代码
2. 更新文档
3. 更新前端调用（如有）
4. 性能优化

---

## 四、兼容性策略

### 4.1 API兼容

保留旧路由一段时间，重定向到新路由：

```python
# 兼容层示例
@router.get("/shortage-alerts/arrivals", deprecated=True)
async def legacy_arrivals(...):
    """[已废弃] 请使用 /shortage/arrivals"""
    return RedirectResponse(url="/api/v1/shortage/arrivals")
```

### 4.2 数据库兼容

无需数据库迁移，模型保持不变，只是代码组织结构调整。

---

## 五、预期收益

| 指标 | 整合前 | 整合后 | 改善 |
|------|--------|--------|------|
| 菜单项数量 | 9个 | 4个 | -56% |
| API模块数 | 7个 | 4个 | -43% |
| 服务文件数 | 11个 | 8个 | -27% |
| 重复代码 | ~2000行 | 0 | -100% |
| 维护复杂度 | 高 | 低 | 显著降低 |

---

## 六、风险与应对

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|----------|
| 前端调用断裂 | 中 | 高 | 保留兼容层，逐步迁移 |
| 业务逻辑差异 | 低 | 中 | 详细对比代码后合并 |
| 测试覆盖不足 | 中 | 中 | 整合前补充测试 |

---

## 七、决策确认

| 决策项 | 结论 |
|--------|------|
| **齐套率计算** | ✅ 保留三种计算方式，统一接口，同时计算输出 |
| **模块命名** | ✅ 使用 `kit_management` 和 `shortage_management` |
| **实施顺序** | ✅ Phase 1: 缺料模块 → Phase 2: 齐套模块 |
| **兼容期长度** | 建议2-4周，待确认 |

### 7.1 齐套率统一输出格式

整合后的齐套率查询将同时返回三种计算结果：

```python
class KitRateResponse(BaseModel):
    """统一齐套率响应"""
    # 简单齐套率（按数量）
    simple_rate: KitRateSimple
    # 简单齐套率（按金额）
    amount_rate: KitRateSimple
    # 工艺阶段齐套率
    stage_rate: KitRateStageAnalysis
    # 汇总
    summary: KitRateSummary

class KitRateSimple(BaseModel):
    """简单齐套率"""
    total_items: int
    fulfilled_items: int
    shortage_items: int
    in_transit_items: int
    kit_rate: float  # 百分比
    kit_status: str  # complete/partial/shortage

class KitRateStageAnalysis(BaseModel):
    """工艺阶段齐套率"""
    overall_kit_rate: float
    blocking_kit_rate: float
    can_start: bool
    current_workable_stage: Optional[str]
    first_blocked_stage: Optional[str]
    stage_details: List[StageKitRate]

class KitRateSummary(BaseModel):
    """齐套率汇总"""
    recommended_rate: float  # 推荐使用的齐套率（工艺阶段的blocking_kit_rate）
    start_recommendation: str  # 开工建议
    risk_level: str  # 风险等级
```
