# 预警与异常管理模块 Sprint 和 Issue 任务清单

> **文档版本**: v1.0  
> **创建日期**: 2026-01-15  
> **基于**: 预警与异常管理模块完成情况评估  
> **估算单位**: Story Point (SP)，1 SP ≈ 0.5 人天

---

## 一、Issue 快速参考表

| Issue | 标题 | Sprint | 优先级 | 估算 | 负责人 | 状态 |
|-------|------|--------|:------:|:----:|--------|:----:|
| 1.1 | 站内消息通知服务 | Sprint 1 | P0 | 8 SP | Backend | ⬜ |
| 1.2 | 预警通知发送集成 | Sprint 1 | P0 | 6 SP | Backend | ⬜ |
| 1.3 | 通知重试机制 | Sprint 1 | P0 | 5 SP | Backend | ⬜ |
| 1.4 | 预警规则配置页面 | Sprint 1 | P0 | 10 SP | Frontend | ⬜ |
| 1.5 | 预警规则管理API完善 | Sprint 1 | P0 | 5 SP | Backend | ⬜ |
| 2.1 | 统一预警规则引擎框架 | Sprint 2 | P1 | 13 SP | Backend | ⬜ |
| 2.2 | 预警去重机制优化 | Sprint 2 | P1 | 5 SP | Backend | ⬜ |
| 2.3 | 预警自动升级机制 | Sprint 2 | P1 | 8 SP | Backend | ⬜ |
| 2.4 | 预警级别动态提升 | Sprint 2 | P1 | 5 SP | Backend | ⬜ |
| 3.1 | 预警订阅数据模型 | Sprint 3 | P1 | 5 SP | Backend | ⬜ |
| 3.2 | 预警订阅配置API | Sprint 3 | P1 | 6 SP | Backend | ⬜ |
| 3.3 | 预警订阅匹配引擎 | Sprint 3 | P1 | 8 SP | Backend | ⬜ |
| 3.4 | 预警订阅配置页面 | Sprint 3 | P1 | 6 SP | Frontend | ⬜ |
| 4.1 | 预警趋势分析图表 | Sprint 4 | P1 | 8 SP | Full Stack | ⬜ |
| 4.2 | 响应时效分析 | Sprint 4 | P1 | 6 SP | Backend | ⬜ |
| 4.3 | 预警处理效率分析 | Sprint 4 | P1 | 6 SP | Backend | ⬜ |
| 4.4 | 预警报表导出功能 | Sprint 4 | P1 | 5 SP | Backend | ⬜ |
| 5.1 | 企业微信通知集成 | Sprint 5 | P2 | 10 SP | Backend | ⬜ |
| 5.2 | 邮件通知集成 | Sprint 5 | P2 | 8 SP | Backend | ⬜ |
| 5.3 | 短信通知集成（可选） | Sprint 5 | P2 | 6 SP | Backend | ⬜ |
| 6.1 | 预警服务代码重构 | Sprint 6 | P1 | 8 SP | Backend | ⬜ |
| 6.2 | 数据库查询优化 | Sprint 6 | P1 | 5 SP | Backend | ⬜ |
| 6.3 | 定时任务性能优化 | Sprint 6 | P1 | 6 SP | Backend | ⬜ |
| 6.4 | 预警规则配置验证 | Sprint 6 | P1 | 4 SP | Backend | ⬜ |
| 7.1 | 预警模块单元测试 | Sprint 7 | P1 | 8 SP | QA+Backend | ⬜ |
| 7.2 | 预警模块集成测试 | Sprint 7 | P1 | 6 SP | QA+Backend | ⬜ |
| 7.3 | API 文档完善 | Sprint 7 | P1 | 3 SP | Backend | ⬜ |
| 7.4 | 用户使用手册 | Sprint 7 | P1 | 3 SP | Product | ⬜ |

**状态说明**: ⬜ 待开始 | 🚧 进行中 | ✅ 已完成 | ❌ 已取消

---

## 二、Sprint 规划总览

| Sprint | 主题 | 优先级 | 预计工时 | 依赖关系 | 目标 |
|--------|------|:------:|:--------:|---------|------|
| **Sprint 1** | 通知机制与规则配置 | 🔴 P0 | 34 SP | 无 | 核心通知功能和规则配置界面 |
| **Sprint 2** | 规则引擎与升级机制 | 🟡 P1 | 31 SP | Sprint 1 | 统一规则引擎和自动升级 |
| **Sprint 3** | 预警订阅功能 | 🟡 P1 | 25 SP | Sprint 1, 2 | 用户订阅配置和匹配 |
| **Sprint 4** | 统计分析增强 | 🟡 P1 | 25 SP | Sprint 1 | 趋势分析和报表导出 |
| **Sprint 5** | 多渠道通知集成 | 🟢 P2 | 24 SP | Sprint 1 | 企业微信、邮件、短信通知 |
| **Sprint 6** | 性能优化与重构 | 🟡 P1 | 23 SP | Sprint 1-4 | 代码重构和性能优化 |
| **Sprint 7** | 测试与文档完善 | 🟡 P1 | 20 SP | Sprint 1-6 | 单元测试、集成测试、文档 |

**总计**: 182 SP（约 91 人天，按 1 人计算约 4.5 个月，按 2 人计算约 2.3 个月）

---

## 三、Sprint 1: 通知机制与规则配置（P0）

**目标**: 实现站内消息通知服务，完成预警规则配置界面，确保核心功能可用

**预计工时**: 34 SP  
**预计周期**: 2 周

### Issue 1.1: 站内消息通知服务

**优先级**: 🔴 P0  
**估算**: 8 SP  
**负责人**: Backend Team

