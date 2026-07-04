# -*- coding: utf-8 -*-
"""
文化墙内容管理
"""

from datetime import date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.models.culture_wall import CultureWallContent, CultureWallReadRecord
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.culture_wall import (
    CultureWallContentCreate,
    CultureWallContentReview,
    CultureWallContentResponse,
    CultureWallContentUpdate,
)
from app.utils.db_helpers import get_or_404

router = APIRouter()


def _to_content_response(
    content: CultureWallContent,
    *,
    is_read: bool = False,
) -> CultureWallContentResponse:
    return CultureWallContentResponse(
        id=content.id,
        content_type=content.content_type,
        title=content.title,
        content=content.content,
        summary=content.summary,
        images=content.images if content.images else [],
        videos=content.videos if content.videos else [],
        attachments=content.attachments if content.attachments else [],
        is_published=content.is_published,
        publish_date=content.publish_date,
        expire_date=content.expire_date,
        priority=content.priority,
        display_order=content.display_order,
        view_count=content.view_count,
        related_project_id=content.related_project_id,
        related_department_id=content.related_department_id,
        published_by=content.published_by,
        published_by_name=content.published_by_name,
        created_by=content.created_by,
        created_at=content.created_at,
        updated_at=content.updated_at,
        is_read=is_read,
    )


@router.get("/contents", response_model=PaginatedResponse)
def read_culture_wall_contents(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    content_type: Optional[str] = Query(None, description="内容类型筛选"),
    is_published: Optional[bool] = Query(None, description="是否发布筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取文化墙内容列表
    """
    query = db.query(CultureWallContent)

    if content_type:
        query = query.filter(CultureWallContent.content_type == content_type)

    if is_published is not None:
        query = query.filter(CultureWallContent.is_published == is_published)

    query = apply_keyword_filter(
        query, CultureWallContent, keyword, ["title", "content", "summary"]
    )

    total = query.count()
    contents = apply_pagination(
        query.order_by(desc(CultureWallContent.priority), desc(CultureWallContent.created_at)),
        pagination.offset,
        pagination.limit,
    ).all()
    content_ids = [content.id for content in contents]
    read_records = {}
    if content_ids:
        read_records = {
            record.content_id: True
            for record in db.query(CultureWallReadRecord)
            .filter(
                and_(
                    CultureWallReadRecord.content_id.in_(content_ids),
                    CultureWallReadRecord.user_id == current_user.id,
                )
            )
            .all()
        }

    items = []
    for content in contents:
        items.append(
            _to_content_response(content, is_read=read_records.get(content.id, False))
        )

    return PaginatedResponse(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pagination.pages_for_total(total),
    )


@router.post("/contents", response_model=CultureWallContentResponse)
def create_culture_wall_content(
    content_data: CultureWallContentCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    创建文化墙内容
    """
    content = CultureWallContent(
        content_type=content_data.content_type,
        title=content_data.title,
        content=content_data.content,
        summary=content_data.summary,
        images=content_data.images,
        videos=content_data.videos,
        attachments=content_data.attachments,
        is_published=False,
        publish_date=content_data.publish_date,
        expire_date=content_data.expire_date,
        priority=content_data.priority or 0,
        display_order=content_data.display_order or 0,
        related_project_id=content_data.related_project_id,
        related_department_id=content_data.related_department_id,
        published_by=None,
        published_by_name=None,
        created_by=current_user.id,
    )

    db.add(content)
    db.commit()
    db.refresh(content)

    return _to_content_response(content)


@router.get("/contents/{content_id}", response_model=CultureWallContentResponse)
def read_culture_wall_content(
    content_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    获取文化墙内容详情（自动记录阅读）
    """
    content = get_or_404(db, CultureWallContent, content_id, "内容不存在")

    # 增加浏览次数
    content.view_count = (content.view_count or 0) + 1

    # 记录阅读
    read_record = (
        db.query(CultureWallReadRecord)
        .filter(
            and_(
                CultureWallReadRecord.content_id == content_id,
                CultureWallReadRecord.user_id == current_user.id,
            )
        )
        .first()
    )

    if not read_record:
        read_record = CultureWallReadRecord(
            content_id=content_id,
            user_id=current_user.id,
            read_at=datetime.now(),
        )
        db.add(read_record)

    db.commit()

    # 检查是否已读
    is_read = read_record is not None

    return _to_content_response(content, is_read=is_read)


@router.put("/contents/{content_id}", response_model=CultureWallContentResponse)
def update_culture_wall_content(
    content_id: int,
    content_data: CultureWallContentUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    更新文化墙内容
    """
    content = get_or_404(db, CultureWallContent, content_id, "内容不存在")
    update_data = content_data.dict(exclude_unset=True)
    update_data.pop("is_published", None)

    for field, value in update_data.items():
        setattr(content, field, value)

    db.commit()
    db.refresh(content)

    return _to_content_response(content)


@router.post("/contents/{content_id}/review", response_model=CultureWallContentResponse)
def review_culture_wall_content(
    content_id: int,
    review_data: CultureWallContentReview,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    审核文化墙内容，审核通过后才发布到文化墙
    """
    content = get_or_404(db, CultureWallContent, content_id, "内容不存在")

    if review_data.approved:
        content.is_published = True
        if not content.publish_date:
            content.publish_date = date.today()
        content.published_by = current_user.id
        content.published_by_name = current_user.real_name
    else:
        content.is_published = False
        content.published_by = None
        content.published_by_name = None

    db.commit()
    db.refresh(content)

    return _to_content_response(content)


@router.delete("/contents/{content_id}", status_code=status.HTTP_200_OK)
def delete_culture_wall_content(
    content_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """
    删除文化墙内容及其阅读记录
    """
    content = get_or_404(db, CultureWallContent, content_id, "内容不存在")
    db.query(CultureWallReadRecord).filter(
        CultureWallReadRecord.content_id == content_id
    ).delete(synchronize_session=False)
    db.delete(content)
    db.commit()

    return {"message": "删除成功"}
