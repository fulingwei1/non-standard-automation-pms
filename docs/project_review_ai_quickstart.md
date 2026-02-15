# 项目复盘智能化系统 - 快速入门

## 📖 概述

项目复盘智能化系统使用AI（GLM-5）自动生成项目总结报告、提取经验教训、对比历史项目并同步到售前知识库。

**核心功能**:
- 🤖 AI自动生成复盘报告（< 30秒）
- 📊 智能提取经验教训（准确率 ≥ 75%）
- 📈 历史项目对比分析
- 📚 自动同步售前知识库

---

## 🚀 快速开始

### 1. 前置要求

- Python 3.8+
- MySQL 5.7+
- 智谱AI API Key（GLM-5）

### 2. 数据库迁移

```bash
cd non-standard-automation-pms

# 运行迁移脚本
mysql -u root -p your_database < migrations/20260215_project_review_ai_enhancement.sql
```

### 3. 配置环境变量

在 `.env` 文件中添加：

```bash
ZHIPU_API_KEY=your_zhipu_api_key
```

### 4. 验证安装

```bash
# 运行验证脚本
python verify_project_review_system.py
```

看到 "所有验证通过" 即表示安装成功！

---

## 💼 基本使用

### 场景1: 生成项目复盘报告

**API**: `POST /api/v1/project-reviews/generate`

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/project-reviews/generate" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 123,
    "review_type": "POST_MORTEM",
    "reviewer_id": 1,
    "auto_extract_lessons": true,
    "auto_sync_knowledge": true
  }'
```

**响应示例**:
```json
{
  "success": true,
  "review_id": 456,
  "review_no": "REV20260215123",
  "processing_time_ms": 25000,
  "ai_summary": "项目整体完成情况良好...",
  "extracted_lessons_count": 8,
  "synced_to_knowledge": true,
  "knowledge_case_id": 789
}
```

**参数说明**:
- `project_id`: 项目ID（必填）
- `review_type`: 复盘类型（POST_MORTEM/MID_TERM/QUARTERLY）
- `reviewer_id`: 复盘负责人ID（必填）
- `auto_extract_lessons`: 是否自动提取经验教训（默认true）
- `auto_sync_knowledge`: 是否自动同步知识库（默认false）

---

### 场景2: 查看复盘报告

**API**: `GET /api/v1/project-reviews/{review_id}`

```bash
curl "http://localhost:8000/api/v1/project-reviews/456" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应包含**:
- 项目基本信息
- 周期和成本对比
- AI生成的总结
- 成功因素
- 问题与教训
- 改进建议
- 最佳实践
- 复盘结论

---

### 场景3: 提取经验教训

**API**: `POST /api/v1/project-reviews/lessons/extract`

```bash
curl -X POST "http://localhost:8000/api/v1/project-reviews/lessons/extract" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "review_id": 456,
    "min_confidence": 0.7,
    "auto_save": true
  }'
```

**响应示例**:
```json
{
  "success": true,
  "review_id": 456,
  "extracted_count": 8,
  "saved_count": 6,
  "lessons": [
    {
      "id": 101,
      "lesson_type": "SUCCESS",
      "title": "敏捷开发模式提升交付效率",
      "description": "采用两周迭代周期，每日站会...",
      "category": "管理",
      "priority": "HIGH",
      "ai_confidence": 0.85
    },
    ...
  ],
  "processing_time_ms": 15000
}
```

**置信度说明**:
- 0.9 - 1.0: 非常可靠
- 0.7 - 0.9: 较可靠
- 0.6 - 0.7: 一般可靠
- < 0.6: 建议人工审核

---

### 场景4: 历史项目对比

**API**: `POST /api/v1/project-reviews/comparison/compare`

```bash
curl -X POST "http://localhost:8000/api/v1/project-reviews/comparison/compare" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "review_id": 456,
    "similarity_type": "industry",
    "comparison_limit": 5
  }'
```

**相似度类型**:
- `industry`: 相同行业的项目
- `type`: 相同类型的项目
- `scale`: 相似规模的项目（预算接近）

**响应包含**:
- 当前项目指标
- 历史平均指标
- 差异分析
- 优势分析（2-3条）
- 劣势分析（2-3条）
- 改进建议（3-5条，含优先级）
- 基准对比

---

### 场景5: 同步到售前知识库

**API**: `POST /api/v1/project-reviews/knowledge/sync`

```bash
curl -X POST "http://localhost:8000/api/v1/project-reviews/knowledge/sync" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "review_id": 456,
    "auto_publish": true,
    "include_lessons": true
  }'
```

**同步内容**:
- 项目摘要（AI生成）
- 技术亮点
- 成功要素
- 失败教训
- 自动标签
- 质量评分

**质量评分计算**:
- 客户满意度（30%）
- 进度控制（20%）
- 成本控制（20%）
- 变更控制（10%）
- 内容完整性（20%）

---

## 📊 API端点总览