**描述**:
实现站内消息通知服务，支持预警通知的发送、存储和阅读状态管理。

**验收标准**:
- [ ] 创建 `app/services/notification_service.py` 服务类
- [ ] 实现 `send_alert_notification()` 方法，支持：
  - 创建 `AlertNotification` 记录
  - 设置通知状态为 `PENDING`
  - 记录通知目标用户
- [ ] 实现 `mark_notification_read()` 方法，更新阅读状态
- [ ] 实现 `get_user_notifications()` 方法，获取用户未读通知列表
- [ ] 在预警生成时自动调用通知服务
- [ ] 添加单元测试覆盖通知发送和阅读场景

**技术实现**:
- 文件: `app/services/notification_service.py`
- 依赖: `app/models/alert.py` 中的 `AlertNotification` 模型
- 集成点: `app/utils/scheduled_tasks.py` 中的预警生成服务

**依赖**: 无

---

### Issue 1.2: 预警通知发送集成

**优先级**: 🔴 P0  
**估算**: 6 SP  
**负责人**: Backend Team

**描述**:
将通知服务集成到预警生成流程中，确保预警生成时自动发送通知。

**验收标准**:
- [ ] 在 `generate_shortage_alerts()` 中集成通知发送
- [ ] 在 `check_task_delay_alerts()` 中集成通知发送
- [ ] 在 `check_production_plan_alerts()` 中集成通知发送
- [ ] 在 `check_work_report_timeout()` 中集成通知发送
- [ ] 在 `daily_kit_check()` 中集成通知发送
- [ ] 在 `check_delivery_delay()` 中集成通知发送
- [ ] 在 `check_task_deadline_reminder()` 中集成通知发送
- [ ] 在 `check_outsourcing_delivery_alerts()` 中集成通知发送
- [ ] 在 `check_milestone_risk_alerts()` 中集成通知发送
- [ ] 通知发送失败不影响预警记录创建
- [ ] 添加错误日志记录

**技术实现**:
- 文件: `app/utils/scheduled_tasks.py`
- 调用: `notification_service.send_alert_notification()`
- 错误处理: 使用 try-except 包裹，记录日志但不抛出异常

**依赖**: Issue 1.1

---

### Issue 1.3: 通知重试机制

**优先级**: 🔴 P0  
**估算**: 5 SP  
**负责人**: Backend Team

**描述**:
实现通知发送失败时的重试机制，确保重要通知能够成功送达。

**验收标准**:
- [ ] 在 `AlertNotification` 模型中已有 `retry_count` 和 `next_retry_at` 字段
- [ ] 实现 `retry_failed_notifications()` 定时任务
- [ ] 重试逻辑：
  - 查询状态为 `FAILED` 且 `retry_count < 3` 的通知
  - 检查 `next_retry_at` 是否已到
  - 重新发送通知
  - 更新重试次数和下次重试时间
- [ ] 重试间隔：第1次重试（5分钟后），第2次重试（30分钟后），第3次重试（2小时后）
- [ ] 超过最大重试次数后标记为 `ABANDONED`
- [ ] 注册到定时任务调度器，每小时执行一次
- [ ] 添加单元测试

**技术实现**:
- 文件: `app/utils/scheduled_tasks.py`
- 调度配置: `app/utils/scheduler_config.py`
- 重试策略: 指数退避

**依赖**: Issue 1.1, 1.2

---

### Issue 1.4: 预警规则配置页面

**优先级**: 🔴 P0  
**估算**: 10 SP  
**负责人**: Frontend Team

**描述**:
实现预警规则配置的前端页面，支持规则的创建、编辑、启用/禁用等操作。

**验收标准**:
- [ ] 创建 `AlertRuleManagement.jsx` 页面
- [ ] 规则列表展示：
  - 规则编码、名称、类型
  - 监控对象、检查频率
  - 启用状态（可切换）
  - 操作按钮（编辑、删除）
- [ ] 规则创建/编辑表单：
  - 基本信息（编码、名称、类型、分类）
  - 监控对象配置（对象类型、监控字段）
  - 触发条件配置（条件类型、运算符、阈值）
  - 预警级别配置
  - 通知配置（通知渠道、通知角色/用户）
  - 执行配置（检查频率、启用状态）
- [ ] 规则模板选择功能（从模板快速创建）
- [ ] 表单验证：
  - 规则编码唯一性检查
  - 必填项验证
  - 阈值格式验证
- [ ] 系统预置规则标识和保护（不允许删除）
- [ ] 响应式设计，支持移动端
- [ ] 集成到侧边栏导航

**技术实现**:
- 文件: `frontend/src/pages/AlertRuleManagement.jsx`
- API 调用: `alertApi.getRules()`, `alertApi.createRule()`, `alertApi.updateRule()`, `alertApi.toggleRule()`
- 组件: 使用 shadcn/ui 组件库
- 路由: `/alerts/rules`

**依赖**: Issue 1.5

---

### Issue 1.5: 预警规则管理API完善

**优先级**: 🔴 P0  
**估算**: 5 SP  
**负责人**: Backend Team

**描述**:
完善预警规则管理API，确保前端页面所需的所有接口都已实现。

**验收标准**:
- [ ] 检查 `GET /api/v1/alert-rules` 接口，确保支持所有筛选参数
- [ ] 检查 `POST /api/v1/alert-rules` 接口，确保：
  - 规则编码唯一性验证
  - 必填项验证
  - JSON 字段格式验证（notify_channels, notify_roles, notify_users）
- [ ] 检查 `PUT /api/v1/alert-rules/{rule_id}` 接口，确保：
  - 系统预置规则保护
  - 部分更新支持
