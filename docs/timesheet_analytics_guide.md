# 工时分析与预测系统 - 完整指南

## 目录
1. [系统概述](#系统概述)
2. [分析功能详解](#分析功能详解)
3. [预测算法说明](#预测算法说明)
4. [API使用文档](#api使用文档)
5. [数据模型](#数据模型)
6. [使用示例](#使用示例)
7. [最佳实践](#最佳实践)

---

## 系统概述

工时分析与预测系统提供全面的工时数据分析和智能预测功能，帮助管理者：
- 📊 实时掌握工时趋势和分布
- 👥 优化人员负荷配置
- 🎯 提升工时效率和资源利用率
- ⚠️ 提前识别人员饱和度风险
- 📈 科学预测项目工时需求

### 核心特性

#### 6种分析维度
1. **工时趋势分析** - 多周期（日/周/月/季/年）趋势追踪
2. **人员负荷分析** - 工时饱和度热力图
3. **工时效率对比** - 计划vs实际对比
4. **加班统计分析** - 加班时长、率、趋势
5. **部门工时对比** - 跨部门对比分析
6. **项目工时分布** - 项目工时占比、集中度

#### 4种预测功能
1. **项目工时预测** - 3种算法（历史平均/线性回归/趋势预测）
2. **完工时间预测** - 基于进度和消耗速度
3. **负荷预警** - 人员饱和度预警
4. **缺口分析** - 需求vs可用工时

---

## 分析功能详解

### 1. 工时趋势分析

**功能说明：**
- 支持多种周期类型：日度、周度、月度、季度、年度
- 可按人员、项目、部门等维度筛选
- 自动计算趋势方向（上升/稳定/下降）和变化率

**关键指标：**
- `total_hours`: 总工时
- `average_hours`: 平均工时
- `max_hours` / `min_hours`: 最大/最小工时
- `trend`: 趋势（INCREASING/STABLE/DECREASING）
- `change_rate`: 变化率（%）

**趋势判断算法：**
```python
# 将数据分为前后两半，对比平均值
mid = len(results) // 2
first_half_avg = avg(results[:mid])
second_half_avg = avg(results[mid:])
change_rate = (second_half_avg - first_half_avg) / first_half_avg * 100

if change_rate > 5:
    trend = 'INCREASING'  # 上升
elif change_rate < -5:
    trend = 'DECREASING'  # 下降
else:
    trend = 'STABLE'      # 稳定
```

**可视化输出：**
- 折线图：显示总工时、正常工时、加班工时三条曲线

---

### 2. 人员负荷分析

**功能说明：**
- 生成人员×日期的工时热力图
- 计算工时饱和度（实际工时/标准工时×100%）
- 识别超负荷人员

**饱和度计算：**
```python
# 标准工时 = 工作日数 × 每日8小时
work_days = days_count * 5 / 7  # 假设周末占2/7
standard_hours = work_days * 8
saturation = (actual_hours / standard_hours) * 100
```

**负荷等级：**
- 🟢 正常：60% ≤ 饱和度 < 85%
- 🟡 中等负荷：85% ≤ 饱和度 < 100%
- 🟠 高负荷：100% ≤ 饱和度 < 120%
- 🔴 严重超负荷：饱和度 ≥ 120%

**可视化输出：**
- 热力图：颜色深浅表示工时多少
- 统计信息：总人数、平均工时、超负荷人数及比例
- 超负荷人员列表（TOP 10）

---

### 3. 工时效率对比

**功能说明：**
- 对比计划工时与实际工时
- 计算工时偏差和效率率
- 提供优化建议

**效率率计算：**
```python
efficiency_rate = (planned_hours / actual_hours) * 100

# 效率率解读：
# > 100%: 实际用时少于计划，效率高
# = 100%: 符合计划
# < 100%: 实际用时超出计划，效率低
```

**偏差分析：**
```python
variance_hours = actual_hours - planned_hours
variance_rate = (variance_hours / planned_hours) * 100

# 偏差率解读：
# > 20%: 严重偏差，需要加强管控
# 10% ~ 20%: 中等偏差
# < 10%: 正常范围
```

**智能建议：**
- 效率率 < 80% → "工时效率较低，建议优化工作流程"
- 效率率 > 120% → "计划工时可能过于保守"
- 偏差率 > 20% → "工时偏差较大，需要加强管控"

---

### 4. 加班统计分析

**功能说明：**
- 统计总加班时长、周末加班、节假日加班
- 计算加班率和人均加班
- 识别加班TOP人员
- 分析加班趋势

**加班率计算：**
```python
overtime_rate = (overtime_hours / total_hours) * 100
```

**人均加班：**
```python
avg_overtime = total_overtime_hours / user_count
```

**可视化输出：**
- 加班趋势折线图（每日加班工时）
- TOP 10加班人员列表
- 加班类型分布（正常加班/周末/节假日）

---

### 5. 部门工时对比

**功能说明：**
- 对比各部门的工时总量、人均工时、加班率
- 生成部门排名
- 识别高负荷部门

**关键指标：**
- `total_hours`: 部门总工时
- `user_count`: 部门人数
- `avg_hours_per_person`: 人均工时
- `overtime_rate`: 部门加班率
- `rank`: 部门排名（按总工时）

**可视化输出：**
- 堆叠柱状图：正常工时 + 加班工时
- 部门排名表

---

### 6. 项目工时分布

**功能说明：**
- 分析各项目的工时占比
- 计算工时集中度指数
- 识别核心项目

**集中度指数：**
```python
# 前3个项目的工时占比之和
top3_percentage = sum(top3_projects.percentage)
concentration_index = top3_percentage / 100

# 集中度解读：
# > 0.8: 高度集中，资源集中在少数项目
# 0.5 ~ 0.8: 中等集中
# < 0.5: 分散，项目较为均衡
```

**可视化输出：**
- 饼图：各项目工时占比
- 项目详细列表：工时、占比、参与人数

---

## 预测算法说明

### 1. 项目工时预测

提供3种预测方法，适用于不同场景：

#### 方法1: 历史平均法 (HISTORICAL_AVERAGE)

**适用场景：**
- 有相似历史项目作为参考
- 项目类型、规模相似
- 快速粗略估算

**算法步骤：**
```python
# 1. 找到相似项目（可手动指定或自动匹配）
similar_projects = find_similar_projects(project_type, complexity)

# 2. 计算相似项目的平均工时
avg_hours = mean([p.total_hours for p in similar_projects])

# 3. 根据团队规模和周期调整
scale_factor = (team_size / avg_team_size) * (duration / avg_duration)
predicted_hours = avg_hours * scale_factor

# 4. 复杂度调整
complexity_factor = {
    'LOW': 0.8,
    'MEDIUM': 1.0,
    'HIGH': 1.2
}
predicted_hours *= complexity_factor[complexity]

# 5. 计算预测范围（±20%）
predicted_min = predicted_hours * 0.8
predicted_max = predicted_hours * 1.2
```

**置信度：**
- 有历史数据：70%
- 无历史数据：50%（使用默认估算）

**优点：**
- 简单直观，易于理解
- 快速获得预测结果

**缺点：**
- 依赖历史数据质量
- 未考虑更多项目特征

---

#### 方法2: 线性回归 (LINEAR_REGRESSION)

**适用场景：**
- 有足够的历史项目数据（≥3个）
- 项目特征可量化（团队规模、周期、复杂度）
- 需要更精确的预测

**算法步骤：**
```python
# 1. 准备训练数据
X = [[team_size, duration, complexity_score], ...]  # 特征
y = [total_hours, ...]  # 目标

# 2. 训练线性回归模型
from sklearn.linear_model import LinearRegression
model = LinearRegression()
model.fit(X, y)

# 3. 预测新项目
X_new = [[new_team_size, new_duration, new_complexity_score]]
predicted_hours = model.predict(X_new)[0]

# 4. 评估模型
r_squared = model.score(X, y)
confidence_level = min(r_squared * 100, 95)
```

**特征编码：**
```python
complexity_encoding = {
    'LOW': 1,
    'MEDIUM': 2,
    'HIGH': 3
}
```

**模型评估：**
- R² (决定系数): 衡量模型拟合度
- R² > 0.7: 良好
- R² < 0.5: 需要更多数据或调整特征

**置信度：**
- 基于R²值：confidence = min(R² × 100, 95)

**优点：**
- 考虑多个项目特征
- 量化特征重要性
- 预测更精确

**缺点：**
- 需要足够的历史数据
- 对数据质量要求高

---

#### 方法3: 趋势预测 (TREND_FORECAST)

**适用场景：**
- 基于当前工时消耗趋势
- 在途项目的工时预测
- 考虑工时变化趋势

**算法步骤：**
```python
# 1. 查询最近90天的工时趋势
trend_data = get_recent_timesheet_trend(days=90)

# 2. 计算日均工时
avg_daily_hours = mean([day.hours for day in trend_data])

# 3. 计算趋势因子（7日移动平均对比）
recent_avg = mean(trend_data[-7:])
earlier_avg = mean(trend_data[:7])
trend_factor = recent_avg / earlier_avg

# 4. 预测项目工时
predicted_hours = (
    avg_daily_hours
    * duration_days
    * (team_size / baseline_team_size)
    * trend_factor
    * complexity_factor
)

# 5. 计算置信度（基于数据稳定性）
std_dev = std(trend_data)
cv = std_dev / avg_daily_hours  # 变异系数
confidence = max(50, min(90, 100 - cv * 50))
```

**趋势因子解读：**
- `> 1.1`: 工时呈上升趋势，效率下降
- `0.9 ~ 1.1`: 稳定
- `< 0.9`: 工时呈下降趋势，效率提升

**置信度：**
- 数据稳定：80-90%
- 数据波动大：50-70%

**优点：**
- 反映最新工时趋势
- 考虑效率变化
- 适合动态调整

**缺点：**
- 依赖近期数据
- 可能受短期波动影响

---

### 2. 完工时间预测

**算法原理：**
```python
# 1. 获取当前进度和已消耗工时
current_progress = get_project_progress()  # 50%
consumed_hours = get_consumed_hours()      # 200小时

# 2. 推算总工时
total_hours = (consumed_hours / current_progress) * 100  # 400小时

# 3. 计算剩余工时
remaining_hours = total_hours - consumed_hours  # 200小时

# 4. 查询最近的消耗速度（最近14天）
recent_hours = get_recent_hours(days=14)
daily_velocity = recent_hours / 14  # 日均消耗速度

# 5. 预测完工时间
predicted_days = remaining_hours / daily_velocity
completion_date = today + timedelta(days=predicted_days)
```

**置信度计算：**
```python
# 基于数据完整性
data_completeness = actual_work_days / 14
confidence = min(85, 50 + data_completeness * 35)
```

**风险因素识别：**
- 完工时间 > 60天 → "存在需求变更风险"
- 置信度 < 60% → "数据不足，预测置信度较低"
- 进度 < 20% → "项目初期，进度波动可能较大"

---

### 3. 负荷预警算法

**饱和度计算：**
```python
# 标准工时
work_days = forecast_days * 5 / 7
standard_hours = work_days * 8

# 历史饱和度
historical_saturation = (historical_hours / standard_hours) * 100

# 预测未来占用（简化：假设保持当前速度）
predicted_occupied = historical_hours * (forecast_days / historical_days)

# 可用工时
available_hours = standard_hours - predicted_occupied
```

**预警级别：**
```python
if saturation >= 120:
    level = 'CRITICAL'  # 严重超负荷
elif saturation >= 100:
    level = 'HIGH'      # 高负荷
elif saturation >= 85:
    level = 'MEDIUM'    # 中等负荷
elif saturation < 60:
    level = 'LOW'       # 低负荷
```

**建议生成：**
- CRITICAL: "减少任务分配或延长交付周期"
- HIGH: "考虑增加协作人员分担工作"
- LOW: "工时利用率较低，可分配更多任务"

---

### 4. 缺口分析算法

**需求工时计算：**
```python
# 方法1: 基于项目计划工时
required_hours = sum([project.planned_hours for project in projects])

# 方法2: 基于历史工时推算（简化）
historical_avg = get_historical_avg_hours(period)
required_hours = historical_avg
```

**可用工时计算：**
```python
# 可用工时 = 人数 × 工作日 × 每日8小时
total_staff = count_staff(department_ids)
work_days = days_count * 5 / 7
available_hours = total_staff * work_days * 8
```

**缺口计算：**
```python
gap_hours = required_hours - available_hours
gap_rate = (gap_hours / required_hours) * 100

# 缺口解读：
# gap_hours > 0: 资源不足
# gap_hours < 0: 资源富余
```

**建议：**
- 缺口 > 0 且缺口率 > 20%: "建议增加人力或延长周期"
- 缺口 < 0: "工时资源充足，可适当增加项目"

---

## API使用文档

### 基础URL
```
/api/v1/timesheet/analytics
```

### 认证
所有API需要权限：`timesheet:read`

### 请求头
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

### 分析API

#### 1. 工时趋势分析
```http
GET /api/v1/timesheet/analytics/trend
```

**Query参数：**
| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| period_type | string | ✅ | 周期类型 | MONTHLY |
| start_date | date | ✅ | 开始日期 | 2024-01-01 |
| end_date | date | ✅ | 结束日期 | 2024-01-31 |
| dimension | string | ❌ | 分析维度 | USER |
| user_ids | string | ❌ | 用户ID列表 | 1,2,3 |
| project_ids | string | ❌ | 项目ID列表 | 10,20 |
| department_ids | string | ❌ | 部门ID列表 | 5,6 |

**period_type枚举：**
- `DAILY` - 日度
- `WEEKLY` - 周度
- `MONTHLY` - 月度
- `QUARTERLY` - 季度
- `YEARLY` - 年度

**响应示例：**
```json
{
  "period_type": "MONTHLY",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "dimension": "USER",
  "total_hours": 1280.5,
  "average_hours": 160.06,
  "max_hours": 180.0,
  "min_hours": 120.0,
  "trend": "INCREASING",
  "change_rate": 8.5,
  "chart_data": {
    "labels": ["2024-01", "2024-02", "2024-03"],
    "datasets": [
      {
        "label": "总工时",
        "data": [1200, 1280, 1350],
        "borderColor": "#3b82f6"
      }
    ]
  }
}
```

---

#### 2. 人员负荷热力图
```http
GET /api/v1/timesheet/analytics/workload
```

**Query参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| period_type | string | ✅ | 周期类型（默认MONTHLY） |
| start_date | date | ✅ | 开始日期 |
| end_date | date | ✅ | 结束日期 |
| user_ids | string | ❌ | 用户ID列表 |
| department_ids | string | ❌ | 部门ID列表 |

**响应示例：**
```json
{
  "period_type": "MONTHLY",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "heatmap_data": {
    "rows": ["张三", "李四", "王五"],
    "columns": ["01-01", "01-02", "01-03"],
    "data": [
      [8.0, 8.5, 9.0],
      [7.5, 8.0, 10.0],
      [8.0, 8.0, 8.0]
    ]
  },
  "statistics": {
    "total_users": 3,
    "average_hours": 162.5,
    "standard_hours": 160.0,
    "overload_count": 1,
    "overload_rate": 33.33
  },
  "overload_users": [
    {
      "user_id": 2,
      "user_name": "李四",
      "department": "研发部",
      "total_hours": 185.5,
      "saturation": 115.94,
      "over_hours": 25.5
    }
  ]
}
```

---

#### 3. 工时效率对比
```http
GET /api/v1/timesheet/analytics/efficiency
```

**响应示例：**
```json
{
  "period_type": "MONTHLY",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31",
  "planned_hours": 800.0,
  "actual_hours": 850.0,
  "variance_hours": 50.0,
  "variance_rate": 6.25,
  "efficiency_rate": 94.12,
  "chart_data": {
    "comparison": {
      "labels": ["计划工时", "实际工时"],
      "values": [800, 850]
    }
  },
  "insights": [
    "工时效率在合理范围内",
    "工时偏差不大，控制良好"
  ]
}
```

---

#### 4. 加班统计
```http
GET /api/v1/timesheet/analytics/overtime
```

**响应示例：**
```json
{
  "total_overtime_hours": 120.5,
  "weekend_hours": 40.0,
  "holiday_hours": 16.0,
  "overtime_rate": 12.5,
  "avg_overtime_per_person": 24.1,
  "top_overtime_users": [
    {
      "user_id": 5,
      "user_name": "张三",
      "department": "研发部",
      "overtime_hours": 45.0
    }
  ],
  "overtime_trend": {
    "labels": ["01-01", "01-02"],
    "datasets": [...]
  }
}
```

---

#### 5. 部门对比
```http
GET /api/v1/timesheet/analytics/department-comparison
```

**响应示例：**
```json
{
  "departments": [
    {
      "department_id": 1,
      "department_name": "研发部",
      "total_hours": 1200.0,
      "normal_hours": 1050.0,
      "overtime_hours": 150.0,
      "user_count": 8,
      "avg_hours_per_person": 150.0,
      "overtime_rate": 12.5,
      "rank": 1
    }
  ],
  "chart_data": {...},
  "rankings": [...]
}
```

---

#### 6. 项目分布
```http
GET /api/v1/timesheet/analytics/project-distribution
```

**响应示例：**
```json
{
  "total_projects": 5,
  "total_hours": 1500.0,
  "pie_chart": {
    "labels": ["项目A", "项目B", "项目C"],
    "values": [600.0, 450.0, 300.0]
  },
  "project_details": [...],
  "concentration_index": 0.72
}
```

---

### 预测API

#### 1. 项目工时预测
```http
POST /api/v1/timesheet/analytics/forecast/project
```

**请求体：**
```json
{
  "project_name": "新项目A",
  "project_type": "WEB_APP",
  "complexity": "MEDIUM",
  "team_size": 5,
  "duration_days": 30,
  "forecast_method": "HISTORICAL_AVERAGE",
  "similar_project_ids": [10, 20, 30]
}
```

**参数说明：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | int | ❌ | 已存在项目ID |
| project_name | string | ✅ | 项目名称 |
| project_type | string | ❌ | 项目类型 |
| complexity | string | ✅ | 复杂度（LOW/MEDIUM/HIGH） |
| team_size | int | ✅ | 团队规模 |
| duration_days | int | ✅ | 计划周期（天） |
| forecast_method | string | ✅ | 预测方法 |
| similar_project_ids | array | ❌ | 相似项目ID列表 |

**forecast_method枚举：**
- `HISTORICAL_AVERAGE` - 历史平均法
- `LINEAR_REGRESSION` - 线性回归
- `TREND_FORECAST` - 趋势预测

**响应示例：**
```json
{
  "forecast_no": "FC-20240115123456",
  "project_name": "新项目A",
  "forecast_method": "HISTORICAL_AVERAGE",
  "predicted_hours": 850.5,
  "predicted_hours_min": 680.4,
  "predicted_hours_max": 1020.6,
  "confidence_level": 75.0,
  "historical_projects_count": 5,
  "similar_projects": [
    {
      "project_id": 10,
      "project_name": "历史项目X",
      "total_hours": 820.0,
      "similarity_score": 0.85
    }
  ],
  "algorithm_params": {
    "method": "HISTORICAL_AVERAGE",
    "complexity_factor": 1.0,
    "scale_factor": 1.05
  },
  "recommendations": [
    "项目工时较大，建议分阶段实施"
  ]
}
```

---

#### 2. 完工时间预测
```http
GET /api/v1/timesheet/analytics/forecast/completion?project_id=1
```

**响应示例：**
```json
{
  "forecast_no": "FC-20240115123457",
  "project_id": 1,
  "project_name": "项目A",
  "current_progress": 50.0,
  "current_consumed_hours": 400.0,
  "predicted_hours": 800.0,
  "remaining_hours": 400.0,
  "predicted_completion_date": "2024-03-15",
  "predicted_days_remaining": 45,
  "confidence_level": 78.5,
  "forecast_curve": {...},
  "risk_factors": [
    "项目初期，进度波动可能较大"
  ]
}
```

---

#### 3. 负荷预警
```http
GET /api/v1/timesheet/analytics/forecast/workload-alert
```

**Query参数：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_ids | string | ❌ | 用户ID列表 |
| department_ids | string | ❌ | 部门ID列表 |
| alert_level | string | ❌ | 预警级别 |
| forecast_days | int | ❌ | 预测天数（默认30） |

**alert_level枚举：**
- `LOW` - 低负荷
- `MEDIUM` - 中等负荷
- `HIGH` - 高负荷
- `CRITICAL` - 严重超负荷

**响应示例：**
```json
[
  {
    "user_id": 5,
    "user_name": "张三",
    "department_name": "研发部",
    "workload_saturation": 125.5,
    "alert_level": "CRITICAL",
    "alert_message": "严重超负荷！饱和度125.5%，建议立即调整任务分配",
    "current_hours": 200.5,
    "available_hours": -40.5,
    "gap_hours": 40.5,
    "recommendations": [
      "减少任务分配或延长交付周期",
      "考虑增加协作人员分担工作"
    ]
  }
]
```

---

#### 4. 缺口分析
```http
GET /api/v1/timesheet/analytics/forecast/gap-analysis
```

**响应示例：**
```json
{
  "period_type": "MONTHLY",
  "start_date": "2024-02-01",
  "end_date": "2024-02-29",
  "required_hours": 1200.0,
  "available_hours": 960.0,
  "gap_hours": 240.0,
  "gap_rate": 20.0,
  "departments": [
    {
      "department_id": 1,
      "department_name": "研发部",
      "required_hours": 720.0,
      "available_hours": 480.0,
      "gap_hours": 240.0
    }
  ],
  "projects": [...],
  "recommendations": [
    "工时缺口240小时，建议增加人力或延长周期",
    "优先级排序，聚焦核心任务"
  ],
  "chart_data": {...}
}
```

---

## 数据模型

### TimesheetAnalytics - 工时分析汇总表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| period_type | string | 周期类型 |
| dimension | string | 分析维度 |
| start_date | date | 开始日期 |
| end_date | date | 结束日期 |
| total_hours | decimal | 总工时 |
| normal_hours | decimal | 正常工时 |
| overtime_hours | decimal | 加班工时 |
| efficiency_rate | decimal | 效率率(%) |
| utilization_rate | decimal | 利用率(%) |
| overtime_rate | decimal | 加班率(%) |
| workload_saturation | decimal | 工时饱和度(%) |
| daily_distribution | json | 每日分布（折线图数据） |
| project_distribution | json | 项目分布（饼图数据） |

### TimesheetTrend - 工时趋势表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| trend_type | string | 趋势类型 |
| period_type | string | 周期类型 |
| trend_date | date | 趋势日期 |
| total_hours | decimal | 总工时 |
| hours_change | decimal | 工时变化量 |
| hours_change_rate | decimal | 工时变化率(%) |
| moving_average_7d | decimal | 7日移动平均 |
| moving_average_30d | decimal | 30日移动平均 |
| workload_trend | string | 负荷趋势 |

### TimesheetForecast - 工时预测表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 主键 |
| forecast_no | string | 预测编号 |
| forecast_type | string | 预测类型 |
| forecast_method | string | 预测方法 |
| project_id | int | 项目ID |
| forecast_date | date | 预测日期 |
| predicted_hours | decimal | 预测工时 |
| predicted_hours_min | decimal | 预测最小值 |
| predicted_hours_max | decimal | 预测最大值 |
| confidence_level | decimal | 置信度(%) |
| predicted_completion_date | date | 预测完工日期 |
| alert_level | string | 预警级别 |
| algorithm_params | json | 算法参数 |
| similar_projects | json | 相似项目列表 |
| is_validated | int | 是否已验证 |
| actual_hours | decimal | 实际工时（验证用） |
| prediction_error | decimal | 预测误差 |

---

## 使用示例

### 场景1: 月度工时趋势分析

```python
# API请求
GET /api/v1/timesheet/analytics/trend?period_type=MONTHLY&start_date=2024-01-01&end_date=2024-12-31

# 用途：
# - 查看全年工时变化趋势
# - 识别工时高峰和低谷
# - 对比不同月份的工时分布

# 决策支持：
# - 趋势上升 → 评估是否需要增加人力
# - 趋势下降 → 分析效率提升原因
# - 异常波动 → 调查具体项目或事件
```

---

### 场景2: 识别超负荷人员

```python
# API请求
GET /api/v1/timesheet/analytics/workload?start_date=2024-01-01&end_date=2024-01-31

# 输出：
# - 热力图：直观看到每个人每天的工时
# - 超负荷人员列表

# 行动：
# 1. 对饱和度>120%的人员：
#    - 立即减少任务分配
#    - 延长交付周期
#    - 增加协作人员
# 2. 对饱和度<60%的人员：
#    - 可分配更多任务
#    - 优化资源利用率
```

---

### 场景3: 新项目工时预测

```python
# API请求
POST /api/v1/timesheet/analytics/forecast/project
{
  "project_name": "移动端APP开发",
  "complexity": "HIGH",
  "team_size": 8,
  "duration_days": 60,
  "forecast_method": "LINEAR_REGRESSION"
}

# 输出：
# - 预测工时：1200小时（范围：1020-1440）
# - 置信度：75%
# - 建议：高复杂度项目，建议预留缓冲时间

# 决策：
# 1. 评估是否有足够人力（8人×60天×8小时=3840可用工时）
# 2. 工时饱和度：1200/3840=31%，资源充足
# 3. 批准项目启动
```

---

### 场景4: 项目完工时间预测

```python
# API请求
GET /api/v1/timesheet/analytics/forecast/completion?project_id=123

# 当前状态：
# - 进度：65%
# - 已消耗：800小时
# - 日均消耗：25小时

# 预测结果：
# - 总工时：1230小时
# - 剩余工时：430小时
# - 预计完工：2024-03-15（17天后）

# 决策：
# - 如果客户要求2024-03-10完工
# - 需要提速：430小时/10天=43小时/天
# - 当前速度：25小时/天
# - 建议：增加人力或协商延期
```

---

### 场景5: 人员负荷预警

```python
# API请求
GET /api/v1/timesheet/analytics/forecast/workload-alert?forecast_days=30&alert_level=HIGH

# 输出：高负荷预警人员
# [
#   {
#     "user_name": "张三",
#     "saturation": 115%,
#     "alert_level": "HIGH",
#     "gap_hours": 24
#   }
# ]

# 行动：
# 1. 立即与张三沟通，了解工作负荷
# 2. 调整任务优先级，延后非紧急任务
# 3. 分配部分任务给其他成员
# 4. 下月排期时减少张三的任务量
```

---

### 场景6: 资源缺口分析

```python
# API请求
GET /api/v1/timesheet/analytics/forecast/gap-analysis?start_date=2024-02-01&end_date=2024-02-29

# 输出：
# - 需求工时：1500小时
# - 可用工时：1200小时
# - 缺口：300小时（20%）
# - 建议：增加人力或延长周期

# 决策方案：
# 方案1：招聘2名新员工（增加320小时）
# 方案2：部分项目延期到3月
# 方案3：外包部分工作
# 方案4：加班填补缺口（不推荐）
```

---

## 最佳实践

### 1. 数据质量保障

**工时记录完整性：**
- ✅ 要求每日填报工时
- ✅ 审批流程规范化
- ✅ 定期检查未填报工时

**数据准确性：**
- 工时记录颗粒度：0.5小时
- 任务关联：明确项目和任务
- 工作内容：简要描述工作内容

### 2. 分析周期建议

| 分析类型 | 建议周期 | 说明 |
|----------|----------|------|
| 工时趋势 | 月度 | 识别长期趋势 |
| 人员负荷 | 周度 | 及时发现问题 |
| 加班统计 | 月度 | 控制加班率 |
| 项目分布 | 季度 | 优化资源配置 |

### 3. 预测精度提升

**提高预测准确性：**
1. 积累历史数据（至少6个月）
2. 标准化项目分类（复杂度、类型）
3. 定期验证预测结果
4. 调整算法参数

**预测误差分析：**
```python
# 预测验证
actual_hours = 850
predicted_hours = 800
error_rate = abs(actual_hours - predicted_hours) / actual_hours * 100

if error_rate < 10:
    # 预测准确
elif error_rate < 20:
    # 可接受范围，需要优化
else:
    # 误差较大，需要调整算法
```

### 4. 预警响应机制

**负荷预警分级响应：**
- 🟢 LOW: 定期监控
- 🟡 MEDIUM: 每周跟进
- 🟠 HIGH: 立即关注，制定调整计划
- 🔴 CRITICAL: 紧急介入，强制调整

**响应SLA：**
- CRITICAL预警：2小时内响应
- HIGH预警：1天内响应
- MEDIUM预警：3天内响应

### 5. 可视化展示

**仪表盘设计：**
```
┌─────────────────────────────────────┐
│  工时分析仪表盘                      │
├─────────────────────────────────────┤
│  本月总工时: 1,280小时 ↑ 8.5%       │
│  平均饱和度: 92% (正常)              │
│  超负荷人数: 2人 (需关注)            │
├─────────────────────────────────────┤
│  [工时趋势图] [部门对比图]           │
│  [项目分布饼图] [负荷热力图]         │
└─────────────────────────────────────┘
```

### 6. 数据隐私

**权限控制：**
- 个人工时：仅本人和直属领导可见
- 部门汇总：部门管理者可见
- 公司汇总：高层管理者可见

### 7. 性能优化

**大数据量处理：**
```python
# 1. 使用聚合查询
SELECT 
  DATE(work_date) as date,
  SUM(hours) as total_hours
FROM timesheet
WHERE work_date BETWEEN '2024-01-01' AND '2024-12-31'
GROUP BY DATE(work_date)

# 2. 建立索引
CREATE INDEX idx_timesheet_date ON timesheet(work_date);
CREATE INDEX idx_timesheet_user_date ON timesheet(user_id, work_date);

# 3. 分页查询
LIMIT 100 OFFSET 0

# 4. 缓存热数据
Redis缓存最近30天的分析结果
```

---

## 附录

### A. 错误码

| 错误码 | 说明 | 解决方法 |
|--------|------|----------|
| 400 | 参数错误 | 检查请求参数 |
| 401 | 未授权 | 检查token |
| 403 | 权限不足 | 申请timesheet:read权限 |
| 404 | 资源不存在 | 检查project_id等 |
| 500 | 服务器错误 | 联系管理员 |

### B. 常见问题

**Q1: 预测结果为什么不准确？**
A: 可能原因：
- 历史数据不足
- 项目特征差异大
- 未考虑外部因素（需求变更、人员变动等）

建议：
- 使用多种方法交叉验证
- 结合专家经验判断
- 定期验证和调整

**Q2: 如何选择预测方法？**
A: 
- 有相似项目 → 历史平均法
- 有充足数据 → 线性回归
- 考虑趋势变化 → 趋势预测

**Q3: 负荷预警阈值可以调整吗？**
A: 可以，在`TimesheetRule`表中配置：
- `standard_daily_hours`: 标准日工时（默认8）
- `max_daily_hours`: 最大日工时（默认12）

### C. 更新日志

**v1.0.0 (2024-01-15)**
- ✨ 初始版本发布
- ✅ 6种分析功能
- ✅ 4种预测功能
- ✅ 3种预测算法
- ✅ 完整API文档

---

**文档维护：**
- 作者：工时分析系统开发团队
- 最后更新：2024-01-15
- 版本：v1.0.0
