# -*- coding: utf-8 -*-
"""
销售团队管理 API 端点
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.schemas.sales_team import (
    SalesTeamCreate,
    SalesTeamUpdate,
    SalesTeamResponse,
    SalesTeamMemberCreate,
    SalesTeamMemberUpdate,
    SalesTeamMemberResponse,
)
from app.schemas.common import ResponseModel
from app.services.sales_team_service import SalesTeamService
from app.core.security import require_permission

router = APIRouter()


@router.post("", response_model=ResponseModel)
@require_permission("sales_team:create")
def create_team(
    *,
    db: Session = Depends(deps.get_db),
    team_in: SalesTeamCreate,
    current_user = Depends(deps.get_current_user),
):
    """创建销售团队"""
    team = SalesTeamService.create_team(db, team_in, current_user.id)
    return ResponseModel(code=200, message="创建成功", data=SalesTeamResponse.from_orm(team))


@router.get("", response_model=ResponseModel)
@require_permission("sales_team:view")
def get_teams(
    db: Session = Depends(deps.get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    team_type: Optional[str] = None,
    department_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_user = Depends(deps.get_current_user),
):
    """获取销售团队列表"""
    teams = SalesTeamService.get_teams(
        db,
        skip=skip,
        limit=limit,
        team_type=team_type,
        department_id=department_id,
        is_active=is_active,
    )
    return ResponseModel(
        code=200,
        message="查询成功",
        data=[SalesTeamResponse.from_orm(team) for team in teams]
    )


@router.get("/tree", response_model=ResponseModel)
@require_permission("sales_team:view")
def get_team_tree(
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """获取销售团队组织树"""
    tree = SalesTeamService.get_team_tree(db)
    return ResponseModel(code=200, message="查询成功", data=tree)


@router.get("/{team_id}", response_model=ResponseModel)
@require_permission("sales_team:view")
def get_team(
    team_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """获取销售团队详情"""
    team = SalesTeamService.get_team(db, team_id)
    if not team:
        return ResponseModel(code=404, message="团队不存在")
    return ResponseModel(code=200, message="查询成功", data=SalesTeamResponse.from_orm(team))


@router.put("/{team_id}", response_model=ResponseModel)
@require_permission("sales_team:update")
def update_team(
    team_id: int,
    team_in: SalesTeamUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """更新销售团队"""
    team = SalesTeamService.update_team(db, team_id, team_in)
    return ResponseModel(code=200, message="更新成功", data=SalesTeamResponse.from_orm(team))


@router.delete("/{team_id}", response_model=ResponseModel)
@require_permission("sales_team:delete")
def delete_team(
    team_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """删除销售团队"""
    SalesTeamService.delete_team(db, team_id)
    return ResponseModel(code=200, message="删除成功")


# ============= 团队成员管理 =============

@router.post("/{team_id}/members", response_model=ResponseModel)
@require_permission("sales_team:update")
def add_member(
    team_id: int,
    member_in: SalesTeamMemberCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """添加团队成员"""
    member = SalesTeamService.add_member(db, member_in)
    return ResponseModel(code=200, message="添加成功", data=SalesTeamMemberResponse.from_orm(member))


@router.get("/{team_id}/members", response_model=ResponseModel)
@require_permission("sales_team:view")
def get_team_members(
    team_id: int,
    db: Session = Depends(deps.get_db),
    is_active: Optional[bool] = Query(True),
    current_user = Depends(deps.get_current_user),
):
    """获取团队成员列表"""
    members = SalesTeamService.get_team_members(db, team_id, is_active)
    return ResponseModel(
        code=200,
        message="查询成功",
        data=[SalesTeamMemberResponse.from_orm(member) for member in members]
    )


@router.delete("/{team_id}/members/{user_id}", response_model=ResponseModel)
@require_permission("sales_team:update")
def remove_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """移除团队成员"""
    SalesTeamService.remove_member(db, team_id, user_id)
    return ResponseModel(code=200, message="移除成功")


@router.put("/{team_id}/members/{user_id}/role", response_model=ResponseModel)
@require_permission("sales_team:update")
def update_member_role(
    team_id: int,
    user_id: int,
    member_in: SalesTeamMemberUpdate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    """更新成员角色"""
    member = SalesTeamService.update_member_role(db, team_id, user_id, member_in)
    return ResponseModel(code=200, message="更新成功", data=SalesTeamMemberResponse.from_orm(member))
