# 移动端AI销售助手 API文档

## 概述

移动端AI销售助手提供一整套RESTful API，支持销售人员在现场拜访时获得AI辅助决策支持。

**Base URL**: `/api/v1/presale/mobile`

**认证方式**: Bearer Token（JWT）

## API端点列表

| 序号 | 端点 | 方法 | 功能 | 响应时间要求 |
|------|------|------|------|--------------|
| 1 | `/chat` | POST | 实时AI问答 | <2秒 |
| 2 | `/voice-question` | POST | 语音提问（STT+AI+TTS） | <3秒 |
| 3 | `/visit-preparation/{ticket_id}` | GET | 拜访准备清单 | <1秒 |
| 4 | `/quick-estimate` | POST | 现场快速估价 | <2秒 |
| 5 | `/equipment-recognition` | POST | 设备图像识别（未实现） | <2秒 |
| 6 | `/create-visit-record` | POST | 创建拜访记录 | <1秒 |
| 7 | `/voice-to-visit-record` | POST | 语音转拜访记录 | <5秒 |
| 8 | `/visit-history/{customer_id}` | GET | 拜访历史 | <1秒 |
| 9 | `/sync-offline-data` | POST | 离线数据同步 | <1秒 |
| 10 | `/customer-snapshot/{id}` | GET | 客户快照 | <1秒 |

---

## 1. 实时AI问答

### 请求

```http
POST /api/v1/presale/mobile/chat
Content-Type: application/json
Authorization: Bearer {token}

{
  "question": "这款机器人的最大负载是多少？",
  "presale_ticket_id": 123,
  "context": {
    "customer_id": 456,
    "previous_question": "什么是六轴机器人？"
  }
}
```

### 响应

```json
{
  "id": 789,
  "answer": "这款六轴工业机器人的最大负载为10kg，工作半径1400mm...",
  "question_type": "technical",
  "response_time": 1250,
  "context": {
    "customer_id": 456,
    "previous_question": "什么是六轴机器人？"
  },
  "created_at": "2024-02-15T10:30:00"
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| question | string | 用户提问（必填） |
| presale_ticket_id | integer | 售前工单ID（可选） |
| context | object | 对话上下文（可选） |
| question_type | enum | 问题类型：technical/competitor/case/pricing/other |
| response_time | integer | 响应时间（毫秒） |

---

## 2. 语音提问

### 请求

```http
POST /api/v1/presale/mobile/voice-question
Content-Type: application/json
Authorization: Bearer {token}

{
  "audio_base64": "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA//tQAAAAAAAAAAAA...",
  "presale_ticket_id": 123,
  "format": "mp3"
}
```

### 响应

```json
{
  "transcription": "这款机器人的价格是多少？",
  "answer": "根据配置不同，价格范围在8万到12万之间...",
  "audio_url": "https://cdn.example.com/tts/audio_12345.mp3",
  "response_time": 2850,
  "question_type": "pricing"
}
```

### 支持的音频格式

- MP3
- WAV
- M4A

---

## 3. 拜访准备清单

### 请求

```http
GET /api/v1/presale/mobile/visit-preparation/123
Authorization: Bearer {token}
```

### 响应

```json
{
  "ticket_id": 123,
  "customer_name": "某某科技有限公司",
  "customer_background": "该公司是一家专注于智能制造的高新技术企业...",
  "previous_interactions": [
    {
      "date": "2024-01-15",
      "type": "电话沟通",
      "summary": "讨论了初步需求，客户关注自动化改造成本"
    }
  ],
  "recommended_scripts": [
    "开场：感谢贵公司对我们的信任...",
    "需求挖掘：请问贵公司目前在生产线上遇到的主要痛点是什么？"
  ],
  "attention_points": [
    "客户非常关注成本，需要重点说明ROI",
    "决策人是技术总监和采购经理"
  ],
  "technical_materials": [
    {
      "name": "产品技术手册",
      "url": "/materials/tech_manual.pdf"
    }
  ],
  "competitor_comparison": {
    "main_competitors": ["竞品A", "竞品B"],
    "our_advantages": ["技术成熟度更高", "性价比更优"]
  }
}
```

---

## 4. 现场快速估价

### 请求

```http
POST /api/v1/presale/mobile/quick-estimate
Content-Type: application/json
Authorization: Bearer {token}

{
  "equipment_description": "六轴工业机器人，负载10kg",
  "equipment_photo_base64": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
  "presale_ticket_id": 123,
  "customer_id": 456
}
```

### 响应

```json
{
  "id": 789,
  "recognized_equipment": "六轴工业机器人",
  "estimated_cost": 100000,
  "price_range_min": 130000,
  "price_range_max": 150000,
  "bom_items": [
    {
      "name": "伺服电机",
      "quantity": 6,
      "unit_price": 3000,
      "amount": 18000
    },
    {
      "name": "减速机",
      "quantity": 6,
      "unit_price": 2000,
      "amount": 12000
    }
  ],
  "confidence_score": 85,
  "recommendation": "建议报价范围：130,000 - 150,000 元"
}
```

---

## 5. 创建拜访记录

### 请求

```http
POST /api/v1/presale/mobile/create-visit-record
Content-Type: application/json
Authorization: Bearer {token}

