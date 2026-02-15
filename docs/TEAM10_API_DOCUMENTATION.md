# Team 10: 售前AI系统集成 - API完整文档

## 📋 概述

本文档详细描述了售前AI系统集成的所有API端点，包括请求参数、响应格式和使用示例。

**基础URL**: `/api/v1/presale/ai`

**认证方式**: Bearer Token (JWT)

---

## 🎯 API端点列表

### 1. 获取AI仪表盘统计

获取AI系统整体运行统计数据。

**端点**: `GET /dashboard/stats`

**查询参数**:
- `days` (int, 可选): 统计天数，默认30天，范围1-365

**响应示例**:
```json
{
  "total_usage": 1250,
  "total_success": 1180,
  "success_rate": 94.4,
  "avg_response_time": 523.5,
  "top_functions": [
    {
      "function": "requirement",
      "usage_count": 450,
      "success_count": 430,
      "success_rate": 95.6
    }
  ],
  "usage_trend": [
    {
      "date": "2026-02-01",
      "count": 45
    }
  ],
  "user_stats": {
    "active_users": 28
  }
}
```

**使用示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/presale/ai/dashboard/stats?days=30" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 2. 获取AI使用统计

获取详细的AI功能使用统计数据。

**端点**: `GET /usage-stats`

**查询参数**:
- `start_date` (date, 可选): 开始日期 (YYYY-MM-DD)
- `end_date` (date, 可选): 结束日期 (YYYY-MM-DD)
- `ai_functions` (list[str], 可选): AI功能列表
- `user_ids` (list[int], 可选): 用户ID列表

**响应示例**:
```json
[
  {
    "id": 1,
    "user_id": 10,
    "ai_function": "requirement",
    "usage_count": 25,
    "success_count": 24,
    "avg_response_time": 450,
    "date": "2026-02-15",
    "created_at": "2026-02-15T10:00:00",
    "updated_at": "2026-02-15T18:00:00"
  }
]
```

---

### 3. 提交AI反馈

提交AI功能使用反馈。

**端点**: `POST /feedback`

**请求体**:
```json
{
  "ai_function": "requirement",
  "presale_ticket_id": 123,
  "rating": 5,
  "feedback_text": "功能非常好用，响应速度快"
}
```

**字段说明**:
- `ai_function` (str, 必填): AI功能名称
- `presale_ticket_id` (int, 可选): 关联售前工单ID
- `rating` (int, 必填): 评分1-5星
- `feedback_text` (str, 可选): 详细反馈文本

**响应示例**:
```json
{
  "id": 1,
  "user_id": 10,
  "ai_function": "requirement",
  "presale_ticket_id": 123,
  "rating": 5,
  "feedback_text": "功能非常好用，响应速度快",
  "created_at": "2026-02-15T10:00:00",
  "updated_at": "2026-02-15T10:00:00"
}
```

---

### 4. 获取指定功能的反馈

获取指定AI功能的用户反馈列表。

**端点**: `GET /feedback/{function}`

**路径参数**:
- `function` (str): AI功能名称

**查询参数**:
- `min_rating` (int, 可选): 最低评分 (1-5)
- `max_rating` (int, 可选): 最高评分 (1-5)
- `start_date` (date, 可选): 开始日期
- `end_date` (date, 可选): 结束日期
- `limit` (int, 可选): 返回数量，默认100
- `offset` (int, 可选): 偏移量，默认0

---

### 5. 启动AI工作流

启动完整的AI售前工作流。

**端点**: `POST /workflow/start`

**请求体**:
```json
{
  "presale_ticket_id": 123,
  "initial_data": {
    "customer_name": "ABC公司",
    "requirement_desc": "需要一套ERP系统"
  },
  "auto_run": true
}
```

**字段说明**:
- `presale_ticket_id` (int, 必填): 售前工单ID
- `initial_data` (object, 可选): 初始数据
- `auto_run` (bool, 可选): 是否自动运行所有步骤，默认true

