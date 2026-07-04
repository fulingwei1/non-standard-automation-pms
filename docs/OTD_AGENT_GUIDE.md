# OTD 项目交付智能体（Order-to-Delivery Agent）

> 把"项目计划→节点→设计→采购→装配→变更→异常→延期→验收→未关闭事项"11 个维度，
> 串成**每日一份的交付风险预警 + 7 核心指标**，让 AI 每天帮项目经理盯交付。

## 1. 这是什么

非标设备公司最怕"签单时有毛利、交付时被吃光"。OTD 智能体是一个**编排层**——
不新建任何数据表、不改任何字段、不动前端，复用 PMS 已有的风险扫描 / AI / 调度 / 通知
能力，把它们聚合为：

- **每日 07:00 全量扫描**执行中项目（生命周期 S2~S8）的 11 维交付风险
- **HIGH/CRITICAL 自动产出预警**，站内消息 + 邮件推送给项目经理（`Project.pm_id`）
- **AI 一句话归因**：对高风险项目，AI 给出"最该先干预什么"的建议
- **7 核心指标**看板：准时交付率 / 延期天数 / 返工 / 变更 / 毛利偏差 / 验收周期 / 投诉率

## 2. API 端点

| 方法 | 路径 | 用途 | 权限 |
|---|---|---|---|
| GET | `/api/v1/otd/scan` | 全量 OTD 扫描（只读，默认不产预警） | 登录用户 |
| GET | `/api/v1/otd/scan?create_alerts=true` | 全量扫描并对 HIGH/CRITICAL 产预警 | 登录用户 |
| GET | `/api/v1/otd/scan/{project_id}` | 单项目 11 维全景 + AI 归因 | 登录用户 |
| GET | `/api/v1/otd/scan/trend?days=30` | 全局风险趋势（每日各等级项目数 + 维度热力图） | 登录用户 |
| GET | `/api/v1/otd/scan/{project_id}/trend?days=30` | 单项目风险趋势（severity/各维度命中随时间） | 登录用户 |
| GET | `/api/v1/otd/metrics?start_date=&end_date=` | 7 核心指标（默认本季度） | 登录用户 |
| GET | `/api/v1/otd/metrics/{project_id}` | 单项目指标 | 登录用户 |
| POST | `/api/v1/otd/scan/run` | 手动触发完整扫描（含预警产出 + 快照） | PMO/管理员 |
| GET | `/api/v1/otd/thresholds` | 查看 11 维阈值配置 | 登录用户 |
| PUT | `/api/v1/otd/thresholds` | 更新阈值配置（立即生效，无需重启） | PMO/管理员 |

### 返回结构示例（GET /otd/scan）

```json
{
  "code": 200,
  "message": "扫描 16 个项目，发现 16 个有风险，其中 16 个 HIGH/CRITICAL",
  "data": {
    "scanned": 16,
    "with_risk": 16,
    "high_or_critical": 16,
    "alerts_created": 0,
    "projects": [
      {
        "project_id": 9,
        "project_code": "DEMO26-PRJ-0009",
        "name": "...",
        "stage": "S5",
        "progress": 45.0,
        "planned_end": "2026-08-15",
        "severity": "CRITICAL",
        "risk_items": [
          {"dim": "procurement_delay", "label": "采购延期", "severity": "HIGH", "msg": "..."},
          {"dim": "design_not_frozen", "label": "图纸未冻结", "severity": "CRITICAL", "msg": "..."}
        ],
        "suggestion": "优先解决采购延期，联系供应商确认交期并启动替代料寻源"
      }
    ]
  }
}
```

## 3. 11 维风险检测

| # | 维度 | 判定逻辑 | 严重度阈值 | 数据源 |
|---|---|---|---|---|
| 1 | 采购延期 | PO 明细 promised_date 过期且 received_qty < quantity | 7-15天 MEDIUM / 15-30 HIGH / >30 CRITICAL | `purchase_orders` + `purchase_order_items` |
| 2 | 图纸未冻结 ⚠️ | S3+ 阶段项目无通过的 DDR 评审 | S3 MEDIUM / S4 HIGH / S5+ CRITICAL | `technical_reviews`（代理口径） |
| 3 | 客户变更频繁 | ChangeRequest(change_source=CUSTOMER) 近30/90天计数 | 30天≥3 HIGH / ≥5 CRITICAL | `change_requests` |
| 4 | BOM 超预算 | 复用 `BudgetAlertService` | 黄 LOW / 橙 MEDIUM / 红 HIGH | `ProjectBudget` + 成本归集 |
| 5 | 现场调试反复 | Issue(category in ACCEPTANCE/QUALITY/TECHNICAL) 近30天 | ≥3 MEDIUM / ≥5 或阻塞 HIGH | `issues` |
| 6 | 验收资料缺失 | 复用 `ClosureReadinessService`，仅 S6+ 或临近交付(60天内)报 | 临近 HIGH / 否则 MEDIUM | `ProjectDocument` |
| 7 | 回款条件不齐 | PaymentPlan 临近(7天内) 且触发里程碑未完成 | HIGH | `project_payment_plans` |
| 8 | 关键节点延期 | ProjectMilestone(is_key) 逾期未完成 | 1个 HIGH / ≥2个或>30天 CRITICAL | `project_milestones` |
| 9 | 进度滞后 | `calculate_progress_stats` 偏差 | <-15% MEDIUM / <-25% HIGH | `projects.progress_pct` |
| 10 | 毛利偏差 | 复用 `ProfitAnalysisService` 的 margin_gap | <-3% MEDIUM / <-5% HIGH / <-10% CRITICAL | 合同/预算/成本 |
| 11 | 未关闭事项 | 聚合未关闭 Issue/变更/里程碑/验收单 | 有阻塞或≥10 HIGH / ≥5 MEDIUM / 否则 LOW | `issues` + `change_requests` + `project_milestones` + `acceptance_orders` |

