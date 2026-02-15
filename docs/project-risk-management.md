# 项目风险管理模块

## 概述

项目风险管理模块为项目提供全生命周期的风险识别、评估、跟踪和应对功能。支持4种风险类型，自动计算风险评分，提供风险矩阵和汇总统计等分析工具。

## 功能特性

### 1. 风险类型
- **技术风险（TECHNICAL）**：技术方案、技术难度、新技术应用等
- **成本风险（COST）**：预算超支、成本控制等
- **进度风险（SCHEDULE）**：延期、资源不足等
- **质量风险（QUALITY）**：质量标准、验收问题等

### 2. 风险评估
- **概率评分**：1-5分（1=很低，5=很高）
- **影响评分**：1-5分（1=很低，5=很高）
- **自动计算风险评分**：评分 = 概率 × 影响
- **自动分级**：
  - 1-4分：低风险（LOW）
  - 5-9分：中风险（MEDIUM）
  - 10-15分：高风险（HIGH）
  - 16-25分：极高风险（CRITICAL）

### 3. 风险状态
- **已识别（IDENTIFIED）**：风险已被识别
- **分析中（ANALYZING）**：正在分析风险
- **规划应对中（PLANNING）**：制定应对措施
- **监控中（MONITORING）**：持续监控
- **已缓解（MITIGATED）**：风险已得到缓解
- **已发生（OCCURRED）**：风险已经发生
- **已关闭（CLOSED）**：风险已关闭

### 4. 风险分析
- **风险矩阵**：5×5矩阵，直观展示风险分布
- **风险汇总统计**：按类型、等级、状态统计
- **平均风险评分**：项目整体风险水平指标

### 5. 权限控制
- `risk:create` - 创建风险
- `risk:read` - 查看风险
- `risk:update` - 更新风险
- `risk:delete` - 删除风险

### 6. 审计日志
所有风险的创建、更新、删除操作均记录审计日志，包括：
- 操作人
- 操作时间
- 操作类型
- 变更详情

## API接口

### 1. 创建风险

**请求**
```http
POST /api/v1/projects/{project_id}/risks
Authorization: Bearer {token}
Content-Type: application/json

{
  "risk_name": "技术风险-新算法实现",
  "description": "新的视觉识别算法可能存在性能问题",
  "risk_type": "TECHNICAL",
  "probability": 4,
  "impact": 5,
  "mitigation_plan": "提前进行技术验证",
  "contingency_plan": "准备备用方案",
  "owner_id": 123,
  "target_closure_date": "2026-03-01T00:00:00"
}
```

**响应**
```json
{
  "code": 200,
  "message": "风险创建成功",
  "data": {
    "id": 1,
    "risk_code": "RISK-PRJ001-0001",
    "project_id": 1,
    "risk_name": "技术风险-新算法实现",
    "description": "新的视觉识别算法可能存在性能问题",
    "risk_type": "TECHNICAL",
    "probability": 4,
    "impact": 5,
    "risk_score": 20,
    "risk_level": "CRITICAL",
    "mitigation_plan": "提前进行技术验证",
    "contingency_plan": "准备备用方案",
    "owner_id": 123,
    "owner_name": "张三",
    "status": "IDENTIFIED",
    "created_at": "2026-02-14T18:00:00"
  }
}
```

### 2. 获取风险列表

**请求**
```http
GET /api/v1/projects/{project_id}/risks?risk_type=TECHNICAL&risk_level=HIGH&offset=0&limit=20
Authorization: Bearer {token}
```

**查询参数**
- `risk_type`: 风险类型筛选（TECHNICAL/COST/SCHEDULE/QUALITY）
- `risk_level`: 风险等级筛选（LOW/MEDIUM/HIGH/CRITICAL）
- `status`: 状态筛选
- `owner_id`: 负责人ID筛选
- `is_occurred`: 是否已发生（true/false）
- `offset`: 偏移量（分页）
- `limit`: 每页数量（分页）

