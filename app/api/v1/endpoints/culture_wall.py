# -*- coding: utf-8 -*-
"""
文化墙 API endpoints
包含：文化墙内容、个人目标、文化墙汇总
"""
from datetime import date, datetime, timedelta
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.culture_wall import (
    CultureWallContent,
    CultureWallReadRecord,
    PersonalGoal,
)
from app.models.culture_wall_config import CultureWallConfig
from app.models.notification import Notification
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.culture_wall import (
    CultureWallContentCreate,
    CultureWallContentResponse,
    CultureWallContentUpdate,
    CultureWallSummary,
    PersonalGoalCreate,
    PersonalGoalResponse,
    PersonalGoalUpdate,
)

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

    # 检查角色权限 - 获取用户的第一个角色代码
    user_roles = list(current_user.roles)
    user_role = ''
    if user_roles:
        role_obj = user_roles[0].role
        user_role = role_obj.role_code if role_obj else ''
    if not check_user_role_permission(config, user_role):
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
    strategies = query_content_by_type(content_query, 'STRATEGY', content_types_config)
    cultures = query_content_by_type(content_query, 'CULTURE', content_types_config)
    important_items = query_content_by_type(content_query, 'IMPORTANT', content_types_config)
    notices = query_content_by_type(content_query, 'NOTICE', content_types_config)
    rewards = query_content_by_type(content_query, 'REWARD', content_types_config)

    # 检查阅读状态
    all_contents = strategies + cultures + important_items + notices + rewards
    content_ids = [c.id for c in all_contents]
    read_records = get_read_records(db, content_ids, current_user.id)

    # 获取个人目标
    personal_goals = get_personal_goals(db, current_user.id, today, content_types_config)

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
