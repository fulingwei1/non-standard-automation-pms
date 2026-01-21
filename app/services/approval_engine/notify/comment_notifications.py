# -*- coding: utf-8 -*-
"""
审批通知服务 - 评论通知

提供评论和@提及通知功能
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.approval import ApprovalInstance

class CommentNotificationsMixin:
    """评论通知 Mixin"""

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
