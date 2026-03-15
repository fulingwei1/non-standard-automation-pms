# ITR 服务架构分析

**分析日期**: 2026-03-15  
**分析范围**: `app/services/itr_service.py` + `itr_analytics_service.py`

---

## 📋 核心服务方法

### 1. `itr_service.py` - ITR 流程核心服务

| 方法名 | 功能描述 | 输入参数 | 返回数据 |
|--------|---------|---------|---------|
| `get_ticket_timeline()` | 获取工单完整时间线，整合工单/问题/验收/SLA 数据 | `db`, `ticket_id` | 时间线事件列表（按时间排序） |
| `get_issue_related_data()` | 获取问题关联数据（工单/验收单/子问题） | `db`, `issue_id` | 问题 + 关联工单 + 关联验收 + 关联问题 |
| `get_itr_dashboard_data()` | 获取 ITR 流程看板统计数据 | `db`, `project_id`, `start_date`, `end_date` | 工单/问题/验收/SLA 统计汇总 |

### 2. `itr_analytics_service.py` - ITR 流程分析服务

| 方法名 | 功能描述 | 输入参数 | 返回数据 |
|--------|---------|---------|---------|
| `analyze_resolution_time()` | 分析问题解决时间（平均/中位数/按类型/按紧急度） | `db`, `start_date`, `end_date`, `project_id` | 解决时间统计 + 分类统计 |
| `analyze_satisfaction_trend()` | 分析客户满意度趋势（按月/按类型） | `db`, `start_date`, `end_date`, `project_id` | 满意度统计 + 趋势分析 |
| `identify_bottlenecks()` | 识别流程瓶颈（各阶段停留时间分析） | `db`, `start_date`, `end_date` | 瓶颈列表（按严重程度排序） |
| `analyze_sla_performance()` | 分析 SLA 达成率（响应/解决） | `db`, `start_date`, `end_date`, `policy_id` | SLA 达成率 + 按策略统计 |

---

## 🔗 数据依赖

### 核心模型（Models）

```
┌─────────────────────────────────────────────────────────────┐
│  ServiceTicket (工单)                                        │
│  - id, ticket_no, project_id, customer_id                   │
│  - problem_type, problem_desc, urgency                      │
│  - status (PENDING/IN_PROGRESS/RESOLVED/CLOSED)             │
│  - reported_time, assigned_time, resolved_time              │
│  - timeline (JSON)                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ project_id
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  Issue (问题)                                                │
│  - id, issue_no, category (CUSTOMER)                        │
│  - project_id, acceptance_order_id, related_issue_id        │
│  - status (OPEN/PROCESSING/RESOLVED/CLOSED)                 │
│  - report_date, resolved_at                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ project_id / acceptance_order_id
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  AcceptanceOrder (验收单)                                    │
│  - id, order_no, project_id, acceptance_type                │
│  - status, overall_result                                   │
│  - created_at, customer_signed_at                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  SLAMonitor (SLA 监控)                                       │
│  - id, ticket_id, policy_id                                 │
│  - response_deadline, resolve_deadline                      │
│  - actual_response_time, actual_resolve_time                │
│  - response_status, resolve_status (ON_TIME/OVERDUE)        │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ policy_id
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  SLAPolicy (SLA 策略)                                        │
│  - id, policy_name, policy_code                             │
│  - problem_type, urgency                                    │
│  - response_time_hours, resolve_time_hours                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  CustomerSatisfaction (客户满意度)                           │
│  - id, survey_type, survey_date                             │
│  - overall_score, project_code                              │
│  - status (COMPLETED)                                       │
└─────────────────────────────────────────────────────────────┘
```

### 外部依赖

| 依赖类型 | 模块 | 用途 |
|---------|------|------|
| **Query Filters** | `app.common.query_filters` | `apply_keyword_filter()` 用于关键词搜索 |
| **Database** | `sqlalchemy` | ORM 查询、过滤、聚合 |
| **Datetime** | `datetime` | 时间处理、日期范围过滤 |
| **Typing** | `typing` | 类型注解 (`Dict`, `Any`, `Optional`) |

---

## 🏗️ 服务架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           ITR 服务层 (Services)                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────┐       ┌─────────────────────────────────┐ │
│  │   itr_service.py        │       │   itr_analytics_service.py      │ │
│  │   (核心流程服务)         │       │   (分析服务)                     │ │
│  ├─────────────────────────┤       ├─────────────────────────────────┤ │
│  │ • get_ticket_timeline   │       │ • analyze_resolution_time       │ │
│  │ • get_issue_related_data│       │ • analyze_satisfaction_trend    │ │
│  │ • get_itr_dashboard_data│       │ • identify_bottlenecks          │ │
│  │                         │       │ • analyze_sla_performance       │ │
│  └─────────────────────────┘       └─────────────────────────────────┘ │
│              │                                   │                       │
│              └─────────────────┬─────────────────┘                       │
│                                │                                         │
│                                ▼                                         │
│                    ┌───────────────────────┐                            │
│                    │   SQLAlchemy Session  │                            │
│                    │   (数据库会话)         │                            │
│                    └───────────────────────┘                            │
│                                │                                         │
└────────────────────────────────┼─────────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  ServiceTicket  │   │     Issue       │   │ AcceptanceOrder │
│  (服务工单)      │   │   (问题)        │   │   (验收单)      │
└─────────────────┘   └─────────────────┘   └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│   SLAMonitor    │   │  SLAPolicy      │   │CustomerSatisfaction│
│  (SLA 监控)      │   │  (SLA 策略)      │   │  (客户满意度)    │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

---

