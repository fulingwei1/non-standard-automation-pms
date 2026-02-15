# 生产排程API使用手册

## 目录

1. [API概览](#1-api概览)
2. [认证](#2-认证)
3. [API端点](#3-api端点)
4. [使用示例](#4-使用示例)
5. [错误处理](#5-错误处理)
6. [最佳实践](#6-最佳实践)

## 1. API概览

### 1.1 基础信息

- **Base URL**: `/api/v1/production/schedule`
- **认证方式**: Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

### 1.2 API端点列表

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/generate` | 生成智能排程 |
| GET | `/preview` | 排程预览 |
| POST | `/confirm` | 确认排程 |
| GET | `/conflicts` | 资源冲突检测 |
| POST | `/adjust` | 手动调整排程 |
| POST | `/urgent-insert` | 紧急插单 |
| GET | `/comparison` | 排程方案对比 |
| GET | `/gantt` | 甘特图数据 |
| DELETE | `/reset` | 重置排程 |
| GET | `/history` | 排程历史 |

## 2. 认证

### 2.1 获取Token

```bash
curl -X POST /api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

响应:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2.2 使用Token

```bash
curl -X GET /api/v1/production/schedule/preview?plan_id=1001 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 3. API端点

### 3.1 生成智能排程

**POST** `/schedule/generate`

#### 请求参数

```json
{
  "work_orders": [1, 2, 3, 4, 5],              // 必需: 工单ID列表
  "start_date": "2026-02-17T08:00:00",        // 必需: 开始日期
  "end_date": "2026-02-28T18:00:00",          // 必需: 结束日期
  "algorithm": "GREEDY",                       // 可选: GREEDY/HEURISTIC (默认GREEDY)
  "optimize_target": "BALANCED",               // 可选: TIME/RESOURCE/BALANCED (默认BALANCED)
  "constraints": null,                         // 可选: 自定义约束
  "consider_worker_skills": true,              // 可选: 考虑工人技能 (默认true)
  "consider_equipment_capacity": true,         // 可选: 考虑设备产能 (默认true)
  "allow_overtime": false                      // 可选: 允许加班 (默认false)
}
```

#### 响应

```json
{
  "plan_id": 1709876400,
  "schedules": [
    {
      "id": 1,
      "work_order_id": 1,
      "equipment_id": 5,
      "worker_id": 12,
      "workshop_id": 1,
      "scheduled_start_time": "2026-02-17T08:00:00",
      "scheduled_end_time": "2026-02-17T16:00:00",
      "duration_hours": 8.0,
      "priority_score": 2.0,
      "status": "PENDING",
      "algorithm_version": "v1.0.0",
      "score": 85.5,
      "sequence_no": 1
    }
  ],
  "total_count": 5,
  "success_count": 5,
  "failed_count": 0,
  "conflicts_count": 0,
  "score": 87.3,
  "metrics": {
    "completion_rate": 1.0,
    "equipment_utilization": 0.75,
    "worker_utilization": 0.68,
    "total_duration_hours": 120.5,
    "skill_match_rate": 0.92,
    "elapsed_time_seconds": 2.34
  },
  "warnings": []
}
```

#### cURL示例

```bash
curl -X POST /api/v1/production/schedule/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "work_orders": [1, 2, 3, 4, 5],
    "start_date": "2026-02-17T08:00:00",
    "end_date": "2026-02-28T18:00:00",
    "algorithm": "HEURISTIC",
    "optimize_target": "BALANCED"
  }'
```

#### Python示例

```python
import requests

url = "http://localhost:8000/api/v1/production/schedule/generate"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
data = {
    "work_orders": [1, 2, 3, 4, 5],
    "start_date": "2026-02-17T08:00:00",
    "end_date": "2026-02-28T18:00:00",
    "algorithm": "GREEDY",
    "optimize_target": "BALANCED",
    "consider_worker_skills": True,
    "consider_equipment_capacity": True
}

response = requests.post(url, headers=headers, json=data)
result = response.json()

print(f"方案ID: {result['plan_id']}")
print(f"成功排程: {result['success_count']}")
print(f"综合评分: {result['score']}")
```

---

### 3.2 排程预览

**GET** `/schedule/preview`

#### 查询参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| plan_id | integer | 是 | 排程方案ID |

#### 响应

```json
{
  "plan_id": 1001,
  "schedules": [...],
  "statistics": {
    "total_schedules": 10,
    "pending": 10,
    "confirmed": 0,
    "in_progress": 0,
    "completed": 0,
    "total_duration_hours": 120.5,
    "completion_rate": 0.95,
    "equipment_utilization": 0.78
  },
  "conflicts": [],
  "warnings": [],
  "is_optimizable": false,
  "optimization_suggestions": []
}
```

#### 示例

```bash
curl -X GET "/api/v1/production/schedule/preview?plan_id=1001" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 3.3 确认排程

**POST** `/schedule/confirm`

#### 查询参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| plan_id | integer | 是 | 排程方案ID |

#### 响应

```json
{
  "success": true,
  "message": "已确认 10 个排程",
  "plan_id": 1001,
  "confirmed_count": 10,
  "confirmed_at": "2026-02-16T10:30:00"
}
```

#### 注意事项

- 只有状态为 `PENDING` 的排程才能被确认
- 如果存在高优先级冲突(HIGH/CRITICAL)，将无法确认
- 确认后排程状态变为 `CONFIRMED`

#### 示例

```bash
curl -X POST "/api/v1/production/schedule/confirm?plan_id=1001" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 3.4 资源冲突检测

**GET** `/schedule/conflicts`

#### 查询参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| plan_id | integer | 否 | 排程方案ID |
| schedule_id | integer | 否 | 单个排程ID |
| status | string | 否 | 冲突状态: UNRESOLVED/RESOLVED/IGNORED |

#### 响应

```json
{
  "has_conflicts": true,
  "total_conflicts": 3,
  "conflicts_by_type": {
    "EQUIPMENT": 2,
    "WORKER": 1
  },
  "severity_summary": {
    "HIGH": 2,
    "MEDIUM": 1
  },
  "conflicts": [
    {
      "id": 1,
      "schedule_id": 5,
      "conflicting_schedule_id": 8,
      "conflict_type": "EQUIPMENT",
      "resource_type": "equipment",
      "resource_id": 3,
      "conflict_description": "设备 3 时间冲突",
      "severity": "HIGH",
      "conflict_start_time": "2026-02-17T14:00:00",
      "conflict_end_time": "2026-02-17T16:00:00",
      "overlap_duration_hours": 2.0,
      "resolution_suggestion": "调整其中一个排程的开始时间",
      "status": "UNRESOLVED",
      "detected_at": "2026-02-16T10:00:00"
    }
  ]
}
```

#### 示例

```bash
# 检查整个方案的冲突
curl -X GET "/api/v1/production/schedule/conflicts?plan_id=1001" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 检查单个排程的冲突
curl -X GET "/api/v1/production/schedule/conflicts?schedule_id=5" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 只看未解决的冲突
curl -X GET "/api/v1/production/schedule/conflicts?plan_id=1001&status=UNRESOLVED" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 3.5 手动调整排程

**POST** `/schedule/adjust`

#### 请求参数

```json
{
  "schedule_id": 5,                                  // 必需: 排程ID
  "adjustment_type": "TIME_CHANGE",                  // 必需: 调整类型
  "new_start_time": "2026-02-18T08:00:00",          // 可选: 新开始时间
  "new_end_time": "2026-02-18T16:00:00",            // 可选: 新结束时间
  "new_equipment_id": 7,                             // 可选: 新设备ID
  "new_worker_id": 15,                               // 可选: 新工人ID
  "reason": "解决设备冲突",                           // 必需: 调整原因
  "auto_resolve_conflicts": true                     // 可选: 自动解决冲突
}
```

**adjustment_type** 可选值:
- `TIME_CHANGE`: 时间调整
- `RESOURCE_CHANGE`: 资源调整
- `PRIORITY_CHANGE`: 优先级调整
- `CANCEL`: 取消
- `RESTORE`: 恢复

#### 响应

```json
{
  "success": true,
  "message": "排程调整成功",
  "schedule_id": 5,
  "changes": ["开始时间", "结束时间"],
  "adjustment_log_id": 123
}
```

#### 示例

```python
# 调整开始时间
response = requests.post('/api/v1/production/schedule/adjust', 
    headers=headers,
    json={
        "schedule_id": 5,
        "adjustment_type": "TIME_CHANGE",
        "new_start_time": "2026-02-18T08:00:00",
        "new_end_time": "2026-02-18T16:00:00",
        "reason": "客户要求延后",
        "auto_resolve_conflicts": True
    }
)

# 更换设备
response = requests.post('/api/v1/production/schedule/adjust',
    headers=headers,
    json={
        "schedule_id": 5,
        "adjustment_type": "RESOURCE_CHANGE",
        "new_equipment_id": 7,
        "reason": "原设备故障",
        "auto_resolve_conflicts": False
    }
)
```

---

### 3.6 紧急插单

**POST** `/schedule/urgent-insert`

#### 请求参数

```json
{
  "work_order_id": 999,                    // 必需: 工单ID
  "insert_time": "2026-02-17T14:00:00",   // 必需: 期望插入时间
  "max_delay_hours": 4.0,                  // 可选: 允许延迟的最大时长(默认4)
  "auto_adjust": true,                     // 可选: 自动调整其他排程(默认true)
  "priority_override": true                // 可选: 覆盖优先级(默认true)
}
```

#### 响应

```json
{
  "success": true,
  "schedule": {
    "id": 25,
    "work_order_id": 999,
    "scheduled_start_time": "2026-02-17T14:00:00",
    "scheduled_end_time": "2026-02-17T18:00:00",
    "is_urgent": true,
    "priority_score": 5.0
  },
  "adjusted_schedules": [
    {
      "id": 10,
      "work_order_id": 5,
      "scheduled_start_time": "2026-02-18T08:00:00",
      "scheduled_end_time": "2026-02-18T16:00:00"
    }
  ],
  "conflicts": [],
  "message": "紧急插单成功，调整了 1 个排程"
}
```

#### 示例

```bash
curl -X POST /api/v1/production/schedule/urgent-insert \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "work_order_id": 999,
    "insert_time": "2026-02-17T14:00:00",
    "max_delay_hours": 6,
    "auto_adjust": true
  }'
```

---

### 3.7 排程方案对比

**GET** `/schedule/comparison`

#### 查询参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| plan_ids | string | 是 | 方案ID列表，逗号分隔 (如: "1001,1002,1003") |

#### 响应

```json
{
  "comparison_time": "2026-02-16T11:00:00",
  "plans_compared": 3,
  "results": [
    {
      "plan_id": 1002,
      "plan_name": "方案 1002",
      "metrics": {
        "overall_score": 92.5,
        "completion_rate": 0.98,
        "equipment_utilization": 0.82,
        "worker_utilization": 0.75,
        "total_duration_hours": 118.3,
        "conflict_count": 0
      },
      "rank": 1,
      "recommendation": "推荐方案：综合评分最高"
    },
    {
      "plan_id": 1001,
      "plan_name": "方案 1001",
      "metrics": {
        "overall_score": 87.3,
        "completion_rate": 1.0,
        "equipment_utilization": 0.75,
        "worker_utilization": 0.68,
        "total_duration_hours": 120.5,
        "conflict_count": 0
      },
      "rank": 2,
      "recommendation": null
    }
  ],
  "best_plan_id": 1002,
  "comparison_summary": {
    "total_plans": 3,
    "best_plan": 1002,
    "score_range": {
      "min": 82.1,
      "max": 92.5
    }
  }
}
```

#### 示例

```bash
curl -X GET "/api/v1/production/schedule/comparison?plan_ids=1001,1002,1003" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 3.8 甘特图数据

**GET** `/schedule/gantt`

#### 查询参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| plan_id | integer | 是 | 排程方案ID |

#### 响应

```json
{
  "tasks": [
    {
      "id": 1,
      "name": "组装任务A",
      "work_order_no": "WO20260001",
      "start": "2026-02-17T08:00:00",
      "end": "2026-02-17T16:00:00",
      "duration": 8.0,
      "progress": 0.0,
      "resource": "设备5",
      "equipment": "设备5",
      "worker": "工人12",
      "status": "PENDING",
      "priority": "NORMAL",
      "dependencies": [],
      "color": "#9E9E9E"
    }
  ],
  "total_tasks": 10,
  "start_date": "2026-02-17T08:00:00",
  "end_date": "2026-02-28T18:00:00",
  "resources": [
    {"type": "equipment", "id": 5, "name": "设备5"},
    {"type": "worker", "id": 12, "name": "工人12"}
  ],
  "milestones": []
}
```

#### 颜色编码

| 状态 | 颜色 | 说明 |
|------|------|------|
| PENDING | #9E9E9E | 灰色 - 待确认 |
| CONFIRMED | #2196F3 | 蓝色 - 已确认 |
| IN_PROGRESS | #FF9800 | 橙色 - 进行中 |
| COMPLETED | #4CAF50 | 绿色 - 已完成 |
| CANCELLED | #F44336 | 红色 - 已取消 |

#### 示例

```bash
curl -X GET "/api/v1/production/schedule/gantt?plan_id=1001" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 3.9 重置排程

**DELETE** `/schedule/reset`

#### 查询参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| plan_id | integer | 是 | 排程方案ID |

#### 响应

```json
{
  "success": true,
  "message": "已重置方案 1001",
  "deleted_count": 10
}
```

#### 注意事项

⚠️ **警告**: 此操作不可恢复！将删除:
- 所有排程记录
- 相关冲突记录
- 调整日志

#### 示例

```bash
curl -X DELETE "/api/v1/production/schedule/reset?plan_id=1001" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

### 3.10 排程历史

**GET** `/schedule/history`

#### 查询参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| schedule_id | integer | 否 | 单个排程ID |
| plan_id | integer | 否 | 方案ID |
| page | integer | 否 | 页码(默认1) |
| page_size | integer | 否 | 每页数量(默认20) |

#### 响应

```json
{
  "schedules": [...],
  "adjustments": [
    {
      "id": 1,
      "schedule_id": 5,
      "adjustment_type": "TIME_CHANGE",
      "trigger_source": "MANUAL",
      "before_data": {
        "scheduled_start_time": "2026-02-17T08:00:00",
        "scheduled_end_time": "2026-02-17T16:00:00"
      },
      "after_data": {
        "scheduled_start_time": "2026-02-18T08:00:00",
        "scheduled_end_time": "2026-02-18T16:00:00"
      },
      "changes_summary": "调整了: 开始时间, 结束时间",
      "reason": "客户要求延后",
      "adjusted_at": "2026-02-16T14:00:00"
    }
  ],
  "total_count": 15,
  "page": 1,
  "page_size": 20
}
```

#### 示例

```bash
# 查看单个排程的历史
curl -X GET "/api/v1/production/schedule/history?schedule_id=5&page=1&page_size=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 查看整个方案的历史
curl -X GET "/api/v1/production/schedule/history?plan_id=1001&page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 4. 使用示例

### 4.1 完整工作流程

```python
import requests
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api/v1"
token = "YOUR_ACCESS_TOKEN"
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Step 1: 生成排程
print("Step 1: 生成排程...")
response = requests.post(f"{BASE_URL}/production/schedule/generate",
    headers=headers,
    json={
        "work_orders": [1, 2, 3, 4, 5],
        "start_date": (datetime.now() + timedelta(days=1)).isoformat(),
        "end_date": (datetime.now() + timedelta(days=15)).isoformat(),
        "algorithm": "HEURISTIC",
        "optimize_target": "BALANCED"
    }
)
data = response.json()
plan_id = data['plan_id']
print(f"✅ 生成成功，方案ID: {plan_id}, 评分: {data['score']}")

# Step 2: 预览排程
print("\nStep 2: 预览排程...")
response = requests.get(f"{BASE_URL}/production/schedule/preview",
    headers=headers,
    params={"plan_id": plan_id}
)
preview = response.json()
print(f"✅ 排程数量: {preview['statistics']['total_schedules']}")
print(f"   交期达成率: {preview['statistics']['completion_rate']:.1%}")

# Step 3: 检查冲突
print("\nStep 3: 检查冲突...")
response = requests.get(f"{BASE_URL}/production/schedule/conflicts",
    headers=headers,
    params={"plan_id": plan_id}
)
conflicts = response.json()
if conflicts['has_conflicts']:
    print(f"⚠️  检测到 {conflicts['total_conflicts']} 个冲突")
    for conflict in conflicts['conflicts']:
        if conflict['severity'] in ['HIGH', 'CRITICAL']:
            print(f"   - {conflict['conflict_description']}")
else:
    print("✅ 无冲突")

# Step 4: 确认排程
print("\nStep 4: 确认排程...")
response = requests.post(f"{BASE_URL}/production/schedule/confirm",
    headers=headers,
    params={"plan_id": plan_id}
)
if response.status_code == 200:
    confirm_data = response.json()
    print(f"✅ 已确认 {confirm_data['confirmed_count']} 个排程")
else:
    print(f"❌ 确认失败: {response.json()['detail']}")

# Step 5: 导出甘特图
print("\nStep 5: 导出甘特图...")
response = requests.get(f"{BASE_URL}/production/schedule/gantt",
    headers=headers,
    params={"plan_id": plan_id}
)
gantt_data = response.json()
print(f"✅ 甘特图数据包含 {gantt_data['total_tasks']} 个任务")
```

### 4.2 紧急插单示例

```python
# 紧急插单
work_order_id = 999
insert_time = (datetime.now() + timedelta(hours=2)).isoformat()

response = requests.post(f"{BASE_URL}/production/schedule/urgent-insert",
    headers=headers,
    json={
        "work_order_id": work_order_id,
        "insert_time": insert_time,
        "max_delay_hours": 4,
        "auto_adjust": True,
        "priority_override": True
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"✅ 紧急插单成功")
    print(f"   新排程ID: {data['schedule']['id']}")
    print(f"   调整了 {len(data['adjusted_schedules'])} 个排程")
    
    if data['adjusted_schedules']:
        print("   被调整的排程:")
        for adj in data['adjusted_schedules']:
            print(f"   - 工单 {adj['work_order_id']}")
else:
    print(f"❌ 插单失败: {response.json()['detail']}")
```

### 4.3 批量对比方案

```python
# 生成多个方案
plan_ids = []

for algorithm in ['GREEDY', 'HEURISTIC']:
    response = requests.post(f"{BASE_URL}/production/schedule/generate",
        headers=headers,
        json={
            "work_orders": [1, 2, 3, 4, 5],
            "start_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=15)).isoformat(),
            "algorithm": algorithm,
            "optimize_target": "BALANCED"
        }
    )
    plan_ids.append(response.json()['plan_id'])

# 对比方案
response = requests.get(f"{BASE_URL}/production/schedule/comparison",
    headers=headers,
    params={"plan_ids": ",".join(map(str, plan_ids))}
)

comparison = response.json()
print(f"📊 方案对比结果:")
for result in comparison['results']:
    print(f"\n方案 {result['plan_id']} (排名: {result['rank']})")
    print(f"   综合评分: {result['metrics']['overall_score']}")
    print(f"   交期达成率: {result['metrics']['completion_rate']:.1%}")
    print(f"   设备利用率: {result['metrics']['equipment_utilization']:.1%}")
    if result['recommendation']:
        print(f"   ⭐ {result['recommendation']}")
```

## 5. 错误处理

### 5.1 常见错误码

| 状态码 | 描述 | 示例 |
|--------|------|------|
| 400 | 请求参数错误 | 工单ID列表为空 |
| 401 | 未认证 | Token无效或过期 |
| 403 | 无权限 | 没有排程操作权限 |
| 404 | 资源不存在 | 排程方案不存在 |
| 500 | 服务器错误 | 排程算法执行失败 |

### 5.2 错误响应格式

```json
{
  "detail": "存在 2 个高优先级冲突，请先解决后再确认"
}
```

### 5.3 错误处理示例

```python
try:
    response = requests.post(f"{BASE_URL}/production/schedule/generate",
        headers=headers,
        json=request_data
    )
    response.raise_for_status()
    data = response.json()
    
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 400:
        print(f"❌ 请求参数错误: {e.response.json()['detail']}")
    elif e.response.status_code == 401:
        print("❌ 认证失败，请重新登录")
        # 重新获取token
    elif e.response.status_code == 404:
        print("❌ 资源不存在")
    else:
        print(f"❌ 服务器错误: {e.response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("❌ 连接失败，请检查网络")
    
except requests.exceptions.Timeout:
    print("❌ 请求超时")
```

## 6. 最佳实践

### 6.1 性能优化

```python
# ✅ 推荐: 批量排程
requests.post('/schedule/generate', json={
    "work_orders": [1, 2, 3, 4, 5]  # 一次性排多个
})

# ❌ 不推荐: 逐个排程
for wo_id in [1, 2, 3, 4, 5]:
    requests.post('/schedule/generate', json={
        "work_orders": [wo_id]  # 慢
    })
```

### 6.2 错误重试

```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# 配置重试策略
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504]
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)

# 使用session发送请求
response = session.post(url, headers=headers, json=data)
```

### 6.3 超时设置

```python
# 设置合理的超时时间
response = requests.post(url, 
    headers=headers, 
    json=data,
    timeout=(5, 30)  # (连接超时, 读取超时)
)
```

---

## 附录

### A. 数据格式说明

#### 日期时间格式

ISO 8601格式: `YYYY-MM-DDTHH:MM:SS`

示例: `2026-02-17T08:00:00`

#### 枚举值

**algorithm**:
- `GREEDY`: 贪心算法
- `HEURISTIC`: 启发式算法
- `GENETIC`: 遗传算法(未实现)

**optimize_target**:
- `TIME`: 最短完成时间
- `RESOURCE`: 最高资源利用率
- `BALANCED`: 平衡模式

**status**:
- `PENDING`: 待确认
- `CONFIRMED`: 已确认
- `IN_PROGRESS`: 进行中
- `COMPLETED`: 已完成
- `CANCELLED`: 已取消

**severity**:
- `LOW`: 低
- `MEDIUM`: 中
- `HIGH`: 高
- `CRITICAL`: 严重

---

## 联系支持

如有问题，请联系技术支持或查看详细文档:
- 技术文档: `/docs/production_schedule_algorithm.md`
- 最佳实践: `/docs/production_schedule_best_practices.md`
