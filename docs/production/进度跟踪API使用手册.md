# 生产进度实时跟踪系统 - API使用手册

## 1. API概览

基础URL: `/api/v1/production/progress`

所有接口需要携带认证Token: `Authorization: Bearer <token>`

权限要求:
- 读取操作: `production:read`
- 写入操作: `production:write`

## 2. 接口详细说明

### 2.1 实时进度总览

**接口**: `GET /production/progress/realtime`

**描述**: 获取生产进度实时总览数据。

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| workshop_id | integer | 否 | 车间ID筛选 |
| workstation_id | integer | 否 | 工位ID筛选 |
| status | string | 否 | 工单状态筛选 |

**请求示例**:
```bash
curl -X GET "http://api.example.com/api/v1/production/progress/realtime?workshop_id=1" \
  -H "Authorization: Bearer your_token"
```

**响应示例**:
```json
{
  "total_work_orders": 150,
  "in_progress": 45,
  "completed_today": 12,
  "delayed": 8,
  "active_workstations": 28,
  "idle_workstations": 5,
  "bottleneck_workstations": 3,
  "active_alerts": 15,
  "critical_alerts": 2,
  "overall_progress": "68.50",
  "overall_capacity_utilization": "82.30",
  "efficiency_rate": "88.75"
}
```

**字段说明**:
- `total_work_orders`: 工单总数
- `in_progress`: 进行中的工单数
- `completed_today`: 今日完成数
- `delayed`: 延期工单数
- `active_workstations`: 活跃工位数
- `idle_workstations`: 空闲工位数
- `bottleneck_workstations`: 瓶颈工位数
- `active_alerts`: 活跃预警数
- `critical_alerts`: 严重预警数
- `overall_progress`: 整体进度(%)
- `overall_capacity_utilization`: 整体产能利用率(%)
- `efficiency_rate`: 平均效率(%)

### 2.2 工单进度时间线

**接口**: `GET /production/progress/work-orders/{work_order_id}/timeline`

**描述**: 获取指定工单的完整进度时间线和预警历史。

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| work_order_id | integer | 是 | 工单ID |

**请求示例**:
```bash
curl -X GET "http://api.example.com/api/v1/production/progress/work-orders/123/timeline" \
  -H "Authorization: Bearer your_token"
```

**响应示例**:
```json
{
  "work_order_id": 123,
  "work_order_no": "WO-2024-001",
  "task_name": "机械加工任务",
  "current_progress": 75,
  "current_status": "IN_PROGRESS",
  "plan_start_date": "2024-02-01",
  "plan_end_date": "2024-02-20",
  "actual_start_time": "2024-02-01T08:00:00",
  "actual_end_time": null,
  "timeline": [
    {
      "id": 1,
      "previous_progress": 0,
      "current_progress": 25,
      "progress_delta": 25,
      "completed_qty": 5,
      "qualified_qty": 5,
      "defect_qty": 0,
      "work_hours": "4.00",
      "cumulative_hours": "4.00",
      "status": "IN_PROGRESS",
      "logged_at": "2024-02-05T16:00:00",
      "logged_by": 10,
      "plan_progress": 20,
      "deviation": 5,
      "is_delayed": 0
    }
  ],
  "alerts": [
    {
      "id": 5,
      "alert_type": "QUALITY",
      "alert_level": "WARNING",
      "alert_title": "质量预警",
      "alert_message": "合格率92%，低于标准",
      "status": "DISMISSED",
      "triggered_at": "2024-02-10T14:30:00"
    }
  ]
}
```

### 2.3 工位实时状态

**接口**: `GET /production/progress/workstations/{workstation_id}/realtime`

**描述**: 获取指定工位的实时运行状态和产能信息。

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| workstation_id | integer | 是 | 工位ID |

**请求示例**:
```bash
curl -X GET "http://api.example.com/api/v1/production/progress/workstations/5/realtime" \
  -H "Authorization: Bearer your_token"
```

