# -*- coding: utf-8 -*-
"""
任务评论 - 自动生成
从 task_center.py 拆分
"""

# -*- coding: utf-8 -*-
"""
个人任务中心 API endpoints
核心功能：多来源任务聚合、智能排序、转办协作
"""

import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.task_center import (
    TaskComment,
    TaskUnified,
)
from app.models.user import User
from app.schemas.task_center import (
    TaskCommentCreate,
    TaskCommentResponse,
)
from app.services.sales_reminder import create_notification
from app.utils.db_helpers import get_or_404

router = APIRouter()
logger = logging.getLogger(__name__)

# 使用统一的编码生成工具和日志工具


from fastapi import APIRouter

router = APIRouter(
    prefix="/task-center/comments",
    tags=["comments"]
)

# 共 2 个路由

# ==================== 任务评论 ====================

@router.post("/tasks/{task_id}/comments", response_model=TaskCommentResponse, status_code=status.HTTP_201_CREATED)
def create_task_comment(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    comment_in: TaskCommentCreate,
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    任务评论（协作沟通）
    """
    task = get_or_404(db, TaskUnified, task_id, "任务不存在")

    # 验证父评论
    parent_comment = None
    if comment_in.parent_id:
        parent_comment = db.query(TaskComment).filter(TaskComment.id == comment_in.parent_id).first()
        if not parent_comment or parent_comment.task_id != task_id:
            raise HTTPException(status_code=400, detail="父评论不存在或不属于此任务")

    comment = TaskComment(
        task_id=task_id,
        content=comment_in.content,
        comment_type=comment_in.comment_type,
        parent_id=comment_in.parent_id,
        commenter_id=current_user.id,
        commenter_name=current_user.real_name or current_user.username,
        mentioned_users=comment_in.mentioned_users if comment_in.mentioned_users else []
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    # 通知被@的用户
    if comment_in.mentioned_users:
        try:
            for user_id in comment_in.mentioned_users:
                if user_id != current_user.id:  # 不通知自己
                    mentioned_user = db.query(User).filter(User.id == user_id).first()
                    if mentioned_user:
                        create_notification(
                            db=db,
                            user_id=user_id,
                            notification_type="TASK_MENTIONED",
                            title="任务评论中@了您",
                            content=f"{current_user.real_name or current_user.username} 在任务「{task.title}」的评论中@了您：{comment_in.content[:100]}",
                            source_type="task",
                            source_id=task.id,
                            link_url=f"/tasks/{task.id}",
                            priority="NORMAL",
                            extra_data={"task_id": task.id, "comment_id": comment.id, "commenter": current_user.real_name or current_user.username}
                        )
            db.commit()
        except Exception:
            # 通知发送失败不影响主流程
            logger.warning("任务评论@通知发送失败，不影响主流程", exc_info=True)

    return TaskCommentResponse(
        id=comment.id,
        task_id=comment.task_id,
        content=comment.content,
        comment_type=comment.comment_type,
        parent_id=comment.parent_id,
        commenter_id=comment.commenter_id,
        commenter_name=comment.commenter_name,
        mentioned_users=comment.mentioned_users if comment.mentioned_users else [],
        created_at=comment.created_at,
        replies=None
    )


@router.get("/tasks/{task_id}/comments", response_model=List[TaskCommentResponse], status_code=status.HTTP_200_OK)
def get_task_comments(
    *,
    db: Session = Depends(deps.get_db),
    task_id: int,
    current_user: User = Depends(security.require_permission("task_center:read")),
) -> Any:
    """
    获取任务评论列表
    """
    task = get_or_404(db, TaskUnified, task_id, "任务不存在")

    comments = db.query(TaskComment).filter(
        TaskComment.task_id == task_id,
        TaskComment.parent_id.is_(None)  # 只获取顶级评论
    ).order_by(TaskComment.created_at).all()

    items = []
    for comment in comments:
        # 获取回复
        replies = db.query(TaskComment).filter(
            TaskComment.parent_id == comment.id
        ).order_by(TaskComment.created_at).all()

        reply_items = []
        for reply in replies:
            reply_items.append(TaskCommentResponse(
                id=reply.id,
                task_id=reply.task_id,
                content=reply.content,
                comment_type=reply.comment_type,
                parent_id=reply.parent_id,
                commenter_id=reply.commenter_id,
                commenter_name=reply.commenter_name,
                mentioned_users=reply.mentioned_users if reply.mentioned_users else [],
                created_at=reply.created_at,
                replies=None
            ))

        items.append(TaskCommentResponse(
            id=comment.id,
            task_id=comment.task_id,
            content=comment.content,
            comment_type=comment.comment_type,
            parent_id=comment.parent_id,
            commenter_id=comment.commenter_id,
            commenter_name=comment.commenter_name,
            mentioned_users=comment.mentioned_users if comment.mentioned_users else [],
            created_at=comment.created_at,
            replies=reply_items if reply_items else None
        ))

    return items


