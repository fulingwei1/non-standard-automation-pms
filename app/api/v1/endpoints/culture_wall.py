# -*- coding: utf-8 -*-
"""
文化墙 API endpoints
包含：文化墙内容、个人目标、文化墙汇总
"""
from typing import Any, List, Optional
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.models.culture_wall import (
    CultureWallContent,
    PersonalGoal,
    CultureWallReadRecord
)
from app.models.culture_wall_config import CultureWallConfig
from app.models.notification import Notification
from app.schemas.culture_wall import (
    CultureWallContentCreate, CultureWallContentUpdate, CultureWallContentResponse,
    PersonalGoalCreate, PersonalGoalUpdate, PersonalGoalResponse,
    CultureWallSummary
)
from app.schemas.common import PaginatedResponse

router = APIRouter()


# ==================== 文化墙汇总 ====================

@router.get("/culture-wall/summary", response_model=CultureWallSummary)
def get_culture_wall_summary(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取文化墙汇总数据（用于滚动播放）
    根据配置过滤内容和角色
    """
    today = date.today()
    
    # 获取配置
    config = db.query(CultureWallConfig).filter(
        CultureWallConfig.is_default == True,
        CultureWallConfig.is_enabled == True
    ).first()
    
    if not config:
        config = db.query(CultureWallConfig).filter(
            CultureWallConfig.is_enabled == True
        ).order_by(desc(CultureWallConfig.created_at)).first()
    
    # 检查角色权限
    if config and config.visible_roles and len(config.visible_roles) > 0:
        user_role = current_user.role or ''
        if user_role not in config.visible_roles:
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
    content_types_config = {}
    if config and config.content_types:
        content_types_config = config.content_types
    
    # 查询已发布且未过期的内容
    content_query = db.query(CultureWallContent).filter(
        and_(
            CultureWallContent.is_published == True,
            or_(
                CultureWallContent.expire_date.is_(None),
                CultureWallContent.expire_date >= today
            )
        )
    )
    
    # 按类型分组查询，根据配置过滤
    strategies = []
    if not content_types_config.get('STRATEGY') or content_types_config['STRATEGY'].get('enabled', True):
        max_count = content_types_config.get('STRATEGY', {}).get('max_count', 10) if content_types_config.get('STRATEGY') else 10
        strategies = content_query.filter(
            CultureWallContent.content_type == 'STRATEGY'
        ).order_by(desc(CultureWallContent.priority), desc(CultureWallContent.publish_date)).limit(max_count).all()
    
    cultures = []
    if not content_types_config.get('CULTURE') or content_types_config['CULTURE'].get('enabled', True):
        max_count = content_types_config.get('CULTURE', {}).get('max_count', 10) if content_types_config.get('CULTURE') else 10
        cultures = content_query.filter(
            CultureWallContent.content_type == 'CULTURE'
        ).order_by(desc(CultureWallContent.priority), desc(CultureWallContent.publish_date)).limit(max_count).all()
    
    important_items = []
    if not content_types_config.get('IMPORTANT') or content_types_config['IMPORTANT'].get('enabled', True):
        max_count = content_types_config.get('IMPORTANT', {}).get('max_count', 10) if content_types_config.get('IMPORTANT') else 10
        important_items = content_query.filter(
            CultureWallContent.content_type == 'IMPORTANT'
        ).order_by(desc(CultureWallContent.priority), desc(CultureWallContent.publish_date)).limit(max_count).all()
    
    notices = []
    if not content_types_config.get('NOTICE') or content_types_config['NOTICE'].get('enabled', True):
        max_count = content_types_config.get('NOTICE', {}).get('max_count', 10) if content_types_config.get('NOTICE') else 10
        notices = content_query.filter(
            CultureWallContent.content_type == 'NOTICE'
        ).order_by(desc(CultureWallContent.priority), desc(CultureWallContent.publish_date)).limit(max_count).all()
    
    rewards = []
    if not content_types_config.get('REWARD') or content_types_config['REWARD'].get('enabled', True):
        max_count = content_types_config.get('REWARD', {}).get('max_count', 10) if content_types_config.get('REWARD') else 10
        rewards = content_query.filter(
            CultureWallContent.content_type == 'REWARD'
        ).order_by(desc(CultureWallContent.priority), desc(CultureWallContent.publish_date)).limit(max_count).all()
    
    # 检查阅读状态
    content_ids = [c.id for c in strategies + cultures + important_items + notices + rewards]
    read_records = {}
    if content_ids:
        records = db.query(CultureWallReadRecord).filter(
            and_(
                CultureWallReadRecord.content_id.in_(content_ids),
                CultureWallReadRecord.user_id == current_user.id
            )
        ).all()
        read_records = {r.content_id: True for r in records}
    
    def format_content(content):
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
    
    # 获取个人目标（根据配置决定是否显示）
    personal_goals = []
    if not content_types_config.get('PERSONAL_GOAL') or content_types_config['PERSONAL_GOAL'].get('enabled', True):
        current_month = today.strftime('%Y-%m')
        quarter = (today.month - 1) // 3 + 1
        current_quarter = f"{today.year}-Q{quarter}"
        
        monthly_goals = db.query(PersonalGoal).filter(
            and_(
                PersonalGoal.user_id == current_user.id,
                PersonalGoal.goal_type == 'MONTHLY',
                PersonalGoal.period == current_month,
                PersonalGoal.status != 'CANCELLED'
            )
        ).order_by(desc(PersonalGoal.created_at)).all()
        
        quarterly_goals = db.query(PersonalGoal).filter(
            and_(
                PersonalGoal.user_id == current_user.id,
                PersonalGoal.goal_type == 'QUARTERLY',
                PersonalGoal.period == current_quarter,
                PersonalGoal.status != 'CANCELLED'
            )
        ).order_by(desc(PersonalGoal.created_at)).all()
        
        max_count = content_types_config.get('PERSONAL_GOAL', {}).get('max_count', 5) if content_types_config.get('PERSONAL_GOAL') else 5
        all_goals = (monthly_goals + quarterly_goals)[:max_count]
        personal_goals = all_goals
    
    def format_goal(goal):
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
    
    # 获取系统通知（根据配置决定是否显示）
    notification_list = []
    if not content_types_config.get('NOTIFICATION') or content_types_config['NOTIFICATION'].get('enabled', True):
        max_count = content_types_config.get('NOTIFICATION', {}).get('max_count', 10) if content_types_config.get('NOTIFICATION') else 10
        notifications = db.query(Notification).filter(
            and_(
                Notification.user_id == current_user.id,
                Notification.is_read == False
            )
        ).order_by(desc(Notification.created_at)).limit(max_count).all()
        
        for notif in notifications:
            notification_list.append({
                'id': notif.id,
                'title': notif.title,
                'content': notif.content,
                'type': notif.notification_type,
                'priority': notif.priority,
                'created_at': notif.created_at.isoformat() if notif.created_at else None,
            })
    
    return CultureWallSummary(
        strategies=[format_content(c) for c in strategies],
        cultures=[format_content(c) for c in cultures],
        important_items=[format_content(c) for c in important_items],
        notices=[format_content(c) for c in notices],
        rewards=[format_content(c) for c in rewards],
        personal_goals=[format_goal(g) for g in personal_goals],
        notifications=notification_list,
    )


# ==================== 文化墙内容 ====================

@router.get("/culture-wall/contents", response_model=PaginatedResponse)
def read_culture_wall_contents(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    content_type: Optional[str] = Query(None, description="内容类型筛选"),
    is_published: Optional[bool] = Query(None, description="是否发布筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取文化墙内容列表
    """
    query = db.query(CultureWallContent)
    
    if content_type:
        query = query.filter(CultureWallContent.content_type == content_type)
    
    if is_published is not None:
        query = query.filter(CultureWallContent.is_published == is_published)
    
    if keyword:
        query = query.filter(
            or_(
                CultureWallContent.title.like(f"%{keyword}%"),
                CultureWallContent.content.like(f"%{keyword}%"),
                CultureWallContent.summary.like(f"%{keyword}%")
            )
        )
    
    total = query.count()
    offset = (page - 1) * page_size
    contents = query.order_by(desc(CultureWallContent.priority), desc(CultureWallContent.created_at)).offset(offset).limit(page_size).all()
    
    items = []
    for content in contents:
        items.append(CultureWallContentResponse(
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
            is_read=False,
        ))
    
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.post("/culture-wall/contents", response_model=CultureWallContentResponse)
def create_culture_wall_content(
    content_data: CultureWallContentCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建文化墙内容
    """
    content = CultureWallContent(
        content_type=content_data.content_type,
        title=content_data.title,
        content=content_data.content,
        summary=content_data.summary,
        images=content_data.images,
        videos=content_data.videos,
        attachments=content_data.attachments,
        is_published=content_data.is_published or False,
        publish_date=content_data.publish_date,
        expire_date=content_data.expire_date,
        priority=content_data.priority or 0,
        display_order=content_data.display_order or 0,
        related_project_id=content_data.related_project_id,
        related_department_id=content_data.related_department_id,
        published_by=current_user.id if content_data.is_published else None,
        published_by_name=current_user.real_name if content_data.is_published else None,
        created_by=current_user.id,
    )
    
    db.add(content)
    db.commit()
    db.refresh(content)
    
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
        is_read=False,
    )


@router.get("/culture-wall/contents/{content_id}", response_model=CultureWallContentResponse)
def read_culture_wall_content(
    content_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取文化墙内容详情（自动记录阅读）
    """
    content = db.query(CultureWallContent).filter(CultureWallContent.id == content_id).first()
    if not content:
        raise HTTPException(status_code=404, detail="内容不存在")
    
    # 增加浏览次数
    content.view_count = (content.view_count or 0) + 1
    
    # 记录阅读
    read_record = db.query(CultureWallReadRecord).filter(
        and_(
            CultureWallReadRecord.content_id == content_id,
            CultureWallReadRecord.user_id == current_user.id
        )
    ).first()
    
    if not read_record:
        read_record = CultureWallReadRecord(
            content_id=content_id,
            user_id=current_user.id,
            read_at=datetime.now(),
        )
        db.add(read_record)
    
    db.commit()
    
    # 检查是否已读
    is_read = read_record is not None
    
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
        is_read=is_read,
    )


# ==================== 个人目标 ====================

@router.get("/personal-goals", response_model=List[PersonalGoalResponse])
def read_personal_goals(
    goal_type: Optional[str] = Query(None, description="目标类型筛选"),
    period: Optional[str] = Query(None, description="周期筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取个人目标列表
    """
    query = db.query(PersonalGoal).filter(PersonalGoal.user_id == current_user.id)
    
    if goal_type:
        query = query.filter(PersonalGoal.goal_type == goal_type)
    
    if period:
        query = query.filter(PersonalGoal.period == period)
    
    goals = query.order_by(desc(PersonalGoal.created_at)).all()
    
    return [
        PersonalGoalResponse(
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
        for goal in goals
    ]


@router.post("/personal-goals", response_model=PersonalGoalResponse)
def create_personal_goal(
    goal_data: PersonalGoalCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建个人目标
    """
    goal = PersonalGoal(
        user_id=current_user.id,
        goal_type=goal_data.goal_type,
        period=goal_data.period,
        title=goal_data.title,
        description=goal_data.description,
        target_value=goal_data.target_value,
        unit=goal_data.unit,
        start_date=goal_data.start_date,
        end_date=goal_data.end_date,
        notes=goal_data.notes,
        created_by=current_user.id,
    )
    
    db.add(goal)
    db.commit()
    db.refresh(goal)
    
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


@router.put("/personal-goals/{goal_id}", response_model=PersonalGoalResponse)
def update_personal_goal(
    goal_id: int,
    goal_data: PersonalGoalUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新个人目标
    """
    goal = db.query(PersonalGoal).filter(
        and_(
            PersonalGoal.id == goal_id,
            PersonalGoal.user_id == current_user.id
        )
    ).first()
    
    if not goal:
        raise HTTPException(status_code=404, detail="目标不存在")
    
    update_data = goal_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(goal, field, value)
    
    # 如果状态更新为已完成，自动设置完成日期
    if goal_data.status == 'COMPLETED' and not goal.completed_date:
        goal.completed_date = date.today()
        # 自动计算进度为100%
        if goal.progress < 100:
            goal.progress = 100
    
    db.commit()
    db.refresh(goal)
    
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
