# 成本仪表盘配置指南

## 📊 概述

成本仪表盘提供全面的项目成本分析和可视化功能，支持：

- **成本总览**：所有项目成本汇总、预算执行率、超支统计
- **TOP项目分析**：成本最高、超支最严重、利润率排名
- **成本预警**：自动检测超支、预算告急、成本异常波动
- **项目级仪表盘**：单项目成本详情、趋势分析、图表可视化

---

## 🚀 快速开始

### 1. 访问仪表盘

所有仪表盘API都需要 `dashboard:view` 权限：

```bash
# 获取成本总览
GET /api/v1/dashboard/cost/overview

# 获取TOP项目
GET /api/v1/dashboard/cost/top-projects?limit=10

# 获取成本预警
GET /api/v1/dashboard/cost/alerts

# 获取单项目仪表盘
GET /api/v1/dashboard/cost/{project_id}
```

### 2. 启用缓存（可选）

设置Redis环境变量以启用缓存：

```bash
export REDIS_URL=redis://localhost:6379/0
```

缓存默认TTL：5分钟

---

## 📈 数据指标说明

### 成本总览指标

| 指标 | 说明 | 计算方式 |
|------|------|----------|
| total_projects | 活跃项目总数 | 排除未启动(S0)和已关闭(S9)的项目 |
| total_budget | 预算总额 | 所有活跃项目的预算汇总 |
| total_actual_cost | 实际成本总额 | 所有活跃项目的实际成本汇总 |
| budget_execution_rate | 预算执行率 | (实际成本 / 预算) × 100% |
| cost_overrun_count | 超支项目数 | 实际成本 > 预算 |
| cost_normal_count | 正常项目数 | 实际成本 ≤ 90% 预算 |
| cost_alert_count | 预警项目数 | 90% < 实际成本 ≤ 100% 预算 |

### TOP项目排序规则

1. **成本最高**：按 `actual_cost` 降序
2. **超支最严重**：按 `cost_variance_pct` 降序（仅超支项目）
3. **利润率最高**：按 `profit_margin` 降序
4. **利润率最低**：按 `profit_margin` 升序

### 预警级别

| 级别 | 触发条件 | 说明 |
|------|----------|------|
| **high** | 超支 > 20% 或 预算使用 > 95% | 高危预警 |
| **medium** | 10% < 超支 ≤ 20% 或 90% < 预算使用 ≤ 95% | 中危预警 |
| **low** | 超支 ≤ 10% | 低危预警 |

### 预警类型

- **overrun**：成本超支
- **budget_critical**：预算告急
- **abnormal**：成本异常波动（本月成本 > 平均月成本 × 2）

---

## 🎨 图表配置

### 1. 成本结构饼图

显示项目成本按类型（cost_type）分类：

```json
{
  "chart_type": "pie",
  "title": "成本结构分析",
  "data_source": "cost_breakdown",
  "metrics": ["category", "amount", "percentage"]
}
```

**数据示例**：

```json
{
  "cost_breakdown": [
    {"category": "物料成本", "amount": 50000, "percentage": 62.5},
    {"category": "人工成本", "amount": 20000, "percentage": 25.0},
    {"category": "外协成本", "amount": 10000, "percentage": 12.5}
  ]
}
```

### 2. 月度成本柱状图

显示近12个月的预算与实际成本对比：

```json
{
  "chart_type": "bar",
  "title": "月度成本对比",
  "x_axis": "month",
  "y_axis": ["budget", "actual_cost"],
  "data_source": "monthly_costs"
}
```

**数据示例**：

```json
{
  "monthly_costs": [
    {
      "month": "2026-01",
      "budget": 10000,
      "actual_cost": 8500,
      "variance": -1500,
      "variance_pct": -15.0
    }
  ]
}
```

### 3. 成本趋势折线图

显示累计成本趋势：

```json
{
  "chart_type": "line",
  "title": "成本趋势分析",
  "x_axis": "month",
  "y_axis": ["cumulative_cost", "budget_line"],
  "data_source": "cost_trend"
}
```

**数据示例**：

```json
{
  "cost_trend": [
    {
      "month": "2026-01",
      "cumulative_cost": 8500,
      "budget_line": 10000
    },
    {
      "month": "2026-02",
      "cumulative_cost": 18000,
      "budget_line": 20000
    }
  ]
}
```

---

## 🔄 缓存管理

### 缓存键规则

