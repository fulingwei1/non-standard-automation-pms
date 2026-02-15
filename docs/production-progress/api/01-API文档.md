# 生产进度模块 API 文档

## 1. 文档说明

### 1.1 概述
本文档描述生产进度模块的所有REST API接口，包括：
- 排程管理API
- 工单管理API
- 报工管理API
- 质量管理API
- 统计分析API

### 1.2 基础信息

**Base URL**: `http://your-domain.com/api/v1`

**认证方式**: Bearer Token (JWT)

**请求头**:
```http
Authorization: Bearer <your_access_token>
Content-Type: application/json
```

**统一响应格式**:
```json
{
    "code": 200,
    "message": "Success",
    "data": {...}
}
```

**错误响应格式**:
```json
{
    "code": 400,
    "message": "Error message",
    "detail": "Detailed error description"
}
```

### 1.3 HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 401 | 未认证 |
| 403 | 无权限 |
| 404 | 资源不存在 |
| 422 | 数据验证失败 |
| 500 | 服务器错误 |

---

## 2. 排程管理API

### 2.1 获取排程计划列表

**接口**: `GET /production/schedules`

**描述**: 获取车间排程计划列表

**权限**: `production:schedule:view`

**请求参数**:
```typescript
{
    workshop_id?: number;      // 车间ID (可选)
    start_date?: string;       // 开始日期 (可选) YYYY-MM-DD
    end_date?: string;         // 结束日期 (可选) YYYY-MM-DD
    status?: string;           // 状态 (可选) PENDING/ACTIVE/COMPLETED
    page?: number;             // 页码 (默认1)
    page_size?: number;        // 每页数量 (默认20)
}
```

**响应示例**:
```json
{
    "code": 200,
    "message": "Success",
    "data": {
        "items": [
            {
                "id": 1,
                "schedule_no": "SCH-2026021601",
                "workshop_id": 1,
                "workshop_name": "车间A",
                "plan_date": "2026-02-16",
                "total_orders": 15,
                "completed_orders": 8,
                "progress_percent": 53,
                "status": "ACTIVE",
                "created_at": "2026-02-16T08:00:00",
                "updated_at": "2026-02-16T10:30:00"
            }
        ],
        "total": 50,
        "page": 1,
        "page_size": 20,
        "total_pages": 3
    }
}
```

---

### 2.2 创建排程计划

**接口**: `POST /production/schedules`

**描述**: 创建新的排程计划

**权限**: `production:schedule:create`

**请求体**:
```json
{
    "workshop_id": 1,
    "plan_date": "2026-02-17",
    "orders": [
        {
            "order_id": 101,
            "priority": 8,
            "plan_start_time": "08:00",
            "plan_end_time": "12:00"
        },
        {
            "order_id": 102,
            "priority": 6,
            "plan_start_time": "13:00",
            "plan_end_time": "17:00"
        }
    ],
    "algorithm": "GENETIC",  // 排程算法: GENETIC/GREEDY/FIFO
    "optimize_target": "MAKESPAN"  // 优化目标: MAKESPAN/UTILIZATION/TARDINESS
}
```

**响应示例**:
```json
{
    "code": 201,
    "message": "排程计划创建成功",
    "data": {
        "id": 101,
        "schedule_no": "SCH-2026021701",
        "workshop_id": 1,
        "plan_date": "2026-02-17",
        "total_orders": 2,
        "estimated_makespan": 8.5,  // 预估完工时间(小时)
        "resource_utilization": 0.85,  // 资源利用率
        "status": "PENDING",
        "created_at": "2026-02-16T10:35:00"
    }
}
```

---

### 2.3 AI智能排程

**接口**: `POST /production/schedules/ai-optimize`

**描述**: 使用AI算法优化排程方案

**权限**: `production:schedule:optimize`

**请求体**:
```json
{
    "workshop_id": 1,
    "plan_date": "2026-02-17",
    "order_ids": [101, 102, 103, 104, 105],
    "constraints": {
        "max_overtime_hours": 2,
        "prefer_skill_match": true,
        "deadline_strict": true
    },
    "algorithm": "GENETIC",
    "population_size": 100,
    "max_generations": 200
}
```

