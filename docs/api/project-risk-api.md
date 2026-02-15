# 项目风险管理 API 文档

## 基本信息

- **基础URL**: `/api/v1`
- **认证方式**: Bearer Token
- **内容类型**: `application/json`

## API端点列表

### 1. 创建风险

创建项目风险记录。系统自动生成风险编号，自动计算风险评分和等级。

**端点**: `POST /projects/{project_id}/risks`

**权限**: `risk:create`

**路径参数**:
- `project_id` (integer, 必填): 项目ID

**请求体**:
```json
{
  "risk_name": "string (必填, 1-200字符)",
  "description": "string (可选)",
  "risk_type": "string (必填, TECHNICAL|COST|SCHEDULE|QUALITY)",
  "probability": "integer (必填, 1-5)",
  "impact": "integer (必填, 1-5)",
  "mitigation_plan": "string (可选)",
  "contingency_plan": "string (可选)",
  "owner_id": "integer (可选)",
  "target_closure_date": "datetime (可选, ISO 8601格式)"
}
```

**响应**: `200 OK`
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
    "identified_date": "2026-02-14T18:00:00",
    "target_closure_date": "2026-03-01T00:00:00",
    "is_occurred": false,
    "created_by_id": 1,
    "created_by_name": "管理员",
    "created_at": "2026-02-14T18:00:00",
    "updated_at": "2026-02-14T18:00:00"
  }
}
```

**错误响应**:
- `404 Not Found`: 项目不存在
- `422 Unprocessable Entity`: 请求数据验证失败
- `403 Forbidden`: 无权限

---

### 2. 获取风险列表

获取项目的风险列表，支持多种筛选条件和分页。

**端点**: `GET /projects/{project_id}/risks`

**权限**: `risk:read`

**路径参数**:
- `project_id` (integer, 必填): 项目ID

**查询参数**:
- `risk_type` (string, 可选): 风险类型筛选 (TECHNICAL|COST|SCHEDULE|QUALITY)
- `risk_level` (string, 可选): 风险等级筛选 (LOW|MEDIUM|HIGH|CRITICAL)
- `status` (string, 可选): 状态筛选
- `owner_id` (integer, 可选): 负责人ID筛选
- `is_occurred` (boolean, 可选): 是否已发生
- `offset` (integer, 可选, 默认0): 分页偏移量
- `limit` (integer, 可选, 默认20): 每页数量

**响应**: `200 OK`
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
        "project_id": 1,
        "risk_name": "技术风险-新算法实现",
        "description": "新的视觉识别算法可能存在性能问题",
        "risk_type": "TECHNICAL",
        "probability": 4,
        "impact": 5,
        "risk_score": 20,
        "risk_level": "CRITICAL",
        "status": "MONITORING",
        "owner_name": "张三",
        "is_occurred": false,
        "created_at": "2026-02-14T18:00:00"
      }
    ]
  }
}
```

**错误响应**:
- `404 Not Found`: 项目不存在
- `403 Forbidden`: 无权限

---

### 3. 获取风险详情

获取单个风险的详细信息。

**端点**: `GET /projects/{project_id}/risks/{risk_id}`

**权限**: `risk:read`

**路径参数**:
- `project_id` (integer, 必填): 项目ID
- `risk_id` (integer, 必填): 风险ID

