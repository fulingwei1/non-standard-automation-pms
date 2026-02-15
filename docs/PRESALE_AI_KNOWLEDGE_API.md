# 售前AI知识库API文档

## 📚 概述

售前AI知识库系统提供以下核心功能：
- 🔍 语义搜索相似案例
- 🌟 最佳实践推荐
- 🧠 知识自动沉淀
- 💬 智能问答系统

**Base URL**: `/api/v1/presale/ai`

---

## 🔌 API端点列表

### 1. 语义搜索相似案例

**POST** `/search-similar-cases`

基于需求语义搜索历史项目，支持多维度筛选。

**请求体**:
```json
{
  "query": "需要汽车零部件的ICT测试方案",
  "industry": "汽车制造",
  "equipment_type": "ICT测试设备",
  "min_amount": 100000,
  "max_amount": 1000000,
  "top_k": 10
}
```

**响应**:
```json
{
  "cases": [
    {
      "id": 1,
      "case_name": "某汽车零部件ICT测试项目",
      "industry": "汽车制造",
      "equipment_type": "ICT测试设备",
      "customer_name": "某汽车零部件公司",
      "project_amount": 500000,
      "project_summary": "为汽车零部件生产线提供ICT测试解决方案",
      "technical_highlights": "高精度测试、快速换线",
      "success_factors": "技术方案成熟、团队经验丰富",
      "lessons_learned": "需要提前确认客户现场环境",
      "tags": ["ICT测试", "汽车行业", "高精度"],
      "quality_score": 0.92,
      "similarity_score": 0.87,
      "created_at": "2026-02-15T10:00:00",
      "updated_at": "2026-02-15T10:00:00"
    }
  ],
  "total": 50,
  "query": "需要汽车零部件的ICT测试方案",
  "search_method": "semantic"
}
```

---

### 2. 获取案例详情

**GET** `/case/{case_id}`

根据ID获取单个案例的完整信息。

**路径参数**:
- `case_id` (int): 案例ID

**响应**:
```json
{
  "id": 1,
  "case_name": "某汽车零部件ICT测试项目",
  "industry": "汽车制造",
  "equipment_type": "ICT测试设备",
  "project_summary": "为汽车零部件生产线提供ICT测试解决方案",
  "quality_score": 0.92,
  "tags": ["ICT测试", "汽车行业"],
  "created_at": "2026-02-15T10:00:00"
}
```

---

### 3. 推荐最佳实践

**POST** `/recommend-best-practices`

基于场景推荐高质量案例和成功模式。

**请求体**:
```json
{
  "scenario": "需要为汽车零部件提供测试方案",
  "industry": "汽车制造",
  "equipment_type": "ICT测试设备",
  "top_k": 5
}
```

**响应**:
```json
{
  "recommended_cases": [
    {
      "id": 1,
      "case_name": "某汽车零部件ICT测试项目",
      "quality_score": 0.92,
      "similarity_score": 0.89
    }
  ],
  "success_pattern_analysis": "基于5个高质量案例的分析，主要成功模式包括：\n1. 技术方案的准确性和可行性\n2. 与客户需求的高度契合...",
  "risk_warnings": [
    "注意：需要提前确认客户现场环境，特别是防静电和温湿度要求",
    "建议仔细评估技术可行性"
  ]
}
```

---

### 4. 提取案例知识

**POST** `/extract-case-knowledge`

从项目数据中自动提取关键信息并生成案例。

**请求体**:
```json
{
  "project_data": {
    "project_name": "测试项目",
    "description": "项目描述",
    "industry": "汽车制造",
    "equipment_type": "ICT测试设备",
    "amount": 500000,
    "status": "completed",
    "technical_highlights": "技术亮点",
    "objectives": "项目目标"
  },
  "auto_save": true
}
```

**响应**:
```json
{
  "extracted_case": {
    "case_name": "测试项目",
    "industry": "汽车制造",
    "equipment_type": "ICT测试设备",
    "project_amount": 500000,
    "project_summary": "项目描述 | 项目目标",
    "technical_highlights": "技术亮点",
    "tags": ["汽车制造", "ICT测试设备", "大型项目"],
    "quality_score": 0.8
  },
  "extraction_confidence": 0.85,
  "suggested_tags": ["汽车制造", "ICT测试设备", "大型项目"],
  "quality_assessment": "高质量案例（置信度85%），建议保存到知识库"
}
```

---

### 5. 智能问答

**POST** `/qa`

基于知识库的智能问答系统。

**请求体**:
```json
{
  "question": "如何进行汽车零部件的ICT测试？",
  "context": {
    "industry": "汽车",
    "budget": 500000
  }
}
```

**响应**:
```json
{
  "answer": "根据知识库中的3个相关案例分析：\n\n1. 某汽车零部件ICT测试项目\n   技术要点：高精度测试、快速换线、实时数据采集...\n\n综合建议：参考以上案例的技术方案和实施经验...",
  "matched_cases": [
    {
      "id": 1,
      "case_name": "某汽车零部件ICT测试项目",
      "quality_score": 0.92
    }
  ],
  "confidence_score": 0.85,
  "sources": [
    "案例#1: 某汽车零部件ICT测试项目",
    "案例#2: 新能源汽车电池管理系统测试"
  ]
}
```

---

### 6. 知识库搜索

**GET** `/knowledge-base/search`

支持关键词、标签、行业等多维度搜索。

**查询参数**:
- `keyword` (string, optional): 搜索关键词
- `tags` (array, optional): 标签筛选
- `industry` (string, optional): 行业筛选
- `equipment_type` (string, optional): 设备类型筛选
- `min_quality_score` (float, optional): 最低质量评分
- `page` (int): 页码，默认1
- `page_size` (int): 每页数量，默认20

