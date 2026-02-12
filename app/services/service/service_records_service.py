# -*- coding: utf-8 -*-
"""
现场服务记录管理服务
"""
import logging

import os
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
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
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.api import deps
from app.common.pagination import get_pagination_params
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.core.config import settings
from app.models.project import Customer, Project
from app.models.service import (
    CustomerCommunication,
    CustomerSatisfaction,
    KnowledgeBase,
    SatisfactionSurveyTemplate,
    ServiceRecord,
    ServiceTicket,
)
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.service import (
    CustomerCommunicationCreate,
    CustomerCommunicationResponse,
    CustomerCommunicationUpdate,
    CustomerSatisfactionCreate,
    CustomerSatisfactionResponse,
    CustomerSatisfactionUpdate,
    KnowledgeBaseCreate,
    KnowledgeBaseResponse,
    KnowledgeBaseUpdate,
    PaginatedResponse,
    SatisfactionSurveyTemplateCreate,
    SatisfactionSurveyTemplateUpdate,
    ServiceDashboardStatistics,
    ServiceRecordCreate,
    ServiceRecordResponse,
    ServiceRecordUpdate,
    ServiceTicketAssign,
    ServiceTicketClose,
    ServiceTicketCreate,
    ServiceTicketResponse,
    ServiceTicketUpdate,
)


logger = logging.getLogger(__name__)