**响应**: `200 OK`
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
    "actual_closure_date": null,
    "is_occurred": false,
    "occurrence_date": null,
    "actual_impact": null,
    "created_by_id": 1,
    "created_by_name": "管理员",
    "updated_by_id": 1,
    "updated_by_name": "管理员",
    "created_at": "2026-02-14T18:00:00",
    "updated_at": "2026-02-14T19:00:00"
  }
}
```

**错误响应**:
- `404 Not Found`: 项目或风险不存在
- `403 Forbidden`: 无权限

---

### 4. 更新风险

更新风险信息。如果更新概率或影响，系统会自动重新计算风险评分和等级。

**端点**: `PUT /projects/{project_id}/risks/{risk_id}`

**权限**: `risk:update`

**路径参数**:
- `project_id` (integer, 必填): 项目ID
- `risk_id` (integer, 必填): 风险ID

**请求体** (所有字段均为可选):
```json
{
  "risk_name": "string (1-200字符)",
  "description": "string",
  "risk_type": "string (TECHNICAL|COST|SCHEDULE|QUALITY)",
  "probability": "integer (1-5)",
  "impact": "integer (1-5)",
  "mitigation_plan": "string",
  "contingency_plan": "string",
  "owner_id": "integer",
  "status": "string (IDENTIFIED|ANALYZING|PLANNING|MONITORING|MITIGATED|OCCURRED|CLOSED)",
  "target_closure_date": "datetime (ISO 8601格式)",
  "is_occurred": "boolean",
  "occurrence_date": "datetime (ISO 8601格式)",
  "actual_impact": "string",
  "actual_closure_date": "datetime (ISO 8601格式)"
}
```

**响应**: `200 OK`
```json
{
  "code": 200,
  "message": "风险更新成功",
  "data": {
    "id": 1,
    "risk_name": "技术风险-算法性能优化",
    "probability": 3,
    "impact": 4,
    "risk_score": 12,
    "risk_level": "HIGH",
    "status": "MITIGATED",
    "updated_by_id": 1,
    "updated_by_name": "管理员",
    "updated_at": "2026-02-14T20:00:00"
  }
}
```

**错误响应**:
- `404 Not Found`: 项目或风险不存在
- `422 Unprocessable Entity`: 请求数据验证失败
- `403 Forbidden`: 无权限

**特殊行为**:
- 当状态更新为 `CLOSED` 且 `actual_closure_date` 为空时，系统会自动设置当前时间
- 更新 `probability` 或 `impact` 时，系统会自动重新计算 `risk_score` 和 `risk_level`
- 更新 `owner_id` 时，系统会自动设置 `owner_name`

---

### 5. 删除风险

删除风险记录。此操作不可恢复，请谨慎使用。

**端点**: `DELETE /projects/{project_id}/risks/{risk_id}`

**权限**: `risk:delete`

**路径参数**:
- `project_id` (integer, 必填): 项目ID
- `risk_id` (integer, 必填): 风险ID

**响应**: `200 OK`
```json
{
  "code": 200,
  "message": "风险删除成功",
  "data": null
}
```

**错误响应**:
- `404 Not Found`: 项目或风险不存在
- `403 Forbidden`: 无权限

---

### 6. 获取风险矩阵

获取项目的风险矩阵，展示5×5网格中每个单元格的风险分布。

**端点**: `GET /projects/{project_id}/risk-matrix`

**权限**: `risk:read`

**路径参数**:
- `project_id` (integer, 必填): 项目ID

**响应**: `200 OK`
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

**说明**:
- `matrix` 数组包含25个元素（5×5）
- 每个元素表示一个矩阵单元格
- 只包含未关闭的风险（`status != CLOSED`）

**错误响应**:
- `404 Not Found`: 项目不存在
- `403 Forbidden`: 无权限

---

### 7. 获取风险汇总统计

获取项目的风险汇总统计信息，包括按类型、等级、状态的分组统计。

**端点**: `GET /projects/{project_id}/risk-summary`

**权限**: `risk:read`

**路径参数**:
- `project_id` (integer, 必填): 项目ID

**响应**: `200 OK`
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

**字段说明**:
- `total_risks`: 项目总风险数（包含所有状态）
- `by_type`: 按风险类型分组统计
- `by_level`: 按风险等级分组统计
- `by_status`: 按风险状态分组统计
- `occurred_count`: 已发生的风险数量
- `closed_count`: 已关闭的风险数量
- `high_priority_count`: 高优先级风险数量（HIGH + CRITICAL）
- `avg_risk_score`: 平均风险评分

**错误响应**:
- `404 Not Found`: 项目不存在
- `403 Forbidden`: 无权限

---

## 枚举类型

### 风险类型 (RiskType)
- `TECHNICAL`: 技术风险
- `COST`: 成本风险
- `SCHEDULE`: 进度风险
- `QUALITY`: 质量风险

### 风险状态 (RiskStatus)
- `IDENTIFIED`: 已识别
- `ANALYZING`: 分析中
- `PLANNING`: 规划应对中
- `MONITORING`: 监控中
- `MITIGATED`: 已缓解
- `OCCURRED`: 已发生
- `CLOSED`: 已关闭

### 风险等级 (RiskLevel)
- `LOW`: 低风险 (评分1-4)
- `MEDIUM`: 中风险 (评分5-9)
- `HIGH`: 高风险 (评分10-15)
- `CRITICAL`: 极高风险 (评分16-25)

## 权限说明

| 权限代码 | 权限名称 | 说明 |
|---------|---------|------|
| `risk:create` | 创建风险 | 允许创建项目风险 |
| `risk:read` | 查看风险 | 允许查看风险列表、详情和分析数据 |
| `risk:update` | 更新风险 | 允许更新风险信息 |
| `risk:delete` | 删除风险 | 允许删除风险 |

## 审计日志

所有风险的创建、更新、删除操作都会记录审计日志，包含以下信息：
- 操作用户
- 操作时间
- 操作类型 (CREATE/UPDATE/DELETE)
- 资源类型 (project_risk)
- 资源ID
- 操作详情（变更前后对比）

## 错误代码

| HTTP状态码 | 说明 |
|-----------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 422 | 请求数据验证失败 |
| 500 | 服务器内部错误 |

## 示例代码

### Python 示例

```python
import requests