## 🔄 数据流向

### 1. 工单时间线查询流程

```
用户请求
   │
   ▼
get_ticket_timeline(ticket_id)
   │
   ├─→ 查询 ServiceTicket (获取工单基本信息 + timeline)
   │
   ├─→ 查询 Issue (通过 project_id + ticket_no 关键词搜索)
   │     └─→ 添加 ISSUE_CREATED / ISSUE_RESOLVED 事件
   │
   ├─→ 查询 AcceptanceOrder (通过 project_id)
   │     └─→ 添加 ACCEPTANCE_CREATED / ACCEPTANCE_SIGNED 事件
   │
   ├─→ 查询 SLAMonitor (通过 ticket_id)
   │     └─→ 添加 SLA_MONITOR_CREATED / SLA_RESPONSE / SLA_RESOLVE 事件
   │
   └─→ 按时间排序所有事件 → 返回完整时间线
```

### 2. 问题关联数据查询流程

```
用户请求
   │
   ▼
get_issue_related_data(issue_id)
   │
   ├─→ 查询 Issue (获取问题基本信息)
   │
   ├─→ 查询 ServiceTicket (通过 project_id, 限 10 条)
   │     └─→ 返回关联工单列表
   │
   ├─→ 查询 AcceptanceOrder (通过 acceptance_order_id 或 project_id)
   │     └─→ 返回关联验收单列表
   │
   ├─→ 查询 Issue.related_issue_id (父问题)
   │
   └─→ 查询 Issue (related_issue_id = 当前 issue_id, 子问题)
         └─→ 返回关联问题列表（父子关系）
```

### 3. 分析服务数据流

```
analyze_resolution_time()
   │
   ├─→ 查询 CLOSED 工单 (含 resolved_time)
   ├─→ 计算解决时间差 (resolved_time - reported_time)
   ├─→ 按 problem_type / urgency 分组统计
   └─→ 返回统计结果 (avg/median/min/max)

analyze_satisfaction_trend()
   │
   ├─→ 查询 COMPLETED 满意度调查
   ├─→ 按月分组计算平均分
   ├─→ 按 survey_type 分组计算平均分
   └─→ 返回趋势数据

identify_bottlenecks()
   │
   ├─→ 计算 PENDING→IN_PROGRESS 时间 (响应时间)
   ├─→ 计算 IN_PROGRESS→RESOLVED 时间 (解决时间)
   ├─→ 计算 RESOLVED→CLOSED 时间 (关闭时间)
   ├─→ 根据阈值判定严重程度 (HIGH/MEDIUM/LOW)
   └─→ 返回瓶颈列表（按严重程度排序）

analyze_sla_performance()
   │
   ├─→ 查询 SLAMonitor 记录
   ├─→ 计算响应达成率 (ON_TIME / total)
   ├─→ 计算解决达成率 (ON_TIME / total)
   ├─→ 按 policy_id 分组统计
   └─→ 返回 SLA 绩效报告
```

---

## 📊 关键业务逻辑

### 1. 时间线整合逻辑
- **多源数据聚合**: 工单 timeline + 问题 + 验收单 + SLA 监控
- **统一事件格式**: 每个事件包含 `type`, `event_type`, `timestamp`, `user`, `description`, `source`
- **时间排序**: 按 `timestamp` 升序排列，形成完整流程视图

### 2. 问题关联逻辑
- **项目维度关联**: 通过 `project_id` 关联工单和验收单
- **问题层级关系**: 通过 `related_issue_id` 支持父子问题
- **关键词搜索**: 使用 `apply_keyword_filter` 在问题描述中搜索工单号

### 3. SLA 统计逻辑
- **双维度监控**: 响应时间 + 解决时间
- **状态枚举**: `ON_TIME` / `OVERDUE` / `WARNING`
- **策略匹配**: 根据问题类型和紧急程度匹配 SLA 策略

### 4. 瓶颈识别逻辑
- **三阶段分析**: 分配响应 → 问题解决 → 工单关闭
- **严重程度判定**:
  - 响应时间 > 24h → HIGH
  - 解决时间 > 72h → HIGH
  - 关闭时间 > 48h → HIGH

---

## ⚠️ 潜在风险点

1. **性能问题**:
   - `get_ticket_timeline()` 未限制关联数据查询数量（issues/acceptance_orders 可能很多）
   - 建议添加 `limit` 限制或使用分页

2. **空指针风险**:
   - `sla_monitor.policy.policy_name` 未检查 `policy` 是否为 `None`
   - 部分时间字段未做 `None` 检查直接调用 `.isoformat()`

3. **数据一致性问题**:
   - 时间线排序依赖 `timestamp` 字段，但部分事件可能缺失时间戳
   - `RESOLVED→CLOSED` 阶段需要从 `timeline` JSON 中解析关闭时间，存在解析失败风险

4. **硬编码阈值**:
   - 瓶颈严重程度的时间阈值（24h/72h/48h）硬编码在代码中
   - 建议配置化或从 SLA 策略中读取

---

## 🔧 建议改进

1. **添加缓存层**: 对看板数据和统计数据进行缓存（Redis）
2. **异步处理**: 时间线整合和数据分析可改为异步任务（Celery）
3. **索引优化**: 确保 `project_id`, `status`, `created_at` 等常用过滤字段有索引
4. **单元测试**: 增加边界条件测试（空数据、大数据量、时间戳缺失等）
5. **API 文档**: 为每个服务方法添加 OpenAPI 文档说明

---

**生成时间**: 2026-03-15 22:45 GMT+8  
**文件路径**: `docs/architecture/itr_service_architecture.md`