**响应示例**:
```json
{
  "id": 1,
  "workstation_id": 5,
  "current_state": "BUSY",
  "current_work_order_id": 123,
  "current_operator_id": 45,
  "current_progress": 75,
  "completed_qty_today": 15,
  "target_qty_today": 20,
  "capacity_utilization": "92.50",
  "work_hours_today": "7.40",
  "idle_hours_today": "0.60",
  "planned_hours_today": "8.00",
  "efficiency_rate": "95.20",
  "quality_rate": "98.50",
  "is_bottleneck": 1,
  "bottleneck_level": 2,
  "alert_count": 2,
  "status_updated_at": "2024-02-16T15:30:00",
  "last_work_start_time": "2024-02-16T08:00:00",
  "last_work_end_time": null,
  "remark": null
}
```

**工位状态说明**:
- `IDLE`: 空闲
- `BUSY`: 忙碌
- `PAUSED`: 暂停
- `MAINTENANCE`: 维护中
- `OFFLINE`: 离线

**瓶颈等级**:
- `0`: 正常
- `1`: 轻度瓶颈（利用率≥90%）
- `2`: 中度瓶颈（利用率≥95%且有排队）
- `3`: 严重瓶颈（利用率≥98%且排队>3）

### 2.4 记录进度日志

**接口**: `POST /production/progress/log`

**描述**: 记录工单的进度变化，自动计算偏差并触发预警规则。

**请求体**:
```json
{
  "work_order_id": 123,
  "workstation_id": 5,
  "current_progress": 80,
  "completed_qty": 16,
  "qualified_qty": 15,
  "defect_qty": 1,
  "work_hours": "2.50",
  "status": "IN_PROGRESS",
  "note": "进展顺利，预计明天完成"
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| work_order_id | integer | 是 | 工单ID |
| workstation_id | integer | 否 | 工位ID |
| current_progress | integer | 是 | 当前进度(0-100) |
| completed_qty | integer | 否 | 已完成数量 |
| qualified_qty | integer | 否 | 合格数量 |
| defect_qty | integer | 否 | 不良数量 |
| work_hours | decimal | 否 | 本次工时 |
| status | string | 是 | 工单状态 |
| note | string | 否 | 备注说明 |

**请求示例**:
```bash
curl -X POST "http://api.example.com/api/v1/production/progress/log" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "work_order_id": 123,
    "current_progress": 80,
    "completed_qty": 16,
    "status": "IN_PROGRESS"
  }'
```

**响应示例**:
```json
{
  "id": 25,
  "work_order_id": 123,
  "workstation_id": 5,
  "previous_progress": 75,
  "current_progress": 80,
  "progress_delta": 5,
  "completed_qty": 16,
  "qualified_qty": 15,
  "defect_qty": 1,
  "work_hours": "2.50",
  "cumulative_hours": "18.50",
  "status": "IN_PROGRESS",
  "previous_status": "IN_PROGRESS",
  "logged_at": "2024-02-16T16:00:00",
  "logged_by": 10,
  "plan_progress": 75,
  "deviation": 5,
  "is_delayed": 0,
  "note": "进展顺利，预计明天完成"
}
```

**自动触发**:
- 更新工单进度和状态
- 更新工位状态
- 计算进度偏差
- 评估预警规则
- 创建预警（如触发）

### 2.5 瓶颈工位识别

**接口**: `GET /production/progress/bottlenecks`

**描述**: 基于产能利用率识别瓶颈工位，支持分级预警。

**请求参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| workshop_id | integer | 否 | - | 车间ID筛选 |
| min_level | integer | 否 | 1 | 最小瓶颈等级(1-3) |
| limit | integer | 否 | 10 | 返回数量限制 |

**请求示例**:
```bash
curl -X GET "http://api.example.com/api/v1/production/progress/bottlenecks?min_level=2&limit=5" \
  -H "Authorization: Bearer your_token"