- `dashboard:cost:overview` - 成本总览
- `dashboard:cost:top_projects:limit:{N}` - TOP项目（N=数量）
- `dashboard:cost:alerts` - 成本预警
- `dashboard:cost:project:{project_id}` - 项目仪表盘

### 强制刷新

使用 `force_refresh=true` 参数跳过缓存：

```bash
GET /api/v1/dashboard/cost/overview?force_refresh=true
```

### 清除缓存

```bash
# 清除所有成本仪表盘缓存
DELETE /api/v1/dashboard/cost/cache

# 清除特定模式的缓存
DELETE /api/v1/dashboard/cost/cache?pattern=dashboard:cost:overview
```

---

## 📥 数据导出

### 导出CSV

```bash
POST /api/v1/dashboard/cost/export
Content-Type: application/json

{
  "export_type": "csv",
  "data_type": "cost_overview"  # 可选: cost_overview, top_projects, cost_alerts, project_dashboard
}
```

**支持的数据类型**：

- `cost_overview` - 成本总览
- `top_projects` - TOP项目
- `cost_alerts` - 成本预警
- `project_dashboard` - 项目仪表盘（需要提供 `filters.project_id`）

**导出项目仪表盘示例**：

```json
{
  "export_type": "csv",
  "data_type": "project_dashboard",
  "filters": {
    "project_id": 1
  }
}
```

---

## 🎯 自定义指标

### 保存图表配置

```bash
POST /api/v1/dashboard/cost/chart-config
Content-Type: application/json

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

### 获取图表配置

```bash
GET /api/v1/dashboard/cost/chart-config/{config_id}
```

---

## 🔐 权限要求

| 操作 | 所需权限 |
|------|----------|
| 查看仪表盘 | `dashboard:view` |
| 导出数据 | `dashboard:view` |
| 保存图表配置 | `dashboard:manage` |
| 清除缓存 | `dashboard:manage` |

---

## 📊 前端集成建议

### 推荐图表库

- **ECharts** - 功能强大，支持多种图表
- **Chart.js** - 轻量级，易于上手
- **Highcharts** - 商业级，功能全面

### ECharts 集成示例

```javascript
// 获取成本总览数据
const response = await fetch('/api/v1/dashboard/cost/overview');
const { data } = await response.json();

// 成本结构饼图
const pieOption = {
  title: { text: '成本结构分析' },
  series: [{
    type: 'pie',
    data: data.cost_breakdown.map(item => ({
      name: item.category,
      value: item.amount
    }))
  }]
};

// 月度成本柱状图
const barOption = {
  title: { text: '月度成本对比' },
  xAxis: {
    type: 'category',
    data: data.monthly_costs.map(m => m.month)
  },
  yAxis: { type: 'value' },
  series: [
    {
      name: '预算',
      type: 'bar',
      data: data.monthly_costs.map(m => m.budget)
    },
    {
      name: '实际成本',
      type: 'bar',
      data: data.monthly_costs.map(m => m.actual_cost)
    }
  ]
};
```

---

## ⚠️ 注意事项

1. **缓存时效性**：默认缓存5分钟，实时性要求高的场景使用 `force_refresh=true`
2. **大数据量**：TOP项目查询默认限制50条，避免性能问题
3. **预警阈值**：可根据实际业务调整预警级别的阈值
4. **月度预算**：当前简化为年预算/12，后续可支持按项目实际计划分配

---

## 🐛 故障排查

### 问题：缓存不生效

**原因**：Redis未配置或连接失败

**解决**：
1. 检查 `REDIS_URL` 环境变量
2. 确认Redis服务运行正常
3. 查看应用日志中的缓存相关信息

### 问题：数据不准确

**原因**：成本数据未及时同步

**解决**：
1. 确认 `ProjectCost` 和 `FinancialProjectCost` 数据已正确录入
2. 检查项目的 `actual_cost` 字段是否同步更新
3. 使用 `force_refresh=true` 强制刷新

### 问题：预警数量异常

**原因**：预警条件设置不当

**解决**：
1. 检查项目的 `budget_amount` 是否设置
2. 确认预警阈值符合业务需求
3. 排除测试项目（stage=S0或S9）

---

## 📚 相关文档

- [成本仪表盘API文档](./COST_DASHBOARD_API.md)
- [成本管理模块](../cost/README.md)
- [项目管理模块](../project/README.md)

---

**版本**: v1.0  
**更新日期**: 2026-02-14  
**负责人**: 系统团队
