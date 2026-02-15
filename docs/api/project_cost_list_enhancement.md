# 项目列表成本显示增强 API文档

## 概述

在项目列表接口中新增成本信息展示功能，支持：
- ✅ 成本摘要展示（总成本、预算、使用率、是否超支等）
- ✅ 按成本排序
- ✅ 按预算使用率排序
- ✅ 仅显示超支项目
- ✅ 批量查询优化（避免N+1查询）

## API端点

### GET /api/v1/projects/

获取项目列表（支持成本展示和筛选）

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量 |
| keyword | string | 否 | - | 关键词搜索（项目名称/编码/合同编号） |
| customer_id | int | 否 | - | 客户ID筛选 |
| stage | string | 否 | - | 阶段筛选（S1-S9） |
| status | string | 否 | - | 状态筛选（ST01-ST30） |
| health | string | 否 | - | 健康度筛选（H1-H4） |
| project_type | string | 否 | - | 项目类型筛选 |
| pm_id | int | 否 | - | 项目经理ID筛选 |
| min_progress | float | 否 | - | 最小进度百分比 |
| max_progress | float | 否 | - | 最大进度百分比 |
| is_active | bool | 否 | - | 是否启用 |
| **include_cost** | **bool** | **否** | **false** | **是否包含成本摘要** |
| **overrun_only** | **bool** | **否** | **false** | **仅显示超支项目** |
| **sort** | **string** | **否** | **created_at_desc** | **排序方式** |

#### 排序选项（sort参数）

| 值 | 描述 |
|----|------|
| `created_at_desc` | 按创建时间倒序（默认） |
| `cost_desc` | 按实际成本倒序（从高到低） |
| `cost_asc` | 按实际成本正序（从低到高） |
| `budget_used_pct` | 按预算使用率倒序（从高到低） |

#### 响应示例

```json
{
  "items": [
    {
      "id": 123,
      "project_code": "PRJ-2024-001",
      "project_name": "XX测试设备",
      "customer_name": "某某公司",
      "stage": "S3",
      "health": "H2",
      "progress_pct": 60.00,
      "pm_name": "张三",
      "pm_id": 10,
      "sales_id": 15,
      "te_id": 20,
      "cost_summary": {
        "total_cost": 750000.00,
        "budget": 900000.00,
        "budget_used_pct": 83.33,
        "overrun": false,
        "variance": -150000.00,
        "variance_pct": -16.67,
        "cost_breakdown": {
          "labor": 400000.00,
          "material": 250000.00,
          "equipment": 100000.00,
          "travel": 0.00,
          "other": 0.00
        }
      }
    },
    {
      "id": 124,
      "project_code": "PRJ-2024-002",
      "project_name": "YY改造项目",
      "customer_name": "另一家公司",
      "stage": "S4",
      "health": "H3",
      "progress_pct": 85.00,
      "pm_name": "李四",
      "pm_id": 11,
      "sales_id": 16,
      "te_id": null,
      "cost_summary": {
        "total_cost": 1200000.00,
        "budget": 1000000.00,
        "budget_used_pct": 120.00,
        "overrun": true,
        "variance": 200000.00,
        "variance_pct": 20.00,
        "cost_breakdown": {
          "labor": 600000.00,
          "material": 450000.00,
          "equipment": 150000.00,
          "travel": 0.00,
          "other": 0.00
        }
      }
    }
  ],
  "total": 50,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

### 成本摘要字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| total_cost | decimal | 项目实际成本总额 |
| budget | decimal | 项目预算 |
| budget_used_pct | decimal | 预算使用率（百分比） |
| overrun | bool | 是否超支（实际成本 > 预算） |
| variance | decimal | 成本差异（实际成本 - 预算） |
| variance_pct | decimal | 差异率（百分比） |
| cost_breakdown | object | 成本明细（可选） |

### 成本明细字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| labor | decimal | 人工成本 |
| material | decimal | 材料成本 |
| equipment | decimal | 设备成本 |
| travel | decimal | 差旅成本 |
| other | decimal | 其他成本 |

## 使用场景

### 1. 基础列表（不含成本）

```bash
GET /api/v1/projects/?page=1&page_size=20
```

### 2. 包含成本信息的列表

```bash
GET /api/v1/projects/?include_cost=true
```

### 3. 仅显示超支项目

```bash
GET /api/v1/projects/?include_cost=true&overrun_only=true
```

### 4. 按成本倒序排序（找出高成本项目）

```bash
GET /api/v1/projects/?include_cost=true&sort=cost_desc
```

### 5. 按预算使用率排序（找出预算告急的项目）

```bash
GET /api/v1/projects/?include_cost=true&sort=budget_used_pct
```

### 6. 组合查询：某阶段的超支项目

```bash
GET /api/v1/projects/?include_cost=true&stage=S3&overrun_only=true&sort=cost_desc
```

### 7. 组合查询：某项目经理负责的项目成本

```bash
GET /api/v1/projects/?include_cost=true&pm_id=10&sort=budget_used_pct
```

## 性能优化

### 批量查询策略

- ✅ 使用批量查询获取成本数据（避免N+1查询）
- ✅ 单次查询同时获取 `ProjectCost` 和 `FinancialProjectCost`
- ✅ 使用 `GROUP BY` 聚合成本明细
- ✅ 在内存中组装成本摘要（减少数据库往返）

### 性能指标

| 项目数量 | 查询时间（含成本） | 查询时间（不含成本） |
|---------|-------------------|---------------------|
| 10 | < 100ms | < 50ms |
| 100 | < 500ms | < 200ms |
| 1000 | < 2s | < 500ms |

### 索引建议

为了优化成本查询性能，建议在以下字段上添加索引：

```sql
-- ProjectCost表索引
CREATE INDEX idx_project_cost_project_id ON project_costs(project_id);
CREATE INDEX idx_project_cost_type ON project_costs(project_id, cost_type);

