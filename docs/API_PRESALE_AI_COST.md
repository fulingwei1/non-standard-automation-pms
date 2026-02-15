# AI智能成本估算 API文档

## 概述

AI智能成本估算模块提供多维度成本预测、优化建议、智能定价等功能,帮助售前团队快速准确地估算项目成本。

**基础路径**: `/api/v1/presale/ai`

**认证方式**: Bearer Token (需要登录)

---

## API端点列表

| 方法 | 端点 | 功能 | 说明 |
|------|------|------|------|
| POST | `/estimate-cost` | 智能成本估算 | 核心功能,提供完整成本分析 |
| GET | `/cost-estimation/{id}` | 获取估算结果 | 查询已有估算记录 |
| POST | `/optimize-cost` | 成本优化建议 | 基于估算结果生成优化方案 |
| POST | `/pricing-recommendation` | 定价推荐 | 智能定价和市场分析 |
| GET | `/cost-breakdown/{ticket_id}` | 成本分解 | 获取工单的最新成本分解 |
| POST | `/cost-comparison` | 成本对比分析 | 对比多个估算方案 |
| GET | `/historical-accuracy` | 历史准确度 | 查看AI模型预测准确度 |
| POST | `/update-actual-cost` | 更新实际成本 | 用于模型学习和改进 |

---

## 详细API说明

### 1. POST /estimate-cost - 智能成本估算

**功能**: 核心估算接口,提供多维度成本预测和分析

**请求体**:
```json
{
  "presale_ticket_id": 1001,
  "solution_id": 2001,
  "project_type": "自动化产线",
  "industry": "制造业",
  "complexity_level": "medium",
  "hardware_items": [
    {
      "name": "PLC控制器",
      "unit_price": 5000,
      "quantity": 2
    },
    {
      "name": "伺服电机",
      "unit_price": 3000,
      "quantity": 4
    }
  ],
  "software_requirements": "需要开发PLC控制程序、MES接口、数据采集模块",
  "estimated_man_days": 20,
  "installation_difficulty": "medium",
  "service_years": 2,
  "target_margin_rate": 0.30
}
```

**参数说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| presale_ticket_id | int | ✅ | 售前工单ID |
| solution_id | int | ❌ | 解决方案ID |
| project_type | string | ✅ | 项目类型(用于历史学习) |
| industry | string | ❌ | 行业 |
| complexity_level | string | ❌ | 复杂度: low/medium/high |
| hardware_items | array | ❌ | 硬件清单 |
| software_requirements | string | ❌ | 软件需求描述 |
| estimated_man_days | int | ❌ | 预估开发人天 |
| installation_difficulty | string | ❌ | 安装难度: low/medium/high |
| service_years | int | ❌ | 售后服务年限(默认1年) |
| target_margin_rate | decimal | ❌ | 目标毛利率(默认0.30) |

**响应示例**:
```json
{
  "id": 1,
  "presale_ticket_id": 1001,
  "solution_id": 2001,
  "cost_breakdown": {
    "hardware_cost": 32200.00,
    "software_cost": 128000.00,
    "installation_cost": 11610.00,
    "service_cost": 32362.00,
    "risk_reserve": 16173.76,
    "total_cost": 220345.76
  },
  "optimization_suggestions": [
    {
      "type": "software",
      "description": "考虑使用现有代码库模块,减少开发工时",
      "original_cost": 128000.00,
      "optimized_cost": 108800.00,
      "saving_amount": 19200.00,
      "saving_rate": 15.0,
      "feasibility_score": 0.75,
      "alternative_solutions": [
        "采用低代码平台",
        "外包部分非核心功能"
      ]
    }
  ],
  "pricing_recommendations": {
    "low": 283314.00,
    "medium": 314794.00,
    "high": 362013.00,
    "suggested_price": 314794.00,
    "target_margin_rate": 30.0,
    "market_analysis": "基于行业标准毛利率和历史成交数据分析"
  },
  "confidence_score": 0.85,
  "model_version": "v1.0.0",
  "created_at": "2026-02-15T10:30:00"
}
```

**错误响应**:
```json
{
  "detail": "估算失败: [错误信息]"
}
```

---

### 2. GET /cost-estimation/{id} - 获取估算结果

