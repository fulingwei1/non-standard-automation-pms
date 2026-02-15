# 售前AI方案生成模块 - API文档

## 概述

售前AI方案生成模块提供智能化的技术方案生成能力，基于客户需求自动生成技术方案、系统架构图、BOM清单等文档。

**Base URL**: `/api/v1/presale/ai`

**认证方式**: Bearer Token (JWT)

---

## API端点列表

### 1. 模板匹配 - Match Templates

**端点**: `POST /match-templates`

**功能**: 基于需求自动匹配历史方案模板，返回TOP K个最佳模板

**请求体**:
```json
{
  "presale_ticket_id": 123,
  "requirement_analysis_id": 456,
  "industry": "汽车",
  "equipment_type": "装配",
  "keywords": "机器人 视觉定位 自动化",
  "top_k": 3
}
```

**响应**:
```json
{
  "matched_templates": [
    {
      "template_id": 1,
      "template_name": "汽车零部件装配线方案",
      "similarity_score": 0.85,
      "industry": "汽车",
      "equipment_type": "装配",
      "usage_count": 15,
      "avg_quality_score": 4.5
    }
  ],
  "total_templates": 3,
  "search_time_ms": 120
}
```

---

### 2. 生成完整方案 - Generate Solution

**端点**: `POST /generate-solution`

**功能**: AI智能生成完整技术方案，包含方案描述、技术参数、设备清单、工艺流程等

**请求体**:
```json
{
  "presale_ticket_id": 123,
  "requirement_analysis_id": 456,
  "template_id": 1,
  "requirements": {
    "industry": "汽车",
    "product_type": "变速箱装配",
    "capacity": "1000件/天",
    "automation_level": "95%",
    "budget": "100万-150万"
  },
  "generate_architecture": true,
  "generate_bom": true,
  "ai_model": "gpt-4"
}
```

**响应**:
```json
{
  "solution": {
    "id": 789,
    "presale_ticket_id": 123,
    "generated_solution": {
      "description": "基于客户需求，设计了...",
      "technical_parameters": {...},
      "equipment_list": [...],
      "process_flow": "...",
      "key_features": [...],
      "technical_advantages": [...]
    },
    "architecture_diagram": "graph TB\nA-->B",
    "bom_list": {...},
    "confidence_score": 0.87,
    "estimated_cost": 1200000.00,
    "status": "draft",
    "created_at": "2026-02-15T10:00:00Z"
  },
  "generation_time_seconds": 18.5,
  "ai_model_used": "gpt-4",
  "tokens_used": 3500
}
```

---

### 3. 生成架构图 - Generate Architecture

**端点**: `POST /generate-architecture`

**功能**: 生成系统架构图、设备拓扑图或信号流程图（Mermaid格式）

**请求体**:
```json
{
  "solution_id": 789,
  "requirements": {
    "equipment_count": 5,
    "control_system": "PLC + SCADA",
    "communication": "Profinet"
  },
  "diagram_type": "architecture",
  "format": "mermaid"
}
```

**diagram_type 可选值**:
- `architecture`: 系统架构图
- `topology`: 设备拓扑图
- `signal_flow`: 信号流程图

**响应**:
```json
{
  "diagram_code": "graph TB\n    A[上料单元] --> B[加工单元]\n    B --> C[检测单元]\n    ...",
  "diagram_type": "architecture",
  "format": "mermaid",
  "preview_url": null
}
```

---

### 4. 生成BOM清单 - Generate BOM

**端点**: `POST /generate-bom`

**功能**: 生成BOM清单，包含设备型号、数量、价格、供应商推荐

**请求体**:
```json
{
  "solution_id": 789,
  "equipment_list": [
    {
      "name": "六轴机器人",
      "model": "KUKA KR 60-3",
      "quantity": 3,
      "function": "零件抓取和装配"
    }
  ],
  "include_cost": true,
  "include_suppliers": true
}
```

**响应**:
```json
{
  "bom_items": [
    {
      "item_name": "六轴机器人",
      "model": "KUKA KR 60-3",
      "quantity": 3,
      "unit": "台",
      "unit_price": 250000.00,
      "total_price": 750000.00,
      "supplier": "KUKA官方代理",
      "lead_time_days": 60,
      "notes": "含安装调试"
    }
  ],
  "total_cost": 750000.00,
  "item_count": 1,
  "generation_time_seconds": 2.3
}
```

---

### 5. 获取方案 - Get Solution

**端点**: `GET /solution/{solution_id}`

