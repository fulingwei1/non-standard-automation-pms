# -*- coding: utf-8 -*-
"""生产领料单兼容端点。"""
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.production import MaterialRequisition, WorkOrder
from app.models.project import Project
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.utils.db_helpers import get_or_404

router = APIRouter()


@router.get("/material-requisitions", response_model=PaginatedResponse)
def read_material_requisitions(
    db: Session = Depends(deps.get_db),
    pagination: PaginationParams = Depends(get_pagination_query),
    work_order_id: Optional[int] = Query(None, description="工单ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取领料单列表（兼容旧前端路径）。"""
    query = db.query(MaterialRequisition)

    if work_order_id:
        get_or_404(db, WorkOrder, work_order_id, detail="工单不存在")
        query = query.filter(MaterialRequisition.work_order_id == work_order_id)
    if status:
        query = query.filter(MaterialRequisition.status == status)

    total = query.count()
    requisitions = (
        query.order_by(MaterialRequisition.created_at.desc())
        .offset(pagination.offset)
        .limit(pagination.limit)
        .all()
    )

    items = []
    for requisition in requisitions:
        work_order_no = None
        if requisition.work_order_id:
            work_order = (
                db.query(WorkOrder).filter(WorkOrder.id == requisition.work_order_id).first()
            )
            work_order_no = work_order.work_order_no if work_order else None

        project_name = None
        if requisition.project_id:
            project = db.query(Project).filter(Project.id == requisition.project_id).first()
            project_name = project.project_name if project else None

        items.append(
            {
                "id": requisition.id,
                "requisition_no": requisition.requisition_no,
                "work_order_id": requisition.work_order_id,
                "work_order_no": work_order_no,
                "project_id": requisition.project_id,
                "project_name": project_name,
                "applicant_id": requisition.applicant_id,
                "apply_time": requisition.apply_time,
                "apply_reason": requisition.apply_reason,
                "status": requisition.status,
                "approved_by": requisition.approved_by,
                "approved_at": requisition.approved_at,
                "approve_comment": requisition.approve_comment,
                "issued_by": requisition.issued_by,
                "issued_at": requisition.issued_at,
                "items": [],
                "remark": requisition.remark,
                "created_at": requisition.created_at,
                "updated_at": requisition.updated_at,
            }
        )

    return pagination.to_response(items, total)
