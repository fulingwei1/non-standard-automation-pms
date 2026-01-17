# -*- coding: utf-8 -*-
"""
知识库管理 API endpoints - 基础CRUD
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, List, Optional

from fastapi import (
    APIRouter,
    Body,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.service import KnowledgeBase
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.service import (
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
)

from .number_utils import generate_article_no

router = APIRouter()

# 知识库上传目录
KNOWLEDGE_UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "knowledge_base"
KNOWLEDGE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 允许的文件类型（文档和视频）
ALLOWED_EXTENSIONS = {
    # 文档
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    '.txt', '.md', '.csv', '.rtf', '.odt', '.ods', '.odp',
    # 图片
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
    # 视频
    '.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv', '.webm', '.m4v',
    # 压缩包
    '.zip', '.rar', '.7z', '.tar', '.gz',
}

# 最大文件大小：200MB
MAX_FILE_SIZE = 200 * 1024 * 1024

# 用户上传配额：5GB
USER_UPLOAD_QUOTA = 5 * 1024 * 1024 * 1024


def get_user_total_upload_size(db: Session, user_id: int) -> int:
    """获取用户已上传文件的总大小"""
    result = db.query(func.sum(KnowledgeBase.file_size)).filter(
        KnowledgeBase.author_id == user_id,
        KnowledgeBase.file_size.isnot(None)
    ).scalar()
    return result or 0


@router.get("/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_knowledge_base_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取知识库统计
    """
    total = db.query(KnowledgeBase).count()
    published = db.query(KnowledgeBase).filter(KnowledgeBase.status == "已发布").count()
    faq = db.query(KnowledgeBase).filter(KnowledgeBase.is_faq == True).count()
    featured = db.query(KnowledgeBase).filter(KnowledgeBase.is_featured == True).count()

    # 总浏览量
    total_views = db.query(func.sum(KnowledgeBase.view_count)).scalar() or 0

    return {
        "total": total,
        "published": published,
        "faq": faq,
        "featured": featured,
        "total_views": int(total_views),
    }


@router.get("/quota", response_model=dict, status_code=status.HTTP_200_OK)
def get_upload_quota(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取当前用户的上传配额使用情况
    """
    used = get_user_total_upload_size(db, current_user.id)
    return {
        "quota": USER_UPLOAD_QUOTA,
        "used": used,
        "remaining": USER_UPLOAD_QUOTA - used,
        "quota_gb": USER_UPLOAD_QUOTA / (1024 * 1024 * 1024),
        "used_gb": used / (1024 * 1024 * 1024),
        "remaining_gb": (USER_UPLOAD_QUOTA - used) / (1024 * 1024 * 1024),
        "usage_percent": (used / USER_UPLOAD_QUOTA * 100) if USER_UPLOAD_QUOTA > 0 else 0,
    }


@router.get("", response_model=PaginatedResponse[KnowledgeBaseResponse], status_code=status.HTTP_200_OK)
def read_knowledge_base(
    db: Session = Depends(deps.get_db),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    category: Optional[str] = Query(None, description="分类筛选"),
    is_faq: Optional[bool] = Query(None, description="是否FAQ筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取知识库文章列表
    """
    query = db.query(KnowledgeBase)

    if category:
        query = query.filter(KnowledgeBase.category == category)
    if is_faq is not None:
        query = query.filter(KnowledgeBase.is_faq == is_faq)
    if status:
        query = query.filter(KnowledgeBase.status == status)
    if keyword:
        query = query.filter(
            or_(
                KnowledgeBase.article_no.like(f"%{keyword}%"),
                KnowledgeBase.title.like(f"%{keyword}%"),
                KnowledgeBase.content.like(f"%{keyword}%"),
            )
        )

    # 精选优先，然后按浏览量排序
    total = query.count()
    items = query.order_by(
        desc(KnowledgeBase.is_featured),
        desc(KnowledgeBase.view_count)
    ).offset((page - 1) * page_size).limit(page_size).all()

    # 获取作者姓名
    for item in items:
        if item.author_id:
            author = db.query(User).filter(User.id == item.author_id).first()
            if author:
                item.author_name = author.name or author.username

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size,
    }


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    *,
    db: Session = Depends(deps.get_db),
    article_in: KnowledgeBaseCreate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建知识库文章
    """
    article = KnowledgeBase(
        article_no=generate_article_no(db),
        title=article_in.title,
        category=article_in.category,
        content=article_in.content,
        tags=article_in.tags or [],
        is_faq=article_in.is_faq or False,
        is_featured=article_in.is_featured or False,
        status=article_in.status or "DRAFT",
        author_id=current_user.id,
        author_name=current_user.real_name or current_user.username,
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    return article


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


@router.get("/{article_id}", response_model=KnowledgeBaseResponse, status_code=status.HTTP_200_OK)
def read_knowledge_base_article(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取知识库文章详情（增加浏览量）
    """
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 增加浏览量
    article.view_count = (article.view_count or 0) + 1
    db.add(article)
    db.commit()
    db.refresh(article)

    return article


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
    from fastapi.responses import FileResponse

    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

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


