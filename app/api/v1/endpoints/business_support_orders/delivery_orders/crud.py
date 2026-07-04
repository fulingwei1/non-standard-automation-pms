# -*- coding: utf-8 -*-
"""
发货单基础CRUD操作
包含：列表、创建、详情、更新
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter
from app.models.approval import ApprovalInstance, ApprovalTask
from app.models.business_support import DeliveryOrder, DeliveryOrderItem, SalesOrder, SalesOrderItem
from app.models.project import Project
from app.models.production import QualityInspection, WorkOrder
from app.models.user import User
from app.schemas.business_support import (
    DeliveryApprovalRequest,
    DeliveryOrderCreate,
    DeliveryOrderItemCreate,
    DeliveryOrderItemResponse,
    DeliveryOrderResponse,
    DeliveryOrderUpdate,
)
from app.schemas.common import PaginatedResponse, ResponseModel
from app.services.approval_engine import ApprovalEngineService
from app.services.sales.payment_plan_service import PaymentPlanService
from app.utils.db_helpers import get_or_404

from ..utils import generate_delivery_no

router = APIRouter()

DELIVERY_ORDER_APPROVAL_ENTITY_TYPE = "DELIVERY_ORDER"
DELIVERY_ORDER_APPROVAL_TEMPLATE_CODE = "TPL_DELIVERY_ORDER"
ACTIVE_APPROVAL_STATUSES = {"PENDING", "IN_PROGRESS"}
READY_MATERIAL_STATUSES = {"齐套", "READY", "KITTED", "COMPLETE", "COMPLETED"}
FINAL_INSPECTION_TYPES = {"FQC", "OQC"}
PROJECT_STATUS_RANK = {f"ST{idx:02d}": idx for idx in range(1, 31)}


def _as_decimal(value: Any) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _build_delivery_item_response(item: DeliveryOrderItem) -> DeliveryOrderItemResponse:
    return DeliveryOrderItemResponse(
        id=item.id,
        delivery_order_id=item.delivery_order_id,
        sales_order_item_id=item.sales_order_item_id,
        material_id=item.material_id,
        item_name=item.item_name,
        item_spec=item.item_spec,
        delivery_qty=item.delivery_qty,
        unit=item.unit,
        unit_price=item.unit_price,
        amount=item.amount,
        quality_status=item.quality_status,
        remark=item.remark,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def _allocated_sales_order_qty(db: Session, sales_order_item_id: int) -> Decimal:
    allocated = (
        db.query(func.coalesce(func.sum(DeliveryOrderItem.delivery_qty), 0))
        .join(DeliveryOrder, DeliveryOrder.id == DeliveryOrderItem.delivery_order_id)
        .filter(
            DeliveryOrderItem.sales_order_item_id == sales_order_item_id,
            DeliveryOrder.delivery_status != "returned",
        )
        .scalar()
    )
    return _as_decimal(allocated)


def _remaining_sales_order_qty(db: Session, source_item: SalesOrderItem) -> Decimal:
    return _as_decimal(source_item.qty) - _allocated_sales_order_qty(db, source_item.id)


def _get_sales_order_item(
    db: Session, sales_order_id: int, sales_order_item_id: int
) -> SalesOrderItem:
    source_item = (
        db.query(SalesOrderItem)
        .filter(
            SalesOrderItem.id == sales_order_item_id,
            SalesOrderItem.sales_order_id == sales_order_id,
        )
        .first()
    )
    if not source_item:
        raise HTTPException(status_code=400, detail="发货明细不属于当前销售订单")
    return source_item


def _build_delivery_order_item(
    *,
    db: Session,
    sales_order: SalesOrder,
    item_data: DeliveryOrderItemCreate,
    source_item: Optional[SalesOrderItem] = None,
) -> DeliveryOrderItem:
    if item_data.sales_order_item_id:
        source_item = _get_sales_order_item(db, sales_order.id, item_data.sales_order_item_id)

    delivery_qty = _as_decimal(item_data.delivery_qty)
    if source_item:
        remaining_qty = _remaining_sales_order_qty(db, source_item)
        if delivery_qty > remaining_qty:
            raise HTTPException(
                status_code=400,
                detail=f"发货数量超过销售订单明细剩余数量：剩余 {remaining_qty}",
            )
        item_name = item_data.item_name or source_item.item_name
        if not item_name:
            raise HTTPException(status_code=400, detail="发货明细名称不能为空")
        unit_price = item_data.unit_price if item_data.unit_price is not None else source_item.unit_price
        amount = item_data.amount
        if amount is None and unit_price is not None:
            amount = delivery_qty * _as_decimal(unit_price)
        return DeliveryOrderItem(
            sales_order_item_id=source_item.id,
            material_id=item_data.material_id,
            item_name=item_name,
            item_spec=item_data.item_spec or source_item.item_spec,
            delivery_qty=delivery_qty,
            unit=item_data.unit or source_item.unit,
            unit_price=unit_price,
            amount=amount if amount is not None else source_item.amount,
            quality_status="pending",
            remark=item_data.remark or source_item.remark,
        )

    if not item_data.item_name:
        raise HTTPException(status_code=400, detail="手工发货明细必须填写名称")
    return DeliveryOrderItem(
        material_id=item_data.material_id,
        item_name=item_data.item_name,
        item_spec=item_data.item_spec,
        delivery_qty=delivery_qty,
        unit=item_data.unit,
        unit_price=item_data.unit_price,
        amount=item_data.amount,
        quality_status="pending",
        remark=item_data.remark,
    )


def _build_delivery_order_items(db: Session, sales_order: SalesOrder, delivery_data: DeliveryOrderCreate) -> list[DeliveryOrderItem]:
    if delivery_data.items:
        return [
            _build_delivery_order_item(db=db, sales_order=sales_order, item_data=item_data)
            for item_data in delivery_data.items
        ]

    source_items = list(sales_order.order_items or [])
    if not source_items:
        raise HTTPException(status_code=400, detail="发货单必须包含明细行，销售订单也没有可复制明细")

    delivery_items: list[DeliveryOrderItem] = []
    for source_item in source_items:
        remaining_qty = _remaining_sales_order_qty(db, source_item)
        if remaining_qty <= 0:
            continue
        delivery_items.append(
            _build_delivery_order_item(
                db=db,
                sales_order=sales_order,
                source_item=source_item,
                item_data=DeliveryOrderItemCreate(
                    sales_order_item_id=source_item.id,
                    item_name=source_item.item_name,
                    item_spec=source_item.item_spec,
                    delivery_qty=remaining_qty,
                    unit=source_item.unit,
                    unit_price=source_item.unit_price,
                    amount=source_item.amount,
                    remark=source_item.remark,
                ),
            )
        )

    if not delivery_items:
        raise HTTPException(status_code=400, detail="销售订单明细已全部发货，不能重复创建发货单")
    return delivery_items


def _ensure_delivery_has_valid_items(delivery_order: DeliveryOrder) -> None:
    items = list(delivery_order.items or [])
    if not items:
        raise HTTPException(status_code=400, detail="发货单没有明细行，不能发货")
    if any(_as_decimal(item.delivery_qty) <= 0 for item in items):
        raise HTTPException(status_code=400, detail="发货明细数量必须大于0")


def _ensure_project_kitting_ready(project: Optional[Project]) -> None:
    if not project:
        raise HTTPException(status_code=400, detail="发货单未关联项目，不能发货")

    material_status = (project.material_status or "").strip()
    kitting_rate = _as_decimal(project.kitting_rate)
    shortage_items_count = int(project.shortage_items_count or 0)
    status_is_ready = material_status.upper() in READY_MATERIAL_STATUSES or material_status == "齐套"
    if not status_is_ready or kitting_rate < 100 or shortage_items_count > 0:
        raise HTTPException(
            status_code=400,
            detail=(
                "项目未达到发货齐套门禁："
                f"物料状态={material_status or '未设置'}，"
                f"齐套率={kitting_rate}，缺料项={shortage_items_count}"
            ),
        )


def _latest_final_quality_inspection(
    db: Session, delivery_order: DeliveryOrder
) -> Optional[QualityInspection]:
    if delivery_order.project_id:
        inspection = (
            db.query(QualityInspection)
            .join(WorkOrder, WorkOrder.id == QualityInspection.work_order_id)
            .filter(
                WorkOrder.project_id == delivery_order.project_id,
                QualityInspection.inspection_type.in_(FINAL_INSPECTION_TYPES),
            )
            .order_by(desc(QualityInspection.inspection_date), desc(QualityInspection.id))
            .first()
        )
        if inspection:
            return inspection

    material_ids = [item.material_id for item in delivery_order.items or [] if item.material_id]
    if not material_ids:
        return None
    return (
        db.query(QualityInspection)
        .filter(
            QualityInspection.material_id.in_(material_ids),
            QualityInspection.inspection_type.in_(FINAL_INSPECTION_TYPES),
        )
        .order_by(desc(QualityInspection.inspection_date), desc(QualityInspection.id))
        .first()
    )


def _ensure_final_quality_passed(db: Session, delivery_order: DeliveryOrder) -> None:
    inspection = _latest_final_quality_inspection(db, delivery_order)
    if not inspection:
        raise HTTPException(status_code=400, detail="项目缺少FQC/OQC质检通过记录，不能发货")
    if inspection.inspection_result != "PASS":
        raise HTTPException(
            status_code=400,
            detail=f"项目最终质检未通过，当前结果为 {inspection.inspection_result}",
        )


def _advance_project_status(project: Optional[Project], *, stage: str, status: str) -> None:
    if not project:
        return
    current_rank = PROJECT_STATUS_RANK.get(project.status or "", 0)
    target_rank = PROJECT_STATUS_RANK[status]
    if current_rank <= target_rank:
        project.stage = stage
        project.status = status


def build_delivery_order_response(delivery_order: DeliveryOrder) -> DeliveryOrderResponse:
    """构建发货单响应对象"""
    return DeliveryOrderResponse(
        id=delivery_order.id,
        delivery_no=delivery_order.delivery_no,
        order_id=delivery_order.order_id,
        order_no=delivery_order.order_no,
        contract_id=delivery_order.contract_id,
        customer_id=delivery_order.customer_id,
        customer_name=delivery_order.customer_name,
        project_id=delivery_order.project_id,
        delivery_date=delivery_order.delivery_date,
        delivery_type=delivery_order.delivery_type,
        logistics_company=delivery_order.logistics_company,
        tracking_no=delivery_order.tracking_no,
        receiver_name=delivery_order.receiver_name,
        receiver_phone=delivery_order.receiver_phone,
        receiver_address=delivery_order.receiver_address,
        delivery_amount=delivery_order.delivery_amount,
        approval_status=delivery_order.approval_status,
        approval_comment=delivery_order.approval_comment,
        approved_by=delivery_order.approved_by,
        approved_at=delivery_order.approved_at,
        special_approval=delivery_order.special_approval,
        special_approver_id=delivery_order.special_approver_id,
        special_approval_reason=delivery_order.special_approval_reason,
        delivery_status=delivery_order.delivery_status,
        print_date=delivery_order.print_date,
        ship_date=delivery_order.ship_date,
        receive_date=delivery_order.receive_date,
        return_status=delivery_order.return_status,
        return_date=delivery_order.return_date,
        remark=delivery_order.remark,
        items=[_build_delivery_item_response(item) for item in delivery_order.items or []],
        created_at=delivery_order.created_at,
        updated_at=delivery_order.updated_at,
    )


def build_delivery_order_approval_form_data(delivery_order: DeliveryOrder) -> dict[str, Any]:
    """构建发货单提交统一审批所需的业务快照。"""
    return {
        "delivery_id": delivery_order.id,
        "delivery_no": delivery_order.delivery_no,
        "order_id": delivery_order.order_id,
        "order_no": delivery_order.order_no,
        "contract_id": delivery_order.contract_id,
        "customer_id": delivery_order.customer_id,
        "customer_name": delivery_order.customer_name,
        "project_id": delivery_order.project_id,
        "delivery_date": (
            delivery_order.delivery_date.isoformat() if delivery_order.delivery_date else None
        ),
        "delivery_type": delivery_order.delivery_type,
        "delivery_amount": (
            float(delivery_order.delivery_amount)
            if delivery_order.delivery_amount is not None
            else 0
        ),
        "items": [
            {
                "item_name": item.item_name,
                "item_spec": item.item_spec,
                "delivery_qty": float(item.delivery_qty or 0),
                "unit": item.unit,
                "amount": float(item.amount or 0),
            }
            for item in delivery_order.items or []
        ],
        "special_approval": bool(delivery_order.special_approval),
        "special_approval_reason": delivery_order.special_approval_reason,
    }


def get_active_delivery_approval_instance(
    db: Session, delivery_id: int
) -> Optional[ApprovalInstance]:
    return (
        db.query(ApprovalInstance)
        .filter(
            ApprovalInstance.entity_type == DELIVERY_ORDER_APPROVAL_ENTITY_TYPE,
            ApprovalInstance.entity_id == delivery_id,
            ApprovalInstance.status.in_(ACTIVE_APPROVAL_STATUSES),
        )
        .order_by(desc(ApprovalInstance.created_at), desc(ApprovalInstance.id))
        .first()
    )


def get_pending_delivery_approval_task(
    db: Session, instance_id: int, user_id: int
) -> Optional[ApprovalTask]:
    return (
        db.query(ApprovalTask)
        .filter(
            ApprovalTask.instance_id == instance_id,
            ApprovalTask.assignee_id == user_id,
            ApprovalTask.status == "PENDING",
        )
        .order_by(ApprovalTask.id.asc())
        .first()
    )


@router.get(
    "/delivery-orders",
    response_model=ResponseModel[PaginatedResponse[DeliveryOrderResponse]],
    summary="获取发货单列表",
)
async def get_delivery_orders(
    pagination: PaginationParams = Depends(get_pagination_query),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    order_id: Optional[int] = Query(None, description="销售订单ID筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    approval_status: Optional[str] = Query(None, description="审批状态筛选"),
    delivery_status: Optional[str] = Query(None, description="发货状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取发货单列表"""
    try:
        query = db.query(DeliveryOrder)

        # 筛选条件
        if project_id:
            query = query.filter(DeliveryOrder.project_id == project_id)
        if order_id:
            query = query.filter(DeliveryOrder.order_id == order_id)
        if customer_id:
            query = query.filter(DeliveryOrder.customer_id == customer_id)
        if approval_status:
            query = query.filter(DeliveryOrder.approval_status == approval_status)
        if delivery_status:
            query = query.filter(DeliveryOrder.delivery_status == delivery_status)

        # 应用关键词过滤（发货单号/客户名称/物流单号）
        query = apply_keyword_filter(
            query, DeliveryOrder, search, ["delivery_no", "customer_name", "tracking_no"]
        )

        # 总数
        total = query.count()

        # 分页
        items = (
            query.order_by(desc(DeliveryOrder.created_at))
            .offset(pagination.offset)
            .limit(pagination.limit)
            .all()
        )

        # 转换为响应格式
        delivery_list = [build_delivery_order_response(item) for item in items]

        return ResponseModel(
            code=200,
            message="获取发货单列表成功",
            data=PaginatedResponse(
                items=delivery_list,
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
                pages=pagination.pages_for_total(total),
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取发货单列表失败: {str(e)}")


@router.post(
    "/delivery-orders", response_model=ResponseModel[DeliveryOrderResponse], summary="创建发货单"
)
async def create_delivery_order(
    delivery_data: DeliveryOrderCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """创建发货单"""
    try:
        # 检查销售订单是否存在
        sales_order = db.query(SalesOrder).filter(SalesOrder.id == delivery_data.order_id).first()
        if not sales_order:
            raise HTTPException(status_code=404, detail="销售订单不存在")

        if not sales_order.project_id:
            raise HTTPException(
                status_code=400,
                detail="发货计划必须从项目交付页或已关联项目的销售订单生成",
            )

        project = db.query(Project).filter(Project.id == sales_order.project_id).first()
        if not project:
            raise HTTPException(status_code=400, detail="销售订单关联的项目不存在")

        # 生成送货单号
        delivery_no = delivery_data.delivery_no or generate_delivery_no(db)

        # 检查送货单号是否已存在
        existing = db.query(DeliveryOrder).filter(DeliveryOrder.delivery_no == delivery_no).first()
        if existing:
            raise HTTPException(status_code=400, detail="送货单号已存在")

        delivery_items = _build_delivery_order_items(db, sales_order, delivery_data)

        # 创建发货单
        delivery_order = DeliveryOrder(
            delivery_no=delivery_no,
            order_id=delivery_data.order_id,
            order_no=sales_order.order_no,
            contract_id=sales_order.contract_id,
            customer_id=sales_order.customer_id,
            customer_name=sales_order.customer_name,
            project_id=sales_order.project_id,
            delivery_date=delivery_data.delivery_date,
            delivery_type=delivery_data.delivery_type,
            logistics_company=delivery_data.logistics_company,
            tracking_no=delivery_data.tracking_no,
            receiver_name=delivery_data.receiver_name,
            receiver_phone=delivery_data.receiver_phone,
            receiver_address=delivery_data.receiver_address,
            delivery_amount=delivery_data.delivery_amount,
            approval_status="pending",
            special_approval=delivery_data.special_approval or False,
            special_approval_reason=delivery_data.special_approval_reason,
            delivery_status="draft",
            remark=delivery_data.remark,
        )
        delivery_order.items = delivery_items

        db.add(delivery_order)
        db.commit()
        db.refresh(delivery_order)

        return ResponseModel(
            code=200,
            message="创建发货单成功",
            data=build_delivery_order_response(delivery_order),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建发货单失败: {str(e)}")


@router.get(
    "/delivery-orders/pending-approval",
    response_model=ResponseModel[PaginatedResponse[DeliveryOrderResponse]],
    summary="获取待审批发货单",
)
async def get_pending_approval_deliveries(
    pagination: PaginationParams = Depends(get_pagination_query),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取审批状态为 pending 的发货单列表"""
    try:
        query = db.query(DeliveryOrder).filter(DeliveryOrder.approval_status == "pending")
        total = query.count()
        items = (
            query.order_by(desc(DeliveryOrder.created_at))
            .offset(pagination.offset)
            .limit(pagination.limit)
            .all()
        )
        return ResponseModel(
            code=200,
            message="获取待审批发货单成功",
            data=PaginatedResponse(
                items=[build_delivery_order_response(item) for item in items],
                total=total,
                page=pagination.page,
                page_size=pagination.page_size,
                pages=pagination.pages_for_total(total),
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取待审批发货单失败: {str(e)}")


@router.post(
    "/delivery-orders/{delivery_id}/submit-approval",
    response_model=ResponseModel[dict[str, Any]],
    summary="提交发货单统一审批",
)
async def submit_delivery_order_approval(
    delivery_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("delivery:manage")),
):
    """将发货单提交到统一审批引擎。"""
    try:
        delivery_order = get_or_404(db, DeliveryOrder, delivery_id, "发货单不存在")
        if delivery_order.delivery_status in {"shipped", "received"}:
            raise HTTPException(status_code=400, detail="已发货或已签收的发货单不能提交审批")

        existing = get_active_delivery_approval_instance(db, delivery_id)
        if existing:
            return ResponseModel(
                code=200,
                message="发货单已在统一审批中",
                data={
                    "approval_instance_id": existing.id,
                    "instance_no": existing.instance_no,
                    "current_status": existing.status,
                    "entity_type": existing.entity_type,
                    "entity_id": existing.entity_id,
                },
            )

        engine = ApprovalEngineService(db)
        instance = engine.submit(
            template_code=DELIVERY_ORDER_APPROVAL_TEMPLATE_CODE,
            entity_type=DELIVERY_ORDER_APPROVAL_ENTITY_TYPE,
            entity_id=delivery_id,
            form_data=build_delivery_order_approval_form_data(delivery_order),
            initiator_id=current_user.id,
            title=f"发货单审批 - {delivery_order.delivery_no}",
            summary=f"客户: {delivery_order.customer_name or '未指定'}",
            urgency="NORMAL",
            cc_user_ids=None,
        )

        db.refresh(delivery_order)
        return ResponseModel(
            code=200,
            message="发货单统一审批已提交",
            data={
                "approval_instance_id": instance.id,
                "instance_no": instance.instance_no,
                "current_status": instance.status,
                "entity_type": instance.entity_type,
                "entity_id": instance.entity_id,
            },
        )
    except HTTPException:
        raise
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"提交发货单审批失败: {str(e)}")


@router.post(
    "/delivery-orders/{delivery_id}/approve",
    response_model=ResponseModel[DeliveryOrderResponse],
    summary="审批发货单",
)
async def approve_delivery_order(
    delivery_id: int,
    approval_data: DeliveryApprovalRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("delivery:manage")),
):
    """兼容旧入口：通过统一审批任务审批或驳回发货单。"""
    try:
        delivery_order = get_or_404(db, DeliveryOrder, delivery_id, "发货单不存在")
        if delivery_order.delivery_status in {"shipped", "received"}:
            raise HTTPException(status_code=400, detail="已发货或已签收的发货单不能重新审批")

        instance = get_active_delivery_approval_instance(db, delivery_id)
        if not instance:
            raise HTTPException(
                status_code=400,
                detail="发货单必须先提交统一审批，不能在模块内直接审批",
            )

        task = get_pending_delivery_approval_task(db, instance.id, current_user.id)
        if not task:
            raise HTTPException(status_code=403, detail="当前用户没有该发货单的待审批任务")

        engine = ApprovalEngineService(db)
        if approval_data.approved:
            engine.approve(
                task_id=task.id,
                approver_id=current_user.id,
                comment=approval_data.approval_comment,
            )
        else:
            engine.reject(
                task_id=task.id,
                approver_id=current_user.id,
                comment=approval_data.approval_comment or "发货审批驳回",
            )
        db.refresh(delivery_order)

        return ResponseModel(
            code=200,
            message="发货单统一审批处理成功",
            data=build_delivery_order_response(delivery_order),
        )
    except HTTPException:
        raise
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"审批发货单失败: {str(e)}")


@router.post(
    "/delivery-orders/{delivery_id}/print",
    response_model=ResponseModel[DeliveryOrderResponse],
    summary="打印送货单",
)
async def print_delivery_order(
    delivery_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """标记送货单已打印"""
    try:
        delivery_order = get_or_404(db, DeliveryOrder, delivery_id, "发货单不存在")
        if delivery_order.approval_status != "approved":
            raise HTTPException(status_code=400, detail="发货单未审批通过，不能打印")
        if delivery_order.delivery_status in {"shipped", "received"}:
            raise HTTPException(status_code=400, detail="已发货或已签收的发货单不能重新打印")

        delivery_order.delivery_status = "printed"
        delivery_order.print_date = datetime.now()

        db.commit()
        db.refresh(delivery_order)

        return ResponseModel(
            code=200,
            message="送货单打印状态更新成功",
            data=build_delivery_order_response(delivery_order),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"打印送货单失败: {str(e)}")


@router.post(
    "/delivery-orders/{delivery_id}/ship",
    response_model=ResponseModel[DeliveryOrderResponse],
    summary="确认发货",
)
async def ship_delivery_order(
    delivery_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("delivery:manage")),
):
    """确认发货并记录实际发货时间"""
    try:
        delivery_order = get_or_404(db, DeliveryOrder, delivery_id, "发货单不存在")
        if delivery_order.approval_status != "approved":
            raise HTTPException(status_code=400, detail="发货单未审批通过，不能发货")
        if delivery_order.delivery_status not in {"approved", "printed"}:
            raise HTTPException(status_code=400, detail="仅已审批或已打印的发货单可以发货")

        _ensure_delivery_has_valid_items(delivery_order)
        _ensure_project_kitting_ready(delivery_order.project)
        _ensure_final_quality_passed(db, delivery_order)

        delivery_order.delivery_status = "shipped"
        delivery_order.ship_date = datetime.now()
        _advance_project_status(delivery_order.project, stage="S8", status="ST24")
        PaymentPlanService(db).trigger_delivery_payment_plan(
            delivery_order,
            triggered_by=current_user.id,
            triggered_by_name=current_user.real_name or current_user.username,
        )

        db.commit()
        db.refresh(delivery_order)

        return ResponseModel(
            code=200,
            message="发货成功",
            data=build_delivery_order_response(delivery_order),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"确认发货失败: {str(e)}")


@router.post(
    "/delivery-orders/{delivery_id}/receive",
    response_model=ResponseModel[DeliveryOrderResponse],
    summary="确认签收",
)
async def receive_delivery_order(
    delivery_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(security.require_permission("delivery:manage")),
):
    """确认客户签收"""
    try:
        delivery_order = get_or_404(db, DeliveryOrder, delivery_id, "发货单不存在")
        if delivery_order.delivery_status != "shipped":
            raise HTTPException(status_code=400, detail="仅已发货的发货单可以确认签收")

        delivery_order.delivery_status = "received"
        delivery_order.receive_date = date.today()
        _advance_project_status(delivery_order.project, stage="S8", status="ST25")

        db.commit()
        db.refresh(delivery_order)

        return ResponseModel(
            code=200,
            message="签收成功",
            data=build_delivery_order_response(delivery_order),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"确认签收失败: {str(e)}")


@router.get(
    "/delivery-orders/{delivery_id}",
    response_model=ResponseModel[DeliveryOrderResponse],
    summary="获取发货单详情",
)
async def get_delivery_order(
    delivery_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """获取发货单详情"""
    try:
        delivery_order = get_or_404(db, DeliveryOrder, delivery_id, "发货单不存在")

        return ResponseModel(
            code=200,
            message="获取发货单详情成功",
            data=build_delivery_order_response(delivery_order),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取发货单详情失败: {str(e)}")


@router.put(
    "/delivery-orders/{delivery_id}",
    response_model=ResponseModel[DeliveryOrderResponse],
    summary="更新发货单",
)
async def update_delivery_order(
    delivery_id: int,
    delivery_data: DeliveryOrderUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """更新发货单"""
    try:
        delivery_order = get_or_404(db, DeliveryOrder, delivery_id, "发货单不存在")

        # 更新字段
        update_data = delivery_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(delivery_order, key, value)

        db.commit()
        db.refresh(delivery_order)

        return ResponseModel(
            code=200,
            message="更新发货单成功",
            data=build_delivery_order_response(delivery_order),
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新发货单失败: {str(e)}")