- [ ] 检查 `PUT /api/v1/alert-rules/{rule_id}/toggle` 接口
- [ ] 添加 `DELETE /api/v1/alert-rules/{rule_id}` 接口（非系统规则可删除）
- [ ] 添加规则配置验证逻辑：
  - 阈值格式验证
  - 条件表达式验证（如果有）
- [ ] 完善错误响应，返回详细的验证错误信息
- [ ] 添加 API 文档注释

**技术实现**:
- 文件: `app/api/v1/endpoints/alerts.py`
- Schema: `app/schemas/alert.py`
- 验证: 使用 Pydantic 模型验证

**依赖**: 无

---

## 四、Sprint 2: 规则引擎与升级机制（P1）

**目标**: 实现统一预警规则引擎框架，完善预警自动升级机制

**预计工时**: 31 SP  
**预计周期**: 2 周

### Issue 2.1: 统一预警规则引擎框架

**优先级**: 🟡 P1  
**估算**: 13 SP  
**负责人**: Backend Team

**描述**:
实现统一的预警规则引擎框架，抽象预警检查、匹配、生成的通用逻辑，提高代码复用性。

**验收标准**:
- [ ] 创建 `app/services/alert_rule_engine.py` 引擎类
- [ ] 实现 `AlertRuleEngine` 基类，包含：
  - `check_rule()` 抽象方法（子类实现具体检查逻辑）
  - `match_threshold()` 方法（阈值匹配）
  - `match_threshold_reverse()` 方法（反向阈值匹配）
  - `create_alert()` 方法（创建预警记录）
  - `should_create_alert()` 方法（去重检查）
  - `get_or_create_rule()` 方法（获取或创建规则）
- [ ] 实现具体的规则引擎子类：
  - `ProjectDelayRuleEngine` - 项目进度延期
  - `TaskDelayRuleEngine` - 任务延期
  - `PurchaseDeliveryRuleEngine` - 采购交期
  - `CostOverrunRuleEngine` - 成本超支
- [ ] 重构现有预警服务，使用统一引擎：
  - `check_task_delay_alerts()` 使用 `TaskDelayRuleEngine`
  - `check_delivery_delay()` 使用 `PurchaseDeliveryRuleEngine`
- [ ] 支持规则配置驱动（从 `AlertRule` 读取配置）
- [ ] 添加单元测试覆盖引擎核心逻辑

**技术实现**:
- 文件: `app/services/alert_rule_engine.py`
- 设计模式: 模板方法模式 + 策略模式
- 重构: `app/utils/scheduled_tasks.py` 中的预警服务

**依赖**: Sprint 1

---

### Issue 2.2: 预警去重机制优化

**优先级**: 🟡 P1  
**估算**: 5 SP  
**负责人**: Backend Team

**描述**:
优化预警去重机制，实现设计文档中的完整去重逻辑，包括级别提升功能。

**验收标准**:
- [ ] 完善 `should_create_alert()` 方法，实现：
  - 检查相同来源（rule_id + target_id）的活跃预警
  - 如果新预警级别更高，升级现有预警（调用 `upgrade_alert()`）
  - 如果级别相同或更低，不重复创建
  - 考虑时间窗口（24小时内不重复创建相同级别预警）
- [ ] 实现 `upgrade_alert()` 方法：
  - 更新预警级别
  - 记录原始级别（`original_level`）
  - 更新预警内容
  - 创建升级记录（`AlertEscalation`）
  - 发送升级通知
- [ ] 实现 `level_priority()` 辅助方法（INFO=1, WARNING=2, CRITICAL=3, URGENT=4）
- [ ] 在规则引擎中集成去重逻辑
- [ ] 添加单元测试覆盖去重和升级场景

**技术实现**:
- 文件: `app/services/alert_rule_engine.py`
- 数据库查询优化: 使用索引查询活跃预警
- 事务处理: 确保升级操作的原子性

**依赖**: Issue 2.1

---

### Issue 2.3: 预警自动升级机制

**优先级**: 🟡 P1  
**估算**: 8 SP  
**负责人**: Backend Team

**描述**:
实现预警超时未处理时的自动升级机制，确保重要预警得到及时响应。

**验收标准**:
- [ ] 创建 `check_alert_timeout_escalation()` 定时任务
- [ ] 升级逻辑：
  - 查询状态为 `PENDING` 或 `ACKNOWLEDGED` 的预警
  - 根据预警级别和响应时限判断是否超时：
    - WARNING: 8小时未确认 → 升级为 CRITICAL
    - CRITICAL: 4小时未处理 → 升级为 URGENT
    - URGENT: 1小时未处理 → 通知上级管理者
  - 从规则配置读取响应时限（`response_timeout_warning` 等）
- [ ] 升级操作：
  - 更新预警级别
  - 记录升级原因（`escalate_reason = "TIMEOUT"`）
  - 创建升级记录
  - 发送升级通知（通知上级管理者）
- [ ] 支持多级升级（记录升级层级）
- [ ] 注册到定时任务调度器，每小时执行一次
- [ ] 添加配置项：是否启用自动升级（`auto_escalate`）
- [ ] 添加单元测试

**技术实现**:
- 文件: `app/utils/scheduled_tasks.py`
- 调度配置: `app/utils/scheduler_config.py`
- 依赖: `AlertRule` 表中的响应时限配置

**依赖**: Issue 2.1, 2.2

---

### Issue 2.4: 预警级别动态提升

**优先级**: 🟡 P1  
**估算**: 5 SP  
**负责人**: Backend Team

