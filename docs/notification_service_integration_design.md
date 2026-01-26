# NotificationService 统一整合设计文档

## 一、现状分析

### 1.1 现有通知服务

当前系统存在多个独立的通知服务：

| 服务 | 文件 | 用途 | 渠道 | 问题 |
|------|------|------|------|------|
| **NotificationService** | `app/services/notification_service.py` | 通用通知（任务、项目等） | WEB, EMAIL, SMS, WECHAT, WEBHOOK | 1. 依赖不存在的WebNotification模型<br>2. 功能重复 |
| **AlertNotificationService** | (在notification_service.py中) | 预警通知 | WEB | 功能与NotificationService重复 |
| **NotificationDispatcher** | `app/services/notification_dispatcher.py` | 预警调度 | SYSTEM, EMAIL, WECHAT, SMS | 1. 专门用于AlertRecord<br>2. 与NotificationService不统一 |
| **WeChatAlertService** | `app/services/wechat_alert_service.py` | 企业微信缺料预警 | WECHAT (模板卡片) | 1. 功能独立<br>2. 未使用统一渠道管理 |
| **ECN通知模块** | `app/services/ecn_notification/` | ECN相关通知 | 通知数据库 | 1. 独立实现<br>2. 未使用NotificationService |
| **Approval Engine通知** | `app/services/approval_engine/notify/` | 审批流程通知 | 多渠道 | 1. 有自己的SendNotificationMixin<br>2. 未与NotificationService整合 |

### 1.2 受影响位置（15+处）

#### API端点（7个文件）
1. `app/api/v1/endpoints/alerts/notifications.py` - AlertNotificationService
2. `app/api/v1/endpoints/engineers/approvals.py` - notification_service
3. `app/api/v1/endpoints/engineers/delays.py` - notification_service
4. `app/api/v1/endpoints/engineers/progress.py` - notification_service
5. `app/api/v1/endpoints/engineers/tasks.py` - notification_service
6. `app/api/v1/endpoints/sales/contracts/approval.py` - notification_service
7. `app/api/v1/endpoints/shortage/handling/substitutions.py` - notification_service

#### 服务层（9个文件）
1. `app/services/alert_rule_engine/alert_creator.py` - AlertNotificationService
2. `app/services/alert_rule_engine/alert_upgrader.py` - AlertNotificationService
3. `app/services/data_integrity/reminders.py` - NotificationService
4. `app/utils/alert_escalation_task.py` - AlertNotificationService
5. `app/utils/scheduled_tasks/alert_tasks.py` - NotificationDispatcher
6. `app/utils/scheduled_tasks/base.py` - NotificationDispatcher
7. `app/services/notification_handlers/*` - NotificationDispatcher依赖
8. `app/services/ecn_notification/*` - 独立实现
9. `app/services/approval_engine/notify/*` - 独立实现

#### 其他
- `app/api/v1/endpoints/assembly_kit/kit_analysis/analysis.py` - WeChatAlertService

### 1.3 通知模型

| 模型 | 用途 | 状态 |
|------|------|------|
| `Notification` | 系统通知（站内消息） | ✅ 已实现 |
| `NotificationSettings` | 用户通知偏好 | ✅ 已实现 |
| `AlertNotification` | 预警通知记录 | ✅ 已实现 |
| `WebNotification` | Web通知（不存在） | ❌ 不存在 |

### 1.4 主要问题

1. **代码重复**: 多个服务实现相似的通知逻辑
2. **不统一**: 不同的服务使用不同的接口和方法
3. **难以维护**: 修改需要同步多处代码
4. **功能割裂**: 新功能只能在一个服务中实现
5. **依赖问题**: WebNotification模型不存在，NotificationService会失败

---

## 二、统一架构设计

### 2.1 设计目标

1. **统一接口**: 所有通知通过统一的NotificationService
2. **渠道抽象**: 支持多种通知渠道，易于扩展
3. **向后兼容**: 保持现有API调用方式
4. **异步支持**: 支持同步和异步发送
5. **重试机制**: 内置失败重试和错误处理
6. **去重机制**: 避免重复通知
7. **偏好管理**: 尊重用户通知偏好
8. **免打扰**: 支持免打扰时间段

### 2.2 架构层次

