# 工程师设计问题统计功能 - API使用指南

> 创建日期：2026-01-07

---

## 一、API端点

### 1.1 创建/更新问题（支持新字段）

**创建问题**
```
POST /api/v1/issues
```

**请求体示例**：
```json
{
  "category": "TECHNICAL",
  "issue_type": "DEFECT",
  "severity": "MAJOR",
  "priority": "HIGH",
  "title": "设计错误导致物料浪费",
  "description": "设计图纸尺寸错误，导致加工件报废",
  "root_cause": "DESIGN_ERROR",
  "responsible_engineer_id": 123,
  "estimated_inventory_loss": 5000.00,
  "estimated_extra_hours": 8.5,
  "project_id": 1
}
```

**更新问题**
```
PUT /api/v1/issues/{issue_id}
```

**请求体示例**：
```json
{
  "root_cause": "DESIGN_ERROR",
  "responsible_engineer_id": 123,
  "estimated_inventory_loss": 5000.00,
  "estimated_extra_hours": 8.5
}
```

### 1.2 查询问题统计

**按工程师统计设计问题**
```
GET /api/v1/issues/statistics/engineer-design-issues
```

**查询参数**：
- `engineer_id` (可选): 工程师ID，不提供则统计所有工程师
- `start_date` (可选): 开始日期，格式：YYYY-MM-DD
- `end_date` (可选): 结束日期，格式：YYYY-MM-DD
- `project_id` (可选): 项目ID

**请求示例**：
```
GET /api/v1/issues/statistics/engineer-design-issues?engineer_id=123&start_date=2026-01-01&end_date=2026-01-31
```

**响应示例**：
```json
[
  {
    "engineer_id": 123,
    "engineer_name": "张三",
    "total_issues": 5,
    "design_issues": 5,
    "total_inventory_loss": 25000.00,
    "total_extra_hours": 42.5,
    "issues": [
      {
        "id": 1,
        "issue_no": "IS20260107001",
        "title": "设计错误导致物料浪费",
        "root_cause": "DESIGN_ERROR",
        "responsible_engineer_id": 123,
        "responsible_engineer_name": "张三",
        "estimated_inventory_loss": 5000.00,
        "estimated_extra_hours": 8.5,
        ...
      }
    ]
  }
]
```

---

## 二、问题原因枚举值

| 值 | 说明 |
|----|------|
| `DESIGN_ERROR` | 设计问题 |
| `MATERIAL_DEFECT` | 物料缺陷 |
| `PROCESS_ERROR` | 工艺问题 |
| `EXTERNAL_FACTOR` | 外部因素 |
| `OTHER` | 其他 |

---

## 三、关联成本和工时记录

### 3.1 关联成本记录

在创建`ProjectCost`时，在`description`字段中包含问题编号，例如：
```json
{
  "project_id": 1,
  "cost_type": "MATERIAL",
  "cost_category": "PURCHASE",
  "amount": 5000.00,
  "description": "因问题IS20260107001导致的库存损失",
  "cost_date": "2026-01-07"
}
```

系统会自动识别`description`中包含"库存"的成本记录为库存损失。

### 3.2 关联工时记录

在创建`Timesheet`时，在`work_content`或`work_result`字段中包含问题编号，例如：
```json
{
  "project_id": 1,
  "user_id": 456,
  "work_date": "2026-01-07",
  "hours": 8.5,
  "work_content": "修复问题IS20260107001的设计缺陷",
  "status": "APPROVED"
}
```

系统会自动识别并只计算已审批（`status='APPROVED'`）的工时记录。

---

## 四、使用流程

### 4.1 记录设计问题

1. 创建问题时，设置：
   - `root_cause = "DESIGN_ERROR"`
   - `responsible_engineer_id` = 责任工程师ID
   - `estimated_inventory_loss` = 预估库存损失（可选）
   - `estimated_extra_hours` = 预估额外工时（可选）

### 4.2 记录实际损失

1. **记录库存损失**：
   - 创建成本记录，在`description`中包含问题编号和"库存"关键词

2. **记录额外工时**：
   - 创建工时记录，在`work_content`或`work_result`中包含问题编号
   - 确保工时记录状态为`APPROVED`

### 4.3 查询统计

调用统计API，获取按工程师汇总的设计问题统计：
- 总问题数
- 设计问题数
- 总库存损失（预估+实际）
- 总额外工时（预估+实际）
- 问题列表详情

---

## 五、注意事项

1. **问题编号格式**：问题编号格式为`ISyymmddxxx`（例如：`IS20260107001`）
2. **关联匹配**：系统通过问题编号在成本/工时记录的文本字段中匹配，需要确保问题编号正确
3. **工时统计**：只统计已审批（`status='APPROVED'`）的工时记录
4. **库存损失识别**：只有`description`中包含"库存"关键词的成本记录才会被识别为库存损失
5. **日期筛选**：统计API支持按问题提出日期（`report_date`）筛选

---

## 六、示例场景

### 场景：统计某工程师1月份的设计问题

**请求**：
```
GET /api/v1/issues/statistics/engineer-design-issues?engineer_id=123&start_date=2026-01-01&end_date=2026-01-31
```

**响应**：
```json
[
  {
    "engineer_id": 123,
    "engineer_name": "张三",
    "total_issues": 3,
    "design_issues": 3,
    "total_inventory_loss": 15000.00,
    "total_extra_hours": 24.0,
    "issues": [
      {
        "issue_no": "IS20260107001",
        "title": "设计错误导致物料浪费",
        "estimated_inventory_loss": 5000.00,
        "estimated_extra_hours": 8.5,
        ...
      },
      {
        "issue_no": "IS20260110002",
        "title": "尺寸设计错误",
        "estimated_inventory_loss": 8000.00,
        "estimated_extra_hours": 12.0,
        ...
      },
      {
        "issue_no": "IS20260115003",
        "title": "材料选型错误",
        "estimated_inventory_loss": 2000.00,
        "estimated_extra_hours": 3.5,
        ...
      }
    ]
  }
]
```

---

*文档版本: 1.0*  
*更新日期: 2026-01-07*