**描述**:
实现预警条件持续恶化时的级别动态提升功能。

**验收标准**:
- [ ] 在规则引擎中实现 `check_level_escalation()` 方法
- [ ] 检查逻辑：
  - 对于已有预警，重新评估触发条件
  - 如果当前值超过更高阈值，自动提升级别
  - 例如：WARNING → CRITICAL → URGENT
- [ ] 级别提升时：
  - 更新预警级别和内容
  - 记录升级原因（`escalate_reason = "CONDITION_WORSENED"`）
  - 创建升级记录
  - 发送升级通知
- [ ] 在预警检查服务中集成级别提升检查
- [ ] 避免频繁升级（同一预警24小时内最多升级一次）
- [ ] 添加单元测试

**技术实现**:
- 文件: `app/services/alert_rule_engine.py`
- 集成: 在定时任务中调用级别提升检查

**依赖**: Issue 2.1, 2.2

---

## 五、Sprint 3: 预警订阅功能（P1）

**目标**: 实现用户预警订阅配置功能，支持个性化预警接收

**预计工时**: 25 SP  
**预计周期**: 2 周

### Issue 3.1: 预警订阅数据模型

**优先级**: 🟡 P1  
**估算**: 5 SP  
**负责人**: Backend Team

**描述**:
创建预警订阅配置的数据模型和数据库迁移脚本。

**验收标准**:
- [ ] 在 `app/models/alert.py` 中添加 `AlertSubscription` 模型
- [ ] 模型字段：
  - `user_id`: 用户ID
  - `alert_type`: 预警类型（可选，空表示全部）
  - `project_id`: 项目ID（可选，空表示全部）
  - `min_level`: 最低接收级别（默认 WARNING）
  - `notify_channels`: 通知渠道（JSON数组）
  - `quiet_start`: 免打扰开始时间
  - `quiet_end`: 免打扰结束时间
  - `is_active`: 是否启用
- [ ] 创建数据库迁移脚本：
  - `migrations/YYYYMMDD_alert_subscriptions_sqlite.sql`
  - `migrations/YYYYMMDD_alert_subscriptions_mysql.sql`
- [ ] 添加索引：
  - `idx_alert_subscriptions_user` (user_id)
  - `idx_alert_subscriptions_type` (alert_type)
  - `idx_alert_subscriptions_project` (project_id)
- [ ] 添加关系：与 `User` 和 `Project` 的外键关系
- [ ] 在 `app/models/__init__.py` 中导出模型

**技术实现**:
- 文件: `app/models/alert.py`
- 迁移脚本: `migrations/` 目录
- 参考: 设计文档中的 `alert_subscriptions` 表设计

**依赖**: 无

---

### Issue 3.2: 预警订阅配置API

**优先级**: 🟡 P1  
**估算**: 6 SP  
**负责人**: Backend Team

**描述**:
实现预警订阅配置的CRUD API接口。

**验收标准**:
- [ ] 在 `app/schemas/alert.py` 中添加订阅相关的 Schema：
  - `AlertSubscriptionCreate`
  - `AlertSubscriptionUpdate`
  - `AlertSubscriptionResponse`
- [ ] 在 `app/api/v1/endpoints/alerts.py` 中添加 API：
  - `GET /api/v1/alerts/subscriptions` - 获取我的订阅配置列表
  - `GET /api/v1/alerts/subscriptions/{id}` - 获取订阅详情
  - `POST /api/v1/alerts/subscriptions` - 创建订阅配置
  - `PUT /api/v1/alerts/subscriptions/{id}` - 更新订阅配置
  - `DELETE /api/v1/alerts/subscriptions/{id}` - 删除订阅配置
  - `PUT /api/v1/alerts/subscriptions/{id}/toggle` - 启用/禁用订阅
- [ ] API 权限控制：
  - 用户只能管理自己的订阅配置
  - 管理员可以查看所有订阅
- [ ] 数据验证：
  - 预警类型枚举验证
  - 预警级别枚举验证
  - 通知渠道数组验证
  - 免打扰时间格式验证
- [ ] 添加 API 文档注释

**技术实现**:
- 文件: `app/api/v1/endpoints/alerts.py`
- Schema: `app/schemas/alert.py`
- 权限: 使用 `get_current_active_user` 依赖

**依赖**: Issue 3.1

---

### Issue 3.3: 预警订阅匹配引擎

**优先级**: 🟡 P1  
**估算**: 8 SP  
**负责人**: Backend Team

**描述**:
实现预警订阅匹配引擎，在预警生成时根据用户订阅配置决定是否发送通知。

**验收标准**:
- [ ] 创建 `app/services/alert_subscription_service.py` 服务类
- [ ] 实现 `match_subscriptions()` 方法：
  - 根据预警类型、项目ID查询匹配的订阅配置
  - 检查预警级别是否满足最低接收级别
  - 检查当前时间是否在免打扰时段
  - 返回匹配的订阅列表
- [ ] 实现 `get_notification_recipients()` 方法：
  - 调用 `match_subscriptions()` 获取匹配订阅
  - 从订阅中提取通知渠道和用户
  - 合并规则配置中的通知对象（`notify_roles`, `notify_users`）
  - 去重后返回最终通知对象列表
- [ ] 在预警生成流程中集成订阅匹配：
  - 在 `create_alert()` 方法中调用订阅匹配
  - 根据匹配结果决定通知发送
- [ ] 支持默认订阅（用户未配置时使用规则默认通知对象）
- [ ] 添加单元测试覆盖匹配逻辑

**技术实现**:
- 文件: `app/services/alert_subscription_service.py`
- 集成: `app/services/alert_rule_engine.py`
- 查询优化: 使用数据库索引加速匹配

