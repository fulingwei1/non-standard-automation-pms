# -*- coding: utf-8 -*-
"""
文化墙服务
"""

from typing import Dict, Any, List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_

from app.models.culture_wall import CultureWallContent, PersonalGoal, CultureWallReadRecord
from app.models.culture_wall_config import CultureWallConfig
from app.models.notification import Notification
from app.models.user import User
from app.schemas.culture_wall import CultureWallContentResponse, PersonalGoalResponse


def get_culture_wall_config(db: Session) -> Optional[CultureWallConfig]:
    """
    获取文化墙配置
    
    Returns:
        Optional[CultureWallConfig]: 配置对象
    """
    # 优先获取默认配置
    config = db.query(CultureWallConfig).filter(
        CultureWallConfig.is_default == True,
        CultureWallConfig.is_enabled == True
    ).first()
    
    if not config:
        # 如果没有默认配置，获取最新的启用配置
        config = db.query(CultureWallConfig).filter(
            CultureWallConfig.is_enabled == True
        ).order_by(desc(CultureWallConfig.created_at)).first()
    
    return config


def check_user_role_permission(
    config: Optional[CultureWallConfig],
    user_role: str
) -> bool:
    """
    检查用户角色权限
    
    Returns:
        bool: 如果用户有权限返回True
    """
    if not config or not config.visible_roles or len(config.visible_roles) == 0:
        return True
    
    return user_role in config.visible_roles


def get_content_types_config(config: Optional[CultureWallConfig]) -> Dict[str, Any]:
    """
    获取内容类型配置
    
    Returns:
        Dict[str, Any]: 内容类型配置字典
    """
    if config and config.content_types:
        return config.content_types
    return {}


def build_content_query(db: Session, today: date):
    """
    构建内容查询（已发布且未过期）
    
    Returns:
        Query: SQLAlchemy查询对象
    """
    return db.query(CultureWallContent).filter(
        and_(
            CultureWallContent.is_published == True,
            or_(
                CultureWallContent.expire_date.is_(None),
                CultureWallContent.expire_date >= today
            )
        )
    )


def query_content_by_type(
    content_query,
    content_type: str,
    content_types_config: Dict[str, Any],
    default_max_count: int = 10
) -> List[CultureWallContent]:
    """
    按类型查询内容
    
    Returns:
        List[CultureWallContent]: 内容列表
    """
    type_config = content_types_config.get(content_type)
    
    # 如果该类型被禁用，返回空列表
    if type_config and not type_config.get('enabled', True):
        return []
    
    max_count = type_config.get('max_count', default_max_count) if type_config else default_max_count
    
    return content_query.filter(
        CultureWallContent.content_type == content_type
    ).order_by(
        desc(CultureWallContent.priority),
        desc(CultureWallContent.publish_date)
    ).limit(max_count).all()


def get_read_records(
    db: Session,
    content_ids: List[int],
    user_id: int
) -> Dict[int, bool]:
    """
    获取阅读记录
    
    Returns:
        Dict[int, bool]: 内容ID到是否已读的映射
    """
    if not content_ids:
        return {}
    
    records = db.query(CultureWallReadRecord).filter(
        and_(
            CultureWallReadRecord.content_id.in_(content_ids),
            CultureWallReadRecord.user_id == user_id
        )
    ).all()
    
    return {r.content_id: True for r in records}


def format_content(
    content: CultureWallContent,
    read_records: Dict[int, bool]
) -> CultureWallContentResponse:
    """
    格式化内容对象
    
    Returns:
        CultureWallContentResponse: 格式化后的内容响应对象
    """
    return CultureWallContentResponse(
        id=content.id,
        content_type=content.content_type,
        title=content.title,
        content=content.content,
        summary=content.summary,
        images=content.images if content.images else [],
        videos=content.videos if content.videos else [],
        attachments=content.attachments if content.attachments else [],
        is_published=content.is_published,
        publish_date=content.publish_date,
        expire_date=content.expire_date,
        priority=content.priority,
        display_order=content.display_order,
        view_count=content.view_count,
        related_project_id=content.related_project_id,
        related_department_id=content.related_department_id,
        published_by=content.published_by,
        published_by_name=content.published_by_name,
        created_by=content.created_by,
        created_at=content.created_at,
        updated_at=content.updated_at,
        is_read=read_records.get(content.id, False),
    )


def get_personal_goals(
    db: Session,
    user_id: int,
    today: date,
    content_types_config: Dict[str, Any]
) -> List[PersonalGoal]:
    """
    获取个人目标
    
    Returns:
        List[PersonalGoal]: 个人目标列表
    """
    type_config = content_types_config.get('PERSONAL_GOAL')
    
    # 如果个人目标被禁用，返回空列表
    if type_config and not type_config.get('enabled', True):
        return []
    
    current_month = today.strftime('%Y-%m')
    quarter = (today.month - 1) // 3 + 1
    current_quarter = f"{today.year}-Q{quarter}"
    
    monthly_goals = db.query(PersonalGoal).filter(
        and_(
            PersonalGoal.user_id == user_id,
            PersonalGoal.goal_type == 'MONTHLY',
            PersonalGoal.period == current_month,
            PersonalGoal.status != 'CANCELLED'
        )
    ).order_by(desc(PersonalGoal.created_at)).all()
    
    quarterly_goals = db.query(PersonalGoal).filter(
        and_(
            PersonalGoal.user_id == user_id,
            PersonalGoal.goal_type == 'QUARTERLY',
            PersonalGoal.period == current_quarter,
            PersonalGoal.status != 'CANCELLED'
        )
    ).order_by(desc(PersonalGoal.created_at)).all()
    
    max_count = type_config.get('max_count', 5) if type_config else 5
    all_goals = (monthly_goals + quarterly_goals)[:max_count]
    
    return all_goals


def format_goal(goal: PersonalGoal) -> PersonalGoalResponse:
    """
    格式化目标对象
    
    Returns:
        PersonalGoalResponse: 格式化后的目标响应对象
    """
    return PersonalGoalResponse(
        id=goal.id,
        user_id=goal.user_id,
        goal_type=goal.goal_type,
        period=goal.period,
        title=goal.title,
        description=goal.description,
        target_value=goal.target_value,
        current_value=goal.current_value,
        unit=goal.unit,
        progress=goal.progress,
        status=goal.status,
        start_date=goal.start_date,
        end_date=goal.end_date,
        completed_date=goal.completed_date,
        notes=goal.notes,
        created_by=goal.created_by,
        created_at=goal.created_at,
        updated_at=goal.updated_at,
    )


def get_notifications(
    db: Session,
    user_id: int,
    content_types_config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    获取系统通知
    
    Returns:
        List[Dict[str, Any]]: 通知列表
    """
    type_config = content_types_config.get('NOTIFICATION')
    
    # 如果通知被禁用，返回空列表
    if type_config and not type_config.get('enabled', True):
        return []
    
    max_count = type_config.get('max_count', 10) if type_config else 10
    
    notifications = db.query(Notification).filter(
        and_(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
    ).order_by(desc(Notification.created_at)).limit(max_count).all()
    
    return [
        {
            'id': notif.id,
            'title': notif.title,
            'content': notif.content,
            'type': notif.notification_type,
            'priority': notif.priority,
            'created_at': notif.created_at.isoformat() if notif.created_at else None,
        }
        for notif in notifications
    ]
