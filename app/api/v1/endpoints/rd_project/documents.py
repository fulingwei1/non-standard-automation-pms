# -*- coding: utf-8 -*-
"""
研发项目文档管理
"""
import uuid
from pathlib import Path
from typing import Any, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.core.config import settings
from app.models.project import ProjectDocument
from app.models.rd_project import RdProject
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.project import ProjectDocumentCreate, ProjectDocumentResponse
from app.common.query_filters import apply_pagination
from app.utils.db_helpers import get_or_404, save_obj

# 文档上传目录
DOCUMENT_UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "documents" / "rd_projects"
DOCUMENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter()

# ==================== 研发项目文档管理 ====================

# 共 4 个路由

# ==================== 研发项目文档管理 ====================

@router.get("/{project_id}/documents", response_model=ResponseModel)
def get_rd_project_documents(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    pagination: PaginationParams = Depends(get_pagination_query),
    doc_type: Optional[str] = Query(None, description="文档类型筛选"),
    doc_category: Optional[str] = Query(None, description="文档分类筛选"),
    doc_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    current_user: User = Depends(security.require_permission("rd_project:read")),
) -> Any:
    """
    获取研发项目文档列表
    """
    project = get_or_404(db, RdProject, project_id, "研发项目不存在")

    query = db.query(ProjectDocument).filter(ProjectDocument.rd_project_id == project_id)

    if doc_type:
        query = query.filter(ProjectDocument.doc_type == doc_type)
    if doc_category:
        query = query.filter(ProjectDocument.doc_category == doc_category)
    if doc_status:
        query = query.filter(ProjectDocument.status == doc_status)

    total = query.count()
    documents = apply_pagination(query.order_by(desc(ProjectDocument.created_at)), pagination.offset, pagination.limit).all()

    return ResponseModel(
        code=200,
        message="success",
        data=PaginatedResponse(
            items=[ProjectDocumentResponse.model_validate(doc) for doc in documents],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pagination.pages_for_total(total)
        )
    )


@router.post("/{project_id}/documents", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def create_rd_project_document(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    doc_in: ProjectDocumentCreate,
    current_user: User = Depends(security.require_permission("rd_project:read")),
) -> Any:
    """
    创建研发项目文档记录
    """
    project = get_or_404(db, RdProject, project_id, "研发项目不存在")

    doc_data = doc_in.model_dump()
    doc_data["rd_project_id"] = project_id
    doc_data["project_id"] = project.linked_project_id  # 如果有关联的非标项目，也记录
    doc_data["uploaded_by"] = current_user.id

    document = ProjectDocument(**doc_data)
    save_obj(db, document)

    return ResponseModel(
        code=201,
        message="文档创建成功",
        data=ProjectDocumentResponse.model_validate(document)
    )


@router.post("/{project_id}/documents/upload", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
async def upload_rd_project_document(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    file: UploadFile = File(..., description="上传的文件"),
    doc_type: str = Form(..., description="文档类型"),
    doc_category: Optional[str] = Form(None, description="文档分类"),
    doc_name: Optional[str] = Form(None, description="文档名称"),
    doc_no: Optional[str] = Form(None, description="文档编号"),
    version: str = Form("1.0", description="版本号"),
    description: Optional[str] = Form(None, description="描述"),
    current_user: User = Depends(security.require_permission("rd_project:read")),
) -> Any:
    """
    上传研发项目文档（包含文件上传）
    """
    project = get_or_404(db, RdProject, project_id, "研发项目不存在")

    # 生成唯一文件名
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = DOCUMENT_UPLOAD_DIR / str(project_id) / unique_filename
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # 保存文件
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    # 创建文档记录
    doc_data = {
        "rd_project_id": project_id,
        "project_id": project.linked_project_id,
        "doc_type": doc_type,
        "doc_category": doc_category,
        "doc_name": doc_name or file.filename,
        "doc_no": doc_no,
        "version": version,
        "file_path": str(file_path.relative_to(settings.UPLOAD_DIR)),
        "file_name": file.filename,
        "file_size": len(content),
        "file_type": file.content_type or file_ext[1:] if file_ext else None,
        "description": description,
        "uploaded_by": current_user.id,
        "status": "DRAFT",
    }

    document = ProjectDocument(**doc_data)
    save_obj(db, document)

    return ResponseModel(
        code=201,
        message="文档上传成功",
        data=ProjectDocumentResponse.model_validate(document)
    )


@router.get("/{project_id}/documents/{doc_id}/download")
def download_rd_project_document(
    *,
    db: Session = Depends(deps.get_db),
    project_id: int,
    doc_id: int,
    current_user: User = Depends(security.require_permission("rd_project:read")),
) -> Any:
    """
    下载研发项目文档
    """
    project = get_or_404(db, RdProject, project_id, "研发项目不存在")

    document = db.query(ProjectDocument).filter(
        ProjectDocument.id == doc_id,
        ProjectDocument.rd_project_id == project_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="文档不存在")

    upload_dir = Path(settings.UPLOAD_DIR)
    file_path = upload_dir / document.file_path

    # 安全检查：解析为规范路径，防止路径遍历攻击
    resolved_path = file_path.resolve()
    upload_dir_resolved = upload_dir.resolve()

    try:
        resolved_path.relative_to(upload_dir_resolved)
    except ValueError:
        raise HTTPException(status_code=403, detail="访问被拒绝：文件路径不合法")

    if not resolved_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=str(resolved_path),
        filename=document.file_name,
        media_type='application/octet-stream'
    )