@router.put("/{article_id}", response_model=KnowledgeBaseResponse, status_code=status.HTTP_200_OK)
def update_knowledge_base(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    article_in: KnowledgeBaseUpdate,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新知识库文章
    """
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    if article_in.title is not None:
        article.title = article_in.title
    if article_in.category is not None:
        article.category = article_in.category
    if article_in.content is not None:
        article.content = article_in.content
    if article_in.tags is not None:
        article.tags = article_in.tags
    if article_in.is_faq is not None:
        article.is_faq = article_in.is_faq
    if article_in.is_featured is not None:
        article.is_featured = article_in.is_featured
    if article_in.status is not None:
        article.status = article_in.status

    db.add(article)
    db.commit()
    db.refresh(article)

    return article


@router.delete("/{article_id}", status_code=status.HTTP_200_OK)
def delete_knowledge_base(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除知识库文章
    """
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    db.delete(article)
    db.commit()

    return {"message": "文章已删除"}


@router.post("/{article_id}/like", response_model=KnowledgeBaseResponse, status_code=status.HTTP_200_OK)
def like_knowledge_base(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    点赞知识库文章
    """
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    article.like_count = (article.like_count or 0) + 1
    db.add(article)
    db.commit()
    db.refresh(article)

    return article


@router.post("/{article_id}/helpful", response_model=KnowledgeBaseResponse, status_code=status.HTTP_200_OK)
def mark_knowledge_base_helpful(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    标记知识库文章为有用
    """
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    article.helpful_count = (article.helpful_count or 0) + 1
    db.add(article)
    db.commit()
    db.refresh(article)

    return article


@router.post("/{article_id}/adopt", response_model=KnowledgeBaseResponse, status_code=status.HTTP_200_OK)
def adopt_knowledge_base(
    *,
    db: Session = Depends(deps.get_db),
    article_id: int,
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    标记采用知识库文章（表示该文档被实际应用到工作中）
    """
    article = db.query(KnowledgeBase).filter(KnowledgeBase.id == article_id).first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    article.adopt_count = (article.adopt_count or 0) + 1
    db.add(article)
    db.commit()
    db.refresh(article)

    return article


@router.post("", response_model=ResponseModel, status_code=status.HTTP_201_CREATED)
def add_knowledge_entry(
    *,
    db: Session = Depends(deps.get_db),
    title: str = Body(..., description="知识条目标题"),
    content: str = Body(..., description="知识条目内容"),
    category: str = Body(..., description="分类"),
    tags: Optional[List[str]] = Body(None, description="标签列表"),
    entry_type: str = Body("article", description="条目类型：article/issue/solution"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    添加知识条目
    快速添加知识库文章
    """
    article = KnowledgeBase(
        article_no=generate_article_no(db),
        title=title,
        category=category,
        content=content,
        tags=tags or [],
        is_faq=False,
        is_featured=False,
        status="PUBLISHED",  # 直接发布
        author_id=current_user.id,
        author_name=current_user.real_name or current_user.username,
    )

    db.add(article)
    db.commit()
    db.refresh(article)

    return ResponseModel(
        code=200,
        message="知识条目添加成功",
        data={
            "id": article.id,
            "article_no": article.article_no,
            "title": article.title,
            "category": article.category,
            "entry_type": entry_type,
            "created_at": article.created_at.isoformat() if article.created_at else None
        }
    )