### 复盘报告管理

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/v1/project-reviews/generate` | AI生成复盘报告 |
| GET | `/api/v1/project-reviews` | 获取复盘列表 |
| GET | `/api/v1/project-reviews/{id}` | 获取复盘详情 |
| PATCH | `/api/v1/project-reviews/{id}` | 更新复盘 |
| DELETE | `/api/v1/project-reviews/{id}` | 删除复盘 |
| GET | `/api/v1/project-reviews/stats/summary` | 统计信息 |

### 经验教训管理

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/v1/project-reviews/lessons/extract` | AI提取经验教训 |
| GET | `/api/v1/project-reviews/lessons` | 获取经验列表 |
| GET | `/api/v1/lessons/{id}` | 获取经验详情 |
| PATCH | `/api/v1/lessons/{id}` | 更新经验 |
| GET | `/api/v1/lessons/{id}/similar` | 查找相似经验 |

### 对比分析

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/v1/project-reviews/comparison/compare` | 历史项目对比 |
| GET | `/api/v1/project-reviews/comparison/{id}/improvements` | 获取改进建议 |
| GET | `/api/v1/project-reviews/comparison/{id}/benchmarks` | 获取基准对比 |

### 知识库集成

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/v1/project-reviews/knowledge/sync` | 同步到知识库 |
| GET | `/api/v1/project-reviews/knowledge/{id}/knowledge-impact` | 查看知识库影响 |
| POST | `/api/v1/project-reviews/{id}/update-from-lessons` | 从经验更新知识库 |

---

## 🔧 高级用法

### 1. 批量生成复盘报告

```python
import requests

# 获取所有已完成项目
projects = get_completed_projects()

# 批量生成
for project in projects:
    response = requests.post(
        "http://localhost:8000/api/v1/project-reviews/generate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_id": project.id,
            "review_type": "POST_MORTEM",
            "reviewer_id": 1,
            "auto_extract_lessons": True,
            "auto_sync_knowledge": True
        }
    )
    print(f"项目 {project.code} 复盘完成")
```

### 2. 定制化经验提取

```python
# 只提取高置信度的成功经验
response = requests.get(
    "http://localhost:8000/api/v1/project-reviews/lessons",
    headers={"Authorization": f"Bearer {token}"},
    params={
        "review_id": 456,
        "lesson_type": "SUCCESS",
        "min_confidence": 0.8,
        "limit": 10
    }
)

lessons = response.json()
```

### 3. 多维度对比分析

```python
# 同时进行行业、类型、规模三个维度的对比
for similarity_type in ['industry', 'type', 'scale']:
    response = requests.post(
        "http://localhost:8000/api/v1/project-reviews/comparison/compare",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "review_id": 456,
            "similarity_type": similarity_type,
            "comparison_limit": 10
        }
    )
    print(f"{similarity_type} 对比结果:", response.json())
```

---

## 🎯 最佳实践

### 1. 何时生成复盘报告

✅ **推荐时机**:
- 项目完成后1周内（POST_MORTEM）
- 项目进行到50%时（MID_TERM）
- 每季度末（QUARTERLY）

❌ **避免**:
- 项目刚启动就复盘
- 数据不完整时强制生成

### 2. 提高报告质量

✅ **最佳实践**:
- 确保项目数据完整（工时、成本、变更记录）
- 添加 `additional_context` 补充背景信息
- 设置 `customer_satisfaction` 客户满意度

### 3. 经验教训管理

✅ **推荐做法**:
- 定期审查低置信度经验（< 0.7）
- 为关键经验添加责任人和截止日期
- 使用标签系统便于检索

### 4. 知识库复用

✅ **提高复用率**:
- 确保标签准确（行业、类型、规模）
- 定期更新质量评分
- 参考相似案例的成功经验

---

## 🐛 常见问题

### Q1: 报告生成失败

**可能原因**:
1. GLM-5 API Key未配置或无效
2. 项目数据不完整
3. 网络连接问题

**解决方法**:
```bash
# 1. 检查环境变量
echo $ZHIPU_API_KEY

# 2. 验证项目数据
SELECT * FROM projects WHERE id = 123;

# 3. 查看错误日志
tail -f logs/app.log
```

### Q2: 经验提取准确率低

**可能原因**:
1. 复盘报告内容太少
2. 描述不够具体

**解决方法**:
- 确保复盘报告包含足够的文本（每部分 > 50字）
- 使用具体案例而非泛泛而谈
- 调低 `min_confidence` 阈值（如0.5）

### Q3: 知识库同步失败

**可能原因**:
1. presale_knowledge_case 表不存在
2. 数据权限问题

**解决方法**:
```bash
# 检查表是否存在
SHOW TABLES LIKE 'presale_knowledge_case';

# 检查权限
SHOW GRANTS FOR CURRENT_USER;
```

---

## 📚 参考资料

- [完整API文档](http://localhost:8000/docs)
- [技术设计文档](./Agent_Team_7_项目复盘_实施计划.md)
- [交付报告](./Agent_Team_7_项目复盘_交付报告.md)

---

## 💡 提示

- 💾 定期备份复盘数据
- 🔐 控制知识库访问权限
- 📊 定期查看统计报表
- 🚀 持续优化提示词

---

## 📞 技术支持

遇到问题？

1. 查看 [常见问题](#常见问题)
2. 运行验证脚本诊断
3. 查看系统日志
4. 提交Issue

---

**版本**: v1.0  
**发布日期**: 2026-02-15  
**开发团队**: Team 7
