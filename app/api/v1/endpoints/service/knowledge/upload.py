# -*- coding: utf-8 -*-
"""
知识库管理 - 文件上传
"""
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.service import KnowledgeBase
from app.models.user import User
from app.schemas.service import KnowledgeBaseResponse

from ..number_utils import generate_article_no
from .utils import (
    ALLOWED_EXTENSIONS,
    KNOWLEDGE_UPLOAD_DIR,
    MAX_FILE_SIZE,
    USER_UPLOAD_QUOTA,
    get_user_total_upload_size,
)

router = APIRouter()


@router.post("/upload", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def upload_knowledge_document(
    *,
    db: Session = Depends(deps.get_db),
    file: UploadFile = File(..., description="上传的文件（最大200MB）"),
    title: str = Form(..., description="文档标题"),
    category: str = Form(..., description="分类"),
    tags: Optional[str] = Form(None, description="标签（逗号分隔）"),
    content: Optional[str] = Form(None, description="文档描述"),
    allow_download: bool = Form(True, description="是否允许他人下载"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    上传知识库文档（支持文档、图片、视频，最大200MB，用户配额5GB）
    """
    # 验证文件扩展名
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {file_ext}。支持的类型: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # 读取文件内容并验证大小
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制。最大允许: 200MB，当前文件: {file_size / (1024*1024):.2f}MB"
        )

    # 检查用户上传配额
    current_used = get_user_total_upload_size(db, current_user.id)
    if current_used + file_size > USER_UPLOAD_QUOTA:
        remaining = USER_UPLOAD_QUOTA - current_used
        raise HTTPException(
            status_code=400,
            detail=f"上传配额不足。您的配额: 5GB，已使用: {current_used / (1024*1024*1024):.2f}GB，"
                   f"剩余: {remaining / (1024*1024*1024):.2f}GB，当前文件: {file_size / (1024*1024):.2f}MB"
        )

    # 创建上传目录（按日期分组）
    date_dir = datetime.now().strftime("%Y%m")
    upload_dir = KNOWLEDGE_UPLOAD_DIR / date_dir
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名
    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = upload_dir / unique_filename

    # 保存文件
    with open(file_path, "wb") as f:
        f.write(file_content)

    # 相对路径用于存储
    relative_path = f"knowledge_base/{date_dir}/{unique_filename}"

    # 解析标签
    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # 创建知识库记录
    article = KnowledgeBase(
        article_no=generate_article_no(db),
        title=title,
        category=category,
        content=content or "",
        tags=tag_list,
        is_faq=False,
        is_featured=False,
        status="已发布",
        author_id=current_user.id,
        author_name=current_user.real_name or current_user.username,
        file_path=relative_path,
        file_name=file.filename,
        file_size=file_size,
        file_type=file.content_type,
        allow_download=allow_download,
        download_count=0,
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    return article