{
  "presale_ticket_id": 123,
  "customer_id": 456,
  "visit_date": "2024-02-15",
  "visit_type": "first_contact",
  "attendees": [
    {
      "name": "张三",
      "title": "技术总监",
      "company": "客户公司"
    }
  ],
  "discussion_points": "1. 讨论了自动化改造需求\n2. 客户关注成本和实施周期",
  "customer_feedback": "客户对方案整体满意，希望优化成本",
  "next_steps": "1周内提供优化方案和详细报价"
}
```

### 响应

```json
{
  "id": 789,
  "presale_ticket_id": 123,
  "customer_id": 456,
  "visit_date": "2024-02-15",
  "visit_type": "first_contact",
  "attendees": [...],
  "discussion_points": "1. 讨论了自动化改造需求...",
  "customer_feedback": "客户对方案整体满意...",
  "next_steps": "1周内提供优化方案...",
  "ai_generated_summary": null,
  "created_at": "2024-02-15T14:30:00"
}
```

### 拜访类型

| 类型 | 说明 |
|------|------|
| first_contact | 初次接触 |
| follow_up | 跟进 |
| demo | 演示 |
| negotiation | 谈判 |
| closing | 签约 |

---

## 6. 语音转拜访记录

### 请求

```http
POST /api/v1/presale/mobile/voice-to-visit-record
Content-Type: application/json
Authorization: Bearer {token}

{
  "audio_base64": "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGF2ZjU4Ljc2LjEwMAAAAAAAAAAAAAAA...",
  "presale_ticket_id": 123,
  "customer_id": 456,
  "visit_date": "2024-02-15",
  "visit_type": "follow_up"
}
```

### 响应

```json
{
  "id": 790,
  "presale_ticket_id": 123,
  "customer_id": 456,
  "visit_date": "2024-02-15",
  "visit_type": "follow_up",
  "attendees": [
    {
      "name": "张三",
      "title": "技术总监",
      "company": "客户公司"
    }
  ],
  "discussion_points": "讨论了自动化改造方案的技术细节和实施计划",
  "customer_feedback": "客户对方案整体满意，但希望进一步优化成本",
  "next_steps": "1周内提供优化方案和详细报价",
  "ai_generated_summary": "本次拜访主要讨论了技术方案，客户反馈积极，下一步需要优化成本方案。",
  "created_at": "2024-02-15T15:00:00"
}
```

---

## 7. 拜访历史

### 请求

```http
GET /api/v1/presale/mobile/visit-history/456
Authorization: Bearer {token}
```

### 响应

```json
{
  "visits": [
    {
      "id": 790,
      "visit_date": "2024-02-15",
      "visit_type": "follow_up",
      "discussion_points": "讨论了技术方案...",
      "created_at": "2024-02-15T15:00:00"
    },
    {
      "id": 789,
      "visit_date": "2024-02-10",
      "visit_type": "first_contact",
      "discussion_points": "初次接触，了解需求...",
      "created_at": "2024-02-10T10:00:00"
    }
  ],
  "total_visits": 2,
  "latest_visit": {
    "id": 790,
    "visit_date": "2024-02-15",
    ...
  }
}
```

---

## 8. 客户快照

### 请求

```http
GET /api/v1/presale/mobile/customer-snapshot/456
Authorization: Bearer {token}
```

### 响应

```json
{
  "customer_id": 456,
  "customer_name": "某某科技有限公司",
  "industry": "智能制造",
  "company_size": "500-1000人",
  "contact_person": "张经理",
  "contact_phone": "138****8888",
  "recent_tickets": [
    {
      "id": 123,
      "title": "生产线自动化改造",
      "status": "进行中",
      "created_at": "2024-01-10"
    }
  ],
  "total_orders": 5,
  "total_revenue": 2500000.0,
  "last_interaction": "2024-01-20T10:30:00",
  "key_concerns": ["成本控制", "实施周期", "售后服务"],
  "decision_makers": [
    {
      "name": "李总",
      "title": "总经理",
      "decision_power": "最终决策"
    }
  ]
}
```

---

## 9. 离线数据同步

### 请求

```http
POST /api/v1/presale/mobile/sync-offline-data
Content-Type: application/json
Authorization: Bearer {token}

{
  "data_type": "chat",
  "local_id": "offline_12345",
  "data_payload": {
    "question": "这是离线时提的问题",
    "answer": "这是离线时AI的回答",
    "question_type": "technical",
    "presale_ticket_id": 123
  }
}
```

### 响应

```json
{
  "success": true,
  "synced_id": 791,
  "message": "同步成功"
}
```

### 支持的数据类型

| 类型 | 说明 |
|------|------|
| chat | 对话记录 |
| visit | 拜访记录 |
| estimate | 估价记录 |

---

## 错误响应

### 格式

```json
{
  "detail": "错误描述信息"
}
```

### 常见错误码

| 状态码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权（Token无效或过期） |
| 403 | 禁止访问（权限不足） |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 性能指标

| 指标 | 目标值 |
|------|--------|
| API响应时间 | <2秒 |
| AI问答准确率 | >85% |
| 语音识别准确率 | >90% |
| 快速估价偏差 | <20% |
| 系统可用性 | >99.5% |

---

## 使用限制

- 单个请求最大大小：10MB
- 音频文件最大大小：5MB
- 图片文件最大大小：5MB
- 请求频率限制：100次/分钟/用户

---

## 版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0 | 2024-02-15 | 初始版本发布 |

---

## 联系支持

- 技术支持邮箱: tech-support@example.com
- 文档更新日期: 2024-02-15
