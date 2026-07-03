# -*- coding: utf-8 -*-
"""
发货单基础CRUD操作
包含：列表、创建、详情、更新
"""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api import deps
from app.core import security
from app.common.pagination import PaginationParams, get_pagination_query
from app.common.query_filters import apply_keyword_filter
from app.models.business_support import DeliveryOrder, SalesOrder
from app.models.project import Project
from app.models.user import User
from app.schemas.business_support import (
    DeliveryApprovalRequest,
    DeliveryOrderCreate,
    DeliveryOrderResponse,
    DeliveryOrderUpdate,
)
from app.schemas.common import PaginatedResponse, ResponseModel
from app.services.sales.payment_plan_service import PaymentPlanService
from app.utils.db_helpers import get_or_404

from ..utils import generate_delivery_no

router = APIRouter()


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
        created_at=delivery_order.created_at,
        updated_at=delivery_order.updated_at,
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
    """审批通过或驳回发货单"""
    try:
        delivery_order = get_or_404(db, DeliveryOrder, delivery_id, "发货单不存在")
        if delivery_order.delivery_status in {"shipped", "received"}:
            raise HTTPException(status_code=400, detail="已发货或已签收的发货单不能重新审批")

        delivery_order.approval_status = "approved" if approval_data.approved else "rejected"
        delivery_order.approval_comment = approval_data.approval_comment
        delivery_order.approved_by = current_user.id
        delivery_order.approved_at = datetime.now()
        delivery_order.delivery_status = "approved" if approval_data.approved else "draft"

        db.commit()
        db.refresh(delivery_order)

        return ResponseModel(
            code=200,
            message="发货单审批成功",
            data=build_delivery_order_response(delivery_order),
        )
    except HTTPException:
        raise
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

        delivery_order.delivery_status = "shipped"
        delivery_order.ship_date = datetime.now()
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
