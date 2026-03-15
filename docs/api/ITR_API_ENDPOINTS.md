# ITR API 端点清单

**文件位置**: `app/api/v1/endpoints/itr.py`  
**路由前缀**: `/api/v1/itr`  
**Tags**: `itr`

---

## 端点总览

| 方法 | 端点 | 描述 | 认证 |
|------|------|------|------|
| GET | `/tickets/{ticket_id}/timeline` | 获取工单完整时间线 | ✅ |
| GET | `/issues/{issue_id}/related` | 获取问题关联数据 | ✅ |
| GET | `/dashboard` | 获取 ITR 流程看板数据 | ✅ |
| GET | `/analytics/efficiency` | 获取 ITR 流程效率分析 | ✅ |
| GET | `/analytics/satisfaction` | 获取客户满意度趋势分析 | ✅ |
| GET | `/analytics/bottlenecks` | 获取流程瓶颈识别 | ✅ |
| GET | `/analytics/sla` | 获取 SLA 达成率分析 | ✅ |

---

## 详细端点说明

### 1. GET `/tickets/{ticket_id}/timeline`

**描述**: 获取工单完整时间线，整合工单、问题、验收、SLA 监控等数据

**路径参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `ticket_id` | `int` | ✅ | 工单 ID |

**查询参数**: 无

**响应**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "ticket": {...},
    "issues": [...],
    "acceptance": {...},
    "sla_monitoring": {...},
    "timeline": [...]
  }
}
```

**错误响应**:
- `404`: 工单不存在

---

### 2. GET `/issues/{issue_id}/related`

**描述**: 获取问题关联数据（工单、验收单等）

**路径参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `issue_id` | `int` | ✅ | 问题 ID |

**查询参数**: 无

**响应**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "issue": {...},
    "related_tickets": [...],
    "related_acceptance": [...]
  }
}
```

**错误响应**:
- `404`: 问题不存在

---

### 3. GET `/dashboard`

**描述**: 获取 ITR 流程看板数据

**路径参数**: 无

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `project_id` | `int` | ❌ | 项目 ID 筛选 |
| `start_date` | `str` | ❌ | 开始日期（YYYY-MM-DD） |
| `end_date` | `str` | ❌ | 结束日期（YYYY-MM-DD） |

**响应**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "overview": {...},
    "ticket_stats": {...},
    "issue_stats": {...},
    "sla_stats": {...}
  }
}
```

**错误响应**:
- `400`: 日期格式错误

---

### 4. GET `/analytics/efficiency`

**描述**: 获取 ITR 流程效率分析（包含问题解决时间分析、流程瓶颈识别）

**路径参数**: 无

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `project_id` | `int` | ❌ | 项目 ID 筛选 |
| `start_date` | `str` | ❌ | 开始日期（YYYY-MM-DD） |
| `end_date` | `str` | ❌ | 结束日期（YYYY-MM-DD） |

**响应**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "resolution_time": {...},
    "bottlenecks": {...}
  }
}
```

**错误响应**:
- `400`: 日期格式错误

---

### 5. GET `/analytics/satisfaction`

**描述**: 获取客户满意度趋势分析

**路径参数**: 无

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `project_id` | `int` | ❌ | 项目 ID 筛选 |
| `start_date` | `str` | ❌ | 开始日期（YYYY-MM-DD） |
| `end_date` | `str` | ❌ | 结束日期（YYYY-MM-DD） |

**响应**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "satisfaction_trend": [...],
    "average_score": 0.0,
    "total_feedbacks": 0
  }
}
```

**错误响应**:
- `400`: 日期格式错误

---

### 6. GET `/analytics/bottlenecks`

**描述**: 获取流程瓶颈识别

**路径参数**: 无

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `start_date` | `str` | ❌ | 开始日期（YYYY-MM-DD） |
| `end_date` | `str` | ❌ | 结束日期（YYYY-MM-DD） |

**响应**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "bottlenecks": [...],
    "avg_resolution_time": 0.0,
    "slowest_stages": [...]
  }
}
```

**错误响应**:
- `400`: 日期格式错误

---

### 7. GET `/analytics/sla`

**描述**: 获取 SLA 达成率分析

**路径参数**: 无

**查询参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `policy_id` | `int` | ❌ | 策略 ID 筛选 |
| `start_date` | `str` | ❌ | 开始日期（YYYY-MM-DD） |
| `end_date` | `str` | ❌ | 结束日期（YYYY-MM-DD） |

**响应**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "sla_compliance_rate": 0.0,
    "breach_count": 0,
    "policy_performance": [...]
  }
}
```

**错误响应**:
- `400`: 日期格式错误

---

## 依赖服务

- `app.services.itr_service`
  - `get_ticket_timeline(db, ticket_id)`
  - `get_issue_related_data(db, issue_id)`
  - `get_itr_dashboard_data(db, project_id, start_date, end_date)`

- `app.services.itr_analytics_service`
  - `analyze_resolution_time(db, start_date, end_date, project_id)`
  - `identify_bottlenecks(db, start_date, end_date)`
  - `analyze_satisfaction_trend(db, start_date, end_date, project_id)`
  - `analyze_sla_performance(db, start_date, end_date, policy_id)`

## 认证要求

所有端点均需通过 `security.get_current_active_user` 进行身份验证。

## Schema 定义

所有响应均使用 `ResponseModel` 统一格式:
```python
class ResponseModel(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None
```
