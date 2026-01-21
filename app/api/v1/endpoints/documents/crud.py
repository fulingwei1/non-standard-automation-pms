# -*- coding: utf-8 -*-
"""
文档CRUD操作
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import Machine, Project, ProjectDocument
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.project import (
    ProjectDocumentCreate,
    ProjectDocumentResponse,
)
from app.services.data_scope_service import DataScopeConfig, DataScopeService

router = APIRouter()

# 文档数据权限配置
DOCUMENT_DATA_SCOPE_CONFIG = DataScopeConfig(
    owner_field="uploaded_by",
    project_field="project_id",
)


@router.get("/", response_model=PaginatedResponse[ProjectDocumentResponse])
def read_documents(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    doc_type: Optional[str] = Query(None, description="文档类型筛选"),
    doc_category: Optional[str] = Query(None, description="文档分类筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取文档记录列表（按数据权限过滤）
    """
    query = db.query(ProjectDocument)

    # 应用数据权限过滤
    query = DataScopeService.filter_by_scope(
        db, query, ProjectDocument, current_user, DOCUMENT_DATA_SCOPE_CONFIG
    )

    if project_id:
        query = query.filter(ProjectDocument.project_id == project_id)
    if machine_id:
        query = query.filter(ProjectDocument.machine_id == machine_id)
    if doc_type:
        query = query.filter(ProjectDocument.doc_type == doc_type)
    if doc_category:
        query = query.filter(ProjectDocument.doc_category == doc_category)
    if status:
        query = query.filter(ProjectDocument.status == status)

    total = query.count()
    offset = (page - 1) * page_size
    documents = query.order_by(desc(ProjectDocument.created_at)).offset(offset).limit(page_size).all()

    return PaginatedResponse(
        items=documents,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size
    )


@router.get("/projects/{project_id}/documents", response_model=List[ProjectDocumentResponse])
def get_project_documents(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    machine_id: Optional[int] = Query(None, description="机台ID筛选"),
    doc_type: Optional[str] = Query(None, description="文档类型筛选"),
    current_user: User = Depends(security.require_permission("document:read")),
) -> Any:
    """
    获取项目的文档列表
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    query = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id)

    if machine_id:
        query = query.filter(ProjectDocument.machine_id == machine_id)
    if doc_type:
        query = query.filter(ProjectDocument.doc_type == doc_type)

    documents = query.order_by(desc(ProjectDocument.created_at)).all()
    return documents


@router.get("/{doc_id}", response_model=ProjectDocumentResponse)
def read_document(
    *,
    db: Session = Depends(deps.get_db),
    doc_id: int,
    current_user: User = Depends(security.require_permission("document:read")),
) -> Any:
    """
    获取文档记录详情
    """
    from app.utils.permission_helpers import check_project_access_or_raise

    document = db.query(ProjectDocument).filter(ProjectDocument.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档记录不存在")

    # IDOR 防护：验证用户对该文档所属项目的访问权限
    if document.project_id:
        check_project_access_or_raise(db, current_user, document.project_id)

    return document


@router.post("/", response_model=ProjectDocumentResponse)
def create_document(
    *,
    db: Session = Depends(deps.get_db),
    doc_in: ProjectDocumentCreate,
    current_user: User = Depends(security.require_permission("document:create")),
) -> Any:
    """
    创建文档记录
    """
    project = db.query(Project).filter(Project.id == doc_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 如果指定了机台ID，验证机台是否存在且属于该项目
    if doc_in.machine_id:
        machine = db.query(Machine).filter(
            Machine.id == doc_in.machine_id,
            Machine.project_id == doc_in.project_id
        ).first()
        if not machine:
            raise HTTPException(
                status_code=404,
                detail="机台不存在或不属于该项目"
            )

    doc_data = doc_in.model_dump()
    doc_data['uploaded_by'] = current_user.id

    document = ProjectDocument(**doc_data)
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.post("/projects/{project_id}/documents", response_model=ProjectDocumentResponse)
def create_project_document(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    doc_in: ProjectDocumentCreate,
    current_user: User = Depends(security.require_permission("document:read")),
) -> Any:
    """
    为项目创建文档记录
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")

    # 确保project_id一致
    doc_data = doc_in.model_dump()
    doc_data['project_id'] = project_id
    doc_data['uploaded_by'] = current_user.id

    # 如果指定了机台ID，验证机台是否存在且属于该项目
    if doc_data.get('machine_id'):
        machine = db.query(Machine).filter(
            Machine.id == doc_data['machine_id'],
            Machine.project_id == project_id
        ).first()
        if not machine:
            raise HTTPException(
                status_code=404,
                detail="机台不存在或不属于该项目"
            )

    document = ProjectDocument(**doc_data)
    db.add(document)
    db.commit()
    db.refresh(document)
    return document
