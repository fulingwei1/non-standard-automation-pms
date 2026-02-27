# -*- coding: utf-8 -*-
"""
会议行动项 - 自动生成
从 management_rhythm.py 拆分
"""

# -*- coding: utf-8 -*-
"""
管理节律 API endpoints
包含：节律配置、战略会议、行动项、仪表盘、会议地图
"""
from datetime import date
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.enums import (
    ActionItemStatus,
)
from app.models.management_rhythm import (
    MeetingActionItem,
    StrategicMeeting,
)
from app.models.user import User
from app.schemas.management_rhythm import (
    ActionItemCreate,
    ActionItemResponse,
    ActionItemUpdate,
)

router = APIRouter()



from fastapi import APIRouter

router = APIRouter(
    prefix="/action-items",
    tags=["action_items"]
)

# 共 3 个路由

# ==================== 会议行动项 ====================

@router.get("/strategic-meetings/{meeting_id}/action-items", response_model=List[ActionItemResponse])
def read_meeting_action_items(
    meeting_id: int,
    status: Optional[str] = Query(None, description="状态筛选"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取会议行动项列表
    """
    query = db.query(MeetingActionItem).filter(MeetingActionItem.meeting_id == meeting_id)

    if status:
        query = query.filter(MeetingActionItem.status == status)

    action_items = query.order_by(MeetingActionItem.due_date, MeetingActionItem.created_at).all()

    return [
        ActionItemResponse(
            id=item.id,
            meeting_id=item.meeting_id,
            action_description=item.action_description,
            owner_id=item.owner_id,
            owner_name=item.owner_name,
            due_date=item.due_date,
            completed_date=item.completed_date,
            status=item.status,
            completion_notes=item.completion_notes,
            priority=item.priority,
            created_by=item.created_by,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )
        for item in action_items
    ]


@router.post("/strategic-meetings/{meeting_id}/action-items", response_model=ActionItemResponse, status_code=status.HTTP_201_CREATED)
def create_action_item(
    meeting_id: int,
    item_data: ActionItemCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建会议行动项
    """
    # 验证会议存在
    meeting = db.query(StrategicMeeting).filter(StrategicMeeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(status_code=404, detail="会议不存在")

    action_item = MeetingActionItem(
        meeting_id=meeting_id,
        action_description=item_data.action_description,
        owner_id=item_data.owner_id,
        owner_name=item_data.owner_name,
        due_date=item_data.due_date,
        priority=item_data.priority or "NORMAL",
        created_by=current_user.id,
    )

    db.add(action_item)
    db.commit()
    db.refresh(action_item)

    return ActionItemResponse(
        id=action_item.id,
        meeting_id=action_item.meeting_id,
        action_description=action_item.action_description,
        owner_id=action_item.owner_id,
        owner_name=action_item.owner_name,
        due_date=action_item.due_date,
        completed_date=action_item.completed_date,
        status=action_item.status,
        completion_notes=action_item.completion_notes,
        priority=action_item.priority,
        created_by=action_item.created_by,
        created_at=action_item.created_at,
        updated_at=action_item.updated_at,
    )


@router.put("/strategic-meetings/{meeting_id}/action-items/{item_id}", response_model=ActionItemResponse)
def update_action_item(
    meeting_id: int,
    item_id: int,
    item_data: ActionItemUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新会议行动项
    """
    action_item = db.query(MeetingActionItem).filter(
        and_(
            MeetingActionItem.id == item_id,
            MeetingActionItem.meeting_id == meeting_id
        )
    ).first()

    if not action_item:
        raise HTTPException(status_code=404, detail="行动项不存在")

    update_data = item_data.dict(exclude_unset=True)

    # 如果状态更新为已完成，自动设置完成日期
    if update_data.get("status") == ActionItemStatus.COMPLETED.value and not action_item.completed_date:
        update_data["completed_date"] = date.today()

    # 如果状态更新为已完成，但完成日期被清除，则恢复为待处理
    if update_data.get("status") != ActionItemStatus.COMPLETED.value and action_item.completed_date:
        if "completed_date" not in update_data:
            update_data["completed_date"] = None

    for field, value in update_data.items():
        setattr(action_item, field, value)

    # 检查是否逾期
    if action_item.status != ActionItemStatus.COMPLETED.value and action_item.due_date < date.today():
        action_item.status = ActionItemStatus.OVERDUE.value

    db.commit()
    db.refresh(action_item)

    return ActionItemResponse(
        id=action_item.id,
        meeting_id=action_item.meeting_id,
        action_description=action_item.action_description,
        owner_id=action_item.owner_id,
        owner_name=action_item.owner_name,
        due_date=action_item.due_date,
        completed_date=action_item.completed_date,
        status=action_item.status,
        completion_notes=action_item.completion_notes,
        priority=action_item.priority,
        created_by=action_item.created_by,
        created_at=action_item.created_at,
        updated_at=action_item.updated_at,
    )



