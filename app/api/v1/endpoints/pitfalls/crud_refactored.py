# -*- coding: utf-8 -*-
"""
踩坑记录 CRUD API（重构版）
使用统一响应格式
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core import security
from app.core.schemas import list_response, paginated_response, success_response
from app.models.user import User
from app.schemas.pitfall import (
    PitfallCreate,
    PitfallUpdate,
)
from app.services.pitfall import PitfallService
from app.common.pagination import PaginationParams, get_pagination_query

router = APIRouter()


@router.post("")
def create_pitfall(
    data: PitfallCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    创建踩坑记录

    必填字段：title, description
    其他字段可选，支持后续补充完善
    """
    service = PitfallService(db)

    pitfall = service.create_pitfall(
        title=data.title,
        description=data.description,
        solution=data.solution,
        stage=data.stage,
        equipment_type=data.equipment_type,
        problem_type=data.problem_type,
        tags=data.tags,
        root_cause=data.root_cause,
        impact=data.impact,
        prevention=data.prevention,
        cost_impact=data.cost_impact,
        schedule_impact=data.schedule_impact,
        source_type=data.source_type,
        source_project_id=data.source_project_id,
        source_ecn_id=data.source_ecn_id,
        source_issue_id=data.source_issue_id,
        is_sensitive=data.is_sensitive,
        sensitive_reason=data.sensitive_reason,
        visible_to=data.visible_to,
        created_by=current_user.id,
    )

    # 使用统一响应格式
    return success_response(
        data={"id": pitfall.id, "pitfall_no": pitfall.pitfall_no},
        message="踩坑记录创建成功"
    )


@router.get("")
def list_pitfalls(
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    stage: Optional[str] = Query(None, description="阶段筛选"),
    equipment_type: Optional[str] = Query(None, description="设备类型筛选"),
    problem_type: Optional[str] = Query(None, description="问题类型筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    verified_only: bool = Query(False, description="仅显示已验证"),
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取踩坑列表

    支持多维度筛选和关键词搜索
    """
    service = PitfallService(db)

    pitfalls, total = service.list_pitfalls(
        user_id=current_user.id,
        keyword=keyword,
        stage=stage,
        equipment_type=equipment_type,
        problem_type=problem_type,
        status=status,
        verified_only=verified_only,
        skip=pagination.offset,
        limit=pagination.limit,
    )

    items = [
        {
            "id": p.id,
            "pitfall_no": p.pitfall_no,
            "title": p.title,
            "stage": p.stage,
            "equipment_type": p.equipment_type,
            "problem_type": p.problem_type,
            "tags": p.tags,
            "status": p.status,
            "verified": p.verified,
            "verify_count": p.verify_count,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in pitfalls
    ]

    # 使用统一响应格式（注意：这里使用skip/limit，不是page/page_size）
    # 为了兼容，我们计算page和pages
    page = (skip // limit) + 1 if limit > 0 else 1
    pages = (total + limit - 1) // limit if limit > 0 else 1
    
    return paginated_response(
        items=items,
        total=total,
        page=page,
        page_size=limit,
        pages=pages,
        message="获取踩坑列表成功"
    )


@router.get("/{pitfall_id}")
def get_pitfall(
    pitfall_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    获取踩坑详情

    敏感记录需要相应权限
    """
    service = PitfallService(db)

    pitfall = service.get_pitfall(pitfall_id, current_user.id)
    if not pitfall:
        raise HTTPException(status_code=404, detail="踩坑记录不存在或无权限查看")

    # 使用统一响应格式
    return success_response(
        data={
            "id": pitfall.id,
            "pitfall_no": pitfall.pitfall_no,
            "title": pitfall.title,
            "description": pitfall.description,
            "solution": pitfall.solution,
            "stage": pitfall.stage,
            "equipment_type": pitfall.equipment_type,
            "problem_type": pitfall.problem_type,
            "tags": pitfall.tags,
            "root_cause": pitfall.root_cause,
            "impact": pitfall.impact,
            "prevention": pitfall.prevention,
            "cost_impact": float(pitfall.cost_impact) if pitfall.cost_impact else None,
            "schedule_impact": pitfall.schedule_impact,
            "source_type": pitfall.source_type,
            "source_project_id": pitfall.source_project_id,
            "is_sensitive": pitfall.is_sensitive,
            "status": pitfall.status,
            "verified": pitfall.verified,
            "verify_count": pitfall.verify_count,
            "created_by": pitfall.created_by,
            "created_at": pitfall.created_at.isoformat()
            if pitfall.created_at
            else None,
            "updated_at": pitfall.updated_at.isoformat()
            if pitfall.updated_at
            else None,
        },
        message="获取踩坑详情成功"
    )


@router.put("/{pitfall_id}")
def update_pitfall(
    pitfall_id: int,
    data: PitfallUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    更新踩坑记录

    只有创建人可以编辑
    """
    service = PitfallService(db)

    update_data = data.model_dump(exclude_unset=True)
    pitfall = service.update_pitfall(pitfall_id, current_user.id, **update_data)

    if not pitfall:
        raise HTTPException(status_code=404, detail="踩坑记录不存在或无权限编辑")

    # 使用统一响应格式
    return success_response(
        data={"id": pitfall.id},
        message="踩坑记录更新成功"
    )


@router.delete("/{pitfall_id}")
def delete_pitfall(
    pitfall_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    删除踩坑记录

    只有创建人可以删除
    """
    service = PitfallService(db)

    success = service.delete_pitfall(pitfall_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="踩坑记录不存在或无权限删除")

    # 使用统一响应格式
    return success_response(
        data={"id": pitfall_id},
        message="踩坑记录删除成功"
    )


@router.post("/{pitfall_id}/publish")
def publish_pitfall(
    pitfall_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_active_user),
):
    """
    发布踩坑记录

    草稿状态 -> 已发布
    """
    service = PitfallService(db)

    pitfall = service.publish_pitfall(pitfall_id, current_user.id)
    if not pitfall:
        raise HTTPException(status_code=404, detail="踩坑记录不存在或无权限发布")

    # 使用统一响应格式
    return success_response(
        data={"id": pitfall.id, "status": pitfall.status},
        message="踩坑记录发布成功"
    )
