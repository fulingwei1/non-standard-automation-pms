# AI客户情绪分析模块 - API文档

## 概述

AI客户情绪分析模块提供基于OpenAI GPT-4的智能客户情绪分析、购买意向识别、流失预警和跟进时机推荐功能。

## 基础信息

- **Base URL**: `/api/v1/presale/ai`
- **认证方式**: Bearer Token (继承系统认证)
- **响应格式**: JSON
- **字符编码**: UTF-8

## API端点列表

### 1. 分析客户情绪

**端点**: `POST /analyze-emotion`

**描述**: 分析客户沟通内容的情绪、购买意向和流失风险

**请求体**:
```json
{
  "presale_ticket_id": 1,
  "customer_id": 100,
  "communication_content": "我对你们的产品很感兴趣，想了解一下价格和功能"
}
```

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| presale_ticket_id | integer | 是 | 售前工单ID |
| customer_id | integer | 是 | 客户ID |
| communication_content | string | 是 | 沟通内容，至少1个字符 |

**响应示例**:
```json
{
  "id": 1,
  "presale_ticket_id": 1,
  "customer_id": 100,
  "sentiment": "positive",
  "purchase_intent_score": 85.5,
  "churn_risk": "low",
  "emotion_factors": {
    "positive_keywords": ["感兴趣", "想了解"],
    "concerns": [],
    "urgency_level": "medium"
  },
  "analysis_result": "客户表现出较高的购买意向...",
  "created_at": "2026-02-15T10:30:00"
}
```

**响应字段说明**:
- `sentiment`: 情绪类型，可选值: `positive`(积极), `neutral`(中性), `negative`(消极)
- `purchase_intent_score`: 购买意向评分，范围 0-100
- `churn_risk`: 流失风险等级，可选值: `high`(高), `medium`(中), `low`(低)

**状态码**:
- `200`: 成功
- `422`: 请求参数验证失败
- `500`: 服务器内部错误

---

### 2. 获取情绪分析

**端点**: `GET /emotion-analysis/{ticket_id}`

**描述**: 获取指定工单的最新情绪分析结果

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| ticket_id | integer | 售前工单ID |

**响应示例**: 同"分析客户情绪"接口

**状态码**:
- `200`: 成功
- `404`: 未找到情绪分析记录
- `500`: 服务器内部错误

---

### 3. 预测流失风险

**端点**: `POST /predict-churn-risk`

**描述**: 基于客户沟通历史预测流失风险

**请求体**:
```json
{
  "presale_ticket_id": 1,
  "customer_id": 100,
  "recent_communications": [
    "第一次沟通内容",
    "第二次沟通内容",
    "最近的沟通内容"
  ],
  "days_since_last_contact": 15,
  "response_time_trend": [2.0, 4.5, 8.0, 12.0]
}
```

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| presale_ticket_id | integer | 是 | 售前工单ID |
| customer_id | integer | 是 | 客户ID |
| recent_communications | array[string] | 是 | 最近的沟通记录列表，至少1条 |
| days_since_last_contact | integer | 否 | 距离上次联系的天数 |
| response_time_trend | array[float] | 否 | 回复时间趋势(小时) |

**响应示例**:
```json
{
  "presale_ticket_id": 1,
  "customer_id": 100,
  "churn_risk": "medium",
  "risk_score": 65.5,
  "risk_factors": [
    {
      "factor": "回复时间逐渐变长",
      "weight": "high",
      "description": "客户回复时间从2小时增加到12小时"
    },
    {
      "factor": "沟通频率降低",
      "weight": "medium",
      "description": "距离上次联系已15天"
    }
  ],
  "retention_strategies": [
    "主动联系客户，了解是否有新的疑虑",
    "提供限时优惠促进决策",
    "分享成功案例增强信心"
  ],
  "analysis_summary": "客户流失风险中等，建议及时跟进..."
}
```

**状态码**:
- `200`: 成功
- `422`: 请求参数验证失败
- `500`: 服务器内部错误

