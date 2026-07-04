# -*- coding: utf-8 -*-
"""生产领料单兼容端点。"""
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
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
from app.services.data_scope.config import DataScopeConfig
from app.services.data_scope.data_scope_service import DataScopeService
from app.services.inventory.outbound_service import OutboundService
from app.services.inventory.stock_update_service import InsufficientStockError
from app.utils.db_helpers import get_or_404

router = APIRouter()
DEFAULT_ISSUE_LOCATION = "默认仓库"

# 领料单数据权限配置
MATERIAL_REQUISITION_DATA_SCOPE_CONFIG = DataScopeConfig(
    owner_field="applicant_id",
    additional_owner_fields=["approved_by", "issued_by"],
    project_field="project_id",
)


def _inventory_tenant_id(user: User) -> int:
    return int(getattr(user, "tenant_id", None) or 1)


def _decimal_qty(value: Any, field_name: str) -> Decimal:
    try:
        qty = Decimal(str(value))
    except Exception:
        raise HTTPException(status_code=400, detail=f"{field_name} 必须是有效数字")
    if qty <= Decimal("0"):
        raise HTTPException(status_code=400, detail=f"{field_name} 必须大于0")
    return qty


def _generate_requisition_no(db: Session) -> str:
    prefix = f"MR-{datetime.now().strftime('%Y%m%d')}-"
    latest = (
        db.query(MaterialRequisition.requisition_no)
        .filter(MaterialRequisition.requisition_no.like(f"{prefix}%"))
        .order_by(MaterialRequisition.requisition_no.desc())
        .first()
    )
    seq = 1
    if latest and latest[0]:
        try:
            seq = int(str(latest[0]).rsplit("-", 1)[-1]) + 1
        except ValueError:
            seq = 1
    return f"{prefix}{seq:03d}"


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

    # 应用数据权限过滤
    query = DataScopeService.filter_by_scope(
        db, query, MaterialRequisition, current_user, MATERIAL_REQUISITION_DATA_SCOPE_CONFIG
    )

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


@router.post("/material-requisitions", response_model=ResponseModel)
def create_material_requisition(
    data: dict[str, Any] = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.get_current_active_user),
) -> Any:
    """创建领料单（兼容旧前端路径）。"""
    work_order_id = data.get("work_order_id")
    project_id = data.get("project_id")
    work_order = None
    if work_order_id:
        work_order = get_or_404(db, WorkOrder, work_order_id, detail="工单不存在")
        project_id = project_id or work_order.project_id
    if project_id:
        get_or_404(db, Project, project_id, detail="项目不存在")

    items_payload = data.get("items") or []
    if not items_payload:
        raise HTTPException(status_code=400, detail="领料单至少需要 1 条明细")

    validated_items: list[tuple[Material, Decimal, Optional[str]]] = []
    for idx, item in enumerate(items_payload, start=1):
        material_id = item.get("material_id")
        material = get_or_404(db, Material, material_id, detail=f"第 {idx} 行物料不存在")
        request_qty = _decimal_qty(item.get("request_qty"), f"第 {idx} 行申请数量")
        validated_items.append((material, request_qty, item.get("remark")))

    requisition = MaterialRequisition(
        requisition_no=_generate_requisition_no(db),
        work_order_id=work_order.id if work_order else None,
        project_id=project_id,
        applicant_id=current_user.id,
        apply_time=datetime.now(),
        apply_reason=data.get("apply_reason"),
        status="DRAFT",
        remark=data.get("remark"),
    )
    db.add(requisition)
    db.flush()

    for material, request_qty, remark in validated_items:
        db.add(
            MaterialRequisitionItem(
                requisition_id=requisition.id,
                material_id=material.id,
                request_qty=request_qty,
                unit=material.unit,
                remark=remark,
            )
        )

    db.commit()
    db.refresh(requisition)
    return ResponseModel(code=200, message="创建成功", data=_serialize_requisition(db, requisition))


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
                item.approved_qty = _decimal_qty(value, "批准数量")
            elif item.approved_qty is None:
                item.approved_qty = item.request_qty

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
    if requisition.status == "ISSUED":
        raise HTTPException(status_code=400, detail="领料单已发料，不能重复发料")
    if requisition.status != "APPROVED":
        raise HTTPException(status_code=400, detail="只有已审批领料单可以发料")

    location = data.get("location") or DEFAULT_ISSUE_LOCATION
    work_order = requisition.work_order
    requisition.status = "ISSUED"
    requisition.issued_by = current_user.id
    requisition.issued_at = datetime.now()

    issued_qty = data.get("issued_qty") or {}
    outbound = OutboundService(db, tenant_id=_inventory_tenant_id(current_user))
    try:
        for item in requisition.items:
            value = None
            if isinstance(issued_qty, dict):
                value = issued_qty.get(str(item.id), issued_qty.get(item.id))
            issue_qty = _decimal_qty(
                value if value is not None else (item.approved_qty or item.request_qty),
                "发料数量",
            )
            approved_qty = item.approved_qty or item.request_qty
            if issue_qty > approved_qty:
                raise HTTPException(status_code=400, detail="发料数量不能大于批准数量")

            outbound.issue_material(
                material_id=item.material_id,
                quantity=issue_qty,
                location=location,
                work_order_id=requisition.work_order_id,
                work_order_no=getattr(work_order, "work_order_no", None),
                project_id=requisition.project_id,
                operator_id=current_user.id,
                remark=f"领料单 {requisition.requisition_no} 发料",
                commit=False,
            )
            item.issued_qty = issue_qty

        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except InsufficientStockError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"发料失败: {exc}")

    db.refresh(requisition)
    return ResponseModel(code=200, message="发料成功", data=_serialize_requisition(db, requisition))