**响应示例**:
```json
{
    "code": 200,
    "message": "AI排程优化完成",
    "data": {
        "schedule_id": 102,
        "optimized_plan": [
            {
                "order_id": 103,
                "assigned_worker_id": 5,
                "assigned_equipment_id": 12,
                "plan_start_time": "2026-02-17T08:00:00",
                "plan_end_time": "2026-02-17T10:30:00",
                "estimated_hours": 2.5
            },
            {
                "order_id": 101,
                "assigned_worker_id": 3,
                "assigned_equipment_id": 8,
                "plan_start_time": "2026-02-17T08:00:00",
                "plan_end_time": "2026-02-17T11:00:00",
                "estimated_hours": 3.0
            }
        ],
        "optimization_metrics": {
            "makespan": 8.5,           // 总完工时间(小时)
            "avg_utilization": 0.87,   // 平均利用率
            "tardiness": 0,            // 延期惩罚
            "fitness_score": 0.92,     // 适应度分数
            "generations_used": 156    // 实际迭代代数
        },
        "comparison": {
            "before_makespan": 10.2,
            "after_makespan": 8.5,
            "improvement_percent": 16.7
        }
    }
}
```

---

## 3. 工单管理API

### 3.1 创建生产工单

**接口**: `POST /production/work-orders`

**描述**: 创建生产工单

**权限**: `production:workorder:create`

**请求体**:
```json
{
    "project_id": 10,
    "process_id": 5,
    "plan_qty": 200,
    "plan_start_date": "2026-02-17T08:00:00",
    "plan_end_date": "2026-02-18T17:00:00",
    "priority": 8,
    "estimated_hours": 16.5,
    "bom_id": 25,  // 物料清单ID (可选)
    "remark": "紧急订单，优先处理"
}
```

**响应示例**:
```json
{
    "code": 201,
    "message": "工单创建成功",
    "data": {
        "id": 1001,
        "work_order_no": "WO-2026021601",
        "project_id": 10,
        "project_name": "XX自动化设备",
        "process_id": 5,
        "process_name": "组装工序",
        "plan_qty": 200,
        "completed_qty": 0,
        "plan_start_date": "2026-02-17T08:00:00",
        "plan_end_date": "2026-02-18T17:00:00",
        "status": "PENDING",
        "priority": 8,
        "created_at": "2026-02-16T10:40:00"
    }
}
```

---

### 3.2 工单派工

**接口**: `POST /production/work-orders/{work_order_id}/assign`

**描述**: 将工单分配给工人

**权限**: `production:workorder:assign`

**路径参数**:
- `work_order_id` (integer): 工单ID

**请求体**:
```json
{
    "worker_id": 15,
    "workstation_id": 8,
    "equipment_id": 12,
    "plan_start_time": "2026-02-17T08:30:00",
    "assigned_reason": "技能匹配，当前负荷适中"
}
```

**响应示例**:
```json
{
    "code": 200,
    "message": "派工成功",
    "data": {
        "work_order_id": 1001,
        "work_order_no": "WO-2026021601",
        "assigned_to": 15,
        "worker_name": "张三",
        "workstation_id": 8,
        "workstation_name": "组装工位A-01",
        "equipment_id": 12,
        "equipment_name": "自动焊接机-01",
        "assigned_at": "2026-02-16T10:45:00",
        "status": "ASSIGNED"
    }
}
```

---

### 3.3 获取工单详情

**接口**: `GET /production/work-orders/{work_order_id}`

**描述**: 获取工单详细信息

**权限**: `production:workorder:view`

**路径参数**:
- `work_order_id` (integer): 工单ID