```
┌─────────────────────────────────────────────────────┐
│           应用层（API / Services）               │
│  使用统一接口: notification_service.send()      │
└───────────────────────┬─────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────┐
│       NotificationService（统一服务层）           │
│  - send_notification()                           │
│  - send_task_assigned()                          │
│  - send_alert()                                  │
│  - send_ecn()                                    │
│  - send_approval()                                 │
└───────┬───────────────┬─────────────────────────┘
        │               │
   ┌────▼─────┐   ┌──▼──────────────────┐
   │  适配器   │   │   渠道管理器      │
   │  层       │   │  ChannelManager    │
   │           │   │                   │
   │ - Task    │   │ - 渠道路由         │
   │ - Alert   │   │ - 偏好检查         │
   │ - ECN     │   │ - 去重            │
   │ - Approval│   │ - 免打扰          │
   └────┬─────┘   └───┬────────────────┘
        │              │
   ┌────▼──────────────▼────────────┐
   │       渠道处理器（Handlers）      │
   │                               │
   │ - SystemHandler（站内通知）     │
   │ - EmailHandler（邮件）          │
   │ - WeChatHandler（企业微信）      │
   │ - SMSHandler（短信）           │
   │ - WebhookHandler（Webhook）     │
   └───────┬──────────────────────────┘
           │
   ┌───────▼────────────────────────┐
   │  外部服务                     │
   │ - 数据库（保存站内通知）        │
   │ - SMTP（邮件发送）             │
   │ - 企业微信API                 │
   │ - 短信API                    │
   │ - Webhook API                │
   └──────────────────────────────────┘
```

### 2.3 核心组件

#### 2.3.1 NotificationChannel（通知渠道枚举）

```python
class NotificationChannel(str, Enum):
    """通知渠道"""
    SYSTEM = "system"      # 站内通知（Notification表）
    EMAIL = "email"        # 邮件
    WECHAT = "wechat"      # 企业微信
    SMS = "sms"           # 短信
    WEBHOOK = "webhook"    # Webhook（钉钉、飞书等）
```

#### 2.3.2 NotificationPriority（优先级枚举）

```python
class NotificationPriority(str, Enum):
    """通知优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
```

#### 2.3.3 NotificationCategory（通知分类枚举）

```python
class NotificationCategory(str, Enum):
    """通知分类（用于去重和偏好）"""
    TASK = "task"           # 任务通知
    APPROVAL = "approval"   # 审批通知
    ALERT = "alert"         # 预警通知
    ECN = "ecn"           # ECN通知
    PROJECT = "project"     # 项目通知
    ISSUE = "issue"        # 问题通知
    DEADLINE = "deadline"   # 截止日期提醒
```

#### 2.3.4 NotificationRequest（通知请求模型）

```python
class NotificationRequest(BaseModel):
    """统一通知请求"""
    # 接收者
    recipient_id: int                      # 接收用户ID

    # 通知内容
    category: NotificationCategory           # 通知分类
    notification_type: str                 # 通知类型（如TASK_ASSIGNED）
    title: str                           # 标题
    content: str                          # 内容

    # 优先级和渠道
    priority: NotificationPriority = NotificationPriority.NORMAL
    channels: Optional[List[NotificationChannel]] = None  # 指定渠道，None为自动

    # 来源和跳转
    source_type: Optional[str] = None     # 来源类型（task/project/alert等）
    source_id: Optional[int] = None       # 来源ID
    link_url: Optional[str] = None       # 跳转链接

    # 扩展数据
    extra_data: Optional[Dict[str, Any]] = None
    wechat_template: Optional[Dict[str, Any]] = None  # 企业微信模板

    # 控制参数
    force_send: bool = False              # 强制发送（忽略偏好和去重）
    async_send: bool = False             # 异步发送（使用队列）
```

#### 2.3.5 ChannelHandler（渠道处理器基类）

```python
class ChannelHandler(ABC):
    """渠道处理器基类"""

    @abstractmethod
    def send(self, request: NotificationRequest) -> bool:
        """发送通知"""
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        """检查渠道是否启用"""
        pass

    @abstractmethod
    def should_send(self, user_settings: NotificationSettings, priority: NotificationPriority) -> bool:
        """检查是否应该发送（根据偏好和优先级）"""
        pass
```

