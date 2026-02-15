# 成本仪表盘API文档

## 📖 API概览

| API | 方法 | 路径 | 说明 |
|-----|------|------|------|
| 成本总览 | GET | `/api/v1/dashboard/cost/overview` | 获取所有项目成本汇总 |
| TOP项目 | GET | `/api/v1/dashboard/cost/top-projects` | 获取成本/超支/利润排名TOP 10 |
| 成本预警 | GET | `/api/v1/dashboard/cost/alerts` | 获取成本预警列表 |
| 项目仪表盘 | GET | `/api/v1/dashboard/cost/{project_id}` | 获取单项目成本详情 |
| 导出数据 | POST | `/api/v1/dashboard/cost/export` | 导出CSV/Excel |
| 保存图表配置 | POST | `/api/v1/dashboard/cost/chart-config` | 保存自定义图表 |
| 获取图表配置 | GET | `/api/v1/dashboard/cost/chart-config/{config_id}` | 获取图表配置 |
| 清除缓存 | DELETE | `/api/v1/dashboard/cost/cache` | 清除仪表盘缓存 |

---

## 1. 成本总览

### GET /api/v1/dashboard/cost/overview

获取所有项目的成本总览数据。

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| force_refresh | boolean | 否 | 是否强制刷新缓存，默认false |

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_projects": 25,
    "total_budget": 5000000.00,
    "total_actual_cost": 4200000.00,
    "total_contract_amount": 6000000.00,
    "budget_execution_rate": 84.00,
    "cost_overrun_count": 3,
    "cost_normal_count": 18,
    "cost_alert_count": 4,
    "month_budget": 416666.67,
    "month_actual_cost": 380000.00,
    "month_variance": -36666.67,
    "month_variance_pct": -8.80
  }
}
```

#### 字段说明

- `total_projects`: 活跃项目总数（排除S0和S9阶段）
- `budget_execution_rate`: 预算执行率（%）
- `cost_overrun_count`: 成本超支项目数量
- `cost_normal_count`: 成本正常项目数量（≤90%预算）
- `cost_alert_count`: 成本预警项目数量（90%-100%预算）
- `month_*`: 本月成本相关数据

---

## 2. TOP项目

### GET /api/v1/dashboard/cost/top-projects

获取成本最高、超支最严重、利润率最高/最低的TOP项目。

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | integer | 否 | 10 | 返回数量（1-50） |
| force_refresh | boolean | 否 | false | 是否强制刷新缓存 |

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "top_cost_projects": [
      {
        "project_id": 1,
        "project_code": "P2026001",
        "project_name": "智能制造生产线项目",
        "customer_name": "某科技公司",
        "pm_name": "张三",
        "budget_amount": 500000.00,
        "actual_cost": 480000.00,
        "contract_amount": 600000.00,
        "cost_variance": -20000.00,
        "cost_variance_pct": -4.00,
        "profit": 120000.00,
        "profit_margin": 20.00,
        "stage": "S6",
        "status": "ST06",
        "health": "H2"
      }
    ],
    "top_overrun_projects": [
      {
        "project_id": 5,
        "project_code": "P2026005",
        "project_name": "超支项目示例",
        "budget_amount": 200000.00,
        "actual_cost": 250000.00,
        "cost_variance": 50000.00,
        "cost_variance_pct": 25.00,
        "profit": -10000.00,
        "profit_margin": -4.17
      }
    ],
    "top_profit_margin_projects": [...],
    "bottom_profit_margin_projects": [...]
  }
}
```

#### 字段说明

- `cost_variance`: 成本偏差（实际成本 - 预算）
- `cost_variance_pct`: 成本偏差率（%）
- `profit`: 毛利润（合同金额 - 实际成本）
- `profit_margin`: 利润率（%）

---

## 3. 成本预警

### GET /api/v1/dashboard/cost/alerts

