# 后台定时服务梳理（2026-01）

## 1. 调度器概览
- **加载方式**：在 FastAPI `startup` 钩子中根据 `ENABLE_SCHEDULER` 环境变量启动（`app/main.py:12-27`），默认开启，关闭需显式设置。
- **运行框架**：`APScheduler` + `MemoryJobStore` + `ThreadPoolExecutor(5)`，统一设置 `coalesce=True / max_instances=1 / misfire_grace_time=300`，并注册事件监听记录成功/失败（`app/utils/scheduler.py:17-57`）。
- **任务配置**：所有元数据集中在 `app/utils/scheduler_config.py`，共 **32 个启用任务**（含 ECN），支持 owner、类别、描述、启停状态等字段，调度器按该文件自动注册。
- **统一日志/指标**：`_wrap_job_callable` 为每个任务输出结构化 start/success/fail 日志（含耗时），并将结果写入内存指标收集器；`job_listener` 继续输出 APS 级别的成功/失败事件。
- **测试/验证**：`test_scheduled_services.py` 现已直接读取元数据，核对任务注册数量、导入情况与函数可调用性，结果用于运维巡检。

## 2. 任务清单

### 2.1 项目健康 & 问题治理
| 序号 | Job ID / 函数 | Cron | 目的 & 依赖 | 监控记录 |
| --- | --- | --- | --- | --- |
| 1 | `calculate_project_health` | hourly `:00` | 调用 `HealthCalculator` 批量更新项目健康度；依赖项目表及指标字段 | `print + logger`，无指标 |
| 2 | `daily_health_snapshot` | 02:00 | 为活跃项目生成每日快照（`ProjectHealthSnapshot`） | 仅 `print` |
| 3 | `daily_spec_match_check` | 09:00 | 扫描采购订单/BOM 与规格要求的匹配度，使用 `SpecMatchService` | 汇总后 `print`，无耗时统计 |
| 4 | `sales_reminder_scan` | 09:00 调度外 | 提醒销售里程碑/收款计划（依赖 `sales_reminder_service`） | `logger + print` |
| 5 | `check_overdue_issues` | hourly `:00` | 根据 `Issue` 表发出逾期预警 | `print` + 手工 SQL |
| 6 | `check_blocking_issues` | hourly `:05` | 标记阻塞类问题 | 同上 |
| 7 | `check_timeout_issues` | 01:00 | 问题超时升级（含责任人升级） | `print`，无通知重试 |
| 8 | `daily_issue_statistics_snapshot` | 03:00 | 统计问题趋势写入 `IssueStatisticsSnapshot` | `print` |
| 9 | `check_milestone_alerts` | 08:00 | 项目里程碑超期检测 | `print` |
|10 | `check_milestone_risk_alerts` | 08:10 | 风险版里程碑检测（多维规则） | `print` |
|11 | `check_cost_overrun_alerts` | 10:00 | 项目成本超支检测（`ProjectCost`） | `print` |
|12 | `check_workload_overload_alerts` | 11:00 | 人力负荷超限检测（工时/排班） | `print` |
|13 | `calculate_progress_summary` | hourly `:00` | 进度汇总缓存，供看板使用 | `print` |

### 2.2 生产、缺料与运营 P0 任务
| 序号 | Job ID / 函数 | Cron | 目的 & 依赖 | 监控记录 |
| --- | --- | --- | --- | --- |
|14 | `generate_shortage_alerts` | 07:00 | 依据缺料数据生成预警，写入 `AlertRecord` | `print`，通知通道待补全 |
|15 | `check_task_delay_alerts` | hourly `:00` | 任务延期预警（项目计划、工单） | `print` |
|16 | `check_production_plan_alerts` | 11:00 | 生产计划偏差预警 | `print` |
|17 | `check_work_report_timeout` | hourly `:00` | 报工超时提醒（依赖报工表） | `print` |
|18 | `daily_kit_check` | 06:00 | 每日齐套分析（BOM、库存、采购） | `print` |
|19 | `check_delivery_delay` | 14:00 | 到货延迟检查（采购、收货） | `print` |
|20 | `check_task_deadline_reminder` | hourly `:00` | 任务到期提醒，写提醒队列 | `print` |
|21 | `check_outsourcing_delivery_alerts` | 15:00 | 外协交期风险预警 | `print` |
|22 | `_calculate_production_daily_stats` | 内部 | 生产日报统计函数，供任务 23 调用 | 仅内部调用 |
|23 | `generate_production_daily_reports` | 05:00 | 生成生产日报记录、推送汇总 | `print` |
|24 | `generate_shortage_daily_report` | 05:15 | 缺料日报生成，供 API 查询 | `print` |
|25 | `generate_job_duty_tasks` | 04:00 | 岗位职责任务派发，写任务表 | `print` |
|26 | `daily_health_snapshot` | (见 2.1) | - | - |
|27 | `run_ecn_scheduler` | 09:00 | 调用 `app/services/ecn_scheduler.run_ecn_scheduler` 处理 ECN 超时 | `print` |
|28 | `daily_kit_check` | (见 18) | - | - |

