# -*- coding: utf-8 -*-
"""
管理节律模块权限辅助函数

该模块在拆分 endpoints 后提供最小可用的权限过滤逻辑：
- 超级管理员：可访问全部会议
- 其他用户：仅可访问自己组织的会议（organizer_id）

后续如需支持参会人/项目成员权限，可在此扩展。
"""

from typing import Any

from sqlalchemy.orm import Session


def filter_meetings_by_permission(db: Session, query: Any, current_user: Any) -> Any:
    """对 StrategicMeeting 查询应用权限过滤。"""
    if getattr(current_user, "is_superuser", False):
        return query

    from app.models.management_rhythm import StrategicMeeting

    return query.filter(StrategicMeeting.organizer_id == current_user.id)


def check_rhythm_level_permission(current_user: Any, rhythm_level: str) -> bool:
    """检查用户是否有权限访问指定会议层级。"""
    if getattr(current_user, "is_superuser", False):
        return True

    # 目前按会议组织者权限过滤，层级不额外限制。
    return True

