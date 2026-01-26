# -*- coding: utf-8 -*-
"""
审批代理人服务

处理审批代理人的配置和自动转派
"""

from datetime import date, datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.approval import (
    ApprovalDelegate,
    ApprovalDelegateLog,
    ApprovalTask,
)


class ApprovalDelegateService:
    """审批代理人服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_active_delegate(
        self,
        user_id: int,
        template_id: Optional[int] = None,
        check_date: Optional[date] = None,
    ) -> Optional[ApprovalDelegate]:
        """
        获取用户当前生效的代理人配置

        Args:
            user_id: 原审批人ID
            template_id: 审批模板ID（用于检查代理范围）
            check_date: 检查日期，默认为今天

        Returns:
            生效的代理人配置，如无则返回None
        """
        if check_date is None:
            check_date = date.today()

        # 查询生效的代理配置
        query = self.db.query(ApprovalDelegate).filter(
            ApprovalDelegate.user_id == user_id,
            ApprovalDelegate.is_active == True,
            ApprovalDelegate.start_date <= check_date,
            ApprovalDelegate.end_date >= check_date,
        )

        delegates = query.all()

        for delegate in delegates:
            # 检查代理范围
            if delegate.scope == "ALL":
                return delegate
            elif delegate.scope == "TEMPLATE" and template_id:
                if delegate.template_ids and template_id in delegate.template_ids:
                    return delegate
            elif delegate.scope == "CATEGORY" and template_id:
                # 需要查询模板的分类
                from app.models.approval import ApprovalTemplate

                template = (
                    self.db.query(ApprovalTemplate)
                    .filter(ApprovalTemplate.id == template_id)
                    .first()
                )
                if template and delegate.categories:
                    if template.category in delegate.categories:
                        return delegate

        return None

    def apply_delegation(
        self,
        task: ApprovalTask,
        original_assignee_id: int,
    ) -> Optional[ApprovalTask]:
        """
        应用代理人配置，将任务转给代理人

        Args:
            task: 审批任务
            original_assignee_id: 原审批人ID

        Returns:
            更新后的任务（如果应用了代理），否则返回None
        """
        instance = task.instance
        delegate_config = self.get_active_delegate(
            user_id=original_assignee_id,
            template_id=instance.template_id,
        )

        if not delegate_config:
            return None

        # 记录原审批人
        task.original_assignee_id = original_assignee_id
        task.assignee_type = "DELEGATED"
        task.assignee_id = delegate_config.delegate_id

        # 获取代理人姓名
        from app.models.user import User

        delegate_user = (
            self.db.query(User).filter(User.id == delegate_config.delegate_id).first()
        )
        if delegate_user:
            task.assignee_name = delegate_user.real_name or delegate_user.username

        # 记录代理日志
        log = ApprovalDelegateLog(
            delegate_config_id=delegate_config.id,
            task_id=task.id,
            instance_id=instance.id,
            original_user_id=original_assignee_id,
            delegate_user_id=delegate_config.delegate_id,
        )
        self.db.add(log)

        return task

    def create_delegate(
        self,
        user_id: int,
        delegate_id: int,
        start_date: date,
        end_date: date,
        scope: str = "ALL",
        template_ids: Optional[List[int]] = None,
        categories: Optional[List[str]] = None,
        reason: Optional[str] = None,
        notify_original: bool = True,
        notify_delegate: bool = True,
        created_by: Optional[int] = None,
    ) -> ApprovalDelegate:
        """
        创建代理人配置

        Args:
            user_id: 原审批人ID
            delegate_id: 代理人ID
            start_date: 开始日期
            end_date: 结束日期
            scope: 代理范围（ALL/TEMPLATE/CATEGORY）
            template_ids: 指定模板ID列表（scope=TEMPLATE时）
            categories: 指定分类列表（scope=CATEGORY时）
            reason: 代理原因
            notify_original: 是否通知原审批人
            notify_delegate: 是否通知代理人
            created_by: 创建人ID

        Returns:
            创建的代理配置
        """
        # 检查是否已存在重叠的代理配置
        existing = (
            self.db.query(ApprovalDelegate)
            .filter(
                ApprovalDelegate.user_id == user_id,
                ApprovalDelegate.is_active == True,
                ApprovalDelegate.end_date >= start_date,
                ApprovalDelegate.start_date <= end_date,
            )
            .first()
        )

        if existing:
            raise ValueError("存在重叠的代理配置")

        delegate = ApprovalDelegate(
            user_id=user_id,
            delegate_id=delegate_id,
            scope=scope,
            template_ids=template_ids,
            categories=categories,
            start_date=start_date,
            end_date=end_date,
            is_active=True,
            reason=reason,
            notify_original=notify_original,
            notify_delegate=notify_delegate,
            created_by=created_by or user_id,
        )

        self.db.add(delegate)
        self.db.flush()

        return delegate

    def update_delegate(
        self,
        delegate_id: int,
        **kwargs,
    ) -> Optional[ApprovalDelegate]:
        """
        更新代理人配置

        Args:
            delegate_id: 代理配置ID
            **kwargs: 要更新的字段

        Returns:
            更新后的代理配置
        """
        delegate = (
            self.db.query(ApprovalDelegate)
            .filter(ApprovalDelegate.id == delegate_id)
            .first()
        )

        if not delegate:
            return None

        allowed_fields = {
            "delegate_id",
            "scope",
            "template_ids",
            "categories",
            "start_date",
            "end_date",
            "reason",
            "notify_original",
            "notify_delegate",
            "is_active",
        }

        for key, value in kwargs.items():
            if key in allowed_fields:
                setattr(delegate, key, value)

        return delegate

    def cancel_delegate(self, delegate_id: int) -> bool:
        """
        取消代理人配置

        Args:
            delegate_id: 代理配置ID

        Returns:
            是否成功取消
        """
        delegate = (
            self.db.query(ApprovalDelegate)
            .filter(ApprovalDelegate.id == delegate_id)
            .first()
        )

        if not delegate:
            return False

        delegate.is_active = False
        return True

    def get_user_delegates(
        self,
        user_id: int,
        include_inactive: bool = False,
    ) -> List[ApprovalDelegate]:
        """
        获取用户的所有代理配置（作为原审批人）

        Args:
            user_id: 用户ID
            include_inactive: 是否包含已失效的配置

        Returns:
            代理配置列表
        """
        query = self.db.query(ApprovalDelegate).filter(
            ApprovalDelegate.user_id == user_id,
        )

        if not include_inactive:
            query = query.filter(ApprovalDelegate.is_active == True)

        return query.order_by(ApprovalDelegate.start_date.desc()).all()

    def get_delegated_to_user(
        self,
        delegate_id: int,
        include_inactive: bool = False,
    ) -> List[ApprovalDelegate]:
        """
        获取用户作为代理人的所有配置

        Args:
            delegate_id: 代理人用户ID
            include_inactive: 是否包含已失效的配置

        Returns:
            代理配置列表
        """
        query = self.db.query(ApprovalDelegate).filter(
            ApprovalDelegate.delegate_id == delegate_id,
        )

        if not include_inactive:
            query = query.filter(ApprovalDelegate.is_active == True)

        return query.order_by(ApprovalDelegate.start_date.desc()).all()

    def record_delegate_action(
        self,
        delegate_log_id: int,
        action: str,
    ):
        """
        记录代理人的审批操作

        Args:
            delegate_log_id: 代理日志ID
            action: 操作类型（APPROVE/REJECT等）
        """
        log = (
            self.db.query(ApprovalDelegateLog)
            .filter(ApprovalDelegateLog.id == delegate_log_id)
            .first()
        )

        if log:
            log.action = action
            log.action_at = datetime.now()

    def notify_original_user(self, delegate_log_id: int):
        """
        通知原审批人代理审批已完成

        Args:
            delegate_log_id: 代理日志ID
        """
        log = (
            self.db.query(ApprovalDelegateLog)
            .filter(ApprovalDelegateLog.id == delegate_log_id)
            .first()
        )

        if log:
            log.original_notified = True
            log.original_notified_at = datetime.now()

            # 获取代理配置
            config = (
                self.db.query(ApprovalDelegate)
                .filter(ApprovalDelegate.id == log.delegate_config_id)
                .first()
            )

            if config and config.notify_original:
                # 发送通知给原审批人
                self._send_delegate_notification(log, config)

    def cleanup_expired_delegates(self):
        """
        清理过期的代理配置

        将结束日期已过的配置标记为不活跃
        """
        today = date.today()

        self.db.query(ApprovalDelegate).filter(
            ApprovalDelegate.is_active == True,
            ApprovalDelegate.end_date < today,
        ).update({"is_active": False}, synchronize_session=False)

    def _send_delegate_notification(
        self, log: ApprovalDelegateLog, config: ApprovalDelegate
    ):
        """
        发送代理审批完成通知给原审批人

        Args:
            log: 代理日志记录
            config: 代理配置
        """
        from app.services.approval_engine.notify import ApprovalNotifyService

        try:
            # 获取审批任务信息
            task = (
                self.db.query(ApprovalTask)
                .filter(ApprovalTask.id == log.task_id)
                .first()
            )

            if not task or not task.instance:
                return

            instance = task.instance

            # 构建通知内容
            action_text = {
                "APPROVED": "通过",
                "REJECTED": "驳回",
            }.get(log.action, "处理")

            notification = {
                "type": "APPROVAL_DELEGATED_RESULT",
                "title": f"代理审批已{action_text}: {instance.title}",
                "content": f"您的代理人已{action_text}审批「{instance.title}」",
                "receiver_id": config.user_id,  # 原审批人
                "instance_id": instance.id,
                "task_id": task.id,
                "urgency": "NORMAL",
                "created_at": datetime.now().isoformat(),
            }

            # 使用通知服务发送
            notify_service = ApprovalNotifyService(self.db)
            notify_service._send_notification(notification)

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"发送代理审批通知失败: {e}")