**功能**: 查询已有的估算记录详情

**路径参数**:
- `id`: 估算记录ID

**响应**: 同 `/estimate-cost` 的响应格式

**状态码**:
- `200`: 成功
- `404`: 估算记录不存在

---

### 3. POST /optimize-cost - 成本优化建议

**功能**: 基于已有估算生成详细优化方案

**请求体**:
```json
{
  "estimation_id": 1,
  "focus_areas": ["hardware", "software"],
  "max_risk_level": "medium"
}
```

**参数说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| estimation_id | int | ✅ | 估算记录ID |
| focus_areas | array | ❌ | 重点优化领域 |
| max_risk_level | string | ❌ | 最大风险接受度: low/medium/high |

**响应示例**:
```json
{
  "original_total_cost": 220345.76,
  "optimized_total_cost": 201145.76,
  "total_saving": 19200.00,
  "total_saving_rate": 8.71,
  "suggestions": [
    {
      "type": "software",
      "description": "考虑使用现有代码库模块",
      "original_cost": 128000.00,
      "optimized_cost": 108800.00,
      "saving_amount": 19200.00,
      "saving_rate": 15.0,
      "feasibility_score": 0.75
    }
  ],
  "feasibility_summary": "共有1项优化建议,总体可行性评分: 0.75"
}
```

---

### 4. POST /pricing-recommendation - 定价推荐

**功能**: 智能定价和市场竞争分析

**请求体**:
```json
{
  "estimation_id": 1,
  "target_margin_rate": 0.35,
  "market_competition_level": "high",
  "customer_budget": 280000
}
```

**参数说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| estimation_id | int | ✅ | 估算记录ID |
| target_margin_rate | decimal | ❌ | 目标毛利率(默认0.30) |
| market_competition_level | string | ❌ | 市场竞争: low/medium/high |
| customer_budget | decimal | ❌ | 客户预算 |

**响应示例**:
```json
{
  "cost_base": 220345.76,
  "pricing_recommendations": {
    "low": 269049.00,
    "medium": 298943.00,
    "high": 343784.00,
    "suggested_price": 298943.00,
    "target_margin_rate": 35.0,
    "market_analysis": "市场竞争程度: high, 建议价格调整系数: 0.95"
  },
  "sensitivity_analysis": {
    "cost_base": 220345.76,
    "price_range": {
      "min": 269049.00,
      "recommended": 298943.00,
      "max": 343784.00
    },
    "margin_analysis": {
      "low_price_margin": 18.10,
      "recommended_margin": 26.28,
      "high_price_margin": 35.92
    },
    "budget_fit": {
      "customer_budget": 280000.00,
      "fits_low": true,
      "fits_recommended": false,
      "fits_high": false,
      "recommended_strategy": "客户预算偏紧,可考虑低价档,但需简化部分服务"
    }
  },
  "competitiveness_score": 0.75
}
```

---

### 5. GET /cost-breakdown/{ticket_id} - 成本分解

**功能**: 获取售前工单的最新成本分解

**路径参数**:
- `ticket_id`: 售前工单ID

**响应示例**:
```json
{
  "hardware_cost": 32200.00,
  "software_cost": 128000.00,
  "installation_cost": 11610.00,
  "service_cost": 32362.00,
  "risk_reserve": 16173.76,
  "total_cost": 220345.76
}
```

---

### 6. POST /cost-comparison - 成本对比分析

**功能**: 对比2-5个估算方案

**请求体**:
```json
{
  "estimation_ids": [1, 2, 3]
}
```

**响应示例**:
```json
{
  "items": [
    {
      "estimation_id": 1,
      "presale_ticket_id": 1001,
      "total_cost": 220345.76,
      "cost_breakdown": {...},
      "confidence_score": 0.85
    },
    {
      "estimation_id": 2,
      "presale_ticket_id": 1002,
      "total_cost": 185230.50,
      "cost_breakdown": {...},
      "confidence_score": 0.78
    }
  ],
  "comparison_summary": {
    "min_cost": 185230.50,
    "max_cost": 220345.76,
    "avg_cost": 202788.13,
    "cost_range": 35115.26,
    "variance_rate": 17.32
  },
  "recommendations": "推荐方案ID 2: 成本最低(185230.50元), 置信度: 0.78"
}
```

