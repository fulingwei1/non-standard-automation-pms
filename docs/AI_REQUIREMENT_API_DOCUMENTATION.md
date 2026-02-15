# AI智能需求理解引擎 - API文档

## 概述

AI智能需求理解引擎通过先进的自然语言处理技术，将客户的非结构化需求描述自动转化为结构化的技术规格文档。

**版本**: v1.0.0  
**基础URL**: `/api/v1/presale/ai`  
**认证方式**: Bearer Token

---

## API端点列表

### 1. 分析需求 (Analyze Requirement)

**端点**: `POST /api/v1/presale/ai/analyze-requirement`

**描述**: 使用AI分析客户的原始需求描述，生成结构化需求文档。

**功能特性**:
- 提取核心需求和目标
- 识别设备清单
- 生成工艺流程
- 提取技术参数
- 自动生成5-10个澄清问题
- 评估技术可行性
- 计算置信度评分

**请求体**:
```json
{
  "presale_ticket_id": 123,
  "raw_requirement": "我们需要一条自动化生产线，用于手机外壳的组装和检测。产能要求：每小时200件，工艺流程：上料 -> 视觉检测 -> 自动组装 -> 质量检测 -> 下料。设备要求：工业机器人、视觉检测系统...",
  "ai_model": "gpt-4",
  "analysis_depth": "standard"
}
```

**参数说明**:
| 参数 | 类型 | 必填 | 说明 | 默认值 |
|------|------|------|------|--------|
| presale_ticket_id | integer | 是 | 售前工单ID | - |
| raw_requirement | string | 是 | 原始需求描述 (≥10字符) | - |
| ai_model | string | 否 | AI模型 | "gpt-4" |
| analysis_depth | string | 否 | 分析深度: quick/standard/deep | "standard" |

**响应示例** (HTTP 201):
```json
{
  "id": 456,
  "presale_ticket_id": 123,
  "raw_requirement": "我们需要...",
  "structured_requirement": {
    "project_type": "手机外壳组装自动化",
    "industry": "消费电子",
    "core_objectives": ["提升产能", "保证质量", "降低人工成本"],
    "functional_requirements": ["自动上料", "视觉检测", "自动组装"],
    "non_functional_requirements": ["产能≥200件/小时", "精度±0.05mm"],
    "constraints": ["温度20-25℃"],
    "assumptions": ["手机外壳标准化"]
  },
  "clarification_questions": [
    {
      "question_id": 1,
      "category": "技术参数",
      "question": "请明确视觉检测系统的分辨率和检测速度要求",
      "importance": "critical",
      "suggested_answer": null
    },
    {
      "question_id": 2,
      "category": "功能需求",
      "question": "组装过程是否需要力控功能？",
      "importance": "high",
      "suggested_answer": "建议配置力控传感器以保证组装质量"
    }
  ],
  "confidence_score": 0.82,
  "feasibility_analysis": {
    "overall_feasibility": "high",
    "technical_risks": ["视觉检测算法需要针对性训练"],
    "resource_requirements": {
      "人力": "3名集成工程师，2名调试工程师",
      "设备": "六轴机器人×2，3D视觉系统×2"
    },
    "estimated_complexity": "medium",
    "development_challenges": ["多工位协调同步", "视觉算法优化"],
    "recommendations": ["建议先进行工艺可行性验证", "考虑分阶段实施"]
  },
  "equipment_list": [
    {
      "name": "六轴工业机器人",
      "type": "机器人",
      "quantity": 2,
      "specifications": {
        "负载": "5kg",
        "重复精度": "±0.02mm"
      },
      "priority": "high"
    },
    {
      "name": "3D视觉检测系统",
      "type": "检测设备",
      "quantity": 2,
      "priority": "high"
    }
  ],
  "process_flow": [
    {
      "step_number": 1,
      "name": "上料",
      "description": "自动上料系统将工件放置到传送带",
      "parameters": {
        "节拍时间": "18秒/件"
      },
      "equipment_required": ["上料机构", "传送带"]
    },
    {
      "step_number": 2,
      "name": "视觉检测",
      "description": "3D视觉系统检测工件外观和尺寸",
      "parameters": {
        "检测时间": "3秒/件",
        "精度": "±0.01mm"
      },
      "equipment_required": ["3D视觉系统"]
    }
  ],
  "technical_parameters": [
    {
      "parameter_name": "产能",
      "value": "200件/小时",
      "unit": "件/小时",
      "tolerance": null,
      "is_critical": true
    },
    {
      "parameter_name": "组装精度",
      "value": "±0.05mm",
      "unit": "mm",
      "tolerance": "±0.01mm",
      "is_critical": true
    }
  ],
  "acceptance_criteria": [
    "产能达到200件/小时",
    "组装精度±0.05mm",
    "连续稳定运行24小时无故障",
    "视觉检测准确率≥99.5%"
  ],
  "ai_model_used": "gpt-4",
  "status": "draft",
  "is_refined": false,
  "refinement_count": 0,
  "created_at": "2026-02-15T10:30:00Z",
  "updated_at": "2026-02-15T10:30:00Z"
}
```

