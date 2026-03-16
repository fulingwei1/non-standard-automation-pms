# -*- coding: utf-8 -*-
"""
现场服务记录管理 API endpoints
"""

import uuid
from datetime import date, datetime
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
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api import deps
from app.common.date_range import get_month_range
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter, apply_pagination
from app.core import security
from app.core.config import settings
from app.models.project import Customer, Project
from app.models.service import ServiceRecord
from app.models.service.enums import ServiceRecordStatusEnum, normalize_service_record_status
from app.models.user import User
from app.schemas.common import PaginatedResponse, ResponseModel
from app.schemas.service import (
    ServiceRecordCreate,
    ServiceRecordPhoto,
    ServiceRecordResponse,
)
from app.utils.permission_helpers import check_project_access_or_raise

from .access import (
    ensure_service_record_access_or_raise,
    filter_service_project_query,
)
from .number_utils import generate_record_no

router = APIRouter()


def _normalize_record_photos(photos: Optional[list[Any]]) -> list[dict[str, Any]]:
    """统一服务记录照片结构，兼容历史字符串列表。"""
    normalized: list[dict[str, Any]] = []
    for photo in photos or []:
        payload: dict[str, Any] | None = None
        if isinstance(photo, ServiceRecordPhoto):
            payload = photo.model_dump(mode="json", exclude_none=True)
        elif hasattr(photo, "model_dump"):
            payload = photo.model_dump(mode="json", exclude_none=True)
        elif isinstance(photo, dict):
            payload = {key: value for key, value in photo.items() if value is not None}
        elif isinstance(photo, str):
            payload = {"url": photo, "filename": Path(photo).name or None}

        if payload and payload.get("url"):
            normalized.append(payload)

    return normalized


def _serialize_service_record(item: ServiceRecord) -> dict[str, Any]:
    return {
        "id": item.id,
        "record_no": item.record_no,
        "service_type": item.service_type,
        "project_id": item.project_id,
        "project_name": item.project_name,
        "machine_no": item.machine_no,
        "customer_id": item.customer_id,
        "customer_name": item.customer_name,
        "location": item.location,
        "service_date": item.service_date,
        "start_time": item.start_time,
        "end_time": item.end_time,
        "duration_hours": item.duration_hours,
        "service_engineer_id": item.service_engineer_id,
        "service_engineer_name": item.service_engineer_name,
        "customer_contact": item.customer_contact,
        "customer_phone": item.customer_phone,
        "service_content": item.service_content,
        "service_result": item.service_result,
        "issues_found": item.issues_found,
        "solution_provided": item.solution_provided,
        "photos": _normalize_record_photos(item.photos),
        "customer_satisfaction": item.customer_satisfaction,
        "customer_feedback": item.customer_feedback,
        "customer_signed": item.customer_signed,
        "status": normalize_service_record_status(item.status)
        or ServiceRecordStatusEnum.SCHEDULED.value,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
    }


@router.get("/statistics", response_model=dict, status_code=status.HTTP_200_OK)
def get_service_record_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("service:read")),
) -> Any:
    """
    获取服务记录统计
    """
    query = filter_service_project_query(db, db.query(ServiceRecord), current_user, ServiceRecord.project_id)

    in_progress_statuses = [
        ServiceRecordStatusEnum.IN_PROGRESS.value,
        "ACTIVE",
    ]
    completed_statuses = [
        ServiceRecordStatusEnum.COMPLETED.value,
        "APPROVED",
    ]
    cancelled_statuses = [
        ServiceRecordStatusEnum.CANCELLED.value,
    ]

    total = query.count()
    in_progress = query.filter(ServiceRecord.status.in_(in_progress_statuses)).count()
    completed = query.filter(ServiceRecord.status.in_(completed_statuses)).count()
    cancelled = query.filter(ServiceRecord.status.in_(cancelled_statuses)).count()

    # 本月服务数
    this_month_start, _ = get_month_range(date.today())
    this_month = query.filter(ServiceRecord.service_date >= this_month_start).count()

    # 总服务时长
    total_duration = query.with_entities(func.sum(ServiceRecord.duration_hours)).scalar() or 0

    return {
        "total": total,
        "in_progress": in_progress,
        "completed": completed,
        "cancelled": cancelled,
        "this_month": this_month,
        "total_duration": float(total_duration),
    }


