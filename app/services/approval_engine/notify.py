# -*- coding: utf-8 -*-
"""
审批通知服务

处理审批流程中的各类通知
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.approval import (
    ApprovalCarbonCopy,
    ApprovalInstance,
    ApprovalTask,
)
from app.models.notification import Notification, NotificationSettings


logger = logging.getLogger(__name__)

# 简单的内存缓存用于通知去重（生产环境建议用 Redis）
_notification_dedup_cache: Dict[str, datetime] = {}
_DEDUP_WINDOW_MINUTES = 30  # 去重窗口：30分钟内相同通知不重复发送


class ApprovalNotifyService:
    """审批通知服务"""

    def __init__(self, db: Session):
        self.db = db

    def notify_pending(
        self,
        task: ApprovalTask,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知待审批

        Args:
            task: 审批任务
            extra_context: 额外上下文信息
        """
        instance = task.instance
        notification = {
            "type": "APPROVAL_PENDING",
            "title": f"您有新的审批待处理: {instance.title}",
            "content": instance.summary or "",
            "receiver_id": task.assignee_id,
            "instance_id": instance.id,
            "task_id": task.id,
            "urgency": instance.urgency,
            "created_at": datetime.now().isoformat(),
        }

        self._send_notification(notification)

    def notify_approved(
        self,
        instance: ApprovalInstance,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知审批通过

        Args:
            instance: 审批实例
            extra_context: 额外上下文信息
        """
        notification = {
            "type": "APPROVAL_APPROVED",
            "title": f"审批已通过: {instance.title}",
            "content": f"您发起的审批「{instance.title}」已通过",
            "receiver_id": instance.initiator_id,
            "instance_id": instance.id,
            "created_at": datetime.now().isoformat(),
        }

        self._send_notification(notification)

    def notify_rejected(
        self,
        instance: ApprovalInstance,
        rejector_name: Optional[str] = None,
        reject_comment: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知审批驳回

        Args:
            instance: 审批实例
            rejector_name: 驳回人姓名
            reject_comment: 驳回原因
            extra_context: 额外上下文信息
        """
        content = f"您发起的审批「{instance.title}」已被驳回"
        if rejector_name:
            content += f"（驳回人: {rejector_name}）"
        if reject_comment:
            content += f"\n驳回原因: {reject_comment}"

        notification = {
            "type": "APPROVAL_REJECTED",
            "title": f"审批已驳回: {instance.title}",
            "content": content,
            "receiver_id": instance.initiator_id,
            "instance_id": instance.id,
            "created_at": datetime.now().isoformat(),
        }

        self._send_notification(notification)

    def notify_cc(
        self,
        cc_record: ApprovalCarbonCopy,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知抄送

        Args:
            cc_record: 抄送记录
            extra_context: 额外上下文信息
        """
        instance = cc_record.instance
        notification = {
            "type": "APPROVAL_CC",
            "title": f"您收到一条审批抄送: {instance.title}",
            "content": instance.summary or "",
            "receiver_id": cc_record.cc_user_id,
            "instance_id": instance.id,
            "created_at": datetime.now().isoformat(),
        }

        self._send_notification(notification)

    def notify_timeout_warning(
        self,
        task: ApprovalTask,
        hours_remaining: int,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知即将超时

        Args:
            task: 审批任务
            hours_remaining: 剩余小时数
            extra_context: 额外上下文信息
        """
        instance = task.instance
        notification = {
            "type": "APPROVAL_TIMEOUT_WARNING",
            "title": f"审批即将超时: {instance.title}",
            "content": f"您有一条审批将在{hours_remaining}小时后超时，请尽快处理",
            "receiver_id": task.assignee_id,
            "instance_id": instance.id,
            "task_id": task.id,
            "urgency": "URGENT",
            "created_at": datetime.now().isoformat(),
        }

        self._send_notification(notification)

    def notify_remind(
        self,
        task: ApprovalTask,
        reminder_id: int,
        reminder_name: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        催办通知

        Args:
            task: 审批任务
            reminder_id: 催办人ID
            reminder_name: 催办人姓名
            extra_context: 额外上下文信息
        """
        instance = task.instance
        content = f"您有一条待处理的审批「{instance.title}」"
        if reminder_name:
            content += f"，{reminder_name}正在催促您尽快处理"

        notification = {
            "type": "APPROVAL_REMIND",
            "title": f"催办提醒: {instance.title}",
            "content": content,
            "receiver_id": task.assignee_id,
            "instance_id": instance.id,
            "task_id": task.id,
            "urgency": "URGENT",
            "created_at": datetime.now().isoformat(),
        }

        self._send_notification(notification)

    def notify_withdrawn(
        self,
        instance: ApprovalInstance,
        affected_user_ids: List[int],
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知审批已撤回

        Args:
            instance: 审批实例
            affected_user_ids: 受影响的用户ID列表
            extra_context: 额外上下文信息
        """
        for user_id in affected_user_ids:
            notification = {
                "type": "APPROVAL_WITHDRAWN",
                "title": f"审批已撤回: {instance.title}",
                "content": f"审批「{instance.title}」已被发起人撤回",
                "receiver_id": user_id,
                "instance_id": instance.id,
                "created_at": datetime.now().isoformat(),
            }

            self._send_notification(notification)

    def notify_transferred(
        self,
        task: ApprovalTask,
        from_user_id: int,
        from_user_name: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知转审

        Args:
            task: 审批任务（已转给新审批人）
            from_user_id: 原审批人ID
            from_user_name: 原审批人姓名
            extra_context: 额外上下文信息
        """
        instance = task.instance
        content = f"您收到一条转审的审批「{instance.title}」"
        if from_user_name:
            content += f"，由{from_user_name}转交给您处理"

        notification = {
            "type": "APPROVAL_TRANSFERRED",
            "title": f"转审通知: {instance.title}",
            "content": content,
            "receiver_id": task.assignee_id,
            "instance_id": instance.id,
            "task_id": task.id,
            "urgency": instance.urgency,
            "created_at": datetime.now().isoformat(),
        }

        self._send_notification(notification)

    def notify_delegated(
        self,
        task: ApprovalTask,
        original_user_name: Optional[str] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知代理审批

        Args:
            task: 审批任务（已转给代理人）
            original_user_name: 原审批人姓名
            extra_context: 额外上下文信息
        """
        instance = task.instance
        content = f"您代理了一条审批「{instance.title}」"
        if original_user_name:
            content += f"（原审批人: {original_user_name}）"

        notification = {
            "type": "APPROVAL_DELEGATED",
            "title": f"代理审批通知: {instance.title}",
            "content": content,
            "receiver_id": task.assignee_id,
            "instance_id": instance.id,
            "task_id": task.id,
            "urgency": instance.urgency,
            "created_at": datetime.now().isoformat(),
        }

        self._send_notification(notification)

    def notify_add_approver(
        self,
        task: ApprovalTask,
        added_by_name: Optional[str] = None,
        position: str = "AFTER",
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知加签

        Args:
            task: 新创建的审批任务
            added_by_name: 加签操作人姓名
            position: 加签位置（BEFORE/AFTER）
            extra_context: 额外上下文信息
        """
        instance = task.instance
        position_text = "前加签" if position == "BEFORE" else "后加签"
        content = f"您被添加为审批人（{position_text}）: {instance.title}"
        if added_by_name:
            content += f"，由{added_by_name}添加"

        notification = {
            "type": "APPROVAL_ADD_APPROVER",
            "title": f"加签通知: {instance.title}",
            "content": content,
            "receiver_id": task.assignee_id,
            "instance_id": instance.id,
            "task_id": task.id,
            "urgency": instance.urgency,
            "created_at": datetime.now().isoformat(),
        }

        self._send_notification(notification)

    def notify_comment(
        self,
        instance: ApprovalInstance,
        commenter_name: str,
        comment_content: str,
        mentioned_user_ids: Optional[List[int]] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ):
        """
        通知评论

        Args:
            instance: 审批实例
            commenter_name: 评论人姓名
            comment_content: 评论内容
            mentioned_user_ids: @提及的用户ID列表
            extra_context: 额外上下文信息
        """
        # 通知@提及的用户
        if mentioned_user_ids:
            for user_id in mentioned_user_ids:
                notification = {
                    "type": "APPROVAL_COMMENT_MENTION",
                    "title": f"{commenter_name}在审批中@了您",
                    "content": f"审批「{instance.title}」中有新评论：{comment_content[:100]}",
                    "receiver_id": user_id,
                    "instance_id": instance.id,
                    "created_at": datetime.now().isoformat(),
                }

                self._send_notification(notification)

    def _generate_dedup_key(self, notification: Dict[str, Any]) -> str:
        """生成通知去重的唯一键"""
        key_parts = [
            str(notification.get("type", "")),
            str(notification.get("receiver_id", "")),
            str(notification.get("instance_id", "")),
            str(notification.get("task_id", "")),
        ]
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _is_duplicate(self, dedup_key: str) -> bool:
        """检查是否为重复通知（在去重窗口内）"""
        global _notification_dedup_cache

        now = datetime.now()

        # 清理过期的缓存项
        expired_keys = [
            k for k, v in _notification_dedup_cache.items()
            if now - v > timedelta(minutes=_DEDUP_WINDOW_MINUTES)
        ]
        for k in expired_keys:
            del _notification_dedup_cache[k]

        # 检查是否存在
        if dedup_key in _notification_dedup_cache:
            return True

        # 添加到缓存
        _notification_dedup_cache[dedup_key] = now
        return False

    def _check_user_preferences(self, user_id: int, notification_type: str) -> Dict[str, bool]:
        """
        检查用户通知偏好设置

        Returns:
            包含各渠道是否启用的字典
        """
        default_prefs = {
            "system_enabled": True,
            "email_enabled": False,
            "wechat_enabled": False,
            "sms_enabled": False,
        }

        try:
            settings = (
                self.db.query(NotificationSettings)
                .filter(NotificationSettings.user_id == user_id)
                .first()
            )

            if not settings:
                return default_prefs

            # 检查用户是否启用审批通知
            if not settings.approval_notifications:
                return {k: False for k in default_prefs}

            # 检查免打扰时间
            if settings.quiet_hours_start and settings.quiet_hours_end:
                now_time = datetime.now().strftime("%H:%M")
                if settings.quiet_hours_start <= now_time <= settings.quiet_hours_end:
                    # 免打扰时间内只发站内通知
                    return {
                        "system_enabled": settings.system_enabled,
                        "email_enabled": False,
                        "wechat_enabled": False,
                        "sms_enabled": False,
                    }

            return {
                "system_enabled": settings.system_enabled,
                "email_enabled": settings.email_enabled,
                "wechat_enabled": settings.wechat_enabled,
                "sms_enabled": settings.sms_enabled,
            }

        except Exception as e:
            logger.warning(f"获取用户通知偏好失败: {e}")
            return default_prefs

    def _send_notification(self, notification: Dict[str, Any]):
        """
        发送通知

        统一通知出口，支持：
        - 站内消息
        - 邮件
        - 企业微信
        - 飞书
        - 短信
        - 推送
        """
        receiver_id = notification.get("receiver_id")
        if not receiver_id:
            logger.warning("通知缺少 receiver_id，跳过发送")
            return

        # 1. 通知去重检查
        dedup_key = self._generate_dedup_key(notification)
        if self._is_duplicate(dedup_key):
            logger.debug(f"重复通知已跳过: {notification.get('type')}")
            return

        # 2. 检查用户偏好
        prefs = self._check_user_preferences(receiver_id, notification.get("type", ""))

        # 3. 发送站内通知
        if prefs.get("system_enabled", True):
            try:
                self._save_system_notification(notification)
            except Exception as e:
                logger.error(f"保存站内通知失败: {e}")

        # 4. 发送其他渠道通知（异步）
        # 注：实际生产环境建议使用 Celery 异步任务
        if prefs.get("email_enabled"):
            self._queue_email_notification(notification)

        if prefs.get("wechat_enabled"):
            self._queue_wechat_notification(notification)

        logger.info(f"审批通知已发送: type={notification.get('type')}, receiver={receiver_id}")

    def _save_system_notification(self, notification: Dict[str, Any]):
        """保存站内通知到数据库"""
        try:
            # 映射通知类型
            type_mapping = {
                "APPROVAL_PENDING": "APPROVAL_PENDING",
                "APPROVAL_APPROVED": "APPROVAL_RESULT",
                "APPROVAL_REJECTED": "APPROVAL_RESULT",
                "APPROVAL_CC": "APPROVAL_CC",
                "APPROVAL_TIMEOUT_WARNING": "APPROVAL_PENDING",
                "APPROVAL_REMIND": "APPROVAL_PENDING",
                "APPROVAL_WITHDRAWN": "APPROVAL_RESULT",
                "APPROVAL_TRANSFERRED": "APPROVAL_PENDING",
                "APPROVAL_DELEGATED": "APPROVAL_PENDING",
                "APPROVAL_ADD_APPROVER": "APPROVAL_PENDING",
                "APPROVAL_COMMENT_MENTION": "APPROVAL_PENDING",
            }

            # 映射优先级
            urgency = notification.get("urgency", "NORMAL")
            priority_mapping = {
                "LOW": "LOW",
                "NORMAL": "NORMAL",
                "HIGH": "HIGH",
                "URGENT": "URGENT",
            }

            db_notification = Notification(
                user_id=notification["receiver_id"],
                notification_type=type_mapping.get(notification.get("type"), "APPROVAL_PENDING"),
                source_type="approval",
                source_id=notification.get("instance_id"),
                title=notification.get("title", "审批通知"),
                content=notification.get("content", ""),
                link_url=f"/approvals/{notification.get('instance_id')}",
                priority=priority_mapping.get(urgency, "NORMAL"),
                extra_data={
                    "original_type": notification.get("type"),
                    "task_id": notification.get("task_id"),
                    "instance_id": notification.get("instance_id"),
                },
            )

            self.db.add(db_notification)
            self.db.commit()

        except Exception as e:
            logger.error(f"保存站内通知异常: {e}")
            self.db.rollback()
            raise

    def _queue_email_notification(self, notification: Dict[str, Any]):
        """
        将邮件通知加入队列

        注：实际生产环境建议使用 Celery 异步任务
        目前仅记录日志，后续集成邮件服务
        """
        logger.info(f"[邮件队列] 审批通知: {notification.get('title')}")
        # TODO: 集成邮件发送服务
        # from app.services.email_service import send_email_async
        # send_email_async.delay(receiver_id, subject, content)

    def _queue_wechat_notification(self, notification: Dict[str, Any]):
        """
        将企业微信通知加入队列

        注：实际生产环境建议使用 Celery 异步任务
        目前仅记录日志，后续集成企微 SDK
        """
        logger.info(f"[企微队列] 审批通知: {notification.get('title')}")
        # TODO: 集成企业微信 SDK
        # from app.services.wechat_service import send_wechat_async
        # send_wechat_async.delay(receiver_id, message)

    def batch_notify(self, notifications: List[Dict[str, Any]]):
        """
        批量发送通知

        Args:
            notifications: 通知列表
        """
        for notification in notifications:
            self._send_notification(notification)