---

### 4. 推荐跟进时机

**端点**: `POST /recommend-follow-up`

**描述**: 基于客户情绪分析推荐最佳跟进时机和内容

**请求体**:
```json
{
  "presale_ticket_id": 1,
  "customer_id": 100,
  "latest_emotion_analysis_id": 5
}
```

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| presale_ticket_id | integer | 是 | 售前工单ID |
| customer_id | integer | 是 | 客户ID |
| latest_emotion_analysis_id | integer | 否 | 最新情绪分析ID，不填则自动获取 |

**响应示例**:
```json
{
  "id": 1,
  "presale_ticket_id": 1,
  "recommended_time": "2026-02-15T14:30:00",
  "priority": "high",
  "follow_up_content": "您好，关于您之前咨询的产品功能，我们可以为您安排一次详细的演示...",
  "reason": "客户购买意向评分达到85分，表现出较高兴趣，建议在2小时内跟进以促成交易",
  "status": "pending",
  "created_at": "2026-02-15T12:00:00"
}
```

**响应字段说明**:
- `priority`: 优先级，可选值: `high`(高), `medium`(中), `low`(低)
- `status`: 状态，可选值: `pending`(待处理), `completed`(已完成), `dismissed`(已忽略)

**状态码**:
- `200`: 成功
- `422`: 请求参数验证失败
- `500`: 服务器内部错误

---

### 5. 获取跟进提醒列表

**端点**: `GET /follow-up-reminders`

**描述**: 获取跟进提醒列表，支持筛选

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态筛选: pending/completed/dismissed |
| priority | string | 否 | 优先级筛选: high/medium/low |
| limit | integer | 否 | 返回数量限制，默认50，最大100 |

**请求示例**:
```
GET /api/v1/presale/ai/follow-up-reminders?status=pending&priority=high&limit=20
```

**响应示例**:
```json
{
  "total": 15,
  "reminders": [
    {
      "id": 1,
      "presale_ticket_id": 1,
      "recommended_time": "2026-02-15T14:30:00",
      "priority": "high",
      "follow_up_content": "...",
      "reason": "...",
      "status": "pending",
      "created_at": "2026-02-15T12:00:00"
    }
  ]
}
```

**状态码**:
- `200`: 成功
- `422`: 查询参数验证失败
- `500`: 服务器内部错误

---

### 6. 获取情绪趋势

**端点**: `GET /emotion-trend/{ticket_id}`

**描述**: 获取指定工单的客户情绪趋势

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| ticket_id | integer | 售前工单ID |

**响应示例**:
```json
{
  "id": 1,
  "presale_ticket_id": 1,
  "customer_id": 100,
  "trend_data": [
    {
      "date": "2026-02-01T10:00:00",
      "sentiment": "neutral",
      "intent_score": 50.0
    },
    {
      "date": "2026-02-05T14:30:00",
      "sentiment": "positive",
      "intent_score": 75.0
    },
    {
      "date": "2026-02-10T16:00:00",
      "sentiment": "positive",
      "intent_score": 85.0
    }
  ],
  "key_turning_points": [
    {
      "date": "2026-02-05T14:30:00",
      "type": "peak",
      "sentiment": "positive",
      "intent_score": 75.0
    }
  ],
  "created_at": "2026-02-01T10:00:00",
  "updated_at": "2026-02-10T16:00:00"
}
```

**响应字段说明**:
- `trend_data`: 趋势数据点列表，按时间排序
- `key_turning_points`: 关键转折点，包括峰值(peak)和谷值(valley)

**状态码**:
- `200`: 成功
- `404`: 未找到情绪趋势数据
- `500`: 服务器内部错误

---

### 7. 忽略提醒

**端点**: `POST /dismiss-reminder/{reminder_id}`

**描述**: 忽略指定的跟进提醒

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| reminder_id | integer | 提醒ID |

**响应示例**:
```json
{
  "message": "提醒已忽略",
  "success": true
}
```