**响应示例**:
```json
[
  {
    "id": 1,
    "presale_ticket_id": 123,
    "workflow_step": "requirement",
    "status": "running",
    "input_data": {...},
    "output_data": null,
    "error_message": null,
    "started_at": "2026-02-15T10:00:00",
    "completed_at": null,
    "created_at": "2026-02-15T10:00:00"
  },
  {
    "id": 2,
    "presale_ticket_id": 123,
    "workflow_step": "solution",
    "status": "pending",
    ...
  }
]
```

**工作流步骤**:
1. `requirement` - 需求理解
2. `solution` - 方案生成
3. `cost` - 成本估算
4. `winrate` - 赢率预测
5. `quotation` - 报价生成

---

### 6. 获取工作流状态

获取指定工单的AI工作流执行状态。

**端点**: `GET /workflow/status/{ticket_id}`

**路径参数**:
- `ticket_id` (int): 售前工单ID

**响应示例**:
```json
{
  "presale_ticket_id": 123,
  "current_step": "solution",
  "overall_status": "running",
  "steps": [...],
  "progress": 40.0,
  "estimated_completion": "2026-02-15T11:00:00"
}
```

**状态说明**:
- `pending`: 待处理
- `running`: 进行中
- `success`: 成功
- `failed`: 失败
- `completed`: 已完成

---

### 7. 批量AI处理

批量处理多个工单的指定AI功能。

**端点**: `POST /batch-process`

**请求体**:
```json
{
  "ticket_ids": [123, 124, 125],
  "ai_function": "requirement",
  "options": {
    "priority": "high"
  }
}
```

**响应示例**:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_count": 3,
  "status": "started",
  "started_at": "2026-02-15T10:00:00"
}
```

---

### 8. AI服务健康检查

检查AI服务各模块的健康状态。

**端点**: `GET /health-check`

**响应示例**:
```json
{
  "status": "healthy",
  "services": {
    "database": {
      "status": "healthy",
      "message": "Connected"
    },
    "ai_functions": {
      "status": "healthy",
      "enabled_count": 9,
      "total_count": 9
    },
    "recent_activity": {
      "status": "healthy",
      "usage_count_24h": 145
    }
  },
  "timestamp": "2026-02-15T10:00:00"
}
```

**状态等级**:
- `healthy`: 健康
- `degraded`: 降级运行
- `unhealthy`: 不健康

---

### 9. 更新AI配置

更新指定AI功能的配置参数。

**端点**: `POST /config/update`

**查询参数**:
- `ai_function` (str): AI功能名称

**请求体**:
```json
{
  "enabled": true,
  "model_name": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000,
  "timeout_seconds": 30,
  "config_json": {
    "custom_param": "value"
  }
}
```

**响应示例**:
```json
{
  "id": 1,
  "ai_function": "requirement",
  "enabled": true,
  "model_name": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000,
  "timeout_seconds": 30,
  "config_json": {...},
  "created_at": "2026-02-15T10:00:00",
  "updated_at": "2026-02-15T10:00:00"
}
```

---

### 10. 获取所有AI配置

获取所有AI功能的配置列表。

**端点**: `GET /config`

**响应示例**:
```json
[
  {
    "id": 1,
    "ai_function": "requirement",
    "enabled": true,
    "model_name": "gpt-4",
    ...
  },
  {
    "id": 2,
    "ai_function": "solution",
    "enabled": true,
    ...
  }
]
```

---

### 11. 获取操作审计日志

获取AI系统操作审计日志。

**端点**: `GET /audit-log`

**查询参数**:
- `user_id` (int, 可选): 用户ID
- `action` (str, 可选): 操作类型
- `start_date` (date, 可选): 开始日期
- `end_date` (date, 可选): 结束日期
- `limit` (int, 可选): 返回数量，默认100
- `offset` (int, 可选): 偏移量，默认0

**响应示例**:
```json
[
  {
    "id": 1,
    "user_id": 10,
    "action": "start_workflow",
    "ai_function": null,
    "resource_type": "workflow",
    "resource_id": 123,
    "details": {...},
    "ip_address": "192.168.1.100",
    "user_agent": "Mozilla/5.0...",
    "created_at": "2026-02-15T10:00:00"
  }
]
```

**常见操作类型**:
- `start_workflow`: 启动工作流
- `update_config`: 更新配置
- `submit_feedback`: 提交反馈
- `batch_process`: 批量处理
- `export_report`: 导出报告

---

### 12. 导出AI使用报告

导出指定时间范围的AI使用报告。

**端点**: `POST /export-report`

**请求体**:
```json
{
  "start_date": "2026-02-01",
  "end_date": "2026-02-15",
  "ai_functions": ["requirement", "solution"],
  "user_ids": [10, 20],
  "format": "excel"
}
```

**字段说明**:
- `start_date` (date, 必填): 开始日期
- `end_date` (date, 必填): 结束日期
- `ai_functions` (list[str], 可选): AI功能列表
- `user_ids` (list[int], 可选): 用户ID列表
- `format` (str, 可选): 导出格式 (excel/pdf/csv)，默认excel

**响应示例**:
```json
{
  "file_url": "/api/v1/presale/ai/downloads/ai_report_2026-02-01_2026-02-15.xlsx",
  "file_name": "ai_report_2026-02-01_2026-02-15.xlsx",
  "file_size": 52480,
  "generated_at": "2026-02-15T10:00:00"
}
```

---

## 🔧 AI功能枚举

所有AI功能的标识符：

| 功能标识 | 功能名称 | 描述 |
|---------|---------|------|
| `requirement` | 需求理解 | AI分析客户需求 |
| `solution` | 方案生成 | 自动生成技术方案 |
| `cost` | 成本估算 | 智能成本评估 |
| `winrate` | 赢率预测 | 项目赢率分析 |
| `quotation` | 报价生成 | 生成正式报价 |
| `knowledge` | 知识库推荐 | 推荐相关知识 |
| `script` | 话术助手 | 推荐销售话术 |
| `emotion` | 情绪分析 | 分析客户情绪 |
| `mobile` | 移动助手 | 移动端AI助手 |

---

## ⚠️ 错误码

| 状态码 | 说明 |
|-------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

**错误响应格式**:
```json
{
  "detail": "错误详细信息"
}
```

---

## 📝 使用示例

### Python示例

```python
import requests