> **直接复用 3 个现成 service**：维度 4（BudgetAlertService）、维度 6（ClosureReadinessService）、维度 10（ProfitAnalysisService）。
>
> **维度 11** 对应符哥原文"跟踪未关闭事项"，把分散在各表的"还没关闭"事项聚合为一个风险信号 + 看板字段。

## 3.5 阈值配置化（管理员可热改）

11 维检测的所有阈值（天数/次数/百分比/阶段门禁/状态集合）都存在 `otd_threshold_configs` 表，
管理员通过 `PUT /api/v1/otd/thresholds` 修改，**改完立即生效，下次扫描即用新值，无需重启服务**。

**设计**（照抄项目里已落地的 `MarginAlertConfig` 范式）：
- `is_default=True` 的单行作为运行时配置；DB 无配置时 fallback 到代码默认值（保证首次运行无需手动建配置）
- Numeric 列存数值阈值（如 `procurement_overdue_high_days=15`）
- JSON 列存集合类（`status_sets` 存 issue_closed/change_closed/payment_pending/milestone_completed）
- 自动建表：`_ensure_sqlite_schema` 启动时检测并补建，**无需手写 migration**

**用法示例**：
```bash
# 改采购延期 HIGH 阈值（从 15 天改成 5 天，更严格）
curl -X PUT -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"procurement_overdue_high_days": 5}' \
  http://localhost:8000/api/v1/otd/thresholds

# 查看当前配置
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/otd/thresholds
```

**可配置字段**：scan_limit、stages_in_delivery、各维度的天数/次数/百分比阈值、阶段门禁字符串、状态集合 JSON。详见 `app/models/otd_threshold_config.py`。

## 4. 7 核心指标

| 指标 | 口径 |
|---|---|
| 项目准时交付率 | stage=S9 中 actual_end_date ≤ planned_end_date 占比 |
| 项目延期天数 | 已完成 (actual-planned).days；在途 (today-planned).days |
| 返工次数 ⚠️ | sum(AcceptanceOrderItem.retry_count) —— **代理口径** |
| 变更次数 | ChangeRequest + Ecn 计数（可分客户/内部） |
| 项目毛利偏差 | ProfitAnalysisService 的 margin_gap 均值 |
| 验收周期 | avg((actual_end - actual_start).days) where status=COMPLETED |
| 客户投诉率 | count(feedback_type=COMPLAINT) / 售后反馈总数 |

## 5. ⚠️ 代理口径（首版，未改表）

两个维度因系统无对应字段，首版用代理口径，文档标清，后续可升级：

| 代理项 | 首版口径 | 升级方案（若需精确） |
|---|---|---|
| 图纸冻结（维度2） | TechnicalReview DDR 评审通过 | 新增 `BomItem.freeze_status` 字段 |
| 返工次数（指标3） | AcceptanceOrderItem.retry_count | 新增 `WorkOrder.rework_count` 或返工单表 |

## 6. 调度任务

| 任务 ID | cron | 说明 |
|---|---|---|
| `daily_otd_scan` | 每天 07:00 | 排在 06:00 项目风险计算之后，拿当日最新数据 |

- 失败时返回 `{"status": "error", ...}`，scheduler.py 会真正标失败（非静默）
- 可在 `SchedulerTaskConfig` 表覆盖 cron（热重排）

## 7. 预警产出与推送

- HIGH/CRITICAL 项目 → 创建 `AlertRecord`（`alert_no` 前缀 `OTD-`，`rule_id` 关联系统规则 `OTD_DELIVERY_RISK`）
- **系统规则首次扫描时自动创建**（`is_system=True, target_type=PROJECT`），无需 migration
- 同项目同日去重（避免重复推送）
- 推送走现有 `send_notification_for_alert` → `NotificationDispatcher`，自动推给 `Project.pm_id`（项目经理）
- 通道：站内（必达）+ 邮件（SMTP 配置后）

## 7.5 风险快照与趋势分析

