# -*- coding: utf-8 -*-
"""
知识库管理 - 文件下载
"""
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.service import KnowledgeBase
from app.models.user import User
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

router = APIRouter()


@router.get("/{article_id}/download")
async def download_knowledge_document(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    下载知识库文档
    """
    article = get_or_404(db, KnowledgeBase, article_id, "文章不存在")

    if not article.file_path:
        raise HTTPException(status_code=404, detail="该文章没有附件")

    # 检查下载权限（作者始终可以下载自己的文件）
    is_author = article.author_id == current_user.id
    if not is_author and not article.allow_download:
        raise HTTPException(status_code=403, detail="该文档不允许下载")

    # 构建文件路径
    file_path = Path(settings.UPLOAD_DIR) / article.file_path

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")

    # 安全检查：确保路径在允许的范围内
    try:
        file_path.resolve().relative_to(Path(settings.UPLOAD_DIR).resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="访问被拒绝")

    # 增加下载计数（非作者下载时计数）
    if not is_author:
        article.download_count = (article.download_count or 0) + 1
        db.add(article)
        db.commit()

    return FileResponse(
        path=str(file_path),
        filename=article.file_name or file_path.name,
        media_type=article.file_type or "application/octet-stream",
    )