**性能指标**: 
- 响应时间: <3秒
- 需求理解准确率: >85%
- 澄清问题覆盖率: >90%

---

### 2. 获取分析结果 (Get Analysis)

**端点**: `GET /api/v1/presale/ai/analysis/{analysis_id}`

**描述**: 根据分析ID获取完整的需求分析结果。

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| analysis_id | integer | 分析记录ID |

**响应示例** (HTTP 200):
```json
{
  "id": 456,
  "presale_ticket_id": 123,
  "raw_requirement": "...",
  "structured_requirement": {...},
  "confidence_score": 0.82,
  "status": "draft"
}
```

**错误响应** (HTTP 404):
```json
{
  "detail": "分析记录 999 不存在"
}
```

---

### 3. 精炼需求 (Refine Requirement)

**端点**: `POST /api/v1/presale/ai/refine-requirement`

**描述**: 基于额外的上下文信息，精炼和深化需求分析。

**使用场景**:
- 客户提供了补充信息
- 需要更深入的分析
- 首次分析置信度较低 (<0.60)

**请求体**:
```json
{
  "analysis_id": 456,
  "additional_context": "客户补充说明：需要支持3种不同规格的手机外壳，要求快速换型，换型时间<15分钟。另外，车间为10万级洁净室。",
  "focus_areas": ["柔性制造", "快速换型", "洁净度控制"]
}
```

**参数说明**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| analysis_id | integer | 是 | 要精炼的分析记录ID |
| additional_context | string | 否 | 额外的上下文信息 |
| focus_areas | array[string] | 否 | 重点关注的领域 |

**响应示例** (HTTP 200):
```json
{
  "id": 456,
  "confidence_score": 0.91,
  "is_refined": true,
  "refinement_count": 1,
  "structured_requirement": {
    "project_type": "柔性手机外壳组装自动化",
    "core_objectives": ["提升产能", "快速换型", "保证洁净度"],
    "functional_requirements": ["自动上料", "视觉检测", "自动组装", "快速换型系统"],
    "constraints": ["10万级洁净室", "换型时间<15分钟", "温度20-25℃"]
  },
  "equipment_list": [
    {
      "name": "柔性工装夹具系统",
      "type": "工装夹具",
      "quantity": 1,
      "priority": "high"
    }
  ]
}
```

**效果**:
- 更详细的结构化需求
- 更精确的设备清单
- 更完整的技术参数
- 置信度评分提升

---

### 4. 获取澄清问题 (Get Clarification Questions)

**端点**: `GET /api/v1/presale/ai/clarification-questions/{ticket_id}`

**描述**: 获取针对特定售前工单的AI生成澄清问题列表。

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| ticket_id | integer | 售前工单ID |