**依赖**: Issue 3.1, 3.2

---

### Issue 3.4: 预警订阅配置页面

**优先级**: 🟡 P1  
**估算**: 6 SP  
**负责人**: Frontend Team

**描述**:
实现预警订阅配置的前端页面，支持用户自定义预警接收设置。

**验收标准**:
- [ ] 创建 `AlertSubscriptionSettings.jsx` 页面
- [ ] 订阅列表展示：
  - 预警类型、项目范围
  - 最低接收级别
  - 通知渠道
  - 免打扰时段
  - 启用状态
  - 操作按钮（编辑、删除、启用/禁用）
- [ ] 订阅创建/编辑表单：
  - 预警类型选择（全部/指定类型）
  - 项目范围选择（全部/指定项目）
  - 最低接收级别选择（INFO/WARNING/CRITICAL/URGENT）
  - 通知渠道多选（站内消息/企业微信/邮件/短信）
  - 免打扰时段设置（开始时间、结束时间）
  - 启用状态开关
- [ ] 表单验证：
  - 必填项验证
  - 时间格式验证
  - 避免重复订阅（相同类型+项目）
- [ ] 默认订阅提示（未配置时使用系统默认）
- [ ] 响应式设计
- [ ] 集成到用户设置页面或独立页面

**技术实现**:
- 文件: `frontend/src/pages/AlertSubscriptionSettings.jsx`
- API 调用: `alertApi.getSubscriptions()`, `alertApi.createSubscription()`, `alertApi.updateSubscription()`
- 组件: 使用 shadcn/ui 组件库
- 路由: `/alerts/subscriptions` 或 `/settings/alert-subscriptions`

**依赖**: Issue 3.2

---

## 六、Sprint 4: 统计分析增强（P1）

**目标**: 完善预警统计分析功能，实现趋势分析和报表导出

**预计工时**: 25 SP  
**预计周期**: 2 周

### Issue 4.1: 预警趋势分析图表

**优先级**: 🟡 P1  
**估算**: 8 SP  
**负责人**: Full Stack Team

**描述**:
实现预警趋势分析的前后端功能，支持多维度趋势图表展示。

**验收标准**:
- [ ] 后端 API 增强：
  - 扩展 `GET /api/v1/alerts/statistics` 接口
  - 添加趋势数据返回：
    - 按日期统计（日/周/月）
    - 按级别统计趋势
    - 按类型统计趋势
    - 按状态统计趋势
- [ ] 前端图表实现：
  - 使用 Chart.js 或 Recharts 库
  - 预警数量趋势折线图
  - 预警级别分布饼图
  - 预警类型分布柱状图
  - 预警状态变化面积图
- [ ] 时间范围选择：
  - 支持自定义日期范围
  - 支持快捷选择（最近7天/30天/90天）
- [ ] 图表交互：
  - 鼠标悬停显示详细数据
  - 点击图表元素筛选数据
  - 图表导出（PNG/PDF）
- [ ] 响应式设计，支持移动端

**技术实现**:
- 后端: `app/api/v1/endpoints/alerts.py`
- 前端: `frontend/src/pages/AlertStatistics.jsx`
- 图表库: Recharts 或 Chart.js
- 数据格式: 时间序列数据

**依赖**: Sprint 1

---

### Issue 4.2: 响应时效分析

**优先级**: 🟡 P1  
**估算**: 6 SP  
**负责人**: Backend Team

**描述**:
实现预警响应时效的统计分析功能。

**验收标准**:
- [ ] 在 `AlertStatistics` 模型中已有 `avg_response_time` 和 `avg_resolve_time` 字段
- [ ] 扩展统计 API，添加响应时效分析：
  - 平均响应时间（确认时间 - 触发时间）
  - 平均解决时间（解决时间 - 确认时间）
  - 响应时效分布（<1小时、1-4小时、4-8小时、>8小时）
  - 按级别统计响应时效
  - 按类型统计响应时效
- [ ] 实现 `calculate_response_metrics()` 方法：
  - 查询已确认/已解决的预警
  - 计算响应时间和解决时间
  - 按维度聚合统计
- [ ] 在定时任务中定期计算并更新统计表
- [ ] 添加 API: `GET /api/v1/alerts/statistics/response-metrics`
- [ ] 返回响应时效排行榜（最快/最慢的项目/责任人）

**技术实现**:
- 文件: `app/api/v1/endpoints/alerts.py`
- 计算逻辑: 使用 SQL 聚合函数计算平均值
- 定时任务: `app/utils/scheduled_tasks.py`

**依赖**: Sprint 1

---

### Issue 4.3: 预警处理效率分析

**优先级**: 🟡 P1  
**估算**: 6 SP  
**负责人**: Backend Team

**描述**:
实现预警处理效率的统计分析功能。

**验收标准**:
- [ ] 扩展统计 API，添加处理效率分析：
  - 处理率（已处理数 / 总数）
  - 及时处理率（在响应时限内处理的比例）
  - 升级率（升级预警数 / 总数）
  - 重复预警率（重复预警数 / 总数）
- [ ] 按维度统计：
  - 按项目统计处理效率
  - 按责任人统计处理效率
  - 按预警类型统计处理效率
- [ ] 实现 `calculate_efficiency_metrics()` 方法
- [ ] 添加 API: `GET /api/v1/alerts/statistics/efficiency-metrics`
- [ ] 返回处理效率排行榜
- [ ] 识别处理效率低的责任人和项目

**技术实现**:
- 文件: `app/api/v1/endpoints/alerts.py`
- 计算逻辑: SQL 聚合和条件统计
- 数据模型: 使用 `AlertStatistics` 表存储

