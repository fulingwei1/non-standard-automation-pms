# -*- coding: utf-8 -*-
"""
发货单审批管理
包含：待审批列表、审批操作
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.business_support import DeliveryOrder
from app.models.user import User
from app.schemas.business_support import (
    DeliveryApprovalRequest,
    DeliveryOrderResponse,
)
from app.schemas.common import ResponseModel

router = APIRouter()


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