**响应**
```json
{
  "code": 200,
  "message": "获取风险列表成功",
  "data": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "risk_code": "RISK-PRJ001-0001",
        "risk_name": "技术风险-新算法实现",
        "risk_type": "TECHNICAL",
        "risk_score": 20,
        "risk_level": "CRITICAL",
        "status": "MONITORING",
        "owner_name": "张三",
        "created_at": "2026-02-14T18:00:00"
      }
    ]
  }
}
```

### 3. 获取风险详情

**请求**
```http
GET /api/v1/projects/{project_id}/risks/{risk_id}
Authorization: Bearer {token}
```

**响应**
```json
{
  "code": 200,
  "message": "获取风险详情成功",
  "data": {
    "id": 1,
    "risk_code": "RISK-PRJ001-0001",
    "project_id": 1,
    "risk_name": "技术风险-新算法实现",
    "description": "新的视觉识别算法可能存在性能问题",
    "risk_type": "TECHNICAL",
    "probability": 4,
    "impact": 5,
    "risk_score": 20,
    "risk_level": "CRITICAL",
    "mitigation_plan": "提前进行技术验证",
    "contingency_plan": "准备备用方案",
    "owner_id": 123,
    "owner_name": "张三",
    "status": "MONITORING",
    "identified_date": "2026-02-14T18:00:00",
    "target_closure_date": "2026-03-01T00:00:00",
    "is_occurred": false,
    "created_at": "2026-02-14T18:00:00",
    "updated_at": "2026-02-14T19:00:00"
  }
}
```

### 4. 更新风险

**请求**
```http
PUT /api/v1/projects/{project_id}/risks/{risk_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "risk_name": "技术风险-算法性能优化",
  "probability": 3,
  "impact": 4,
  "status": "MITIGATED",
  "mitigation_plan": "已完成技术验证，性能达标"
}
```

**响应**
```json
{
  "code": 200,
  "message": "风险更新成功",
  "data": {
    "id": 1,
    "risk_name": "技术风险-算法性能优化",
    "risk_score": 12,
    "risk_level": "HIGH",
    "status": "MITIGATED",
    "updated_at": "2026-02-14T20:00:00"
  }
}
```

### 5. 删除风险

**请求**
```http
DELETE /api/v1/projects/{project_id}/risks/{risk_id}
Authorization: Bearer {token}
```

**响应**
```json
{
  "code": 200,
  "message": "风险删除成功",
  "data": null
}
```

### 6. 获取风险矩阵

**请求**
```http
GET /api/v1/projects/{project_id}/risk-matrix
Authorization: Bearer {token}
```

**响应**
```json
{
  "code": 200,
  "message": "获取风险矩阵成功",
  "data": {
    "matrix": [
      {
        "probability": 1,
        "impact": 1,
        "count": 2,
        "risks": [
          {
            "id": 5,
            "risk_code": "RISK-PRJ001-0005",
            "risk_name": "低风险示例",
            "risk_type": "COST",
            "risk_score": 1,
            "risk_level": "LOW"
          }
        ]
      },
      {
        "probability": 5,
        "impact": 5,
        "count": 1,
        "risks": [
          {
            "id": 1,
            "risk_code": "RISK-PRJ001-0001",
            "risk_name": "技术风险-新算法实现",
            "risk_type": "TECHNICAL",
            "risk_score": 25,
            "risk_level": "CRITICAL"
          }
        ]
      }
    ],
    "summary": {
      "total_risks": 15,
      "critical_count": 2,
      "high_count": 5,
      "medium_count": 6,
      "low_count": 2
    }
  }
}
```

### 7. 获取风险汇总统计

**请求**
```http
GET /api/v1/projects/{project_id}/risk-summary
Authorization: Bearer {token}
```