**响应示例** (HTTP 200):
```json
{
  "analysis_id": 456,
  "presale_ticket_id": 123,
  "questions": [
    {
      "question_id": 1,
      "category": "技术参数",
      "question": "请明确设备的具体技术参数要求（如速度、精度、负载等）",
      "importance": "critical",
      "suggested_answer": null
    },
    {
      "question_id": 2,
      "category": "功能需求",
      "question": "是否需要数据采集和MES系统对接？",
      "importance": "high",
      "suggested_answer": "建议集成MES接口以实现生产数据实时监控"
    },
    {
      "question_id": 3,
      "category": "约束条件",
      "question": "现场是否有特殊的空间、环境或安全约束？",
      "importance": "high",
      "suggested_answer": null
    },
    {
      "question_id": 4,
      "category": "验收标准",
      "question": "项目的验收标准和成功指标是什么？",
      "importance": "critical",
      "suggested_answer": null
    },
    {
      "question_id": 5,
      "category": "资源预算",
      "question": "项目的预算范围和交付时间要求是什么？",
      "importance": "medium",
      "suggested_answer": null
    }
  ],
  "total_count": 8,
  "critical_count": 2,
  "high_priority_count": 4
}
```

**问题分类**:
- `技术参数`: 设备性能、工艺参数等
- `功能需求`: 系统功能、特殊需求
- `约束条件`: 空间、环境、安全等限制
- `验收标准`: 质量标准、性能指标
- `资源预算`: 成本、时间、人力

**问题优先级**:
- `critical`: 必须澄清，影响方案可行性
- `high`: 高度建议澄清
- `medium`: 建议澄清
- `low`: 可选澄清

---

### 5. 更新结构化需求 (Update Structured Requirement)

**端点**: `POST /api/v1/presale/ai/update-structured-requirement`

**描述**: 手动更新和完善AI生成的结构化需求。

**用途**:
- 修正AI的识别错误
- 补充AI遗漏的信息
- 根据客户反馈调整需求

**请求体**:
```json
{
  "analysis_id": 456,
  "structured_requirement": {
    "project_type": "手机外壳组装自动化（修正后）",
    "industry": "消费电子",
    "core_objectives": ["提升产能", "保证质量", "降低人工成本", "提高柔性"],
    "functional_requirements": ["自动上料", "视觉检测", "自动组装", "快速换型"],
    "non_functional_requirements": ["产能≥200件/小时", "精度±0.05mm", "换型时间<15分钟"]
  },
  "equipment_list": [
    {
      "name": "六轴工业机器人",
      "type": "机器人",
      "quantity": 2,
      "specifications": {
        "负载": "10kg",
        "重复精度": "±0.02mm",
        "工作半径": "1400mm"
      },
      "priority": "high"
    }
  ],
  "technical_parameters": [
    {
      "parameter_name": "产能",
      "value": "220件/小时",
      "unit": "件/小时",
      "tolerance": null,
      "is_critical": true
    }
  ],
  "acceptance_criteria": [
    "产能达到220件/小时（含10%余量）",
    "组装精度±0.05mm",
    "连续稳定运行48小时",
    "视觉检测准确率≥99.5%",
    "换型时间≤15分钟"
  ]
}
```

**参数说明**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| analysis_id | integer | 是 | 分析记录ID |
| structured_requirement | object | 否 | 结构化需求 |
| equipment_list | array | 否 | 设备清单 |
| process_flow | array | 否 | 工艺流程 |
| technical_parameters | array | 否 | 技术参数 |
| acceptance_criteria | array | 否 | 验收标准 |

**响应示例** (HTTP 200):
```json
{
  "id": 456,
  "status": "reviewed",
  "structured_requirement": {...},
  "equipment_list": [...],
  "updated_at": "2026-02-15T11:45:00Z"
}
```

---

### 6. 获取置信度评分 (Get Requirement Confidence)

**端点**: `GET /api/v1/presale/ai/requirement-confidence/{ticket_id}`

**描述**: 获取AI需求理解的置信度评分和评估建议。

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| ticket_id | integer | 售前工单ID |

**响应示例** (HTTP 200):
```json
{
  "analysis_id": 456,
  "presale_ticket_id": 123,
  "confidence_score": 0.82,
  "score_breakdown": {
    "需求完整性": 0.25,
    "技术清晰度": 0.24,
    "参数明确性": 0.21,
    "可执行性": 0.12
  },
  "assessment": "medium_confidence",
  "recommendations": [
    "需求基本清晰，建议澄清部分细节",
    "重点关注技术参数的明确性",
    "建议补充验收标准"
  ]
}
```