-- FinancialProjectCost表索引
CREATE INDEX idx_financial_cost_project_id ON financial_project_costs(project_id);
CREATE INDEX idx_financial_cost_type ON financial_project_costs(project_id, cost_type);

-- Project表成本字段索引
CREATE INDEX idx_project_actual_cost ON projects(actual_cost);
CREATE INDEX idx_project_budget_amount ON projects(budget_amount);
```

## 错误处理

### 错误码

| HTTP状态码 | 错误说明 |
|-----------|---------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限访问 |
| 500 | 服务器内部错误 |

### 错误响应示例

```json
{
  "detail": "Invalid sort parameter. Must be one of: cost_desc, cost_asc, budget_used_pct, created_at_desc"
}
```

## 注意事项

1. **成本数据来源**：
   - 实际成本 = `Project.actual_cost`（从 `ProjectCost` 和 `FinancialProjectCost` 聚合）
   - 预算 = `Project.budget_amount`

2. **超支判断**：
   - 超支条件：`actual_cost > budget_amount` 且 `budget_amount > 0`
   - 预算为0的项目不计入超支统计

3. **成本明细**：
   - 仅在 `include_cost=true` 时返回
   - 成本类型自动映射到标准分类（labor/material/equipment/travel/other）

4. **缓存策略**：
   - 启用成本查询时不使用缓存
   - 确保数据实时性

5. **数据权限**：
   - 遵循原有的数据权限过滤规则
   - 仅返回当前用户有权查看的项目

## 扩展功能

### 后续可能的增强

1. **导出功能**：支持导出含成本数据的Excel
2. **成本趋势**：在列表中显示成本趋势（本月vs上月）
3. **预警标识**：超支项目、预算告急项目的视觉标识
4. **成本对比**：同类项目成本对比
5. **成本预测**：基于进度预测最终成本

## 测试用例

参见 `tests/unit/test_project_cost_list_enhancement.py`

- ✅ 项目列表（不含成本）
- ✅ 项目列表（含成本）
- ✅ 仅显示超支项目
- ✅ 按成本排序（正序/倒序）
- ✅ 按预算使用率排序
- ✅ 成本数据准确性验证
- ✅ 超支检测准确性
- ✅ 性能测试（100个项目 < 1秒）
- ✅ 组合筛选测试

## 更新日志

### v1.0.0 (2026-02-14)

- ✅ 项目列表API支持成本摘要展示
- ✅ 支持3种排序方式（cost_desc/cost_asc/budget_used_pct）
- ✅ 支持超支项目过滤
- ✅ 批量查询优化，避免N+1查询
- ✅ 完整的单元测试覆盖
- ✅ API文档完成

## 联系方式

如有问题或建议，请联系项目维护者。