**功能**: 获取方案详细信息

**路径参数**:
- `solution_id`: 方案ID

**响应**:
```json
{
  "id": 789,
  "presale_ticket_id": 123,
  "requirement_analysis_id": 456,
  "matched_template_ids": [1, 2, 3],
  "generated_solution": {...},
  "architecture_diagram": "...",
  "bom_list": {...},
  "solution_description": "...",
  "confidence_score": 0.87,
  "quality_score": 4.5,
  "estimated_cost": 1200000.00,
  "status": "draft",
  "created_by": 10,
  "created_at": "2026-02-15T10:00:00Z",
  "updated_at": "2026-02-15T12:00:00Z"
}
```

---

### 6. 更新方案 - Update Solution

**端点**: `PUT /solution/{solution_id}`

**功能**: 更新方案内容

**请求体**:
```json
{
  "generated_solution": {...},
  "architecture_diagram": "graph TB\nA-->B",
  "bom_list": {...},
  "solution_description": "更新后的方案描述",
  "status": "reviewing"
}
```

**响应**: 同 Get Solution

---

### 7. 导出PDF - Export Solution PDF

**端点**: `POST /export-solution-pdf`

**功能**: 导出方案为PDF文件

**请求体**:
```json
{
  "solution_id": 789,
  "include_diagrams": true,
  "include_bom": true,
  "template_style": "standard"
}
```

**响应**:
```json
{
  "success": true,
  "pdf_path": "/exports/presale_solutions/solution_789_20260215_120000.pdf",
  "message": "PDF导出成功"
}
```

---

### 8. 获取模板库 - Get Template Library

**端点**: `GET /template-library`

**功能**: 获取方案模板库列表

**查询参数**:
- `industry`: 行业筛选（可选）
- `equipment_type`: 设备类型筛选（可选）
- `is_active`: 是否启用（默认true）

**示例**: `GET /template-library?industry=汽车&equipment_type=装配`

**响应**:
```json
[
  {
    "id": 1,
    "name": "汽车零部件装配线方案",
    "code": "AUTO_ASSEMBLY_001",
    "industry": "汽车",
    "equipment_type": "装配",
    "complexity_level": "medium",
    "usage_count": 15,
    "avg_quality_score": 4.5,
    "typical_cost_range_min": 800000.00,
    "typical_cost_range_max": 1200000.00,
    "tags": ["汽车", "装配", "机器人"],
    "is_active": 1,
    "created_at": "2026-01-01T00:00:00Z"
  }
]
```

---

## 数据模型

### Solution Status 状态枚举

- `draft`: 草稿
- `reviewing`: 审核中
- `approved`: 已通过
- `rejected`: 已拒绝

### Complexity Level 复杂度枚举

- `simple`: 简单
- `medium`: 中等
- `complex`: 复杂

---

## 错误码

| HTTP Code | Error Code | 描述 |
|-----------|------------|------|
| 400 | BAD_REQUEST | 请求参数错误 |
| 401 | UNAUTHORIZED | 未授权 |
| 404 | NOT_FOUND | 资源不存在 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

**错误响应示例**:
```json
{
  "detail": "方案不存在"
}
```

---

## 使用示例

### Python示例

```python
import requests

API_BASE = "https://your-domain.com/api/v1/presale/ai"
TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 1. 匹配模板
response = requests.post(
    f"{API_BASE}/match-templates",
    json={
        "presale_ticket_id": 123,
        "industry": "汽车",
        "keywords": "机器人 装配",
        "top_k": 3
    },
    headers=headers
)
templates = response.json()

# 2. 生成方案
response = requests.post(
    f"{API_BASE}/generate-solution",
    json={
        "presale_ticket_id": 123,
        "template_id": templates["matched_templates"][0]["template_id"],
        "requirements": {
            "industry": "汽车",
            "capacity": "1000件/天"
        },
        "generate_architecture": True,
        "generate_bom": True
    },
    headers=headers
)
solution = response.json()

print(f"方案ID: {solution['solution']['id']}")
print(f"置信度: {solution['solution']['confidence_score']}")
```

---

## 性能指标

- 模板匹配: <1秒
- 方案生成: <30秒
- 架构图生成: <10秒
- BOM生成: <5秒

---

## 版本历史

- **v1.0.0** (2026-02-15): 初始版本发布
  - 8个核心API端点
  - 支持GPT-4和Kimi API
  - 30+单元测试覆盖

---

## 支持与反馈

技术支持: tech-support@company.com

文档更新: 2026-02-15