**依赖**: Issue 4.2

---

### Issue 4.4: 预警报表导出功能

**优先级**: 🟡 P1  
**估算**: 5 SP  
**负责人**: Backend Team

**描述**:
实现预警数据的 Excel 和 PDF 报表导出功能。

**验收标准**:
- [ ] 安装依赖库：`openpyxl`（Excel）、`reportlab` 或 `weasyprint`（PDF）
- [ ] 实现 Excel 导出：
  - `GET /api/v1/alerts/export/excel` 接口
  - 支持筛选参数（与列表接口一致）
  - 导出字段：预警编号、级别、标题、项目、触发时间、状态、处理人、处理时间
  - 支持多 Sheet（按级别或类型分组）
  - 添加格式：表头加粗、级别颜色标识
- [ ] 实现 PDF 导出：
  - `GET /api/v1/alerts/export/pdf` 接口
  - 包含统计摘要
  - 包含预警列表
  - 支持分页
- [ ] 前端导出按钮：
  - 在预警列表页面添加"导出 Excel"和"导出 PDF"按钮
  - 导出时显示加载状态
  - 下载文件
- [ ] 添加单元测试

**技术实现**:
- 后端: `app/api/v1/endpoints/alerts.py`
- 库: `openpyxl`, `reportlab` 或 `weasyprint`
- 前端: `frontend/src/pages/AlertCenter.jsx`

**依赖**: Sprint 1

---

## 七、Sprint 5: 多渠道通知集成（P2）

**目标**: 集成企业微信、邮件、短信等外部通知渠道

**预计工时**: 24 SP  
**预计周期**: 2 周

### Issue 5.1: 企业微信通知集成

**优先级**: 🟢 P2  
**估算**: 10 SP  
**负责人**: Backend Team

**描述**:
集成企业微信通知功能，支持预警通知推送到企业微信。

**验收标准**:
- [ ] 安装依赖：`requests` 库（如果未安装）
- [ ] 创建 `app/services/wechat_notification_service.py` 服务类
- [ ] 实现企业微信 API 调用：
  - 获取 access_token（支持缓存和刷新）
  - 发送应用消息（文本/卡片消息）
- [ ] 实现 `send_wechat_alert()` 方法：
  - 构建消息内容（包含预警标题、内容、链接）
  - 根据预警级别选择消息模板
  - 调用企业微信 API 发送
  - 处理发送结果和错误
- [ ] 配置管理：
  - 在 `app/core/config.py` 中添加企业微信配置项
  - 支持环境变量配置（`WECHAT_CORP_ID`, `WECHAT_AGENT_ID`, `WECHAT_SECRET`）
- [ ] 在通知服务中集成：
  - 检查订阅配置中的通知渠道
  - 如果包含 `WECHAT`，调用企业微信通知服务
- [ ] 错误处理：
  - API 调用失败时记录日志
  - 更新通知状态为 `FAILED`
  - 支持重试机制
- [ ] 添加单元测试（使用 Mock）

**技术实现**:
- 文件: `app/services/wechat_notification_service.py`
- 配置: `app/core/config.py`
- 集成: `app/services/notification_service.py`
- API 文档: 企业微信应用消息 API

**依赖**: Sprint 1

---

### Issue 5.2: 邮件通知集成

**优先级**: 🟢 P2  
**估算**: 8 SP  
**负责人**: Backend Team

**描述**:
集成邮件通知功能，支持预警通知通过邮件发送。

**验收标准**:
- [ ] 安装依赖：`aiosmtplib` 或 `smtplib`（Python 标准库）
- [ ] 创建 `app/services/email_notification_service.py` 服务类
- [ ] 实现邮件发送功能：
  - SMTP 连接配置
  - 邮件模板（HTML格式）
  - 邮件发送（支持异步）
- [ ] 实现 `send_email_alert()` 方法：
  - 构建邮件主题和内容
  - 根据预警级别选择邮件模板
  - 包含预警详情和链接
  - 发送邮件
- [ ] 配置管理：
  - 在 `app/core/config.py` 中添加邮件配置项
  - 支持环境变量配置（`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`）
- [ ] 邮件模板：
  - 创建 HTML 邮件模板
  - 支持预警级别颜色标识
  - 响应式设计（移动端友好）
- [ ] 在通知服务中集成邮件通知
- [ ] 错误处理和重试机制
- [ ] 添加单元测试

**技术实现**:
- 文件: `app/services/email_notification_service.py`
- 配置: `app/core/config.py`
- 模板: `app/templates/email/alert_notification.html`
- 集成: `app/services/notification_service.py`

**依赖**: Sprint 1

---

### Issue 5.3: 短信通知集成（可选）

**优先级**: 🟢 P2  
**估算**: 6 SP  
**负责人**: Backend Team

**描述**:
集成短信通知功能，仅用于紧急预警通知。

**验收标准**:
- [ ] 选择短信服务提供商（阿里云、腾讯云等）
- [ ] 安装对应的 SDK
- [ ] 创建 `app/services/sms_notification_service.py` 服务类
- [ ] 实现短信发送功能：
  - 调用短信服务 API
  - 短信模板配置
  - 发送结果处理
- [ ] 实现 `send_sms_alert()` 方法：
  - 仅对 URGENT 级别预警发送短信
  - 短信内容简洁（预警标题 + 链接）
  - 发送短信
- [ ] 配置管理：
  - 在 `app/core/config.py` 中添加短信配置项
  - 支持环境变量配置
- [ ] 在通知服务中集成短信通知
- [ ] 错误处理和重试机制
- [ ] 成本控制（限制发送频率）
- [ ] 添加单元测试

