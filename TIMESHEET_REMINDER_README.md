# 工时提醒自动化系统

## 📋 项目简介

工时提醒自动化系统是一个完整的工时管理辅助工具，提供自动检测、智能提醒和异常预警功能。

## ✨ 主要功能

### 1. 提醒类型（6种）

| 类型 | 说明 | 检测频率 |
|------|------|---------|
| 未填报工时 | 每日检测未填报工时 | 每天9:00 |
| 审批超时 | 检测超时未审批的工时 | 每天11:00, 15:00 |
| 异常工时 | 检测5种异常情况 | 每天14:00 |
| 周末工时 | 检测周末工作 | 可配置 |
| 节假日工时 | 检测节假日工作 | 可配置 |
| 同步失败 | 检测数据同步失败 | 可配置 |

### 2. 异常检测规则（5种）

- ✅ **单日工时>12小时** - 检测过度加班
- ✅ **单日工时<0或>24** - 检测无效数据
- ✅ **周工时>60小时** - 检测周过度加班
- ✅ **连续7天无休息** - 检测连续工作
- ✅ **工时与进度不匹配** - 检测填报质量

### 3. 通知渠道（3种）

- 📱 **系统通知** - 登录系统可见
- 📧 **邮件通知** - SMTP邮件发送
- 💬 **企业微信** - 企业微信推送

### 4. 管理功能

- 提醒规则配置
- 待处理提醒查询
- 提醒历史查询
- 异常记录管理
- 统计Dashboard

## 🚀 快速开始

### 1. 数据库迁移

```bash
# 执行迁移
alembic upgrade head
```

### 2. 初始化规则配置

```bash
# 创建默认规则
python scripts/init_reminder_rules.py
```

### 3. 配置环境变量

```env
# 邮件配置
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@example.com
SMTP_PASSWORD=your_password

# 企业微信配置
WECHAT_CORP_ID=your_corp_id
WECHAT_CORP_SECRET=your_corp_secret
WECHAT_AGENT_ID=1000001
```

### 4. 运行验证

```bash
# 验证核心功能
python verify_timesheet_reminder.py

# 运行单元测试
pytest tests/test_timesheet_reminder.py -v
```

### 5. 启动服务

```bash
# 启动FastAPI服务
python -m uvicorn app.main:app --reload

# 定时任务会自动运行
```

## 📁 文件结构

```
app/
├── models/
│   └── timesheet_reminder.py          # 数据模型
├── services/
│   └── timesheet_reminder/
│       ├── __init__.py
│       ├── reminder_manager.py        # 提醒管理器
│       ├── anomaly_detector.py        # 异常检测器
│       └── notification_sender.py     # 通知发送器
├── api/v1/endpoints/
│   └── timesheet_reminders.py         # API接口
└── schemas/
    └── timesheet_reminder.py          # Schema定义

docs/
├── TIMESHEET_REMINDER_GUIDE.md        # 配置指南
├── TIMESHEET_REMINDER_USER_MANUAL.md  # 用户手册
└── TIMESHEET_REMINDER_IMPLEMENTATION.md # 实现报告

tests/
└── test_timesheet_reminder.py         # 单元测试

scripts/
└── init_reminder_rules.py             # 初始化脚本

migrations/versions/
└── 20260214185031_add_timesheet_reminder_tables.py  # 数据库迁移
```

## 🔌 API接口

### 基础URL

```
http://localhost:8000/api/v1/timesheet/reminders
```

### 主要接口

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | /configure | 配置提醒规则 |
| PUT | /configure/{id} | 更新提醒规则 |
| GET | /configure | 获取规则列表 |
| GET | /pending | 待处理提醒 |
| GET | /history | 提醒历史 |
| POST | /{id}/dismiss | 忽略提醒 |
| POST | /{id}/read | 标记已读 |
| GET | /anomalies | 异常记录列表 |
| POST | /anomalies/{id}/resolve | 解决异常 |
| GET | /statistics | 提醒统计 |
| GET | /dashboard | Dashboard |

### 示例请求

#### 配置提醒规则

