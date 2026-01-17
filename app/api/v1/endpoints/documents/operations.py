# -*- coding: utf-8 -*-
"""
文档操作API（更新、下载、版本、删除）
"""
from pathlib import Path
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import ProjectDocument
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.project import (
    ProjectDocumentResponse,
    ProjectDocumentUpdate,
)
from app.utils.permission_helpers import check_project_access_or_raise

router = APIRouter()

# 文档上传目录
DOCUMENT_UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "documents"
DOCUMENT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


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
