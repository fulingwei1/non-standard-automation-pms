# AI智能话术推荐引擎 - API文档

## 目录
- [概述](#概述)
- [认证](#认证)
- [客户画像API](#客户画像api)
- [话术推荐API](#话术推荐api)
- [异议处理API](#异议处理api)
- [销售进程API](#销售进程api)
- [话术库API](#话术库api)
- [错误码](#错误码)

---

## 概述

**基础URL**: `http://localhost:8000/api/v1`

**版本**: v1.0.0

**数据格式**: JSON

**响应时间**: < 3秒

---

## 认证

当前版本暂不需要认证。生产环境建议添加API Key或JWT认证。

---

## 客户画像API

### 1. 分析客户画像

**端点**: `POST /presale/ai/analyze-customer-profile`

**描述**: 基于沟通记录自动分析客户画像，识别客户类型、关注点、决策风格

**请求体**:
```json
{
  "customer_id": 12345,
  "presale_ticket_id": 101,
  "communication_notes": "客户表示对我们的技术架构很感兴趣，特别关注系统的高可用性和扩展能力。他们团队主要是技术背景，希望能详细了解API对接方式..."
}
```

**响应**:
```json
{
  "id": 1,
  "customer_id": 12345,
  "presale_ticket_id": 101,
  "customer_type": "technical",
  "focus_points": ["quality", "delivery"],
  "decision_style": "rational",
  "communication_notes": "客户表示对我们的技术架构很感兴趣...",
  "ai_analysis": "这是一位典型的技术型客户，决策理性，关注产品质量和交付速度。建议从技术架构、API文档、案例经验等角度切入。",
  "created_at": "2026-02-15T10:30:00",
  "updated_at": "2026-02-15T10:30:00"
}
```

**状态码**:
- `201`: 创建成功
- `400`: 请求参数错误
- `500`: 服务器内部错误

---

### 2. 获取客户画像

**端点**: `GET /presale/ai/customer-profile/{customer_id}`

**描述**: 获取指定客户的画像信息

**路径参数**:
- `customer_id` (int): 客户ID

**响应**:
```json
{
  "id": 1,
  "customer_id": 12345,
  "customer_type": "technical",
  "focus_points": ["quality", "delivery"],
  "decision_style": "rational",
  "ai_analysis": "技术型客户，注重产品质量...",
  "created_at": "2026-02-15T10:30:00",
  "updated_at": "2026-02-15T10:30:00"
}
```

**状态码**:
- `200`: 成功
- `404`: 客户画像不存在

---

## 话术推荐API

### 3. 推荐销售话术

**端点**: `POST /presale/ai/recommend-sales-script`

**描述**: 根据场景和客户画像智能推荐话术

**请求体**:
```json
{
  "presale_ticket_id": 101,
  "scenario": "first_contact",
  "customer_profile_id": 1,
  "context": "初次联系，通过展会认识"
}
```

**场景类型** (`scenario`):
- `first_contact`: 首次接触
- `needs_discovery`: 需求挖掘
- `solution_presentation`: 方案讲解
- `price_negotiation`: 价格谈判
- `objection_handling`: 异议处理
- `closing`: 成交

**响应**:
```json
{
  "id": 101,
  "presale_ticket_id": 101,
  "scenario": "first_contact",
  "customer_profile_id": 1,
  "recommended_scripts": [
    "您好，我是XX公司的技术顾问。了解到贵司在寻找XXX解决方案，我们在该领域有成熟的技术架构和实施经验，方便和您深入探讨技术细节吗？",
    "注意到贵司技术栈使用XXX，我们的产品在该架构下有深度优化，API对接简单，部署周期短，可以先安排技术交流吗？"
  ],
  "response_strategy": "针对技术型客户，从技术架构和实施经验切入，强调API易用性和快速部署能力，邀请技术交流。",
  "success_case_references": [
    {
      "case_title": "XX科技公司案例",
      "description": "类似技术栈，2周完成对接",
      "result": "成功签约，客户满意度90%"
    }
  ],
  "created_at": "2026-02-15T11:00:00"
}
```

**状态码**:
- `201`: 创建成功
- `400`: 请求参数错误（场景类型无效等）
- `500`: AI服务调用失败

---

## 异议处理API

### 4. 异议处理建议

**端点**: `POST /presale/ai/handle-objection`

**描述**: 针对客户异议提供应对策略和话术

**请求体**:
```json
{
  "presale_ticket_id": 102,
  "objection_type": "价格太高",
  "customer_profile_id": 1,
  "context": "客户反馈我们的报价比竞品A高20%"
}
```

**常见异议类型**:
- 价格太高
- 技术不成熟
- 竞品更好
- 暂时不需要
- 预算不足
- 决策周期长
- 兼容性问题
- 数据安全担忧

**响应**:
```json
{
  "id": 201,
  "objection_type": "价格太高",
  "response_strategy": "强调价值和ROI，提供TCO对比，突出服务和质量优势。避免直接降价，可提供分期或效果付费方案。",
  "recommended_scripts": [
    "价格确实是考量因素，但更重要的是投入产出比。我们的方案能带来XX%的效率提升，6个月即可回本。",
    "如果只看单价，我们确实不是最便宜的。但算上实施成本、维护成本、机会成本，我们的总拥有成本最低。",
    "我们可以提供分期付款方案，首付只需XX%，减轻现金流压力。"
  ],
  "success_case_references": [
    {
      "case_title": "XX企业价格谈判案例",
      "objection": "报价比预算高30%",
      "resolution": "提供详细ROI分析+分期方案",
      "result": "客户接受报价，签约3年"
    }
  ],
  "created_at": "2026-02-15T11:30:00"
}
```

**状态码**:
- `201`: 创建成功
- `500`: 服务器错误

---

## 销售进程API

### 5. 销售进程指导

**端点**: `POST /presale/ai/sales-progress-guidance`

**描述**: 分析当前销售进度，提供下一步行动建议

**请求体**:
```json
{
  "presale_ticket_id": 103,
  "customer_profile_id": 1,
  "current_situation": "已完成3次技术交流，客户技术团队认可方案，但商务负责人对价格有疑虑，决策层尚未介入。下周将进行正式报价。"
}
```

**响应**:
```json
{
  "current_stage": "方案设计/报价",
  "next_actions": [
    "准备详细的ROI分析报告，应对价格疑虑",
    "联系决策层，安排高层会议",
    "准备竞品对比分析，突出差异化优势",
    "制定灵活的付款方案（分期、效果付费等）",
    "锁定技术团队支持，内部推动"
  ],
  "key_milestones": [
    "下周报价提交",
    "2周内决策层会议",
    "1个月内完成商务谈判"
  ],
  "recommendations": "当前处于关键阶段，技术认可但商务有疑虑，建议双线推进：1）强化价值传递，准备ROI和对比分析；2）升级接触层级，触达决策层。时间窗口约2-3周，需快速推进。",
  "risks": [
    "价格谈判陷入僵局",
    "竞品突然降价",
    "决策层对项目优先级下调"
  ],
  "timeline": "预计4-6周完成签约"
}
```

**状态码**:
- `200`: 成功
- `500`: 服务器错误

---

## 话术库API

### 6. 获取场景话术

**端点**: `GET /presale/ai/sales-scripts/{scenario}`

**描述**: 获取指定场景的话术模板

**路径参数**:
- `scenario` (string): 场景类型

**查询参数**:
- `customer_type` (string, 可选): 客户类型筛选
- `limit` (int, 可选): 返回数量限制，默认10

**示例**: `GET /presale/ai/sales-scripts/first_contact?customer_type=technical&limit=5`

**响应**:
```json
[
  {
    "id": 1,
    "scenario": "first_contact",
    "customer_type": "technical",
    "script_content": "您好，我是XX公司的技术顾问...",
    "tags": ["技术导向", "专业"],
    "success_rate": 78.5,
    "created_at": "2026-02-15T09:00:00"
  },
  {
    "id": 2,
    "scenario": "first_contact",
    "customer_type": "technical",
    "script_content": "注意到贵司技术栈使用XXX...",
    "tags": ["技术兼容", "快速集成"],
    "success_rate": 76.8,
    "created_at": "2026-02-15T09:05:00"
  }
]
```

**状态码**:
- `200`: 成功
- `400`: 场景类型无效

---

### 7. 获取话术库

**端点**: `GET /presale/ai/script-library`

**描述**: 获取完整话术库，支持多维度筛选

**查询参数**:
- `scenario` (string, 可选): 场景类型
- `customer_type` (string, 可选): 客户类型
- `limit` (int, 可选): 返回数量限制，默认50

**示例**: `GET /presale/ai/script-library?scenario=objection_handling&limit=20`

**响应**:
```json
{
  "total": 15,
  "scripts": [
    {
      "id": 50,
      "scenario": "objection_handling",
      "customer_type": "commercial",
      "script_content": "您说价格高，我理解。但如果算上实施效率...",
      "tags": ["价格异议", "TCO"],
      "success_rate": 79.5,
      "created_at": "2026-02-15T09:00:00"
    }
  ]
}
```

**状态码**:
- `200`: 成功

---

### 8. 添加话术模板

**端点**: `POST /presale/ai/add-script-template`

**描述**: 添加新的话术模板到库中

**请求体**:
```json
{
  "scenario": "needs_discovery",
  "customer_type": "technical",
  "script_content": "请问贵司目前在XXX方面遇到的最大技术挑战是什么？",
  "tags": ["痛点挖掘", "技术"],
  "success_rate": 81.2
}
```

**响应**:
```json
{
  "id": 101,
  "scenario": "needs_discovery",
  "customer_type": "technical",
  "script_content": "请问贵司目前在XXX方面遇到的最大技术挑战是什么？",
  "tags": ["痛点挖掘", "技术"],
  "success_rate": 81.2,
  "created_at": "2026-02-15T14:00:00"
}
```

**状态码**:
- `201`: 创建成功
- `400`: 参数错误

---

### 9. 话术反馈

**端点**: `POST /presale/ai/script-feedback`

**描述**: 记录话术使用效果反馈，用于优化推荐算法

**请求体**:
```json
{
  "script_id": 101,
  "is_effective": true,
  "feedback_notes": "客户对这个话术反应很好，成功推进到下一阶段"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Feedback recorded successfully"
}
```

**状态码**:
- `200`: 成功
- `500`: 服务器错误

---

## 错误码

| 状态码 | 说明 |
|-------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

**错误响应格式**:
```json
{
  "detail": "错误详细信息"
}
```

---

## 使用建议

### 1. 典型工作流

```
1. 客户首次接触
   ↓
2. POST /analyze-customer-profile  # 分析客户画像
   ↓
3. POST /recommend-sales-script (scenario=first_contact)  # 获取首次接触话术
   ↓
4. POST /recommend-sales-script (scenario=needs_discovery)  # 需求挖掘
   ↓
5. POST /handle-objection  # 处理异议（如有）
   ↓
6. POST /sales-progress-guidance  # 获取进程指导
   ↓
7. POST /recommend-sales-script (scenario=closing)  # 成交话术
   ↓
8. POST /script-feedback  # 反馈效果
```

### 2. 性能优化

- 客户画像分析较耗时（2-3秒），建议异步处理
- 话术推荐可批量调用，减少API请求
- 使用话术库API预加载常用话术，减少实时计算

### 3. 数据安全

- 所有通信建议使用HTTPS
- 敏感客户信息加密存储
- 定期备份话术库和客户画像

---

## 联系支持

- 技术支持: tech-support@example.com
- 文档更新: docs@example.com
- GitHub: https://github.com/yourorg/ai-sales-script