**响应**
```json
{
  "code": 200,
  "message": "获取风险汇总统计成功",
  "data": {
    "total_risks": 25,
    "by_type": {
      "TECHNICAL": 10,
      "COST": 6,
      "SCHEDULE": 5,
      "QUALITY": 4
    },
    "by_level": {
      "CRITICAL": 3,
      "HIGH": 7,
      "MEDIUM": 10,
      "LOW": 5
    },
    "by_status": {
      "IDENTIFIED": 5,
      "ANALYZING": 3,
      "PLANNING": 2,
      "MONITORING": 10,
      "MITIGATED": 3,
      "OCCURRED": 1,
      "CLOSED": 1
    },
    "occurred_count": 1,
    "closed_count": 1,
    "high_priority_count": 10,
    "avg_risk_score": 9.5
  }
}
```

## 使用指南

### 1. 风险识别与创建

**步骤**：
1. 识别项目中可能的风险
2. 确定风险类型（技术/成本/进度/质量）
3. 评估发生概率（1-5分）
4. 评估影响程度（1-5分）
5. 制定应对措施和应急计划
6. 指定负责人
7. 调用创建风险API

**示例**：
```python
import requests

risk_data = {
    "risk_name": "供应商延期交货",
    "description": "关键物料供应商可能延期交货2周",
    "risk_type": "SCHEDULE",
    "probability": 3,  # 中等概率
    "impact": 4,       # 较高影响
    "mitigation_plan": "联系备用供应商，提前采购",
    "contingency_plan": "调整项目进度，优先其他任务",
    "owner_id": 123
}

response = requests.post(
    f"http://api.example.com/api/v1/projects/1/risks",
    json=risk_data,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

print(response.json())
# 系统自动计算：risk_score = 3 * 4 = 12 (HIGH)
```

### 2. 风险监控与更新

**步骤**：
1. 定期查看风险列表
2. 评估风险状态变化
3. 更新概率、影响或应对措施
4. 记录风险发生情况
5. 关闭已解决的风险

