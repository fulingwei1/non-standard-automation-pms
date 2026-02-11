# -*- coding: utf-8 -*-
"""
研发项目立项管理
"""
from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter
from app.core import security
from app.models.project import Project
from app.models.rd_project import RdProject
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.rd_project import (
    RdProjectApproveRequest,
    RdProjectCloseRequest,
    RdProjectCreate,
    RdProjectLinkRequest,
    RdProjectResponse,
    RdProjectUpdate,
)

from .utils import generate_project_no

router = APIRouter()

# ==================== 研发项目立项 ====================

@router.get("/rd-projects", response_model=PaginatedResponse)
def get_rd_projects(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    keyword: Optional[str] = Query(None, description="关键词搜索（项目名称/编号）"),
    category_id: Optional[int] = Query(None, description="分类ID筛选"),
    category_type: Optional[str] = Query(None, description="项目类型筛选：SELF/ENTRUST/COOPERATION"),
    project_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    approval_status: Optional[str] = Query(None, description="审批状态筛选"),
    project_manager_id: Optional[int] = Query(None, description="项目负责人ID筛选"),
    current_user: User = Depends(security.require_permission("rd_project:read")),
) -> Any:
    """
    获取研发项目列表（支持分页、搜索、筛选）
    """
    query = db.query(RdProject)

    # 关键词搜索
    query = apply_keyword_filter(query, RdProject, keyword, ["project_name", "project_no"])

    # 筛选条件
    if category_id:
        query = query.filter(RdProject.category_id == category_id)
    if category_type:
        query = query.filter(RdProject.category_type == category_type)
    if project_status:
        query = query.filter(RdProject.status == project_status)
    if approval_status:
        query = query.filter(RdProject.approval_status == approval_status)
    if project_manager_id:
        query = query.filter(RdProject.project_manager_id == project_manager_id)

    # 总数
    total = query.count()

    # 分页
    projects = apply_pagination(query.order_by(desc(RdProject.created_at)), pagination.offset, pagination.limit).all()

    items = [RdProjectResponse.model_validate(proj) for proj in projects]

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total)
    )


@router.post("/rd-projects", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_rd_project(
    *,
    db: Session = Depends(deps.get_db),
    project_in: RdProjectCreate,
    current_user: User = Depends(security.require_permission("rd_project:read")),
) -> Any:
    """
    创建研发项目（立项申请）
    """
    # 生成项目编号
    project_no = generate_project_no(db)

    # 获取项目负责人姓名
    project_manager_name = None
    if project_in.project_manager_id:
        manager = db.query(User).filter(User.id == project_in.project_manager_id).first()
        if manager:
            project_manager_name = manager.real_name or manager.username

    # 创建研发项目
    project = RdProject(
        project_no=project_no,
        project_name=project_in.project_name,
        category_id=project_in.category_id,
        category_type=project_in.category_type,
        initiation_date=project_in.initiation_date,
        planned_start_date=project_in.planned_start_date,
        planned_end_date=project_in.planned_end_date,
        project_manager_id=project_in.project_manager_id,
        project_manager_name=project_manager_name,
        initiation_reason=project_in.initiation_reason,
        research_goal=project_in.research_goal,
        research_content=project_in.research_content,
        expected_result=project_in.expected_result,
        budget_amount=project_in.budget_amount,
        linked_project_id=project_in.linked_project_id,
        status='DRAFT',
        approval_status='PENDING',
        remark=project_in.remark,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return ResponseModel(
        code=201,
        message="研发项目创建成功",
        data=RdProjectResponse.model_validate(project)
    )


@router.get("/rd-projects/{project_id}", response_model=ResponseModel)
def get_rd_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    current_user: User = Depends(security.require_permission("rd_project:read")),
) -> Any:
    """
    获取研发项目详情
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")

    return ResponseModel(
        code=200,
        message="success",
        data=RdProjectResponse.model_validate(project)
    )


@router.put("/rd-projects/{project_id}", response_model=ResponseModel)
def update_rd_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    project_in: RdProjectUpdate,
    current_user: User = Depends(security.require_permission("rd_project:read")),
) -> Any:
    """
    更新研发项目
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")

    # 只有草稿状态才能更新
    if project.status != 'DRAFT':
        raise HTTPException(status_code=400, detail="只有草稿状态的研发项目才能更新")

    # 更新字段
    update_data = project_in.model_dump(exclude_unset=True)

    # 更新项目负责人姓名
    if 'project_manager_id' in update_data and update_data['project_manager_id']:
        manager = db.query(User).filter(User.id == update_data['project_manager_id']).first()
        if manager:
            update_data['project_manager_name'] = manager.real_name or manager.username

    for field, value in update_data.items():
        setattr(project, field, value)

    db.add(project)
    db.commit()
    db.refresh(project)

    return ResponseModel(
        code=200,
        message="研发项目更新成功",
        data=RdProjectResponse.model_validate(project)
    )


@router.put("/rd-projects/{project_id}/approve", response_model=ResponseModel)
def approve_rd_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    approve_request: RdProjectApproveRequest,
    current_user: User = Depends(security.require_permission("rd_project:read")),
) -> Any:
    """
    研发项目审批
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")

    if project.approval_status != 'PENDING':
        raise HTTPException(status_code=400, detail="只有待审批状态的研发项目才能审批")

    if approve_request.approved:
        project.approval_status = 'APPROVED'
        project.status = 'APPROVED'
        project.approved_by = current_user.id
        project.approved_at = datetime.now()
    else:
        project.approval_status = 'REJECTED'
        project.status = 'DRAFT'

    project.approval_remark = approve_request.approval_remark

    db.add(project)
    db.commit()
    db.refresh(project)

    return ResponseModel(
        code=200,
        message="研发项目审批成功" if approve_request.approved else "研发项目已驳回",
        data=RdProjectResponse.model_validate(project)
    )


@router.put("/rd-projects/{project_id}/close", response_model=ResponseModel)
def close_rd_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    close_request: RdProjectCloseRequest,
    current_user: User = Depends(security.require_permission("rd_project:read")),
) -> Any:
    """
    研发项目结项
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")

    if project.status in ['COMPLETED', 'CANCELLED']:
        raise HTTPException(status_code=400, detail="项目已结项或已取消")

    project.status = 'COMPLETED'
    project.close_date = date.today()
    project.close_reason = close_request.close_reason
    project.close_result = close_request.close_result
    project.closed_by = current_user.id

    db.add(project)
    db.commit()
    db.refresh(project)

    return ResponseModel(
        code=200,
        message="研发项目结项成功",
        data=RdProjectResponse.model_validate(project)
    )


@router.put("/rd-projects/{project_id}/link-project", response_model=ResponseModel)
def link_rd_project(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    link_request: RdProjectLinkRequest,
    current_user: User = Depends(security.require_permission("rd_project:read")),
) -> Any:
    """
    关联非标项目
    """
    project = db.query(RdProject).filter(RdProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="研发项目不存在")

    # 验证关联的非标项目是否存在
    linked_project = db.query(Project).filter(Project.id == link_request.linked_project_id).first()
    if not linked_project:
        raise HTTPException(status_code=404, detail="关联的非标项目不存在")

    project.linked_project_id = link_request.linked_project_id

    db.add(project)
    db.commit()
    db.refresh(project)

    return ResponseModel(
        code=200,
        message="关联非标项目成功",
        data=RdProjectResponse.model_validate(project)
    )



