# 项目管理模块 API 文档

> **版本**: v1.0  
> **最后更新**: 2025-01-XX  
> **在线文档**: http://localhost:8000/docs

---

## 一、概述

项目管理模块提供项目全生命周期管理的 API，包括项目 CRUD、阶段推进、健康度计算、模板管理等功能。

### 基础信息

- **API 前缀**: `/api/v1/projects`
- **认证方式**: Bearer Token (JWT)
- **数据格式**: JSON
- **字符编码**: UTF-8

### 通用响应格式

所有 API 响应遵循统一格式：

```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

### 错误码说明

| 错误码 | 说明 | HTTP 状态码 |
|--------|------|-------------|
| 200 | 成功 | 200 |
| 400 | 请求参数错误 | 400 |
| 401 | 未授权 | 401 |
| 403 | 无权限 | 403 |
| 404 | 资源不存在 | 404 |
| 409 | 资源冲突（如编码重复） | 409 |
| 422 | 数据验证失败 | 422 |
| 500 | 服务器内部错误 | 500 |

---

## 二、项目 CRUD API

### 2.1 创建项目

**端点**: `POST /api/v1/projects/`

**功能**: 创建新项目

**请求体**:
```json
{
  "project_code": "PJ250101001",
  "project_name": "测试项目",
  "short_name": "测试",
  "customer_id": 1,
  "project_type": "FIXED_PRICE",
  "contract_amount": 100000.00,
  "budget_amount": 90000.00,
  "planned_start_date": "2025-01-01",
  "planned_end_date": "2025-04-01",
  "stage": "S1",
  "status": "ST01",
  "health": "H1"
}
```

**响应示例**:
```json
{
  "code": 201,
  "message": "项目创建成功",
  "data": {
    "id": 1,
    "project_code": "PJ250101001",
    "project_name": "测试项目",
    "stage": "S1",
    "status": "ST01",
    "health": "H1",
    "created_at": "2025-01-01T10:00:00"
  }
}
```

**字段说明**:
- `project_code`: 项目编码（必填，格式：PJ + YYMMDD + 序号）
- `project_name`: 项目名称（必填）
- `customer_id`: 客户ID（必填）
- `project_type`: 项目类型（FIXED_PRICE/TIME_MATERIAL）
- `stage`: 项目阶段（S1-S9，默认S1）
- `status`: 项目状态（ST01-ST99）
- `health`: 健康度（H1-H4，默认H1）

---

### 2.2 获取项目列表

**端点**: `GET /api/v1/projects/`

**功能**: 获取项目列表（支持分页、筛选、搜索）

**查询参数**:
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20，最大100）
- `stage`: 阶段筛选（S1-S9）
- `status`: 状态筛选（ST01-ST99）
- `health`: 健康度筛选（H1-H4）
- `keyword`: 关键词搜索（项目名称、编码）
- `customer_id`: 客户ID筛选
- `pm_id`: 项目经理ID筛选

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "project_code": "PJ250101001",
        "project_name": "测试项目",
        "stage": "S1",
        "status": "ST01",
        "health": "H1"
      }
    ],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

---

### 2.3 获取项目详情

**端点**: `GET /api/v1/projects/{project_id}`

**功能**: 获取项目详细信息

**路径参数**:
- `project_id`: 项目ID

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "project_code": "PJ250101001",
    "project_name": "测试项目",
    "customer_id": 1,
    "customer_name": "测试客户",
    "stage": "S1",
    "status": "ST01",
    "health": "H1",
    "contract_amount": 100000.00,
    "budget_amount": 90000.00,
    "planned_start_date": "2025-01-01",
    "planned_end_date": "2025-04-01",
    "machines": [],
    "milestones": [],
    "members": []
  }
}
```

---

### 2.4 更新项目

**端点**: `PUT /api/v1/projects/{project_id}`

**功能**: 更新项目信息

**请求体**: 同创建项目，所有字段可选

**响应示例**:
```json
{
  "code": 200,
  "message": "项目更新成功",
  "data": {
    "id": 1,
    "project_name": "更新后的项目名称",
    "updated_at": "2025-01-01T11:00:00"
  }
}
```

**注意事项**:
- 更新项目状态会自动触发健康度计算
- 项目编码不可修改

---

### 2.5 删除项目

**端点**: `DELETE /api/v1/projects/{project_id}`

**功能**: 软删除项目（设置 `is_active=False`）

**响应示例**:
```json
{
  "code": 200,
  "message": "项目删除成功"
}
```

---

## 三、阶段门校验 API

### 3.1 获取阶段门校验结果

