# 工时提醒自动化系统 - 配置指南

## 概述

工时提醒自动化系统提供全面的工时填报监控、异常检测和自动提醒功能，帮助团队及时完成工时填报，及时发现和处理异常工时。

### 主要功能

1. **未填报工时检测** - 每日自动检测未填报工时的员工
2. **审批超时提醒** - 提醒审批人处理超时的工时审批
3. **异常工时检测** - 检测5种异常工时情况
4. **周末/节假日工时提醒** - 提醒周末和节假日的工时填报
5. **同步失败提醒** - 提醒工时数据同步失败的情况

## 数据模型

### 1. 提醒规则配置 (TimesheetReminderConfig)

存储提醒规则的配置信息。

| 字段 | 类型 | 说明 |
|------|------|------|
| rule_code | String | 规则编码（唯一） |
| rule_name | String | 规则名称 |
| reminder_type | Enum | 提醒类型 |
| rule_parameters | JSON | 规则参数 |
| apply_to_departments | JSON | 适用部门ID列表 |
| apply_to_roles | JSON | 适用角色ID列表 |
| apply_to_users | JSON | 适用用户ID列表 |
| notification_channels | JSON | 通知渠道（SYSTEM/EMAIL/WECHAT） |
| remind_frequency | String | 提醒频率 |
| max_reminders_per_day | Integer | 每日最大提醒次数 |
| priority | String | 优先级 |
| is_active | Boolean | 是否启用 |

### 2. 提醒记录 (TimesheetReminderRecord)

存储每次提醒的详细记录。

| 字段 | 类型 | 说明 |
|------|------|------|
| reminder_no | String | 提醒编号 |
| reminder_type | Enum | 提醒类型 |
| user_id | Integer | 接收人ID |
| title | String | 提醒标题 |
| content | Text | 提醒内容 |
| status | Enum | 状态（PENDING/SENT/READ/DISMISSED/RESOLVED） |
| notification_channels | JSON | 已发送的通知渠道 |
| sent_at | DateTime | 发送时间 |
| dismissed_at | DateTime | 忽略时间 |
| resolved_at | DateTime | 解决时间 |

### 3. 异常工时记录 (TimesheetAnomalyRecord)

存储检测到的异常工时详情。

| 字段 | 类型 | 说明 |
|------|------|------|
| timesheet_id | Integer | 工时记录ID |
| anomaly_type | Enum | 异常类型 |
| description | Text | 异常描述 |
| anomaly_data | JSON | 异常数据 |
| severity | String | 严重程度 |
| is_resolved | Boolean | 是否已解决 |
| resolved_at | DateTime | 解决时间 |

## 提醒类型

### 1. MISSING_TIMESHEET (未填报工时)

**检测规则**：每日检查是否填报前一天的工时

**规则参数示例**：
```json
{
    "check_days_ago": 1,
    "remind_time": "09:00"
}
```

**提醒内容**：
```
标题：工时填报提醒：2024-02-13
内容：您还未填报 2024年02月13日 的工时，请及时填报。
```

### 2. APPROVAL_TIMEOUT (审批超时)

**检测规则**：检查提交超过指定天数仍未审批的工时

**规则参数示例**：
```json
{
    "timeout_days": 3
}
```

**提醒内容**：
```
标题：工时审批超时提醒
内容：您有工时记录提交已超过3天未审批，请及时处理。
```

### 3. ANOMALY_TIMESHEET (异常工时)

包含5种异常检测规则：

#### 3.1 单日工时 > 12小时 (DAILY_OVER_12)

```python
# 规则：单日总工时超过12小时
threshold = 12.0  # 小时
severity = 'WARNING'
```

#### 3.2 单日工时无效 (DAILY_INVALID)

```python
# 规则：单日总工时 < 0 或 > 24
min_hours = 0
max_hours = 24
severity = 'ERROR'
```

#### 3.3 周工时 > 60小时 (WEEKLY_OVER_60)

```python
# 规则：一周（7天）总工时超过60小时
threshold = 60.0  # 小时
severity = 'WARNING'
```

#### 3.4 连续7天无休息 (NO_REST_7DAYS)

