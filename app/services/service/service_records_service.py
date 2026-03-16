# -*- coding: utf-8 -*-
"""
现场服务记录兼容服务

该模块仅作为旧服务层的兼容适配器保留：
1. 对外维持历史方法签名，避免遗留测试/调用方失效
2. 对内尽量映射到当前 ServiceRecord 模型的真实字段
3. 不再依赖已经漂移的 ticket/technician/created_by_user 等旧关系
"""

import logging
import uuid
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.common.pagination import get_pagination_params
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core.config import settings
from app.models.service import ServiceRecord
from app.models.service.enums import (
    ServiceRecordStatusEnum,
    normalize_service_record_status,
)
from app.models.user import User
from app.schemas.service import PaginatedResponse, ServiceRecordCreate, ServiceRecordResponse
from app.utils.db_helpers import save_obj

logger = logging.getLogger(__name__)


class ServiceRecordsService:
    """现场服务记录兼容服务。"""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _normalize_status_value(raw_status: Any, default: str) -> str:
        normalized = normalize_service_record_status(raw_status or default)
        if isinstance(normalized, ServiceRecordStatusEnum):
            return normalized.value
        return str(normalized)

    @staticmethod
    def _normalize_photos(photos: Optional[List[Any]]) -> List[Dict[str, Any]]:
        """统一照片结构，兼容历史字符串列表。"""
        normalized: List[Dict[str, Any]] = []
        for photo in photos or []:
            payload: Optional[Dict[str, Any]] = None
            if hasattr(photo, "model_dump"):
                payload = photo.model_dump(mode="json", exclude_none=True)
            elif isinstance(photo, dict):
                payload = {key: value for key, value in photo.items() if value is not None}
            elif isinstance(photo, str):
                payload = {"url": photo, "filename": Path(photo).name or None}

            if payload and payload.get("url"):
                normalized.append(payload)
        return normalized

    @staticmethod
    def _build_record_no(record_data: Any) -> str:
        record_no = getattr(record_data, "record_no", None)
        if record_no:
            return record_no
        return f"LEGACY-SR-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

    @staticmethod
    def _safe_duration_hours(record: Any) -> Optional[float]:
        if getattr(record, "duration_hours", None) is not None:
            try:
                return float(record.duration_hours)
            except (TypeError, ValueError):
                return None

        start_time = getattr(record, "start_time", None)
        end_time = getattr(record, "end_time", None)
        if isinstance(start_time, datetime) and isinstance(end_time, datetime):
            return (end_time - start_time).total_seconds() / 3600.0
        return None

    def get_record_statistics(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        technician_id: Optional[int] = None,
    ) -> dict:
        """获取服务记录统计。"""
        query = self.db.query(ServiceRecord)

        if start_date:
            query = query.filter(ServiceRecord.service_date >= start_date)

        if end_date:
            query = query.filter(ServiceRecord.service_date <= end_date)

        engineer_column = getattr(ServiceRecord, "service_engineer_id", None)
        if technician_id and engineer_column is not None:
            query = query.filter(engineer_column == technician_id)

        total_records = query.count()

        type_stats = (
            query.with_entities(
                ServiceRecord.service_type, func.count(ServiceRecord.id).label("count")
            )
            .group_by(ServiceRecord.service_type)
            .all()
        )
        type_distribution = {stat.service_type: stat.count for stat in type_stats}

        status_stats = (
            query.with_entities(ServiceRecord.status, func.count(ServiceRecord.id).label("count"))
            .group_by(ServiceRecord.status)
            .all()
        )
        status_distribution = {stat.status: stat.count for stat in status_stats}

        completed_records = query.filter(
            ServiceRecord.status.in_(
                [ServiceRecordStatusEnum.COMPLETED.value, ServiceRecordStatusEnum.CANCELLED.value]
            )
        ).all()
        service_durations = [
            duration
            for duration in (self._safe_duration_hours(record) for record in completed_records)
            if duration is not None
        ]
        avg_duration = (
            sum(service_durations) / len(service_durations) if service_durations else 0
        )

        completed_count = status_distribution.get(ServiceRecordStatusEnum.COMPLETED.value, 0)

        return {
            "total_records": total_records,
            "type_distribution": type_distribution,
            "status_distribution": status_distribution,
            "average_service_duration_hours": round(avg_duration, 2),
            "completed_records": completed_count,
            "completion_rate": (
                (completed_count / total_records * 100) if total_records > 0 else 0
            ),
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
        end_date: Optional[date] = None,
    ) -> PaginatedResponse[ServiceRecordResponse]:
        """获取服务记录列表。"""
        query = self.db.query(ServiceRecord).options(
            joinedload(ServiceRecord.project),
            joinedload(ServiceRecord.customer),
            joinedload(ServiceRecord.service_engineer),
        )

        query = apply_keyword_filter(
            query,
            ServiceRecord,
            keyword,
            ["record_no", "service_content", "location"],
        )

        if service_type:
            query = query.filter(ServiceRecord.service_type == service_type)

        if status:
            query = query.filter(
                ServiceRecord.status
                == self._normalize_status_value(status, ServiceRecordStatusEnum.SCHEDULED.value)
            )

        engineer_column = getattr(ServiceRecord, "service_engineer_id", None)
        if technician_id and engineer_column is not None:
            query = query.filter(engineer_column == technician_id)

        ticket_column = getattr(ServiceRecord, "ticket_id", None)
        if ticket_id and ticket_column is not None:
            query = query.filter(ticket_column == ticket_id)

        if start_date:
            query = query.filter(ServiceRecord.service_date >= start_date)

        if end_date:
            query = query.filter(ServiceRecord.service_date <= end_date)

        query = query.order_by(ServiceRecord.service_date.desc())

        pagination = get_pagination_params(page=page, page_size=page_size)
        total = query.count()
        items = apply_pagination(query, pagination.offset, pagination.limit).all()

        return PaginatedResponse(
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pagination.pages_for_total(total),
            items=[ServiceRecordResponse.model_validate(item) for item in items],
        )

    def create_service_record(
        self,
        record_data: ServiceRecordCreate,
        current_user: Optional[User] = None,
        current_user_id: Optional[int] = None,
    ) -> ServiceRecord:
        """创建服务记录。"""
        operator_id = getattr(current_user, "id", None) or current_user_id
        service_record = ServiceRecord(
            record_no=self._build_record_no(record_data),
            service_type=getattr(record_data, "service_type", None) or "OTHER",
            project_id=getattr(record_data, "project_id", None) or 0,
            machine_no=getattr(record_data, "machine_no", None),
            customer_id=getattr(record_data, "customer_id", None) or 0,
            location=getattr(record_data, "location", None),
            service_date=getattr(record_data, "service_date", None) or date.today(),
            start_time=getattr(record_data, "start_time", None),
            end_time=getattr(record_data, "end_time", None),
            duration_hours=getattr(record_data, "duration_hours", None),
            service_engineer_id=(
                getattr(record_data, "service_engineer_id", None)
                or getattr(record_data, "technician_id", None)
                or operator_id
                or 0
            ),
            service_content=(
                getattr(record_data, "service_content", None)
                or getattr(record_data, "description", None)
                or getattr(record_data, "work_summary", None)
                or getattr(record_data, "title", None)
                or ""
            ),
            service_result=getattr(record_data, "service_result", None),
            issues_found=getattr(record_data, "issues_found", None),
            solution_provided=(
                getattr(record_data, "solution_provided", None)
                or getattr(record_data, "next_actions", None)
            ),
            photos=self._normalize_photos(getattr(record_data, "photos", None)),
            customer_feedback=getattr(record_data, "customer_feedback", None),
            status=self._normalize_status_value(
                getattr(record_data, "status", None),
                ServiceRecordStatusEnum.IN_PROGRESS.value,
            ),
        )

        save_obj(self.db, service_record)
        self._update_ticket_status(service_record)
        return service_record

    def upload_record_photos(
        self, record_id: int, photos: List[UploadFile], current_user: Optional[User]
    ) -> dict:
        """上传服务记录照片。"""
        service_record = self.db.query(ServiceRecord).filter(ServiceRecord.id == record_id).first()

        if not service_record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="服务记录不存在")

        uploaded_photos: List[Dict[str, Any]] = []
        existing_photos = self._normalize_photos(getattr(service_record, "photos", None))

        for index, photo in enumerate(photos):
            file_extension = Path(getattr(photo, "filename", "")).suffix
            unique_filename = (
                f"record_{record_id}_photo_{index + 1}_{uuid.uuid4().hex[:8]}{file_extension}"
            )
            upload_dir = Path(settings.UPLOAD_DIR) / "service_records" / str(record_id)
            upload_dir.mkdir(parents=True, exist_ok=True)
            file_path = upload_dir / unique_filename

            try:
                content = photo.file.read()
                with open(file_path, "wb") as file_obj:
                    file_obj.write(content)
            except Exception as exc:  # pragma: no cover - 防御式保护
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"照片上传失败: {exc}",
                ) from exc

            uploaded_photos.append(
                {
                    "filename": unique_filename,
                    "url": f"service_records/{record_id}/{unique_filename}",
                    "size": len(content),
                    "uploaded_at": datetime.now().isoformat(),
                    "uploaded_by": (
                        getattr(current_user, "username", None)
                        or getattr(current_user, "real_name", None)
                    ),
                }
            )

        service_record.photos = existing_photos + uploaded_photos
        self.db.add(service_record)
        self.db.commit()

        return {"message": f"成功上传 {len(uploaded_photos)} 张照片", "photos": uploaded_photos}

    def delete_record_photo(
        self, record_id: int, photo_index: int, current_user: Optional[User]
    ) -> dict:
        """删除服务记录照片。"""
        service_record = self.db.query(ServiceRecord).filter(ServiceRecord.id == record_id).first()

        if not service_record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="服务记录不存在")

        photos = self._normalize_photos(getattr(service_record, "photos", None))
        if photo_index < 0 or photo_index >= len(photos):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="照片不存在")

        photo = photos.pop(photo_index)
        if photo.get("url"):
            file_path = Path(settings.UPLOAD_DIR) / photo["url"]
            if file_path.exists():
                file_path.unlink()

        service_record.photos = photos
        self.db.add(service_record)
        self.db.commit()

        return {"message": "照片删除成功"}

    def _update_ticket_status(self, service_record: ServiceRecord) -> None:
        """保留旧钩子，但不再依赖已移除的 ticket 关系。"""
        ticket = getattr(service_record, "ticket", None)
        if not ticket:
            return

        normalized_status = self._normalize_status_value(
            getattr(service_record, "status", None),
            ServiceRecordStatusEnum.IN_PROGRESS.value,
        )
        if normalized_status == ServiceRecordStatusEnum.COMPLETED.value and not getattr(
            ticket, "resolved_at", None
        ):
            logger.info(
                "记录兼容层检测到关联工单可更新 (record_id=%s, ticket_id=%s)",
                getattr(service_record, "id", None),
                getattr(ticket, "id", None),
            )