**端点**: `GET /api/v1/projects/{project_id}/gate-check/{target_stage}`

**功能**: 获取项目推进到目标阶段的阶段门校验结果

**路径参数**:
- `project_id`: 项目ID
- `target_stage`: 目标阶段（S2-S9）

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "gate_code": "G1",
    "gate_name": "需求进入→需求澄清",
    "from_stage": "S1",
    "to_stage": "S2",
    "passed": false,
    "total_conditions": 2,
    "passed_conditions": 1,
    "failed_conditions": 1,
    "conditions": [
      {
        "condition_name": "客户信息齐全",
        "condition_desc": "客户名称、联系人、联系电话",
        "status": "PASSED",
        "message": "客户信息已完整",
        "action_url": "/projects/1/edit",
        "action_text": "去填写"
      },
      {
        "condition_name": "需求采集表完整",
        "condition_desc": "项目基本信息、需求描述",
        "status": "FAILED",
        "message": "请填写需求采集表",
        "action_url": "/projects/1/edit",
        "action_text": "去填写"
      }
    ],
    "missing_items": ["需求采集表"],
    "suggestions": ["请填写项目需求描述"],
    "progress_pct": 50.0
  }
}
```

**阶段门说明**:
- **G1**: S1→S2（需求进入→需求澄清）
- **G2**: S2→S3（需求澄清→立项评审）
- **G3**: S3→S4（立项评审→方案设计）
- **G4**: S4→S5（方案设计→采购制造）
- **G5**: S5→S6（采购制造→装配联调）
- **G6**: S6→S7（装配联调→出厂验收）
- **G7**: S7→S8（出厂验收→现场交付）
- **G8**: S8→S9（现场交付→质保结项）

---

### 3.2 推进项目阶段

**端点**: `POST /api/v1/projects/{project_id}/advance-stage`

**功能**: 推进项目到目标阶段（自动执行阶段门校验）

**请求体**:
```json
{
  "target_stage": "S2",
  "skip_gate_check": false,
  "remark": "需求已确认，可以进入下一阶段"
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "阶段推进成功",
  "data": {
    "project_id": 1,
    "old_stage": "S1",
    "new_stage": "S2",
    "gate_passed": true
  }
}
```

**错误响应**（Gate校验失败）:
```json
{
  "code": 400,
  "message": "阶段门校验未通过",
  "data": {
    "gate_code": "G1",
    "missing_items": ["需求采集表"],
    "suggestions": ["请填写项目需求描述"]
  }
}
```

**参数说明**:
- `target_stage`: 目标阶段（必填）
- `skip_gate_check`: 是否跳过Gate校验（默认false，仅管理员可跳过）
- `remark`: 推进原因备注（可选）

---

## 四、健康度计算 API

### 4.1 手动触发健康度计算

**端点**: `POST /api/v1/projects/{project_id}/health/calculate`

**功能**: 手动触发单个项目的健康度计算

**响应示例**:
```json
{
  "code": 200,
  "message": "健康度计算完成",
  "data": {
    "project_id": 1,
    "old_health": "H1",
    "new_health": "H2",
    "changed": true,
    "factors": {
      "deadline_approaching": true,
      "overdue_milestones": 0
    }
  }
}
```

---

### 4.2 批量计算健康度

**端点**: `POST /api/v1/projects/health/batch-calculate`

**功能**: 批量计算多个项目的健康度

**请求体**:
```json
{
  "project_ids": [1, 2, 3]
}
```

**响应示例**:
```json
{
  "code": 200,
  "message": "批量计算完成",
  "data": {
    "total": 3,
    "updated": 2,
    "unchanged": 1,
    "results": [
      {
        "project_id": 1,
        "old_health": "H1",
        "new_health": "H2",
        "changed": true
      }
    ]
  }
}
```

---

### 4.3 获取健康度详情

**端点**: `GET /api/v1/projects/{project_id}/health/details`

**功能**: 获取项目健康度的详细诊断信息

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "health": "H2",
    "diagnosis": "项目交期临近，存在风险",
    "factors": {
      "deadline_approaching": true,
      "days_until_deadline": 5,
      "overdue_milestones": 0,
      "blocking_issues": 0,
      "shortage_alerts": 0
    },
    "recommendations": [
      "建议加快项目进度",
      "关注交期风险"
    ]
  }
}
```

**健康度等级说明**:
- **H1**: 正常（绿色）- 项目按计划进行
- **H2**: 有风险（黄色）- 存在风险因素
- **H3**: 阻塞（红色）- 项目受阻，需要立即处理
- **H4**: 已完结（灰色）- 项目已结项或取消

---