获取成本预警列表，包括超支、预算告急、异常波动。

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| force_refresh | boolean | 否 | 是否强制刷新缓存 |

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "total_alerts": 7,
    "high_alerts": 2,
    "medium_alerts": 3,
    "low_alerts": 2,
    "alerts": [
      {
        "project_id": 3,
        "project_code": "P2026003",
        "project_name": "严重超支项目",
        "alert_type": "overrun",
        "alert_level": "high",
        "budget_amount": 300000.00,
        "actual_cost": 375000.00,
        "variance": 75000.00,
        "variance_pct": 25.00,
        "message": "项目成本严重超支 25.0%",
        "created_at": "2026-02-14"
      },
      {
        "project_id": 7,
        "project_code": "P2026007",
        "project_name": "预算告急项目",
        "alert_type": "budget_critical",
        "alert_level": "high",
        "budget_amount": 150000.00,
        "actual_cost": 145000.00,
        "variance": -5000.00,
        "variance_pct": -3.33,
        "message": "预算即将用尽，已使用 96.7%",
        "created_at": "2026-02-14"
      },
      {
        "project_id": 12,
        "project_code": "P2026012",
        "project_name": "成本波动项目",
        "alert_type": "abnormal",
        "alert_level": "high",
        "budget_amount": 400000.00,
        "actual_cost": 350000.00,
        "variance": -50000.00,
        "variance_pct": -12.50,
        "message": "本月成本异常增长，为平均月成本的 2.5 倍",
        "created_at": "2026-02-14"
      }
    ]
  }
}
```

#### 预警类型

- **overrun**: 成本超支
  - high: 超支 > 20%
  - medium: 10% < 超支 ≤ 20%
  - low: 超支 ≤ 10%

- **budget_critical**: 预算告急
  - high: 已使用 > 95%
  - medium: 90% < 已使用 ≤ 95%

- **abnormal**: 成本异常波动
  - high: 本月成本 > 平均月成本 × 2

---

## 4. 项目成本仪表盘

### GET /api/v1/dashboard/cost/{project_id}

获取单个项目的详细成本仪表盘数据。

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | integer | 是 | 项目ID |

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| force_refresh | boolean | 否 | 是否强制刷新缓存 |

#### 响应示例

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "project_id": 1,
    "project_code": "P2026001",
    "project_name": "智能制造生产线项目",
    "budget_amount": 500000.00,
    "actual_cost": 480000.00,
    "contract_amount": 600000.00,
    "variance": -20000.00,
    "variance_pct": -4.00,
    
    "cost_breakdown": [
      {"category": "物料成本", "amount": 300000.00, "percentage": 62.50},
      {"category": "人工成本", "amount": 120000.00, "percentage": 25.00},
      {"category": "外协成本", "amount": 40000.00, "percentage": 8.33},
      {"category": "其他", "amount": 20000.00, "percentage": 4.17}
    ],
    
    "monthly_costs": [
      {
        "month": "2025-03",
        "budget": 41666.67,
        "actual_cost": 35000.00,
        "variance": -6666.67,
        "variance_pct": -16.00
      },
      {
        "month": "2025-04",
        "budget": 41666.67,
        "actual_cost": 42000.00,
        "variance": 333.33,
        "variance_pct": 0.80
      }
    ],
    
    "cost_trend": [
      {"month": "2025-03", "cumulative_cost": 35000.00, "budget_line": 41666.67},
      {"month": "2025-04", "cumulative_cost": 77000.00, "budget_line": 83333.34}
    ],
    
    "received_amount": 360000.00,
    "invoiced_amount": 420000.00,
    "gross_profit": 120000.00,
    "profit_margin": 20.00
  }
}
```

#### 字段说明

- `cost_breakdown`: 成本结构分类（饼图数据）
- `monthly_costs`: 月度成本对比（柱状图数据）
- `cost_trend`: 累计成本趋势（折线图数据）
- `received_amount`: 已收款金额
- `invoiced_amount`: 已开票金额
- `gross_profit`: 毛利润
- `profit_margin`: 利润率（%）

---

## 5. 导出数据

### POST /api/v1/dashboard/cost/export

导出仪表盘数据为CSV或Excel格式。

#### 请求体

```json
{
  "export_type": "csv",
  "data_type": "cost_overview",
  "filters": {}
}
```

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| export_type | string | 是 | 导出格式: csv, excel |
| data_type | string | 是 | 数据类型（见下表） |
| filters | object | 否 | 筛选条件 |

#### 支持的数据类型

| data_type | 说明 | 必需的filters |
|-----------|------|---------------|
| cost_overview | 成本总览 | - |
| top_projects | TOP项目 | - |
| cost_alerts | 成本预警 | - |
| project_dashboard | 项目仪表盘 | project_id |

#### 导出项目仪表盘示例

```json
{
  "export_type": "csv",
  "data_type": "project_dashboard",
  "filters": {
    "project_id": 1
  }
}
```

#### 响应

```
Content-Type: text/csv
Content-Disposition: attachment; filename=cost_overview.csv

total_projects,total_budget,total_actual_cost,...
25,5000000.00,4200000.00,...
```

---

## 6. 保存图表配置

### POST /api/v1/dashboard/cost/chart-config

保存自定义图表配置。

#### 请求体

