# -*- coding: utf-8 -*-
"""
项目里程碑 CRUD （迁移至 BaseCRUDService）
"""

from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Path, Query, Response, status
from sqlalchemy.orm import Session

from app.api import deps
from app.common.crud import QueryParams
from app.core import security
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.project import MilestoneCreate, MilestoneResponse, MilestoneUpdate
from app.services.project import ProjectMilestoneService
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()


# ==================== 静态端点（必须在 /{milestone_id} 之前注册）====================

@router.get("/statistics", response_model=dict)
def get_milestone_statistics(
    project_id: int = Path(..., description="项目 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:read")),
) -> Any:
    """获取项目里程碑统计"""
    check_project_access_or_raise(db, current_user, project_id)
    
    from sqlalchemy import func
    from app.models.project import ProjectMilestone
    
    total = db.query(func.count(ProjectMilestone.id)).filter(
        ProjectMilestone.project_id == project_id
    ).scalar() or 0
    
    completed = db.query(func.count(ProjectMilestone.id)).filter(
        ProjectMilestone.project_id == project_id,
        ProjectMilestone.status == "COMPLETED"
    ).scalar() or 0
    
    pending = db.query(func.count(ProjectMilestone.id)).filter(
        ProjectMilestone.project_id == project_id,
        ProjectMilestone.status == "PENDING"
    ).scalar() or 0
    
    delayed = db.query(func.count(ProjectMilestone.id)).filter(
        ProjectMilestone.project_id == project_id,
        ProjectMilestone.status == "DELAYED"
    ).scalar() or 0
    
    return {
        "project_id": project_id,
        "total": total,
        "completed": completed,
        "pending": pending,
        "delayed": delayed,
        "completion_rate": round(completed / total * 100, 2) if total > 0 else 0,
    }


@router.get("/summary", response_model=dict)
def get_milestone_summary(
    project_id: int = Path(..., description="项目 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:read")),
) -> Any:
    """获取项目里程碑汇总"""
    check_project_access_or_raise(db, current_user, project_id)
    
    from app.models.project import ProjectMilestone
    
    milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id
    ).all()
    
    return {
        "data": {
            "project_id": project_id,
            "total": len(milestones),
            "completed": sum(1 for m in milestones if m.status == "COMPLETED"),
            "pending": sum(1 for m in milestones if m.status == "PENDING"),
            "overdue": 0,
        }
    }


@router.get("/timeline", response_model=dict)
def get_milestone_timeline(
    project_id: int = Path(..., description="项目 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:read")),
) -> Any:
    """获取项目里程碑时间线"""
    check_project_access_or_raise(db, current_user, project_id)
    
    from app.models.project import ProjectMilestone
    
    milestones = db.query(ProjectMilestone).filter(
        ProjectMilestone.project_id == project_id
    ).order_by(ProjectMilestone.planned_date).all()
    
    return {
        "project_id": project_id,
        "timeline": [
            {
                "id": m.id,
                "milestone_code": m.milestone_code,
                "milestone_name": m.milestone_name,
                "milestone_type": m.milestone_type,
                "planned_date": m.planned_date.isoformat() if m.planned_date else None,
                "actual_date": m.actual_date.isoformat() if m.actual_date else None,
                "status": m.status,
            }
            for m in milestones
        ],
    }


# ==================== CRUD 端点 ====================


def _get_service(db: Session, project_id: int) -> ProjectMilestoneService:
    return ProjectMilestoneService(db=db, project_id=project_id)


def _ensure_project_exists(db: Session, project_id: int) -> None:
    exists = db.query(Project.id).filter(Project.id == project_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="项目不存在")


@router.get("/", response_model=PaginatedResponse[MilestoneResponse])
def list_project_milestones(
    project_id: int = Path(..., description="项目ID"),
    params: QueryParams = Depends(QueryParams),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    status_filter: Optional[str] = Query(None, alias="status", description="状态筛选"),
    milestone_type: Optional[str] = Query(None, description="里程碑类型"),
    owner_id: Optional[int] = Query(None, description="责任人"),
    order_by: Optional[str] = Query(None, description="排序字段"),
    order_direction: Optional[str] = Query(None, description="排序方向 asc/desc"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:read")),
) -> Any:
    """获取项目里程碑列表（统一分页/筛选）"""
    check_project_access_or_raise(db, current_user, project_id)

    params_updates = {}
    if keyword is not None:
        params_updates["search"] = keyword
    if order_by:
        params_updates["sort_by"] = order_by
    if order_direction:
        params_updates["sort_order"] = order_direction
    if params_updates:
        params = params.model_copy(update=params_updates)

    service = _get_service(db, project_id)

    extra_filters = {}
    if status_filter:
        extra_filters["status"] = status_filter
    if milestone_type:
        extra_filters["milestone_type"] = milestone_type
    if owner_id:
        extra_filters["owner_id"] = owner_id

    result = service.list(params=params, extra_filters=extra_filters or None)
    return PaginatedResponse(
        items=result.items,
        total=result.total,
        page=params.page,
        page_size=params.page_size,
        pages=result.pages,
    )


@router.post("/", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED)
def create_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_in: MilestoneCreate = Body(..., description="创建数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:create")),
) -> MilestoneResponse:
    """为项目创建新里程碑"""
    check_project_access_or_raise(db, current_user, project_id, "您没有权限在该项目中创建里程碑")
    _ensure_project_exists(db, project_id)

    service = _get_service(db, project_id)
    return service.create(milestone_in)


@router.get("/{milestone_id}", response_model=MilestoneResponse)
def get_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:read")),
) -> MilestoneResponse:
    """获取单个里程碑"""
    check_project_access_or_raise(db, current_user, project_id)
    service = _get_service(db, project_id)
    return service.get(milestone_id)


@router.put("/{milestone_id}", response_model=MilestoneResponse)
def update_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    milestone_in: MilestoneUpdate = Body(..., description="更新数据"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:update")),
) -> MilestoneResponse:
    """更新里程碑"""
    check_project_access_or_raise(db, current_user, project_id)
    service = _get_service(db, project_id)
    return service.update(milestone_id, milestone_in)


@router.delete(
    "/{milestone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_project_milestone(
    project_id: int = Path(..., description="项目ID"),
    milestone_id: int = Path(..., description="里程碑ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("milestone:delete")),
) -> Response:
    """删除里程碑"""
    check_project_access_or_raise(db, current_user, project_id)
    service = _get_service(db, project_id)
    service.delete(milestone_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