BASE_URL = "http://api.example.com/api/v1"
TOKEN = "your_access_token"

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

# 创建风险
def create_risk(project_id, risk_data):
    url = f"{BASE_URL}/projects/{project_id}/risks"
    response = requests.post(url, json=risk_data, headers=headers)
    return response.json()

# 获取风险列表
def get_risks(project_id, **filters):
    url = f"{BASE_URL}/projects/{project_id}/risks"
    response = requests.get(url, params=filters, headers=headers)
    return response.json()

# 更新风险
def update_risk(project_id, risk_id, update_data):
    url = f"{BASE_URL}/projects/{project_id}/risks/{risk_id}"
    response = requests.put(url, json=update_data, headers=headers)
    return response.json()

# 获取风险矩阵
def get_risk_matrix(project_id):
    url = f"{BASE_URL}/projects/{project_id}/risk-matrix"
    response = requests.get(url, headers=headers)
    return response.json()

# 获取风险汇总
def get_risk_summary(project_id):
    url = f"{BASE_URL}/projects/{project_id}/risk-summary"
    response = requests.get(url, headers=headers)
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 创建技术风险
    risk = create_risk(1, {
        "risk_name": "API性能问题",
        "description": "高并发下API响应时间可能超标",
        "risk_type": "TECHNICAL",
        "probability": 3,
        "impact": 4,
        "mitigation_plan": "进行性能测试和优化"
    })
    print(f"创建风险: {risk['data']['risk_code']}")
    
    # 获取高风险列表
    high_risks = get_risks(1, risk_level="HIGH")
    print(f"高风险数量: {high_risks['data']['total']}")
    
    # 获取风险汇总
    summary = get_risk_summary(1)
    print(f"平均风险评分: {summary['data']['avg_risk_score']}")
```

### JavaScript 示例

```javascript
const BASE_URL = 'http://api.example.com/api/v1';
const TOKEN = 'your_access_token';

const headers = {
  'Authorization': `Bearer ${TOKEN}`,
  'Content-Type': 'application/json'
};

// 创建风险
async function createRisk(projectId, riskData) {
  const response = await fetch(`${BASE_URL}/projects/${projectId}/risks`, {
    method: 'POST',
    headers,
    body: JSON.stringify(riskData)
  });
  return response.json();
}

// 获取风险列表
async function getRisks(projectId, filters = {}) {
  const params = new URLSearchParams(filters);
  const response = await fetch(`${BASE_URL}/projects/${projectId}/risks?${params}`, {
    headers
  });
  return response.json();
}

// 更新风险
async function updateRisk(projectId, riskId, updateData) {
  const response = await fetch(`${BASE_URL}/projects/${projectId}/risks/${riskId}`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(updateData)
  });
  return response.json();
}

// 使用示例
(async () => {
  // 创建成本风险
  const risk = await createRisk(1, {
    risk_name: '原材料价格上涨',
    risk_type: 'COST',
    probability: 4,
    impact: 3,
    mitigation_plan: '提前锁定价格'
  });
  console.log('创建风险:', risk.data.risk_code);
  
  // 获取极高风险
  const criticalRisks = await getRisks(1, { risk_level: 'CRITICAL' });
  console.log('极高风险数量:', criticalRisks.data.total);
})();
```

## 版本历史

- **v1.0.0** (2026-02-14) - 初始版本