**响应示例**:
```json
{
    "code": 200,
    "message": "Success",
    "data": {
        "id": 1001,
        "work_order_no": "WO-2026021601",
        "project": {
            "id": 10,
            "name": "XX自动化设备",
            "customer": "某科技公司"
        },
        "process": {
            "id": 5,
            "name": "组装工序",
            "standard_hours": 0.08
        },
        "plan_qty": 200,
        "completed_qty": 65,
        "qualified_qty": 62,
        "defect_qty": 3,
        "progress_percent": 32.5,
        "plan_start_date": "2026-02-17T08:00:00",
        "plan_end_date": "2026-02-18T17:00:00",
        "actual_start_time": "2026-02-17T08:15:00",
        "actual_end_time": null,
        "assigned_to": 15,
        "worker": {
            "id": 15,
            "name": "张三",
            "skill_level": 4,
            "efficiency_rate": 1.15
        },
        "workstation": {
            "id": 8,
            "name": "组装工位A-01",
            "workshop_id": 1,
            "workshop_name": "车间A"
        },
        "equipment": {
            "id": 12,
            "name": "自动焊接机-01",
            "status": "RUNNING",
            "efficiency": 0.92
        },
        "estimated_hours": 16.5,
        "actual_hours": 5.2,
        "status": "IN_PROGRESS",
        "priority": 8,
        "predicted_completion": "2026-02-18T15:30:00",  // AI预测完工时间
        "delay_hours": 0,  // 延期小时数（负数表示提前）
        "created_at": "2026-02-16T10:40:00",
        "updated_at": "2026-02-17T14:00:00"
    }
}
```

---

### 3.4 工单列表查询

**接口**: `GET /production/work-orders`

**描述**: 查询工单列表（支持多种筛选条件）

**权限**: `production:workorder:view`

**请求参数**:
```typescript
{
    project_id?: number;       // 项目ID
    workshop_id?: number;      // 车间ID
    worker_id?: number;        // 工人ID
    status?: string;           // 状态: PENDING/ASSIGNED/IN_PROGRESS/PAUSED/COMPLETED
    priority_min?: number;     // 最小优先级
    priority_max?: number;     // 最大优先级
    start_date?: string;       // 计划开始日期 (YYYY-MM-DD)
    end_date?: string;         // 计划结束日期 (YYYY-MM-DD)
    keyword?: string;          // 关键词搜索 (工单号/项目名)
    sort_by?: string;          // 排序字段: priority/plan_start_date/progress_percent
    order?: string;            // 排序方向: asc/desc
    page?: number;
    page_size?: number;
}
```

**响应示例**:
```json
{
    "code": 200,
    "message": "Success",
    "data": {
        "items": [
            {
                "id": 1001,
                "work_order_no": "WO-2026021601",
                "project_name": "XX自动化设备",
                "process_name": "组装工序",
                "plan_qty": 200,
                "completed_qty": 65,
                "progress_percent": 32.5,
                "worker_name": "张三",
                "status": "IN_PROGRESS",
                "priority": 8,
                "plan_start_date": "2026-02-17T08:00:00",
                "plan_end_date": "2026-02-18T17:00:00",
                "delay_hours": 0
            }
        ],
        "total": 150,
        "page": 1,
        "page_size": 20,
        "statistics": {
            "total_orders": 150,
            "pending": 25,
            "in_progress": 80,
            "completed": 45,
            "avg_progress": 58.3,
            "on_time_rate": 0.85
        }
    }
}
```

---

### 3.5 暂停工单

**接口**: `POST /production/work-orders/{work_order_id}/pause`

**描述**: 暂停正在进行的工单

**权限**: `production:workorder:pause`

**请求体**:
```json
{
    "pause_reason": "EQUIPMENT_FAILURE",  // 暂停原因
    "pause_description": "焊接机故障，需要维修",
    "estimated_resume_time": "2026-02-17T16:00:00"
}
```

**响应示例**:
```json
{
    "code": 200,
    "message": "工单已暂停",
    "data": {
        "work_order_id": 1001,
        "status": "PAUSED",
        "paused_at": "2026-02-17T14:30:00",
        "pause_reason": "EQUIPMENT_FAILURE",
        "estimated_resume_time": "2026-02-17T16:00:00"
    }
}
```

---

### 3.6 恢复工单

**接口**: `POST /production/work-orders/{work_order_id}/resume`

**描述**: 恢复暂停的工单

**权限**: `production:workorder:resume`

**请求体**:
```json
{
    "resume_description": "设备维修完成，恢复生产"
}
```

**响应示例**:
```json
{
    "code": 200,
    "message": "工单已恢复",
    "data": {
        "work_order_id": 1001,
        "status": "IN_PROGRESS",
        "resumed_at": "2026-02-17T16:15:00",
        "pause_duration_hours": 1.75
    }
}
```

