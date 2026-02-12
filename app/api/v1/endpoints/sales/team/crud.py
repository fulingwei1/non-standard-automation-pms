# -*- coding: utf-8 -*-
"""
销售团队CRUD API endpoints
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.sales import SalesTeam, SalesTeamMember
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.sales import SalesTeamCreate, SalesTeamUpdate
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination

from .utils import build_team_response

router = APIRouter()


@router.get("/sales-teams", response_model=ResponseModel)
def list_sales_teams(
    *,
    db: Session = Depends(deps.get_db),
    team_type: Optional[str] = Query(None, description="团队类型筛选"),
    department_id: Optional[int] = Query(None, description="部门ID筛选"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    keyword: Optional[str] = Query(None, description="团队名称/编码关键字"),
    pagination: PaginationParams = Depends(get_pagination_query),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取销售团队列表"""
    query = db.query(SalesTeam)

    if team_type:
        query = query.filter(SalesTeam.team_type == team_type)
    if department_id:
        query = query.filter(SalesTeam.department_id == department_id)
    if is_active is not None:
        query = query.filter(SalesTeam.is_active == is_active)
    query = apply_keyword_filter(query, SalesTeam, keyword, ["team_name", "team_code"])

    total = query.count()
    teams = query.order_by(SalesTeam.sort_order, apply_pagination(SalesTeam.id), pagination.offset, pagination.limit).all()

    items = []
    for team in teams:
        member_count = db.query(SalesTeamMember).filter(
            SalesTeamMember.team_id == team.id,
            SalesTeamMember.is_active == True,
        ).count()
        sub_team_count = db.query(SalesTeam).filter(
            SalesTeam.parent_team_id == team.id,
            SalesTeam.is_active == True,
        ).count()

        items.append({
            "id": team.id,
            "team_code": team.team_code,
            "team_name": team.team_name,
            "team_type": team.team_type,
            "department_name": team.department.name if team.department else None,
            "leader_name": (team.leader.real_name or team.leader.username) if team.leader else None,
            "is_active": team.is_active,
            "member_count": member_count,
            "sub_team_count": sub_team_count,
        })

    return ResponseModel(
        code=200,
        message="success",
        data={
            "items": items,
            "total": total,
            "page": pagination.page,
            "page_size": pagination.page_size,
        }
    )


@router.post("/sales-teams", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_sales_team(
    *,
    db: Session = Depends(deps.get_db),
    request: SalesTeamCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建销售团队"""
    # 检查团队编码唯一性
    existing = db.query(SalesTeam).filter(SalesTeam.team_code == request.team_code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"团队编码 {request.team_code} 已存在",
        )

    team = SalesTeam(
        team_code=request.team_code,
        team_name=request.team_name,
        description=request.description,
        team_type=request.team_type,
        department_id=request.department_id,
        leader_id=request.leader_id,
        parent_team_id=request.parent_team_id,
        sort_order=request.sort_order,
        created_by=current_user.id,
    )
    db.add(team)
    db.commit()
    db.refresh(team)

    # 如果指定了负责人，自动添加为团队成员
    if request.leader_id:
        member = SalesTeamMember(
            team_id=team.id,
            user_id=request.leader_id,
            role="LEADER",
            is_primary=True,
        )
        db.add(member)
        db.commit()

    return ResponseModel(
        code=201,
        message="团队创建成功",
        data=build_team_response(team, db),
    )


@router.get("/sales-teams/{team_id}", response_model=ResponseModel)
def get_sales_team(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取销售团队详情"""
    team = db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在",
        )

    return ResponseModel(
        code=200,
        message="success",
        data=build_team_response(team, db),
    )


@router.put("/sales-teams/{team_id}", response_model=ResponseModel)
def update_sales_team(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    request: SalesTeamUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """更新销售团队"""
    team = db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在",
        )

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)

    db.commit()
    db.refresh(team)

    return ResponseModel(
        code=200,
        message="团队更新成功",
        data=build_team_response(team, db),
    )


@router.delete("/sales-teams/{team_id}", response_model=ResponseModel)
def delete_sales_team(
    *,
    db: Session = Depends(deps.get_db),
    team_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """删除销售团队（软删除）"""
    team = db.query(SalesTeam).filter(SalesTeam.id == team_id).first()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="团队不存在",
        )

    # 检查是否有子团队
    sub_teams = db.query(SalesTeam).filter(
        SalesTeam.parent_team_id == team_id,
        SalesTeam.is_active == True,
    ).count()
    if sub_teams > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该团队下有子团队，无法删除",
        )

    team.is_active = False
    db.commit()

    return ResponseModel(
        code=200,
        message="团队已删除",
        data={"team_id": team_id},
    )
