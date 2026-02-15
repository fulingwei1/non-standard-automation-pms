# 成本预测API快速参考

## 🚀 基础URL
```
http://localhost:8000/api/v1/projects/{project_id}/costs
```

## 📌 认证
所有端点需要 `cost:read` 权限
```bash
-H "Authorization: Bearer YOUR_TOKEN"
```

---

## 1️⃣ 成本预测
```bash
GET /forecast?method={LINEAR|EXPONENTIAL|HISTORICAL_AVERAGE}
```

**参数**:
- `method`: 预测方法（必填）
- `save_result`: 是否保存（可选，默认false）

**示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/projects/1/costs/forecast?method=LINEAR"
```

**响应**:
```json
{
  "forecasted_completion_cost": 950000.00,
  "is_over_budget": false,
  "trend_data": {"slope": 80000, "r_squared": 0.95}
}
```

---

## 2️⃣ 成本趋势
```bash
GET /trend?start_month={YYYY-MM}&end_month={YYYY-MM}
```

**示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/projects/1/costs/trend"
```

**响应**:
```json
{
  "monthly_trend": [{"month": "2025-01", "cost": 80000}],
  "cumulative_trend": [{"month": "2025-01", "cumulative_cost": 80000}]
}
```

---

## 3️⃣ 燃尽图
```bash
GET /burn-down
```

**示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/projects/1/costs/burn-down"
```

**响应**:
```json
{
  "budget": 1000000,
  "current_spent": 480000,
  "remaining_budget": 520000,
  "is_on_track": true
}
```

---

## 4️⃣ 成本预警
```bash
GET /alerts?auto_create={true|false}
```

**示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/projects/1/costs/alerts"
```

**响应**:
```json
{
  "alerts": [
    {
      "alert_type": "OVERSPEND",
      "alert_level": "WARNING",
      "alert_message": "成本接近预算！"
    }
  ]
}
```

---

## 5️⃣ 预测历史
```bash
GET /forecast-history?limit={10}
```

**示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/projects/1/costs/forecast-history"
```

---

## 6️⃣ 对比预测方法
```bash
GET /compare-methods
```

**示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/projects/1/costs/compare-methods"
```

**响应**:
```json
{
  "comparison": {
    "forecasted_costs": {
      "LINEAR": 950000,
      "EXPONENTIAL": 1020000,
      "HISTORICAL_AVERAGE": 960000
    },
    "average_forecast": 976666.67
  }
}
```

---

## 📊 预警类型

| 类型 | 代码 | 说明 |
|------|------|------|
| 超支预警 | `OVERSPEND` | 成本超过预算阈值 |
| 进度预警 | `PROGRESS_MISMATCH` | 进度与成本不匹配 |
| 趋势预警 | `TREND_ANOMALY` | 成本增长率异常 |

## 🎯 预测方法选择

| 方法 | 适用场景 | R²要求 |
|------|---------|--------|
| `LINEAR` | 成本稳定增长 | >0.8 |
| `EXPONENTIAL` | 研发项目、后期加速 | - |
| `HISTORICAL_AVERAGE` | 快速估算、数据不足 | - |

## ⚡ 快速测试

```bash
# 1. 线性预测
curl -X GET "http://localhost:8000/api/v1/projects/1/costs/forecast?method=LINEAR"

# 2. 查看趋势
curl -X GET "http://localhost:8000/api/v1/projects/1/costs/trend"

# 3. 检查预警
curl -X GET "http://localhost:8000/api/v1/projects/1/costs/alerts"

# 4. 对比方法
curl -X GET "http://localhost:8000/api/v1/projects/1/costs/compare-methods"
```

---

**完整文档**: `docs/cost_forecast_guide.md`