---

### 7. GET /historical-accuracy - 历史准确度

**功能**: 查看AI模型的历史预测准确度

**响应示例**:
```json
{
  "total_predictions": 156,
  "average_variance_rate": 9.85,
  "accuracy_rate": 87.82,
  "best_performing_category": "标准自动化产线",
  "worst_performing_category": "定制化机器人集成",
  "recent_trend": "improving",
  "sample_cases": [
    {
      "project_name": "XX自动化产线",
      "estimated_cost": 200000,
      "actual_cost": 218000,
      "variance_rate": 9.0
    }
  ]
}
```

---

### 8. POST /update-actual-cost - 更新实际成本

**功能**: 记录项目实际成本,用于模型学习

**请求体**:
```json
{
  "estimation_id": 1,
  "project_id": 3001,
  "project_name": "XX自动化产线项目",
  "actual_cost": 235000.00,
  "actual_breakdown": {
    "hardware_cost": 35000.00,
    "software_cost": 135000.00,
    "installation_cost": 12000.00,
    "service_cost": 33000.00,
    "risk_reserve": 20000.00,
    "total_cost": 235000.00
  }
}
```

**响应示例**:
```json
{
  "history_id": 101,
  "variance_rate": 6.65,
  "variance_analysis": {
    "total_variance": 14654.24,
    "variance_rate": 6.65,
    "estimation_id": 1
  },
  "learning_applied": true,
  "message": "实际成本已记录,模型将从此数据学习"
}
```

---

## 错误码说明

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 使用示例 (Python)

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/presale/ai"
TOKEN = "your_auth_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 1. 智能成本估算
estimation_data = {
    "presale_ticket_id": 1001,
    "project_type": "自动化产线",
    "complexity_level": "medium",
    "hardware_items": [
        {"name": "PLC控制器", "unit_price": 5000, "quantity": 2}
    ],
    "software_requirements": "开发控制系统",
    "estimated_man_days": 20,
    "target_margin_rate": 0.30
}

response = requests.post(
    f"{BASE_URL}/estimate-cost",
    json=estimation_data,
    headers=headers
)

estimation = response.json()
print(f"估算ID: {estimation['id']}")
print(f"总成本: {estimation['cost_breakdown']['total_cost']}")

# 2. 成本优化建议
optimization_data = {
    "estimation_id": estimation['id'],
    "max_risk_level": "medium"
}

response = requests.post(
    f"{BASE_URL}/optimize-cost",
    json=optimization_data,
    headers=headers
)

optimization = response.json()
print(f"可节省: {optimization['total_saving']} 元")

# 3. 定价推荐
pricing_data = {
    "estimation_id": estimation['id'],
    "target_margin_rate": 0.35,
    "customer_budget": 280000
}

response = requests.post(
    f"{BASE_URL}/pricing-recommendation",
    json=pricing_data,
    headers=headers
)

pricing = response.json()
print(f"建议报价: {pricing['pricing_recommendations']['suggested_price']}")
```

---

## 最佳实践

### 1. 提高置信度的方法
- 提供完整的硬件清单
- 详细描述软件需求(>100字)
- 准确估算开发人天
- 选择正确的项目类型(用于历史学习)

### 2. 优化建议使用
- 根据`feasibility_score`判断建议可行性
- `max_risk_level`设为`low`可获得最保守的建议
- 结合实际情况评估`alternative_solutions`

### 3. 定价策略
- 根据`budget_fit`调整报价档位
- 参考`margin_analysis`确保利润空间
- 使用`competitiveness_score`评估成交可能性

### 4. 持续改进
- 项目完成后务必调用`update-actual-cost`
- 定期查看`historical-accuracy`评估模型准确度
- 偏差率>15%的项目需要分析原因

---

## 更新日志

### v1.0.0 (2026-02-15)
- ✅ 初始版本发布
- ✅ 8个核心API端点
- ✅ 多维度成本估算
- ✅ 智能优化建议
- ✅ 定价推荐引擎
- ✅ 历史学习功能

---

## 技术支持

如有问题,请联系:
- **技术支持**: tech-support@example.com
- **API反馈**: api-feedback@example.com