@router.get(
    "", response_model=PaginatedResponse[ServiceRecordResponse], status_code=status.HTTP_200_OK
)
def read_service_records(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    service_type: Optional[str] = Query(None, description="服务类型筛选"),
    record_status: Optional[str] = Query(None, alias="status", description="状态筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    service_engineer_id: Optional[int] = Query(None, description="服务工程师ID筛选"),
    date_from: Optional[date] = Query(None, description="开始日期"),
    date_to: Optional[date] = Query(None, description="结束日期"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    current_user: User = Depends(security.require_permission("service:read")),
) -> Any:
    """
    获取服务记录列表
    """
    query = db.query(ServiceRecord)
    query = filter_service_project_query(db, query, current_user, ServiceRecord.project_id)

    if service_type:
        query = query.filter(ServiceRecord.service_type == service_type)
    if record_status:
        record_status = normalize_service_record_status(record_status)
        query = query.filter(ServiceRecord.status == record_status)
    if project_id:
        check_project_access_or_raise(db, current_user, project_id, "您没有权限查看该项目的服务记录")
        query = query.filter(ServiceRecord.project_id == project_id)
    if customer_id:
        query = query.filter(ServiceRecord.customer_id == customer_id)
    if service_engineer_id:
        query = query.filter(ServiceRecord.service_engineer_id == service_engineer_id)
    if date_from:
        query = query.filter(ServiceRecord.service_date >= date_from)
    if date_to:
        query = query.filter(ServiceRecord.service_date <= date_to)

    # 应用关键词过滤（记录编号/服务内容/位置）
    query = apply_keyword_filter(
        query, ServiceRecord, keyword, ["record_no", "service_content", "location"]
    )

    total = query.count()
    items = apply_pagination(
        query.order_by(desc(ServiceRecord.service_date)), pagination.offset, pagination.limit
    ).all()

    # 获取项目名称和客户名称
    serialized_items = []
    for item in items:
        if item.project_id:
            project = db.query(Project).filter(Project.id == item.project_id).first()
            if project:
                item.project_name = project.project_name
        if item.customer_id:
            customer = db.query(Customer).filter(Customer.id == item.customer_id).first()
            if customer:
                item.customer_name = customer.customer_name
        if item.service_engineer_id:
            from app.models.user import User

            engineer = db.query(User).filter(User.id == item.service_engineer_id).first()
            if engineer:
                item.service_engineer_name = engineer.real_name or engineer.username
        serialized_items.append(_serialize_service_record(item))

    return {
        "items": serialized_items,
        "total": total,
        "page": pagination.page,
        "page_size": pagination.page_size,
        "pages": pagination.pages_for_total(total),
    }


@router.post("", response_model=ServiceRecordResponse, status_code=status.HTTP_201_CREATED)
def create_service_record(
    *,
    db: Session = Depends(deps.get_db),
    record_in: ServiceRecordCreate,
    current_user: User = Depends(security.require_permission("service:create")),
) -> Any:
    """
    创建服务记录
    """
    # 验证项目是否存在
    project = db.query(Project).filter(Project.id == record_in.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"项目不存在 (ID: {record_in.project_id})")
    check_project_access_or_raise(db, current_user, record_in.project_id, "您没有权限在该项目下创建服务记录")

    # 验证客户是否存在
    customer = db.query(Customer).filter(Customer.id == record_in.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"客户不存在 (ID: {record_in.customer_id})")

    # 验证服务工程师是否存在
    from app.models.user import User

    engineer = db.query(User).filter(User.id == record_in.service_engineer_id).first()
    if not engineer:
        raise HTTPException(
            status_code=404, detail=f"服务工程师不存在 (ID: {record_in.service_engineer_id})"
        )

    record = ServiceRecord(
        record_no=generate_record_no(db),
        service_type=record_in.service_type,
        project_id=record_in.project_id,
        machine_no=record_in.machine_no,
        customer_id=record_in.customer_id,
        location=record_in.location,
        service_date=record_in.service_date,
        start_time=record_in.start_time,
        end_time=record_in.end_time,
        duration_hours=record_in.duration_hours,
        service_engineer_id=record_in.service_engineer_id,
        service_engineer_name=engineer.real_name or engineer.username,
        customer_contact=record_in.customer_contact,
        customer_phone=record_in.customer_phone,
        service_content=record_in.service_content,
        service_result=record_in.service_result,
        issues_found=record_in.issues_found,
        solution_provided=record_in.solution_provided,
        photos=_normalize_record_photos(record_in.photos),
        customer_satisfaction=record_in.customer_satisfaction,
        customer_feedback=record_in.customer_feedback,
        customer_signed=record_in.customer_signed or False,
        status=(record_in.status or ServiceRecordStatusEnum.SCHEDULED).value,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    # 获取项目名称和客户名称
    if record.project_id:
        project = db.query(Project).filter(Project.id == record.project_id).first()
        if project:
            record.project_name = project.project_name
    if record.customer_id:
        customer = db.query(Customer).filter(Customer.id == record.customer_id).first()
        if customer:
            record.customer_name = customer.customer_name

    return _serialize_service_record(record)


@router.post(
    "/{record_id}/photos", response_model=ResponseModel, status_code=status.HTTP_201_CREATED
)
async def upload_service_record_photo(
    *,
    db: Session = Depends(deps.get_db),
    record_id: int,
    file: UploadFile = File(..., description="照片文件"),
    description: Optional[str] = Form(None, description="照片描述"),
    current_user: User = Depends(security.require_permission("service:update")),
) -> Any:
    """
    上传服务记录照片
    """
    # 验证服务记录是否存在
    record = ensure_service_record_access_or_raise(db, current_user, record_id)

    # 验证文件类型
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="只支持图片文件")

    # 验证文件大小（最大5MB）
    file_content = await file.read()
    if len(file_content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过5MB")

    # 创建上传目录
    upload_dir = Path(settings.UPLOAD_DIR) / "service_records" / str(record_id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名
    file_ext = Path(file.filename).suffix
    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = upload_dir / unique_filename

    # 保存文件
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    # 生成文件URL（相对路径）
    relative_path = f"service_records/{record_id}/{unique_filename}"

    # 更新服务记录的照片列表
    photos = _normalize_record_photos(record.photos)
    photos.append(
        {
            "url": relative_path,
            "filename": file.filename,
            "size": len(file_content),
            "type": file.content_type,
            "description": description,
            "uploaded_at": datetime.now().isoformat(),
            "uploaded_by": current_user.real_name or current_user.username,
        }
    )
    record.photos = photos

    db.add(record)
    db.commit()
    db.refresh(record)

    return ResponseModel(
        code=201,
        message="照片上传成功",
        data={
            "record_id": record_id,
            "photo": photos[-1],
            "total_photos": len(photos),
        },
    )


@router.delete(
    "/{record_id}/photos/{photo_index}",
    response_model=ResponseModel,
    status_code=status.HTTP_200_OK,
)
def delete_service_record_photo(
    *,
    db: Session = Depends(deps.get_db),
    record_id: int,
    photo_index: int,
    current_user: User = Depends(security.require_permission("service:update")),
) -> Any:
    """
    删除服务记录照片
    """
    # 验证服务记录是否存在
    record = ensure_service_record_access_or_raise(db, current_user, record_id)

    photos = _normalize_record_photos(record.photos)
    if photo_index < 0 or photo_index >= len(photos):
        raise HTTPException(status_code=400, detail="照片索引无效")

    # 删除文件
    photo = photos[photo_index]
    if "url" in photo:
        file_path = Path(settings.UPLOAD_DIR) / photo["url"]
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                import logging

                logging.warning(f"删除照片文件失败: {str(e)}")

    # 从列表中移除
    photos.pop(photo_index)
    record.photos = photos

    db.add(record)
    db.commit()

    return ResponseModel(
        code=200,
        message="照片删除成功",
        data={
            "record_id": record_id,
            "total_photos": len(photos),
        },
    )
