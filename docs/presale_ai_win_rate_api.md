# 售前AI赢率预测模块 - API文档

**版本**: v1.0.0  
**创建日期**: 2026-02-15  
**团队**: Team 4 - AI智能赢率预测模型

---

## 📖 概述

售前AI赢率预测模块使用AI技术（GPT-4/Kimi API）分析售前项目的多维度特征，预测成交概率，提供影响因素分析、竞品分析和改进建议。

### 核心功能

1. **成交概率预测**: 基于客户画像、项目金额、技术评估等特征，预测赢单概率（0-100%）
2. **影响因素分析**: 识别TOP 5影响赢率的关键因素
3. **竞品分析**: 分析竞争对手，提供差异化策略建议
4. **改进建议**: 提供短期、中期行动计划和里程碑监控
5. **模型学习**: 记录实际结果，持续优化模型准确度

---

## 🔑 API端点

### 基础URL

```
/api/v1/presale/ai
```

### 认证

所有API需要在请求头中携带JWT Token：

```http
Authorization: Bearer <your_token>
```

---

## 1. 预测赢率

### POST `/predict-win-rate`

基于多维度特征预测售前项目的成交概率。

#### 请求参数

```json
{
  "presale_ticket_id": 1,
  "ticket_no": "PS-2026-001",
  "title": "某汽车零部件测试系统项目",
  "customer_name": "某汽车公司",
  "estimated_amount": 1500000,
  "ticket_type": "SOLUTION",
  "urgency": "URGENT",
  "is_repeat_customer": true,
  "cooperation_count": 3,
  "success_count": 2,
  "competitor_count": 2,
  "main_competitors": "竞争对手A, 竞争对手B",
  "requirement_maturity": 75,
  "technical_feasibility": 80,
  "business_feasibility": 70,
  "delivery_risk": 30,
  "customer_relationship": 85,
  "salesperson_id": 10,
  "salesperson_win_rate": 0.65
}
```

#### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| presale_ticket_id | int | 是 | 售前工单ID |
| ticket_no | string | 否 | 工单编号 |
| title | string | 否 | 工单标题 |
| customer_name | string | 否 | 客户名称 |
| estimated_amount | decimal | 否 | 预估金额 |
| is_repeat_customer | bool | 否 | 是否老客户（默认false） |
| cooperation_count | int | 否 | 历史合作次数（默认0） |
| success_count | int | 否 | 历史成功次数（默认0） |
| competitor_count | int | 否 | 竞争对手数量（默认3） |
| requirement_maturity | int | 否 | 需求成熟度（0-100） |
| technical_feasibility | int | 否 | 技术可行性（0-100） |
| business_feasibility | int | 否 | 商务可行性（0-100） |
| delivery_risk | int | 否 | 交付风险（0-100） |
| customer_relationship | int | 否 | 客户关系（0-100） |
| salesperson_id | int | 否 | 销售人员ID |
| salesperson_win_rate | float | 否 | 销售人员历史赢率（0-1） |

#### 响应示例

```json
{
  "id": 123,
  "presale_ticket_id": 1,
  "win_rate_score": 72.5,
  "confidence_interval": "68-77%",
  "influencing_factors": [
    {
      "factor": "客户关系",
      "impact": "positive",
      "score": 9,
      "description": "客户关系良好，历史合作成功率高"
    },
    {
      "factor": "技术可行性",
      "impact": "positive",
      "score": 8,
      "description": "技术方案成熟，实现难度适中"
    },
    {
      "factor": "竞争态势",
      "impact": "neutral",
      "score": 6,
      "description": "竞争对手数量适中，需重点关注"
    }
  ],
  "competitor_analysis": {
    "competitors": ["竞争对手A", "竞争对手B"],
    "our_advantages": ["技术领先", "服务响应快", "行业经验丰富"],
    "competitor_advantages": ["价格可能更低", "本地化服务"],
    "differentiation_strategy": [
      "突出技术优势和成功案例",
      "强调长期服务价值",
      "提供定制化解决方案"
    ]
  },
  "improvement_suggestions": {
    "short_term": [
      "安排技术专家与客户深入沟通",
      "准备详细的技术方案和演示",
      "收集竞争对手报价信息"
    ],
    "mid_term": [
      "建立客户高层关系",
      "提供试用或POC方案",
      "准备差异化价值主张"
    ],
    "milestones": [
      "技术方案评审通过",
      "商务报价提交",
      "客户决策会议",
      "合同谈判"
    ]
  },
  "ai_analysis_report": "综合分析：该项目赢率较高（72.5%），主要得益于良好的客户关系和技术优势。建议重点关注竞争对手动态，强化技术方案的差异化价值...",
  "model_version": "gpt-4",
  "predicted_at": "2026-02-15T10:30:00",
  "created_by": 5
}
```

