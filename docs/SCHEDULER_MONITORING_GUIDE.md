# Scheduler Monitoring & Configuration Guide

## 1. 任务元数据
- **文件**：`app/utils/scheduler_config.py`
- **字段**：`id`、`name`、`module`、`callable`、`cron`、`owner`、`category`、`description`、`enabled`
- **使用方式**：
  1. 调度器启动时读取该列表，只为 `enabled=True` 的任务注册 `cron` 规则。
  2. 新增/修改任务时只需编辑此文件并补充描述、负责人、类别等信息。
  3. 未启用的任务（`enabled=False`）将被跳过并在日志中提示，可用于灰度或临时禁用。

## 2. 统一日志与 Telemetry
- **执行包裹**：`app/utils/scheduler.py` 在注册任务时使用 `_wrap_job_callable` 统一输出结构化日志，包含：
  - `job_id` / `job_name` / `owner` / `category`
  - `event`（`job_run_start`、`job_run_success`、`job_run_failed`）
  - `timestamp`（UTC）与 `duration_ms`
  - `error` 字段（失败时）
- **事件监听**：`job_listener` 仍会在任务完成后写入成功/失败日志，形成“双层”记录，可对接日志平台或 Prometheus exporter。
- **建议指标**：
  - `scheduler_job_duration_ms{job_id}`：从结构化日志中提取
  - `scheduler_job_success_total{job_id}` / `scheduler_job_failed_total`
  - `scheduler_job_last_run_timestamp{job_id}`
- **内存指标**：`app/utils/scheduler_metrics.py` 提供轻量 collector，所有任务成功/失败都会更新计数、耗时与历史分布，并额外统计通知渠道的成功/失败次数；可通过 `/api/v1/scheduler/metrics` 或 `/api/v1/scheduler/metrics/prometheus` 获取。

## 3. 验证脚本
- **脚本**：`python test_scheduled_services.py`
- **校验内容**：
  1. 所有模块/函数是否可导入（依据元数据自动生成列表）
  2. 调度器是否已注册 `EXPECTED_JOBS`（自动同步 `enabled=True` 的任务）
  3. 每个函数是否可调用
- **输出**：列出缺失/额外任务、下一次执行时间，可作为巡检日报。

## 4. 通知链路计划
- **统一出口**：`send_alert_notifications` 按小时执行，先基于 `AlertRecord` 生成 `AlertNotification` 队列，再通过 `NotificationDispatcher` 发送 SYSTEM/EMAIL/WECHAT 等渠道，并按 5/15/30/60 分钟策略自动重试。
- **现状**：
  1. 队列生成：每次最多处理 50 条预警，为每个接收人+渠道创建 `AlertNotification`（状态 `PENDING`）。
  2. 发送流程：一次最多取 100 条待发/失败通知，满足条件后写入 Redis 队列（`notification:dispatch:queue`），由 `scripts/notification_worker.py` 异步消费；若 Redis 不可用则回退为同步派发。成功/失败都会更新 `AlertNotification` 与 metrics。
  3. 渠道适配：系统通知已落地；邮件/企微目前输出日志，可按需替换为真实网关。
- **用户偏好**：`NotificationSettings`（`/api/v1/notifications/settings`）记录每个用户的 system/email/wechat/sms 开关与免打扰时间；`send_alert_notifications` 会在派发阶段读取并尊重这些偏好（无记录则按默认启用 system+email+wechat），若当前处于静默区间则自动把通知延迟到静默结束。
- **后续**：
  - 接入企业微信/邮件/SMS 实际 API，并补充凭证配置。
- 若需更高吞吐，可部署多个 `notification_worker` 实例共同消费 Redis 队列；也可替换为更先进的消息系统（如 RabbitMQ / Kafka）。