---

## 4. 报工管理API

### 4.1 提交报工

**接口**: `POST /production/work-reports`

**描述**: 工人提交工作报告

**权限**: `production:workreport:submit`

**请求体**:
```json
{
    "work_order_id": 1001,
    "worker_id": 15,
    "report_type": "PROGRESS",  // 报工类型: START/PROGRESS/PAUSE/RESUME/COMPLETE
    "report_time": "2026-02-17T14:00:00",
    "work_hours": 2.5,
    "completed_qty": 20,
    "qualified_qty": 19,
    "defect_qty": 1,
    "description": "本次完成20件，1件焊接不良",
    "defect_images": [
        "https://example.com/defect-001.jpg"
    ]
}
```

**响应示例**:
```json
{
    "code": 201,
    "message": "报工提交成功",
    "data": {
        "id": 5001,
        "report_no": "WR-2026021701",
        "work_order_id": 1001,
        "work_order_no": "WO-2026021601",
        "worker_id": 15,
        "worker_name": "张三",
        "report_type": "PROGRESS",
        "report_time": "2026-02-17T14:00:00",
        "work_hours": 2.5,
        "completed_qty": 20,
        "qualified_qty": 19,
        "defect_qty": 1,
        "status": "PENDING",  // 待审核
        "created_at": "2026-02-17T14:05:00",
        "warnings": [
            {
                "type": "DEFECT_DETECTED",
                "message": "检测到1件不良品，请注意质量控制"
            }
        ]
    }
}
```

---

### 4.2 审核报工

**接口**: `POST /production/work-reports/{report_id}/approve`

**描述**: 审核工作报告

**权限**: `production:workreport:approve`

**请求体**:
```json
{
    "approved": true,  // true-通过, false-拒绝
    "approve_comment": "报工数据准确，通过审核",
    "adjust_work_hours": null,  // 调整工时 (可选)
    "adjust_qty": null  // 调整数量 (可选)
}
```

**响应示例**:
```json
{
    "code": 200,
    "message": "审核完成",
    "data": {
        "report_id": 5001,
        "report_no": "WR-2026021701",
        "status": "APPROVED",
        "approved_by": 8,
        "approver_name": "李主管",
        "approved_at": "2026-02-17T14:20:00",
        "approve_comment": "报工数据准确，通过审核",
        "work_order_updated": {
            "completed_qty": 65,  // 更新后的完成数量
            "progress_percent": 32.5
        }
    }
}
```

---

### 4.3 报工记录查询

**接口**: `GET /production/work-reports`

**描述**: 查询报工记录

**权限**: `production:workreport:view`

**请求参数**:
```typescript
{
    work_order_id?: number;
    worker_id?: number;
    report_type?: string;
    status?: string;  // PENDING/APPROVED/REJECTED
    start_date?: string;
    end_date?: string;
    page?: number;
    page_size?: number;
}
```

**响应示例**:
```json
{
    "code": 200,
    "message": "Success",
    "data": {
        "items": [
            {
                "id": 5001,
                "report_no": "WR-2026021701",
                "work_order_no": "WO-2026021601",
                "worker_name": "张三",
                "report_type": "PROGRESS",
                "report_time": "2026-02-17T14:00:00",
                "work_hours": 2.5,
                "completed_qty": 20,
                "status": "APPROVED",
                "approved_by": "李主管",
                "approved_at": "2026-02-17T14:20:00"
            }
        ],
        "total": 300,
        "page": 1,
        "page_size": 20
    }
}
```

---

### 4.4 批量报工

**接口**: `POST /production/work-reports/batch`

**描述**: 批量提交报工记录

**权限**: `production:workreport:submit`

**请求体**:
```json
{
    "worker_id": 15,
    "report_time": "2026-02-17T17:00:00",
    "reports": [
        {
            "work_order_id": 1001,
            "report_type": "PROGRESS",
            "work_hours": 4.0,
            "completed_qty": 30,
            "qualified_qty": 30,
            "defect_qty": 0
        },
        {
            "work_order_id": 1005,
            "report_type": "START",
            "work_hours": 0.5,
            "completed_qty": 0
        }
    ]
}
```

