# AI项目规划助手 - 快速开始

## 🎯 5分钟上手指南

### 步骤1: 数据库初始化

```bash
# 执行数据库迁移
cd non-standard-automation-pms
sqlite3 data/app.db < migrations/20260215_ai_planning_assistant_sqlite.sql
```

### 步骤2: 配置GLM API密钥（可选）

```bash
# 方法1: 环境变量
export GLM_API_KEY="your_api_key_here"

# 方法2: .env文件
echo "GLM_API_KEY=your_api_key_here" >> .env
```

> **注意**: 如果不配置GLM API，系统会自动使用规则引擎备用方案。

### 步骤3: 运行验证脚本

```bash
python verify_ai_planning_assistant.py
```

如果所有验证通过，你会看到：
```
✅ 所有验证通过！系统工作正常。
```

---

## 📖 核心功能使用

### 1. 生成项目计划

**API调用**:
```bash
curl -X POST "http://localhost:8000/api/v1/ai-planning/generate-plan" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "project_name": "电商平台开发",
    "project_type": "WEB_DEV",
    "requirements": "开发B2C电商网站",
    "industry": "电商",
    "complexity": "HIGH"
  }'
```

**Python代码**:
```python
from app.services.ai_planning import AIProjectPlanGenerator

generator = AIProjectPlanGenerator(db)

template = await generator.generate_plan(
    project_name="电商平台开发",
    project_type="WEB_DEV",
    requirements="开发B2C电商网站",
    industry="电商",
    complexity="HIGH"
)

print(f"预计工期: {template.estimated_duration_days}天")
```

**返回示例**:
```json
{
  "template_id": 1,
  "template_name": "电商平台开发",
  "estimated_duration_days": 120,
  "estimated_effort_hours": 2880,
  "estimated_cost": 500000,
  "confidence_score": 85.0,
  "phases": [...],
  "milestones": [...]
}
```

---

### 2. WBS任务分解

**API调用**:
```bash
curl -X POST "http://localhost:8000/api/v1/ai-planning/decompose-wbs" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "project_id": 123,
    "template_id": 1,
    "max_level": 3
  }'
```

**Python代码**:
```python
from app.services.ai_planning import AIWbsDecomposer

decomposer = AIWbsDecomposer(db)

suggestions = await decomposer.decompose_project(
    project_id=123,
    template_id=1,
    max_level=3
)

for suggestion in suggestions:
    print(f"{suggestion.wbs_code} - {suggestion.task_name}")
```

**返回示例**:
```json
{
  "project_id": 123,
  "total_tasks": 25,
  "suggestions": [
    {
      "wbs_id": 1,
      "wbs_code": "1",
      "task_name": "需求分析",
      "level": 1,
      "estimated_duration_days": 15,
      "is_critical_path": true
    },
    {
      "wbs_id": 2,
      "wbs_code": "1.1",
      "task_name": "需求调研",
      "level": 2,
      "parent_id": 1,
      "estimated_duration_days": 5
    }
  ]
}
```

---

### 3. 资源分配优化

**API调用**:
```bash
curl -X POST "http://localhost:8000/api/v1/ai-planning/allocate-resources" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "wbs_suggestion_id": 5,
    "available_user_ids": [1, 2, 3, 4, 5]
  }'
```

**Python代码**:
```python
from app.services.ai_planning import AIResourceOptimizer

optimizer = AIResourceOptimizer(db)

allocations = await optimizer.allocate_resources(
    wbs_suggestion_id=5,
    available_user_ids=[1, 2, 3, 4, 5]
)

for alloc in allocations:
    print(f"用户{alloc.user_id}: 匹配度{alloc.overall_match_score}%")
```

**返回示例**:
```json
{
  "wbs_suggestion_id": 5,
  "total_recommendations": 3,
  "allocations": [
    {
      "allocation_id": 1,
      "user_id": 3,
      "allocation_type": "PRIMARY",
      "overall_match_score": 92.5,
      "skill_match_score": 95.0,
      "availability_score": 90.0,
      "estimated_cost": 16000,
      "recommendation_reason": "技能高度匹配；拥有丰富的相关经验"
    }
  ]
}
```