```python
# 规则：连续7天都有工时记录
consecutive_days = 7
severity = 'WARNING'
```

#### 3.5 工时与进度不匹配 (PROGRESS_MISMATCH)

```python
# 规则：
# 1. 填报超过4小时但进度未变化
# 2. 填报超过8小时但进度增加少于10%
severity = 'INFO'
```

### 4. WEEKEND_WORK (周末工时)

**检测规则**：检测周末（周六、周日）的工时填报

### 5. HOLIDAY_WORK (节假日工时)

**检测规则**：检测法定节假日的工时填报

### 6. SYNC_FAILURE (同步失败)

**检测规则**：检测工时数据同步失败的情况

## 配置步骤

### 1. 创建提醒规则

```bash
POST /api/v1/timesheet/reminders/configure
```

**请求示例**：

```json
{
    "rule_code": "DAILY_MISSING_REMINDER",
    "rule_name": "每日工时填报提醒",
    "reminder_type": "MISSING_TIMESHEET",
    "rule_parameters": {
        "check_days_ago": 1,
        "remind_time": "09:00"
    },
    "apply_to_departments": [1, 2, 3],
    "notification_channels": ["SYSTEM", "EMAIL"],
    "remind_frequency": "ONCE_DAILY",
    "max_reminders_per_day": 1,
    "priority": "NORMAL"
}
```

### 2. 配置定时任务

系统内置定时任务配置：

| 任务 | Cron表达式 | 执行时间 | 说明 |
|------|-----------|---------|------|
| 未填报工时检测 | 0 9 * * * | 每天9:00 | 检查昨天未填报工时 |
| 审批超时检测 | 0 11,15 * * * | 每天11:00和15:00 | 检查审批超时 |
| 异常工时检测 | 0 14 * * * | 每天14:00 | 检测各类异常工时 |
| 周工时提醒 | 0 10 * * 1 | 每周一10:00 | 提醒上周工时 |

### 3. 配置通知渠道

#### 3.1 邮件通知配置

在环境变量中配置SMTP信息：

```env
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=your_password
SMTP_FROM=noreply@example.com
SMTP_TLS=true
```

#### 3.2 企业微信通知配置

在环境变量中配置企业微信信息：

```env
WECHAT_CORP_ID=your_corp_id
WECHAT_CORP_SECRET=your_corp_secret
WECHAT_AGENT_ID=1000001
```

用户需要绑定企业微信ID（在用户表中设置 wechat_user_id 字段）。

## API接口使用

### 1. 配置提醒规则

```bash
# 创建规则
POST /api/v1/timesheet/reminders/configure

# 更新规则
PUT /api/v1/timesheet/reminders/configure/{config_id}

# 查询规则列表
GET /api/v1/timesheet/reminders/configure?reminder_type=MISSING_TIMESHEET&is_active=true
```

### 2. 查询待处理提醒

```bash
GET /api/v1/timesheet/reminders/pending?reminder_type=MISSING_TIMESHEET&priority=HIGH
```

### 3. 查询提醒历史

```bash
GET /api/v1/timesheet/reminders/history?start_date=2024-02-01&end_date=2024-02-14
```

### 4. 忽略提醒

```bash
POST /api/v1/timesheet/reminders/{reminder_id}/dismiss
{
    "reason": "已手动填报工时"
}
```

### 5. 查询异常记录

```bash
GET /api/v1/timesheet/reminders/anomalies?anomaly_type=DAILY_OVER_12&is_resolved=false
```

### 6. 解决异常

```bash
POST /api/v1/timesheet/reminders/anomalies/{anomaly_id}/resolve
{
    "resolution_note": "已修正工时数据"
}
```

### 7. 查询统计信息

```bash
# 提醒统计
GET /api/v1/timesheet/reminders/statistics

# Dashboard（综合统计）
GET /api/v1/timesheet/reminders/dashboard
```

## 权限控制

系统使用以下权限控制访问：

| 权限代码 | 说明 |
|---------|------|
| timesheet:reminder:config | 配置提醒规则 |
| timesheet:reminder:view | 查看提醒信息 |
| timesheet:reminder:dismiss | 忽略提醒 |
| timesheet:reminder:resolve | 解决异常 |

