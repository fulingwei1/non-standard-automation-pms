# -*- coding: utf-8 -*-
"""
文件归档 API endpoints
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.models.business_support import DocumentArchive
from app.models.user import User
from app.schemas.business_support import (
    DocumentArchiveCreate,
    DocumentArchiveResponse,
    DocumentArchiveUpdate,
)
from app.schemas.common import PaginatedResponse, ResponseModel

router = APIRouter()


def generate_archive_no(db: Session) -> str:
    """生成归档编号：ARC250101-001"""
    today = datetime.now()
    month_str = today.strftime("%y%m%d")
    prefix = f"ARC{month_str}-"

    max_archive = (
        db.query(DocumentArchive)
        .filter(DocumentArchive.archive_no.like(f"{prefix}%"))
        .order_by(desc(DocumentArchive.archive_no))
        .first()
    )

    if max_archive:
        try:
            seq = int(max_archive.archive_no.split("-")[-1]) + 1
        except (ValueError, TypeError, IndexError):
            seq = 1
    else:
        seq = 1

    return f"{prefix}{seq:03d}"


@router.post("", response_model=ResponseModel[DocumentArchiveResponse], summary="创建文件归档")
async def create_document_archive(
    archive_data: DocumentArchiveCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:create"))
):
    """创建文件归档"""
    try:
        # 生成归档编号
        archive_no = generate_archive_no(db)

        # 创建归档记录
        archive = DocumentArchive(
            archive_no=archive_no,
            document_type=archive_data.document_type,
            related_type=archive_data.related_type,
            related_id=archive_data.related_id,
            document_name=archive_data.document_name,
            file_path=archive_data.file_path,
            file_size=archive_data.file_size,
            archive_location=archive_data.archive_location,
            archive_date=archive_data.archive_date,
            archiver_id=current_user.id,
            status="archived",
            remark=archive_data.remark
        )

        db.add(archive)
        db.commit()
        db.refresh(archive)

        return ResponseModel(
            code=200,
            message="创建文件归档成功",
            data=DocumentArchiveResponse(
                id=archive.id,
                archive_no=archive.archive_no,
                document_type=archive.document_type,
                related_type=archive.related_type,
                related_id=archive.related_id,
                document_name=archive.document_name,
                file_path=archive.file_path,
                file_size=archive.file_size,
                archive_location=archive.archive_location,
                archive_date=archive.archive_date,
                archiver_id=archive.archiver_id,
                status=archive.status,
                remark=archive.remark,
                created_at=archive.created_at,
                updated_at=archive.updated_at
            )
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建文件归档失败: {str(e)}")


@router.get("", response_model=ResponseModel[PaginatedResponse[DocumentArchiveResponse]], summary="获取文件归档列表")
async def get_document_archives(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    document_type: Optional[str] = Query(None, description="文件类型筛选"),
    related_type: Optional[str] = Query(None, description="关联类型筛选"),
    related_id: Optional[int] = Query(None, description="关联ID筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("business_support:read"))
):
    """获取文件归档列表"""
    try:
        query = db.query(DocumentArchive)

        # 筛选条件
        if document_type:
            query = query.filter(DocumentArchive.document_type == document_type)
        if related_type:
            query = query.filter(DocumentArchive.related_type == related_type)
        if related_id:
            query = query.filter(DocumentArchive.related_id == related_id)
        if search:
            query = query.filter(
                or_(
                    DocumentArchive.document_name.like(f"%{search}%"),
                    DocumentArchive.archive_no.like(f"%{search}%")
                )
            )

        # 总数
        total = query.count()

        # 分页
        items = (
            query.order_by(desc(DocumentArchive.archive_date))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        # 转换为响应格式
        archive_list = [
            DocumentArchiveResponse(
                id=item.id,
                archive_no=item.archive_no,
                document_type=item.document_type,
                related_type=item.related_type,
                related_id=item.related_id,
                document_name=item.document_name,
                file_path=item.file_path,
                file_size=item.file_size,
                archive_location=item.archive_location,
                archive_date=item.archive_date,
                archiver_id=item.archiver_id,
                status=item.status,
                remark=item.remark,
                created_at=item.created_at,
                updated_at=item.updated_at
            )
            for item in items
        ]

        return ResponseModel(
            code=200,
            message="获取文件归档列表成功",
            data=PaginatedResponse(
                items=archive_list,
                total=total,
                page=page,
                page_size=page_size,
                pages=(total + page_size - 1) // page_size
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取文件归档列表失败: {str(e)}")