---

### 4. 进度排期优化

**API调用**:
```bash
curl -X POST "http://localhost:8000/api/v1/ai-planning/optimize-schedule" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "project_id": 123,
    "start_date": "2026-03-01"
  }'
```

**Python代码**:
```python
from app.services.ai_planning import AIScheduleOptimizer
from datetime import date

optimizer = AIScheduleOptimizer(db)

result = optimizer.optimize_schedule(
    project_id=123,
    start_date=date(2026, 3, 1)
)

print(f"总工期: {result['total_duration_days']}天")
print(f"关键路径: {result['critical_path_length']}个任务")
```

**返回示例**:
```json
{
  "project_id": 123,
  "start_date": "2026-03-01",
  "total_duration_days": 120,
  "end_date": "2026-06-29",
  "gantt_data": [...],
  "critical_path": [
    {
      "task_id": 1,
      "task_name": "需求分析",
      "duration_days": 15
    }
  ],
  "critical_path_length": 8,
  "conflicts": [],
  "recommendations": [
    {
      "category": "CRITICAL_PATH",
      "priority": "HIGH",
      "title": "关注关键路径任务",
      "actions": ["为关键任务分配最优秀的人员"]
    }
  ]
}
```

---

## 🧪 运行测试

### 运行所有测试
```bash
pytest tests/ai_planning/ -v
```

### 运行特定测试
```bash
# 测试计划生成器
pytest tests/ai_planning/test_plan_generator.py -v

# 测试WBS分解器
pytest tests/ai_planning/test_wbs_decomposer.py -v

# 测试资源优化器
pytest tests/ai_planning/test_resource_optimizer.py -v

# 测试排期优化器
pytest tests/ai_planning/test_schedule_optimizer.py -v

# 测试API
pytest tests/ai_planning/test_api.py -v
```

### 测试覆盖率
```bash
pytest tests/ai_planning/ --cov=app.services.ai_planning --cov-report=html
```

---

## 📊 性能基准

| 操作 | 目标 | 实际 |
|------|------|------|
| 生成项目计划 | ≤30秒 | ~15秒 |
| WBS分解（3层） | - | ~8秒 |
| 资源分配（10人） | - | ~2秒 |
| 进度排期（50任务） | - | ~2秒 |

---

## 🔍 常见问题

### Q: GLM API配置失败怎么办？
A: 系统会自动降级使用规则引擎备用方案，不影响基本功能。

### Q: 生成的计划不准确？
A: 系统会基于历史项目数据学习。增加更多历史项目数据可以提高准确性。

### Q: 如何提高WBS分解的准确性？
A: 
1. 提供更详细的项目需求描述
2. 使用经过验证的项目模板
3. 为AI提供更多参考项目

### Q: 资源分配考虑了哪些因素？
A: 
- 技能匹配度（40%权重）
- 经验匹配度（20%权重）
- 可用性（20%权重）
- 历史绩效（20%权重）

### Q: 关键路径如何计算？
A: 使用CPM（关键路径法）算法，浮动时间为0的任务即为关键路径上的任务。

---

## 📚 更多文档

- [完整API文档](./api-documentation.md)
- [算法说明](./algorithms.md)
- [最佳实践](./best-practices.md)
- [交付报告](../../Agent_Team_4_项目规划助手_交付报告.md)

---

## 💡 使用技巧

1. **提供详细需求**: 需求描述越详细，AI生成的计划越准确
2. **使用模板加速**: 对于常见项目类型，使用已验证的模板可以节省时间
3. **人工审核**: AI生成的结果仅供参考，建议人工审核后再使用
4. **反馈学习**: 及时反馈AI建议的采纳情况，帮助系统持续学习
5. **关注关键路径**: 重点关注关键路径上的任务，避免延期

---

## 🆘 获取帮助

- 查看日志: `tail -f logs/ai_planning.log`
- 运行诊断: `python verify_ai_planning_assistant.py`
- 查看API文档: `http://localhost:8000/docs`

---

**祝你使用愉快！** 🎉