**状态码**:
- `200`: 成功
- `404`: 未找到指定提醒
- `500`: 服务器内部错误

---

### 8. 批量分析客户

**端点**: `POST /batch-analyze-customers`

**描述**: 批量分析多个客户的情绪和流失风险

**请求体**:
```json
{
  "customer_ids": [100, 101, 102, 103, 104],
  "analysis_type": "full"
}
```

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| customer_ids | array[integer] | 是 | 客户ID列表，1-100个 |
| analysis_type | string | 否 | 分析类型: full(完整)/emotion(仅情绪)/churn(仅流失)，默认full |

**响应示例**:
```json
{
  "total_analyzed": 5,
  "success_count": 5,
  "failed_count": 0,
  "summaries": [
    {
      "customer_id": 100,
      "latest_sentiment": "positive",
      "purchase_intent_score": 85.0,
      "churn_risk": "low",
      "needs_attention": true,
      "recommended_action": "高意向客户，建议立即联系促成交易"
    },
    {
      "customer_id": 101,
      "latest_sentiment": "negative",
      "purchase_intent_score": 30.0,
      "churn_risk": "high",
      "needs_attention": true,
      "recommended_action": "紧急跟进，制定挽回策略"
    }
  ],
  "analysis_timestamp": "2026-02-15T15:00:00"
}
```

**响应字段说明**:
- `needs_attention`: 是否需要关注（高流失风险、消极情绪或高购买意向时为true）
- `recommended_action`: 推荐的行动建议

**状态码**:
- `200`: 成功
- `422`: 请求参数验证失败
- `500`: 服务器内部错误

---

## 错误响应格式

所有API在发生错误时返回统一格式：

```json
{
  "detail": "错误详细信息"
}
```

## 使用示例

### Python示例

```python
import requests

# 1. 分析客户情绪
response = requests.post(
    "http://api.example.com/api/v1/presale/ai/analyze-emotion",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={
        "presale_ticket_id": 1,
        "customer_id": 100,
        "communication_content": "我对你们的产品很感兴趣"
    }
)
result = response.json()
print(f"情绪: {result['sentiment']}, 意向评分: {result['purchase_intent_score']}")

# 2. 批量分析客户
response = requests.post(
    "http://api.example.com/api/v1/presale/ai/batch-analyze-customers",
    headers={"Authorization": "Bearer YOUR_TOKEN"},
    json={
        "customer_ids": [100, 101, 102],
        "analysis_type": "full"
    }
)
batch_result = response.json()
for summary in batch_result['summaries']:
    if summary['needs_attention']:
        print(f"客户 {summary['customer_id']} 需要关注: {summary['recommended_action']}")
```

### cURL示例

```bash
# 分析客户情绪
curl -X POST "http://api.example.com/api/v1/presale/ai/analyze-emotion" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "presale_ticket_id": 1,
    "customer_id": 100,
    "communication_content": "我对你们的产品很感兴趣"
  }'

# 获取跟进提醒列表
curl -X GET "http://api.example.com/api/v1/presale/ai/follow-up-reminders?status=pending&priority=high" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 性能指标

- **响应时间**: < 3秒 (95th percentile)
- **准确率**:
  - 情绪识别: > 80%
  - 意向评分偏差: < 15%
  - 流失预警: > 75%
  - 跟进时机合理性: > 85%

## 注意事项

1. **频率限制**: 建议批量分析时每批不超过100个客户
2. **内容长度**: 沟通内容建议控制在5000字符以内，过长可能影响分析准确性
3. **AI响应时间**: OpenAI API调用可能需要2-5秒，请设置合理的超时时间
4. **异步处理**: 对于大批量分析，建议使用批量分析接口
5. **数据隐私**: 所有沟通内容会发送到OpenAI API，请确保符合隐私政策

## 更新日志

### v1.0.0 (2026-02-15)
- 初始版本发布
- 8个核心API端点
- 支持情绪分析、流失预警、跟进推荐
- 批量分析功能
