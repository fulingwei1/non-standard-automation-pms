# -*- coding: utf-8 -*-
"""生产领料单兼容端点。"""
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.common.pagination import PaginationParams, get_pagination_query
from app.core import security
from app.models.material import Material
from app.models.production import MaterialRequisition, MaterialRequisitionItem, WorkOrder
from app.models.project import Project
from app.models.user import User
from app.schemas.common import ResponseModel
from app.schemas.common import PaginatedResponse
from app.utils.db_helpers import get_or_404

router = APIRouter()


def _serialize_requisition(db: Session, requisition: MaterialRequisition) -> dict[str, Any]:
    work_order_no = None
    if requisition.work_order_id:
        work_order = db.query(WorkOrder).filter(WorkOrder.id == requisition.work_order_id).first()
        work_order_no = work_order.work_order_no if work_order else None

    project_name = None
    if requisition.project_id:
        project = db.query(Project).filter(Project.id == requisition.project_id).first()
        project_name = project.project_name if project else None

    applicant_name = None
    if requisition.applicant_id:
        applicant = db.query(User).filter(User.id == requisition.applicant_id).first()
        applicant_name = applicant.real_name or applicant.username if applicant else None

    item_rows = (
        db.query(MaterialRequisitionItem, Material)
        .outerjoin(Material, Material.id == MaterialRequisitionItem.material_id)
        .filter(MaterialRequisitionItem.requisition_id == requisition.id)
        .order_by(MaterialRequisitionItem.id)
        .all()
    )
    items = []
    for item, material in item_rows:
        items.append(
            {
                "id": item.id,
                "requisition_id": item.requisition_id,
                "material_id": item.material_id,
                "material_code": material.material_code if material else None,
                "material_name": material.material_name if material else None,
                "specification": material.specification if material else None,
                "request_qty": float(item.request_qty or 0),
                "approved_qty": float(item.approved_qty or 0) if item.approved_qty is not None else None,
                "issued_qty": float(item.issued_qty or 0) if item.issued_qty is not None else None,
                "unit": item.unit or (material.unit if material else None),
                "remark": item.remark,
            }
        )

    return {
        "id": requisition.id,
        "requisition_no": requisition.requisition_no,
        "work_order_id": requisition.work_order_id,
        "work_order_no": work_order_no,
        "project_id": requisition.project_id,
        "project_name": project_name,
        "applicant_id": requisition.applicant_id,
        "applicant_name": applicant_name,
        "apply_time": requisition.apply_time,
        "apply_reason": requisition.apply_reason,
        "status": requisition.status,
        "approved_by": requisition.approved_by,
        "approved_at": requisition.approved_at,
        "approve_comment": requisition.approve_comment,
        "issued_by": requisition.issued_by,
        "issued_at": requisition.issued_at,
        "items": items,
        "remark": requisition.remark,
        "created_at": requisition.created_at,
        "updated_at": requisition.updated_at,
    }


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
        data = _serialize_requisition(db, requisition)
        data["items"] = []
        items.append(data)

    return pagination.to_response(items, total)


@router.get("/material-requisitions/{requisition_id}", response_model=ResponseModel)
def read_material_requisition(
    requisition_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """获取领料单详情（兼容旧前端路径）。"""
    requisition = get_or_404(db, MaterialRequisition, requisition_id, detail="领料单不存在")
    return ResponseModel(code=200, message="success", data=_serialize_requisition(db, requisition))


@router.put("/material-requisitions/{requisition_id}/approve", response_model=ResponseModel)
def approve_material_requisition(
    requisition_id: int,
    data: dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """审批领料单（兼容旧前端路径）。"""
    requisition = get_or_404(db, MaterialRequisition, requisition_id, detail="领料单不存在")
    requisition.status = "APPROVED"
    requisition.approved_by = current_user.id
    requisition.approved_at = datetime.now()
    requisition.approve_comment = data.get("approve_comment") or data.get("comment")

    approved_qty = data.get("approved_qty") or {}
    if isinstance(approved_qty, dict):
        for item in requisition.items:
            value = approved_qty.get(str(item.id), approved_qty.get(item.id))
            if value is not None:
                item.approved_qty = value

    db.commit()
    db.refresh(requisition)
    return ResponseModel(code=200, message="审批成功", data=_serialize_requisition(db, requisition))


@router.put("/material-requisitions/{requisition_id}/issue", response_model=ResponseModel)
def issue_material_requisition(
    requisition_id: int,
    data: dict[str, Any] = Body(default_factory=dict),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """发料领料单（兼容旧前端路径）。"""
    requisition = get_or_404(db, MaterialRequisition, requisition_id, detail="领料单不存在")
    requisition.status = "ISSUED"
    requisition.issued_by = current_user.id
    requisition.issued_at = datetime.now()

    issued_qty = data.get("issued_qty") or {}
    if isinstance(issued_qty, dict):
        for item in requisition.items:
            value = issued_qty.get(str(item.id), issued_qty.get(item.id))
            if value is not None:
                item.issued_qty = value

    db.commit()
    db.refresh(requisition)
    return ResponseModel(code=200, message="发料成功", data=_serialize_requisition(db, requisition))