#### 2.3.6 具体Handler实现

```python
class SystemChannelHandler(ChannelHandler):
    """站内通知处理器"""
    def send(self, request: NotificationRequest) -> bool:
        # 保存到Notification表
        notification = Notification(
            user_id=request.recipient_id,
            notification_type=request.notification_type,
            title=request.title,
            content=request.content,
            source_type=request.source_type,
            source_id=request.source_id,
            link_url=request.link_url,
            priority=request.priority.value,
            extra_data=request.extra_data
        )
        db.add(notification)
        db.commit()
        return True

class EmailChannelHandler(ChannelHandler):
    """邮件通知处理器"""
    # 使用SMTP发送邮件

class WeChatChannelHandler(ChannelHandler):
    """企业微信通知处理器"""
    # 使用企业微信API发送消息
    # 支持普通消息和模板卡片

class SMSChannelHandler(ChannelHandler):
    """短信通知处理器"""
    # 使用短信API发送短信

class WebhookChannelHandler(ChannelHandler):
    """Webhook通知处理器"""
    # 发送HTTP POST到webhook URL
```

---

## 三、NotificationService统一实现

### 3.1 核心接口

```python
class NotificationService:
    """统一通知服务"""

    # ============== 核心方法 ==============

    def send_notification(self, request: NotificationRequest) -> NotificationResult:
        """
        发送通知（通用方法）

        处理流程：
        1. 检查去重（除非force_send=True）
        2. 检查用户偏好
        3. 检查免打扰时间
        4. 路由到指定渠道
        5. 发送并记录结果
        """

    def send_bulk_notification(self, requests: List[NotificationRequest]) -> List[NotificationResult]:
        """批量发送通知"""

    # ============== 便捷方法 ==============

    def send_task_assigned(self, ...):
        """发送任务分配通知"""

    def send_task_completed(self, ...):
        """发送任务完成通知"""

    def send_approval_pending(self, ...):
        """发送审批待处理通知"""

    def send_alert(self, ...):
        """发送预警通知"""

    def send_ecn_submitted(self, ...):
        """发送ECN提交通知"""

    def send_deadline_reminder(self, ...):
        """发送截止日期提醒"""

    # ============== 向后兼容方法 ==============

    @staticmethod
    def send_notification_legacy(
        db: Session,
        recipient_id: int,
        notification_type: str,
        title: str,
        content: str,
        priority: str = "normal",
        channels: Optional[List[str]] = None,
        data: Optional[Dict] = None,
        link: Optional[str] = None
    ) -> bool:
        """
        向后兼容的send_notification方法
        用于无缝迁移现有代码
        """
```

### 3.2 NotificationResult（通知结果）

```python
class NotificationResult(BaseModel):
    """通知发送结果"""
    success: bool              # 是否成功
    channels_sent: List[str]    # 已发送的渠道
    channels_failed: List[str]   # 失败的渠道
    errors: List[str]           # 错误信息
    deduped: bool = False      # 是否被去重
```

---

## 四、迁移策略

### 4.1 迁移优先级

#### 第一阶段（核心服务）
1. ✅ 创建新的统一NotificationService
2. ✅ 迁移NotificationService（通用通知）
3. ✅ 迁移AlertNotificationService（预警通知）

#### 第二阶段（其他服务）
4. ✅ 迁移NotificationDispatcher
5. ✅ 迁移WeChatAlertService
6. ✅ 迁移ECN通知模块
7. ✅ 迁移Approval Engine通知

#### 第三阶段（API端点）
8. ✅ 更新所有API端点的通知调用
9. ✅ 删除或标记旧的代码

#### 第四阶段（验证）
10. ✅ 全面测试所有通知功能
11. ✅ 性能测试和优化

### 4.2 向后兼容策略

1. **保留旧接口**: 在旧服务中调用新的NotificationService
2. **渐进式迁移**: 先迁移新功能，再逐步迁移旧代码
3. **标记废弃**: 添加@deprecated装饰器到旧方法
4. **文档更新**: 更新所有使用文档

### 4.3 测试计划

#### 单元测试
- [ ] 各渠道Handler的单元测试
- [ ] 去重机制测试
- [ ] 偏好检查测试
- [ ] 免打扰测试

