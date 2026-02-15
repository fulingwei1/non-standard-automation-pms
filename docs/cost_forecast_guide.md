# 项目成本预测和趋势分析文档

## 📋 目录

1. [功能概述](#功能概述)
2. [预测原理](#预测原理)
3. [使用指南](#使用指南)
4. [API文档](#api文档)
5. [数据模型](#数据模型)
6. [最佳实践](#最佳实践)

---

## 功能概述

项目成本预测和趋势分析模块为项目管理者提供科学的成本预测和预警能力，帮助提前识别成本风险，优化预算管理。

### 核心功能

#### 1. 成本预测
- **3种预测方法**：线性回归、指数预测、历史平均
- **完工成本预测**：基于当前趋势预测最终完工成本
- **月度预测**：提供未来每月的成本预测数据

#### 2. 成本趋势分析
- **月度成本趋势**：分析每月成本变化
- **累计成本趋势**：展示成本累计曲线
- **成本统计汇总**：总成本、月均成本、最大/最小月成本

#### 3. 成本燃尽图
- **理想燃尽线**：基于预算和计划时间的均匀消耗
- **实际燃尽线**：实际成本消耗情况
- **进度对比**：判断项目是否按计划进行

#### 4. 成本预警
- **超支预警**：实际成本超过预算阈值时触发
- **进度预警**：成本消耗与完成度不匹配时触发
- **趋势预警**：成本增长率异常时触发

---

## 预测原理

### 1. 线性回归预测（LINEAR）

#### 原理
使用最小二乘法对历史成本数据进行线性拟合，得到成本增长趋势线。

**数学模型**：
```
y = mx + b
```
其中：
- `y` = 累计成本
- `x` = 时间（月数）
- `m` = 斜率（月度成本增长率）
- `b` = 截距

#### 预测公式
```
预测完工成本 = 斜率 × 预计总月数 + 截距
```

#### 适用场景
- 成本呈稳定线性增长的项目
- 历史数据较为规律
- 短期预测（3-6个月）

#### 示例
```python
# 历史数据：
# 第1月：80,000元（累计）
# 第2月：160,000元（累计）
# 第3月：240,000元（累计）

# 线性拟合结果：
# 斜率 m = 80,000（每月增长）
# 截距 b = 0

# 预测：
# 假设项目计划12个月
# 预测完工成本 = 80,000 × 12 + 0 = 960,000元
```

#### 评估指标
- **R²（决定系数）**：衡量拟合优度，范围 [0, 1]，越接近1表示拟合越好
- **月度燃烧率**：斜率值，表示每月平均成本

---

### 2. 指数预测（EXPONENTIAL）

#### 原理
适用于成本呈指数增长的项目，基于历史增长率预测未来成本。

**数学模型**：
```
Future_Cost = Current_Cost × (1 + growth_rate)^periods
```

其中：
- `growth_rate` = 平均月度增长率
- `periods` = 剩余预测期数

#### 计算步骤
1. 计算每月增长率：`(本月成本 - 上月成本) / 上月成本`
2. 计算平均增长率
3. 根据剩余进度估算剩余期数
4. 使用指数公式预测完工成本

#### 适用场景
- 项目初期成本增长缓慢，后期加速
- 研发项目、创新项目
- 成本呈加速增长趋势

#### 示例
```python
# 历史数据：
# 第1月：50,000元（累计）
# 第2月：110,000元（累计，增长率 120%）
# 第3月：200,000元（累计，增长率 82%）

# 平均增长率 = (1.2 + 0.82) / 2 = 1.01 (101%)

# 预测：
# 当前进度50%，剩余期数 = 3期
# 预测完工成本 = 200,000 × (1 + 1.01)^3 ≈ 1,624,080元
```

---

### 3. 历史平均法（HISTORICAL_AVERAGE）

#### 原理
基于历史月均成本，假设未来成本保持相同速率。

**数学模型**：
```
预测完工成本 = 月均成本 × 预计总月数
```

#### 计算步骤
1. 计算历史月均成本：`总成本 / 已过月数`
2. 估算项目总月数（基于当前进度）
3. 预测完工成本

#### 适用场景
- 成本波动较小的项目
- 稳定的生产型项目
- 数据不足时的快速估算

#### 示例
```python
# 历史数据（6个月）：
# 总成本：480,000元
# 月均成本 = 480,000 / 6 = 80,000元/月

# 预测：
# 当前进度50%，预计总月数 = 6 / 0.5 = 12月
# 预测完工成本 = 80,000 × 12 = 960,000元
```

---

### 4. 预警检测算法

#### 超支预警（OVERSPEND）

**检测逻辑**：
```python
成本消耗率 = (实际成本 / 预算) × 100%

if 成本消耗率 >= 100%:
    预警级别 = "CRITICAL"  # 严重
elif 成本消耗率 >= 80%:
    预警级别 = "WARNING"   # 警告
else:
    无预警
```

**默认阈值**：
- 警告阈值：80%
- 严重阈值：100%

#### 进度不匹配预警（PROGRESS_MISMATCH）

**检测逻辑**：
```python
成本消耗率 = (实际成本 / 预算) × 100%
完成进度 = 项目进度百分比
偏差 = 成本消耗率 - 完成进度

if abs(偏差) >= 15%:
    预警
```

**解释**：
- 偏差为正：成本消耗超前（花钱多，进度慢）
- 偏差为负：进度超前成本（进度快，花钱少）

**默认阈值**：15%

#### 趋势异常预警（TREND_ANOMALY）

**检测逻辑**：
```python
# 计算最近3个月的月度增长率
growth_rates = []
for i in range(1, 4):
    rate = (本月成本 - 上月成本) / 上月成本
    growth_rates.append(rate)

avg_growth_rate = sum(growth_rates) / len(growth_rates)

if avg_growth_rate >= 30%:
    预警
```

**默认阈值**：30%

---

## 使用指南

### 快速开始

#### 1. 执行成本预测

**方法A：通过API**
```bash
# 线性预测
curl -X GET "http://localhost:8000/api/v1/projects/1/costs/forecast?method=LINEAR" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 指数预测
curl -X GET "http://localhost:8000/api/v1/projects/1/costs/forecast?method=EXPONENTIAL" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 历史平均预测
curl -X GET "http://localhost:8000/api/v1/projects/1/costs/forecast?method=HISTORICAL_AVERAGE" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**方法B：通过Python SDK**
```python
from app.services.cost_forecast_service import CostForecastService

service = CostForecastService(db)
result = service.linear_forecast(project_id=1)

print(f"预测完工成本: {result['forecasted_completion_cost']}元")
print(f"是否超预算: {result['is_over_budget']}")
```

#### 2. 查看成本趋势

```bash
curl -X GET "http://localhost:8000/api/v1/projects/1/costs/trend" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**：
```json
{
  "monthly_trend": [
    {"month": "2025-01", "cost": 80000},
    {"month": "2025-02", "cost": 90000}
  ],
  "cumulative_trend": [
    {"month": "2025-01", "cumulative_cost": 80000},
    {"month": "2025-02", "cumulative_cost": 170000}
  ]
}
```

#### 3. 查看燃尽图

```bash
curl -X GET "http://localhost:8000/api/v1/projects/1/costs/burn-down" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 4. 检查预警

```bash
curl -X GET "http://localhost:8000/api/v1/projects/1/costs/alerts" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 5. 对比多种预测方法

```bash
curl -X GET "http://localhost:8000/api/v1/projects/1/costs/compare-methods" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 选择合适的预测方法

| 场景 | 推荐方法 | 理由 |
|------|---------|------|
| 成本稳定增长 | 线性回归 | 简单可靠，适合大多数项目 |
| 项目初期 | 历史平均 | 数据不足时的快速估算 |
| 研发项目 | 指数预测 | 适应后期成本加速增长 |
| 生产项目 | 历史平均 | 成本波动小，月度稳定 |
| 不确定 | 对比方法 | 同时使用3种方法对比 |

---

### 配置预警规则

#### 全局规则（适用所有项目）

```python
from app.models.project import CostAlertRule

# 创建全局超支预警规则
rule = CostAlertRule(
    rule_code="GLOBAL_OVERSPEND_STRICT",
    rule_name="严格超支预警",
    alert_type="OVERSPEND",
    rule_config={
        "warning_threshold": 70,    # 70%预警
        "critical_threshold": 90    # 90%严重
    },
    is_enabled=True,
    priority=10
)
db.add(rule)
db.commit()
```

#### 项目特定规则（覆盖全局规则）

```python
# 为重要项目设置更严格的规则
rule = CostAlertRule(
    rule_code="PROJECT_001_OVERSPEND",
    rule_name="001项目超支预警",
    project_id=1,  # 项目ID
    alert_type="OVERSPEND",
    rule_config={
        "warning_threshold": 60,
        "critical_threshold": 80
    },
    is_enabled=True,
    priority=1  # 高优先级
)
db.add(rule)
db.commit()
```

---

## API文档

### 1. 获取成本预测

**端点**：`GET /api/v1/projects/{project_id}/costs/forecast`

**参数**：
- `method` (string, required): 预测方法
  - `LINEAR`: 线性回归
  - `EXPONENTIAL`: 指数预测
  - `HISTORICAL_AVERAGE`: 历史平均
- `save_result` (boolean, optional): 是否保存预测结果，默认 `false`

**响应**：
```json
{
  "code": 200,
  "message": "预测成功",
  "data": {
    "method": "LINEAR",
    "forecast_date": "2025-02-14",
    "forecasted_completion_cost": 950000.00,
    "current_actual_cost": 480000.00,
    "current_budget": 1000000.00,
    "current_progress_pct": 50.00,
    "data_points": 6,
    "trend_data": {
      "slope": 80000.00,
      "intercept": 0.00,
      "r_squared": 0.95,
      "monthly_burn_rate": 80000.00
    },
    "monthly_forecast_data": [
      {
        "month": "2025-01",
        "type": "actual",
        "monthly_cost": 80000.00,
        "cumulative_cost": 80000.00
      },
      {
        "month": "2025-07",
        "type": "forecast",
        "monthly_cost": 80000.00,
        "cumulative_cost": 560000.00
      }
    ],
    "is_over_budget": false,
    "budget_variance": -50000.00
  }
}
```

---

### 2. 获取成本趋势

**端点**：`GET /api/v1/projects/{project_id}/costs/trend`

**参数**：
- `start_month` (string, optional): 开始月份，格式 `YYYY-MM`
- `end_month` (string, optional): 结束月份，格式 `YYYY-MM`

**响应**：
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "project_id": 1,
    "project_name": "测试项目",
    "monthly_trend": [
      {"month": "2025-01", "cost": 80000.00},
      {"month": "2025-02", "cost": 90000.00}
    ],
    "cumulative_trend": [
      {"month": "2025-01", "cumulative_cost": 80000.00},
      {"month": "2025-02", "cumulative_cost": 170000.00}
    ],
    "summary": {
      "total_months": 6,
      "total_cost": 480000.00,
      "avg_monthly_cost": 80000.00,
      "min_monthly_cost": 70000.00,
      "max_monthly_cost": 95000.00
    }
  }
}
```

---

### 3. 获取成本燃尽图

**端点**：`GET /api/v1/projects/{project_id}/costs/burn-down`

**响应**：
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "project_id": 1,
    "project_name": "测试项目",
    "budget": 1000000.00,
    "current_spent": 480000.00,
    "remaining_budget": 520000.00,
    "burn_rate": 80000.00,
    "burn_down_data": [
      {
        "month": "2025-01",
        "ideal_remaining": 920000.00,
        "actual_spent": 80000.00,
        "actual_remaining": 920000.00
      }
    ],
    "is_on_track": true
  }
}
```

---

### 4. 获取成本预警

**端点**：`GET /api/v1/projects/{project_id}/costs/alerts`

**参数**：
- `auto_create` (boolean, optional): 是否自动创建预警记录，默认 `true`

**响应**：
```json
{
  "code": 200,
  "message": "检测到 2 个预警",
  "data": {
    "alerts": [
      {
        "alert_type": "OVERSPEND",
        "alert_level": "WARNING",
        "alert_title": "成本超支预警",
        "alert_message": "项目成本接近预算！当前成本850000元，已使用85.0%预算",
        "alert_data": {
          "budget": 1000000.00,
          "actual_cost": 850000.00,
          "consumption_rate": 85.00,
          "threshold": 80
        }
      }
    ],
    "total_count": 2
  }
}
```

---

### 5. 对比预测方法

**端点**：`GET /api/v1/projects/{project_id}/costs/compare-methods`

**响应**：
```json
{
  "code": 200,
  "message": "对比成功",
  "data": {
    "methods": {
      "LINEAR": {...},
      "EXPONENTIAL": {...},
      "HISTORICAL_AVERAGE": {...}
    },
    "comparison": {
      "forecasted_costs": {
        "LINEAR": 950000.00,
        "EXPONENTIAL": 1020000.00,
        "HISTORICAL_AVERAGE": 960000.00
      },
      "average_forecast": 976666.67,
      "min_forecast": 950000.00,
      "max_forecast": 1020000.00,
      "forecast_range": 70000.00
    }
  }
}
```

---

### 6. 获取预测历史

**端点**：`GET /api/v1/projects/{project_id}/costs/forecast-history`

**参数**：
- `limit` (integer, optional): 返回记录数，默认 `10`

**响应**：
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "forecasts": [
      {
        "id": 1,
        "forecast_date": "2025-02-14",
        "forecast_method": "LINEAR",
        "forecasted_completion_cost": 950000.00,
        "current_progress_pct": 50.00,
        "forecast_accuracy": null
      }
    ],
    "total_count": 5
  }
}
```

---

## 数据模型

### CostForecast（成本预测表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| project_id | Integer | 项目ID |
| forecast_method | String | 预测方法 |
| forecast_date | Date | 预测日期 |
| forecasted_completion_cost | Decimal | 预测完工成本 |
| current_progress_pct | Decimal | 当前进度 |
| current_actual_cost | Decimal | 当前实际成本 |
| monthly_forecast_data | JSON | 月度预测数据 |
| trend_data | JSON | 趋势数据 |
| forecast_accuracy | Decimal | 预测准确率（事后计算） |

### CostAlert（成本预警表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| project_id | Integer | 项目ID |
| alert_type | String | 预警类型 |
| alert_level | String | 预警级别 |
| alert_date | Date | 预警日期 |
| alert_message | Text | 预警消息 |
| status | String | 状态 |

### CostAlertRule（成本预警规则表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| rule_code | String | 规则编码 |
| rule_name | String | 规则名称 |
| project_id | Integer | 项目ID（NULL=全局） |
| alert_type | String | 预警类型 |
| rule_config | JSON | 规则配置 |
| is_enabled | Boolean | 是否启用 |

---

## 最佳实践

### 1. 数据准备

#### 确保数据完整性
```python
# 成本数据需包含 cost_date 或 cost_month
# 至少需要2个月的数据才能进行预测

# ✅ 正确
cost = ProjectCost(
    project_id=1,
    cost_type="MATERIAL",
    amount=50000,
    cost_date=date(2025, 1, 15)  # 明确日期
)

# ❌ 错误
cost = ProjectCost(
    project_id=1,
    amount=50000
    # 缺少 cost_date
)
```

### 2. 选择预测方法

#### 数据驱动决策
```python
# 1. 对比多种方法
result = service.compare_forecast_methods(project_id)

# 2. 查看R²值（线性回归）
if result['LINEAR']['trend_data']['r_squared'] > 0.8:
    # R²>0.8，线性拟合良好
    use_method = 'LINEAR'

# 3. 查看预测范围
forecast_range = result['comparison']['forecast_range']
if forecast_range / result['comparison']['average_forecast'] < 0.1:
    # 预测差异<10%，三种方法结果接近
    print("预测结果较为一致")
```

### 3. 定期更新预测

```python
# 建议每月更新一次预测
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

def monthly_forecast():
    projects = db.query(Project).filter(Project.is_active == True).all()
    for project in projects:
        result = service.linear_forecast(project.id)
        if 'error' not in result:
            service.save_forecast(project.id, result, admin_user_id)

# 每月1号执行
scheduler.add_job(monthly_forecast, 'cron', day=1, hour=0)
scheduler.start()
```

### 4. 预警响应流程

```python
# 1. 自动检测预警
alerts = service.check_cost_alerts(project_id, auto_create=True)

# 2. 通知相关人员
for alert in alerts:
    if alert['alert_level'] == 'CRITICAL':
        send_email(project_manager, alert['alert_message'])
        send_sms(project_manager, alert['alert_title'])
    elif alert['alert_level'] == 'WARNING':
        send_email(project_manager, alert['alert_message'])

# 3. 记录处理措施
db_alert = db.query(CostAlert).filter(...).first()
db_alert.acknowledged_by = current_user.id
db_alert.acknowledged_at = datetime.now()
db_alert.resolution_note = "已采取成本控制措施..."
db.commit()
```

### 5. 预测准确率评估

```python
# 项目完成后，回填实际完工成本，评估预测准确率
def update_forecast_accuracy(project_id):
    project = db.query(Project).filter(Project.id == project_id).first()
    actual_cost = float(project.actual_cost)
    
    forecasts = db.query(CostForecast).filter(
        CostForecast.project_id == project_id
    ).all()
    
    for forecast in forecasts:
        predicted = float(forecast.forecasted_completion_cost)
        error = actual_cost - predicted
        error_pct = abs(error / actual_cost * 100)
        accuracy = 100 - error_pct
        
        forecast.actual_completion_cost = actual_cost
        forecast.forecast_error = error
        forecast.forecast_error_pct = error_pct
        forecast.forecast_accuracy = accuracy
    
    db.commit()
```

---

## 常见问题

### Q1: 为什么显示"历史数据不足"？

**A**: 预测算法至少需要2个月的成本数据。请确保：
1. 项目成本记录包含 `cost_date` 或 `cost_month`
2. 至少有2个不同月份的数据

### Q2: 哪种预测方法最准确？

**A**: 没有绝对最准确的方法，建议：
1. 使用 `/compare-methods` 对比3种方法
2. 查看线性回归的 R² 值（>0.8 表示拟合良好）
3. 根据项目特点选择方法

### Q3: 如何关闭预警通知？

**A**: 修改预警规则配置：
```python
rule = db.query(CostAlertRule).filter(...).first()
rule.notification_enabled = False
db.commit()
```

### Q4: 预测结果可以修改吗？

**A**: 预测结果是只读的。如需调整，应：
1. 修正历史成本数据
2. 重新执行预测

---

## 技术支持

如有问题，请联系：
- 📧 Email: support@example.com
- 📱 电话: 400-xxx-xxxx
- 💬 在线客服: https://support.example.com