**响应示例**:
```json
{
    "code": 201,
    "message": "批量报工成功",
    "data": {
        "total_submitted": 2,
        "success_count": 2,
        "failed_count": 0,
        "reports": [
            {
                "id": 5010,
                "report_no": "WR-2026021710",
                "work_order_id": 1001,
                "status": "PENDING"
            },
            {
                "id": 5011,
                "report_no": "WR-2026021711",
                "work_order_id": 1005,
                "status": "PENDING"
            }
        ]
    }
}
```

---

## 5. 质量管理API

### 5.1 创建质检记录

**接口**: `POST /production/quality-inspections`

**描述**: 创建质量检验记录

**权限**: `production:quality:inspect`

**请求体**:
```json
{
    "work_order_id": 1001,
    "inspection_type": "IPQC",  // IQC/IPQC/FQC/OQC
    "inspection_date": "2026-02-17T15:00:00",
    "inspector_id": 20,
    "inspection_qty": 50,
    "qualified_qty": 48,
    "defect_qty": 2,
    "measured_value": 5.23,  // 测量值 (可选)
    "spec_upper_limit": 5.50,
    "spec_lower_limit": 5.00,
    "measurement_unit": "mm",
    "defect_type": "焊接不良",
    "defect_description": "焊点虚焊，需要返工",
    "defect_images": [
        "https://example.com/defect-002.jpg"
    ],
    "handling_result": "REWORK"  // REWORK/SCRAP/CONCESSION
}
```

**响应示例**:
```json
{
    "code": 201,
    "message": "质检记录创建成功",
    "data": {
        "id": 3001,
        "inspection_no": "QC-2026021701",
        "work_order_id": 1001,
        "work_order_no": "WO-2026021601",
        "inspection_type": "IPQC",
        "inspection_date": "2026-02-17T15:00:00",
        "inspector_name": "王质检",
        "inspection_qty": 50,
        "qualified_qty": 48,
        "defect_qty": 2,
        "defect_rate": 4.0,  // 不良率%
        "inspection_result": "PARTIAL_PASS",
        "handling_result": "REWORK",
        "created_at": "2026-02-17T15:10:00",
        "alerts": [
            {
                "type": "DEFECT_RATE_WARNING",
                "message": "不良率4.0%，接近阈值5%"
            }
        ]
    }
}
```

---

### 5.2 SPC分析

**接口**: `GET /production/quality-inspections/spc-analysis`

**描述**: 统计过程控制分析

**权限**: `production:quality:analyze`

**请求参数**:
```typescript
{
    work_order_id?: number;
    material_id?: number;
    process_id?: number;
    start_date?: string;
    end_date?: string;
    measurement_type?: string;  // 测量类型
}
```

**响应示例**:
```json
{
    "code": 200,
    "message": "Success",
    "data": {
        "work_order_id": 1001,
        "measurement_type": "焊点直径",
        "sample_size": 100,
        "time_range": {
            "start": "2026-02-17T08:00:00",
            "end": "2026-02-17T17:00:00"
        },
        "statistics": {
            "mean": 5.25,
            "std_dev": 0.12,
            "min": 5.02,
            "max": 5.48,
            "range": 0.46
        },
        "control_limits": {
            "ucl": 5.61,  // 控制上限 (μ + 3σ)
            "cl": 5.25,   // 中心线 (μ)
            "lcl": 4.89,  // 控制下限 (μ - 3σ)
            "usl": 5.50,  // 规格上限
            "lsl": 5.00   // 规格下限
        },
        "process_capability": {
            "cp": 1.39,   // 过程能力指数
            "cpk": 1.25,  // 过程能力指数（考虑偏移）
            "pp": 1.42,   // 过程性能指数
            "ppk": 1.28   // 过程性能指数（考虑偏移）
        },
        "is_in_control": true,
        "out_of_control_points": [],
        "warnings": [
            {
                "type": "TREND_WARNING",
                "message": "连续5点呈上升趋势，请关注"
            }
        ]
    }
}
```

---

### 5.3 不良品分析

**接口**: `POST /production/defect-analysis`

**描述**: 创建不良品分析记录

**权限**: `production:quality:analyze`

