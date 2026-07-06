# -*- coding: utf-8 -*-
"""
文档CRUD操作（重构版）
使用统一响应格式
"""
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.common.pagination import PaginationParams, get_pagination_query
from app.core.schemas import list_response, paginated_response, success_response
from app.models.project import Machine, Project, ProjectDocument
from app.models.user import User
from app.schemas.project import (
    ProjectDocumentCreate,
    ProjectDocumentResponse,
)
from app.services.data_scope.config import DataScopeConfig
from app.services.data_scope.data_scope_service import DataScopeService
from app.services.file_upload_service import FileUploadService
from app.common.query_filters import apply_pagination
from app.utils.db_helpers import get_or_404

router = APIRouter()

DOCUMENT_UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "documents"
DOCUMENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

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


def _is_truthy_optional(value: Any) -> bool:
    return value is not None and value != ""


def _exclude_demo_file_paths(query):
    return query.filter(ProjectDocument.file_path.notlike("/demo/%"))


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
    query = _exclude_demo_file_paths(query)

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
    query = _exclude_demo_file_paths(query)

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


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document_file(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(..., description="上传的文档文件"),
    project_id: int = Form(..., description="关联项目ID"),
    machine_id: Optional[int] = Form(None, description="关联机台ID"),
    doc_type: str = Form("OTHER", description="文档类型"),
    doc_category: Optional[str] = Form(None, description="文档分类"),
    doc_name: Optional[str] = Form(None, description="文档名称"),
    doc_no: Optional[str] = Form(None, description="文档编号"),
    version: str = Form("1.0", description="版本号"),
    description: Optional[str] = Form(None, description="描述"),
    current_user: User = Depends(security.require_permission("document:create")),
) -> Any:
    """
    上传文档文件并创建文档记录。
    """
    get_or_404(db, Project, project_id, "项目不存在")

    if _is_truthy_optional(machine_id):
        machine = (
            db.query(Machine)
            .filter(Machine.id == machine_id, Machine.project_id == project_id)
            .first()
        )
        if not machine:
            raise HTTPException(status_code=404, detail="机台不存在或不属于该项目")

    filename = file.filename or "uploaded_document"
    upload_service = FileUploadService(
        upload_dir=DOCUMENT_UPLOAD_DIR,
        max_file_size=50 * 1024 * 1024,
    )

    is_valid_ext, ext_error = upload_service.validate_file_extension(filename)
    if not is_valid_ext:
        raise HTTPException(status_code=400, detail=ext_error)

    content = await file.read()
    is_valid_size, size_error = upload_service.validate_file_size(len(content))
    if not is_valid_size:
        raise HTTPException(status_code=400, detail=size_error)

    is_valid_content, content_error = upload_service.validate_file_content(content, filename)
    if not is_valid_content:
        raise HTTPException(status_code=400, detail=content_error)

    _, relative_path = upload_service.save_file(
        content,
        filename,
        subdir=str(project_id),
        use_date_subdir=True,
    )

    file_ext = Path(filename).suffix.lower().lstrip(".")
    document = ProjectDocument(
        project_id=project_id,
        machine_id=machine_id,
        doc_type=doc_type or "OTHER",
        doc_category=doc_category,
        doc_name=doc_name or filename,
        doc_no=doc_no,
        version=version or "1.0",
        file_path=relative_path,
        file_name=filename,
        file_size=len(content),
        file_type=file.content_type or file_ext or None,
        description=description,
        uploaded_by=current_user.id,
        status="DRAFT",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    return success_response(
        data=_build_document_response(document),
        message="文档上传成功",
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
    current_user: User = Depends(security.require_permission("document:create")),
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