```json
{
  "chart_type": "bar",
  "title": "自定义月度成本",
  "x_axis": "month",
  "y_axis": "cost",
  "data_source": "monthly_costs",
  "filters": {
    "stage": "S3"
  },
  "custom_metrics": ["budget", "actual_cost", "variance"]
}
```

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| chart_type | string | 是 | 图表类型: bar, line, pie, area |
| title | string | 是 | 图表标题 |
| x_axis | string | 否 | X轴字段 |
| y_axis | string | 否 | Y轴字段 |
| data_source | string | 是 | 数据源 |
| filters | object | 否 | 筛选条件 |
| custom_metrics | array | 否 | 自定义指标列表 |

#### 响应

```json
{
  "code": 200,
  "message": "图表配置已保存",
  "data": {
    "chart_type": "bar",
    "title": "自定义月度成本",
    ...
  }
}
```

---

## 7. 获取图表配置

### GET /api/v1/dashboard/cost/chart-config/{config_id}

获取保存的图表配置。

#### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| config_id | integer | 是 | 配置ID |

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "bar",
    "title": "月度成本对比",
    "x_axis": "month",
    "y_axis": "cost",
    "data_source": "monthly_costs",
    "filters": {},
    "custom_metrics": ["budget", "actual_cost", "variance"]
  }
}
```

---

## 8. 清除缓存

### DELETE /api/v1/dashboard/cost/cache

清除仪表盘缓存。

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| pattern | string | 否 | dashboard:cost:* | 缓存键模式 |

#### 响应

```json
{
  "code": 200,
  "message": "已清除 5 个缓存键",
  "data": {
    "deleted_count": 5
  }
}
```

#### 缓存键模式

- `dashboard:cost:*` - 所有成本仪表盘缓存
- `dashboard:cost:overview` - 仅成本总览
- `dashboard:cost:top_projects:*` - 所有TOP项目缓存
- `dashboard:cost:project:*` - 所有项目仪表盘缓存

---

## 🔐 权限要求

所有API都需要有效的JWT token：

```
Authorization: Bearer <your_jwt_token>
```

| API | 所需权限 |
|-----|----------|
| 成本总览 | dashboard:view |
| TOP项目 | dashboard:view |
| 成本预警 | dashboard:view |
| 项目仪表盘 | dashboard:view |
| 导出数据 | dashboard:view |
| 保存图表配置 | dashboard:manage |
| 获取图表配置 | dashboard:view |
| 清除缓存 | dashboard:manage |

---

## 🚨 错误码

| HTTP状态码 | 错误码 | 说明 |
|-----------|--------|------|
| 200 | 200 | 请求成功 |
| 400 | 400 | 请求参数错误 |
| 401 | 401 | 未认证 |
| 403 | 403 | 权限不足 |
| 404 | 404 | 资源不存在 |
| 500 | 500 | 服务器内部错误 |

### 错误响应示例

```json
{
  "code": 404,
  "message": "项目 999 不存在",
  "data": null
}
```

---

## 📌 注意事项

1. **缓存时效**：默认缓存5分钟，使用 `force_refresh=true` 可强制刷新
2. **分页限制**：TOP项目最多返回50条
3. **数据实时性**：成本数据来自 `ProjectCost` 和 `FinancialProjectCost` 表
4. **权限检查**：所有接口都需要相应权限，否则返回403

---

## 🧪 测试示例

### cURL示例

```bash
# 获取成本总览
curl -X GET "http://localhost:8000/api/v1/dashboard/cost/overview" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 获取TOP 5项目
curl -X GET "http://localhost:8000/api/v1/dashboard/cost/top-projects?limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 导出成本预警
curl -X POST "http://localhost:8000/api/v1/dashboard/cost/export" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"export_type":"csv","data_type":"cost_alerts"}' \
  --output alerts.csv

# 清除缓存
curl -X DELETE "http://localhost:8000/api/v1/dashboard/cost/cache" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Python示例

```python
import requests

API_BASE = "http://localhost:8000/api/v1"
TOKEN = "YOUR_TOKEN"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

# 获取成本总览
response = requests.get(f"{API_BASE}/dashboard/cost/overview", headers=HEADERS)
overview = response.json()["data"]

print(f"总项目数: {overview['total_projects']}")
print(f"预算执行率: {overview['budget_execution_rate']}%")

# 获取预警
response = requests.get(f"{API_BASE}/dashboard/cost/alerts", headers=HEADERS)
alerts = response.json()["data"]

print(f"高危预警: {alerts['high_alerts']} 个")
```

---

**版本**: v1.0  
**更新日期**: 2026-02-14  
**维护团队**: 系统开发部