# 认证
headers = {
    "Authorization": "Bearer YOUR_TOKEN"
}

# 获取仪表盘统计
response = requests.get(
    "http://localhost:8000/api/v1/presale/ai/dashboard/stats",
    headers=headers,
    params={"days": 30}
)
stats = response.json()
print(f"总使用次数: {stats['total_usage']}")

# 启动工作流
workflow_data = {
    "presale_ticket_id": 123,
    "initial_data": {"customer": "ABC公司"},
    "auto_run": True
}
response = requests.post(
    "http://localhost:8000/api/v1/presale/ai/workflow/start",
    headers=headers,
    json=workflow_data
)
print(f"工作流已启动: {response.json()}")
```

### JavaScript示例

```javascript
// 认证
const headers = {
  'Authorization': 'Bearer YOUR_TOKEN',
  'Content-Type': 'application/json'
};

// 获取仪表盘统计
fetch('http://localhost:8000/api/v1/presale/ai/dashboard/stats?days=30', {
  headers: headers
})
  .then(res => res.json())
  .then(stats => {
    console.log(`总使用次数: ${stats.total_usage}`);
  });

// 提交反馈
const feedbackData = {
  ai_function: 'requirement',
  rating: 5,
  feedback_text: '非常好用'
};

fetch('http://localhost:8000/api/v1/presale/ai/feedback', {
  method: 'POST',
  headers: headers,
  body: JSON.stringify(feedbackData)
})
  .then(res => res.json())
  .then(data => console.log('反馈已提交:', data));
```

---

## 🚀 快速开始

1. **获取访问令牌**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -d '{"username":"admin","password":"password"}'
   ```

2. **查看AI系统状态**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/presale/ai/health-check" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

3. **启动AI工作流**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/presale/ai/workflow/start" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"presale_ticket_id":123,"auto_run":true}'
   ```

---

## 📞 技术支持

如有问题，请联系：
- 技术支持邮箱: support@example.com
- 文档地址: http://localhost:8000/docs
- Swagger UI: http://localhost:8000/api/docs

---

**最后更新**: 2026-02-15
**版本**: v1.0.0