#### 错误响应

```json
{
  "detail": "预测赢率失败: AI服务暂时不可用"
}
```

---

## 2. 获取预测结果

### GET `/win-rate/{prediction_id}`

根据预测ID获取完整的预测结果。

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| prediction_id | int | 预测记录ID |

#### 响应示例

同"预测赢率"的响应格式。

---

## 3. 获取影响因素

### GET `/influencing-factors/{ticket_id}`

获取TOP 5影响赢率的关键因素。

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| ticket_id | int | 售前工单ID |

#### 响应示例

```json
[
  {
    "factor": "客户关系",
    "impact": "positive",
    "score": 9,
    "description": "客户关系良好，历史合作成功率高"
  },
  {
    "factor": "技术可行性",
    "impact": "positive",
    "score": 8,
    "description": "技术方案成熟，实现难度适中"
  },
  {
    "factor": "项目金额",
    "impact": "negative",
    "score": 7,
    "description": "金额较大，决策周期可能较长"
  }
]
```

---

## 4. 竞品分析

### POST `/competitor-analysis?ticket_id={ticket_id}`

获取竞品分析，包括竞争对手、优劣势、差异化策略。

#### 查询参数

| 参数 | 类型 | 说明 |
|------|------|------|
| ticket_id | int | 售前工单ID |

#### 响应示例

```json
{
  "competitors": ["竞争对手A", "竞争对手B", "竞争对手C"],
  "our_advantages": [
    "技术领先，拥有核心专利",
    "行业经验丰富，成功案例多",
    "服务响应快，售后支持完善"
  ],
  "competitor_advantages": [
    "价格可能更低",
    "本地化服务网络广",
    "品牌知名度高"
  ],
  "differentiation_strategy": [
    "突出技术创新和独特价值",
    "展示成功案例和ROI分析",
    "提供定制化解决方案",
    "强调长期合作价值"
  ]
}
```

---

## 5. 改进建议

### GET `/improvement-suggestions/{ticket_id}`

获取赢率提升建议。

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| ticket_id | int | 售前工单ID |

#### 响应示例

```json
{
  "short_term": [
    "1周内安排技术专家深度交流",
    "准备详细技术方案和演示",
    "收集竞争对手信息",
    "制定差异化价值主张"
  ],
  "mid_term": [
    "1个月内建立客户高层关系",
    "提供POC或试用方案",
    "准备商务报价和合同模板",
    "制定风险应对预案"
  ],
  "milestones": [
    "需求澄清会议",
    "技术方案评审",
    "商务报价提交",
    "客户决策会议",
    "合同谈判",
    "合同签订"
  ]
}
```

---

## 6. 更新实际结果

### POST `/update-actual-result`

更新项目的实际成交结果，用于模型学习和准确度评估。

#### 请求参数

```json
{
  "presale_ticket_id": 1,
  "actual_result": "won",
  "win_date": "2026-03-01T10:00:00"
}
```

#### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| presale_ticket_id | int | 是 | 售前工单ID |
| actual_result | string | 是 | 实际结果：won（赢单）/ lost（失单）/ pending（待定） |
| win_date | datetime | 否 | 赢单日期（actual_result=won时） |
| lost_date | datetime | 否 | 失单日期（actual_result=lost时） |