**请求体**:
```json
{
    "inspection_id": 3001,
    "analyst_id": 22,
    "analysis_date": "2026-02-17T16:00:00",
    "defect_type": "焊接不良",
    "defect_qty": 2,
    "root_cause_analysis": {
        "man": "操作工熟练度不足",
        "machine": "焊接机温度偏高",
        "material": "焊料质量合格",
        "method": "焊接工艺参数需优化",
        "measurement": "测量设备正常",
        "environment": "车间温度偏高"
    },
    "related_equipment_id": 12,
    "related_worker_id": 15,
    "corrective_action": "1. 调整焊接温度至350℃\n2. 对操作工进行培训\n3. 优化焊接参数",
    "preventive_action": "1. 每周检查焊接机温度校准\n2. 定期组织培训\n3. 制定标准操作规程",
    "responsible_person_id": 8,
    "due_date": "2026-02-20T17:00:00"
}
```

**响应示例**:
```json
{
    "code": 201,
    "message": "不良分析创建成功",
    "data": {
        "id": 2001,
        "analysis_no": "DA-2026021701",
        "inspection_id": 3001,
        "analyst_name": "刘分析员",
        "defect_type": "焊接不良",
        "defect_qty": 2,
        "root_causes": ["man", "machine", "method", "environment"],
        "corrective_action": "1. 调整焊接温度至350℃\n2. 对操作工进行培训\n3. 优化焊接参数",
        "responsible_person": "李主管",
        "due_date": "2026-02-20T17:00:00",
        "status": "OPEN",
        "created_at": "2026-02-17T16:15:00"
    }
}
```

---

### 5.4 质量预警规则

**接口**: `POST /production/quality-alert-rules`

**描述**: 创建质量预警规则

**权限**: `production:quality:alert:manage`

**请求体**:
```json
{
    "rule_name": "焊接不良率预警",
    "alert_type": "DEFECT_RATE",
    "target_material_id": null,  // null表示全局
    "target_process_id": 5,
    "threshold_value": 5.0,  // 5%
    "threshold_operator": "GT",  // GT/GTE/LT/LTE/EQ
    "time_window_hours": 24,
    "min_sample_size": 30,
    "alert_level": "WARNING",  // INFO/WARNING/CRITICAL
    "notify_users": [8, 20, 22],
    "notify_channels": ["EMAIL", "SMS"],
    "enabled": true
}
```

**响应示例**:
```json
{
    "code": 201,
    "message": "预警规则创建成功",
    "data": {
        "id": 101,
        "rule_no": "QAR-001",
        "rule_name": "焊接不良率预警",
        "alert_type": "DEFECT_RATE",
        "threshold_value": 5.0,
        "alert_level": "WARNING",
        "enabled": true,
        "created_at": "2026-02-17T16:30:00"
    }
}
```

---

## 6. 统计分析API

### 6.1 生产进度统计

**接口**: `GET /production/statistics/progress`

**描述**: 获取生产进度统计数据

**权限**: `production:statistics:view`

**请求参数**:
```typescript
{
    workshop_id?: number;
    start_date?: string;
    end_date?: string;
    group_by?: string;  // day/week/month
}
```

**响应示例**:
```json
{
    "code": 200,
    "message": "Success",
    "data": {
        "time_range": {
            "start": "2026-02-01",
            "end": "2026-02-17"
        },
        "overall_statistics": {
            "total_orders": 156,
            "completed_orders": 98,
            "in_progress_orders": 42,
            "pending_orders": 16,
            "completion_rate": 62.8,
            "on_time_rate": 85.7,
            "avg_progress": 68.5
        },
        "daily_progress": [
            {
                "date": "2026-02-17",
                "total_orders": 45,
                "completed_orders": 12,
                "completion_rate": 26.7,
                "avg_progress": 58.3
            }
        ],
        "workshop_breakdown": [
            {
                "workshop_id": 1,
                "workshop_name": "车间A",
                "total_orders": 80,
                "completed_orders": 52,
                "completion_rate": 65.0
            }
        ]
    }
}
```

---

### 6.2 产能利用率分析

**接口**: `GET /production/statistics/capacity-utilization`

**描述**: 获取产能利用率统计

**权限**: `production:statistics:view`