```

**响应示例**:
```json
[
  {
    "workstation_id": 5,
    "workstation_code": "WS-001",
    "workstation_name": "数控车床1号",
    "workshop_name": "机加工车间",
    "bottleneck_level": 3,
    "capacity_utilization": "99.20",
    "work_hours_today": "7.94",
    "idle_hours_today": "0.06",
    "current_work_order_count": 2,
    "pending_work_order_count": 5,
    "alert_count": 4,
    "bottleneck_reason": "产能利用率99.2%，排队工单5个"
  },
  {
    "workstation_id": 12,
    "workstation_code": "WS-008",
    "workstation_name": "焊接工位3号",
    "workshop_name": "焊接车间",
    "bottleneck_level": 2,
    "capacity_utilization": "96.50",
    "work_hours_today": "7.72",
    "idle_hours_today": "0.28",
    "current_work_order_count": 1,
    "pending_work_order_count": 2,
    "alert_count": 1,
    "bottleneck_reason": "产能利用率96.5%，排队工单2个"
  }
]
```

### 2.6 进度预警列表

**接口**: `GET /production/progress/alerts`

**描述**: 获取进度预警列表，支持多维度筛选。

**请求参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| work_order_id | integer | 否 | 工单ID |
| workstation_id | integer | 否 | 工位ID |
| alert_type | string | 否 | 预警类型 |
| alert_level | string | 否 | 预警级别 |
| status | string | 否 | 状态（默认ACTIVE） |

**预警类型**:
- `DELAY`: 延期预警
- `BOTTLENECK`: 瓶颈预警
- `QUALITY`: 质量预警
- `EFFICIENCY`: 效率预警
- `CAPACITY`: 产能预警

**预警级别**:
- `INFO`: 信息
- `WARNING`: 警告
- `CRITICAL`: 严重
- `URGENT`: 紧急

**请求示例**:
```bash
curl -X GET "http://api.example.com/api/v1/production/progress/alerts?alert_level=CRITICAL&status=ACTIVE" \
  -H "Authorization: Bearer your_token"
```

**响应示例**:
```json
[
  {
    "id": 15,
    "work_order_id": 123,
    "workstation_id": 5,
    "alert_type": "DELAY",
    "alert_level": "CRITICAL",
    "alert_title": "严重进度延期",
    "alert_message": "工单 WO-2024-001 进度严重落后，偏差-22%",
    "current_value": "53.00",
    "threshold_value": "75.00",
    "deviation_value": "22.00",
    "status": "ACTIVE",
    "triggered_at": "2024-02-16T14:00:00",
    "acknowledged_at": null,
    "acknowledged_by": null,
    "resolved_at": null,
    "resolved_by": null,
    "dismissed_at": null,
    "dismissed_by": null,
    "action_taken": null,
    "resolution_note": null,
    "rule_code": "RULE_DELAY_CRITICAL",
    "rule_name": "严重延期预警规则"
  }
]
```

### 2.7 关闭预警

**接口**: `POST /production/progress/alerts/{alert_id}/dismiss`

**描述**: 关闭指定的进度预警，可添加处理说明。

**路径参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| alert_id | integer | 是 | 预警ID |

**请求体**:
```json
{
  "resolution_note": "已加派人手，预计明天赶上进度"
}
```

**请求示例**:
```bash
curl -X POST "http://api.example.com/api/v1/production/progress/alerts/15/dismiss" \
  -H "Authorization: Bearer your_token" \
  -H "Content-Type: application/json" \
  -d '{
    "resolution_note": "已加派人手，预计明天赶上进度"
  }'
```

**响应示例**:
```json
{
  "message": "预警已关闭",
  "alert_id": 15
}
```

### 2.8 进度偏差分析

**接口**: `GET /production/progress/deviation`

**描述**: 分析工单进度偏差，识别延期风险。

**请求参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| workshop_id | integer | 否 | - | 车间ID筛选 |
| min_deviation | integer | 否 | 10 | 最小偏差(%) |
| only_delayed | boolean | 否 | true | 只显示延期工单 |

**请求示例**:
```bash
curl -X GET "http://api.example.com/api/v1/production/progress/deviation?min_deviation=15" \
  -H "Authorization: Bearer your_token"
