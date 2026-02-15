# 质量风险识别系统 API 文档

## API 基础信息

- **Base URL**: `/api/v1/quality-risk`
- **认证方式**: Bearer Token
- **响应格式**: JSON

## API 端点列表

### 1. 质量风险检测

#### 1.1 分析工作日志

**端点**: `POST /detections/analyze`

**描述**: 分析指定时间段的工作日志，自动检测质量风险。

**请求参数**:

```json
{
  "project_id": 1,
  "start_date": "2026-02-01",
  "end_date": "2026-02-15",
  "module_name": "登录模块",
  "user_ids": [10, 20]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | integer | 是 | 项目ID |
| start_date | string(date) | 否 | 开始日期（默认最近7天） |
| end_date | string(date) | 否 | 结束日期（默认今天） |
| module_name | string | 否 | 模块名称（筛选） |
| user_ids | array[integer] | 否 | 用户ID列表（筛选） |

**响应示例**:

```json
{
  "id": 1,
  "project_id": 1,
  "module_name": "登录模块",
  "detection_date": "2026-02-15",
  "source_type": "WORK_LOG",
  "risk_level": "HIGH",
  "risk_score": 65.5,
  "risk_category": "BUG",
  "risk_signals": [
    {
      "date": "2026-02-14",
      "user": "张三",
      "module": "登录模块",
      "risk_score": 70,
      "keywords": {"BUG": ["bug", "错误"]}
    }
  ],
  "risk_keywords": {
    "BUG": ["bug", "错误", "缺陷"],
    "PERFORMANCE": ["慢"]
  },
  "abnormal_patterns": [
    {
      "name": "频繁修复",
      "severity": "HIGH",
      "matches": ["修复了bug"],
      "count": 1
    }
  ],
  "predicted_issues": [
    {
      "issue": "登录功能可能存在缺陷",
      "probability": 75,
      "impact": "影响用户登录",
      "suggested_action": "加强测试"
    }
  ],
  "rework_probability": 60.0,
  "estimated_impact_days": 3,
  "ai_analysis": {
    "method": "GLM_BASED",
    "reasoning": "...",
    "model": "glm-4-flash"
  },
  "ai_confidence": 85.0,
  "analysis_model": "glm-4-flash",
  "status": "DETECTED",
  "created_at": "2026-02-15T10:30:00",
  "updated_at": "2026-02-15T10:30:00"
}
```

**错误响应**:

- `404 Not Found`: 未找到符合条件的工作日志
- `422 Unprocessable Entity`: 请求参数验证失败
- `500 Internal Server Error`: 分析失败

---

#### 1.2 查询检测记录列表

**端点**: `GET /detections`

**描述**: 查询质量风险检测记录列表。

**Query参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | integer | 否 | 项目ID |
| risk_level | string | 否 | 风险等级（LOW/MEDIUM/HIGH/CRITICAL） |
| status | string | 否 | 状态（DETECTED/CONFIRMED/FALSE_POSITIVE/RESOLVED） |
| start_date | string(date) | 否 | 开始日期 |
| end_date | string(date) | 否 | 结束日期 |
| skip | integer | 否 | 跳过记录数（默认0） |
| limit | integer | 否 | 返回记录数（默认20，最大100） |

**响应示例**:

```json
[
  {
    "id": 1,
    "project_id": 1,
    "module_name": "登录模块",
    "risk_level": "HIGH",
    "risk_score": 65.5,
    "detection_date": "2026-02-15",
    "status": "DETECTED",
    ...
  },
  {
    "id": 2,
    "project_id": 1,
    "module_name": "支付模块",
    "risk_level": "MEDIUM",
    "risk_score": 45.0,
    "detection_date": "2026-02-14",
    "status": "CONFIRMED",
    ...
  }
]
```

---

#### 1.3 获取检测详情

**端点**: `GET /detections/{detection_id}`

**描述**: 获取单条质量风险检测记录的详细信息。

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| detection_id | integer | 检测记录ID |

**响应**: 同 1.1 分析工作日志的响应格式

**错误响应**:

- `404 Not Found`: 检测记录不存在

---

#### 1.4 更新检测状态

**端点**: `PATCH /detections/{detection_id}`

**描述**: 更新质量风险检测的状态（确认、标记为误报、解决）。

**请求参数**:

```json
{
  "status": "CONFIRMED",
  "resolution_note": "已确认为真实风险，需要重点关注"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态（CONFIRMED/FALSE_POSITIVE/RESOLVED） |
| resolution_note | string | 否 | 处理说明 |

**响应**: 更新后的检测记录

---

### 2. 测试推荐

#### 2.1 生成测试推荐

**端点**: `POST /recommendations/generate`

**描述**: 基于质量风险检测结果，生成智能测试推荐。

**Query参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| detection_id | integer | 是 | 质量风险检测ID |

**响应示例**:

```json
{
  "id": 1,
  "project_id": 1,
  "detection_id": 1,
  "recommendation_date": "2026-02-15",
  "priority_level": "HIGH",
  "focus_areas": [
    {
      "area": "登录模块",
      "reason": "检测到质量风险信号",
      "risk_score": 70,
      "priority": "HIGH"
    },
    {
      "area": "支付模块",
      "reason": "检测到质量风险信号",
      "risk_score": 60,
      "priority": "MEDIUM"
    }
  ],
  "priority_modules": ["登录模块", "支付模块"],
  "risk_modules": [
    {
      "module": "登录模块",
      "risk_score": 70,
      "date": "2026-02-14",
      "user": "张三"
    }
  ],
  "test_types": ["功能测试", "回归测试", "集成测试"],
  "test_scenarios": [
    {
      "scenario": "登录功能可能存在缺陷",
      "description": "影响用户登录",
      "priority": "HIGH",
      "suggested_action": "加强测试"
    }
  ],
  "test_coverage_target": 85.0,
  "recommended_testers": 2,
  "recommended_days": 5,
  "ai_reasoning": "基于AI分析，当前质量风险等级为 HIGH，风险评分 65.5/100。识别出 2 个测试重点区域，建议优先关注。预测到 1 个高概率问题，需要重点测试验证。",
  "risk_summary": "风险等级: HIGH, 类别: BUG, 返工概率: 60%\n检测到的风险关键词: BUG(3), PERFORMANCE(1)",
  "status": "PENDING",
  "created_at": "2026-02-15T10:35:00",
  "updated_at": "2026-02-15T10:35:00"
}
```

**错误响应**:

- `404 Not Found`: 质量风险检测记录不存在

---

#### 2.2 查询推荐列表

**端点**: `GET /recommendations`

**描述**: 查询测试推荐列表。

**Query参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | integer | 否 | 项目ID |
| priority_level | string | 否 | 优先级（LOW/MEDIUM/HIGH/URGENT） |
| status | string | 否 | 状态（PENDING/ACCEPTED/IN_PROGRESS/COMPLETED/REJECTED） |
| skip | integer | 否 | 跳过记录数（默认0） |
| limit | integer | 否 | 返回记录数（默认20） |

**响应**: 推荐记录列表

---

#### 2.3 更新推荐

**端点**: `PATCH /recommendations/{recommendation_id}`

**描述**: 更新测试推荐（接受、拒绝、完成、评估效果）。

**请求参数**:

```json
{
  "status": "COMPLETED",
  "acceptance_note": "已接受推荐并完成测试",
  "actual_test_days": 5,
  "actual_coverage": 87.5,
  "bugs_found": 12,
  "critical_bugs_found": 3,
  "recommendation_accuracy": 85.0
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 状态 |
| acceptance_note | string | 否 | 接受/拒绝说明 |
| actual_test_days | integer | 否 | 实际测试天数 |
| actual_coverage | float | 否 | 实际测试覆盖率 |
| bugs_found | integer | 否 | 发现的BUG数量 |
| critical_bugs_found | integer | 否 | 发现的严重BUG数量 |
| recommendation_accuracy | float | 否 | 推荐准确度评分 |

**响应**: 更新后的推荐记录

---

### 3. 质量报告

#### 3.1 生成质量报告

**端点**: `POST /reports/generate`

**描述**: 生成项目质量分析报告，包含风险趋势、推荐建议等。

**请求参数**:

```json
{
  "project_id": 1,
  "start_date": "2026-01-01",
  "end_date": "2026-02-15",
  "include_recommendations": true
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | integer | 是 | 项目ID |
| start_date | string(date) | 是 | 开始日期 |
| end_date | string(date) | 是 | 结束日期 |
| include_recommendations | boolean | 否 | 是否包含测试推荐（默认true） |

**响应示例**:

```json
{
  "project_id": 1,
  "project_name": "项目 1",
  "report_period": "2026-01-01 至 2026-02-15",
  "overall_risk_level": "HIGH",
  "total_detections": 15,
  "risk_distribution": {
    "LOW": 3,
    "MEDIUM": 7,
    "HIGH": 4,
    "CRITICAL": 1
  },
  "top_risk_modules": [
    {
      "module": "登录模块",
      "risk_score": 75.0,
      "risk_level": "HIGH",
      "detection_date": "2026-02-15"
    },
    {
      "module": "支付模块",
      "risk_score": 68.0,
      "risk_level": "HIGH",
      "detection_date": "2026-02-14"
    }
  ],
  "trend_analysis": {
    "2026-02-01": {"count": 1, "avg_score": 45.0},
    "2026-02-05": {"count": 2, "avg_score": 52.5},
    "2026-02-10": {"count": 3, "avg_score": 60.0},
    "2026-02-15": {"count": 4, "avg_score": 68.0}
  },
  "recommendations": [
    {
      "id": 1,
      "priority": "HIGH",
      "status": "PENDING",
      "recommended_days": 5,
      "ai_reasoning": "..."
    }
  ],
  "summary": "在2026-01-01至2026-02-15期间，共检测到15个质量风险，总体风险等级为HIGH。其中包含1个严重风险，需立即关注。",
  "generated_at": "2026-02-15T11:00:00"
}
```

**错误响应**:

- `404 Not Found`: 指定时间段内没有质量风险检测数据
- `422 Unprocessable Entity`: 请求参数验证失败

---

### 4. 统计分析

#### 4.1 获取统计摘要

**端点**: `GET /statistics/summary`

**描述**: 获取质量风险统计摘要。

**Query参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | integer | 否 | 项目ID（不填则全部项目） |
| days | integer | 否 | 统计天数（默认30，最大365） |

**响应示例**:

```json
{
  "total_detections": 25,
  "average_risk_score": 52.3,
  "by_risk_level": {
    "LOW": 8,
    "MEDIUM": 10,
    "HIGH": 6,
    "CRITICAL": 1
  },
  "by_status": {
    "DETECTED": 10,
    "CONFIRMED": 8,
    "FALSE_POSITIVE": 3,
    "RESOLVED": 4
  },
  "period_days": 30,
  "start_date": "2026-01-16",
  "end_date": "2026-02-15"
}
```

---

## 通用响应格式

### 成功响应

所有成功的API请求返回HTTP状态码`200 OK`，响应体为JSON格式的数据。

### 错误响应

错误响应包含HTTP状态码和错误详情：

```json
{
  "detail": "错误描述信息"
}
```

**常见错误码**:

| 状态码 | 说明 |
|--------|------|
| 400 | Bad Request - 请求格式错误 |
| 401 | Unauthorized - 未认证 |
| 403 | Forbidden - 无权限 |
| 404 | Not Found - 资源不存在 |
| 422 | Unprocessable Entity - 请求参数验证失败 |
| 500 | Internal Server Error - 服务器内部错误 |

---

## 认证方式

所有API请求需要在HTTP头中携带认证令牌：

```
Authorization: Bearer <your_access_token>
```

---

## 速率限制

- 每个用户每分钟最多100次请求
- 超出限制返回`429 Too Many Requests`

---

## 版本信息

- **当前版本**: v1
- **最后更新**: 2026-02-15
- **兼容性**: 需要FastAPI 0.104+, Python 3.9+

---

**维护者**: AI Team 3  
**联系方式**: team3@example.com