**示例**: `/knowledge-base/search?keyword=ICT&industry=汽车制造&page=1&page_size=20`

**响应**:
```json
{
  "cases": [
    {
      "id": 1,
      "case_name": "某汽车零部件ICT测试项目",
      "quality_score": 0.92
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

### 7. 添加案例

**POST** `/knowledge-base/add-case`

手动添加案例到知识库。

**请求体**:
```json
{
  "case_name": "新案例",
  "industry": "汽车制造",
  "equipment_type": "ICT测试设备",
  "customer_name": "客户名称",
  "project_amount": 500000,
  "project_summary": "项目摘要",
  "technical_highlights": "技术亮点",
  "success_factors": "成功要素",
  "lessons_learned": "失败教训",
  "tags": ["标签1", "标签2"],
  "quality_score": 0.8,
  "is_public": true
}
```

**响应**:
```json
{
  "id": 51,
  "case_name": "新案例",
  "quality_score": 0.8,
  "created_at": "2026-02-15T12:00:00"
}
```

---

### 8. 更新案例

**PUT** `/knowledge-base/case/{case_id}`

更新现有案例信息。

**路径参数**:
- `case_id` (int): 案例ID

**请求体** (所有字段可选):
```json
{
  "case_name": "更新后的案例名称",
  "project_summary": "更新后的摘要",
  "quality_score": 0.9,
  "tags": ["新标签1", "新标签2"]
}
```

---

### 9. 获取所有标签

**GET** `/knowledge-base/tags`

获取知识库中所有使用的标签及统计。

**响应**:
```json
{
  "tags": [
    "ICT测试",
    "汽车行业",
    "高精度",
    "功能测试"
  ],
  "tag_counts": {
    "ICT测试": 15,
    "汽车行业": 20,
    "高精度": 8,
    "功能测试": 25
  }
}
```

---

### 10. 问答反馈

**POST** `/qa-feedback`

提交智能问答的用户反馈。

**请求体**:
```json
{
  "qa_id": 123,
  "feedback_score": 5,
  "feedback_comment": "回答很有帮助"
}
```

**响应**:
```json
{
  "message": "反馈已提交",
  "qa_id": 123
}
```

---

## 📊 数据模型

### KnowledgeCase (案例)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | int | 案例ID |
| case_name | string | 案例名称 |
| industry | string | 行业分类 |
| equipment_type | string | 设备类型 |
| customer_name | string | 客户名称 |
| project_amount | float | 项目金额 |
| project_summary | string | 项目摘要 |
| technical_highlights | string | 技术亮点 |
| success_factors | string | 成功要素 |
| lessons_learned | string | 失败教训 |
| tags | array | 标签数组 |
| quality_score | float | 案例质量评分 (0-1) |
| is_public | boolean | 是否公开 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

---

## 🔧 使用示例

### Python示例

```python
import requests

BASE_URL = "http://localhost:8000/api/v1/presale/ai"

# 1. 语义搜索
response = requests.post(f"{BASE_URL}/search-similar-cases", json={
    "query": "需要汽车零部件的ICT测试方案",
    "industry": "汽车制造",
    "top_k": 5
})
cases = response.json()["cases"]
print(f"找到 {len(cases)} 个相似案例")

# 2. 智能问答
response = requests.post(f"{BASE_URL}/qa", json={
    "question": "如何进行ICT测试？"
})
answer = response.json()["answer"]
print(f"AI回答: {answer}")

# 3. 添加案例
response = requests.post(f"{BASE_URL}/knowledge-base/add-case", json={
    "case_name": "新项目",
    "industry": "制造业",
    "project_summary": "项目摘要",
    "quality_score": 0.8
})
case_id = response.json()["id"]
print(f"案例创建成功，ID: {case_id}")
```

### cURL示例

```bash
# 语义搜索
curl -X POST "http://localhost:8000/api/v1/presale/ai/search-similar-cases" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ICT测试方案",
    "top_k": 5
  }'

# 智能问答
curl -X POST "http://localhost:8000/api/v1/presale/ai/qa" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "如何选择测试设备？"
  }'
```

---

## ⚙️ 配置说明

### 向量嵌入

系统使用向量嵌入支持语义搜索。默认使用模拟嵌入，生产环境建议配置：

1. **OpenAI嵌入** (推荐):
```python
# 在 presale_ai_knowledge_service.py 中修改 _generate_embedding 方法
import openai
openai.api_key = "your-api-key"
response = openai.Embedding.create(model="text-embedding-ada-002", input=text)
return np.array(response['data'][0]['embedding'])
```

2. **Kimi API嵌入**:
```python
# 使用 Kimi API 配置
```

---

## 📈 性能指标

- **搜索响应时间**: <2秒
- **案例搜索准确率**: >80%
- **推荐相关性评分**: >4/5
- **知识提取完整度**: >85%
- **问答准确率**: >80%

---

## 🐛 错误处理

所有API在出错时返回标准错误响应：

```json
{
  "detail": "错误描述信息"
}
```

常见HTTP状态码：
- `200`: 成功
- `404`: 资源不存在
- `422`: 请求参数验证失败
- `500`: 服务器内部错误

---

## 🚀 快速开始

1. **运行数据库迁移**:
```bash
python migrations/versions/20260215_add_presale_ai_knowledge_base.py
```

2. **导入示例案例**:
```bash
python scripts/import_ai_knowledge_cases.py
```

3. **生成嵌入向量**:
```bash
python scripts/generate_embeddings.py
```

4. **测试API**:
```bash
pytest tests/test_presale_ai_knowledge.py -v
```

---

## 📞 支持

如有问题，请联系技术团队或查阅[完整文档](./PRESALE_AI_KNOWLEDGE_USER_GUIDE.md)。
