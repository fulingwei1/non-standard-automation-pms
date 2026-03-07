# -*- coding: utf-8 -*-
"""
文档CRUD操作（重构版）
使用统一响应格式
"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.core.schemas import list_response, paginated_response, success_response
from app.models.project import Machine, Project, ProjectDocument
from app.models.user import User
from app.schemas.project import (
    ProjectDocumentCreate,
    ProjectDocumentResponse,
)
from app.services.data_scope.config import DataScopeConfig
from app.services.data_scope_service import DataScopeService
from app.common.query_filters import apply_pagination
from app.utils.db_helpers import get_or_404

router = APIRouter()

# 文档数据权限配置
DOCUMENT_DATA_SCOPE_CONFIG = DataScopeConfig(
    owner_field="uploaded_by",
    project_field="project_id",
)


def _build_document_response(document: ProjectDocument) -> ProjectDocumentResponse:
    """将 ORM 文档对象转换为可序列化响应对象。"""
    data = {column.name: getattr(document, column.name) for column in document.__table__.columns}

    # 兼容历史数据中的空值，避免列表页直接 500
    data["version"] = data.get("version") or "1.0"
    data["doc_type"] = data.get("doc_type") or "UNKNOWN"
    data["doc_name"] = data.get("doc_name") or "未命名文档"
    data["file_path"] = data.get("file_path") or ""
    data["file_name"] = data.get("file_name") or data["doc_name"]

    return ProjectDocumentResponse.model_validate(data)


@router.get("/")
def read_documents(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
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
    documents = apply_pagination(query.order_by(desc(ProjectDocument.created_at)), pagination.offset, pagination.limit).all()
    items = [_build_document_response(document) for document in documents]

    # 使用统一响应格式
    return paginated_response(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.get("/projects/{project_id}/documents")
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
    get_or_404(db, Project, project_id, "项目不存在")

    query = db.query(ProjectDocument).filter(ProjectDocument.project_id == project_id)

    if machine_id:
        query = query.filter(ProjectDocument.machine_id == machine_id)
    if doc_type:
        query = query.filter(ProjectDocument.doc_type == doc_type)

    documents = query.order_by(desc(ProjectDocument.created_at)).all()
    items = [_build_document_response(document) for document in documents]
    
    # 使用统一响应格式
    return list_response(
        items=items,
        message="获取项目文档列表成功"
    )


@router.get("/{doc_id}")
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

    document = get_or_404(db, ProjectDocument, doc_id, "文档记录不存在")

    # IDOR 防护：验证用户对该文档所属项目的访问权限
    if document.project_id:
        check_project_access_or_raise(db, current_user, document.project_id)

    # 使用统一响应格式
    return success_response(
        data=_build_document_response(document),
        message="获取文档详情成功"
    )


@router.post("/")
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
    
    # 使用统一响应格式
    return success_response(
        data=_build_document_response(document),
        message="文档创建成功"
    )


@router.post("/projects/{project_id}/documents")
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
    get_or_404(db, Project, project_id, "项目不存在")

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
    
    # 使用统一响应格式
    return success_response(
        data=_build_document_response(document),
        message="项目文档创建成功"
    )
