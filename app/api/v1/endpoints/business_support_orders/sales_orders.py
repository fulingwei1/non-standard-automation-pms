# -*- coding: utf-8 -*-
"""
商务支持模块 - 销售订单管理 API endpoints
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.api import deps
from app.models.business_support import SalesOrder, SalesOrderItem
from app.models.project import Customer, Project
from app.models.sales import Contract
from app.models.user import User
from app.schemas.business_support import (
    AssignProjectRequest,
    SalesOrderCreate,
    SalesOrderItemResponse,
    SalesOrderResponse,
    SalesOrderUpdate,
    SendNoticeRequest,
)
from app.schemas.common import PaginatedResponse, ResponseModel

from .utils import _send_project_department_notifications, generate_order_no

router = APIRouter()


# ==================== 销售订单管理 ====================


@router.get("/sales-orders", response_model=ResponseModel[PaginatedResponse[SalesOrderResponse]], summary="获取销售订单列表")
async def get_sales_orders(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    contract_id: Optional[int] = Query(None, description="合同ID筛选"),
    customer_id: Optional[int] = Query(None, description="客户ID筛选"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    order_status: Optional[str] = Query(None, description="订单状态筛选"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取销售订单列表"""
    try:
        query = db.query(SalesOrder)

        # 筛选条件
        if contract_id:
            query = query.filter(SalesOrder.contract_id == contract_id)
        if customer_id:
            query = query.filter(SalesOrder.customer_id == customer_id)
        if project_id:
            query = query.filter(SalesOrder.project_id == project_id)
        if order_status:
            query = query.filter(SalesOrder.order_status == order_status)
        if search:
            query = query.filter(
                or_(
                    SalesOrder.order_no.like(f"%{search}%"),
                    SalesOrder.customer_name.like(f"%{search}%"),
                    SalesOrder.contract_no.like(f"%{search}%")
                )
            )

        # 总数
        total = query.count()

        # 分页
        items = (
            query.order_by(desc(SalesOrder.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        # 转换为响应格式
        order_list = []
        for item in items:
            # 查询订单明细
            items_data = [
                SalesOrderItemResponse(
                    id=oi.id,
                    sales_order_id=oi.sales_order_id,
                    item_name=oi.item_name,
                    item_spec=oi.item_spec,
                    qty=oi.qty,
                    unit=oi.unit,
                    unit_price=oi.unit_price,
                    amount=oi.amount,
                    remark=oi.remark,
                    created_at=oi.created_at,
                    updated_at=oi.updated_at
                )
                for oi in item.order_items
            ]

            order_list.append(SalesOrderResponse(
                id=item.id,
                order_no=item.order_no,
                contract_id=item.contract_id,
                contract_no=item.contract_no,
                customer_id=item.customer_id,
                customer_name=item.customer_name,
                project_id=item.project_id,
                project_no=item.project_no,
                order_type=item.order_type,
                order_amount=item.order_amount,
                currency=item.currency,
                required_date=item.required_date,
                promised_date=item.promised_date,
                order_status=item.order_status,
                project_no_assigned=item.project_no_assigned,
                project_no_assigned_date=item.project_no_assigned_date,
                project_notice_sent=item.project_notice_sent,
                project_notice_date=item.project_notice_date,
                erp_order_no=item.erp_order_no,
                erp_sync_status=item.erp_sync_status,
                sales_person_id=item.sales_person_id,
                sales_person_name=item.sales_person_name,
                support_person_id=item.support_person_id,
                remark=item.remark,
                items=items_data,
                created_at=item.created_at,
                updated_at=item.updated_at
            ))

        return ResponseModel(
            code=200,
            message="获取销售订单列表成功",
            data=PaginatedResponse(
                items=order_list,
                total=total,
                page=page,
                page_size=page_size,
                pages=(total + page_size - 1) // page_size
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取销售订单列表失败: {str(e)}")


@router.post("/sales-orders", response_model=ResponseModel[SalesOrderResponse], summary="创建销售订单")
async def create_sales_order(
    order_data: SalesOrderCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """创建销售订单"""
    try:
        # 生成订单编号
        order_no = order_data.order_no or generate_order_no(db)

        # 检查订单编号是否已存在
        existing = db.query(SalesOrder).filter(SalesOrder.order_no == order_no).first()
        if existing:
            raise HTTPException(status_code=400, detail="订单编号已存在")

        # 获取客户名称
        customer = db.query(Customer).filter(Customer.id == order_data.customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="客户不存在")

        # 获取合同编号（如果有）
        contract_no = None
        if order_data.contract_id:
            contract = db.query(Contract).filter(Contract.id == order_data.contract_id).first()
            if contract:
                contract_no = contract.contract_code

        # 创建销售订单
        sales_order = SalesOrder(
            order_no=order_no,
            contract_id=order_data.contract_id,
            contract_no=contract_no,
            customer_id=order_data.customer_id,
            customer_name=customer.customer_name,
            project_id=order_data.project_id,
            order_type=order_data.order_type or "standard",
            order_amount=order_data.order_amount,
            currency=order_data.currency or "CNY",
            required_date=order_data.required_date,
            promised_date=order_data.promised_date,
            order_status="draft",
            sales_person_id=order_data.sales_person_id,
            sales_person_name=order_data.sales_person_name,
            support_person_id=current_user.id,
            remark=order_data.remark
        )

        db.add(sales_order)
        db.flush()  # 获取订单ID

        # 创建订单明细
        if order_data.items:
            for item_data in order_data.items:
                order_item = SalesOrderItem(
                    sales_order_id=sales_order.id,
                    item_name=item_data.item_name,
                    item_spec=item_data.item_spec,
                    qty=item_data.qty,
                    unit=item_data.unit,
                    unit_price=item_data.unit_price,
                    amount=item_data.amount,
                    remark=item_data.remark
                )
                db.add(order_item)

        db.commit()
        db.refresh(sales_order)

        # 查询订单明细
        items_data = [
            SalesOrderItemResponse(
                id=oi.id,
                sales_order_id=oi.sales_order_id,
                item_name=oi.item_name,
                item_spec=oi.item_spec,
                qty=oi.qty,
                unit=oi.unit,
                unit_price=oi.unit_price,
                amount=oi.amount,
                remark=oi.remark,
                created_at=oi.created_at,
                updated_at=oi.updated_at
            )
            for oi in sales_order.order_items
        ]

        return ResponseModel(
            code=200,
            message="创建销售订单成功",
            data=SalesOrderResponse(
                id=sales_order.id,
                order_no=sales_order.order_no,
                contract_id=sales_order.contract_id,
                contract_no=sales_order.contract_no,
                customer_id=sales_order.customer_id,
                customer_name=sales_order.customer_name,
                project_id=sales_order.project_id,
                project_no=sales_order.project_no,
                order_type=sales_order.order_type,
                order_amount=sales_order.order_amount,
                currency=sales_order.currency,
                required_date=sales_order.required_date,
                promised_date=sales_order.promised_date,
                order_status=sales_order.order_status,
                project_no_assigned=sales_order.project_no_assigned,
                project_no_assigned_date=sales_order.project_no_assigned_date,
                project_notice_sent=sales_order.project_notice_sent,
                project_notice_date=sales_order.project_notice_date,
                erp_order_no=sales_order.erp_order_no,
                erp_sync_status=sales_order.erp_sync_status,
                sales_person_id=sales_order.sales_person_id,
                sales_person_name=sales_order.sales_person_name,
                support_person_id=sales_order.support_person_id,
                remark=sales_order.remark,
                items=items_data,
                created_at=sales_order.created_at,
                updated_at=sales_order.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建销售订单失败: {str(e)}")


@router.get("/sales-orders/{order_id}", response_model=ResponseModel[SalesOrderResponse], summary="获取销售订单详情")
async def get_sales_order(
    order_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """获取销售订单详情"""
    try:
        sales_order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if not sales_order:
            raise HTTPException(status_code=404, detail="销售订单不存在")

        # 查询订单明细
        items_data = [
            SalesOrderItemResponse(
                id=oi.id,
                sales_order_id=oi.sales_order_id,
                item_name=oi.item_name,
                item_spec=oi.item_spec,
                qty=oi.qty,
                unit=oi.unit,
                unit_price=oi.unit_price,
                amount=oi.amount,
                remark=oi.remark,
                created_at=oi.created_at,
                updated_at=oi.updated_at
            )
            for oi in sales_order.order_items
        ]

        return ResponseModel(
            code=200,
            message="获取销售订单详情成功",
            data=SalesOrderResponse(
                id=sales_order.id,
                order_no=sales_order.order_no,
                contract_id=sales_order.contract_id,
                contract_no=sales_order.contract_no,
                customer_id=sales_order.customer_id,
                customer_name=sales_order.customer_name,
                project_id=sales_order.project_id,
                project_no=sales_order.project_no,
                order_type=sales_order.order_type,
                order_amount=sales_order.order_amount,
                currency=sales_order.currency,
                required_date=sales_order.required_date,
                promised_date=sales_order.promised_date,
                order_status=sales_order.order_status,
                project_no_assigned=sales_order.project_no_assigned,
                project_no_assigned_date=sales_order.project_no_assigned_date,
                project_notice_sent=sales_order.project_notice_sent,
                project_notice_date=sales_order.project_notice_date,
                erp_order_no=sales_order.erp_order_no,
                erp_sync_status=sales_order.erp_sync_status,
                sales_person_id=sales_order.sales_person_id,
                sales_person_name=sales_order.sales_person_name,
                support_person_id=sales_order.support_person_id,
                remark=sales_order.remark,
                items=items_data,
                created_at=sales_order.created_at,
                updated_at=sales_order.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取销售订单详情失败: {str(e)}")


@router.put("/sales-orders/{order_id}", response_model=ResponseModel[SalesOrderResponse], summary="更新销售订单")
async def update_sales_order(
    order_id: int,
    order_data: SalesOrderUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """更新销售订单"""
    try:
        sales_order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if not sales_order:
            raise HTTPException(status_code=404, detail="销售订单不存在")

        # 更新字段
        update_data = order_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(sales_order, key, value)

        db.commit()
        db.refresh(sales_order)

        # 查询订单明细
        items_data = [
            SalesOrderItemResponse(
                id=oi.id,
                sales_order_id=oi.sales_order_id,
                item_name=oi.item_name,
                item_spec=oi.item_spec,
                qty=oi.qty,
                unit=oi.unit,
                unit_price=oi.unit_price,
                amount=oi.amount,
                remark=oi.remark,
                created_at=oi.created_at,
                updated_at=oi.updated_at
            )
            for oi in sales_order.order_items
        ]

        return ResponseModel(
            code=200,
            message="更新销售订单成功",
            data=SalesOrderResponse(
                id=sales_order.id,
                order_no=sales_order.order_no,
                contract_id=sales_order.contract_id,
                contract_no=sales_order.contract_no,
                customer_id=sales_order.customer_id,
                customer_name=sales_order.customer_name,
                project_id=sales_order.project_id,
                project_no=sales_order.project_no,
                order_type=sales_order.order_type,
                order_amount=sales_order.order_amount,
                currency=sales_order.currency,
                required_date=sales_order.required_date,
                promised_date=sales_order.promised_date,
                order_status=sales_order.order_status,
                project_no_assigned=sales_order.project_no_assigned,
                project_no_assigned_date=sales_order.project_no_assigned_date,
                project_notice_sent=sales_order.project_notice_sent,
                project_notice_date=sales_order.project_notice_date,
                erp_order_no=sales_order.erp_order_no,
                erp_sync_status=sales_order.erp_sync_status,
                sales_person_id=sales_order.sales_person_id,
                sales_person_name=sales_order.sales_person_name,
                support_person_id=sales_order.support_person_id,
                remark=sales_order.remark,
                items=items_data,
                created_at=sales_order.created_at,
                updated_at=sales_order.updated_at
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新销售订单失败: {str(e)}")


@router.post("/sales-orders/{order_id}/assign-project", response_model=ResponseModel[SalesOrderResponse], summary="分配项目号")
async def assign_project_to_order(
    order_id: int,
    assign_data: AssignProjectRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """为销售订单分配项目号"""
    try:
        sales_order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if not sales_order:
            raise HTTPException(status_code=404, detail="销售订单不存在")

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

        # 查询订单明细
        items_data = [
            SalesOrderItemResponse(
                id=oi.id,
                sales_order_id=oi.sales_order_id,
                item_name=oi.item_name,
                item_spec=oi.item_spec,
                qty=oi.qty,
                unit=oi.unit,
                unit_price=oi.unit_price,
                amount=oi.amount,
                remark=oi.remark,
                created_at=oi.created_at,
                updated_at=oi.updated_at
            )
            for oi in sales_order.order_items
        ]

        return ResponseModel(
            code=200,
            message="分配项目号成功",
            data=SalesOrderResponse(
                id=sales_order.id,
                order_no=sales_order.order_no,
                contract_id=sales_order.contract_id,
                contract_no=sales_order.contract_no,
                customer_id=sales_order.customer_id,
                customer_name=sales_order.customer_name,
                project_id=sales_order.project_id,
                project_no=sales_order.project_no,
                order_type=sales_order.order_type,
                order_amount=sales_order.order_amount,
                currency=sales_order.currency,
                required_date=sales_order.required_date,
                promised_date=sales_order.promised_date,
                order_status=sales_order.order_status,
                project_no_assigned=sales_order.project_no_assigned,
                project_no_assigned_date=sales_order.project_no_assigned_date,
                project_notice_sent=sales_order.project_notice_sent,
                project_notice_date=sales_order.project_notice_date,
                erp_order_no=sales_order.erp_order_no,
                erp_sync_status=sales_order.erp_sync_status,
                sales_person_id=sales_order.sales_person_id,
                sales_person_name=sales_order.sales_person_name,
                support_person_id=sales_order.support_person_id,
                remark=sales_order.remark,
                items=items_data,
                created_at=sales_order.created_at,
                updated_at=sales_order.updated_at
            )
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
        sales_order = db.query(SalesOrder).filter(SalesOrder.id == order_id).first()
        if not sales_order:
            raise HTTPException(status_code=404, detail="销售订单不存在")

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
