# 工程师进度管理API快速参考

## 📚 目录

1. [工程师端API (9个端点)](#工程师端api)
2. [PM审批端API (4个端点)](#pm审批端api)
3. [通用查询API (2个端点)](#通用查询api)
4. [认证说明](#认证说明)
5. [错误码参考](#错误码参考)

---

## 工程师端API

### 1. GET `/api/v1/engineers/my-projects` - 获取我的项目列表

**功能：** 获取当前工程师参与的所有项目，包含任务统计信息

**请求参数：**
```
Query Parameters:
- page: int = 1 (页码)
- page_size: int = 20 (每页数量，最大100)
```

**响应示例：**
```json
{
  "items": [
    {
      "project_id": 1,
      "project_code": "PJ260101001",
      "project_name": "ICT测试设备项目",
      "customer_name": "某客户",
      "stage": "S4",
      "status": "IN_PROGRESS",
      "health": "H1",
      "progress_pct": 45.5,
      "my_roles": ["机械工程师", "装配工程师"],
      "my_allocation_pct": 100,
      "task_stats": {
        "total_tasks": 15,
        "pending_tasks": 2,
        "in_progress_tasks": 8,
        "completed_tasks": 5,
        "overdue_tasks": 1,
        "delayed_tasks": 0,
        "pending_approval_tasks": 0
      },
      "planned_start_date": "2026-01-01",
      "planned_end_date": "2026-03-31",
      "last_activity_at": "2026-01-07T10:30:00"
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

**使用场景：** 工程师工作台首页显示

---

### 2. POST `/api/v1/engineers/tasks` - 创建任务

**功能：** 创建新任务，支持智能审批路由（IMPORTANT任务自动进入审批流程）

**请求体：**
```json
{
  "project_id": 1,
  "title": "设计机械装配方案",
  "description": "根据客户需求设计装配方案",
  "task_importance": "IMPORTANT",  // IMPORTANT | GENERAL
  "justification": "此任务是项目关键路径节点，影响整体进度",  // IMPORTANT必填
  "wbs_code": "1.2.3",
  "plan_start_date": "2026-01-08",
  "plan_end_date": "2026-01-15",
  "deadline": "2026-01-15T18:00:00",
  "estimated_hours": 40,
  "priority": "HIGH",  // URGENT | HIGH | MEDIUM | LOW
  "tags": ["机械设计", "方案"],
  "category": "设计"
}
```

**响应示例：**
```json
{
  "id": 123,
  "task_code": "TASK20260107001",
  "title": "设计机械装配方案",
  "status": "PENDING_APPROVAL",  // IMPORTANT→PENDING_APPROVAL, GENERAL→ACCEPTED
  "approval_required": true,
  "approval_status": "PENDING_APPROVAL",
  "task_importance": "IMPORTANT",
  "progress": 0,
  "priority": "HIGH",
  "assignee_id": 5,
  "project_id": 1,
  "created_at": "2026-01-07T14:20:00",
  "updated_at": "2026-01-07T14:20:00"
}
```

**智能路由规则：**
- `task_importance=IMPORTANT` → 需要PM审批 → `status=PENDING_APPROVAL`
- `task_importance=GENERAL` → 直接创建 → `status=ACCEPTED`

**使用场景：** 工程师添加自己发现的任务节点

---

### 3. PUT `/api/v1/engineers/tasks/{task_id}` - 更新任务基础信息

**功能：** 更新任务的基础信息（标题、描述、计划时间等）

**路径参数：**
- `task_id`: int (任务ID)

**请求体：** (所有字段可选)
```json
{
  "title": "更新后的任务标题",
  "description": "更新后的描述",
  "plan_start_date": "2026-01-10",
  "plan_end_date": "2026-01-20",
  "deadline": "2026-01-20T18:00:00",
  "estimated_hours": 50,
  "priority": "URGENT",
  "tags": ["机械设计", "紧急"]
}
```

**响应：** 完整的TaskResponse对象

**权限：** 仅任务负责人可更新

**使用场景：** 修正任务信息、调整计划时间

---

### 4. PUT `/api/v1/engineers/tasks/{task_id}/progress` - 更新任务进度

**功能：** 更新任务进度，自动触发项目和阶段进度聚合

**路径参数：**
- `task_id`: int (任务ID)

**请求体：**
```json
{
  "progress": 50,  // 0-100
  "actual_hours": 20.5,
  "progress_note": "已完成方案初稿，等待评审"
}
```

**响应示例：**
```json
{
  "task_id": 123,
  "progress": 50,
  "actual_hours": 20.5,
  "status": "IN_PROGRESS",
  "project_progress_updated": true,
  "stage_progress_updated": true
}
```

**自动状态转换：**
- `progress > 0` 且 `status=ACCEPTED` → 自动转为 `IN_PROGRESS`
- `progress = 100` → 自动转为 `COMPLETED`

**聚合触发：**
1. 计算项目所有任务的加权平均进度 → 更新 `Project.progress_pct`
2. 计算阶段所有任务的加权平均进度 → 更新 `ProjectStage.progress_pct`
3. 检查并更新项目健康度 (H1/H2/H3)

**使用场景：** 每日/每周进度更新

---

### 5. PUT `/api/v1/engineers/tasks/{task_id}/complete` - 完成任务

**功能：** 标记任务完成，需要填写完成说明

**路径参数：**
- `task_id`: int (任务ID)

**请求体：**
```json
{
  "completion_note": "装配方案已完成并通过评审，相关图纸已归档",
  "skip_proof_validation": false  // 是否跳过证明材料验证
}
```

**响应示例：**
```json
{
  "task_id": 123,
  "status": "COMPLETED",
  "progress": 100,
  "actual_end_date": "2026-01-15",
  "completion_note": "装配方案已完成并通过评审，相关图纸已归档",
  "proof_count": 3
}
```

**验证规则：**
- 默认情况下，任务必须有至少1个完成证明才能完成
- 可通过 `skip_proof_validation=true` 跳过验证（不推荐）

**使用场景：** 任务全部完成时

---

### 6. POST `/api/v1/engineers/tasks/{task_id}/completion-proofs/upload` - 上传完成证明

**功能：** 上传任务完成证明材料（文档、照片、视频、测试报告等）

**路径参数：**
- `task_id`: int (任务ID)

**请求体：** (multipart/form-data)
```
Form Data:
- file: File (上传的文件)
- proof_type: str (DOCUMENT | PHOTO | VIDEO | TEST_REPORT | DATA)
- file_category: str (可选，如：DRAWING, SPEC, SITE_PHOTO等)
- description: str (可选，文件说明)
```

**cURL示例：**
```bash
curl -X POST "http://localhost:8000/api/v1/engineers/tasks/123/completion-proofs/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/document.pdf" \
  -F "proof_type=DOCUMENT" \
  -F "file_category=DRAWING" \
  -F "description=装配方案设计图纸"
```

**响应示例：**
```json
{
  "id": 45,
  "task_id": 123,
  "proof_type": "DOCUMENT",
  "file_category": "DRAWING",
  "file_name": "assembly_design.pdf",
  "file_size": 2048576,
  "file_type": "pdf",
  "description": "装配方案设计图纸",
  "uploaded_at": "2026-01-15T16:30:00"
}
```

**支持的证明类型：**
- `DOCUMENT`: 技术文档、图纸、规格书
- `PHOTO`: 现场照片、产品照片
- `VIDEO`: 测试视频、演示视频
- `TEST_REPORT`: 测试报告、检测报告
- `DATA`: 测试数据、日志文件

**文件限制：**
- 最大文件大小：10MB（可配置）
- 存储路径：`uploads/task_proofs/{task_id}/`

**使用场景：** 任务完成前上传证明材料

---

### 7. GET `/api/v1/engineers/tasks/{task_id}/completion-proofs` - 获取完成证明列表

**功能：** 获取指定任务的所有完成证明材料

**路径参数：**
- `task_id`: int (任务ID)

**响应示例：**
```json
{
  "task_id": 123,
  "proofs": [
    {
      "id": 45,
      "task_id": 123,
      "proof_type": "DOCUMENT",
      "file_category": "DRAWING",
      "file_name": "assembly_design.pdf",
      "file_size": 2048576,
      "file_type": "pdf",
      "description": "装配方案设计图纸",
      "uploaded_at": "2026-01-15T16:30:00"
    },
    {
      "id": 46,
      "task_id": 123,
      "proof_type": "PHOTO",
      "file_name": "site_photo_001.jpg",
      "file_size": 512000,
      "file_type": "jpg",
      "description": "装配现场照片",
      "uploaded_at": "2026-01-15T17:00:00"
    }
  ],
  "total_count": 2
}
```

**使用场景：** 查看任务证明材料、审核完成情况

---

### 8. DELETE `/api/v1/engineers/tasks/{task_id}/completion-proofs/{proof_id}` - 删除完成证明

**功能：** 删除指定的完成证明材料（同时删除数据库记录和物理文件）

**路径参数：**
- `task_id`: int (任务ID)
- `proof_id`: int (证明ID)

**响应：** 204 No Content

**权限：** 仅任务负责人或证明上传者可删除

**使用场景：** 删除错误上传或过期的证明材料

---

### 9. POST `/api/v1/engineers/tasks/{task_id}/report-delay` - 报告任务延期

**功能：** 报告任务延期，记录详细延期信息，触发通知和健康度更新

**路径参数：**
- `task_id`: int (任务ID)

**请求体：**
```json
{
  "delay_reason": "客户需求变更导致方案需要重新设计，涉及主要结构调整",
  "delay_responsibility": "客户需求变更",
  "delay_impact_scope": "PROJECT",  // LOCAL | PROJECT | MULTI_PROJECT
  "schedule_impact_days": 5,
  "cost_impact": 8000.00,  // 可选
  "new_completion_date": "2026-01-20",
  "root_cause_analysis": "客户在评审会上提出新的安全要求",  // 可选
  "preventive_measures": "后续方案评审前要求客户确认所有安全规范"  // 可选
}
```

**响应示例：**
```json
{
  "task_id": 123,
  "exception_event_id": 89,
  "delay_visible_to": ["PM", "部门经理", "项目组成员"],
  "notifications_sent_count": 5,
  "health_status_updated": true
}
```

**延期影响范围：**
- `LOCAL`: 仅影响本任务，不影响其他任务
- `PROJECT`: 影响本项目其他任务
- `MULTI_PROJECT`: 影响多个项目（跨项目依赖）

**自动触发：**
1. 创建异常事件记录 (ExceptionEvent)
2. 更新任务延期状态 (`is_delayed=True`)
3. 发送通知给相关人员（PM、部门经理等）
4. 更新项目健康度（可能从H1→H2或H2→H3）

**使用场景：** 任务预计无法按时完成时及时上报

---

## PM审批端API

### 10. GET `/api/v1/engineers/tasks/pending-approval` - 获取待审批任务列表

**功能：** PM查看所有待自己审批的任务

**请求参数：**
```
Query Parameters:
- page: int = 1
- page_size: int = 20
```

**响应：** TaskListResponse (任务列表)

**筛选条件：**
- `approval_status = PENDING_APPROVAL`
- `approved_by = 当前PM的ID` 或 `项目PM = 当前用户`

**使用场景：** PM审批中心页面

---

### 11. PUT `/api/v1/engineers/tasks/{task_id}/approve` - 批准任务

**功能：** PM批准任务，任务状态变为ACCEPTED，可以开始执行

**路径参数：**
- `task_id`: int (任务ID)

**请求体：**
```json
{
  "approval_note": "任务必要性合理，同意创建"  // 可选
}
```

**响应示例：**
```json
{
  "task_id": 123,
  "approval_status": "APPROVED",
  "approved_by": 2,
  "approved_at": "2026-01-08T09:30:00",
  "approval_note": "任务必要性合理，同意创建"
}
```

**状态变化：**
- `approval_status`: PENDING_APPROVAL → APPROVED
- `status`: PENDING_APPROVAL → ACCEPTED
- 更新审批工作流记录

**权限验证：**
- 必须是项目PM
- 任务必须在待审批状态

**使用场景：** PM批准工程师创建的重要任务

---

### 12. PUT `/api/v1/engineers/tasks/{task_id}/reject` - 拒绝任务

**功能：** PM拒绝任务，需要说明拒绝原因

**路径参数：**
- `task_id`: int (任务ID)

**请求体：**
```json
{
  "rejection_reason": "任务与项目范围不符，建议调整为维护类任务"
}
```

**响应示例：**
```json
{
  "task_id": 123,
  "approval_status": "REJECTED",
  "approved_by": 2,
  "approved_at": "2026-01-08T09:30:00",
  "approval_note": "任务与项目范围不符，建议调整为维护类任务"
}
```

**状态变化：**
- `approval_status`: PENDING_APPROVAL → REJECTED
- `status`: PENDING_APPROVAL → CANCELLED
- 更新审批工作流记录

**使用场景：** PM拒绝不合理的任务创建申请

---

### 13. GET `/api/v1/engineers/tasks/{task_id}/approval-history` - 查看审批历史

**功能：** 查看任务的完整审批历史

**路径参数：**
- `task_id`: int (任务ID)

**响应示例：**
```json
[
  {
    "id": 56,
    "task_id": 123,
    "submitted_by": 5,
    "submitted_at": "2026-01-07T14:20:00",
    "submit_note": "此任务是项目关键路径节点",
    "approver_id": 2,
    "approval_status": "APPROVED",
    "approved_at": "2026-01-08T09:30:00",
    "approval_note": "任务必要性合理，同意创建",
    "task_details": {
      "title": "设计机械装配方案",
      "estimated_hours": 40
    }
  }
]
```

**使用场景：** 审计、历史追溯

---

## 通用查询API

### 14. GET `/api/v1/engineers/tasks` - 获取我的任务列表

**功能：** 查询当前用户的任务，支持多维度筛选

**请求参数：**
```
Query Parameters:
- project_id: int (可选，筛选特定项目)
- status: str (可选，PENDING|ACCEPTED|IN_PROGRESS|COMPLETED|CANCELLED)
- priority: str (可选，URGENT|HIGH|MEDIUM|LOW)
- is_delayed: bool (可选，筛选延期任务)
- is_overdue: bool (可选，筛选逾期任务)
- page: int = 1
- page_size: int = 20
```

**响应：** TaskListResponse

**示例URL：**
```
GET /api/v1/engineers/tasks?project_id=1&status=IN_PROGRESS&page=1&page_size=20
```

**使用场景：** 任务列表页面、任务筛选

---

### 15. GET `/api/v1/engineers/tasks/{task_id}` - 获取任务详情

**功能：** 获取任务的完整详细信息

**路径参数：**
- `task_id`: int (任务ID)

**响应：** 完整的TaskResponse对象

**使用场景：** 任务详情页面

---

### 16. GET `/api/v1/engineers/projects/{project_id}/progress-visibility` - 跨部门进度可见性

**功能：** 获取项目的跨部门进度视图，解决"各部门看不到彼此进度"痛点

**路径参数：**
- `project_id`: int (项目ID)

**响应示例：**
```json
{
  "project_id": 1,
  "project_name": "ICT测试设备项目",
  "overall_progress": 45.5,
  "department_progress": [
    {
      "department_id": 1,
      "department_name": "机械部",
      "total_tasks": 20,
      "completed_tasks": 8,
      "in_progress_tasks": 10,
      "delayed_tasks": 2,
      "progress_pct": 42.5,
      "members": [
        {
          "name": "张工",
          "total_tasks": 12,
          "completed_tasks": 5,
          "in_progress_tasks": 6,
          "progress_pct": 45.0
        },
        {
          "name": "李工",
          "total_tasks": 8,
          "completed_tasks": 3,
          "in_progress_tasks": 4,
          "progress_pct": 37.5
        }
      ]
    },
    {
      "department_id": 2,
      "department_name": "电气部",
      "total_tasks": 18,
      "completed_tasks": 10,
      "in_progress_tasks": 7,
      "delayed_tasks": 1,
      "progress_pct": 55.6,
      "members": [...]
    }
  ],
  "stage_progress": {
    "S1": {"progress": 100.0, "status": "COMPLETED"},
    "S2": {"progress": 100.0, "status": "COMPLETED"},
    "S3": {"progress": 90.0, "status": "COMPLETED"},
    "S4": {"progress": 45.5, "status": "IN_PROGRESS"},
    "S5": {"progress": 0.0, "status": "PENDING"}
  },
  "active_delays": [
    {
      "task_id": 115,
      "task_title": "电气原理图设计",
      "assignee_name": "王工",
      "department": "电气部",
      "delay_days": 3,
      "impact_scope": "PROJECT",
      "new_completion_date": "2026-01-12",
      "delay_reason": "客户需求变更导致重新设计",
      "reported_at": "2026-01-06T16:00:00"
    }
  ],
  "last_updated_at": "2026-01-07T14:25:00"
}
```

**数据维度：**
1. **部门级统计**：各部门任务数、完成率、进行中、延期数
2. **人员级统计**：每个成员的任务分布和进度
3. **阶段级进度**：各阶段(S1-S9)的完成情况
4. **活跃延期**：当前所有延期任务的详细信息

**使用场景：**
- 部门经理了解本部门在各项目中的工作进度
- PM了解项目整体跨部门协作情况
- 项目看板展示

---

## 认证说明

所有API端点都需要JWT认证。

### 获取Token

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "engineer01",
  "password": "your_password"
}

# 响应
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 5,
    "username": "engineer01",
    "real_name": "张工",
    "department": "机械部"
  }
}
```

### 使用Token

在所有请求的Header中添加：

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**cURL示例：**
```bash
curl -X GET "http://localhost:8000/api/v1/engineers/my-projects" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json"
```

**JavaScript Fetch示例：**
```javascript
const token = localStorage.getItem('access_token');

fetch('http://localhost:8000/api/v1/engineers/my-projects', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
})
.then(response => response.json())
.then(data => console.log(data));
```

---

## 错误码参考

### HTTP状态码

| 状态码 | 说明 | 场景 |
|--------|------|------|
| 200 | 成功 | GET/PUT请求成功 |
| 201 | 创建成功 | POST创建资源成功 |
| 204 | 无内容 | DELETE删除成功 |
| 400 | 请求错误 | 参数验证失败 |
| 401 | 未认证 | Token缺失或无效 |
| 403 | 无权限 | 没有操作权限 |
| 404 | 未找到 | 资源不存在 |
| 422 | 验证错误 | Pydantic验证失败 |
| 500 | 服务器错误 | 内部错误 |

### 常见错误响应

**401 Unauthorized - Token无效：**
```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden - 权限不足：**
```json
{
  "detail": "您没有权限审批此任务"
}
```

**404 Not Found - 资源不存在：**
```json
{
  "detail": "Task not found"
}
```

**400 Bad Request - 参数错误：**
```json
{
  "detail": "重要任务必须填写任务必要性说明"
}
```

**422 Validation Error - 数据验证失败：**
```json
{
  "detail": [
    {
      "loc": ["body", "progress"],
      "msg": "ensure this value is greater than or equal to 0",
      "type": "value_error.number.not_ge"
    }
  ]
}
```

---

## 数据字典

### 任务状态 (status)

| 值 | 说明 | 可转换到 |
|----|------|----------|
| PENDING | 待接收 | ACCEPTED, CANCELLED |
| PENDING_APPROVAL | 待审批 | APPROVED→ACCEPTED, REJECTED→CANCELLED |
| ACCEPTED | 已接收 | IN_PROGRESS, CANCELLED |
| IN_PROGRESS | 进行中 | COMPLETED, CANCELLED |
| COMPLETED | 已完成 | - |
| CANCELLED | 已取消 | - |

### 审批状态 (approval_status)

| 值 | 说明 |
|----|------|
| PENDING_APPROVAL | 待审批 |
| APPROVED | 已批准 |
| REJECTED | 已拒绝 |

### 任务重要性 (task_importance)

| 值 | 说明 | 审批要求 |
|----|------|----------|
| IMPORTANT | 重要任务 | 需要PM审批 |
| GENERAL | 一般任务 | 无需审批 |

### 优先级 (priority)

| 值 | 说明 |
|----|------|
| URGENT | 紧急 |
| HIGH | 高 |
| MEDIUM | 中 |
| LOW | 低 |

### 延期影响范围 (delay_impact_scope)

| 值 | 说明 |
|----|------|
| LOCAL | 仅影响本任务 |
| PROJECT | 影响本项目其他任务 |
| MULTI_PROJECT | 影响多个项目 |

### 证明类型 (proof_type)

| 值 | 说明 | 示例 |
|----|------|------|
| DOCUMENT | 文档 | 图纸、规格书、说明书 |
| PHOTO | 照片 | 现场照片、产品照片 |
| VIDEO | 视频 | 测试视频、演示视频 |
| TEST_REPORT | 测试报告 | 检测报告、验收报告 |
| DATA | 数据文件 | 测试数据、日志文件 |

### 项目健康度 (health)

| 值 | 说明 | 颜色 | 触发条件 |
|----|------|------|----------|
| H1 | 正常 | 绿色 | 延期<10%，逾期<5% |
| H2 | 有风险 | 黄色 | 延期10-25%，或逾期5-15% |
| H3 | 阻塞 | 红色 | 延期>25%，或逾期>15% |
| H4 | 已完结 | 灰色 | 项目已关闭 |

---

## 前端集成示例

### React Hook - 获取我的项目列表

```javascript
import { useState, useEffect } from 'react';
import axios from 'axios';

function useMyProjects(page = 1, pageSize = 20) {
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({});

  useEffect(() => {
    const fetchProjects = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('access_token');
        const response = await axios.get(
          `/api/v1/engineers/my-projects?page=${page}&page_size=${pageSize}`,
          {
            headers: { Authorization: `Bearer ${token}` }
          }
        );
        setProjects(response.data.items);
        setPagination({
          total: response.data.total,
          page: response.data.page,
          pageSize: response.data.page_size,
          pages: response.data.pages
        });
      } catch (err) {
        setError(err.response?.data?.detail || '获取项目列表失败');
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, [page, pageSize]);

  return { projects, loading, error, pagination };
}

// 使用
function MyProjectsPage() {
  const { projects, loading, error, pagination } = useMyProjects(1, 10);

  if (loading) return <div>加载中...</div>;
  if (error) return <div>错误: {error}</div>;

  return (
    <div>
      {projects.map(project => (
        <ProjectCard key={project.project_id} project={project} />
      ))}
      <Pagination {...pagination} />
    </div>
  );
}
```

### Vue 3 Composition API - 更新任务进度

```javascript
import { ref } from 'vue';
import axios from 'axios';

export function useTaskProgress() {
  const updating = ref(false);
  const error = ref(null);

  const updateProgress = async (taskId, progressData) => {
    updating.value = true;
    error.value = null;

    try {
      const token = localStorage.getItem('access_token');
      const response = await axios.put(
        `/api/v1/engineers/tasks/${taskId}/progress`,
        progressData,
        {
          headers: { Authorization: `Bearer ${token}` }
        }
      );

      // 显示聚合结果提示
      if (response.data.project_progress_updated) {
        console.log('项目进度已更新');
      }
      if (response.data.stage_progress_updated) {
        console.log('阶段进度已更新');
      }

      return response.data;
    } catch (err) {
      error.value = err.response?.data?.detail || '更新进度失败';
      throw err;
    } finally {
      updating.value = false;
    }
  };

  return { updateProgress, updating, error };
}

// 使用
const { updateProgress, updating, error } = useTaskProgress();

const handleProgressUpdate = async () => {
  try {
    await updateProgress(123, {
      progress: 50,
      actual_hours: 20.5,
      progress_note: '已完成方案初稿'
    });
    // 刷新任务列表
  } catch (err) {
    // 显示错误消息
  }
};
```

---

## 性能优化建议

### 1. 分页查询

**所有列表查询都应使用分页：**
```javascript
// 不推荐：一次性加载所有数据
GET /api/v1/engineers/tasks

// 推荐：使用分页
GET /api/v1/engineers/tasks?page=1&page_size=20
```

### 2. 条件筛选

**优先使用后端筛选而非前端筛选：**
```javascript
// 不推荐：获取所有任务再前端筛选
const allTasks = await fetchAllTasks();
const inProgressTasks = allTasks.filter(t => t.status === 'IN_PROGRESS');

// 推荐：后端筛选
const inProgressTasks = await fetchTasks({ status: 'IN_PROGRESS' });
```

### 3. 避免频繁请求

**使用防抖/节流处理频繁操作：**
```javascript
import { debounce } from 'lodash';

const debouncedUpdateProgress = debounce(async (taskId, progress) => {
  await updateProgress(taskId, progress);
}, 1000); // 1秒内多次调用只执行最后一次
```

### 4. 缓存策略

**对不常变化的数据使用缓存：**
```javascript
// 使用SWR或React Query
import useSWR from 'swr';

function useMyProjects() {
  const { data, error, mutate } = useSWR(
    '/api/v1/engineers/my-projects',
    fetcher,
    {
      revalidateOnFocus: false,  // 窗口聚焦时不重新验证
      dedupingInterval: 60000    // 60秒内不重复请求
    }
  );

  return { projects: data, error, refresh: mutate };
}
```

---

## 测试工具推荐

### Postman Collection

导入以下JSON到Postman快速测试所有端点：

```json
{
  "info": {
    "name": "工程师进度管理API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "工程师端",
      "item": [
        {
          "name": "获取我的项目列表",
          "request": {
            "method": "GET",
            "header": [
              {
                "key": "Authorization",
                "value": "Bearer {{token}}"
              }
            ],
            "url": {
              "raw": "{{base_url}}/api/v1/engineers/my-projects?page=1&page_size=10",
              "host": ["{{base_url}}"],
              "path": ["api", "v1", "engineers", "my-projects"],
              "query": [
                {"key": "page", "value": "1"},
                {"key": "page_size", "value": "10"}
              ]
            }
          }
        }
      ]
    }
  ],
  "variable": [
    {
      "key": "base_url",
      "value": "http://localhost:8000"
    },
    {
      "key": "token",
      "value": "YOUR_TOKEN_HERE"
    }
  ]
}
```

### cURL测试脚本

```bash
#!/bin/bash
# test_api.sh

BASE_URL="http://localhost:8000"
TOKEN="YOUR_TOKEN_HERE"

# 1. 获取我的项目列表
echo "=== 测试1: 获取我的项目列表 ==="
curl -X GET "$BASE_URL/api/v1/engineers/my-projects" \
  -H "Authorization: Bearer $TOKEN" | jq

# 2. 创建任务
echo -e "\n=== 测试2: 创建任务 ==="
TASK_ID=$(curl -X POST "$BASE_URL/api/v1/engineers/tasks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "title": "测试任务",
    "task_importance": "GENERAL",
    "priority": "MEDIUM"
  }' | jq -r '.id')

echo "创建的任务ID: $TASK_ID"

# 3. 更新进度
echo -e "\n=== 测试3: 更新进度 ==="
curl -X PUT "$BASE_URL/api/v1/engineers/tasks/$TASK_ID/progress" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "progress": 50,
    "actual_hours": 10,
    "progress_note": "进行中"
  }' | jq
```

---

**文档版本：** 1.0.0
**最后更新：** 2026-01-07
**维护者：** 开发团队