#### 集成测试
- [ ] 任务通知端到端测试
- [ ] 预警通知端到端测试
- [ ] 审批通知端到端测试
- [ ] ECN通知端到端测试

#### 回归测试
- [ ] 所有API端点通知功能测试
- [ ] 性能测试（与旧版本对比）

---

## 五、实施步骤

### Step 1: 创建新的NotificationService
- [ ] 创建`app/services/unified_notification.py`
- [ ] 实现核心NotificationService类
- [ ] 实现所有ChannelHandler
- [ ] 实现去重和偏好检查逻辑

### Step 2: 迁移核心服务
- [ ] 更新`app/services/notification_service.py`
- [ ] 实现向后兼容的wrapper方法
- [ ] 迁移AlertNotificationService

### Step 3: 迁移其他服务
- [ ] 更新NotificationDispatcher
- [ ] 迁移WeChatAlertService
- [ ] 更新ECN通知模块
- [ ] 更新Approval Engine通知

### Step 4: 更新API端点
- [ ] 更新所有使用notification_service的API端点
- [ ] 更新所有使用AlertNotificationService的API端点
- [ ] 更新所有使用NotificationDispatcher的API端点

### Step 5: 测试和验证
- [ ] 单元测试
- [ ] 集成测试
- [ ] 回归测试
- [ ] 性能测试

### Step 6: 清理
- [ ] 删除重复代码
- [ ] 更新文档
- [ ] 代码审查

---

## 六、文件清单

### 新增文件
- `app/services/unified_notification.py` - 统一通知服务实现
- `app/services/channel_handlers/` - 渠道处理器目录
  - `__init__.py`
  - `base.py` - 基类
  - `system_handler.py` - 站内通知
  - `email_handler.py` - 邮件
  - `wechat_handler.py` - 企业微信
  - `sms_handler.py` - 短信
  - `webhook_handler.py` - Webhook

### 修改文件
- `app/services/notification_service.py` - 重构为兼容层
- `app/services/notification_dispatcher.py` - 更新为使用新服务
- `app/services/wechat_alert_service.py` - 迁移到新服务
- `app/services/ecn_notification/*.py` - 更新为使用新服务
- `app/services/approval_engine/notify/*.py` - 更新为使用新服务
- 所有API端点文件（15+处）

### 删除文件（可选）
- 旧的NotificationService实现（保留向后兼容后可删除）
- 旧的notification_handlers目录（功能已迁移到channel_handlers）

---

## 七、成功标准

### 功能标准
- [ ] 所有现有通知功能正常工作
- [ ] 新的NotificationService支持所有通知场景
- [ ] 向后兼容，不影响现有代码
- [ ] 支持所有通知渠道（SYSTEM, EMAIL, WECHAT, SMS, WEBHOOK）

### 性能标准
- [ ] 通知发送性能不低于旧版本
- [ ] 支持异步发送（可选）
- [ ] 数据库查询优化

### 代码质量标准
- [ ] 代码重复率降低50%以上
- [ ] 统一的接口和错误处理
- [ ] 完整的类型注解和文档
- [ ] 通过所有linter检查

---

## 八、风险评估

### 风险1: 向后兼容性
- **风险**: 旧代码可能无法正常工作
- **缓解**: 保留旧的接口作为wrapper
- **回滚**: 发现问题可以快速回滚

### 风险2: 数据不一致
- **风险**: Notification和AlertNotification可能冲突
- **缓解**: 统一使用Notification模型
- **验证**: 充分测试数据一致性

### 风险3: 性能下降
- **风险**: 统一服务可能增加复杂度
- **缓解**: 优化查询和缓存
- **监控**: 添加性能监控

### 风险4: 功能缺失
- **风险**: 某些特殊功能可能遗漏
- **缓解**: 详细的功能清单和测试
- **测试**: 完整的回归测试

---

## 九、后续优化方向

1. **异步发送**: 使用Celery或RQ实现真正的异步
2. **消息队列**: 使用Redis或RabbitMQ解耦
3. **消息模板**: 支持多语言和模板管理
4. **通知统计**: 添加发送统计和分析
5. **批量优化**: 批量发送优化性能
6. **失败补偿**: 更智能的重试和补偿机制