```

**响应示例**:
```json
[
  {
    "work_order_id": 123,
    "work_order_no": "WO-2024-001",
    "task_name": "机械加工任务",
    "plan_progress": 75,
    "actual_progress": 53,
    "deviation": -22,
    "deviation_percentage": "29.33",
    "is_delayed": true,
    "plan_end_date": "2024-02-20",
    "estimated_completion_date": "2024-02-25T16:00:00",
    "delay_days": 5,
    "risk_level": "CRITICAL"
  },
  {
    "work_order_id": 145,
    "work_order_no": "WO-2024-023",
    "task_name": "组装任务",
    "plan_progress": 60,
    "actual_progress": 45,
    "deviation": -15,
    "deviation_percentage": "25.00",
    "is_delayed": true,
    "plan_end_date": "2024-02-18",
    "estimated_completion_date": "2024-02-21T10:00:00",
    "delay_days": 3,
    "risk_level": "HIGH"
  }
]
```

**风险等级**:
- `LOW`: 偏差 < 10%
- `MEDIUM`: 偏差 10-15%
- `HIGH`: 偏差 15-20%
- `CRITICAL`: 偏差 > 20%

## 3. 错误码说明

| HTTP状态码 | 说明 |
|-----------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

**错误响应格式**:
```json
{
  "detail": "工单 99999 不存在"
}
```

## 4. 使用示例

### 4.1 场景1: 更新工单进度并处理预警

```python
import requests

# 1. 更新进度
response = requests.post(
    "http://api.example.com/api/v1/production/progress/log",
    headers={"Authorization": "Bearer token"},
    json={
        "work_order_id": 123,
        "current_progress": 80,
        "completed_qty": 16,
        "qualified_qty": 15,
        "defect_qty": 1,
        "status": "IN_PROGRESS"
    }
)
log = response.json()
print(f"进度已更新至 {log['current_progress']}%")

# 2. 检查是否有新预警
alerts = requests.get(
    "http://api.example.com/api/v1/production/progress/alerts",
    headers={"Authorization": "Bearer token"},
    params={"work_order_id": 123, "status": "ACTIVE"}
).json()

# 3. 处理预警
for alert in alerts:
    if alert['alert_level'] == 'CRITICAL':
        print(f"严重预警: {alert['alert_message']}")
        # 采取措施...
        # 关闭预警
        requests.post(
            f"http://api.example.com/api/v1/production/progress/alerts/{alert['id']}/dismiss",
            headers={"Authorization": "Bearer token"},
            json={"resolution_note": "已处理"}
        )
```

### 4.2 场景2: 监控瓶颈工位

```python
# 获取所有严重瓶颈
bottlenecks = requests.get(
    "http://api.example.com/api/v1/production/progress/bottlenecks",
    headers={"Authorization": "Bearer token"},
    params={"min_level": 3}
).json()

for ws in bottlenecks:
    print(f"严重瓶颈: {ws['workstation_name']}")
    print(f"  利用率: {ws['capacity_utilization']}%")
    print(f"  排队工单: {ws['pending_work_order_count']}个")
    print(f"  建议: {ws['bottleneck_reason']}")
```

### 4.3 场景3: 进度偏差日报

```python
# 获取所有延期工单
deviations = requests.get(
    "http://api.example.com/api/v1/production/progress/deviation",
    headers={"Authorization": "Bearer token"},
    params={"min_deviation": 10, "only_delayed": True}
).json()

# 生成报表
print("===== 进度偏差日报 =====")
for item in deviations:
    print(f"\n工单: {item['work_order_no']}")
    print(f"  任务: {item['task_name']}")
    print(f"  计划进度: {item['plan_progress']}%")
    print(f"  实际进度: {item['actual_progress']}%")
    print(f"  偏差: {item['deviation']}%")
    print(f"  风险等级: {item['risk_level']}")
    if item['delay_days']:
        print(f"  预计延期: {item['delay_days']}天")
```

## 5. 最佳实践

### 5.1 进度更新频率
- 建议每2-4小时更新一次进度
- 关键工单可增加更新频率
- 避免过于频繁的更新（<30分钟）

### 5.2 预警处理流程
1. 定期检查活跃预警（建议每小时）
2. 优先处理CRITICAL级别预警
3. 处理后及时关闭预警
4. 记录详细的处理说明

### 5.3 性能优化
- 使用分页查询大量数据
- 合理设置查询条件减少结果集
- 缓存常用的实时数据

### 5.4 数据质量
- 确保进度值在0-100范围内
- 合格数 + 不良数 = 完成数
- 工时数据应真实准确