**示例**：
```python
# 更新风险状态为已缓解
update_data = {
    "status": "MITIGATED",
    "probability": 1,  # 降低概率
    "mitigation_plan": "已联系备用供应商并签订合同"
}

response = requests.put(
    f"http://api.example.com/api/v1/projects/1/risks/5",
    json=update_data,
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

### 3. 风险分析与报告

**步骤**：
1. 获取风险矩阵，识别高风险区域
2. 查看风险汇总统计
3. 重点关注极高风险（CRITICAL）和高风险（HIGH）
4. 定期向项目干系人汇报

**示例**：
```python
# 获取风险矩阵
response = requests.get(
    f"http://api.example.com/api/v1/projects/1/risk-matrix",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
matrix = response.json()["data"]

# 获取风险汇总
response = requests.get(
    f"http://api.example.com/api/v1/projects/1/risk-summary",
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
summary = response.json()["data"]

print(f"项目总风险数：{summary['total_risks']}")
print(f"高优先级风险：{summary['high_priority_count']}")
print(f"平均风险评分：{summary['avg_risk_score']}")
```

## 最佳实践

### 1. 风险识别
- 在项目启动阶段进行全面风险识别
- 每月至少进行一次风险回顾
- 鼓励团队成员主动识别新风险

### 2. 风险评估
- 使用团队共识评估概率和影响
- 参考历史项目数据
- 考虑最坏情况

### 3. 风险应对
- 高风险和极高风险必须制定应对措施
- 应对措施要具体、可执行
- 指定明确的负责人

### 4. 风险监控
- 每周检查高优先级风险状态
- 及时更新风险信息
- 风险发生时立即记录并启动应急计划

### 5. 风险关闭
- 风险消除或已转化为问题后关闭
- 关闭时记录经验教训
- 定期清理已关闭风险

## 常见问题

### Q1: 如何判断风险概率和影响？

**概率评分参考**：
- 1分：很低（<10%）
- 2分：低（10-30%）
- 3分：中（30-50%）
- 4分：高（50-70%）
- 5分：很高（>70%）

**影响评分参考**：
- 1分：很低（对项目影响微小）
- 2分：低（轻微影响）
- 3分：中（中等影响）
- 4分：高（重大影响）
- 5分：很高（严重影响，可能导致项目失败）

### Q2: 什么时候应该关闭风险？

以下情况可以关闭风险：
- 风险已完全消除
- 风险已发生并已解决
- 风险不再适用（如项目范围变更）
- 风险已转化为问题并在问题管理中跟踪

### Q3: 如何处理已发生的风险？

1. 将状态更新为"已发生（OCCURRED）"
2. 记录发生日期
3. 记录实际影响
4. 启动应急计划
5. 跟踪问题解决进度
6. 问题解决后关闭风险

### Q4: 风险评分如何自动计算？

系统自动计算：
```
风险评分 = 概率 × 影响

风险等级：
- 1-4分：低风险（LOW）
- 5-9分：中风险（MEDIUM）
- 10-15分：高风险（HIGH）
- 16-25分：极高风险（CRITICAL）
```

### Q5: 如何使用风险矩阵？

风险矩阵是5×5网格，展示所有风险的分布：
- **横轴**：影响程度（1-5）
- **纵轴**：发生概率（1-5）
- **右上角**：高概率、高影响（最危险）
- **左下角**：低概率、低影响（相对安全）

重点关注右上角的风险，优先制定应对措施。

## 数据字典

### ProjectRisk 表

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Integer | 是 | 主键ID |
| risk_code | String(50) | 是 | 风险编号（自动生成）|
| project_id | Integer | 是 | 项目ID |
| risk_name | String(200) | 是 | 风险名称 |
| description | Text | 否 | 风险描述 |
| risk_type | Enum | 是 | 风险类型（TECHNICAL/COST/SCHEDULE/QUALITY）|
| probability | Integer | 是 | 发生概率（1-5）|
| impact | Integer | 是 | 影响程度（1-5）|
| risk_score | Integer | 是 | 风险评分（自动计算）|
| risk_level | String(20) | 是 | 风险等级（自动计算）|
| mitigation_plan | Text | 否 | 应对措施 |
| contingency_plan | Text | 否 | 应急计划 |
| owner_id | Integer | 否 | 负责人ID |
| owner_name | String(50) | 否 | 负责人姓名 |
| status | Enum | 是 | 风险状态 |
| identified_date | DateTime | 否 | 识别日期 |
| target_closure_date | DateTime | 否 | 计划关闭日期 |
| actual_closure_date | DateTime | 否 | 实际关闭日期 |
| is_occurred | Boolean | 是 | 是否已发生 |
| occurrence_date | DateTime | 否 | 发生日期 |
| actual_impact | Text | 否 | 实际影响描述 |
| created_by_id | Integer | 否 | 创建人ID |
| created_by_name | String(50) | 否 | 创建人姓名 |
| updated_by_id | Integer | 否 | 最后更新人ID |
| updated_by_name | String(50) | 否 | 最后更新人姓名 |
| created_at | DateTime | 是 | 创建时间 |
| updated_at | DateTime | 是 | 更新时间 |

## 附录

### 权限配置示例

```sql
-- 创建风险管理权限
INSERT INTO api_permissions (permission_code, permission_name, resource, action, description) VALUES
('risk:create', '创建风险', 'risk', 'create', '创建项目风险'),
('risk:read', '查看风险', 'risk', 'read', '查看项目风险列表和详情'),
('risk:update', '更新风险', 'risk', 'update', '更新项目风险信息'),
('risk:delete', '删除风险', 'risk', 'delete', '删除项目风险');

-- 为项目经理角色分配权限
INSERT INTO role_api_permissions (role_id, permission_id)
SELECT r.id, p.id
FROM roles r, api_permissions p
WHERE r.role_code = 'PROJECT_MANAGER'
AND p.permission_code IN ('risk:create', 'risk:read', 'risk:update', 'risk:delete');
```

### 迁移脚本

数据库迁移文件：`migrations/20260214_182354_add_project_risk.py`

执行迁移：
```bash
# 使用Alembic或项目自定义迁移工具
python migrations/20260214_182354_add_project_risk.py
```

## 版本历史

- **v1.0.0** (2026-02-14)
  - 初始版本发布
  - 支持4种风险类型
  - 自动风险评分和分级
  - CRUD API完整实现
  - 风险矩阵和汇总统计
  - 权限控制和审计日志
