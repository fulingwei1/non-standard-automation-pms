from typing import Any, List, Optional
from pathlib import Path
import os

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.api import deps
from app.core.config import settings
from app.core import security
from app.models.user import User
from app.models.project import ProjectDocument, Project, Machine
from app.schemas.project import ProjectDocumentCreate, ProjectDocumentResponse, ProjectDocumentUpdate
from app.schemas.common import PaginatedResponse, ResponseModel
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()

# 文档上传目录
DOCUMENT_UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "documents"
DOCUMENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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
    获取文档记录列表（支持分页、筛选）
    """
    query = db.query(ProjectDocument)
    
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


@router.put("/{doc_id}", response_model=ProjectDocumentResponse)
def update_document(
    *,
    db: Session = Depends(deps.get_db),
    doc_id: int,
    doc_in: ProjectDocumentUpdate,
    current_user: User = Depends(security.require_permission("document:update")),
) -> Any:
    """
    更新文档记录
    """
    document = db.query(ProjectDocument).filter(ProjectDocument.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档记录不存在")

    # IDOR 防护：验证用户对该文档所属项目的访问权限
    if document.project_id:
        check_project_access_or_raise(db, current_user, document.project_id)

    update_data = doc_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(document, field):
            setattr(document, field, value)
    
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.get("/{doc_id}/download")
def download_document(
    *,
    db: Session = Depends(deps.get_db),
    doc_id: int,
    current_user: User = Depends(security.require_permission("document:read")),
) -> Any:
    """
    下载文档文件
    """
    document = db.query(ProjectDocument).filter(ProjectDocument.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档记录不存在")

    # IDOR 防护：验证用户对该文档所属项目的访问权限
    if document.project_id:
        check_project_access_or_raise(db, current_user, document.project_id)

    file_path = Path(document.file_path)

    # 如果是相对路径，转换为绝对路径
    if not file_path.is_absolute():
        file_path = DOCUMENT_UPLOAD_DIR / file_path

    # 安全检查：解析为规范路径，防止路径遍历攻击（如 ../../../etc/passwd）
    resolved_path = file_path.resolve()
    upload_dir_resolved = DOCUMENT_UPLOAD_DIR.resolve()

    # 验证文件路径在允许的上传目录内
    try:
        resolved_path.relative_to(upload_dir_resolved)
    except ValueError:
        # 路径不在上传目录内，可能是路径遍历攻击
        raise HTTPException(status_code=403, detail="访问被拒绝：文件路径不合法")

    if not resolved_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(
        path=str(resolved_path),
        filename=document.file_name,
        media_type='application/octet-stream'
    )


@router.get("/{doc_id}/versions", response_model=List[ProjectDocumentResponse])
def get_document_versions(
    *,
    db: Session = Depends(deps.get_db),
    doc_id: int,
    current_user: User = Depends(security.require_permission("document:read")),
) -> Any:
    """
    获取文档的所有版本
    注意：当前实现基于doc_no和doc_name匹配，后续可以优化为更精确的版本管理
    """
    document = db.query(ProjectDocument).filter(ProjectDocument.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档记录不存在")
    
    # 根据文档编号或名称查找所有版本
    query = db.query(ProjectDocument).filter(
        ProjectDocument.project_id == document.project_id
    )
    
    if document.doc_no:
        query = query.filter(ProjectDocument.doc_no == document.doc_no)
    else:
        # 如果没有文档编号，使用文档名称匹配
        query = query.filter(ProjectDocument.doc_name == document.doc_name)
    
    # 如果指定了机台，也按机台筛选
    if document.machine_id:
        query = query.filter(ProjectDocument.machine_id == document.machine_id)
    
    versions = query.order_by(desc(ProjectDocument.created_at)).all()
    return versions


@router.delete("/{doc_id}", status_code=200)
def delete_document(
    *,
    db: Session = Depends(deps.get_db),
    doc_id: int,
    current_user: User = Depends(security.require_permission("document:delete")),
) -> Any:
    """
    删除文档记录
    注意：这里只删除数据库记录，不删除实际文件。如需删除文件，需要额外处理。
    """
    document = db.query(ProjectDocument).filter(ProjectDocument.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="文档记录不存在")

    # IDOR 防护：验证用户对该文档所属项目的访问权限
    if document.project_id:
        check_project_access_or_raise(db, current_user, document.project_id)

    db.delete(document)
    db.commit()
    
    return ResponseModel(code=200, message="文档记录已删除")
