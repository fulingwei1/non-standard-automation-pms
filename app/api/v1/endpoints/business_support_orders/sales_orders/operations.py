# -*- coding: utf-8 -*-
"""
销售订单管理 - 业务操作
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api import deps
from app.models.business_support import SalesOrder
from app.models.project import Project
from app.models.user import User
from app.schemas.business_support import AssignProjectRequest, SalesOrderResponse, SendNoticeRequest
from app.schemas.common import ResponseModel
from app.utils.db_helpers import get_or_404, save_obj, delete_obj

from ..utils import _send_project_department_notifications
from .utils import build_sales_order_response

router = APIRouter()


@router.post("/sales-orders/{order_id}/assign-project", response_model=ResponseModel[SalesOrderResponse], summary="分配项目号")
async def assign_project_to_order(
    order_id: int,
    assign_data: AssignProjectRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """为销售订单分配项目号"""
    try:
        sales_order = get_or_404(db, SalesOrder, order_id, "销售订单不存在")

        # 检查项目是否存在
        project = db.query(Project).filter(Project.id == assign_data.project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 分配项目号和项目ID
        sales_order.project_id = assign_data.project_id
        sales_order.project_no = assign_data.project_no or project.project_code
        sales_order.project_no_assigned = True
        sales_order.project_no_assigned_date = datetime.now()

        db.commit()
        db.refresh(sales_order)

        return ResponseModel(
            code=200,
            message="分配项目号成功",
            data=build_sales_order_response(sales_order)
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"分配项目号失败: {str(e)}")


@router.post("/sales-orders/{order_id}/send-notice", response_model=ResponseModel, summary="发送项目通知单")
async def send_project_notice(
    order_id: int,
    notice_data: SendNoticeRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """发送项目通知单"""
    try:
        sales_order = get_or_404(db, SalesOrder, order_id, "销售订单不存在")

        if not sales_order.project_no_assigned:
            raise HTTPException(status_code=400, detail="订单尚未分配项目号，无法发送通知单")

        # 更新通知单发送状态
        sales_order.project_notice_sent = True
        sales_order.project_notice_date = datetime.now()

        db.commit()

        # 实际发送通知给相关部门（PMC、生产、采购等）
        project = db.query(Project).filter(Project.id == sales_order.project_id).first()
        if project:
            title = f"项目通知单已发送：{project.project_name}"
            content = f"销售订单 {sales_order.order_no} 的项目通知单已发送。\n\n项目名称：{project.project_name}\n客户名称：{sales_order.customer_name}\n订单金额：¥{sales_order.total_amount or 0}\n交货日期：{sales_order.delivery_date or '未设置'}\n\n请相关部门做好准备工作。"

            _send_project_department_notifications(
                db=db,
                project_id=project.id,
                notification_type="SALES_ORDER_NOTICE",
                title=title,
                content=content,
                source_type="SALES_ORDER",
                source_id=sales_order.id,
                priority="HIGH",
                extra_data={
                    "order_no": sales_order.order_no,
                    "project_id": project.id,
                    "project_name": project.project_name
                }
            )

        return ResponseModel(
            code=200,
            message="项目通知单发送成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"发送项目通知单失败: {str(e)}")