**请求参数**:
```typescript
{
    workshop_id?: number;
    start_date?: string;
    end_date?: string;
}
```

**响应示例**:
```json
{
    "code": 200,
    "message": "Success",
    "data": {
        "workshop_id": 1,
        "workshop_name": "车间A",
        "time_range": {
            "start": "2026-02-01",
            "end": "2026-02-17"
        },
        "overall_utilization": {
            "total_capacity_hours": 2720,  // 总产能(小时)
            "used_hours": 2176,             // 已用工时
            "idle_hours": 544,              // 空闲工时
            "utilization_rate": 0.80        // 利用率80%
        },
        "resource_utilization": [
            {
                "resource_type": "WORKER",
                "resource_id": 15,
                "resource_name": "张三",
                "total_hours": 160,
                "used_hours": 145,
                "utilization_rate": 0.906
            },
            {
                "resource_type": "EQUIPMENT",
                "resource_id": 12,
                "resource_name": "自动焊接机-01",
                "total_hours": 160,
                "used_hours": 128,
                "utilization_rate": 0.800
            }
        ],
        "bottlenecks": [
            {
                "resource_type": "EQUIPMENT",
                "resource_id": 8,
                "resource_name": "激光切割机-02",
                "utilization_rate": 0.98,
                "severity": "HIGH",
                "recommendation": "建议增加同类设备或延长工作时间"
            }
        ]
    }
}
```

---

### 6.3 质量统计分析

**接口**: `GET /production/statistics/quality`

**描述**: 获取质量统计数据

**权限**: `production:statistics:view`

**请求参数**:
```typescript
{
    workshop_id?: number;
    process_id?: number;
    start_date?: string;
    end_date?: string;
}
```

**响应示例**:
```json
{
    "code": 200,
    "message": "Success",
    "data": {
        "time_range": {
            "start": "2026-02-01",
            "end": "2026-02-17"
        },
        "overall_quality": {
            "total_inspections": 320,
            "total_inspection_qty": 16000,
            "total_qualified_qty": 15520,
            "total_defect_qty": 480,
            "avg_defect_rate": 3.0,  // 平均不良率%
            "pass_rate": 97.0
        },
        "defect_type_distribution": [
            {
                "defect_type": "焊接不良",
                "count": 180,
                "percentage": 37.5
            },
            {
                "defect_type": "尺寸偏差",
                "count": 150,
                "percentage": 31.25
            },
            {
                "defect_type": "外观不良",
                "count": 150,
                "percentage": 31.25
            }
        ],
        "defect_rate_trend": [
            {
                "date": "2026-02-17",
                "defect_rate": 2.8,
                "inspection_qty": 1200,
                "defect_qty": 34
            }
        ],
        "process_quality_ranking": [
            {
                "process_id": 5,
                "process_name": "组装工序",
                "defect_rate": 1.5,
                "rank": 1
            }
        ]
    }
}
```

---

## 7. 错误码说明

### 7.1 业务错误码

| 错误码 | 说明 |
|--------|------|
| 40001 | 工单不存在 |
| 40002 | 工单状态不允许该操作 |
| 40003 | 工人不存在或无相应技能 |
| 40004 | 设备不可用 |
| 40005 | 报工数量超过计划数量 |
| 40006 | 工时异常（超过12小时或连续7天无休） |
| 40007 | 质检数据不一致 |
| 40008 | 超出规格上下限 |
| 40009 | 排程冲突（资源已占用） |
| 40010 | 优先级超出范围(1-10) |

### 7.2 错误响应示例

```json
{
    "code": 40005,
    "message": "报工数量超过计划数量",
    "detail": "工单WO-2026021601计划数量200，已完成65，本次报工20，累计超过计划数量",
    "timestamp": "2026-02-17T14:05:00",
    "path": "/api/v1/production/work-reports"
}
```

---

## 8. 版本历史

| 版本 | 日期 | 作者 | 说明 |
|------|------|------|------|
| v1.0 | 2026-02-16 | Team 8 | 初始版本 |

---

## 9. 相关文档

- [API调用示例](./02-API调用示例.md)
- [错误码完整列表](./03-错误码说明.md)
- [架构设计](../design/01-架构设计.md)
