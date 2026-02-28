"""
任务提醒推送服务
支持多渠道通知：企业微信、邮件、站内消息、APP推送

提醒场景：
1. 任务分配提醒 - 新任务分配给你
2. 截止前提醒 - 24h/4h/1h前提醒
3. 逾期提醒 - 任务已逾期
4. 进度催办 - 任务进度落后
5. 转办通知 - 任务被转办给你
6. 审批提醒 - 流程待你处理
7. 完成通知 - 你的任务已被验收
8. 驳回通知 - 任务被驳回
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict
import json
import asyncio
import hashlib


class ReminderType(Enum):
    """提醒类型"""
    TASK_ASSIGNED = "task_assigned"           # 任务分配
    DEADLINE_24H = "deadline_24h"             # 24小时前
    DEADLINE_4H = "deadline_4h"               # 4小时前
    DEADLINE_1H = "deadline_1h"               # 1小时前
    TASK_OVERDUE = "task_overdue"             # 任务逾期
    PROGRESS_URGE = "progress_urge"           # 进度催办
    TASK_TRANSFERRED = "task_transferred"     # 任务转办
    WORKFLOW_PENDING = "workflow_pending"     # 流程待办
    TASK_APPROVED = "task_approved"           # 任务通过
    TASK_REJECTED = "task_rejected"           # 任务驳回
    DAILY_SUMMARY = "daily_summary"           # 每日汇总
    WEEKLY_SUMMARY = "weekly_summary"         # 每周汇总


class NotifyChannel(Enum):
    """通知渠道"""
    WECHAT_WORK = "wechat_work"    # 企业微信
    EMAIL = "email"                 # 邮件
    SMS = "sms"                     # 短信
    IN_APP = "in_app"              # 站内消息
    APP_PUSH = "app_push"          # APP推送


class ReminderPriority(Enum):
    """提醒优先级"""
    URGENT = "urgent"       # 紧急（立即推送）
    HIGH = "high"           # 高（5分钟内）
    NORMAL = "normal"       # 普通（下一批次）
    LOW = "low"             # 低（合并推送）


@dataclass
class ReminderTemplate:
    """提醒模板"""
    type: ReminderType
    title_template: str
    content_template: str
    channels: List[NotifyChannel]
    priority: ReminderPriority
    can_disable: bool = True        # 用户是否可关闭
    merge_window: int = 0           # 合并窗口(分钟)，0表示不合并


@dataclass
class ReminderMessage:
    """提醒消息"""
    id: str
    type: ReminderType
    user_id: int
    user_name: str
    title: str
    content: str
    data: Dict[str, Any]            # 关联数据
    channels: List[NotifyChannel]
    priority: ReminderPriority
    created_at: datetime
    scheduled_at: Optional[datetime] = None  # 计划发送时间
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    is_sent: bool = False
    is_read: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "user_id": self.user_id,
            "title": self.title,
            "content": self.content,
            "data": self.data,
            "channels": [c.value for c in self.channels],
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "is_sent": self.is_sent,
            "is_read": self.is_read
        }


@dataclass
class UserReminderSettings:
    """用户提醒设置"""
    user_id: int
    
    # 渠道开关
    enable_wechat: bool = True
    enable_email: bool = True
    enable_sms: bool = False        # 短信默认关闭
    enable_in_app: bool = True
    enable_app_push: bool = True
    
    # 类型开关
    enable_task_assigned: bool = True
    enable_deadline_reminder: bool = True
    enable_overdue_reminder: bool = True
    enable_progress_urge: bool = True
    enable_transfer_notify: bool = True
    enable_workflow_pending: bool = True
    enable_daily_summary: bool = True
    enable_weekly_summary: bool = True
    
    # 免打扰时段
    dnd_enabled: bool = False
    dnd_start_time: str = "22:00"   # 免打扰开始
    dnd_end_time: str = "08:00"     # 免打扰结束
    
    # 提前提醒时间
    deadline_remind_hours: List[int] = field(default_factory=lambda: [24, 4, 1])
    
    def to_dict(self) -> Dict:
        return {
            "user_id": self.user_id,
            "channels": {
                "wechat": self.enable_wechat,
                "email": self.enable_email,
                "sms": self.enable_sms,
                "in_app": self.enable_in_app,
                "app_push": self.enable_app_push
            },
            "types": {
                "task_assigned": self.enable_task_assigned,
                "deadline_reminder": self.enable_deadline_reminder,
                "overdue_reminder": self.enable_overdue_reminder,
                "progress_urge": self.enable_progress_urge,
                "transfer_notify": self.enable_transfer_notify,
                "workflow_pending": self.enable_workflow_pending,
                "daily_summary": self.enable_daily_summary,
                "weekly_summary": self.enable_weekly_summary
            },
            "dnd": {
                "enabled": self.dnd_enabled,
                "start": self.dnd_start_time,
                "end": self.dnd_end_time
            },
            "deadline_remind_hours": self.deadline_remind_hours
        }


# ==================== 提醒模板配置 ====================

REMINDER_TEMPLATES: Dict[ReminderType, ReminderTemplate] = {
    ReminderType.TASK_ASSIGNED: ReminderTemplate(
        type=ReminderType.TASK_ASSIGNED,
        title_template="📋 新任务：{task_title}",
        content_template="{assigner}给您分配了新任务\n任务：{task_title}\n截止：{deadline}\n优先级：{priority}",
        channels=[NotifyChannel.WECHAT_WORK, NotifyChannel.IN_APP],
        priority=ReminderPriority.HIGH
    ),
    
    ReminderType.DEADLINE_24H: ReminderTemplate(
        type=ReminderType.DEADLINE_24H,
        title_template="⏰ 任务即将到期（24小时）",
        content_template="您有任务即将在24小时内到期\n任务：{task_title}\n截止：{deadline}\n当前进度：{progress}%",
        channels=[NotifyChannel.WECHAT_WORK, NotifyChannel.IN_APP],
        priority=ReminderPriority.NORMAL
    ),
    
    ReminderType.DEADLINE_4H: ReminderTemplate(
        type=ReminderType.DEADLINE_4H,
        title_template="⚠️ 任务即将到期（4小时）",
        content_template="您有任务即将在4小时内到期\n任务：{task_title}\n截止：{deadline}\n当前进度：{progress}%\n请尽快完成！",
        channels=[NotifyChannel.WECHAT_WORK, NotifyChannel.IN_APP, NotifyChannel.APP_PUSH],
        priority=ReminderPriority.HIGH
    ),
    
    ReminderType.DEADLINE_1H: ReminderTemplate(
        type=ReminderType.DEADLINE_1H,
        title_template="🔴 任务即将到期（1小时）",
        content_template="紧急！您有任务1小时内到期\n任务：{task_title}\n截止：{deadline}\n当前进度：{progress}%",
        channels=[NotifyChannel.WECHAT_WORK, NotifyChannel.IN_APP, NotifyChannel.APP_PUSH],
        priority=ReminderPriority.URGENT
    ),
    
    ReminderType.TASK_OVERDUE: ReminderTemplate(
        type=ReminderType.TASK_OVERDUE,
        title_template="❗ 任务已逾期",
        content_template="您有任务已逾期\n任务：{task_title}\n原截止：{deadline}\n已逾期：{overdue_hours}小时\n请立即处理！",
        channels=[NotifyChannel.WECHAT_WORK, NotifyChannel.IN_APP, NotifyChannel.APP_PUSH, NotifyChannel.EMAIL],
        priority=ReminderPriority.URGENT
    ),
    
    ReminderType.PROGRESS_URGE: ReminderTemplate(
        type=ReminderType.PROGRESS_URGE,
        title_template="📊 任务进度催办",
        content_template="{urger}催办您的任务进度\n任务：{task_title}\n当前进度：{progress}%\n预期进度：{expected_progress}%\n备注：{remark}",
        channels=[NotifyChannel.WECHAT_WORK, NotifyChannel.IN_APP],
        priority=ReminderPriority.HIGH
    ),
    
    ReminderType.TASK_TRANSFERRED: ReminderTemplate(
        type=ReminderType.TASK_TRANSFERRED,
        title_template="📨 收到转办任务",
        content_template="{from_user}将任务转办给您\n任务：{task_title}\n原因：{reason}\n截止：{deadline}",
        channels=[NotifyChannel.WECHAT_WORK, NotifyChannel.IN_APP],
        priority=ReminderPriority.HIGH
    ),
    
    ReminderType.WORKFLOW_PENDING: ReminderTemplate(
        type=ReminderType.WORKFLOW_PENDING,
        title_template="🔄 待您审批",
        content_template="有流程待您处理\n流程：{workflow_name}\n发起人：{initiator}\n提交时间：{submit_time}",
        channels=[NotifyChannel.WECHAT_WORK, NotifyChannel.IN_APP],
        priority=ReminderPriority.HIGH
    ),
    
    ReminderType.TASK_APPROVED: ReminderTemplate(
        type=ReminderType.TASK_APPROVED,
        title_template="✅ 任务已通过验收",
        content_template="恭喜！您的任务已通过验收\n任务：{task_title}\n验收人：{approver}\n评语：{comment}",
        channels=[NotifyChannel.IN_APP],
        priority=ReminderPriority.NORMAL
    ),
    
    ReminderType.TASK_REJECTED: ReminderTemplate(
        type=ReminderType.TASK_REJECTED,
        title_template="❌ 任务被驳回",
        content_template="您的任务被驳回\n任务：{task_title}\n驳回人：{rejecter}\n原因：{reason}\n请修改后重新提交",
        channels=[NotifyChannel.WECHAT_WORK, NotifyChannel.IN_APP],
        priority=ReminderPriority.HIGH
    ),
    
    ReminderType.DAILY_SUMMARY: ReminderTemplate(
        type=ReminderType.DAILY_SUMMARY,
        title_template="📅 今日任务汇总",
        content_template="今日任务概况：\n待处理：{pending_count}个\n今日到期：{due_today_count}个\n已逾期：{overdue_count}个\n\n请合理安排时间完成任务",
        channels=[NotifyChannel.WECHAT_WORK],
        priority=ReminderPriority.LOW,
        merge_window=60
    ),
    
    ReminderType.WEEKLY_SUMMARY: ReminderTemplate(
        type=ReminderType.WEEKLY_SUMMARY,
        title_template="📊 本周工作汇总",
        content_template="本周工作汇总：\n完成任务：{completed_count}个\n待完成：{pending_count}个\n本周工时：{total_hours}小时\n\n下周待办：{next_week_count}个",
        channels=[NotifyChannel.EMAIL, NotifyChannel.IN_APP],
        priority=ReminderPriority.LOW
    )
}


# ==================== 通知渠道实现 ====================

class NotifyChannelHandler:
    """通知渠道处理器基类"""
    
    async def send(self, message: ReminderMessage) -> bool:
        raise NotImplementedError


class WeChatWorkHandler(NotifyChannelHandler):
    """企业微信推送"""
    
    def __init__(self, corp_id: str, agent_id: str, secret: str):
        self.corp_id = corp_id
        self.agent_id = agent_id
        self.secret = secret
        self.access_token = None
        self.token_expires = None
    
    async def get_access_token(self) -> str:
        """获取access_token"""
        # 实际实现需要调用企业微信API
        if self.access_token and self.token_expires and datetime.now() < self.token_expires:
            return self.access_token
        
        # 模拟获取token
        self.access_token = "mock_token"
        self.token_expires = datetime.now() + timedelta(hours=2)
        return self.access_token
    
    async def send(self, message: ReminderMessage) -> bool:
        """发送企业微信消息"""
        try:
            token = await self.get_access_token()
            
            # 获取用户的企业微信ID
            wechat_user_id = await self._get_wechat_user_id(message.user_id)
            
            # 构建消息体
            msg_data = {
                "touser": wechat_user_id,
                "msgtype": "textcard",
                "agentid": self.agent_id,
                "textcard": {
                    "title": message.title,
                    "description": message.content,
                    "url": self._build_task_url(message.data),
                    "btntxt": "查看详情"
                }
            }
            
            # 实际发送（这里模拟）
            print(f"[企业微信] 发送给 {message.user_name}: {message.title}")
            return True
            
        except Exception as e:
            print(f"[企业微信] 发送失败: {e}")
            return False
    
    async def _get_wechat_user_id(self, user_id: int) -> str:
        """获取用户的企业微信ID"""
        # 实际从数据库查询
        return f"user_{user_id}"
    
    def _build_task_url(self, data: Dict) -> str:
        """构建任务链接"""
        task_id = data.get("task_id", "")
        return f"https://your-domain.com/task-center?task_id={task_id}"


class EmailHandler(NotifyChannelHandler):
    """邮件推送"""
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
    
    async def send(self, message: ReminderMessage) -> bool:
        """发送邮件"""
        try:
            # 获取用户邮箱
            email = await self._get_user_email(message.user_id)
            
            # 构建邮件内容（HTML格式）
            html_content = self._build_html_content(message)
            
            # 实际发送（这里模拟）
            print(f"[邮件] 发送给 {email}: {message.title}")
            return True
            
        except Exception as e:
            print(f"[邮件] 发送失败: {e}")
            return False
    
    async def _get_user_email(self, user_id: int) -> str:
        """获取用户邮箱"""
        return f"user{user_id}@company.com"
    
    def _build_html_content(self, message: ReminderMessage) -> str:
        """构建HTML邮件内容"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #333;">{message.title}</h2>
            <div style="background: #f5f5f5; padding: 15px; border-radius: 8px;">
                <p style="white-space: pre-line;">{message.content}</p>
            </div>
            <p style="margin-top: 20px;">
                <a href="https://your-domain.com/task-center" 
                   style="background: #4F46E5; color: white; padding: 10px 20px; 
                          text-decoration: none; border-radius: 5px;">
                    查看详情
                </a>
            </p>
        </body>
        </html>
        """


class InAppHandler(NotifyChannelHandler):
    """站内消息"""
    
    def __init__(self):
        self.messages: Dict[int, List[ReminderMessage]] = defaultdict(list)
    
    async def send(self, message: ReminderMessage) -> bool:
        """保存站内消息"""
        try:
            # 实际存入数据库
            self.messages[message.user_id].append(message)
            print(f"[站内消息] 保存给 {message.user_name}: {message.title}")
            return True
        except Exception as e:
            print(f"[站内消息] 保存失败: {e}")
            return False
    
    def get_unread(self, user_id: int, limit: int = 20) -> List[ReminderMessage]:
        """获取未读消息"""
        user_msgs = self.messages.get(user_id, [])
        unread = [m for m in user_msgs if not m.is_read]
        return sorted(unread, key=lambda x: x.created_at, reverse=True)[:limit]
    
    def mark_read(self, user_id: int, message_id: str):
        """标记已读"""
        for msg in self.messages.get(user_id, []):
            if msg.id == message_id:
                msg.is_read = True
                msg.read_at = datetime.now()
                break


class AppPushHandler(NotifyChannelHandler):
    """APP推送（极光/个推等）"""
    
    def __init__(self, app_key: str, master_secret: str):
        self.app_key = app_key
        self.master_secret = master_secret
    
    async def send(self, message: ReminderMessage) -> bool:
        """发送APP推送"""
        try:
            # 获取用户设备token
            device_tokens = await self._get_device_tokens(message.user_id)
            
            if not device_tokens:
                return False
            
            # 构建推送内容
            push_data = {
                "platform": ["android", "ios"],
                "audience": {"registration_id": device_tokens},
                "notification": {
                    "alert": message.content[:100],  # 推送内容限制
                    "title": message.title,
                    "extras": {
                        "type": message.type.value,
                        "task_id": message.data.get("task_id")
                    }
                }
            }
            
            # 实际推送（这里模拟）
            print(f"[APP推送] 发送给 {message.user_name}: {message.title}")
            return True
            
        except Exception as e:
            print(f"[APP推送] 发送失败: {e}")
            return False
    
    async def _get_device_tokens(self, user_id: int) -> List[str]:
        """获取用户设备token"""
        return [f"device_token_{user_id}"]


# ==================== 提醒服务 ====================

class ReminderService:
    """提醒推送服务"""
    
    def __init__(self):
        self.handlers: Dict[NotifyChannel, NotifyChannelHandler] = {}
        self.user_settings: Dict[int, UserReminderSettings] = {}
        self.pending_messages: List[ReminderMessage] = []
        self.sent_reminders: Dict[str, datetime] = {}  # 防重复发送
        
        # 初始化默认处理器
        self._init_handlers()
    
    def _init_handlers(self):
        """初始化通知处理器"""
        self.handlers[NotifyChannel.WECHAT_WORK] = WeChatWorkHandler(
            corp_id="your_corp_id",
            agent_id="your_agent_id", 
            secret="your_secret"
        )
        self.handlers[NotifyChannel.EMAIL] = EmailHandler(
            smtp_host="smtp.company.com",
            smtp_port=465,
            username="notify@company.com",
            password="password"
        )
        self.handlers[NotifyChannel.IN_APP] = InAppHandler()
        self.handlers[NotifyChannel.APP_PUSH] = AppPushHandler(
            app_key="your_app_key",
            master_secret="your_secret"
        )
    
    def get_user_settings(self, user_id: int) -> UserReminderSettings:
        """获取用户提醒设置"""
        if user_id not in self.user_settings:
            self.user_settings[user_id] = UserReminderSettings(user_id=user_id)
        return self.user_settings[user_id]
    
    def update_user_settings(self, user_id: int, settings: Dict) -> UserReminderSettings:
        """更新用户提醒设置"""
        user_settings = self.get_user_settings(user_id)
        
        if "channels" in settings:
            user_settings.enable_wechat = settings["channels"].get("wechat", True)
            user_settings.enable_email = settings["channels"].get("email", True)
            user_settings.enable_sms = settings["channels"].get("sms", False)
            user_settings.enable_in_app = settings["channels"].get("in_app", True)
            user_settings.enable_app_push = settings["channels"].get("app_push", True)
        
        if "types" in settings:
            user_settings.enable_task_assigned = settings["types"].get("task_assigned", True)
            user_settings.enable_deadline_reminder = settings["types"].get("deadline_reminder", True)
            user_settings.enable_overdue_reminder = settings["types"].get("overdue_reminder", True)
        
        if "dnd" in settings:
            user_settings.dnd_enabled = settings["dnd"].get("enabled", False)
            user_settings.dnd_start_time = settings["dnd"].get("start", "22:00")
            user_settings.dnd_end_time = settings["dnd"].get("end", "08:00")
        
        if "deadline_remind_hours" in settings:
            user_settings.deadline_remind_hours = settings["deadline_remind_hours"]
        
        return user_settings
    
    def _generate_message_id(self, type: ReminderType, user_id: int, data: Dict) -> str:
        """生成消息ID（用于去重）"""
        key = f"{type.value}_{user_id}_{data.get('task_id', '')}_{datetime.now().strftime('%Y%m%d%H')}"
        return hashlib.md5(key.encode()).hexdigest()[:16]
    
    def _is_duplicate(self, message_id: str, window_minutes: int = 60) -> bool:
        """检查是否重复发送"""
        if message_id in self.sent_reminders:
            last_sent = self.sent_reminders[message_id]
            if datetime.now() - last_sent < timedelta(minutes=window_minutes):
                return True
        return False
    
    def _is_in_dnd(self, user_settings: UserReminderSettings) -> bool:
        """检查是否在免打扰时段"""
        if not user_settings.dnd_enabled:
            return False
        
        now = datetime.now().time()
        dnd_start = datetime.strptime(user_settings.dnd_start_time, "%H:%M").time()
        dnd_end = datetime.strptime(user_settings.dnd_end_time, "%H:%M").time()
        
        if dnd_start <= dnd_end:
            return dnd_start <= now <= dnd_end
        else:  # 跨天
            return now >= dnd_start or now <= dnd_end
    
    def _filter_channels(self, channels: List[NotifyChannel], user_settings: UserReminderSettings) -> List[NotifyChannel]:
        """根据用户设置过滤渠道"""
        result = []
        for channel in channels:
            if channel == NotifyChannel.WECHAT_WORK and user_settings.enable_wechat:
                result.append(channel)
            elif channel == NotifyChannel.EMAIL and user_settings.enable_email:
                result.append(channel)
            elif channel == NotifyChannel.SMS and user_settings.enable_sms:
                result.append(channel)
            elif channel == NotifyChannel.IN_APP and user_settings.enable_in_app:
                result.append(channel)
            elif channel == NotifyChannel.APP_PUSH and user_settings.enable_app_push:
                result.append(channel)
        return result
    
    def _is_type_enabled(self, type: ReminderType, user_settings: UserReminderSettings) -> bool:
        """检查提醒类型是否启用"""
        type_mapping = {
            ReminderType.TASK_ASSIGNED: user_settings.enable_task_assigned,
            ReminderType.DEADLINE_24H: user_settings.enable_deadline_reminder,
            ReminderType.DEADLINE_4H: user_settings.enable_deadline_reminder,
            ReminderType.DEADLINE_1H: user_settings.enable_deadline_reminder,
            ReminderType.TASK_OVERDUE: user_settings.enable_overdue_reminder,
            ReminderType.PROGRESS_URGE: user_settings.enable_progress_urge,
            ReminderType.TASK_TRANSFERRED: user_settings.enable_transfer_notify,
            ReminderType.WORKFLOW_PENDING: user_settings.enable_workflow_pending,
            ReminderType.DAILY_SUMMARY: user_settings.enable_daily_summary,
            ReminderType.WEEKLY_SUMMARY: user_settings.enable_weekly_summary,
        }
        return type_mapping.get(type, True)
    
    def create_reminder(
        self,
        type: ReminderType,
        user_id: int,
        user_name: str,
        data: Dict[str, Any],
        scheduled_at: Optional[datetime] = None
    ) -> Optional[ReminderMessage]:
        """创建提醒消息"""
        
        # 获取模板
        template = REMINDER_TEMPLATES.get(type)
        if not template:
            return None
        
        # 获取用户设置
        user_settings = self.get_user_settings(user_id)
        
        # 检查类型是否启用
        if not self._is_type_enabled(type, user_settings):
            return None
        
        # 过滤渠道
        channels = self._filter_channels(template.channels, user_settings)
        if not channels:
            return None
        
        # 生成消息ID
        message_id = self._generate_message_id(type, user_id, data)
        
        # 检查重复
        if self._is_duplicate(message_id, template.merge_window or 60):
            return None
        
        # 渲染标题和内容
        title = template.title_template.format(**data)
        content = template.content_template.format(**data)
        
        # 创建消息
        message = ReminderMessage(
            id=message_id,
            type=type,
            user_id=user_id,
            user_name=user_name,
            title=title,
            content=content,
            data=data,
            channels=channels,
            priority=template.priority,
            created_at=datetime.now(),
            scheduled_at=scheduled_at
        )
        
        return message
    
    async def send_reminder(self, message: ReminderMessage) -> Dict[NotifyChannel, bool]:
        """发送提醒"""
        results = {}
        user_settings = self.get_user_settings(message.user_id)
        
        # 检查免打扰（除了紧急消息）
        if message.priority != ReminderPriority.URGENT and self._is_in_dnd(user_settings):
            # 延迟到免打扰结束后发送
            dnd_end = datetime.strptime(user_settings.dnd_end_time, "%H:%M")
            tomorrow = datetime.now().date() + timedelta(days=1)
            message.scheduled_at = datetime.combine(tomorrow, dnd_end.time())
            self.pending_messages.append(message)
            return {"deferred": True}
        
        # 发送到各渠道
        for channel in message.channels:
            handler = self.handlers.get(channel)
            if handler:
                success = await handler.send(message)
                results[channel] = success
        
        # 记录已发送
        if any(results.values()):
            message.is_sent = True
            message.sent_at = datetime.now()
            self.sent_reminders[message.id] = datetime.now()
        
        return results
    
    async def send_task_assigned(
        self,
        user_id: int,
        user_name: str,
        task_id: int,
        task_title: str,
        assigner: str,
        deadline: str,
        priority: str
    ):
        """发送任务分配提醒"""
        message = self.create_reminder(
            type=ReminderType.TASK_ASSIGNED,
            user_id=user_id,
            user_name=user_name,
            data={
                "task_id": task_id,
                "task_title": task_title,
                "assigner": assigner,
                "deadline": deadline,
                "priority": priority
            }
        )
        if message:
            await self.send_reminder(message)
    
    async def send_deadline_reminder(
        self,
        user_id: int,
        user_name: str,
        task_id: int,
        task_title: str,
        deadline: str,
        progress: int,
        hours_left: int
    ):
        """发送截止时间提醒"""
        # 根据剩余时间选择提醒类型
        if hours_left <= 1:
            type = ReminderType.DEADLINE_1H
        elif hours_left <= 4:
            type = ReminderType.DEADLINE_4H
        else:
            type = ReminderType.DEADLINE_24H
        
        message = self.create_reminder(
            type=type,
            user_id=user_id,
            user_name=user_name,
            data={
                "task_id": task_id,
                "task_title": task_title,
                "deadline": deadline,
                "progress": progress
            }
        )
        if message:
            await self.send_reminder(message)
    
    async def send_overdue_reminder(
        self,
        user_id: int,
        user_name: str,
        task_id: int,
        task_title: str,
        deadline: str,
        overdue_hours: int
    ):
        """发送逾期提醒"""
        message = self.create_reminder(
            type=ReminderType.TASK_OVERDUE,
            user_id=user_id,
            user_name=user_name,
            data={
                "task_id": task_id,
                "task_title": task_title,
                "deadline": deadline,
                "overdue_hours": overdue_hours
            }
        )
        if message:
            await self.send_reminder(message)
    
    async def send_transfer_notify(
        self,
        user_id: int,
        user_name: str,
        task_id: int,
        task_title: str,
        from_user: str,
        reason: str,
        deadline: str
    ):
        """发送转办通知"""
        message = self.create_reminder(
            type=ReminderType.TASK_TRANSFERRED,
            user_id=user_id,
            user_name=user_name,
            data={
                "task_id": task_id,
                "task_title": task_title,
                "from_user": from_user,
                "reason": reason,
                "deadline": deadline
            }
        )
        if message:
            await self.send_reminder(message)
    
    async def send_daily_summary(
        self,
        user_id: int,
        user_name: str,
        pending_count: int,
        due_today_count: int,
        overdue_count: int
    ):
        """发送每日汇总"""
        message = self.create_reminder(
            type=ReminderType.DAILY_SUMMARY,
            user_id=user_id,
            user_name=user_name,
            data={
                "pending_count": pending_count,
                "due_today_count": due_today_count,
                "overdue_count": overdue_count
            }
        )
        if message:
            await self.send_reminder(message)
    
    def get_unread_notifications(self, user_id: int, limit: int = 20) -> List[Dict]:
        """获取未读站内消息"""
        handler = self.handlers.get(NotifyChannel.IN_APP)
        if isinstance(handler, InAppHandler):
            messages = handler.get_unread(user_id, limit)
            return [m.to_dict() for m in messages]
        return []
    
    def mark_notification_read(self, user_id: int, message_id: str):
        """标记消息已读"""
        handler = self.handlers.get(NotifyChannel.IN_APP)
        if isinstance(handler, InAppHandler):
            handler.mark_read(user_id, message_id)


# ==================== 定时任务扫描器 ====================

class ReminderScheduler:
    """提醒定时扫描器"""
    
    def __init__(self, reminder_service: ReminderService):
        self.service = reminder_service
        self.running = False
    
    async def scan_deadline_reminders(self):
        """扫描即将到期的任务"""
        # 实际从数据库查询
        tasks_to_remind = [
            {"user_id": 1, "user_name": "张三", "task_id": 1001, "task_title": "机械结构设计", 
             "deadline": "2025-01-04 18:00", "progress": 60, "hours_left": 20},
            {"user_id": 2, "user_name": "李四", "task_id": 1002, "task_title": "电气图纸", 
             "deadline": "2025-01-03 17:00", "progress": 30, "hours_left": 3},
        ]
        
        for task in tasks_to_remind:
            await self.service.send_deadline_reminder(**task)
    
    async def scan_overdue_tasks(self):
        """扫描已逾期的任务"""
        overdue_tasks = [
            {"user_id": 1, "user_name": "张三", "task_id": 1003, "task_title": "文档整理",
             "deadline": "2025-01-02 18:00", "overdue_hours": 12}
        ]
        
        for task in overdue_tasks:
            await self.service.send_overdue_reminder(**task)
    
    async def send_daily_summaries(self):
        """发送每日汇总"""
        users = [
            {"user_id": 1, "user_name": "张三", "pending_count": 5, "due_today_count": 2, "overdue_count": 1},
            {"user_id": 2, "user_name": "李四", "pending_count": 3, "due_today_count": 1, "overdue_count": 0},
        ]
        
        for user in users:
            await self.service.send_daily_summary(**user)
    
    async def run_once(self):
        """执行一次扫描"""
        print(f"[{datetime.now()}] 开始扫描提醒...")
        await self.scan_deadline_reminders()
        await self.scan_overdue_tasks()
        print(f"[{datetime.now()}] 扫描完成")
    
    async def start(self, interval_minutes: int = 15):
        """启动定时扫描"""
        self.running = True
        while self.running:
            await self.run_once()
            await asyncio.sleep(interval_minutes * 60)
    
    def stop(self):
        """停止扫描"""
        self.running = False


# ==================== 工厂方法 ====================

_reminder_service: Optional[ReminderService] = None

def get_reminder_service() -> ReminderService:
    """获取提醒服务单例"""
    global _reminder_service
    if _reminder_service is None:
        _reminder_service = ReminderService()
    return _reminder_service


# ==================== 测试 ====================

if __name__ == "__main__":
    async def test():
        service = get_reminder_service()
        
        print("=" * 60)
        print("测试：发送任务分配提醒")
        print("=" * 60)
        
        await service.send_task_assigned(
            user_id=1,
            user_name="张三",
            task_id=1001,
            task_title="XX设备机械结构设计",
            assigner="张经理",
            deadline="2025-01-05 18:00",
            priority="高"
        )
        
        print("\n" + "=" * 60)
        print("测试：发送截止提醒")
        print("=" * 60)
        
        await service.send_deadline_reminder(
            user_id=1,
            user_name="张三",
            task_id=1001,
            task_title="XX设备机械结构设计",
            deadline="2025-01-04 18:00",
            progress=60,
            hours_left=4
        )
        
        print("\n" + "=" * 60)
        print("测试：获取未读消息")
        print("=" * 60)
        
        unread = service.get_unread_notifications(user_id=1)
        for msg in unread:
            print(f"- {msg['title']}")
        
        print("\n" + "=" * 60)
        print("测试：用户提醒设置")
        print("=" * 60)
        
        settings = service.get_user_settings(1)
        print(json.dumps(settings.to_dict(), indent=2, ensure_ascii=False))
    
    asyncio.run(test())
