# -*- coding: utf-8 -*-
"""
个人目标管理
"""

from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.culture_wall import PersonalGoal
from app.models.user import User
from app.schemas.culture_wall import (
    PersonalGoalCreate,
    PersonalGoalResponse,
    PersonalGoalUpdate,
)

router = APIRouter()


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