## 通知模板自定义

可以在规则配置中自定义通知模板：

```json
{
    "notification_template": "您好 {{user_name}}，您还未填报 {{target_date}} 的工时，请及时填报。"
}
```

支持的变量：
- `{{user_name}}` - 用户姓名
- `{{target_date}}` - 目标日期
- `{{hours}}` - 工时
- `{{project_name}}` - 项目名称
- 更多变量根据提醒类型而定

## 最佳实践

### 1. 提醒频率控制

建议配置：
- 未填报工时：每天1次（早上9点）
- 审批超时：每天2次（上午11点、下午3点）
- 异常工时：每天1次（下午2点）

### 2. 优先级设置

- **URGENT** - 严重异常（如无效工时数据）
- **HIGH** - 重要提醒（如审批超时、周工时超标）
- **NORMAL** - 常规提醒（如日常未填报）
- **LOW** - 信息提示（如进度不匹配）

### 3. 适用范围配置

精确配置适用范围可以避免不必要的提醒：

```json
{
    "apply_to_departments": [1, 2, 3],  // 只适用于技术部门
    "apply_to_roles": [5, 6],           // 只适用于工程师角色
    "apply_to_users": []                // 不指定具体用户
}
```

### 4. 通知渠道组合

根据紧急程度选择通知渠道：

- 常规提醒：`["SYSTEM"]`
- 重要提醒：`["SYSTEM", "EMAIL"]`
- 紧急提醒：`["SYSTEM", "EMAIL", "WECHAT"]`

## 故障排查

### 1. 提醒未发送

检查项：
- 规则是否启用（is_active=true）
- 用户是否在适用范围内
- 是否达到每日提醒次数上限
- 定时任务是否正常运行

### 2. 邮件发送失败

检查项：
- SMTP配置是否正确
- 用户是否配置了邮箱
- 邮件服务器是否可访问

### 3. 异常检测不准确

检查项：
- 工时记录的status字段（已取消的记录会被排除）
- 日期范围是否正确
- 是否有重复的异常记录

## 审计日志

所有提醒相关的操作都会记录审计日志：

- 创建/更新规则配置
- 创建/发送提醒
- 忽略/解决提醒
- 创建/解决异常

可以通过审计日志追溯所有操作历史。

## 性能优化

### 1. 批量处理

系统支持批量发送提醒，提高效率：

```python
notification_sender.send_batch_reminders(reminders, channels)
```

### 2. 数据库索引

已为以下字段创建索引：
- user_id
- reminder_type
- status
- sent_at
- detected_at

### 3. 异常检测优化

- 按用户ID分组查询，减少全表扫描
- 使用日期范围限制查询范围
- 避免重复检测已存在的异常

## 扩展开发

### 1. 自定义异常检测规则

继承 `TimesheetAnomalyDetector` 类并实现自定义检测方法：

```python
class CustomAnomalyDetector(TimesheetAnomalyDetector):
    def detect_custom_anomaly(self, ...):
        # 自定义检测逻辑
        pass
```

### 2. 自定义通知渠道

继承 `NotificationSender` 类并实现自定义通知方法：

```python
class CustomNotificationSender(NotificationSender):
    def _send_custom_notification(self, reminder, user):
        # 自定义通知逻辑
        pass
```

### 3. 自定义提醒规则

通过 API 创建自定义规则配置，系统会自动应用。

## 常见问题

**Q: 如何临时停止某个规则的提醒？**

A: 更新规则配置，设置 `is_active=false`

**Q: 如何批量忽略某类提醒？**

A: 使用批量操作API，或者调整规则的适用范围

**Q: 异常检测的阈值可以调整吗？**

A: 可以，在规则参数中配置不同的阈值

**Q: 如何查看某个用户的所有提醒？**

A: 使用 `/api/v1/timesheet/reminders/history?user_id=xxx`

**Q: 提醒编号的规则是什么？**

A: 格式为 `{前缀}{日期时间}{序号}`，前缀根据提醒类型而定（RM/RA/RN/RW/RH/RS）
