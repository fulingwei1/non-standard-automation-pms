# -*- coding: utf-8 -*-
"""
商务支持模块 - 发货管理 API endpoints
"""

from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.models.business_support import DeliveryOrder, SalesOrder
from app.models.user import User
from app.schemas.business_support import (
    DeliveryApprovalRequest,
    DeliveryOrderCreate,
    DeliveryOrderResponse,
    DeliveryOrderUpdate,
    DeliveryStatistics,
)
from app.schemas.common import PaginatedResponse, ResponseModel

from .utils import generate_delivery_no

router = APIRouter()


# ==================== 发货管理 ====================


@router.get("/delivery-orders", response_model=ResponseModel[PaginatedResponse[DeliveryOrderResponse]], summary="获取发货单列表")
async def get_delivery_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    order_id: Optional[int] = Query(None, description="销售订单ID筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    approval_status: Optional[str] = Query(None, description="审批状态筛选"),
    delivery_status: Optional[str] = Query(None, description="发货状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取发货单列表"""
    try:
        query = db.query(DeliveryOrder)

        # 筛选条件
        if order_id:
            query = query.filter(DeliveryOrder.order_id == order_id)
        if customer_id:
            query = query.filter(DeliveryOrder.customer_id == customer_id)
        if approval_status:
            query = query.filter(DeliveryOrder.approval_status == approval_status)
        if delivery_status:
            query = query.filter(DeliveryOrder.delivery_status == delivery_status)
        if search:
            query = query.filter(
                or_(
                    DeliveryOrder.delivery_no.like(f"%{search}%"),
                    DeliveryOrder.customer_name.like(f"%{search}%"),
                    DeliveryOrder.tracking_no.like(f"%{search}%")
                )
            )

        # 总数
        total = query.count()

        # 分页
        items = (
            query.order_by(desc(DeliveryOrder.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        # 转换为响应格式
        delivery_list = [
            DeliveryOrderResponse(
                id=item.id,
                delivery_no=item.delivery_no,
                order_id=item.order_id,
                order_no=item.order_no,
                contract_id=item.contract_id,
                customer_id=item.customer_id,
                customer_name=item.customer_name,
                project_id=item.project_id,
                delivery_date=item.delivery_date,
                delivery_type=item.delivery_type,
                logistics_company=item.logistics_company,
                tracking_no=item.tracking_no,
                receiver_name=item.receiver_name,
                receiver_phone=item.receiver_phone,
                receiver_address=item.receiver_address,
                delivery_amount=item.delivery_amount,
                approval_status=item.approval_status,
                approval_comment=item.approval_comment,
                approved_by=item.approved_by,
                approved_at=item.approved_at,
                special_approval=item.special_approval,
                special_approver_id=item.special_approver_id,
                special_approval_reason=item.special_approval_reason,
                delivery_status=item.delivery_status,
                print_date=item.print_date,
                ship_date=item.ship_date,
                receive_date=item.receive_date,
                return_status=item.return_status,
                return_date=item.return_date,
                remark=item.remark,
                created_at=item.created_at,
                updated_at=item.updated_at
            )
            for item in items
        ]

        return ResponseModel(
            code=200,
            message="获取发货单列表成功",
            data=PaginatedResponse(
                items=delivery_list,
                total=total,
                page=page,
                page_size=page_size,
                pages=(total + page_size - 1) // page_size
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取发货单列表失败: {str(e)}")


@router.post("/delivery-orders", response_model=ResponseModel[DeliveryOrderResponse], summary="创建发货单")
async def create_delivery_order(
    delivery_data: DeliveryOrderCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """创建发货单"""
    try:
        # 检查销售订单是否存在
        sales_order = db.query(SalesOrder).filter(SalesOrder.id == delivery_data.order_id).first()
        if not sales_order:
            raise HTTPException(status_code=404, detail="销售订单不存在")

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
            remark=delivery_data.remark
        )

        db.add(delivery_order)
        db.commit()
        db.refresh(delivery_order)

        return ResponseModel(
            code=200,
            message="创建发货单成功",
            data=DeliveryOrderResponse(
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
                updated_at=delivery_order.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建发货单失败: {str(e)}")


@router.get("/delivery-orders/pending-approval", response_model=ResponseModel[List[DeliveryOrderResponse]], summary="获取待审批发货单列表")
async def get_pending_approval_deliveries(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取待审批发货单列表"""
    try:
        deliveries = (
            db.query(DeliveryOrder)
            .filter(DeliveryOrder.approval_status == "pending")
            .order_by(DeliveryOrder.created_at.asc())
            .all()
        )

        delivery_list = [
            DeliveryOrderResponse(
                id=item.id,
                delivery_no=item.delivery_no,
                order_id=item.order_id,
                order_no=item.order_no,
                contract_id=item.contract_id,
                customer_id=item.customer_id,
                customer_name=item.customer_name,
                project_id=item.project_id,
                delivery_date=item.delivery_date,
                delivery_type=item.delivery_type,
                logistics_company=item.logistics_company,
                tracking_no=item.tracking_no,
                receiver_name=item.receiver_name,
                receiver_phone=item.receiver_phone,
                receiver_address=item.receiver_address,
                delivery_amount=item.delivery_amount,
                approval_status=item.approval_status,
                approval_comment=item.approval_comment,
                approved_by=item.approved_by,
                approved_at=item.approved_at,
                special_approval=item.special_approval,
                special_approver_id=item.special_approver_id,
                special_approval_reason=item.special_approval_reason,
                delivery_status=item.delivery_status,
                print_date=item.print_date,
                ship_date=item.ship_date,
                receive_date=item.receive_date,
                return_status=item.return_status,
                return_date=item.return_date,
                remark=item.remark,
                created_at=item.created_at,
                updated_at=item.updated_at
            )
            for item in deliveries
        ]

        return ResponseModel(
            code=200,
            message="获取待审批发货单列表成功",
            data=delivery_list
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取待审批发货单列表失败: {str(e)}")


@router.post("/delivery-orders/{delivery_id}/approve", response_model=ResponseModel[DeliveryOrderResponse], summary="审批发货单")
async def approve_delivery_order(
    delivery_id: int,
    approval_data: DeliveryApprovalRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """审批发货单"""
    try:
        delivery_order = db.query(DeliveryOrder).filter(DeliveryOrder.id == delivery_id).first()
        if not delivery_order:
            raise HTTPException(status_code=404, detail="发货单不存在")

        if delivery_order.approval_status != "pending":
            raise HTTPException(status_code=400, detail="发货单已审批，无法重复审批")

        # 更新审批状态
        delivery_order.approval_status = "approved" if approval_data.approved else "rejected"
        delivery_order.approval_comment = approval_data.approval_comment
        delivery_order.approved_by = current_user.id
        delivery_order.approved_at = datetime.now()

        # 如果审批通过，更新发货状态
        if approval_data.approved:
            delivery_order.delivery_status = "approved"

        db.commit()
        db.refresh(delivery_order)

        return ResponseModel(
            code=200,
            message="审批发货单成功",
            data=DeliveryOrderResponse(
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
                updated_at=delivery_order.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"审批发货单失败: {str(e)}")


@router.get("/delivery-orders/{delivery_id}", response_model=ResponseModel[DeliveryOrderResponse], summary="获取发货单详情")
async def get_delivery_order(
    delivery_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取发货单详情"""
    try:
        delivery_order = db.query(DeliveryOrder).filter(DeliveryOrder.id == delivery_id).first()
        if not delivery_order:
            raise HTTPException(status_code=404, detail="发货单不存在")

        return ResponseModel(
            code=200,
            message="获取发货单详情成功",
            data=DeliveryOrderResponse(
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
                updated_at=delivery_order.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取发货单详情失败: {str(e)}")


@router.put("/delivery-orders/{delivery_id}", response_model=ResponseModel[DeliveryOrderResponse], summary="更新发货单")
async def update_delivery_order(
    delivery_id: int,
    delivery_data: DeliveryOrderUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新发货单"""
    try:
        delivery_order = db.query(DeliveryOrder).filter(DeliveryOrder.id == delivery_id).first()
        if not delivery_order:
            raise HTTPException(status_code=404, detail="发货单不存在")

        # 更新字段
        update_data = delivery_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(delivery_order, key, value)

        db.commit()
        db.refresh(delivery_order)

        return ResponseModel(
            code=200,
            message="更新发货单成功",
            data=DeliveryOrderResponse(
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
                updated_at=delivery_order.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新发货单失败: {str(e)}")


@router.get("/delivery-orders/statistics", response_model=ResponseModel[DeliveryStatistics], summary="获取发货统计")
async def get_delivery_statistics(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    发货统计（给生产总监看）
    """
    try:
        today = date.today()
        today_start = datetime.combine(today, datetime.min.time())

        # 本周开始日期
        week_start = today - timedelta(days=today.weekday())

        # 待发货（已审批但未发货）
        pending_shipments = db.query(DeliveryOrder).filter(
            DeliveryOrder.delivery_status == "approved"
        ).count()

        # 今日已发
        shipped_today = db.query(DeliveryOrder).filter(
            DeliveryOrder.delivery_status == "shipped",
            DeliveryOrder.ship_date >= today_start
        ).count()

        # 在途订单（已发货但未签收）
        in_transit = db.query(DeliveryOrder).filter(
            DeliveryOrder.delivery_status == "shipped",
            DeliveryOrder.receive_date.is_(None)
        ).count()

        # 本周已送达
        delivered_this_week = db.query(DeliveryOrder).filter(
            DeliveryOrder.delivery_status == "received",
            DeliveryOrder.receive_date >= week_start
        ).count()

        # 准时发货率（计划发货日期 vs 实际发货日期）
        all_shipped = db.query(DeliveryOrder).filter(
            DeliveryOrder.delivery_status.in_(["shipped", "received"]),
            DeliveryOrder.delivery_date.isnot(None),
            DeliveryOrder.ship_date.isnot(None)
        ).all()

        on_time_count = 0
        for order in all_shipped:
            if order.ship_date.date() <= order.delivery_date:
                on_time_count += 1

        on_time_shipping_rate = (on_time_count / len(all_shipped) * 100) if all_shipped else 0.0

        # 平均发货时间（从发货到签收）
        delivered_orders = db.query(DeliveryOrder).filter(
            DeliveryOrder.delivery_status == "received",
            DeliveryOrder.ship_date.isnot(None),
            DeliveryOrder.receive_date.isnot(None)
        ).all()

        avg_shipping_time = 0.0
        if delivered_orders:
            total_days = sum(
                (order.receive_date - order.ship_date.date()).days
                for order in delivered_orders
            )
            avg_shipping_time = total_days / len(delivered_orders) if delivered_orders else 0.0

        # 总订单数
        total_orders = db.query(DeliveryOrder).count()

        return ResponseModel(
            code=200,
            message="获取发货统计成功",
            data=DeliveryStatistics(
                pending_shipments=pending_shipments,
                shipped_today=shipped_today,
                in_transit=in_transit,
                delivered_this_week=delivered_this_week,
                on_time_shipping_rate=on_time_shipping_rate,
                avg_shipping_time=avg_shipping_time,
                total_orders=total_orders,
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取发货统计失败: {str(e)}")