**置信度等级**:

| 等级 | 分数范围 | 评估 | 建议 |
|------|----------|------|------|
| high_confidence | ≥0.85 | 需求理解充分 | 可以进入方案设计阶段 |
| medium_confidence | 0.60-0.84 | 需求基本清晰 | 建议澄清部分细节 |
| low_confidence | <0.60 | 需求信息不足 | 需要与客户进一步沟通 |

**评分维度**:
- **需求完整性** (30%): 核心需求、功能需求、约束条件的完整度
- **技术清晰度** (30%): 技术路线、设备选型、工艺流程的清晰度
- **参数明确性** (25%): 技术参数、性能指标的明确程度
- **可执行性** (15%): 需求的可实施性和可验证性

---

## 通用响应格式

### 成功响应
所有成功的API调用都返回相应的数据对象。

### 错误响应

**400 Bad Request** - 请求参数错误:
```json
{
  "detail": "需求描述至少10个字符"
}
```

**401 Unauthorized** - 未授权:
```json
{
  "detail": "未提供认证信息"
}
```

**404 Not Found** - 资源不存在:
```json
{
  "detail": "分析记录 999 不存在"
}
```

**500 Internal Server Error** - 服务器错误:
```json
{
  "detail": "需求分析失败: OpenAI API连接超时"
}
```

---

## 认证

所有API端点都需要Bearer Token认证。

**请求头示例**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

获取Token请参考: [认证API文档](/docs/auth.md)

---

## 使用示例

### Python示例

```python
import requests

API_BASE = "http://localhost:8000/api/v1"
TOKEN = "your_access_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 1. 分析需求
data = {
    "presale_ticket_id": 123,
    "raw_requirement": """
        我们需要一条手机外壳自动化组装线。
        产能：200件/小时
        工艺：上料->视觉检测->组装->质检->下料
        精度要求：±0.05mm
    """,
    "analysis_depth": "standard"
}

response = requests.post(
    f"{API_BASE}/presale/ai/analyze-requirement",
    json=data,
    headers=headers
)

analysis = response.json()
print(f"置信度: {analysis['confidence_score']}")
print(f"识别设备数: {len(analysis['equipment_list'])}")

# 2. 获取澄清问题
ticket_id = 123
response = requests.get(
    f"{API_BASE}/presale/ai/clarification-questions/{ticket_id}",
    headers=headers
)

questions = response.json()
print(f"需要澄清 {questions['total_count']} 个问题")
for q in questions['questions']:
    print(f"[{q['importance']}] {q['question']}")

# 3. 检查置信度
response = requests.get(
    f"{API_BASE}/presale/ai/requirement-confidence/{ticket_id}",
    headers=headers
)

confidence = response.json()
print(f"置信度评分: {confidence['confidence_score']}")
print(f"评估: {confidence['assessment']}")
```

### cURL示例

```bash
# 分析需求
curl -X POST "http://localhost:8000/api/v1/presale/ai/analyze-requirement" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "presale_ticket_id": 123,
    "raw_requirement": "我们需要一条自动化生产线...",
    "analysis_depth": "standard"
  }'

# 获取分析结果
curl -X GET "http://localhost:8000/api/v1/presale/ai/analysis/456" \
  -H "Authorization: Bearer $TOKEN"

# 获取澄清问题
curl -X GET "http://localhost:8000/api/v1/presale/ai/clarification-questions/123" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 性能和限制

| 指标 | 值 |
|------|-----|
| 最大请求体大小 | 10MB |
| 需求描述最小长度 | 10字符 |
| 需求描述最大长度 | 10000字符 |
| API调用速率限制 | 60次/分钟 |
| 响应时间(P95) | <3秒 |
| 澄清问题数量 | 5-10个 |
| 置信度评分范围 | 0.00-1.00 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2026-02-15 | 初始版本，包含6个核心API端点 |

---

## 支持与反馈

如有问题或建议，请联系：
- 技术支持: tech-support@company.com
- 文档反馈: doc-feedback@company.com