```bash
curl -X POST "http://localhost:8000/api/v1/timesheet/reminders/configure" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rule_code": "MY_RULE_001",
    "rule_name": "我的提醒规则",
    "reminder_type": "MISSING_TIMESHEET",
    "rule_parameters": {
      "check_days_ago": 1
    },
    "notification_channels": ["SYSTEM", "EMAIL"],
    "priority": "NORMAL"
  }'
```

#### 查询待处理提醒

```bash
curl -X GET "http://localhost:8000/api/v1/timesheet/reminders/pending?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 忽略提醒

```bash
curl -X POST "http://localhost:8000/api/v1/timesheet/reminders/123/dismiss" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "已手动填报工时"
  }'
```

## 🧪 测试

### 运行单元测试

```bash
# 运行所有测试
pytest tests/test_timesheet_reminder.py -v

# 运行特定测试
pytest tests/test_timesheet_reminder.py::test_detect_daily_over_12 -v

# 生成覆盖率报告
pytest tests/test_timesheet_reminder.py --cov=app/services/timesheet_reminder
```

### 测试覆盖

- ✅ 规则配置测试（3个）
- ✅ 提醒记录测试（4个）
- ✅ 异常检测测试（5个）
- ✅ 异常记录测试（2个）
- ✅ 综合测试（4个）

**总计：18个测试用例**

## 📊 定时任务

系统内置4个定时任务：

```python
# 每天9:00 - 未填报工时检测
@cron("0 9 * * *")
def daily_timesheet_reminder_task():
    pass

# 每天11:00和15:00 - 审批超时检测
@cron("0 11,15 * * *")
def timesheet_approval_timeout_reminder_task():
    pass

# 每天14:00 - 异常工时检测
@cron("0 14 * * *")
def timesheet_anomaly_alert_task():
    pass

# 每周一10:00 - 周工时提醒
@cron("0 10 * * 1")
def weekly_timesheet_reminder_task():
    pass
```

## 🔐 权限控制

系统使用以下权限：

| 权限代码 | 说明 | 适用角色 |
|---------|------|---------|
| timesheet:reminder:config | 配置提醒规则 | 管理员 |
| timesheet:reminder:view | 查看提醒 | 所有用户 |
| timesheet:reminder:dismiss | 忽略提醒 | 所有用户 |
| timesheet:reminder:resolve | 解决异常 | 所有用户 |

## 📖 文档

- **配置指南**: `docs/TIMESHEET_REMINDER_GUIDE.md`
  - 系统概述和数据模型
  - 详细配置步骤
  - API接口文档
  - 最佳实践和故障排查

- **用户手册**: `docs/TIMESHEET_REMINDER_USER_MANUAL.md`
  - 功能介绍
  - 操作指南
  - 常见问题解答

- **实现报告**: `docs/TIMESHEET_REMINDER_IMPLEMENTATION.md`
  - 项目概述
  - 技术实现
  - 验收标准对照
  - 后续优化计划

## 🎯 验收标准

| 标准 | 状态 |
|------|------|
| 数据模型完整，支持3种提醒类型 | ✅ 完成（6种） |
| 定时任务可用，每日自动检测 | ✅ 完成 |
| 异常工时检测规则完整（5条） | ✅ 完成 |
| 通知机制可用（邮件/企业微信） | ✅ 完成 |
| 15+测试用例通过 | ✅ 完成（18个） |
| 文档完整（中文） | ✅ 完成 |

## 🔧 技术栈

- **后端框架**: FastAPI 0.100+
- **ORM**: SQLAlchemy 2.0+
- **数据库**: MySQL 8.0+
- **定时任务**: APScheduler
- **测试**: Pytest
- **邮件**: SMTP
- **企业微信**: 企业微信API

## 📝 开发者

**开发时间**: 2026-02-14  
**版本**: v1.0  
**状态**: ✅ 已完成

## 📧 支持

如有问题，请：

1. 查看文档：`docs/`目录
2. 运行验证脚本：`python verify_timesheet_reminder.py`
3. 查看日志：检查应用日志和定时任务日志
4. 联系技术支持

## 📄 License

本项目是内部使用的PMS系统的一部分。

---

**最后更新**: 2026-02-14