class ServiceRecordsService:
    """现场服务记录管理服务"""

    def __init__(self, db: Session):
        self.db = db

    def get_record_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        technician_id: Optional[int] = None
    ) -> dict:
        """获取服务记录统计"""
        query = self.db.query(ServiceRecord)

        if start_date:
            query = query.filter(ServiceRecord.service_date >= start_date)

        if end_date:
            query = query.filter(ServiceRecord.service_date <= end_date)

        if technician_id:
            query = query.filter(ServiceRecord.technician_id == technician_id)

        # 基础统计
        total_records = query.count()

        # 按类型统计
        type_stats = query.with_entities(
            ServiceRecord.service_type,
            func.count(ServiceRecord.id).label('count')
        ).group_by(ServiceRecord.service_type).all()

        type_distribution = {stat.service_type: stat.count for stat in type_stats}

        # 按状态统计
        status_stats = query.with_entities(
            ServiceRecord.status,
            func.count(ServiceRecord.id).label('count')
        ).group_by(ServiceRecord.status).all()

        status_distribution = {stat.status: stat.count for stat in status_stats}

        # 服务时长统计
        service_durations = []
        for record in query.filter(ServiceRecord.status == "completed").all():
            if record.end_time and record.start_time:
                duration = (record.end_time - record.start_time).total_seconds() / 3600  # 小时
                service_durations.append(duration)

        avg_duration = sum(service_durations) / len(service_durations) if service_durations else 0

        return {
            "total_records": total_records,
            "type_distribution": type_distribution,
            "status_distribution": status_distribution,
            "average_service_duration_hours": round(avg_duration, 2),
            "completed_records": status_distribution.get("completed", 0),
            "completion_rate": (status_distribution.get("completed", 0) / total_records * 100) if total_records > 0 else 0
        }

    def get_service_records(
        self,
        page: int = 1,
        page_size: int = 20,
        keyword: Optional[str] = None,
        service_type: Optional[str] = None,
        status: Optional[str] = None,
        technician_id: Optional[int] = None,
        ticket_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> PaginatedResponse[ServiceRecordResponse]:
        """获取服务记录列表"""
        query = self.db.query(ServiceRecord).options(
            joinedload(ServiceRecord.ticket),
            joinedload(ServiceRecord.technician),
            joinedload(ServiceRecord.created_by_user)
        )

        # 搜索条件
        query = apply_keyword_filter(
            query,
            ServiceRecord,
            keyword,
            ["title", "description", "location"],
        )

        # 筛选条件
        if service_type:
            query = query.filter(ServiceRecord.service_type == service_type)

        if status:
            query = query.filter(ServiceRecord.status == status)

        if technician_id:
            query = query.filter(ServiceRecord.technician_id == technician_id)

        if ticket_id:
            query = query.filter(ServiceRecord.ticket_id == ticket_id)

        if start_date:
            query = query.filter(ServiceRecord.service_date >= start_date)

        if end_date:
            query = query.filter(ServiceRecord.service_date <= end_date)

        # 按服务时间倒序
        query = query.order_by(ServiceRecord.service_date.desc())

        # 分页
        pagination = get_pagination_params(page=page, page_size=page_size)
        total = query.count()
        query = apply_pagination(query, pagination.offset, pagination.limit)
        items = query.all()

        return PaginatedResponse(
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pagination.pages_for_total(total),
            items=[ServiceRecordResponse.model_validate(item) for item in items]
        )

    def create_service_record(
        self,
        record_data: ServiceRecordCreate,
        current_user: User
    ) -> ServiceRecord:
        """创建服务记录"""
        service_record = ServiceRecord(
            ticket_id=record_data.ticket_id,
            title=record_data.title,
            description=record_data.description,
            service_type=record_data.service_type,
            service_date=record_data.service_date or date.today(),
            start_time=record_data.start_time,
            end_time=record_data.end_time,
            location=record_data.location,
            technician_id=record_data.technician_id or current_user.id,
            work_summary=record_data.work_summary,
            parts_used=record_data.parts_used,
            next_actions=record_data.next_actions,
            customer_feedback=record_data.customer_feedback,
            status=record_data.status or "in_progress",
            created_by=current_user.id
        )

        self.db.add(service_record)
        self.db.commit()
        self.db.refresh(service_record)

        # 更新工单状态
        self._update_ticket_status(service_record)

        return service_record

    def upload_record_photos(
        self,
        record_id: int,
        photos: List[UploadFile],
        current_user: User
    ) -> dict:
        """上传服务记录照片"""
        service_record = self.db.query(ServiceRecord).filter(
            ServiceRecord.id == record_id
        ).first()

        if not service_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="服务记录不存在"
            )

        uploaded_photos = []

        for i, photo in enumerate(photos):
            # 生成文件名
            file_extension = os.path.splitext(photo.filename)[1]
            unique_filename = f"record_{record_id}_photo_{i+1}_{uuid.uuid4().hex[:8]}{file_extension}"

            # 保存文件
            upload_dir = Path(settings.UPLOAD_DIR) / "service_records" / str(record_id)
            upload_dir.mkdir(parents=True, exist_ok=True)

            file_path = upload_dir / unique_filename

            try:
                content = photo.file.read()
                with open(file_path, "wb") as f:
                    f.write(content)

                photo_url = f"/uploads/service_records/{record_id}/{unique_filename}"
                uploaded_photos.append({
                    "filename": unique_filename,
                    "url": photo_url,
                    "size": len(content)
                })

            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"照片上传失败: {str(e)}"
                )

        # 更新记录的照片字段
        if not service_record.photos:
            service_record.photos = []

        service_record.photos.extend(uploaded_photos)
        service_record.updated_by = current_user.id
        service_record.updated_at = datetime.now(timezone.utc)

        self.db.commit()

        return {
            "message": f"成功上传 {len(uploaded_photos)} 张照片",
            "photos": uploaded_photos
        }

    def delete_record_photo(
        self,
        record_id: int,
        photo_index: int,
        current_user: User
    ) -> dict:
        """删除服务记录照片"""
        service_record = self.db.query(ServiceRecord).filter(
            ServiceRecord.id == record_id
        ).first()

        if not service_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="服务记录不存在"
            )

        if not service_record.photos or photo_index >= len(service_record.photos):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="照片不存在"
            )

        photo = service_record.photos[photo_index]

        # 删除文件
        file_path = Path(settings.UPLOAD_DIR) / "service_records" / str(record_id) / photo["filename"]
        if file_path.exists():
            file_path.unlink()

        # 从数据库记录中删除
        service_record.photos.pop(photo_index)
        service_record.updated_by = current_user.id
        service_record.updated_at = datetime.now(timezone.utc)

        self.db.commit()

        return {"message": "照片删除成功"}

    def _update_ticket_status(self, service_record: ServiceRecord):
        """更新关联工单状态"""
        if service_record.ticket:
            # 根据服务记录状态更新工单状态
            if service_record.status == "completed" and not service_record.ticket.resolved_at:
                # TODO: 完善实现 - 设置工单为解决状态或等待客户确认
                logger.info("工单状态联动: 暂未实现 (record_id=%s, ticket_id=%s)",
                            service_record.id, service_record.ticket.id)

    # 其他方法可以根据需要添加...
