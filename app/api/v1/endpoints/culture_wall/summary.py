# -*- coding: utf-8 -*-
"""
文化墙汇总
"""

from datetime import date
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.user import User
from app.schemas.culture_wall import CultureWallSummary

router = APIRouter()


@router.get("/culture-wall/summary", response_model=CultureWallSummary)
def get_culture_wall_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取文化墙汇总数据（用于滚动播放）
    根据配置过滤内容和角色
    """
    from app.services.culture_wall_service import (
        build_content_query,
        check_user_role_permission,
        format_content,
        format_goal,
        get_content_types_config,
        get_culture_wall_config,
        get_notifications,
        get_personal_goals,
        get_read_records,
        query_content_by_type,
    )

    today = date.today()

    # 获取配置
    config = get_culture_wall_config(db)

    # 检查角色权限
    if not check_user_role_permission(config, current_user.role_codes):
        # 如果用户角色不在可见列表中，返回空数据
        return CultureWallSummary(
            strategies=[],
            cultures=[],
            important_items=[],
            notices=[],
            rewards=[],
            personal_goals=[],
            notifications=[],
        )

    # 获取内容类型配置
    content_types_config = get_content_types_config(config)

    # 构建内容查询
    content_query = build_content_query(db, today)

    # 按类型查询内容
    strategies = query_content_by_type(content_query, "STRATEGY", content_types_config)
    cultures = query_content_by_type(content_query, "CULTURE", content_types_config)
    important_items = query_content_by_type(
        content_query, "IMPORTANT", content_types_config
    )
    notices = query_content_by_type(content_query, "NOTICE", content_types_config)
    rewards = query_content_by_type(content_query, "REWARD", content_types_config)

    # 检查阅读状态
    all_contents = strategies + cultures + important_items + notices + rewards
    content_ids = [c.id for c in all_contents]
    read_records = get_read_records(db, content_ids, current_user.id)

    # 获取个人目标
    personal_goals = get_personal_goals(
        db, current_user.id, today, content_types_config
    )

    # 获取系统通知
    notification_list = get_notifications(db, current_user.id, content_types_config)

    return CultureWallSummary(
        strategies=[format_content(c, read_records) for c in strategies],
        cultures=[format_content(c, read_records) for c in cultures],
        important_items=[format_content(c, read_records) for c in important_items],
        notices=[format_content(c, read_records) for c in notices],
        rewards=[format_content(c, read_records) for c in rewards],
        personal_goals=[format_goal(g) for g in personal_goals],
        notifications=notification_list,
    )
