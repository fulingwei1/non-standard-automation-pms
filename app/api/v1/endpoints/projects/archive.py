# -*- coding: utf-8 -*-
"""
项目归档管理端点

包含归档、取消归档、获取归档列表等操作
"""

from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import Project, ProjectStatusLog
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.project import ProjectArchiveRequest
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter

router = APIRouter()


@router.put("/{project_id}/archive", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def archive_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    reason: Optional[str] = Body(None, description="归档原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    归档项目
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    if project.is_archived:
        return ResponseModel(
            code=200,
            message="项目已归档",
            data={"project_id": project_id}
        )

    # 检查项目是否可以归档（通常需要项目已完成或已结项）
    if project.stage not in ["S9"] and project.status not in ["ST30"]:
        # 非管理员不能归档未完成的项目
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=400,
                detail="项目未完成，无法归档。只有管理员可以强制归档未完成的项目。"
            )

    project.is_archived = True
    project.archived_at = datetime.now()
    project.archived_by = current_user.id

    if reason:
        if project.description:
            project.description += f"\n[归档原因] {reason}"
        else:
            project.description = f"[归档原因] {reason}"

    db.add(project)

    # 记录状态变更
    status_log = ProjectStatusLog(
        project_id=project_id,
        old_stage=project.stage,
        new_stage=project.stage,
        old_status=project.status,
        new_status=project.status,
        old_health=project.health,
        new_health='H4',  # 归档后健康度变为H4
        change_type="ARCHIVE",
        change_reason=reason or "项目归档",
        changed_by=current_user.id,
        changed_at=datetime.now()
    )
    db.add(status_log)

    # 更新健康度为H4（已完结）
    old_health = project.health
    project.health = 'H4'

    db.commit()

    return ResponseModel(
        code=200,
        message="项目归档成功",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "archived_at": project.archived_at.isoformat(),
            "old_health": old_health,
            "new_health": 'H4',
        }
    )


@router.put("/{project_id}/unarchive", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def unarchive_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    reason: Optional[str] = Body(None, description="取消归档原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    取消归档项目
    """
    from app.utils.permission_helpers import check_project_access_or_raise
    project = check_project_access_or_raise(db, current_user, project_id)

    if not project.is_archived:
        return ResponseModel(
            code=200,
            message="项目未归档",
            data={"project_id": project_id}
        )

    project.is_archived = False
    project.archived_at = None
    project.archived_by = None

    db.add(project)

    # 记录状态变更
    status_log = ProjectStatusLog(
        project_id=project_id,
        old_stage=project.stage,
        new_stage=project.stage,
        old_status=project.status,
        new_status=project.status,
        old_health='H4',
        new_health='H1',  # 取消归档后恢复为正常
        change_type="UNARCHIVE",
        change_reason=reason or "取消归档",
        changed_by=current_user.id,
        changed_at=datetime.now()
    )
    db.add(status_log)

    # 恢复健康度为H1
    project.health = 'H1'

    db.commit()

    return ResponseModel(
        code=200,
        message="取消归档成功",
        data={
            "project_id": project_id,
            "project_code": project.project_code,
            "project_name": project.project_name,
        }
    )


@router.get("/archived", response_model=PaginatedResponse, status_code=status.HTTP_200_OK)
def get_archived_projects(
    *,
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    project_type: Optional[str] = Query(None, description="项目类型筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取归档项目列表
    """
    query = db.query(Project).filter(Project.is_archived == True)

    # 应用数据权限过滤
    from app.services.data_scope import DataScopeService
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)

    query = apply_keyword_filter(query, Project, keyword, ["project_name", "project_code"])

    if customer_id:
        query = query.filter(Project.customer_id == customer_id)

    if project_type:
        query = query.filter(Project.project_type == project_type)

    total = query.count()
    projects = apply_pagination(query.order_by(desc(Project.archived_at)), pagination.offset, pagination.limit).all()

    items = []
    for project in projects:
        items.append({
            "id": project.id,
            "project_code": project.project_code,
            "project_name": project.project_name,
            "project_type": project.project_type,
            "customer_name": project.customer_name,
            "pm_name": project.pm_name,
            "stage": project.stage,
            "status": project.status,
            "contract_amount": float(project.contract_amount or 0),
            "archived_at": project.archived_at.isoformat() if project.archived_at else None,
            "archived_by": project.archived_by,
        })

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages = pagination.pages_for_total(total)
    )


@router.post("/batch/archive", response_model=ResponseModel, status_code=status.HTTP_200_OK)
def batch_archive_projects(
    *,
    db: Session = Depends(deps.get_db),
    project_ids: List[int] = Body(..., description="项目ID列表"),
    archive_reason: Optional[str] = Body(None, description="归档原因"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    批量归档项目
    """
    success_count = 0
    failed_projects = []

    from app.services.data_scope import DataScopeService
    query = db.query(Project).filter(Project.id.in_(project_ids))
    query = DataScopeService.filter_projects_by_scope(db, query, current_user)
    accessible_project_ids = {p.id for p in query.all()}

    for project_id in project_ids:
        try:
            if project_id not in accessible_project_ids:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "无访问权限"
                })
                continue

            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "项目不存在"
                })
                continue

            if project.is_archived:
                failed_projects.append({
                    "project_id": project_id,
                    "reason": "项目已归档"
                })
                continue

            # 检查项目是否可以归档
            if project.stage not in ["S9"] and project.status not in ["ST30"]:
                if not current_user.is_superuser:
                    failed_projects.append({
                        "project_id": project_id,
                        "reason": "项目未完成，无法归档"
                    })
                    continue

            project.is_archived = True
            project.archived_at = datetime.now()
            project.archived_by = current_user.id
            project.health = 'H4'

            if archive_reason:
                if project.description:
                    project.description += f"\n[批量归档原因] {archive_reason}"
                else:
                    project.description = f"[批量归档原因] {archive_reason}"

            db.add(project)
            success_count += 1

        except Exception as e:
            failed_projects.append({
                "project_id": project_id,
                "reason": str(e)
            })

    db.commit()

    return ResponseModel(
        code=200,
        message=f"批量归档完成：成功 {success_count} 个，失败 {len(failed_projects)} 个",
        data={
            "success_count": success_count,
            "failed_count": len(failed_projects),
            "failed_projects": failed_projects
        }
    )