### 4.1 通道配置
- `.env` 示例：
  ```
  EMAIL_ENABLED=true
  EMAIL_SMTP_SERVER=smtp.example.com
  EMAIL_SMTP_PORT=587
  EMAIL_USERNAME=bot@example.com
  EMAIL_PASSWORD=your-password
  EMAIL_FROM="Project Bot <bot@example.com>"

  WECHAT_ENABLED=true
  WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxxx
  ```
- 若关闭某通道，只需将 `*_ENABLED` 设为 `false` 或不配置即可；`NotificationDispatcher` 会抛错并在 metrics 中计入失败。

## 5. Dashboard 设计蓝图
- **数据源**：收集结构化日志 + `test_scheduled_services.py` 输出。
- **建议面板**：
  1. **任务运行表**：展示 job_id、owner、最近运行状态、耗时 P95。
  2. **告警热力图**：统计一天内失败次数，阈值报警。
  3. **启停控制**：增加 “enabled” 状态展示，与元数据文件联动。
  4. **通知链路监控**：展示 `send_alert_notifications` 成功率与外部网关响应时间，可直接消费 `/scheduler/metrics` 中 `notification_channels` 的数据。
  5. **实时指标卡片**：消费 `/scheduler/metrics` 接口 snapshot，快速查看成功/失败次数、最近耗时与各渠道状态。

## 6. 运维 Checklist
1. **每周**：运行验证脚本 → 更新 `docs/BURNDOWN_TRACKING_LOG.md` → 归档结果。
2. **每次改动**：仅需编辑 `scheduler_config.py` + 编写任务函数 → 运行脚本 → 部署。
3. **告警处理**：监控平台捕获 `job_run_failed` 日志后，联系 owner 并在 `docs/RISK_REGISTER.md` 登记。

## 7. 通知通道告警配置
- **数据来源**：`/api/v1/scheduler/metrics` 会返回 `notification_channels` 数组，字段包含 `channel / success_count / failure_count`。Prometheus 抓取 `/metrics/prometheus` 时也会获得 `scheduler_notification_success_total` 与 `scheduler_notification_failure_total`。
- **Grafana / Prometheus**：
  1. 在 Prometheus 中创建记录规则：  
     `rate(scheduler_notification_failure_total{channel="WECHAT"}[5m])`、`rate(scheduler_notification_success_total{channel="WECHAT"}[5m])`。  
  2. 定义告警条件：`failure_rate > 0 AND success_rate == 0`（表示连续失败），或 `failure_rate / (success_rate + 1) > 0.3`（失败率超过 30%）。
  3. 告警标签中带上 `channel`，便于路由给对应 owner。
- **日志/可视化**：在仪表盘新增“通知通道”面板，展示每个 channel 的成功/失败累计、最近 24h 成功率（可通过 `increase()` 计算），实现可视化。
- **自动化响应**：一旦告警触发，按以下步骤处理：  
  1. 在 `/api/v1/scheduler/metrics` 核对实时数据，确认是否单通道异常。  
  2. 结合 `scheduler.log` 中 `NotificationDispatcher` 输出或 `AlertNotification` 的 `error_message` 定位根因。  
  3. 若为外部网关不可达，可临时在 `scheduler_config.py` 中将对应 channel 置为 `enabled=False`，同时通知业务方改走系统通知。
- **附加建议**：  
  - 为不同 channel 设定 SLA 阈值（如失败率 <5%），出现连续 N 次失败自动升级。  
  - 将 `/scheduler/metrics` 的 JSON 结果通过脚本推送到企业微信，方便值班人员无需登录监控系统也能看到通道状态。

按此流程操作即可实现“配置化 + 观测化 + 可回溯”的后台定时服务体系，为后续的通知链路与 Dashboard 接入提供稳定地基。
### 4.2 Worker 管理
- 启动：`python scripts/notification_worker.py`
- 依赖：需要配置 `REDIS_URL`、数据库连接和相关通知通道凭证。
- 监控：可在监控平台中检查队列长度（`LLEN notification:dispatch:queue`）和 `scheduler_notification_*` 指标；若 worker 持续失败，应查看日志与 Redis 状态。