## 五、项目模板 API

### 5.1 获取推荐模板

**端点**: `GET /api/v1/projects/templates/recommend`

**功能**: 根据项目属性推荐合适的项目模板

**查询参数**:
- `project_type`: 项目类型（FIXED_PRICE/TIME_MATERIAL）
- `device_type`: 设备类型
- `customer_id`: 客户ID

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "recommended_templates": [
      {
        "id": 1,
        "template_name": "标准测试设备模板",
        "match_score": 0.95,
        "match_reasons": ["项目类型匹配", "设备类型匹配"]
      }
    ]
  }
}
```

---

### 5.2 从模板创建项目

**端点**: `POST /api/v1/projects/templates/{template_id}/create-project`

**功能**: 使用模板创建新项目

**请求体**:
```json
{
  "project_code": "PJ250101002",
  "project_name": "从模板创建的项目",
  "customer_id": 1,
  "override_fields": {
    "contract_amount": 150000.00
  }
}
```

**响应示例**:
```json
{
  "code": 201,
  "message": "项目创建成功",
  "data": {
    "id": 2,
    "project_code": "PJ250101002",
    "template_id": 1,
    "template_name": "标准测试设备模板"
  }
}
```

---

## 六、项目状态日志 API

### 6.1 获取状态变更日志

**端点**: `GET /api/v1/projects/{project_id}/status-logs`

**功能**: 获取项目的状态变更历史记录

**查询参数**:
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认20）

**响应示例**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "items": [
      {
        "id": 1,
        "project_id": 1,
        "old_status": "ST01",
        "new_status": "ST02",
        "old_health": "H1",
        "new_health": "H1",
        "changed_by": 1,
        "changed_by_name": "张三",
        "changed_at": "2025-01-01T10:00:00",
        "remark": "项目状态更新"
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 20
  }
}
```

---

## 七、使用示例

### Python 示例

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = "your_jwt_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 创建项目
project_data = {
    "project_code": "PJ250101001",
    "project_name": "测试项目",
    "customer_id": 1,
    "stage": "S1"
}

response = requests.post(
    f"{BASE_URL}/projects/",
    json=project_data,
    headers=headers
)

project_id = response.json()["data"]["id"]

# 检查阶段门
gate_response = requests.get(
    f"{BASE_URL}/projects/{project_id}/gate-check/S2",
    headers=headers
)

gate_data = gate_response.json()["data"]
if gate_data["passed"]:
    # 推进阶段
    advance_response = requests.post(
        f"{BASE_URL}/projects/{project_id}/advance-stage",
        json={"target_stage": "S2"},
        headers=headers
    )
```

### JavaScript 示例

```javascript
const BASE_URL = 'http://localhost:8000/api/v1';
const TOKEN = 'your_jwt_token';

const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Content-Type': 'application/json'
};

// 创建项目
const projectData = {
  project_code: 'PJ250101001',
  project_name: '测试项目',
  customer_id: 1,
  stage: 'S1'
};

const response = await fetch(`${BASE_URL}/projects/`, {
  method: 'POST',
  headers,
  body: JSON.stringify(projectData)
});

const { data } = await response.json();
const projectId = data.id;

// 检查阶段门
const gateResponse = await fetch(
  `${BASE_URL}/projects/${projectId}/gate-check/S2`,
  { headers }
);

const gateData = (await gateResponse.json()).data;
if (gateData.passed) {
  // 推进阶段
  await fetch(`${BASE_URL}/projects/${projectId}/advance-stage`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ target_stage: 'S2' })
  });
}
```

---

## 八、常见问题

### Q1: 项目编码格式是什么？
A: 项目编码格式为 `PJ + YYMMDD + 序号（3位）`，例如：`PJ250101001`。

### Q2: 如何跳过阶段门校验？
A: 只有管理员可以跳过阶段门校验，在 `advance-stage` API 中设置 `skip_gate_check: true`。

### Q3: 健康度什么时候自动计算？
A: 健康度在以下情况自动计算：
- 项目状态更新时
- 项目阶段推进时
- 定时任务（每小时）

### Q4: 如何获取项目的完整信息？
A: 使用 `GET /api/v1/projects/{project_id}` 获取项目详情，包含关联的机台、里程碑、成员等信息。

---

## 九、相关文档

- [项目管理模块详细设计文档](../项目管理模块_详细设计文档.md)
- [项目管理模块用户手册](./项目管理模块用户手册.md)
- [Swagger UI](http://localhost:8000/docs)
- [ReDoc](http://localhost:8000/redoc)

---

**文档维护**: Backend Team  
**最后更新**: 2025-01-XX