#### 响应示例

```json
{
  "success": true,
  "message": "实际结果已更新: won",
  "history_id": 45,
  "prediction_error": 5.3,
  "is_correct": 1
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| success | bool | 操作是否成功 |
| message | string | 提示信息 |
| history_id | int | 历史记录ID |
| prediction_error | float | 预测误差（仅当结果确定时） |
| is_correct | int | 预测是否正确（1=正确, 0=错误, null=待定） |

---

## 7. 模型准确度

### GET `/model-accuracy`

获取AI预测模型的准确度统计。

#### 响应示例

```json
{
  "overall_accuracy": 78.5,
  "total_predictions": 200,
  "correct_predictions": 157,
  "average_error": 12.3,
  "by_result": {
    "won": {
      "count": 120,
      "avg_predicted_score": 72.5,
      "avg_error": 10.2
    },
    "lost": {
      "count": 80,
      "avg_predicted_score": 35.8,
      "avg_error": 14.5
    }
  },
  "last_updated": "2026-02-15T11:00:00"
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| overall_accuracy | float | 总体准确率（%） |
| total_predictions | int | 总预测数 |
| correct_predictions | int | 正确预测数 |
| average_error | float | 平均预测误差 |
| by_result | object | 按结果分组的详细统计 |
| last_updated | string | 最后更新时间 |

---

## 📊 使用场景

### 场景1: 新项目评估

```python
# 1. 创建售前工单后，立即预测赢率
response = requests.post(
    "/api/v1/presale/ai/predict-win-rate",
    json={
        "presale_ticket_id": 1,
        "customer_name": "某汽车公司",
        "estimated_amount": 1500000,
        "is_repeat_customer": True,
        "competitor_count": 2,
        ...
    },
    headers={"Authorization": f"Bearer {token}"}
)

prediction = response.json()
print(f"赢率: {prediction['win_rate_score']}%")
print(f"置信区间: {prediction['confidence_interval']}")
```

### 场景2: 查看影响因素

```python
# 2. 查看TOP 5影响因素
response = requests.get(
    f"/api/v1/presale/ai/influencing-factors/{ticket_id}",
    headers={"Authorization": f"Bearer {token}"}
)

factors = response.json()
for factor in factors:
    print(f"{factor['factor']}: {factor['impact']} (分数: {factor['score']})")
```

### 场景3: 获取竞品分析

```python
# 3. 获取竞品分析和策略建议
response = requests.post(
    f"/api/v1/presale/ai/competitor-analysis?ticket_id={ticket_id}",
    headers={"Authorization": f"Bearer {token}"}
)

analysis = response.json()
print("我方优势:", analysis['our_advantages'])
print("差异化策略:", analysis['differentiation_strategy'])
```

### 场景4: 项目结束后更新结果

```python
# 4. 项目结束后，更新实际结果（用于模型学习）
response = requests.post(
    "/api/v1/presale/ai/update-actual-result",
    json={
        "presale_ticket_id": 1,
        "actual_result": "won",
        "win_date": "2026-03-01T10:00:00"
    },
    headers={"Authorization": f"Bearer {token}"}
)

result = response.json()
print(f"预测误差: {result['prediction_error']}%")
print(f"预测是否正确: {'是' if result['is_correct'] else '否'}")
```

---

## ⚠️ 注意事项

1. **AI服务配置**: 需要配置 `OPENAI_API_KEY` 或 `KIMI_API_KEY` 环境变量
2. **响应时间**: AI预测可能需要3-5秒，建议异步处理
3. **数据质量**: 输入数据越完整，预测越准确
4. **模型学习**: 定期更新实际结果，帮助模型持续优化
5. **准确率**: 模型准确率目标 >75%，需要持续监控和调优

---

## 🔧 错误码

| HTTP状态码 | 说明 |
|-----------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未授权（Token无效或过期） |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 📞 技术支持

如有问题，请联系开发团队：Team 4 - AI智能赢率预测模型