每次扫描（定时任务 / 手动 scan/run）会为每个项目落一条 `OTDRiskSnapshot`，用于趋势分析。

**设计**（照抄项目里已落地的 `ProjectRiskSnapshot` + `ProjectHealthSnapshot` 范式）：
- `otd_risk_snapshots` 表：`project_id + snapshot_date` 同日幂等去重
- 列式冗余 11 个维度的命中标记（`*_hit` Boolean），便于全局聚合
- JSON 字段存完整 `risk_items[]` + 7 指标快照值
- 自动建表（`_ensure_sqlite_schema` 补丁，零 migration）

**两个趋势端点**：
- `GET /otd/scan/trend?days=30` — 全局趋势：每日各 severity 等级的项目数 + 各维度命中项目数热力图（照抄 `risk_analytics.py` 聚合）
- `GET /otd/scan/{project_id}/trend?days=30` — 单项目趋势：连续日期序列 + severity 演化 + 各维度命中 + OTD 预警事件打点（照抄 `HealthTrendService`，含缺日补齐）

**用途**：回答符哥关心的"风险在改善还是恶化"——延期天数趋势、毛利偏差轨迹、某维度命中频率变化。

## 8. 文件清单

**新建：**
- `app/services/otd/__init__.py`
- `app/services/otd/otd_scan_service.py` — 11 维检测 + 批量扫描 + AI 归因 + 预警产出（读配置阈值）
- `app/services/otd/otd_metrics_service.py` — 7 核心指标
- `app/services/otd/threshold_service.py` — 阈值配置加载/更新/兜底
- `app/services/otd/trend_service.py` — 单项目/全局趋势分析
- `app/models/otd_threshold_config.py` — 阈值配置表（自动建表，零 migration）
- `app/models/otd_risk_snapshot.py` — 风险快照表（自动建表，零 migration）
- `app/schemas/otd_threshold.py` — 阈值配置 pydantic schema
- `app/api/v1/endpoints/otd.py` — 7 个扫描/指标/趋势端点
- `app/api/v1/endpoints/otd_thresholds.py` — 阈值配置 GET/PUT 端点
- `app/utils/scheduled_tasks/otd_tasks.py` — 调度入口函数
- `app/utils/scheduler_config/otd.py` — 调度元数据
- `tests/services/test_otd_scan_service.py` — 16 个单测（含第 11 维未关闭事项）
- `tests/services/test_otd_metrics_service.py` — 19 个指标单测（覆盖 7 核心指标口径）
- `tests/services/test_otd_threshold_service.py` — 7 个阈值配置单测
- `tests/services/test_otd_snapshot_trend.py` — 10 个快照/趋势单测
- `tests/api/test_otd_endpoints.py` — 11 个 API 测试
- `tests/api/test_otd_threshold_endpoints.py` — 3 个阈值 API 测试

**修改（登记）：**
- `app/api/v1/api.py` — 注册 `/otd` + `/otd/thresholds` router
- `app/models/__init__.py` — 导入 OtdThresholdConfig（注册到 metadata）
- `app/models/base.py` — `_ensure_sqlite_schema` 加 OTD 表补丁（自动建表）
- `app/utils/scheduled_tasks/__init__.py` — import + SCHEDULED_TASKS + TASK_GROUPS + __all__
- `app/utils/scheduler_config/__init__.py` — 拼进 SCHEDULER_TASKS

## 9. 验收结果

- ✅ 66 个 pytest 全绿（52 service + 14 API，含阈值配置化 + 7 指标口径 + 快照趋势测试）
- ✅ 真实 DB：GET /otd/scan 扫描 16 个执行中项目，全部命中风险维度
- ✅ GET /otd/metrics 返回 7 个指标，数值可追溯
- ✅ GET /otd/scan/{id} 返回单项目全景 + **AI 归因真实工作**（qwen3-coder-plus）
- ✅ POST /otd/scan/run 新建 16 条 AlertRecord，rule_id 非空（NOT NULL 通过）
- ✅ `daily_otd_scan` 注册到 SCHEDULER_TASKS（59 个任务），cron 07:00
- ✅ OTD 系统 rule 自动创建（id=13, is_system=True）
- ✅ 阈值配置化：`otd_threshold_configs` 表自动建（`_ensure_sqlite_schema` 补丁，零 migration）
- ✅ 阈值热改生效：PUT 改 `procurement_overdue_critical_days=999` 后再扫描，采购延期 severity 从全 CRITICAL 变全 LOW（立即生效，无需重启）
- ✅ DB 无配置时 fallback 到代码默认值（首次运行无需手动建配置）
- ✅ 风险快照：`otd_risk_snapshots` 表自动建，scan/run 后落 16 条快照（同日幂等去重）
- ✅ 单项目趋势：severity 演化 + 11 维度命中序列 + 连续日期补齐
- ✅ 全局趋势：每日各等级项目数 + 维度命中热力图（照抄 risk_analytics 聚合）
