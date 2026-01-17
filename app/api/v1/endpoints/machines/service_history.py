# -*- coding: utf-8 -*-
"""
机台服务历史端点
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.project import Machine
from app.models.service import ServiceRecord
from app.models.user import User
from app.schemas.common import ResponseModel

router = APIRouter()


@router.get("/{machine_id}/service-history", response_model=ResponseModel)
def get_machine_service_history(
    *,
    db: Session = Depends(deps.get_db),
    machine_id: int,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE, description="每页数量"),
    current_user: User = Depends(security.require_permission("machine:read")),
) -> Any:
    """
    设备档案（服务历史记录）
    获取机台的所有服务记录，包括安装、调试、维修、保养等
    """
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="机台不存在")

    # 查询服务记录（通过machine_no匹配）
    query = db.query(ServiceRecord).filter(ServiceRecord.machine_no == machine.machine_no)

    total = query.count()
    offset = (page - 1) * page_size
    records = query.order_by(desc(ServiceRecord.service_date)).offset(offset).limit(page_size).all()

    # 构建服务历史列表
    history_items = []
    for record in records:
        history_items.append({
            "id": record.id,
            "record_no": record.record_no,
            "service_type": record.service_type,
            "service_date": record.service_date.isoformat() if record.service_date else None,
            "service_content": record.service_content,
            "service_result": record.service_result,
            "issues_found": record.issues_found,
            "solution_provided": record.solution_provided,
            "duration_hours": float(record.duration_hours) if record.duration_hours else None,
            "service_engineer_name": record.service_engineer_name,
            "customer_satisfaction": record.customer_satisfaction,
            "customer_feedback": record.customer_feedback,
            "location": record.location,
            "created_at": record.created_at.isoformat() if record.created_at else None
        })

    # 统计信息
    total_records = total
    total_hours = sum([float(r.duration_hours or 0) for r in records])
    avg_satisfaction = None
    satisfaction_scores = [r.customer_satisfaction for r in records if r.customer_satisfaction]
    if satisfaction_scores:
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)

    return ResponseModel(
        code=200,
        message="success",
        data={
            "machine_id": machine_id,
            "machine_no": machine.machine_no,
            "machine_name": machine.machine_name,
            "summary": {
                "total_records": total_records,
                "total_service_hours": round(total_hours, 2),
                "avg_satisfaction": round(avg_satisfaction, 2) if avg_satisfaction else None
            },
            "items": history_items,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "pages": (total + page_size - 1) // page_size
            }
        }
    )