**技术实现**:
- 文件: `app/services/sms_notification_service.py`
- 配置: `app/core/config.py`
- SDK: 根据选择的提供商安装对应 SDK
- 集成: `app/services/notification_service.py`

**依赖**: Sprint 1

**注意**: 此功能为可选功能，可根据实际需求决定是否实现。

---

## 八、Sprint 6: 性能优化与重构（P1）

**目标**: 优化代码结构，提升系统性能

**预计工时**: 23 SP  
**预计周期**: 2 周

### Issue 6.1: 预警服务代码重构

**优先级**: 🟡 P1  
**估算**: 8 SP  
**负责人**: Backend Team

**描述**:
重构预警服务代码，使用统一的规则引擎框架，提高代码复用性和可维护性。

**验收标准**:
- [ ] 重构 `app/utils/scheduled_tasks.py` 中的预警服务：
  - 使用 `AlertRuleEngine` 基类
  - 抽取通用逻辑到基类
  - 简化各服务的实现代码
- [ ] 代码质量提升：
  - 减少代码重复
  - 提高函数可读性
  - 统一错误处理
  - 统一日志记录
- [ ] 代码审查：
  - 确保所有服务遵循统一模式
  - 确保向后兼容（不影响现有功能）
- [ ] 添加代码注释和文档字符串
- [ ] 运行现有测试确保功能正常

**技术实现**:
- 文件: `app/utils/scheduled_tasks.py`
- 重构工具: 使用 IDE 重构功能
- 测试: 运行现有单元测试和集成测试

**依赖**: Issue 2.1

---

### Issue 6.2: 数据库查询优化

**优先级**: 🟡 P1  
**估算**: 5 SP  
**负责人**: Backend Team

**描述**:
优化预警相关的数据库查询，解决 N+1 问题，提升查询性能。

**验收标准**:
- [ ] 分析现有查询性能：
  - 使用 SQLAlchemy 查询分析工具
  - 识别 N+1 查询问题
  - 识别缺少索引的查询
- [ ] 优化预警列表查询：
  - 使用 `joinedload` 或 `selectinload` 预加载关联数据
  - 批量查询处理人信息
  - 减少数据库往返次数
- [ ] 优化预警统计查询：
  - 使用 SQL 聚合函数替代 Python 循环
  - 添加必要的数据库索引
  - 考虑使用物化视图（MySQL）或临时表
- [ ] 优化定时任务查询：
  - 使用批量查询替代循环查询
  - 添加查询条件索引
  - 限制查询结果数量（分页）
- [ ] 性能测试：
  - 对比优化前后的查询时间
  - 确保性能提升明显（至少 50%）
- [ ] 添加查询性能监控日志

**技术实现**:
- 文件: `app/api/v1/endpoints/alerts.py`, `app/utils/scheduled_tasks.py`
- 工具: SQLAlchemy 查询分析、数据库 EXPLAIN 分析
- 索引: 在迁移脚本中添加索引

**依赖**: Sprint 1-4

---

### Issue 6.3: 定时任务性能优化

**优先级**: 🟡 P1  
**估算**: 6 SP  
**负责人**: Backend Team

**描述**:
优化定时任务的执行性能，避免处理大量数据时内存溢出和超时。

**验收标准**:
- [ ] 分析定时任务性能：
  - 识别处理大量数据的任务
  - 测量任务执行时间
  - 识别内存使用峰值
- [ ] 实现分批处理：
  - 对于需要处理大量记录的任务，实现分批查询
  - 每批处理固定数量（如 100 条）
  - 使用生成器或迭代器避免一次性加载所有数据
- [ ] 优化数据库查询：
  - 使用 `yield_per()` 分批获取数据
  - 添加查询条件限制范围
  - 使用索引加速查询
- [ ] 添加任务执行监控：
  - 记录任务执行时间
  - 记录处理记录数量
  - 记录内存使用情况
- [ ] 错误处理优化：
  - 单条记录处理失败不影响整批
  - 记录失败记录并继续处理
  - 任务完成后汇总错误信息
- [ ] 性能测试：
  - 测试处理 1000+ 条记录的性能
  - 确保任务在合理时间内完成（< 5 分钟）
  - 确保内存使用稳定

**技术实现**:
- 文件: `app/utils/scheduled_tasks.py`
- 技术: 分批处理、生成器、数据库游标
- 监控: 添加性能日志

**依赖**: Issue 6.2

---

### Issue 6.4: 预警规则配置验证

**优先级**: 🟡 P1  
**估算**: 4 SP  
**负责人**: Backend Team

**描述**:
增强预警规则配置的验证逻辑，使用 Pydantic 模型进行类型检查和格式验证。

**验收标准**:
- [ ] 完善 `AlertRuleCreate` 和 `AlertRuleUpdate` Schema：
  - 添加字段类型验证
  - 添加枚举值验证（rule_type, target_type, alert_level 等）
  - 添加数值范围验证（threshold_value）
  - 添加 JSON 格式验证（notify_channels, notify_roles, notify_users）
- [ ] 实现自定义验证器：
  - 规则编码格式验证（字母数字下划线）
  - 阈值格式验证（数字或表达式）
  - 条件表达式语法验证（如果有）
- [ ] 实现业务规则验证：
  - 阈值合理性检查（min < max）
  - 通知渠道有效性检查
  - 通知角色/用户存在性检查
- [ ] 错误消息优化：
  - 返回详细的验证错误信息
  - 指出具体哪个字段有问题
  - 提供修复建议
- [ ] 添加单元测试覆盖所有验证场景

