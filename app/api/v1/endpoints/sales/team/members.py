# -*- coding: utf-8 -*-
"""
团队成员管理 API endpoints
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import SalesTeam, SalesTeamMember
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import (
    TeamMemberAddRequest,
    TeamMemberBatchAddRequest,
    TeamMemberUpdateRequest,
)

router = APIRouter()


@router.get("/sales-teams/{team_id}/members", response_model=ResponseModel)
def list_team_members(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    include_inactive: bool = Query(False, description="是否包含已移除成员"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取团队成员列表"""
    team = db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在",
        )

    query = db.query(SalesTeamMember).filter(SalesTeamMember.team_id == team_id)
    if not include_inactive:
        query = query.filter(SalesTeamMember.is_active)

    members = query.all()
    items = [
        {
            "id": m.id,
            "user_id": m.user_id,
            "user_name": m.user.real_name if m.user else None,
            "username": m.user.username if m.user else None,
            "email": m.user.email if m.user else None,
            "phone": m.user.phone if m.user else None,
            "role": m.role,
            "is_primary": m.is_primary,
            "is_active": m.is_active,
            "joined_at": m.joined_at,
            "remark": m.remark,
        }
        for m in members
    ]

    return ResponseModel(
        code=200,
        message="success",
        data={
            "team_id": team_id,
            "team_name": team.team_name,
            "members": items,
            "total": len(items),
        }
    )


@router.post("/sales-teams/{team_id}/members", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def add_team_member(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    request: TeamMemberAddRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """添加团队成员"""
    team = db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在",
        )

    # 检查用户是否存在
    user = db.query(User).filter(User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在",
        )

    # 检查是否已是成员
    existing = db.query(SalesTeamMember).filter(
        SalesTeamMember.team_id == team_id,
        SalesTeamMember.user_id == request.user_id,
    ).first()
    if existing:
        if existing.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该用户已是团队成员",
            )
        # 重新激活
        existing.is_active = True
        existing.role = request.role
        existing.is_primary = request.is_primary
        existing.remark = request.remark
        db.commit()
        db.refresh(existing)
        member = existing
    else:
        member = SalesTeamMember(
            team_id=team_id,
            user_id=request.user_id,
            role=request.role,
            is_primary=request.is_primary,
            remark=request.remark,
        )
        db.add(member)
        db.commit()
        db.refresh(member)

    # 如果设为主团队，清除其他团队的主团队标记
    if request.is_primary:
        db.query(SalesTeamMember).filter(
            SalesTeamMember.user_id == request.user_id,
            SalesTeamMember.id != member.id,
        ).update({"is_primary": False})
        db.commit()

    return ResponseModel(
        code=201,
        message="成员添加成功",
        data={
            "id": member.id,
            "team_id": team_id,
            "user_id": member.user_id,
            "user_name": user.real_name or user.username,
            "role": member.role,
            "is_primary": member.is_primary,
        }
    )


@router.post("/sales-teams/{team_id}/members/batch", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def batch_add_team_members(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    request: TeamMemberBatchAddRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """批量添加团队成员"""
    team = db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在",
        )

    added = []
    skipped = []
    for user_id in request.user_ids:
        existing = db.query(SalesTeamMember).filter(
            SalesTeamMember.team_id == team_id,
            SalesTeamMember.user_id == user_id,
            SalesTeamMember.is_active,
        ).first()
        if existing:
            skipped.append(user_id)
            continue

        member = SalesTeamMember(
            team_id=team_id,
            user_id=user_id,
            role=request.role,
        )
        db.add(member)
        added.append(user_id)

    db.commit()

    return ResponseModel(
        code=201,
        message=f"成功添加 {len(added)} 人，跳过 {len(skipped)} 人（已存在）",
        data={
            "added": added,
            "skipped": skipped,
        }
    )


@router.put("/sales-teams/{team_id}/members/{member_id}", response_model=ResponseModel)
def update_team_member(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    member_id: int,
    request: TeamMemberUpdateRequest,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新团队成员"""
    member = db.query(SalesTeamMember).filter(
        SalesTeamMember.id == member_id,
        SalesTeamMember.team_id == team_id,
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成员不存在",
        )

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)

    # 如果设为主团队，清除其他团队的主团队标记
    if request.is_primary:
        db.query(SalesTeamMember).filter(
            SalesTeamMember.user_id == member.user_id,
            SalesTeamMember.id != member.id,
        ).update({"is_primary": False})

    db.commit()
    db.refresh(member)

    return ResponseModel(
        code=200,
        message="成员更新成功",
        data={
            "id": member.id,
            "user_id": member.user_id,
            "role": member.role,
            "is_primary": member.is_primary,
            "is_active": member.is_active,
        }
    )


@router.delete("/sales-teams/{team_id}/members/{member_id}", response_model=ResponseModel)
def remove_team_member(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    member_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """移除团队成员（软删除）"""
    member = db.query(SalesTeamMember).filter(
        SalesTeamMember.id == member_id,
        SalesTeamMember.team_id == team_id,
    ).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="成员不存在",
        )

    member.is_active = False
    db.commit()

    return ResponseModel(
        code=200,
        message="成员已移除",
        data={"member_id": member_id},
    )