### 2.3 商务 / 财务 / 售前扩展
| 序号 | Job ID / 函数 | Cron | 目的 & 依赖 | 监控记录 |
| --- | --- | --- | --- | --- |
|29 | `check_payment_reminder` | 09:30 | 依据收款计划推送提醒（商务/财务） | `print` |
|30 | `check_overdue_receivable_alerts` | 10:30 | 逾期应收预警 | `print` |
|31 | `check_alert_escalation` | hourly `:10` | 对未处理的预警升级级别/通知 | `print` |
|32 | `check_opportunity_stage_timeout` | 15:30 | 商机阶段超时提醒 | `print` |
|33 | `check_presale_workorder_timeout` | 16:00 | 售前工单超时提醒 | `print` |
|34 | `check_issue_timeout_escalation` | 01:30 | 第二层问题超时升级（与 7 区分） | `print` |
|35 | `check_equipment_maintenance_reminder` | 08:30 | 设备保养计划提醒 | `print` |
|36 | `send_alert_notifications` | hourly `:15` | 汇聚待通知事件，生成 `AlertNotification` 队列并通过系统/企微/邮件渠道发送（含重试） | `logger + metrics` |
|37 | `calculate_monthly_labor_cost` | 每月1号 02:00 | 计算月度工时成本（自动执行） | `print` |
|38 | `sales_reminder_scan` | 09:00 | 扫描销售里程碑、收款计划等提醒事项 | `print` |

> 说明：所有任务默认通过 `with get_db_session()` 访问数据库，并以 `print` 或局部 `logger` 输出；尚未统一结构化日志或指标。

## 3. 差距与风险
1. **监控深化**：虽然已有统一日志，但尚未落地 metrics/exporter，需要结合日志平台或 Prometheus 做进一步可视化。
2. **通知链路对接**：系统通道与队列/重试机制已落地，但企业微信 / 邮件仍为占位实现，后续需接入真实网关并补充凭证管理、worker 监控。
3. **配置治理**：元数据集中化后，需要建立变更流程与 code review checklist，避免误改 Cron 或 owner 信息。
4. **故障恢复能力**：若任务抛异常，目前仍依赖日志追踪，缺少自动重试/熔断策略，也未对执行耗时设置 SLA 阈值。
5. **依赖明确性**：虽然元数据包含 `category/description`，但尚未沉淀成可视化对照表供业务侧查阅，排障成本仍可优化。

## 4. 建议的后续动作
1. **指标落地**：基于结构化日志导出 metrics（成功率、耗时、最近运行时间），并在监控平台构建警报规则。
2. **通知链路落地**：将现有 dispatcher 与企业微信 / 邮件 / SMS 真正打通，并在失败 case 中触发报警、监控队列长度/worker 健康。
3. **配置治理**：为 `scheduler_config.py` 建立 review checklist 和文档化流程（见 `docs/SCHEDULER_MONITORING_GUIDE.md`）。
4. **运行仪表盘**：结合 `docs/MILESTONE_CHART.md` 的节奏建立 Dashboard，展示任务运行趋势、失败率，供 PMO/运维查看。
5. **SLA / 重试策略**：为关键任务设定最大耗时与失败阈值，并在任务函数中增加按需重试或熔断逻辑；通知通道已支持退避和用户免打扰，可继续扩展至其他关键任务。

## 5. 验证流程
1. 运行 `python test_scheduled_services.py`：
   - `test_imports` 会按元数据自动校验所有模块/函数导入情况。
   - `test_scheduler_config` 会初始化调度器、对比 `EXPECTED_JOBS`（32 个启用任务），输出缺失/多余清单及下次执行时间。
   - “服务函数”检查涵盖所有可调用入口（含 ECN 调度器），确保代码入口存在。
2. 观察应用日志：
   - `_wrap_job_callable` 在执行前/后输出结构化日志（含 start/stop/duration）。
   - `job_listener` 输出 APS 层级的 success/fail 事件，失败日志附 `error` 字段，可直接用于报警。

更多监控、通知与看板设计细节参见《docs/SCHEDULER_MONITORING_GUIDE.md》。

执行完上述动作后，可认为“后台定时服务梳理”阶段完成，为后续的性能优化与自动化恢复打下基础。