**技术实现**:
- 文件: `app/schemas/alert.py`
- 验证: Pydantic 模型验证 + 自定义验证器
- 错误处理: 使用 FastAPI 的验证错误响应

**依赖**: Issue 1.5

---

## 九、Sprint 7: 测试与文档完善（P1）

**目标**: 完善单元测试、集成测试和文档

**预计工时**: 20 SP  
**预计周期**: 1 周

### Issue 7.1: 预警模块单元测试

**优先级**: 🟡 P1  
**估算**: 8 SP  
**负责人**: QA + Backend Team

**验收标准**:
- [ ] 创建 `tests/test_alert_services.py`：
  - 测试通知服务（发送、阅读、重试）
  - 测试规则引擎（检查、匹配、创建）
  - 测试订阅服务（匹配、过滤）
- [ ] 创建 `tests/test_alert_api.py`：
  - 测试预警规则 API（CRUD）
  - 测试预警记录 API（列表、详情、操作）
  - 测试异常事件 API
  - 测试统计 API
- [ ] 创建 `tests/test_alert_models.py`：
  - 测试模型关系
  - 测试模型方法
- [ ] 测试覆盖率目标：> 80%
- [ ] 使用 pytest 和 pytest-cov
- [ ] 添加测试数据 Fixture

**技术实现**:
- 文件: `tests/test_alert_*.py`
- 框架: pytest, pytest-cov
- Mock: unittest.mock 或 pytest-mock

**依赖**: Sprint 1-6

---

### Issue 7.2: 预警模块集成测试

**优先级**: 🟡 P1  
**估算**: 6 SP  
**负责人**: QA + Backend Team

**验收标准**:
- [ ] 创建 `tests/integration/test_alert_workflow.py`：
  - 测试完整预警流程（生成 → 通知 → 确认 → 处理 → 关闭）
  - 测试预警升级流程
  - 测试订阅匹配流程
- [ ] 创建 `tests/integration/test_alert_scheduled_tasks.py`：
  - 测试定时任务执行
  - 测试预警生成逻辑
  - 测试统计计算逻辑
- [ ] 使用测试数据库（SQLite in-memory）
- [ ] 测试数据清理（每个测试后清理）
- [ ] 添加测试报告生成

**技术实现**:
- 文件: `tests/integration/test_alert_*.py`
- 框架: pytest
- 数据库: SQLite in-memory 或测试 MySQL

**依赖**: Issue 7.1

---

### Issue 7.3: API 文档完善

**优先级**: 🟡 P1  
**估算**: 3 SP  
**负责人**: Backend Team

**验收标准**:
- [ ] 完善 API 端点文档字符串：
  - 添加详细的接口描述
  - 添加请求参数说明
  - 添加响应示例
  - 添加错误码说明
- [ ] 完善 Schema 文档：
  - 添加字段说明
  - 添加示例值
  - 添加验证规则说明
- [ ] 生成 OpenAPI 文档：
  - 确保所有接口都有文档
  - 确保文档准确无误
  - 添加使用示例
- [ ] 创建 API 使用指南：
  - 常见场景示例
  - 错误处理指南
  - 最佳实践

**技术实现**:
- 文件: `app/api/v1/endpoints/alerts.py`, `app/schemas/alert.py`
- 工具: FastAPI 自动文档生成
- 文档: Markdown 格式的使用指南

**依赖**: Sprint 1-6

---

### Issue 7.4: 用户使用手册

**优先级**: 🟡 P1  
**估算**: 3 SP  
**负责人**: Product Team

**验收标准**:
- [ ] 创建预警模块用户手册：
  - 预警中心使用指南
  - 预警规则配置指南
  - 预警订阅配置指南
  - 预警处理流程说明
- [ ] 包含截图和示例：
  - 界面截图
  - 操作步骤截图
  - 配置示例
- [ ] 创建常见问题 FAQ
- [ ] 创建视频教程（可选）
- [ ] 文档格式：Markdown 或 PDF

**技术实现**:
- 文件: `docs/预警模块用户手册.md`
- 工具: Markdown 编辑器或文档工具
- 格式: 支持导出 PDF

**依赖**: Sprint 1-6

---

## 十、总结

### 10.1 Sprint 优先级排序

1. **Sprint 1** (P0) - 通知机制与规则配置 - **必须完成**
2. **Sprint 2** (P1) - 规则引擎与升级机制 - **重要**
3. **Sprint 3** (P1) - 预警订阅功能 - **重要**
4. **Sprint 4** (P1) - 统计分析增强 - **重要**
5. **Sprint 6** (P1) - 性能优化与重构 - **重要**
6. **Sprint 7** (P1) - 测试与文档完善 - **重要**
7. **Sprint 5** (P2) - 多渠道通知集成 - **可选**

### 10.2 关键里程碑

- **里程碑 1** (Sprint 1 完成): 核心通知功能和规则配置可用
- **里程碑 2** (Sprint 2 完成): 统一规则引擎和自动升级机制完成
- **里程碑 3** (Sprint 3 完成): 预警订阅功能完成
- **里程碑 4** (Sprint 4 完成): 统计分析功能完善
- **里程碑 5** (Sprint 6-7 完成): 性能优化和测试文档完成

### 10.3 风险提示

1. **通知服务集成风险**: 企业微信、邮件等外部服务集成可能遇到配置和权限问题
2. **性能风险**: 大量预警数据可能影响查询和统计性能，需要提前优化
3. **兼容性风险**: 重构代码时需确保向后兼容，不影响现有功能

---

**文档版本**: v1.0  
**创建日期**: 2026-01-15  
**最后更新**: 2026-01-15
